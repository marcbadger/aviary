import numpy as np
import os
import cv2
import yaml
import sys
import json
from glob import glob
from tqdm import tqdm
import argparse

import subprocess

from matplotlib import pyplot as plt

from scipy.io import wavfile as wv
from scipy.signal import spectrogram, butter, sosfiltfilt, sosfreqz
from scipy.ndimage.filters import gaussian_filter
from scipy.interpolate import interp1d, RectBivariateSpline
from scipy.ndimage import maximum_filter

from scipy import ndimage as ndi
from skimage import measure

import skvideo.io

import scipy.optimize as opt

from utils.cameras import CameraSystem
from utils.SoundLoc import SoundLocalizer
from utils.cluster import ClusterStateManager

csm = ClusterStateManager(time_to_run=int(12*3600))

def export_spectrogram_localization(data_dir, segment_name, view='top'):

    if 'bot' in view:
        view = 'bot'
    else:
        view = 'top'

    cam_sys = CameraSystem(device='cpu')
    segment_dir = os.path.join(data_dir, segment_name + "_files")

    audio_file = os.path.join(segment_dir, segment_name + "_audio.wav")

    fs, this_wav = wv.read(audio_file)
    this_wav = this_wav.T
    mean_wav = np.mean(this_wav, axis = 0)

    sn=256
    fact=2

    window_size = 256*fact
    skip=sn//fact

    num_image_pixels = 3840
    the_buffer = window_size
    samples_per_spect = int(skip*(num_image_pixels-1)+window_size)
    pixels_to_crop = the_buffer//skip

    samples_per_jump = fs//40

    spect_windows = [[max(0, i - samples_per_spect//2 - the_buffer), min(i + samples_per_spect//2 + the_buffer, mean_wav.shape[0])] for i in range(0, mean_wav.shape[0], samples_per_jump)]

    filt_signal = butter_bandpass_filter(mean_wav, 5300, 10900, 48000)
    vocalization_signal = maximum_filter(np.abs(filt_signal), size = 160*skip)
    vocalization_mask = vocalization_signal > 40

    sl = SoundLocalizer(audio_file)

    outputfile = os.path.join(segment_dir, segment_name + f"_{view}_locspectmp.mp4")
    video_writer = skvideo.io.FFmpegWriter(outputfile, inputdict={'-r': '40'},
                                           outputdict={'-vcodec': 'libx264',
                                                       '-pix_fmt': 'yuv420p'})

    json_out = os.path.join(segment_dir, segment_name + f"_locspec.json")
    if os.path.exists(json_out):
        from_data_file = True
        with open(json_out, 'r') as f:
            json_data = json.load(f)
        last_frame_localized = max(json_data.keys())
    else:
        from_data_file = False
        json_data = {}

    mosaic_file = os.path.join(segment_dir, segment_name + f"_{view}.mp4")
    if not os.path.exists(mosaic_file):
        print("This video file doesn't exist:")
        print(mosaic_file)
        sys.exit()
    video_reader = cv2.VideoCapture(mosaic_file)
    stop_frame = int(video_reader.get(cv2.CAP_PROP_FRAME_COUNT))

    start_frame = 0
    video_reader.set(1, start_frame)

    colors = (plt.cm.tab20((4./3*np.arange(20*3/4)).astype(int))[:,:3]*255).astype(int)
    colors = colors[:,[1, 2, 0]]

    all_outputs = []
    for idx in tqdm(range(start_frame, stop_frame)):
        sw = spect_windows[idx]
        
        spec_low, spec_high, frequencies = make_spec(mean_wav[sw[0]:sw[1]], fs, window="hann", nperseg=window_size, noverlap = window_size-skip)
        spec_low, spec_high = (s[:-1,pixels_to_crop:-pixels_to_crop] for s in (spec_low, spec_high))
        spec = np.vstack([spec_high, spec_low])
        if spec.shape[1] != num_image_pixels:
            if idx < 18000:
                pw = ((0, 0), (num_image_pixels-spec.shape[1], 0))
            else:
                pw = ((0, 0), (0, num_image_pixels-spec.shape[1]))
            spec = np.pad(spec, 
                          pad_width = pw, 
                          mode = 'constant', constant_values = -3)
        img = ((spec+3)*255/6).astype(np.uint8)
        img = cv2.applyColorMap(img, cv2.COLORMAP_VIRIDIS)
        
        # draw a red vertical line
        img[:,num_image_pixels//2,:] = (0, 0, 255)
        
        valid, frame = video_reader.read()

        if from_data_file and idx <= last_frame_localized:
            try:
                output = json_data[idx]
            except KeyError as e:
                output = None
        else:
            from_data_file = False
            output, sample_start, sample_end = localize_sound(sl, sw, vocalization_mask, samples_per_spect, the_buffer)


        # TODO: debug drawing the window used for sound localization in the right place
        # line_start = num_image_pixels//2 + (sample_start - sw[0])//skip
        # line_end = num_image_pixels//2 + (sample_end-sw[0])//skip
        # img[:,line_start,:] = (0, 255, 255)
        # img[:,line_stop,:] = (0, 255, 255)

        if valid and output is not None:

            if not from_data_file:
                output = update_max_points(output)
                points_3d = np.concatenate(output['max_pt_updated'])
                points_2d = cam_sys.perspective_projection(points_3d)
                notvis_mask = points_2d[:,:,2] == 0
                depths = np.sqrt(np.sum(np.square(points_3d[None,:,:] - cam_sys.location.cpu().numpy()[:,None,:]), axis = -1))
                depths[notvis_mask] = np.NaN
                circle_size = (375/(depths+0.001)/2).astype(int)

                json_data[idx] = {'spect_window':sw,
                                  'sound_loc_sample_start':sample_start,
                                  'sound_loc_sample_end':sample_end,
                                  'points_3d':points_3d,
                                  'points_2d':points_2d,
                                  'depths':depths,
                                  'circle_size':circle_size}
            else:
                points_2d = np.array(output['points_2d'])
                circle_size = np.array(output['circle_size'])

            if view == 'top':
                points_2d[[0,1,4,5],:,2] = 0
            if view == 'bot':
                points_2d[[2,3,6,7],:,2] = 0

            mosaic_x_offsets = 1920 * np.array([0, 1, 1, 0, 0, 1, 1, 0])
            mosaic_y_offsets = 1200 * np.array([0, 0, 0, 0, 1, 1, 1, 1])
            for cam_num, (pts, sizes) in enumerate(zip(points_2d, circle_size)):
                for pt_num, (pt, pt_size) in enumerate(zip(pts, sizes)):
                    if pt[2]:
                        plot_x = int(pt[0] + mosaic_x_offsets[cam_num])
                        plot_y = int(pt[1] + mosaic_y_offsets[cam_num])
                        color_num = pt_num % colors.shape[0]
                        cv2.circle(frame, (plot_x, plot_y), pt_size, tuple(colors[color_num].tolist()), 5)

        if valid:
            frame = np.vstack([frame, img])
            video_writer.writeFrame(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        if csm.should_exit():
            try:
                os.remove(output_file)
                print("Job ending and partial file deleted.")
                sys.exit(csm.get_exit_code())
            except OSError as e:
                print("Job ending but couldn't delete the partial file!")
                print(f"{e.strerror}")
                sys.exit(csm.get_exit_code())

    video_writer.close()

    if not from_data_file:
        with open(json_out, 'w') as f:
            json.dump(jsonize(json_data), f)

    bashCommand = f"ffmpeg -y -i {output_file} -i {mosaic_file} -c copy -map 0:0 -map 1:1 {output_file.replace('_locspectmp.mp4', '_locspec.mp4')}"
    print(bashCommand)
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

    try:
        os.remove(output_file)
    except OSError as e:
        print(e.strerror)

    print(f"Final frame analyzed: {idx}")

    if __name__ == '__main__':
        sys.exit(csm.get_exit_code())

def jsonize(obj):
    if isinstance(obj, list):
        return [jsonize(o) for o in obj]
    elif isinstance(obj, dict):
        return {k:jsonize(v) for k, v in obj.items()}
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.int64):
        return int(obj)
    else:
        return obj

def make_spec(wavpart, fs, **kwargs):
    """Wrapper for scipy spectrogram that flips and clips"""
    f, ts, Sxx = spectrogram(wavpart, fs, **kwargs)
    Sxx = np.flipud(Sxx)
    Sxx = np.log(Sxx)
    Sxx_low = (np.clip(Sxx, -6, -3) + 6)*2 -3
    Sxx_high = np.clip(Sxx, -3, 3)
    
    return Sxx_low, Sxx_high, f

def butter_bandpass(lowcut, highcut, fs, order=5):
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        sos = butter(order, [low, high], analog=False, btype='band', output='sos')
        return sos

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
        sos = butter_bandpass(lowcut, highcut, fs, order=order)
        y = sosfiltfilt(sos, data)
        return y

def localize_sound(sl, sw, vocalization_mask, samples_per_spect, the_buffer, window_len = 400*128):
    
    # the middle of the window is samples_per_spect//2 + buffer from the beginning
    # so we'll crop 1/2 window_len on either side
    mid_idx = sw[0] + samples_per_spect//2 + the_buffer
    crop_start = mid_idx - window_len//2
    crop_end = mid_idx + window_len//2
     
    # trim to a 1s song-length window
    crop_mask = vocalization_mask[crop_start:crop_end]

    # trim further if surrounded by silence
    silence_idxs = np.where(crop_mask == False)[0]

    # first silence earlier than midpoint
    try:
        sample_start = crop_start + silence_idxs[silence_idxs <= crop_mask.shape[0]//2][-1]
    except IndexError:
        sample_start = crop_start
    
    # first silence later than midpoint
    try:
        sample_end = crop_start + silence_idxs[silence_idxs > crop_mask.shape[0]//2][0]
    except IndexError:
        sample_end = crop_end
    
    if not sample_end - sample_start > 48000/40/40:
        #print(f"silent window:{sw[0]}-{sw[1]},crop:{crop_start}-{crop_end},sample:{sample_start}-{sample_end}")
        return None, sample_start, sample_end
    
    #print(f"window:{sw[0]}-{sw[1]},crop:{crop_start}-{crop_end},sample:{sample_start}-{sample_end}")
    
    output = sl.wav_to_srp(sample_start, sample_end, fmt = 'samples')
    
    return output, sample_start, sample_end

def update_max_points(srp, mode='subpixel', sigma=1):
    '''Recalculate location of maximum SRP
    
    Args:
        mode (str): can be none, smooth, or subpixel
        sigma (int): amount of gaussian smoothing
    
    '''
    temp_srp = srp['srp']

    if mode == 'none':
        srp['max_pt_updated'] = srp['max_pt']
        return srp

    if sigma > 0:
        temp_srp = gaussian_filter(temp_srp, sigma = sigma)

    srp_min = np.amin(temp_srp)
    srp_max = np.amax(temp_srp)

    max_mask = temp_srp > 0.95 * (srp_max - srp_min) + srp_min
    labels = measure.label(max_mask, connectivity=2)
    regionprops = measure.regionprops(labels, intensity_image=temp_srp)
    max_locs = [tuple([int(wc) for wc in r.weighted_centroid]) for r in regionprops]

    xyz_grid = srp['gridpts'].copy().reshape(srp['srp'].shape[0], srp['srp'].shape[1], srp['srp'].shape[2], -1)

    if mode == 'smooth':
        srp['max_pt_updated'] = [xyz_grid[max_loc][None,:] for max_loc in max_locs]
        return srp

    srp['max_pt_updated'] = []
    for max_loc in max_locs:
        maxx = xyz_grid.shape[0]
        xp = xyz_grid[max(0,max_loc[0]-5):min(max_loc[0]+5, maxx), max_loc[1], max_loc[2]][:,0]
    #     fp = temp_srp[max(0,max_loc[0]-5):min(max_loc[0]+5, maxx), max_loc[1], max_loc[2]]
        xs = np.linspace(-0.1,0.1,200) + xyz_grid[max_loc[0], max_loc[1], max_loc[2]][0]
        xs = xs[(xs >= np.min(xp)) & (xs <= np.max(xp))]

    #     f = interp1d(xp, fp, kind='cubic')
    #     ipx = f(xs)
    #     ipx_max = np.argmax(ipx)

        maxy = xyz_grid.shape[1]

#         print(max_loc[0], max(0,max_loc[1]-5), min(max_loc[1]+5, maxy), max_loc[2])
#         print(xyz_grid[max_loc[0], 0:maxy, max_loc[2]])

        yp = xyz_grid[max_loc[0], max(0,max_loc[1]-5):min(max_loc[1]+5, maxy), max_loc[2]][:,1]
        fp = temp_srp[max_loc[0], max(0,max_loc[1]-5):min(max_loc[1]+5, maxy), max_loc[2]]
        ys = np.linspace(-0.1,0.1,200) + xyz_grid[max_loc[0], max_loc[1], max_loc[2]][1]
        ys = ys[(ys >= np.min(yp)) & (ys <= np.max(yp))]

    #     f = interp1d(yp, fp, kind='cubic')
    #     ipy = f(ys)
    #     ipy_max = np.argmax(ipy)

        fp = temp_srp[max(0,max_loc[0]-5):min(max_loc[0]+5, maxx), max(0,max_loc[1]-5):min(max_loc[1]+5, maxy), max_loc[2]]
        xy = np.array(np.meshgrid(xs, ys)).T
        xy_flat = xy.reshape(-1,2)

#         print(xp)
#         print(yp)

        f = RectBivariateSpline(xp, yp, fp, s = 0)
        fev = f.ev(xy_flat[:,0], xy_flat[:,1])
        fev_max = np.argmax(fev)
        themax_idx = np.unravel_index(fev_max, xy.shape[:2])
        themax = xy_flat[fev_max,:]

        srp['max_pt_updated'].append(np.array([[themax[0], themax[1], xyz_grid[max_loc[0], max_loc[1], max_loc[2]][2]]]))

    return srp

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='export mosaic with sound localization and spectrogram')
    parser.add_argument(
        '--data_dir', help='target directory containing mp4 files to extract data from')
    parser.add_argument(
        '--segment_name', help='target directory containing mp4 and audio files to extract data from')
    parser.add_argument(
        '--view', help="Output for 'top' or 'bottom' views.")
    
    args = parser.parse_args()

    export_spectrogram_localization(args.data_dir, args.segment_name, args.view)
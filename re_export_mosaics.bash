SEQUENCE=$1

FILE_DIR=/archive/birds/aviary/data2019/long_videos/female_annotations_dataset
SOURCE=${FILE_DIR}/${SEQUENCE}/${SEQUENCE/_files/_all.mp4}
echo $SOURCE
DEST_TOP=${FILE_DIR}/${SEQUENCE}/${SEQUENCE/_files/_top.mp4}
DEST_BOT=${FILE_DIR}/${SEQUENCE}/${SEQUENCE/_files/_bot.mp4}
echo ${DEST_TOP}
echo ${DEST_BOT}

# COMMAND=(ffmpeg -y -i ${SOURCE} -to 00:00:10 -filter_complex "[0:v] crop=in_w/4:in_h/2:in_w*(0/4):0 [topupperleft]; [0:v] crop=in_w/4:in_h/2:in_w*(1/4):0 [topupperright]; [0:v] crop=in_w/4:in_h/2:in_w*(2/4):0 [toplowerleft]; [0:v] crop=in_w/4:in_h/2:in_w*(3/4):0 [toplowerright]; nullsrc=size=3840x2400 [topbase]; [topbase][topupperleft] overlay=shortest=1 [toptmp1]; [toptmp1][topupperright] overlay=shortest=1:x=1920 [toptmp2]; [toptmp2][toplowerleft] overlay=shortest=1:y=1200 [toptmp3]; [toptmp3][toplowerright] overlay=shortest=1:x=1920:y=1200 [topout]; [0:v] crop=in_w/4:in_h/2:in_w*(0/4):in_h/2 [botupperleft]; [0:v] crop=in_w/4:in_h/2:in_w*(1/4):in_h/2 [botupperright]; [0:v] crop=in_w/4:in_h/2:in_w*(2/4):in_h/2 [botlowerleft]; [0:v] crop=in_w/4:in_h/2:in_w*(3/4):in_h/2 [botlowerright]; nullsrc=size=3840x2400 [botbase]; [botbase][botupperleft] overlay=shortest=1 [bottmp1]; [bottmp1][botupperright] overlay=shortest=1:x=1920 [bottmp2]; [bottmp2][botlowerleft] overlay=shortest=1:y=1200 [bottmp3]; [bottmp3][botlowerright] overlay=shortest=1:x=1920:y=1200 [botout]" -map "[topout]" -map 0:a -c:v libx264 -crf $RATE -pix_fmt yuv420p ${DEST_TOP} -map "[botout]" -map 0:a -c:v libx264 -crf $RATE -pix_fmt yuv420p ${DEST_BOT})
COMMAND=(ffmpeg -y -r 25 -i ${SOURCE} -filter_complex "[0:v]crop=in_w/4:in_h/2:in_w*(0/4):0[topupperleft];[0:v]crop=in_w/4:in_h/2:in_w*(1/4):0[topupperright];[0:v]crop=in_w/4:in_h/2:in_w*(2/4):0[toplowerleft];[0:v]crop=in_w/4:in_h/2:in_w*(3/4):0[toplowerright];[topupperleft][topupperright][toplowerleft][toplowerright]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[topout];[0:v]crop=in_w/4:in_h/2:in_w*(0/4):in_h/2[botupperleft];[0:v]crop=in_w/4:in_h/2:in_w*(1/4):in_h/2[botupperright];[0:v]crop=in_w/4:in_h/2:in_w*(2/4):in_h/2[botlowerleft];[0:v]crop=in_w/4:in_h/2:in_w*(3/4):in_h/2[botlowerright];[botupperleft][botupperright][botlowerleft][botlowerright]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[botout];[0:a]pan=stereo|c0<c0|c1<c1[topaout]; [0:a]pan=stereo|c0<c0|c1<c1[botaout]" -map "[topout]" -c:v libx264 -crf 30 -pix_fmt yuv420p -map "[topaout]" -c:a aac -strict -2 ${DEST_TOP} -map "[botout]" -c:v libx264 -crf 30 -pix_fmt yuv420p -map "[botaout]" -c:a aac -strict -2 ${DEST_BOT})

echo "${COMMAND[@]}"
# srun --qos=low --partition=compute --mem-per-gpu=16G --cpus-per-gpu=4 --time=4:00:00 --gpus=rtx2080ti:1 --pty "${COMMAND[@]}"
srun --qos=kostas-med --partition=kostas-compute --mem-per-cpu=4G --cpus-per-task=8 --time=24:00:00 --pty "${COMMAND[@]}"

# COMMAND=(ffmpeg -y -r 25 -i ${SOURCE} -to 00:00:10 -filter_complex \
# "[0:v] crop=in_w/4:in_h/2:in_w*(0/4):0 [topupperleft]; \
# [0:v] crop=in_w/4:in_h/2:in_w*(1/4):0 [topupperright]; \
# [0:v] crop=in_w/4:in_h/2:in_w*(2/4):0 [toplowerleft]; \
# [0:v] crop=in_w/4:in_h/2:in_w*(3/4):0 [toplowerright]; \
# nullsrc=size=3840x2400 [topbase]; \
# [topbase][topupperleft] overlay=shortest=1 [toptmp1]; \
# [toptmp1][topupperright] overlay=shortest=1:x=1920 [toptmp2]; \
# [toptmp2][toplowerleft] overlay=shortest=1:y=1200 [toptmp3]; \
# [toptmp3][toplowerright] overlay=shortest=1:x=1920:y=1200 [topout]" \
# -map "[topout]" -map 0:a -c:v libx264 -crf 30 -pix_fmt yuv420p -r 25 ${DEST_TOP})



# merge_audio_and_video(audio_file=os.path.join(filesdir,'{}_audio.raw'.format(basename)),
#                                   video_file=os.path.join(filesdir,'video_full.h265'),
#                                   audio_aux=os.path.join(filesdir,'{}_audio.aux'.format(basename)),
#                                   video_aux=os.path.join(filesdir,'video_full.aux'),
#                                   output_file=os.path.join(filesdir,'{}_all.mp4'.format(basename)),
#                                   channels=[0,2], video_format='copy')

# ffmpeg -y -r 40.000000 -itsoffset 0.2905 -i /archive/birds/aviary/data2019/long_videos/female_annotations_dataset/aviary_2019-05-15_1557918000.000-1557918900.000_files/video_full.h265 -f s24le -ar 48000.000000 -ac 24  -i /archive/birds/aviary/data2019/long_videos/female_annotations_dataset/aviary_2019-05-15_1557918000.000-1557918900.000_files/aviary_2019-05-15_1557918000.000-1557918900.000_audio.raw -map_channel 1.0.0 -map_channel 1.0.2 -filter_complex "[0:v] crop=in_w/4:in_h/2:in_w*(0/4):0 [topupperleft]; [0:v] crop=in_w/4:in_h/2:in_w*(1/4):0 [topupperright]; [0:v] crop=in_w/4:in_h/2:in_w*(2/4):0 [toplowerleft]; [0:v] crop=in_w/4:in_h/2:in_w*(3/4):0 [toplowerright]; nullsrc=size=3840x2400 [topbase]; [topbase][topupperleft] overlay=shortest=1 [toptmp1]; [toptmp1][topupperright] overlay=shortest=1:x=1920 [toptmp2]; [toptmp2][toplowerleft] overlay=shortest=1:y=1200 [toptmp3]; [toptmp3][toplowerright] overlay=shortest=1:x=1920:y=1200 [topout]; [0:v] crop=in_w/4:in_h/2:in_w*(0/4):in_h/2 [botupperleft]; [0:v] crop=in_w/4:in_h/2:in_w*(1/4):in_h/2 [botupperright]; [0:v] crop=in_w/4:in_h/2:in_w*(2/4):in_h/2 [botlowerleft]; [0:v] crop=in_w/4:in_h/2:in_w*(3/4):in_h/2 [botlowerright]; nullsrc=size=3840x2400 [botbase]; [botbase][botupperleft] overlay=shortest=1 [bottmp1]; [bottmp1][botupperright] overlay=shortest=1:x=1920 [bottmp2]; [bottmp2][botlowerleft] overlay=shortest=1:y=1200 [bottmp3]; [bottmp3][botlowerright] overlay=shortest=1:x=1920:y=1200 [botout]" -map "[topout]" -c:v libx264 -crf 30 -pix_fmt yuv420p -c:a:0 aac -strict -2 -c:a:1 aac -strict -2 /archive/birds/aviary/data2019/long_videos/female_annotations_dataset/aviary_2019-05-15_1557918000.000-1557918900.000_top.mp4 -map "[botout]" -c:v libx264 -crf 30 -pix_fmt yuv420p -c:a:0 aac -strict -2 -c:a:1 aac -strict -2 /archive/birds/aviary/data2019/long_videos/female_annotations_dataset/aviary_2019-05-15_1557918000.000-1557918900.000_bot.mp4
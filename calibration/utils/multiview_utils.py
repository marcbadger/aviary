import yaml
import os
import numpy as np
import torch

from .geometry import perspective_projection


def get_fullsize_masks(masks, bboxes, h=1200, w=1920):
    full_masks = []
    for i in range(len(masks)):
        box = bboxes[i]
        full_mask = torch.zeros([h, w], dtype=torch.bool)
        full_mask[box[1]:box[1]+box[3]+1, box[0]:box[0]+box[2]+1] = masks[i]
        full_masks.append(full_mask)
    full_masks = torch.stack(full_masks)

    return full_masks


def get_cam(frames, device='cpu', yaml_file='extrinsic_calib_v5.yaml'):
    '''
    Input:
    frames: list containing frame numbers
    
    '''
    # map frames to cams
    frame_to_cam_map = {0:3,1:2,2:7,3:6,4:0,5:1,6:4,7:5}
    cams = [frame_to_cam_map[i] for i in frames]  
    
    # cam parameters from yaml
    this_dir = os.path.dirname(__file__)

    calibs = yaml.safe_load(open(os.path.join(this_dir, yaml_file)))
    cam_Ps = [np.array(calibs[key]['T_cam_imu']) for key in sorted(calibs)]
    cam_in = [np.array(calibs[key]['intrinsics']) for key in sorted(calibs)]
    cam_dt = [np.array(calibs[key]['distortion_coeffs']) for key in sorted(calibs)]
    
    # rotation, translation, focal_length, camera_center
    rotation = [cam_Ps[i][:3, :3] for i in cams]
    translation = [cam_Ps[i][:3, 3] for i in cams]
    focal = [cam_in[i][:2].mean() for i in cams]
    center = [cam_in[i][2:] for i in cams]
    distortion = [cam_dt[i] for i in cams]

    # Convert to tensor
    rotation = torch.tensor(rotation).float().to(device)
    translation = torch.tensor(translation).float().to(device)
    focal = torch.tensor(focal).float().to(device)
    center = torch.tensor(center).float().to(device)
    distortion = torch.tensor(distortion).float().to(device)
    
    return rotation, translation, focal, center, distortion


def projection_loss(x, y):
    loss = (x.float() - y.float()).norm(p=2)
    return loss


def triangulation_LBFGS(x, R, t, focal, center, distortion, device='cpu'):
    n = x.shape[0]
    X = torch.tensor([2.9, 1.4, 1.4])[None,None,:]
    X.requires_grad_()
    
    x = x.to(device)
    X = X.to(device)
    
    losses = []
    optimizer = torch.optim.LBFGS([X], lr=1, max_iter=100, line_search_fn='strong_wolfe')
    
    def closure():
        projected_points = perspective_projection(X.repeat(n,1,1), R, t, focal, center, distortion)
        loss = projection_loss(projected_points.squeeze(), x)
        
        optimizer.zero_grad()
        loss.backward()
        return loss
    
    optimizer.step(closure)
    
    with torch.no_grad():
        projected_points = perspective_projection(X.repeat(n,1,1), R, t, focal, center, distortion)
        loss = projection_loss(projected_points.squeeze(), x)
        losses.append(loss.detach().item())    
    X = X.detach().squeeze()
    
    return X, losses


def triangulation(x, R, t, focal, center, distortion, device='cpu'):
    n = x.shape[0]
    X = torch.tensor([2.5, 1.2, 1.95])[None,None,:]
    X.requires_grad_()
    
    x = x.to(device)
    X = X.to(device)
    
    losses = []
    optimizer = torch.optim.Adam([X], lr=0.1)
    scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer, [50, 90], gamma=0.1)
    for i in range(100):
        projected_points = perspective_projection(X.repeat(n,1,1), R, t, focal, center, distortion)
        loss = projection_loss(projected_points.squeeze(), x)
    
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        scheduler.step()
        losses.append(loss.detach().item())
        
    X = X.detach().squeeze()
    
    return X, losses


def get_gt_3d(keypoints, frames, LBFGS=False):
    '''
    Input: 
        keypoints (bn, kn, 2): 2D kpts from different views
        frames (bn): frame numbers
    Output:
        kpts_3d (kn, 4): ground truth 3D kpts, with validility

    '''
    bn, kn, _ = keypoints.shape
    kpts_3d = torch.zeros([kn, 4])
    
    # 
    rotation, translation, focal, center, distortion = get_cam(frames)
    kpts_valid = []
    cams = []
    for i in range(kn):
        valid = keypoints[:, i, -1]>0
        kpts_valid.append(keypoints[valid, i, :2])
        cams.append(valid)
    
    #
    for i in range(kn):
        x = kpts_valid[i]
        if len(x)>=2:
            R = rotation[cams[i]]
            t = translation[cams[i]]
            f = focal[cams[i]]
            c = center[cams[i]]
            dis = distortion[cams[i]]
            
            if LBFGS:
                X, _ = triangulation_LBFGS(x, R, t, f, c, dis)
            else:
                X, _ = triangulation(x, R, t, f, c, dis)
                
            kpts_3d[i,:3] = X
            kpts_3d[i,-1] = 1
            
    return kpts_3d


def Procrustes(X, Y):
    """ 
    Solve full Procrustes: Y = s*RX + t

    Input:
        X (N,3): tensor of N points
        Y (N,3): tensor of N points in world coordinate 
    Returns:
        R (3x3): tensor describing camera orientation in the world (R_wc)
        t (3,): tensor describing camera translation in the world (t_wc)
        s (1): scale
    """
    # remove translation
    A = Y - Y.mean(dim=0, keepdim=True)
    B = X - X.mean(dim=0, keepdim=True)
    
    # remove scale
    sA = (A*A).sum()/A.shape[0]
    sA = sA.sqrt()
    sB = (B*B).sum()/B.shape[0]
    sB = sB.sqrt()   
    A = A / sA
    B = B / sB
    s = sA / sB
    
    # to numpy, then solve for R
    A = A.t().numpy()
    B = B.t().numpy()
    
    M = B @ A.T
    U, S, VT = np.linalg.svd(M)
    V = VT.T
    
    d = np.eye(3)
    d[-1, -1] = np.linalg.det(V @ U.T)
    R = V @ d @ U.T
    
    # back to tensor
    R = torch.tensor(R).float()
    t = Y.mean(axis=0) - R@X.mean(axis=0) * s
    
    return R, t, s
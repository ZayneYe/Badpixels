import numpy as np
import os
import torch

def reconstruct_expand(predict):
    B, _, h, w = predict.shape
    H = (h - 2) * 2
    W = (w - 2) * 2
    mid_H = int(H / 2)
    mid_W = int(W / 2)
    reconstruct =  torch.zeros(B, H, W)
    reconstruct[:, :mid_H,:mid_W] = predict[:, 0, :mid_H,:mid_W]
    reconstruct[:, mid_H:H,:mid_W] = predict[:, 1, :mid_H,2:mid_W+2]
    reconstruct[:, :mid_H,mid_W:W] = predict[:, 2, 2:mid_H+2,:mid_W]
    reconstruct[:, mid_H:H,mid_W:W] = predict[:, 3, 2:mid_H+2,2:mid_W+2]
    return reconstruct

def reconstruct(predict):
    B, p, h, w = predict.shape
    p_sqrt = int(pow(p, 0.5))
    H = int(p_sqrt * h)
    W = int(p_sqrt * w)
    reconstruct =  torch.zeros(B, H, W)
    cnt = 0
    for i in range(p_sqrt):
        row_start = i * h
        row_end = (i + 1) * h
        
        for j in range(p_sqrt):
            col_start = j * w
            col_end = (j + 1) * w
            reconstruct[:, row_start:row_end, col_start:col_end] = predict[:, cnt, :, :]
            cnt += 1
    return reconstruct

def divide64(fea, idx):
    patch = 8
    fea_combine = []
    H, W = fea.shape
    H_slice = int(H / patch)
    W_slice = int(W / patch)
    for i in range(patch):
        row_start = i * H_slice
        row_end = (i + 1) * H_slice
        
        for j in range(patch):
            col_start = j * W_slice
            col_end = (j + 1) * W_slice
            fea_sliced = fea[row_start:row_end, col_start:col_end]
            fea_combine.append(fea_sliced)
    return fea_combine[idx]
            
def divide4(fea, idx):
    H, W = fea.shape
    fea1 = fea[0:int(H/2 + 2), 0:int(W/2 + 2)]
    fea2 = fea[int(H/2 - 2):H, 0:int(W/2 + 2)]
    fea3 = fea[0:int(H/2 + 2), int(W/2 - 2):W]
    fea4 = fea[int(H/2 - 2):H, int(W/2 - 2):W]
    fea_combine = np.stack((fea1, fea2, fea3, fea4))
    return fea_combine[idx]

def preprocess(img, mask, idx):
    img_ = divide4(img, idx)
    mask_ = divide4(mask, idx)
    return img_, mask_

def generate_pred_dict(pred_dict, file, predict, label):
    if file in pred_dict:
        pred_dict[file]['pred'].append(predict)
        pred_dict[file]['lab'].append(label)
    else:
        pred_dict[file] = {}
        pred_dict[file]['pred'] = [predict]
        pred_dict[file]['lab'] = [label]
    return pred_dict

def postprocess(pred_dict, dataset):
    pred_all, lab_all = [], []

    for key in pred_dict.keys():
        pred = torch.cat(pred_dict[key]['pred'], dim=1)
        lab = torch.cat(pred_dict[key]['lab'], dim=1)
        pred_recon = reconstruct_expand(pred)
        lab_recon = reconstruct_expand(lab)
        # lab_real = np.load(os.path.join("/home/xinanye/project/Badpixels/data/ISP/masks/val", str(key[0]))).astype(np.float32)
        # lab_real = torch.tensor(lab_real)
        # print(lab_real.shape)
        # print(lab_recon.squeeze(0).shape)
        # print(torch.equal(lab_real, lab_recon.squeeze(0)))
        pred_all.append(pred_recon)
        lab_all.append(lab_recon)
    if dataset == "ISP":
        return torch.cat(pred_all, dim=0), torch.cat(lab_all, dim=0)
    else:
        return pred_all, lab_all
    
if __name__ == '__main__':
    npy_dir = "/home/xinanye/project/Badpixels/data/SIDD_DNG/masks"
    for cate in os.listdir(npy_dir):
        for npy in os.listdir(os.path.join(npy_dir, cate)):
            npy = np.load(os.path.join(npy_dir, cate, npy))
            npy_4 = divide4(npy)
            npy_re = reconstruct_expand(npy_4)
            print(npy_re.all() == npy.all())
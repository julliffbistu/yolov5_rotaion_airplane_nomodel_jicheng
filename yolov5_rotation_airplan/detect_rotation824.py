import argparse
import time
from pathlib import Path

import numpy as np
import cv2,glob,os,pickle
import torch
import math
import json
import torch.backends.cudnn as cudnn

import os.path as osp
import matplotlib.pyplot as plt
from tqdm import tqdm

from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages
from utils.general import check_img_size, check_requirements, check_imshow, non_max_suppression, apply_classifier, non_max_suppression_rotation, \
    scale_coords, xyxy2xywh, strip_optimizer, set_logging, increment_path, save_one_box
from utils.plots import colors, plot_one_box
from utils.torch_utils import select_device, load_classifier, time_synchronized
from utils.remote_utils import crop_xyxy2ori_xyxy,nms,draw_clsdet,draw_clsdet_rotation,rboxes2points
from utils.eval_casia import casia_eval
from class_thres import class_thres


multi_img_type=['*.jpg','*.png','*.tif','*.tiff']
# multi_img_type=['*PAN.tif']# remote origin image
#def work_dirs(data_dir):
CLASSES=['A','B','C','D','E','F','G','H','I','J','K']

def takesix(elem):
    return elem[5]

def new_list_pred(data):
    new_data = []
    center_list = []
    #print("len: ", len(data))
    if data:
        data.sort(key=takesix, reverse=True)
        # print(data[0])
        temp_point = data[0]
        #print(temp_point)
        tempx = int(temp_point[0])
        tempy = int(temp_point[1])
        center_list.append([tempx, tempy])
        #print(center_list[0])
        new_data.append(data[0])
        #print("============================================================")
        #print(new_data)
        #print(center_list)
        #print("============================================================")

        for i in range(1, len(data)):
            has = False
            point = data[i]

            centerx = int(point[0])
            centery = int(point[1])
            for j in range(len(center_list)):

                distancex = (centerx - center_list[j][0]) * (centerx - center_list[j][0])
                distancey = (centery - center_list[j][1]) * (centery - center_list[j][1])

                if (distancex + distancey < 100):
                    has = True
            if has == False:
                center_list.append([centerx, centery])
                new_data.append(data[i])
            #print(center_list)
    #print("new data: ", new_data)
    return new_data

@torch.no_grad()
def detect(weights='yolov5s.pt',  # model.pt path(s)
           source='data/images',  # file/dir/URL/glob, 0 for webcam
           annot_dir='data/labels',
           imgsz=640,  # inference size (pixels)
           overlap=200,# cut subimage overlap for remote images
           conf_thres=0.01,  # confidence threshold
           iou_thres=0.45,  # NMS IOU threshold
           max_det=1000,  # maximum detections per image
           remote=True, #infer remote big
           device='',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
           view_img=False,  # show results
           save_pkl=False,  # save results to *.txt
           save_json=True,  # save json  labels
           save_crop=False,  # save cropped prediction boxes
           nosave=False,  # do not save images/videos
           classes=None,  # filter by class: --class 0, or --class 0 2 3
           agnostic_nms=False,  # class-agnostic NMS
           augment=False,  # augmented inference
           update=False,  # update all models
           project='runs/detect',  # save results to project/name
           name='exp',  # save results to project/name
           exist_ok=False,  # existing project/name ok, do not increment
           line_thickness=3,  # bounding box thickness (pixels)
           hide_labels=False,  # hide labels
           hide_conf=False,  # hide confidences
           half=False,  # use FP16 half-precision inference
           ):
    save_img = not nosave and not source.endswith('.txt')  # save inference images
    # Directories
    save_dir = increment_path(Path(project) / name, exist_ok=exist_ok)  # increment run
    (save_dir / 'labels' if save_pkl else save_dir).mkdir(parents=True, exist_ok=True)  # make dir
    
    # Initialize
    set_logging()
    device = select_device(device)
    half &= device.type != 'cpu'  # half precision only supported on CUDA

    # Load model
    #weights = '/work/weights/best.pt'
    model = attempt_load(weights, map_location=device)  # load FP32 model
    stride = int(model.stride.max())  # model stride
    imgsz = check_img_size(imgsz, s=stride)  # check image size
    if remote:
        imglist=[]
        for img_type in multi_img_type:
            imglist+=glob.glob(os.path.join(source,img_type))
    # Run inference
    if device.type != 'cpu':
        model(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model.parameters())))  # run once
    t0 = time.time()
    vis_dir=osp.join(save_dir,'vis_results')
    if not osp.exists(vis_dir):
        os.mkdir(vis_dir)
    det_results={}
    save_results=[]
    # import pdb;pdb.set_trace()
    for i,imgpath in enumerate(imglist):
        # print(f'{i}/{len(imglist)} processing {imgpath}')
        
        ts=time.time()
        
        basename=os.path.splitext(os.path.basename(imgpath))[0]

        ori_img=cv2.imread(imgpath)
        H,W,C=ori_img.shape
        img=ori_img.copy()
        
        img=img.transpose(2,0,1)
        img = torch.from_numpy(img).to(device)

        img = img.half() if half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # Inference
        pred = model(img, augment=augment)[0]
        # Apply NMS
        # import pdb;pdb.set_trace()
        pred = non_max_suppression_rotation(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)
        # import pdb;pdb.set_trace()
        
        # import pdb;pdb.set_trace()
        if len(pred[0])>0:
            # import pdb;pdb.set_trace()
            pred=[pd.cpu().numpy().tolist() for pd in pred[0]]
            pred = new_list_pred(pred)
            pred = class_thres(pred)
            if pred == []:
                continue
            img_result=rboxes2points(pred,CLASSES)
            # import pdb;pdb.set_trace()
            det_results[basename]=pred
            p = Path(imgpath)
            print(f'detected {len(pred)} airplane !')
            if save_json:
                save_result={}
                save_result['image_name']=osp.basename(imgpath)
                save_result['labels']=img_result
                save_results.append(save_result)            
            # import pdb;pdb.set_trace()
            if save_img:
                show_img=ori_img.copy()
                show_img2=draw_clsdet_rotation(show_img,pred,conf_thres) 
                # import pdb;pdb.set_trace()
                save_path = osp.join(vis_dir,'{}.png'.format(basename))  
                cv2.imwrite(save_path,show_img2)  
                print(f'{save_path} saved!')
            print(f'{i}/{len(imglist)}  processing {p.name}  shape:{(H,W,C)} ({time.time()-ts:.3f}s ETA: {(time.time()-ts)*(len(imglist)-i):.3f}s)')

    det_file=os.path.join(save_dir,'results.pkl')
    if save_json!=None:
        save_result_file=open(save_json,'w')
        json.dump(save_results,save_result_file,indent=2)
        save_result_file.close()
        print('save json file {} succeed!'.format(save_result_file))        
    with open(det_file, 'wb') as f:
        pickle.dump(det_results, f, pickle.HIGHEST_PROTOCOL)
        print(f'save {det_file} successed!')
    print(f'Done. ({time.time() - t0:.3f}s)')
    return det_file

def eval_remote(annot_dir,annot_type,det_path,imglist,clssname,iou_thre,conf_thre,opt):

    rec,prec,ap=casia_eval(annot_dir,annot_type,det_path,  
                    imglist,clssname,conf_thre)
    det_dir=os.path.dirname(det_path)
    results_path=osp.join(det_dir,'results.txt')
    save_ap_fig=osp.join(det_dir,'AP.png')
    plt.plot(rec,prec)
    plt.xlim(0,1)
    plt.ylim(0,1)

    plt.xlabel('recall');plt.ylabel('presicion')
    plt.savefig(save_ap_fig)
    with open(results_path,'w',encoding='utf-8') as f:
        f.write('imgsource: {}\nweights: {}\n'.format(opt.source,opt.weights))
        f.write('iou overthre:{}\nConfidence thre:{}\nAP:{}\nMaxRecall:{} \nMinPrecision: {}\n'\
                .format(iou_thre,conf_thre,ap,rec[-1],prec[-1]))
    f.close()
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str, default='yolov5s.pt', help='model.pt path(s)')
    parser.add_argument('--source', type=str, default='data/images', help='file/dir/URL/glob, 0 for webcam')
    parser.add_argument('--annot_dir', type=str, default='data/labels', help='file/dir/URL/glob, 0 for webcam')
    parser.add_argument('--imgsz', '--img', '--img-size', type=int, default=640, help='inference size (pixels)')
    parser.add_argument('--overlap', type=int, default=100, help='sub image overlap size (pixels)')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.05, help='NMS IoU threshold')
    parser.add_argument('--max-det', type=int, default=1000, help='maximum detections per image')
    parser.add_argument('--remote', action='store_true', help='inference big remote images')    
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--view-img', action='store_true', help='show results')
    parser.add_argument('--save-pkl', action='store_true', help='save results to *.txt')
    parser.add_argument('--save_json', type=str,default='submit/aircraft_results.json' ,help='save json results')
    parser.add_argument('--save-crop', action='store_true', help='save cropped prediction boxes')
    parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 0 2 3')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--update', action='store_true', help='update all models')
    parser.add_argument('--project', default='runs/detect', help='save results to project/name')
    parser.add_argument('--name', default='exp', help='save results to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    parser.add_argument('--line-thickness', default=3, type=int, help='bounding box thickness (pixels)')
    parser.add_argument('--hide-labels', default=False, action='store_true', help='hide labels')
    parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences')
    parser.add_argument('--half', action='store_true', help='use FP16 half-precision inference')
    opt = parser.parse_args()
    print(opt)
    #check_requirements(exclude=('tensorboard', 'thop'))
    # import pdb;pdb.set_trace()
    det_path=detect(**vars(opt))
    #imglist=glob.glob(os.path.join(opt.source,'*.jpg'))
    #eval_remote(opt.annot_dir,'polygon',det_path,imglist,'ship',opt.iou_thres,opt.conf_thres,opt)

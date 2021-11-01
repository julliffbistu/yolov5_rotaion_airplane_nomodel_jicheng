import numpy as np
def class_thres(pred):
    conf_thres_A = 0.37
    conf_thres_B = 0.40
    conf_thres_C = 0.38
    conf_thres_D = 0.39
    conf_thres_E = 0.68
    conf_thres_F = 0.38
    conf_thres_G = 0.47
    conf_thres_H = 0.5
    conf_thres_I = 0.42
    conf_thres_J = 0.38
    conf_thres_K = 0.40
    l = []
    array_pred = np.array(pred)
    for arr in array_pred:
        if arr[-1] == 0:
            if arr[-2] < conf_thres_A:
                pass
            else:
                l.append(list(arr))
        if arr[-1] == 1:
            if arr[-2] < conf_thres_B:
                pass
            else:
                l.append(list(arr))
        if arr[-1] == 2:
            if arr[-2] < conf_thres_C:
                pass
            else:
                l.append(list(arr))
        if arr[-1] == 3:
            if arr[-2] < conf_thres_D:
                pass
            else:
                l.append(list(arr))
        if arr[-1] == 4:
            if arr[-2] < conf_thres_E:
                pass
            else:
                l.append(list(arr))
        if arr[-1] == 5:
            if arr[-2] < conf_thres_F:
                pass
            else:
                l.append(list(arr))
        if arr[-1] == 6:
            if arr[-2] < conf_thres_G:
                pass
            else:
                l.append(list(arr))
        if arr[-1] == 7:
            if arr[-2] < conf_thres_H:
                pass
            else:
                l.append(list(arr))
        if arr[-1] == 8:
            if arr[-2] < conf_thres_I:
                pass
            else:
                l.append(list(arr))
        if arr[-1] == 9:
            if arr[-2] < conf_thres_J:
                pass
            else:
                l.append(list(arr))
        if arr[-1] == 10:
            if arr[-2] < conf_thres_K:
                pass
            else:
                l.append(list(arr))
    return l

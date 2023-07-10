import numpy as np
import math
import cv2


def changeContrast(img):
    lab= cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l_channel)
    limg = cv2.merge((cl,a,b))
    enhanced_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    return enhanced_img

def rotate_image(image, angle):
    image_center = tuple(np.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    result = cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)
    return result

def compute_skew(src_img, is_center_limit):
    if len(src_img.shape) == 3:
        h, w, _ = src_img.shape
    elif len(src_img.shape) == 2:
        h, w = src_img.shape
    else:
        print('upsupported image type')
    img = cv2.medianBlur(src_img, 3)
    edges = cv2.Canny(img,  threshold1 = 30,  threshold2 = 100, apertureSize = 3, L2gradient = True)
    lines = cv2.HoughLinesP(edges, 1, math.pi/180, 30, minLineLength=w / 1.5, maxLineGap=h/3.0)
    if lines is None:
        return 1

    min_line = 100
    min_line_pos = 0
    for i in range (len(lines)):
        for x1, y1, x2, y2 in lines[i]:
            center_point = [((x1+x2)/2), ((y1+y2)/2)]
            if is_center_limit == 1:
                if center_point[1] < 5: # Remove short line
                    continue
            if center_point[1] < min_line:
                min_line = center_point[1]
                min_line_pos = i

    angle = 0.0
    nlines = lines.size
    cnt = 0
    for x1, y1, x2, y2 in lines[min_line_pos]:
        ang = np.arctan2(y2 - y1, x2 - x1)
        if math.fabs(ang) <= 30: 
            angle += ang
            cnt += 1
    if cnt == 0:
        return 0.0
    print(angle)
    return (angle / cnt)*180/math.pi

def deskew(src_img, is_change_constrast,is_center_limit):
    if is_change_constrast == 1:
        return rotate_image(src_img, compute_skew(changeContrast(src_img), is_center_limit))
    else:
        return rotate_image(src_img, compute_skew(src_img, is_center_limit))
    
if __name__ == '__main__':
    import cv2
    img = cv2.imread('crop.jpg')
    corrected_img = deskew(img,1,1)
    cv2.imshow('origin',img)
    cv2.imshow('rotate',corrected_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
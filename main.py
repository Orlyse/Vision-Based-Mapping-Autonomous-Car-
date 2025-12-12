import requests
import socket
import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import time
import py_comm
import csv

# Plan
# Run camera, take a picture every 3 seconds (robot moves in those 3 seconds)
# Using edge detection, estimate whether it is safe for the robot to move forward
# As the robot move for those 3 seconds, in the background
# Record all movements made and create a map with obstacles using
# recorded edges along the way and rough estimates of distance

ESP32_IP = "172.20.10.3"
SNAP_URL = f"http://{ESP32_IP}/capture"

def get_frame():
    r = requests.get(SNAP_URL, timeout=5)
    r.raise_for_status()

    img_array = np.frombuffer(r.content, np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    return frame

# save image
def save_image(img, name):
    dir = r'C:/Users/ineza/OneDrive/Documents/ME 399/camera_project'
    #   save_name = 'hallway_edges.jpg'
    save_path = os.path.join(dir, name)
    cv2.imwrite(save_path, img)

def manipulate_img(img):
    #   resize = cv2.resize(img, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_LINEAR)
    resize = cv2.resize(img, (500, 500))
    resize = cv2.flip(resize, 0)
    resize = cv2.flip(resize, 1)
    
    # convert to gray scale
    gray = cv2.cvtColor(resize, cv2.COLOR_BGR2GRAY)
    kernel_size = 1     # low values seem to create straighter lines
    
    gray_f = gray.astype(np.float32)

    mean = cv2.blur(gray_f, (kernel_size, kernel_size))
    sq_mean = cv2.blur(np.square(gray_f), (kernel_size, kernel_size))
    variance = sq_mean - np.square(mean)
    stddev = np.sqrt(np.maximum(variance, 0))
    
    #   normalize to [0, 255]
    texture_map = cv2.normalize(stddev, None, 0, 255, cv2.NORM_MINMAX)
    texture_map = texture_map.astype(np.uint8)

    # Threshold, high texture
    _, texture_map = cv2.threshold(texture_map, 100, 255, cv2.THRESH_BINARY)    # play around with thresh to capture more/less texture

    # Separate smooth regions
    smooth_reg = cv2.bitwise_not(texture_map)    

    # blur and detect edges
    blurred = cv2.GaussianBlur(resize, (5, 5), 0)   
    #   sobelx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
    #   sobely = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
    #   grad_mag = cv2.magnitude(sobelx, sobely)
    grad_mag = cv2.Canny(blurred, 100, 200)

    # shape
    g_sh = grad_mag.shape
    
    # convert gradient to uint8
    grad_mag = cv2.convertScaleAbs(grad_mag)
    smooth_reg = cv2.resize(smooth_reg, (g_sh[1], g_sh[0]))
    mask = smooth_reg.astype(np.uint8)
    
    filtered_edges = cv2.bitwise_and(grad_mag, grad_mag, mask=mask)
    
    cv2.imshow('display', filtered_edges)

    return filtered_edges

#   im = cv2.imread(r'C:/Users/ineza/OneDrive/Documents/ME 399/camera_project/room1.jpg')
#   frame = manipulate_img(im)
#   cv2.imshow('test', frame)


# determine safety for motion
def check_edge_location(img):
    Im_shape = img.shape
    h = Im_shape[0]
    w = Im_shape[1]
    h_bot = int(h*0.5)
    mid_w = int(w/2)
    quat = int(0.25*w)
    quat1 = int(0.75*w)

    bot_half = img[h_bot:h, :]
    left_half = img[h_bot:h, 0:mid_w]
    right_half = img[h_bot:h, mid_w:]
    front = img[h_bot:h, quat:quat1]
    
    #   cv2.imshow('display', front)

    return np.sum(left_half), np.sum(front), np.sum(right_half)

def move_dir( l, f, r):
    
    #   1: move forward
    #   0: turn left
    #   -1: turn right
    
    if f < 100000:  # no edge front
        return 1
    elif l < 100000:
        return 0
    elif r < 100000:
        return -1
    else:
        print(f'no available path, moving forward.\n')
        return 1
    
FORWARD_PWM = 200
TURN_PWM = 175

def robot_move(dir):
    '''
    inputr = input('r:')
    inputl = input('l:')

    py_comm.send_pwm(int(inputl), int(inputr))
    '''
    if dir == 1:    # move forward
        py_comm.send_pwm(FORWARD_PWM, FORWARD_PWM)
        #   time.sleep(0.2)
    elif dir == -1:
        py_comm.send_pwm(TURN_PWM, 0)
        #   time.sleep(0.2)
    else:
        py_comm.send_pwm(0, TURN_PWM)
        #   time.sleep(0.2)
    

counter = 0
CONTROL_PERIOD = 2.0
FORWARD_DUR = 2.0
TURN_DUR = 0.4
map = []

while True:

    t0 = time.time()
    frame = get_frame()

    print(f'new frame {counter} obtained\n')
    counter += 1

    if frame is None:
        print("Failed to decode frame")
        break
    
    man_image = manipulate_img(frame)

    print(f'counter = {counter}\n')
    if counter == 5:
        save_image(man_image, 'cam_image.jpg')

    l, f, r = check_edge_location(man_image)
    dir = move_dir(l, f, r)
    map.append(dir) 

    print(f'move direction = {dir}\n')

    if dir == 1:
        robot_move(dir)
        time.sleep(FORWARD_DUR)
    else:
        robot_move(dir)
        time.sleep(TURN_DUR)
        py_comm.send_pwm(0, 0)

        leftover = CONTROL_PERIOD - (time.time() - t0)
        if leftover > 0:
            time.sleep(leftover)

    #   cv2.imshow("Snap", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print(f'Leaving loop\n')
        break

    elapsed = time.time() - t0
    remaining = CONTROL_PERIOD - elapsed
    if remaining > 0:
        time.sleep(remaining)

with open("map.csv", 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(map)
    

# close windows
cv2.waitKey(0)
cv2.destroyAllWindows()
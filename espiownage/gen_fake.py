
# Generates 'fake' images akin to the ESPI images of steelpan drums, from
# https://www.zooniverse.org/projects/achmorrison/steelpan-vibrations
#

# num_rings can be between 0 and 11.  0 means there is no antinode there
# You can also have num_antinodes=0, but this produces more of a 'skewed' dataset
#   than if you use num_rings=0 instead and let num_antinodes=1

# note that this doesn't require any GPU usage, just a lot of disk usage

# Added multiprocesing: runs lots of processes to cut execution time down

from fastcore.script import *

import numpy as np
import cv2
import random
import os
import time
from functools import partial
import multiprocessing as mp
from espiownage.core import *

import sys, traceback
from shutil import get_terminal_size
import glob

winName = 'ImgWindowName'
imWidth = 512
imHeight = 384

meta_extension = ".csv"     # file extension for metadata files

# Define some colors: openCV uses BGR instead of RGB
blue = (255,0,0)
red = (0,0,255)
green = (0,255,0)
white = (255)
black = (0)
grey = (128)

blur_prob = 0.3    # probability that an image gets blurred

min_line_width = 4  # number of pixels per each ring (dark-light pair)

pad = "       "

def bandpass_mixup(img_fake, path_real=os.path.expanduser('~/datasets/espiownage-data/images/')):
    '''
    For more realistic-looking images (still not as good as StyleGAN),
    replace low & high frequency components ('background')
    of fake images using those components from real images
    '''

    # get a random background from the group of 'true' images
    file_true = random.choice(glob.glob(path_real+'/*.png'))
    img_true = cv2.imread(file_true, cv2.IMREAD_GRAYSCALE)
    # maybe flip the image
    flipchoice = np.random.choice([-1,0,1,2])
    if (flipchoice != 2):
        img_true = cv2.flip(img_true, flipchoice)

    # take fourier transforms of fake and true images
    dft_true = cv2.dft(np.float32(img_true),flags = cv2.DFT_COMPLEX_OUTPUT)
    dft_shift_true = np.fft.fftshift(dft_true)    # center the "dc" part of image

    dft_fake = cv2.dft(np.float32(img_fake),flags = cv2.DFT_COMPLEX_OUTPUT)
    dft_shift_fake = np.fft.fftshift(dft_fake)    # center the "dc" part of image

    # Set up a filter: Keep the Lows and the Highs
    # create a rectagular mask first, center square is 1, remaining all zeros. LPF
    rows, cols = img_fake.shape
    crow,ccol = rows//2 , cols//2
    wl, wh = 8, 0     #  width for LPF and HPF respectively
    mask = np.zeros((rows,cols,2),np.uint8)
    mask[crow-wl:crow+wl, ccol-wl:ccol+wl] = 1   # LPF
    if wh > 0:
        mask[0:wh,:] = 1    # HPF
        mask[-wh:,:] = 1    # HPF
        mask[:,0:wh] = 1    # HPF
        mask[:,-wh:] = 1    # HPF
    fshift = np.random.rand()*3*dft_shift_true*mask + (1-mask)*dft_shift_fake   # L/H from true, mids from fake

    # inverse DFT
    f_ishift = np.fft.ifftshift(fshift)
    img_back = cv2.idft(f_ishift)
    img_back = cv2.magnitude(img_back[:,:,0],img_back[:,:,1])
    cv2.normalize(img_back, img_back, 0, 255, cv2.NORM_MINMAX)

    return np.clip(img_back, 0, 255)


def blur_image(img, kernel_size=7):
    if (0==kernel_size):
        return img
    new_img = img#.copy()
    new_img = cv2.GaussianBlur(img,(kernel_size,kernel_size),0)
    return new_img


def draw_waves(img):  # TODO make intensity vary smoothly
    xs = np.arange(0, imWidth)
    ys = np.arange(0, imHeight)

    amp = random.randint(10,200)
    x_wavelength = random.randint(100,int(imWidth/2))
    thickness = random.randint(15,40)
    slope = 3*(np.random.rand()-.5)
    y_spacing = random.randint(thickness + thickness*int(np.abs(1.5*slope)), int(imHeight/3))
    numlines = 60+int(imHeight/y_spacing)

    for j in range(numlines):   # skips y_spacing in between drawings
        y_start = j*y_spacing - img.shape[1]*abs(slope)
        pts = []
        for i in range(len(xs)):
            pt = [ int(xs[i]), int(y_start + slope*xs[i]+ amp * np.cos(xs[i]/x_wavelength))]
            pts.append(pt)
        pts = np.array(pts, np.int32)
        cv2.polylines(img, [pts], False, black, thickness=thickness)
    return


# wrapper for legacy code with different calling sequence than newer code
def get_ellipse_box(center, axes, angle):  # converts ellipse to bounding box
    return ellipse_to_bbox( center[0], center[1], axes[0], axes[1], angle)



def draw_rings(img,center,axes,angle=45,num_rings=5.5):  # TODO make intensity vary smoothly
    num_drawrings, thickness = max(axes), 1
    if num_rings < 0.2: num_rings = 0.2+0.2*np.random.rand()
    phase = 2*np.pi*np.random.rand()
    minc, maxc = random.randint(0,60), random.randint(150,250)
    for j in range(num_drawrings):
        color = int(minc + (maxc-minc)*np.sin(2*np.pi*num_rings * j/num_drawrings + phase))
        thisring_axes = [axes[i] * (j+1)*1.0/(num_drawrings+1) for i in range(len(axes))]
        ellipse = draw_ellipse(img,center,thisring_axes,angle,color=color, thickness=thickness)
    return ellipse   # returns outermost ellipse




def does_overlap( a, b):
    if (a[2] < b[0]): return False # a is left of b
    if (a[0] > b[2]): return False # a is right of b
    if (a[3] < b[1]): return False # a is above b
    if (a[1] > b[3]): return False # a is below b
    return True

def does_overlap_previous(box, boxes_arr):
    # returns true if bounding box of new ellipse (ignoring angle) would
    # overlap with previous ellipses
    if ([] == boxes_arr):
        return False
    for i in range(len(boxes_arr)):
        #print("                boxes_arr[",i,"] = ",boxes_arr[i])
        if (does_overlap( box, boxes_arr[i])):
            return True
    return False



def draw_antinodes(img,num_antinodes=1):
    boxes_arr = []
    caption = ""

    if (num_antinodes==0):
        caption = "{0},{1},{2},{3},{4},{5}".format( 0,  0,    0,  0,    0,   0.0)  # as per @achmorrison's format

    for an in range(num_antinodes): # draw a bunch of antinodes

        axes = (random.randint(15,int(imWidth/3.5)), random.randint(15,int(imHeight/3.5)))   # semimajor and semiminor axes of ellipse
        axes = sorted(axes, reverse=True)   # do descending order, for definiteness. i.e. so a > b


        # TODO: based on viewing real images: for small antinodes, number of rings should also be small
        max_rings = min(axes[1] // 8, 11)                  # '8' chosen from experience looking at the data
        num_rings = np.random.uniform(low=0.5,high=11.0)            # well say that an antinode has at least 1 ring

        # make sure line width isn't too small to be resolved
        if (axes[1]/num_rings < min_line_width):
            num_rings = axes[1] / min_line_width

        center = (random.randint(axes[0], imWidth-axes[0]),
            random.randint(axes[1], imHeight-axes[1]))
        angle = random.randint(1, 179)       # ellipses are symmetric after 180 degree rotation
        box = get_ellipse_box(center, axes, angle)

        # make sure they don't overlap, and are in bounds of image
        # TODO: the following random placement is painfully inefficient
        trycount, maxtries = 0, 2000
        while (   ( (True == does_overlap_previous(box, boxes_arr))
            or (box[0]<0) or (box[2] > imWidth)
            or (box[1]<0) or (box[3] > imHeight)  ) and (trycount < maxtries) ):
            trycount += 1
            # if there's a problem, then generate new values - "Re-do"
            axes = (random.randint(25, int(imWidth/3)), random.randint(25, int(imHeight/3)))
            axes = sorted(axes, reverse=True)   # do descending order
            # make sure line width isn't too small to be resolved
            if (axes[1]/num_rings < min_line_width):
                num_rings = axes[1] / min_line_width

            center = (random.randint(axes[0], imWidth-axes[0]),
                random.randint(axes[1], imHeight-axes[1]))
            angle = random.randint(1, 180)
            box = get_ellipse_box(center, axes, angle)

        success = False
        if (trycount < maxtries):
            draw_rings(img, center, axes, angle=angle, num_rings=num_rings)
            this_caption = "{0},{1},{2},{3},{4},{5}".format(center[0], center[1],axes[0], axes[1], angle, round(num_rings,1))
            if '0,0,0,0' not in this_caption: success = True
        else:   # just skip this antinode
            print("\n\r",pad,":WARNING Can't fit an=",an,"\n",sep="",end="\r")
            this_caption = ""

        if (success):               # don't add blank lines, only add lines for success
            if (an > 0):
                caption+="\n"
            caption += this_caption
            boxes_arr.append(box)
    return img, caption



def handle_one_file(outdir, framenum):
    print("framenum = ",framenum)

    np_dims = (imHeight, imWidth, 1)     # for numpy, image dimensions are reversed
    img = 128*np.ones(np_dims, np.uint8)

    draw_waves(img)   # this is the main bottleneck, execution-time-wise

    max_antinodes = 6
    num_antinodes= random.randint(1,max_antinodes)
    img, caption = draw_antinodes(img, num_antinodes=num_antinodes)

    if (np.random.random() <= blur_prob): # blur image a bit
        blur_ksize = random.choice([3,5])
        img = blur_image(img, kernel_size=blur_ksize)

    # post-blur noise
    noise = cv2.randn(np.zeros(np_dims, np.uint8),40,40); # normal dist, mean 40 std 40
    img = cv2.add(img, noise)


    # further degrade image: drop some pixels
    mask = np.random.choice([0,1],size=img.shape).astype(np.float32)
    img = img*mask

    # finally replace background using real data
    img = bandpass_mixup(img)

    prefix = 'steelpan_'+str(framenum).zfill(7)
    cv2.imwrite(outdir+'/images/'+prefix+'.png',img)
    with open(outdir+'/annotations/'+prefix+meta_extension, "w") as text_file:
        text_file.write(caption+'\n')
    return


@call_parse
def gen_fake(
    n:Param("Number of images to generate", int)=2000,
    outdir:Param("Directory to write to",str)='espiownage-fake',
    ):
    "Generates fake ESPI-like images"

    random.seed(1)   # for reproducibility
    np.random.seed(1)

    mkdir_if_needed(outdir)
    mkdir_if_needed(outdir+'/images')
    mkdir_if_needed(outdir+'/annotations')

    parallel = True  # want this on, this one's slow
    if not parallel:
        for framenum in range(n):
            handle_one_file(outdir, framenum)
    else:
        wrapper = partial(handle_one_file, outdir)
        pool = mp.Pool(mp.cpu_count())
        results = pool.map(wrapper, range(n))
        pool.close()
        pool.join()
    return

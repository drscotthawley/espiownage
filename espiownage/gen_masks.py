
from fastcore.script import *
from pathlib import Path
import glob
import os
import pandas as pd
import numpy as np
import cv2
from espiownage.core import *
from functools import partial
import multiprocessing as mp

""" Note that (normally) we don't care about the actual images. we're just generating
    image masks from the annotations
"""

def ring_float_to_mask_int(rings:float, step=0.1):
    """Ring value rounded to mask value; rounded to nearest step size"""
    return round(rings/step)

all_colors = {0}

def handle_one_file(meta_file_list, # list of all the csv files
    mask_dir,                # output directory, where to write mask files to
    step,                   # resolution of (float) rings, when converting to int
    #imglinks,               # boolean on whether or not to create links to original images
    i,                      # index of which meta file we'll read from
    height=512, width=384):  # image dimensions
    global all_colors

    meta_file = meta_file_list[i]
    col_names = ['cx', 'cy', 'a', 'b', 'angle', 'rings']
    df = pd.read_csv(meta_file, header=None, names=col_names)

    # progress message
    mask_path = meta_to_mask_path(meta_file,mask_dir=mask_dir)
    print(f"{i}/{len(meta_file_list)}: meta_file = {meta_file}, mask_path = {mask_path} ",flush=True) #", df = \n",df.to_string(index=False))

    df.drop_duplicates(inplace=True)  # sometimes the data from Zooniverse has duplicate rows
    img = np.zeros((width, height), dtype=np.uint8)  # blank black image, dimensions are wonky
    for index, row in df.iterrows() :
        [cx, cy, a, b, angle] = [int(round(x)) for x in [row['cx'], row['cy'], row['a'], row['b'], row['angle']]]
        rings = row['rings']
        a, b, angle = fix_abangle(a,b,angle)
        if (rings > 0):
            color =ring_float_to_mask_int(rings, step=step)
            all_colors = all_colors.union({color})
            img = draw_ellipse(img, (cx,cy), (a,b), angle, color=color, filled=True)

    #all_colors = all_colors.union(set(np.array(img).flatten()))  # super sanity check but slow
    cv2.imwrite(str(mask_path), img)
    return img



@call_parse
def gen_masks(files:Param("Wildcard name for all CSV files to edit", str)='annotations/*.csv',
    maskdir:Param("Directory to write segmentation masks to",str)='masks/',
    step:Param("Step size / resolution / precision of ring count",float)=0.1,
    #imglinks:Param("Generate links to original images?", store_true)
    ):
    global all_colors

    mkdir_if_needed(maskdir)

    "Generate segmentation masks for all annotations"
    files = ''.join(files)
    meta_file_list = sorted(glob.glob(files))

    parallel = False
    if not parallel:  # it's not that slow, really
        for i in range(len(meta_file_list)):
            handle_one_file(meta_file_list, maskdir, step, i)
        print("all_colors = ",sorted(list(all_colors))) # Very handy 
    else:
        # parallel processing
        wrapper = partial(handle_one_file, meta_file_list, maskdir, step)
        pool = mp.Pool(mp.cpu_count())
        results = pool.map(wrapper, range(len(meta_file_list)))
        pool.close()
        pool.join()

    return

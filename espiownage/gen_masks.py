
from fastcore.script import * 
from pathlib import Path
import glob
import os, shutil
import pandas as pd
import numpy as np
import cv2
from PIL import Image
from espiownage.core import *
from functools import partial
import multiprocessing as mp
import sys

""" Note that (normally) we don't care about the actual images. we're just generating
    image masks from the annotations
"""


imgbank, ann_img_dir = "images/", "annotated_images/"
all_colors = {0}

def handle_one_file(meta_file_list, # list of all the csv files
    mask_dir,                # output directory, where to write mask files to
    step,                   # resolution of (float) rings, when converting to int
    #imglinks,               # boolean on whether or not to create links to original images
    allone,                 # set all values to one for non-background
    cp_ann_imgs,            # hack to make directory of only images for which annotations exist
    quiet,                   # don't print many status messages
    i,                      # index of which meta file we'll read from
    height=512, width=384):  # image dimensions
    global all_colors, ann_img_dir

    meta_file = meta_file_list[i]
    col_names = ['cx', 'cy', 'a', 'b', 'angle', 'rings']
    df = pd.read_csv(meta_file, header=None, names=col_names)

    # progress message
    mask_path = meta_to_mask_path(meta_file, mask_dir=mask_dir+'/')
    if not quiet:
        print(f"{i}/{len(meta_file_list)}: meta_file = {meta_file}, mask_path = {mask_path} ",flush=True)

    df.drop_duplicates(inplace=True)  # sometimes the data from Zooniverse has duplicate rows
    img = np.zeros((width, height), dtype=np.uint8)  # blank black image, dimensions are wonky
    for index, row in df.iterrows() :
        [cx, cy, a, b, angle] = [int(round(x)) for x in [row['cx'], row['cy'], row['a'], row['b'], row['angle']]]
        rings = round(float(row['rings']),2)
        a, b, angle = fix_abangle(a,b,angle)
        if (rings > 0):
            if rings > 11: # saw an error once
                print(f"Sever warning for file {meta_file}: rings = {rings}.  Aborting")
                sys.exit(1)
            color = 1 if allone else ring_float_to_class_int(rings, step=step)
            all_colors = all_colors.union({color})
            img = draw_ellipse(img, (cx,cy), (a,b), angle, color=color, filled=True)

    #all_colors = all_colors.union(set(np.array(img).flatten()))  # super sanity check but slow
    # cv2.imwrite(str(mask_path), img)  Don't write as cv2, write as PIL
    pil_image = Image.fromarray(img)
    pil_image = pil_image.save(str(mask_path))


    if cp_ann_imgs:
        src_img = meta_to_img_path(meta_file)
        dest_img = ann_img_dir+os.path.basename(src_img)
        shutil.copyfile(src_img, dest_img)

    return img



@call_parse
def gen_masks(
    allone:Param("All objects get assigned to class 1", store_true),
    quiet:Param("Suppress output log", store_true),
    cp_ann_imgs:Param("make directory of only images for which annotations exist (to annotated_images/)", store_true),
    files:Param("Wildcard name for all CSV files to edit", str)='annotations/*.csv',
    maskdir:Param("Directory to write segmentation masks to",str)='masks/',
    step:Param("Step size / resolution / precision of ring count",float)=1,
    ):
    "Generate segmentation masks for all annotations"
    global all_colors, ann_img_dir

    mkdir_if_needed(maskdir)
    if cp_ann_imgs: mkdir_if_needed(ann_img_dir)

    files = ''.join(files)
    meta_file_list = sorted(glob.glob(files))

    parallel = True  # could leave off. it's not that slow, really
    if not parallel:
        for i in range(len(meta_file_list)):
            handle_one_file(meta_file_list, maskdir, step, allone, cp_ann_imgs, quiet, i)
        print("all_colors = ",sorted(list(all_colors))) # Very handy
    else:
        # parallel processing
        wrapper = partial(handle_one_file, meta_file_list, maskdir, step, allone, cp_ann_imgs, quiet)
        pool = mp.Pool(mp.cpu_count())
        results = pool.map(wrapper, range(len(meta_file_list)))
        pool.close()
        pool.join()

    return

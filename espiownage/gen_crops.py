
from fastcore.script import *
from pathlib import Path
import glob
import os
import pandas as pd
import numpy as np
import cv2
from PIL import Image
from espiownage.core import *
from functools import partial
import multiprocessing as mp
import sys

""" Generates cropped images of individual antinodes using annotations
"""

def handle_one_file(meta_file_list, # list of all the csv files
    outdir,                # output directory, where to write mask files to
    i,                      # index of which meta file we'll read from
    height=512, width=384):  # image dimensions

    meta_file = meta_file_list[i]
    print(f"{i}/{len(meta_file_list)}: meta_file = {meta_file}",flush=True)

    img_path = meta_to_img_path(meta_file)
    img = Image.open(img_path)

    # read meta csv file for all rings
    col_names = ['cx', 'cy', 'a', 'b', 'angle', 'rings']
    df = pd.read_csv(meta_file, header=None, names=col_names)
    df.drop_duplicates(inplace=True)  # sometimes the data from Zooniverse has duplicate rows
    for index, row in df.iterrows() :
        [cx, cy, a, b, angle] = [int(round(x)) for x in [row['cx'], row['cy'], row['a'], row['b'], row['angle']]]
        rings = round(float(row['rings']),2)
        a, b, angle = fix_abangle(a,b,angle)
        if (rings > 0):
            bb = ellipse_to_bbox(cx, cy, a, b, angle)
            if bb is not None:
                img_cropped = crop_to_bbox(img, bb)
                if img_cropped is not None:
                    out_file = outdir+'/'+str(Path(meta_file).stem)+f"_{bb[0]}_{bb[1]}_{bb[2]}_{bb[3]}_{rings}.png"
                    img_cropped.save(out_file)
    return



@call_parse
def gen_crops(
    files:Param("Wildcard name for all CSV files to edit", str)='annotations/*.csv',
    outdir:Param("Directory to write output cropped images to",str)='crops/',
    ):
    "Generate cropped images for all annotations"

    mkdir_if_needed(outdir)

    files = ''.join(files)
    meta_file_list = sorted(glob.glob(files))

    parallel = True  # not too slow sequential but parallel=True is good
    if not parallel:
        for i in range(len(meta_file_list)):
            handle_one_file(meta_file_list, outdir, i)
    else:
        # parallel processing
        wrapper = partial(handle_one_file, meta_file_list, outdir)
        pool = mp.Pool(mp.cpu_count())
        results = pool.map(wrapper, range(len(meta_file_list)))
        pool.close()
        pool.join()

    return

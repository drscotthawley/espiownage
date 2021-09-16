
from fastcore.script import *
from pathlib import Path
import glob
import os
import pandas as pd
import numpy as np
import cv2
from PIL import Image
import json
from espiownage.core import *
#from functools import partial
#import multiprocessing as mp

""" Generates bounding box info from our edited CSV files.  It outputs in two formats:
    1. .json: COCO(-TINY)-style bbox JSON file
    2. .csv: All the annotations in one big long CSV: see this notebook where we use this format:
        https://colab.research.google.com/drive/1bi8PYLFexoEcNKRClul0X3U6JRLKaH7M?usp=sharing
"""

def gen_coco_json(meta_file_list, bboxdir, step, reg, maxrings=11):
    """ sample file format is a dict like...
    sample_coco_dict = {
        "categories": [{"id": 62, "name": "chair"}, {"id": 63, "name": "couch"}, {"id": 72, "name": "tv"}, {"id": 75, "name": "remote"}, {"id": 84, "name": "book"}, {"id": 86, "name": "vase"}],
        "images": [{"id": 542959, "file_name": "000000542959.jpg"}, {"id": 129739, "file_name": "000000129739.jpg"}],
        "annotations": [{"image_id": 542959, "bbox": [32.52, 86.34, 8.53, 9.41], "category_id": 62}, {"image_id": 542959, "bbox": [98.12, 110.52, 1.95, 4.07], "category_id": 86}, {"image_id": 542959, "bbox": [91.28, 51.62, 3.95, 5.72], "category_id": 86}, {"image_id": 542959, "bbox": [110.48, 110.82, 14.55, 15.22], "category_id": 62}, {"image_id": 542959, "bbox": [96.63, 50.18, 18.67, 13.46], "category_id": 62}, {"image_id": 542959, "bbox": [0.69, 111.73, 11.8, 13.06], "category_id": 62}]
    }"""
    json_filename = bboxdir+'/coco_bboxes.json'
    print(f"Generating COCO-style JSON file {json_filename} ...")
    coco_dict = {}

    # categories
    if reg:
        print('Regression model: 1 class, called "rings"')
        coco_dict["categories"] = [{"id": 0, "name": "rings"}] # probably won't work
    else:
        coco_dict["categories"] = [{"id": x, "name":str((x+1)*step)} for x in range(int(round(maxrings/step)))]

    # images
    coco_dict["images"] = [{"id":i, "file_name":os.path.basename(str(meta_to_img_path(x)))} for i,x in enumerate(meta_file_list)]

    # annotations
    ann_list = []
    for i, meta_file in enumerate(meta_file_list):
        this_df = meta_to_df(meta_file)
        image = os.path.basename(str(meta_to_img_path(meta_file)))
        #print("meta_file = ",meta_file)
        for index, row in this_df.iterrows():
            [cx, cy, a, b, angle] = [x for x in [row['cx'], row['cy'], row['a'], row['b'], row['angle']]]
            bbox = ellipse_to_bbox(cx, cy, a, b, angle, coco=True)
            rings = round(float(row['rings']),2)
            category_id = rings if reg else int(round(maxrings/step))
            this_ann = {"image_id":image, "bbox": bbox, "category_id":category_id}
            ann_list = ann_list + [this_ann]
    coco_dict["annotations"] = ann_list

    #print("coco_dict =\n",coco_dict)
    with open(json_filename, 'w') as fp:
        json.dump(coco_dict, fp)
    return


def gen_long_csv(files_str, meta_file_list, bboxdir, step, reg, maxrings=11):
    out_csv_filename = bboxdir+'/annotations.csv'
    print(f"Generating long CSV {out_csv_filename} ...")

    width, height = 512, 384  # image dims
    final_col_names = ['filename','width', 'height', 'label', 'xmin', 'ymin', 'xmax', 'ymax']

    # Goal: make one big long DataFrame and then write it
    ann_list = []
    for i, meta_file in enumerate(meta_file_list):
        this_df = meta_to_df(meta_file)
        image_file = os.path.basename(str(meta_to_img_path(meta_file)))
        this_df['filename'] = image_file

        for index, row in this_df.iterrows(): #convert to bboxes
            [cx, cy, a, b, angle] = [x for x in [row['cx'], row['cy'], row['a'], row['b'], row['angle']]]
            bbox = ellipse_to_bbox(cx, cy, a, b, angle, coco=False)
            rings = round(float(row['rings']),2)
            label = rings if reg else ring_float_to_class_int(rings)
            line_list = [image_file, width, height, label, bbox[0], bbox[1], bbox[2], bbox[3]]
            ann_list.append(line_list)

    new_df = pd.DataFrame(ann_list, columns=final_col_names)
    new_df = new_df[final_col_names]  # just to force ordering
    new_df.to_csv(out_csv_filename, index=False)
    return


@call_parse
def gen_bboxes(
    reg:Param("Set this for regression model (1 class, no steps)", store_true),
    files:Param("Wildcard name for all (ellipse) CSV files to read", str)='annotations/*.csv',
    bboxdir:Param("Directory to write bboxes to",str)='bboxes',
    step:Param("For classification model: Step size / resolution / precision of ring count",float)=0.5,
    ):

    mkdir_if_needed(bboxdir)

    files = ''.join(files)  # convert to str
    meta_file_list = sorted(glob.glob(files)) # list of all annotation .csv files for ellipses

    gen_long_csv(files, meta_file_list, bboxdir, step, reg)
    gen_coco_json(meta_file_list, bboxdir, step, reg)

    return

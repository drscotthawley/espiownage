
from fastcore.script import *
from pathlib import Path
import glob
import os

@call_parse
def gen_masks(dir:str,  # the directory where images & CSVs are
    ):
    "Generate segmentation masks for all images in dir"
    print("dir=",dir)
    csv_list = glob.glob(dir+'/*.csv')
    for csv_filename in csv_list:  # TODO: map this in parallel
        csv_path = Path(csv_filename)
        img_path = os.path.splitext(csv_path)[0]+'.png'
        mask_path = img_path = os.path.splitext(csv_path)[0]+'_P.png'
        print("csv_path, img_path = ",csv_path, img_path, mask_path)
    return

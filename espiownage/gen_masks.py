
from fastcore.script import *
from pathlib import Path
import glob
import os
import pandas as pd

# note that we don't care

@call_parse
def gen_masks(files:Param("Wildcard name for all CSV files to edit", str)='annotations/*.csv',
    maskdir:Param("Directory to write segmentation masks to",str)='masks/',
    ):
    "Generate segmentation masks for all annotations"
    files = ''.join(files)
    meta_file_list = sorted(glob.glob(files))

    for meta_file in meta_file_list:  # TODO: map this in parallel
        csv_path = Path(meta_file)
        mask_path = Path(maskdir + csv_path.stem+'_P.png')  # _P because that's what CAMVID dataset does
        print("csv_path, img_path = ",csv_path, mask_path)
        df = pd.read_csv(csv_path)
    return

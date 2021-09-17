
from fastcore.script import *
from pathlib import Path
import glob
import os
import numpy as np
from espiownage.core import *
import shutil
#from functools import partial
#import multiprocessing as mp

""" Grabs most recent version of annotations from various "annotations*" directories
"""




@call_parse
def grab_recent(
    dirs:Param("annotation directories check", str)='annotations*',
    dest:Param("Directory to write new annotations to",str)='recent_annotations',
    ):


    dirs = ''.join(dirs)  # convert to str
    print("dirs = ",dirs)
    dir_list = sorted(glob.glob(dirs)) # list of all annotation .csv files for ellipses
    print(dir_list)
    main_dir = dir_list[0]
    meta_files = [os.path.basename(x) for x in sorted(glob.glob(main_dir+'/'+'*.csv'))]
    recent_files = []
    more_recent_than_orig_count = 0
    for file in meta_files:
        time = -20.0
        recent_file = ''
        more_recent = 0
        for i, dir in enumerate(dir_list):
            full_filename = dir+'/'+file
            if os.path.exists(full_filename):
                this_time = os.path.getmtime(full_filename)
                if  this_time > time:
                    time, recent_file = this_time, full_filename
                    if i>0: more_recent = 1
        more_recent_than_orig_count += more_recent
        recent_files.append(recent_file)

    mkdir_if_needed(dest)

    for src_file in recent_files:
        dest_file =  dest+'/'+os.path.basename(src_file)
        print("src_file, dest_file =",src_file, dest_file)
        shutil.copyfile(src_file, dest_file)

    print(f"{len(recent_files)} most recent files. {more_recent_than_orig_count} more recent than original.")

    return

#! /usr/bin/env python3
"""
This produces bounding boxes and "existence" objects (i.e. all of the same class = "object")
from the rotated ellipses.  For use in testing with other object detector codes.
"""
import pandas as pd
import numpy as np
import json
import os
from shutil import copy2
import errno
import sys
from espiownage.core import *


datapath = '/home/shawley/datasets/'


use_andrews_raw_data = False
if use_andrews_raw_data:
    # generate big csv based on my own edits
    my_data_dir = datapath + 'parsed_zooniverse_steelpan/'
    # Inputs:
    #in_filename = 'zooniverse_labeled_dataset.csv'   # input CSV filename
    #in_filename = datapath+'average_all-good-ellipses-five_or_more-072420.csv' # input CSV filename
    in_filename = datapath+'average_good_ellipses_bad_values_removed.csv' # input CSV filename


    # @achmorrison:  "The order of each row is: x, y, filename, fringe_count, rx, ry, angle"
    col_names = ['cx', 'cy', 'filename', 'rings', 'a', 'b', 'angle']

    print("Reading metadata file",in_filename)
    df = pd.read_csv(in_filename, names=col_names) # no header

else:   # use my cleaned data of individuals csvs instead of morrison's big csv

    in_filename = '/tmp/big_steelpan_csv.csv'
    execstr = "awk '{print FILENAME, $0}' /home/shawley/datasets/cleaned_zooniverse_steelpan/*.csv | sed 's/csv/png,/g' | sed 's/\/home\/shawley\/datasets\/cleaned_zooniverse_steelpan\///g' > " + in_filename
    os.system(execstr)
    col_names = ['filename','cx', 'cy', 'a', 'b', 'angle', 'rings']
    df = pd.read_csv(in_filename, names=col_names) # no header

df.drop_duplicates(inplace=True)  # drop duplicate rows
df.dropna(inplace=True)           # drop rows containing NaNs
df = df[(df[['rings']] >= 1e-6).all(axis=1)]  # drop rows where ring count is zero
df = df.reset_index(drop=True)   # renumber indices after dropping rows
df['filename'] = [x.replace('.bmp','') for x in df['filename']]  # remove '.bmp' from filenames
n = df.shape[0] # len(df.index) # number rows
print('df = ',df)
print("n = ",n)

# Convert to bboxes
width, height = 512, 384
boxinfo = [ellipse_to_bb(row[0],row[1],row[2],row[3],row[4],width=width,height=height) for row in zip(df['cx'],df['cy'],df['a'],df['b'],df['angle'])]
#print("boxinfo = ",boxinfo)
box_df = pd.DataFrame(boxinfo, columns=['xmin', 'ymin', 'xmax', 'ymax'])
print("box_df = ",box_df)
print("box_df.shape[0] = ",box_df.shape[0])

# new dataframe, following format of https://airctic.com/0.7.0/custom_parser/
new_df = pd.concat([df, box_df], axis=1)
print("after concat, new_df = ",new_df)
n = new_df.shape[0] # len(df.index) # number rows
new_df['width'] = [width]*n
new_df['height'] = [height]*n
# two choices for labels:
if True:
    new_df['label'] = ['object']*n # group as all one class (called "object")
else:  # or group by integer bins of ring counts. NOTE: this goes very poorly, training-wise!
    new_df['label'] = df['rings'].round().astype(int).astype(str) + '_rings'

new_col_names = ['filename','width', 'height', 'label', 'xmin', 'ymin', 'xmax', 'ymax']
new_df = new_df[new_col_names]
print("new_df = ",new_df)

out_filename = datapath+'zooniverse_bounding_boxes.csv'
print("Writing to new file",out_filename)
new_df.to_csv(out_filename, index=False)

if True: # normally don't do this.
    print("One more thing: Copy files over for packaging")
    imgpath = datapath+'zooniverse_steelpan/'  # directory where ALL images are stored (e.g. in lecun:datasets/+this)
    for f in new_df['filename']:
        os.system(f'/bin/cp {imgpath}/{f} /tmp/spnet_sample-master/images/')
    os.system(f'/bin/cp {out_filename} /tmp/spnet_sample-master/annotations.csv')
    os.system("cd /tmp/; rm -f spnet_sample-master.zip; zip -r spnet_sample-master.zip spnet_sample-master/; scp spnet_sample-master.zip hedges.belmont.edu:public_html/")

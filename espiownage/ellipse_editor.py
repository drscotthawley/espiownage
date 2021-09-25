#! /usr/bin/env python3

'''
Ellipse editor, standalone utility for use with steelpan images & annotations
Author: Scott H. Hawley  License: MIT (below)

Reads a CSV file of the format cx,cy,a,b,angle,rings  (a & b are ellipse axes), as in..
$ cat test_img.csv
37,42,30,42,63,0
402,71,37,20,41,0
459,256,40,19,45,0
175,198,41,30,134,0

To get the corresponding image file, it replaces '.csv' with '.png' in the file name

For more options, run $ ./ellipse_editor.py --help


This code actually uses Tk instead OpenCV.  Because...those are the first tutorials I found.
The rest of the SPNet code uses OpenCV.



MIT License:
Copyright (c) 2018 Scott Hawley, https://github.com/drscotthawley

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''


import tkinter as tk
from tkinter.simpledialog import askfloat
import math
import numpy as np
import pandas as pd
from PIL import Image, ImageTk, ImageOps
import tkinter.font
import argparse
import os
import glob
import sys
from pathlib import Path
from fastcore.script import *
import re
from espiownage.core import *
from itertools import cycle
from collections import defaultdict



def increment(num, digits,step):
    # return the first part of match as is, Return the 2nd match + 1 which is 'x + 1'
    return num.group(1) + str(int(num.group(2)) + step).zfill(digits)

def get_next_img(meta_file, step=1, img_bank='images/'):
    "Increments the number of the image filename and tries to load it"
    digits = len(Path(meta_file).stem.split('_')[-1]) # num digits in ending number part of the name
    next_meta = re.sub('(proc_)([0-9]{'+str(digits)+'})', lambda m: increment(m,digits,step), meta_file)
    next_img_path = meta_to_img_path(next_meta, img_bank=img_bank)
    if os.path.exists(str(next_img_path)):
        return ImageTk.PhotoImage(image=Image.open(next_img_path)), str(next_img_path)
    blank_img = Image.new('RGB', (512, 384), (255, 255, 255))
    return ImageTk.PhotoImage(image=blank_img), 'None'



def poly_oval(cx, cy, a, b, angle=0, steps=100 ):
    # From https://mail.python.org/pipermail/python-list/2000-December/022013.html
    """return an oval as coordinates suitable for create_polygon"""

    # angle is in degrees anti-clockwise, convert to radians
    rotation = angle * math.pi / 180.0  # overall angle of the ellipse

    point_list = []

    # create the oval as a list of points
    for i in range(steps):

        # Calculate the angle for this step: 360 degrees == 2 pi radians
        theta = (math.pi * 2) * (float(i) / steps)  # theta is for points drawing the circumference of the ellipse
        x1, y1 = a * math.cos(theta), b * math.sin(theta)

        # rotate x, y
        x = (x1 * math.cos(rotation)) + (y1 * math.sin(rotation))
        y = (y1 * math.cos(rotation)) - (x1 * math.sin(rotation))

        point_list.append((x + cx))
        point_list.append((y + cy))

    return point_list


def clean_pandas_list(list_):
    list_ = list_.replace(', ', '","')
    list_ = list_.replace('[', '["')
    list_ = list_.replace(']', '"]')
    return list_


def interleave_lists(list1:list, list2:list):
    "alternate between 1 and 2; if they're of different lengths, it keeps going with whatever's left in the longer one"
    return [x for both in zip(cycle(list1), list2) for x in both]

def dedup_list(li):
    "remove duplicates while preserving order of first dup(non-dup?/orig?).  cf. https://stackoverflow.com/a/480227/4259243"
    seen = set()
    seen_add = seen.add
    return [x for x in li if not (x in seen or seen_add(x))]


def get_top_loss_list(
    top_losses_dir,  # directory where top-losses info is stored
    ):
    "gets list of filenames with top losses for use with preferential ordering"
    if (top_losses_dir==None) or (not os.path.exists(top_losses_dir)): return []
    # slurp in any csv files we've got
    # note they likely have different columns, and the loss values are not comparable
    tldir_files_list = glob.glob(top_losses_dir+'/*.csv') # files in tl directory
    top_loss_list = []
    for tldir_file in tldir_files_list:
        #print("top losses tldir_file = ",tldir_file)
        df = pd.read_csv(tldir_file)
        fnames = dedup_list(list(df["filename"]))
        if [] == top_loss_list: top_loss_list = fnames
        else: top_loss_list = interleave_lists(top_loss_list, fnames)
    return dedup_list(top_loss_list)


class EllipseEditor(tk.Frame):
    '''Edit ellipses for steelpan images'''

    def __init__(self, parent,  # tk class and parent window
        meta_file_list,         # list of csv files to edi
        img_bank='images/',     # where images are stored
        tldir=None,        # directory where top-losses info is stored
        seq=True,               # ignore top losses and do sequential selection of frames (per existing annotations)
        ):
        tk.Frame.__init__(self, parent)
        self.meta_file_list = meta_file_list
        self.img_bank = img_bank
        self.top_loss_list = get_top_loss_list(tldir)
        if self.top_loss_list == []: seq = True
        if not seq: self.meta_file_list = combine_file_and_tl_lists(self.meta_file_list, self.top_loss_list)
        self.seq = seq

        # create a canvas
        self.width, self.height = 512, 384   # size of images
        self.y0 = 0# self.height    # y offset for all operations
        self.readout = 700                   # width for additional annotation text
        self.canvas = tk.Canvas(width=self.width + self.readout, height=20+2*self.height )
        self.canvas.pack(fill="both", expand=True)

        self.file_index = 0                 # TODO: change to grab from top losses
        self.meta_file = meta_file_list[self.file_index]
        self.img_file = str(meta_to_img_path(self.meta_file, img_bank=self.img_bank))

        self.mask_pred_file = ''
        self.mask_img = None
        self.showing_mask = True

        self.bbox_pred_file = 'top_losses/bboxes_top_losses_real.csv' # TODO: this is fragile
        self.showing_bboxes = True
        self.bbox_list = []
        self.bbox_df = pd.read_csv(self.bbox_pred_file, converters={'bblist': eval})
        self.bbox_df.apply(clean_pandas_list)

        self.tl_ring_count_file, self.tl_ring_count_dict = '', {}
        self.tl_ring_count_dict = defaultdict(lambda: [], self.tl_ring_count_dict) # map filenames to lists of rings info; defaults to empty list
        tl_rc_files = glob.glob(tldir+'/*ring*.csv')
        if len(tl_rc_files) > 0:
            self.tl_ring_count_file = tl_rc_files[0] # not sure I'll keep the same name. something ring-related
            self.setup_tl_ring_count_dict()
        self.showing_predrings, self.predringlist = True, []  # thing we actually use

        self.color = "green"

        # this data is used to keep track of an item being dragged
        self._drag_data = {"x": 0, "y": 0, "items": None}

        self._token_data = []
        self._numtokens = 0
        self.hr = 4             # handle radius

        # Define global event bindings
        self.canvas.bind("<B1-Motion>", self.update_readout)
        self.canvas.bind("<Double-Button-1>", self.on_doubleclick)
        self.canvas.bind("<ButtonPress-2>", self.on_rightpress)   # on mac, button 2 is right mouse
        self.canvas.bind("<ButtonPress-3>", self.on_rightpress)   # on linux, button 3 is right mouse

        self.canvas.focus_set()
        self.canvas.bind("<Q>", self.on_qkey)
        self.canvas.bind("<q>", self.on_qkey)
        self.canvas.bind("<S>", self.on_skey)
        self.canvas.bind("<s>", self.on_skey)
        self.canvas.bind("<M>", self.on_mkey)
        self.canvas.bind("<m>", self.on_mkey)
        self.canvas.bind("<R>", self.on_rkey)
        self.canvas.bind("<r>", self.on_rkey)
        self.canvas.bind("<B>", self.on_bkey)
        self.canvas.bind("<b>", self.on_bkey)
        self.canvas.bind("<Left>", self.on_leftarrow)
        self.canvas.bind("<Right>", self.on_rightarrow)
        self.canvas.bind('<Motion>', self.mouse_move)

        self.infostr = ""
        self.text = self.canvas.create_text(self.width+10, 10+self.height, text=self.infostr,
            anchor=tk.NW, font=tk.font.Font(size=15,family='Consolas'))
        self.df = ''

        self.load_new_files()


    def setup_tl_ring_count_dict(self):
        "this will store info about all the antinode ring counts for each file, as a list of lists for each file"
        df = pd.read_csv(self.tl_ring_count_file)
        #print(df.head())
        for i, row in df.iterrows(): # stop telling me stop using iterrows, it's clear coding ;-)
            meta, parts = meta_from_str(row['filename']), row['filename'].split('_')[-5:]
            bbox, rings = [int(x) for x in parts[0:4]], float(row['prediction'])
            bb_rings = bbox + [rings]
            if len(self.tl_ring_count_dict[meta]) == 0: self.tl_ring_count_dict[meta] = [bb_rings]
            else: self.tl_ring_count_dict[meta].append(bb_rings)

    def setup_pred_mask(self):
        self.mask_img = None
        self.mask_pred_file = 'top_losses/seg_images/'+str(Path(self.meta_file).stem)+'_pred.png'
        if os.path.exists(self.mask_pred_file):
            self.mask_img = Image.open(self.mask_pred_file)
            if self.mask_img.size != (self.width, self.height): # to allow for half-size masks
                self.mask_img.size = self.mask_img.size.resize((self.width, self.height))
            self.mask_img = ImageOps.colorize(self.mask_img, black ="black", white =(150,0,150))
        return

    def merge_mask_image(self):
        if not self.mask_img: return
        if self.showing_mask:
            self.image = Image.blend(self.image, self.mask_img, 0.5)
            self.assign_image()

    def draw_pred_rings(self):
        if (not self.showing_predrings) or (len(self.predringlist) == 0): return
        for bbr in self.predringlist:
            cx, cy, ringstr = int((bbr[0]+bbr[2])/2), int((bbr[1]+bbr[3])/2), '{0:.1f}'.format(bbr[-1])
            #print("predicted ring counts: ",cx, cy, ringstr)
            ringtext = self.canvas.create_text(cx, self.y0+cy-15, text=ringstr, anchor=tk.CENTER, font=tk.font.Font(size=15), fill="yellow")

    def draw_pred_bboxes(self, please_fix=True):
        if (not self.showing_bboxes) or len(self.bbox_list)==0: return
        for bb in self.bbox_list[0]:
            if please_fix:
                # icevision shrank our images and then ebedded them in 384,384, we need to undo that?
                bb = [int(x*512/384) for x in bb]  # unshrink everything
                bb[1], bb[3] = bb[1]-(512-384)//2, bb[3]-(512-384)//2
            box = self.canvas.create_rectangle(bb[0],bb[1],bb[2],bb[3], outline="cyan", width=2)

    def load_new_files(self):
        self.canvas.delete("all")  #destroy old tokens
        self.text = self.canvas.create_text(self.width+10, 10+self.y0, text=self.infostr,
            anchor=tk.NW, font=tk.font.Font(size=15,family='Consolas'))
        self.meta_file = self.meta_file_list[self.file_index]
        self.img_file = meta_to_img_path(self.meta_file, img_bank=self.img_bank)
        self.setup_pred_mask()
        self.read_assign_image()
        self.merge_mask_image()

        self.read_prev_next_imgs()
        self.bbox_list = self.bbox_df[self.bbox_df['filename'] == os.path.basename(self.meta_file)]['bblist'].tolist() # nice, huh? ;-)
        self.draw_pred_bboxes()
        self.predringlist = self.tl_ring_count_dict[os.path.basename(self.meta_file)]
        self.draw_pred_rings()
        self.read_assign_csv()


    def assign_image(self):
        self.tkimage = ImageTk.PhotoImage(image=self.image)
        self.label = tk.Label(image=self.tkimage)
        self.label.image = self.tkimage # keep a reference!
        self.canvas.create_image(self.width/2, self.y0 + self.height/2, image=self.tkimage)

    def read_assign_image(self):
        self.image = Image.open(self.img_file)
        self.image = ImageOps.colorize(self.image, black ="black", white ="white")
        self.backup = self.image
        self.assign_image()

    def read_assign_csv(self):
        col_names = ['cx', 'cy', 'a', 'b', 'angle', 'rings']
        self.df = pd.read_csv(self.meta_file,header=None,names=col_names)  # read metadata file
        self.df.drop_duplicates(inplace=True)  # sometimes the data from Zooniverse has duplicate rows
        # assign  ellipse tokens (and their handles)
        for index, row in self.df.iterrows() :
            cx, cy, a, b, angle, rings = row['cx'], row['cy'], row['a'], row['b'], float(row['angle']), row['rings']
            a, b, angle = fix_abangle(a,b,angle)
            if (0!=rings):    # 0 rings means no antinode, i.e. nothing there
                self._create_token((cx, cy), (a, b), angle, rings, self.color)
        self.update_readout(None)

    def read_prev_next_imgs(self):
        # prev image
        self.prev_img, name = get_next_img(self.meta_file, -1, img_bank=self.img_bank)
        if self.prev_img: self.canvas.create_image(self.width/2, self.y0 + self.height+20 + self.height/2, image=self.prev_img)
        imlabel = f"Previous Image: {name.split('/')[-1]}"
        self.canvas.create_text(10, self.y0+self.height, text=imlabel, anchor=tk.NW, font=tk.font.Font(size=12), fill='black')

        # next image
        self.next_img, name = get_next_img(self.meta_file, 1, img_bank=self.img_bank)
        if self.next_img: self.canvas.create_image(self.width+20+self.width/2, self.y0 + self.height+20 + self.height/2, image=self.next_img)
        imlabel = f"Next Image: {name.split('/')[-1]}"
        self.canvas.create_text(self.width+30, self.y0+self.height, text=imlabel, anchor=tk.NW, font=tk.font.Font(size=12), fill='black')
        return

    def _create_token(self, coord, axes, angle, rings, color):
        '''Create a tk token at the given coordinate in the given color'''
        self._numtokens += 1
        (x,y) = coord
        (a,b) = axes
        thistag = "token"+str(self._numtokens)   # each token gets its own unique id, plus the whole ellipse gets a 'main' tag
        oval = self.canvas.create_polygon(*tuple(poly_oval(x, self.y0+y, a, b, angle=angle)),outline=color, fill='', width=3, tags=(thistag,"main"))

        # handles for resize / rotation
        h_a_x, h_a_y = x + a*np.cos(np.deg2rad(angle)),  y - a*np.sin(np.deg2rad(angle))
        h_b_x, h_b_y = x + b*np.sin(np.deg2rad(angle)),  y + b*np.cos(np.deg2rad(angle))
        h_a = self.canvas.create_oval(h_a_x-self.hr, self.y0+h_a_y-self.hr, h_a_x+self.hr, self.y0+h_a_y+self.hr, outline=color, fill=color, width=3, tags=(thistag,"handle","axis_a"))
        h_b = self.canvas.create_oval(h_b_x-self.hr, self.y0+h_b_y-self.hr, h_b_x+self.hr, self.y0+h_b_y+self.hr, outline=color, fill="blue", width=3, tags=(thistag,"handle","axis_b"))

        ringstr = '{0:.1f}'.format(rings)
        ringtext = self.canvas.create_text(x-5, self.y0+y-10, text=ringstr, anchor=tk.NW, font=tk.font.Font(size=16), fill=color, tags=(thistag,"ringtext"))

        self._token_data.append([oval,h_a,h_b,ringtext])

        # Define Event Bindings for moving objects around
        self.canvas.tag_bind("main", "<ButtonPress-1>", self.on_main_press)
        self.canvas.tag_bind("main", "<ButtonRelease-1>", self.on_main_release)
        self.canvas.tag_bind("main", "<B1-Motion>", self.on_main_motion)

        self.canvas.tag_bind("handle", "<ButtonPress-1>", self.on_handle_press)
        self.canvas.tag_bind("handle", "<ButtonRelease-1>", self.on_handle_release)
        self.canvas.tag_bind("handle", "<B1-Motion>", self.on_handle_motion)

    def on_qkey(self, event):
        print("Quitting")
        sys.exit()
    def on_skey(self,event):
        print("Saving file ",self.meta_file)
        # TODO: add code to enforce a > b (and fix angle)
        self.df.to_csv(self.meta_file,index=False,header=None)
    def on_mkey(self,event):
        self.showing_mask = not self.showing_mask
        if self.showing_mask and self.mask_img is not None:
            self.merge_mask_image()
            self.load_new_files()
        if not self.showing_mask:
            self.image = self.backup
            self.load_new_files()
    def on_rkey(self,event):
        self.showing_predrings = not self.showing_predrings
        self.load_new_files()
    def on_bkey(self,event):
        self.showing_bboxes = not self.showing_bboxes
        self.load_new_files()
    def on_rightarrow(self,event):               # right arrow on keyboard
        self.file_index += 1                     # TODO: grab from top_losses
        if (self.file_index >= len(self.meta_file_list)):
            self.file_index = 0
        self.load_new_files()
    def on_leftarrow(self,event):
        self.file_index -= 1
        if (self.file_index < 0):
            self.file_index = len(self.meta_file_list)-1
        self.load_new_files()
    def mouse_move(self,event):
        x, y = event.x, event.y
        tx, ty = 2*self.width+40, 2*self.height-40
        box = self.canvas.create_rectangle(tx-5,ty, tx+110,ty+25, fill="white", outline="white")
        self.canvas.create_text(tx, ty, text=f'({x},{y})', anchor=tk.NW, font=tk.font.Font(size=12), fill='black')

    def on_main_press(self, event):
        '''Begining drag of an object'''
        obj_id = self.canvas.find_closest(event.x, event.y)[0]  # record the item and its location
        tags = self.canvas.gettags( obj_id )
        self._drag_data["items"] = tags[0]
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_main_release(self, event):
        '''End drag of an object'''
        # if object is off the screen, delete it
        if ((event.x < 0) or (event.y < 0 ) or (event.x > self.width) or (event.y > self.height)):
            self.canvas.delete(self._drag_data["items"])
            self.update_readout(None)
        # reset the drag information
        self._drag_data["items"] = None
        self._drag_data["x"] = 0
        self._drag_data["y"] = 0

    def on_main_motion(self, event):
        '''Handle dragging of an object'''
        # compute how much the mouse has moved
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]
        # move the object the appropriate amount
        self.canvas.move(self._drag_data["items"], delta_x, delta_y)
        # record the new position
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y



    def retrieve_ellipse_info(self, tokentag):
        # retrieves info for whichever single ellipse is currently being manipulated
        tokenitems = self.canvas.find_withtag( tokentag )
        [main_id, axis_a_id, axis_b_id, ringtext_id ]= tokenitems

        ell_coords = self.canvas.coords(main_id)   # coordinates of all points in ellipse
        cxoords, cyoords = ell_coords[0::2],  ell_coords[1::2]
        cx, cy = np.mean( cxoords ),  np.mean( cyoords )   # coordinates of center of ellipse

        h_a_coords = self.canvas.coords(axis_a_id)
        h_a_x, h_a_y = np.mean( h_a_coords[0::2] ),  np.mean( h_a_coords[1::2] )
        a = np.sqrt( (h_a_x - cx)**2 + (h_a_y - cy)**2 )

        h_b_coords = self.canvas.coords(axis_b_id)
        h_b_x, h_b_y = np.mean( h_b_coords[0::2] ),  np.mean( h_b_coords[1::2] )
        b = np.sqrt( (h_b_x - cx)**2 + (h_b_y - cy)**2 )

        angle = np.rad2deg( np.arctan2( cy - h_a_y, h_a_x - cx) )

        rings = self.canvas.itemcget(ringtext_id, 'text')

        return cx, cy, a, b, angle, rings, ell_coords


    def update_df(self):
        # iterate through all ellipses -- i.e. tokens with with 'main' tag
        tokenitems = self.canvas.find_withtag( 'main' )


    def on_handle_press(self, event):
        '''Begining drag of an handle'''
        # record the item and its location
        ids = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags( ids )
        self._drag_data["items"] = ids
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_handle_release(self, event):
        '''End drag of an handle'''
        # reset the drag information
        self._drag_data["items"] = None
        self._drag_data["x"] = 0
        self._drag_data["y"] = 0

    def on_handle_motion(self, event):
        '''Handle dragging of an handle'''
        # compute how much the mouse has moved
        oldx, oldy = self._drag_data["x"], self._drag_data["y"]
        delta_x = event.x - oldx
        delta_y = event.y - oldy
        # move the handle the appropriate amount
        self.canvas.move(self._drag_data["items"], delta_x, delta_y)

        # what are the tags for this particular handle
        tags = self.canvas.gettags( self._drag_data["items"] )
        tokentag = tags[0]
        cx, cy, a, b, angle, rings, coords  = self.retrieve_ellipse_info( tokentag )

        tokenitems = self.canvas.find_withtag( tokentag )
        [main_id, axis_a_id, axis_b_id, ringtext_id ]= tokenitems

        new_r = np.sqrt( (event.x -cx)**2 + (event.y - cy)**2 )
        new_angle = np.rad2deg( np.arctan2( cy-oldy, oldx-cx) )

        # which handle is currently being manipulated?
        if ("axis_a" in tags):
            b_coords = self.canvas.coords(axis_b_id)
            h_b_x, h_b_y = np.mean( b_coords[0::2] ),  np.mean( b_coords[1::2] )
            new_coords = poly_oval( cx, cy, new_r, b, angle=new_angle)
            h_b_x, h_b_y =  cx + b*np.sin(np.deg2rad(new_angle)),  cy + b*np.cos(np.deg2rad(new_angle))
            self.canvas.coords(axis_b_id, [ h_b_x-self.hr, h_b_y-self.hr, h_b_x+self.hr, h_b_y+self.hr] )
        elif ("axis_b" in tags):
            a_coords = self.canvas.coords(axis_a_id)
            h_a_x, h_a_y = np.mean( a_coords[0::2] ),  np.mean( a_coords[1::2] )
            new_angle = new_angle + 90   # a and b axes are offset by 90 degrees; angle is defined relative to a axis
            new_coords = poly_oval( cx, cy, a, new_r, angle=new_angle)
            h_a_x, h_a_y =  cx + a*np.cos(np.deg2rad(new_angle)),  cy - a*np.sin(np.deg2rad(new_angle))
            self.canvas.coords(axis_a_id, [ h_a_x-self.hr, h_a_y-self.hr, h_a_x+self.hr, h_a_y+self.hr] )
        else:
            print("Error: bad tags")
            assert(0==1)

        self.canvas.coords(main_id, new_coords)  # reassign coords for the entire ellipse (i.e. 'redraw')
        # record the new position
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y


    def on_doubleclick(self, event):  # create a new ellipse
        cx, cy, a, b, angle, rings = event.x, event.y, 50, 50, 0, 1     # give it some default data
        self._create_token((cx, cy), (a, b), angle, rings, self.color)
        self.update_readout(None)

    def on_rightpress(self,event):
        obj_id = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags( obj_id )
        ringtext = self.canvas.itemcget(obj_id, 'text')
        result = askfloat("How many rings", "How many rings?", initialvalue=float(ringtext))

        self.canvas.itemconfigure(obj_id,text=str(result))
        self.canvas.focus_set()           # that dialog box stole the focus. get it back
        self.update_readout(None)

    def update_readout(self, event):
        mains = self.canvas.find_withtag( "main" )
        self.infostr = self.meta_file+'\n'+str(self.img_file)+'\n\n'

        new_df = pd.DataFrame(columns=self.df.columns)
        # first we update the dataframe info
        for main_id in mains:
            tokentag = self.canvas.gettags( main_id )[0]
            cx, cy, a, b, angle, rings, coords = self.retrieve_ellipse_info( tokentag )
            a,b,angle = fix_abangle(a,b,angle)
            [cx, cy, a, b, angle] = [int(round(x)) for x in [cx, cy, a, b, angle]]
            #x, cy, a, b, angle = int(round(cx,0)), int(round(cy,0)), int(round(a,0), round(b,0), round(angle,0)
            new_df = new_df.append({'cx':cx, 'cy':cy, 'a':a, 'b':b, 'angle':angle, 'rings':rings},ignore_index=True)

        self.df = new_df
        self.infostr += self.df.to_string(index=False,justify='left')      # then we output the dataframe info to a string
        self.canvas.itemconfigure(self.text, text=self.infostr)   # then we re-assign the text widget with the new string



@call_parse
def ellipse_editor(
    seq:Param("Ignore top-loss ordering and do sequential ordering", store_true),
    files:Param("Wildcard name for all CSV files to edit", str)='annotations/*.csv',
    imgbank:Param("Directory where all the (unlabeled) images are",str)='images/',
    tldir:Param("Directory where 'top losses' info is stored'",str)='top_losses/',
    ):
    global img_bank
    # typical command-line calling sequence:
    #  $ ./ellipse_editor.py *.csv
    files = ''.join(files)
    meta_file_list = sorted(glob.glob(files))
    img_bank = imgbank

    print("Instructions:")
    print(" Mouse bindings:")
    print("    - Double-click to create ellipse")
    print("    - Left-click and drag inside ellipse (but not on a number) to move ellipse")
    print("    - Left-click and drag 'handles' to resize/rotate ellipse (solid = 'a', hollow = 'b')")
    print("    - Right-click (or middle click) inside number to change ring count")
    print("    - Drag off-screen to destroy/delete ellipse")
    print(" Key bindings:")
    print("    - Right Arrow : Next file")
    print("    - Left Arrow  : Previous file")
    print("    - M           : Toggle display of predicted segmentation mask (if available)")
    print("    - R           : Toggle display of predicted ring counts (if available)")
    print("    - B           : Toggle display of predicted bounding boxes (if available)")
    print("    - S           : Save metadata")
    print("    - Q           : Quit")


    root = tk.Tk()
    root.title('espiownage: ellipse_editor')
    EllipseEditor(root, meta_file_list, img_bank=img_bank, tldir=tldir, seq=seq).pack(fill="both", expand=True)
    root.mainloop()

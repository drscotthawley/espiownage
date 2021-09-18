# espiownage



> Ownage (domination) of ESPI image inference. (Pronounced like "espionage" but with a little "own" in the middle.)

Welcome to the new phase of [SPNet](https://github.com/drscotthawley/SPNet) developement -- IN PROGRESS.  
In this incarnation, we'll be making it an image-segmentation code instead of an object detector, and we'll use [fast.ai](fast.ai).   

## Install

### Preliminaries

Ubuntu (& probably other Linuxes):
```bash
sudo apt-get install python3-tk
```

Mac (with [Homebrew](https://brew.sh/))
```bash
brew install python-tk
```

Then on all systems, let's set up a virtual environment called `espi`. 
I like to put my environments in `~/envs`:

```
mkdir ~/envs; python3 -m venv ~/envs/espi; source ~/envs/espi/bin/activate
```
And then you want/need to update `pip` in case it gave you an ancient version:

```bash
python3 -m pip install pip --upgrade
```

### Pip install

```bash
pip install espiownage
```
Note: the requirements on this package follow a "kitchen sink" approach so that everything a student might need gets installed, e.g. `jupyter` and more. (And `wheel` because it speeds up the installations...I think.)

## How to use

If you're reading this, you probably have access to the "real" data, which sits (on my machine) in `~/Dropbox/Data/espiownage-data`.  So `cd` to that directory, i.e.,
```
$ cd ~/Dropbox/Data/espiownage-data
```
...(or whereever you've got it) for what follows. 

**AND THEN**, so we don't "clobber" each other's work, make *your own copy* (~17MB) of the main `annotations` directory, as in append your last name (hawley, morrison, morgan, etc):

```bash
cp -r annotations annotations_yourlastname
```
and then we'll each edit our own copy just to avoid...confusion. 
> *Note:If you don't have access to the real data,* you can still grab the [fake SPNet data](https://zenodo.org/record/4445434) and then, for each of those datasets: Move (or symlink) all the images to a directory called `images/`, and all the `.csv` files to a directory called `annotations/`, and proceed.

## Console Scripts:
These can all be run from the command line / terminal:

### ellipse_editor


<h4 id="ellipse_editor" class="doc_header"><code>ellipse_editor</code><a href="https://github.com/drscotthawley/espiownage/tree/master/espiownage/ellipse_editor.py#L404" class="source_link" style="float:right">[source]</a></h4>

> <code>ellipse_editor</code>(**`files`**:"Wildcard name for all CSV files to edit"=*`'annotations/*.csv'`*, **`imgbank`**:"Directory where all the (unlabeled) images are"=*`'images/'`*)



**Parameters:**


 - **`files`** : *`str <Wildcard name for all CSV files to edit>`*, *optional*

 - **`imgbank`** : *`str <Directory where all the (unlabeled) images are>`*, *optional*



```python
!ellipse_editor -h
```

    usage: ellipse_editor [-h] [--files FILES] [--imgbank IMGBANK]
    
    optional arguments:
      -h, --help         show this help message and exit
      --files FILES      Wildcard name for all CSV files to edit (default:
                         annotations/*.csv)
      --imgbank IMGBANK  Directory where all the (unlabeled) images are (default:
                         images/)


**Examples:**
```bash
ellipse_editor --files=annotations_yourlastname/*.csv
```

See `ellipse_editor -h` for command-line options.   You can, for example, edit only one strike's worth of data by running

```bash
ellipse_editor --files=annotations_yourlastname/06241902*.csv
```
or a range of annotations, as in `ellipse editor --files=annotations_yourlastname/06241902_proc_001*.csv`

### gen_masks


<h4 id="gen_masks" class="doc_header"><code>gen_masks</code><a href="https://github.com/drscotthawley/espiownage/tree/master/espiownage/gen_masks.py#L70" class="source_link" style="float:right">[source]</a></h4>

> <code>gen_masks</code>(**`allone`**:"All objects get assigned to class 1", **`cp_ann_imgs`**:"make directory of only images for which annotations exist (to annotated_images/)", **`files`**:"Wildcard name for all CSV files to edit"=*`'annotations/*.csv'`*, **`maskdir`**:"Directory to write segmentation masks to"=*`'masks/'`*, **`step`**:"Step size / resolution / precision of ring count"=*`1`*)

Generate segmentation masks for all annotations

**Parameters:**


 - **`allone`** : *`<All objects get assigned to class 1>`*

 - **`cp_ann_imgs`** : *`<make directory of only images for which annotations exist (to annotated_images/)>`*

 - **`files`** : *`str <Wildcard name for all CSV files to edit>`*, *optional*

 - **`maskdir`** : *`str <Directory to write segmentation masks to>`*, *optional*

 - **`step`** : *`float <Step size / resolution / precision of ring count>`*, *optional*



```python
!gen_masks -h
```

    usage: gen_masks [-h] [--allone] [--cp_ann_imgs] [--files FILES]
                     [--maskdir MASKDIR] [--step STEP]
    
    Generate segmentation masks for all annotations
    
    optional arguments:
      -h, --help         show this help message and exit
      --allone           All objects get assigned to class 1 (default: False)
      --cp_ann_imgs      make directory of only images for which annotations exist
                         (to annotated_images/) (default: False)
      --files FILES      Wildcard name for all CSV files to edit (default:
                         annotations/*.csv)
      --maskdir MASKDIR  Directory to write segmentation masks to (default: masks/)
      --step STEP        Step size / resolution / precision of ring count (default:
                         1)


### gen_bboxes


<h4 id="gen_bboxes" class="doc_header"><code>gen_bboxes</code><a href="https://github.com/drscotthawley/espiownage/tree/master/espiownage/gen_bboxes.py#L116" class="source_link" style="float:right">[source]</a></h4>

> <code>gen_bboxes</code>(**`reg`**:"Set this for regression model (1 class, no steps)", **`files`**:"Wildcard name for all (ellipse) CSV files to read"=*`'annotations/*.csv'`*, **`bboxdir`**:"Directory to write bboxes to"=*`'bboxes'`*, **`step`**:"For classification model: Step size / resolution / precision of ring count"=*`0.5`*)



**Parameters:**


 - **`reg`** : *`<Set this for regression model (1 class, no steps)>`*

 - **`files`** : *`str <Wildcard name for all (ellipse) CSV files to read>`*, *optional*	<p>obpr:Param("Set this for one box per ring", store_true),</p>


 - **`bboxdir`** : *`str <Directory to write bboxes to>`*, *optional*

 - **`step`** : *`float <For classification model: Step size / resolution / precision of ring count>`*, *optional*



```python
!gen_bboxes -h
```

    usage: gen_bboxes [-h] [--reg] [--files FILES] [--bboxdir BBOXDIR] [--step STEP]
    
    optional arguments:
      -h, --help         show this help message and exit
      --reg              Set this for regression model (1 class, no steps) (default:
                         False)
      --files FILES      Wildcard name for all (ellipse) CSV files to read (default:
                         annotations/*.csv)
      --bboxdir BBOXDIR  Directory to write bboxes to (default: bboxes)
      --step STEP        For classification model: Step size / resolution /
                         precision of ring count (default: 0.5)


### gen_crops


<h4 id="gen_crops" class="doc_header"><code>gen_crops</code><a href="https://github.com/drscotthawley/espiownage/tree/master/espiownage/gen_crops.py#L47" class="source_link" style="float:right">[source]</a></h4>

> <code>gen_crops</code>(**`files`**:"Wildcard name for all CSV files to edit"=*`'annotations/*.csv'`*, **`outdir`**:"Directory to write output cropped images to"=*`'crops/'`*)

Generate cropped images for all annotations

**Parameters:**


 - **`files`** : *`str <Wildcard name for all CSV files to edit>`*, *optional*

 - **`outdir`** : *`str <Directory to write output cropped images to>`*, *optional*



```python
!gen_crops -h
```

    usage: gen_crops [-h] [--files FILES] [--outdir OUTDIR]
    
    Generate cropped images for all annotations
    
    optional arguments:
      -h, --help       show this help message and exit
      --files FILES    Wildcard name for all CSV files to edit (default:
                       annotations/*.csv)
      --outdir OUTDIR  Directory to write output cropped images to (default: crops/)


### grab_recent


<h4 id="grab_recent" class="doc_header"><code>grab_recent</code><a href="https://github.com/drscotthawley/espiownage/tree/master/espiownage/grab_recent.py#L18" class="source_link" style="float:right">[source]</a></h4>

> <code>grab_recent</code>(**`dirs`**:"annotation directories check"=*`'annotations*'`*, **`dest`**:"Directory to write new annotations to"=*`'recent_annotations'`*)



**Parameters:**


 - **`dirs`** : *`str <annotation directories check>`*, *optional*

 - **`dest`** : *`str <Directory to write new annotations to>`*, *optional*



```python
!grab_recent -h
```

    usage: grab_recent [-h] [--dirs DIRS] [--dest DEST]
    
    optional arguments:
      -h, --help   show this help message and exit
      --dirs DIRS  annotation directories check (default: annotations*)
      --dest DEST  Directory to write new annotations to (default:
                   recent_annotations)


### gen_fake


<h4 id="gen_fake" class="doc_header"><code>gen_fake</code><a href="https://github.com/drscotthawley/espiownage/tree/master/espiownage/gen_fake.py#L265" class="source_link" style="float:right">[source]</a></h4>

> <code>gen_fake</code>(**`n`**:"Number of images to generate"=*`2000`*, **`outdir`**:"Directory to write to"=*`'espiownage-fake'`*)

Generates fake ESPI-like images

**Parameters:**


 - **`n`** : *`int <Number of images to generate>`*, *optional*

 - **`outdir`** : *`str <Directory to write to>`*, *optional*



```python
!gen_fake -h
```

    usage: gen_fake [-h] [--n N] [--outdir OUTDIR]
    
    Generates fake ESPI-like images
    
    optional arguments:
      -h, --help       show this help message and exit
      --n N            Number of images to generate (default: 2000)
      --outdir OUTDIR  Directory to write to (default: espiownage-fake)


## Contributing / Development 

You'll want to install more things:

```bash
pip install nbdev twine 
```

Fork this repo.  When you want to update your repo, one macro does it all (see `Makefile`):
```bash
make git_update
```

## Asides

### Handy tips for students
I can never remember how to start up virtual environments / or I don't *want* to remember. So in my `~/.bashrc` file (you may have a `~/.zshrc`) I put in a line where I define an alias/function I call `gimme`, that reads like so:
```bash
gimme() { source ~/envs/"$1"/bin/activate;  }
```
(note that in order for this alias to be recognized, you need to either logout and log back in or else run `$ source ~/.bashrc`)

Then when I want to load environment like `espi` I just type...
```bash
gimme espi
```


--Scott H. Hawley, September 2021

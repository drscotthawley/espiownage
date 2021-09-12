# espiownage
> Utterly dominating ESPI image inference (Pronounced like "espionage" but with a little "own" in the middle.)


Welcome to the new phase of [SPNet](https://github.com/drscotthawley/SPNet) developement.  In this incarnation, we'll make it an image-segmentation code instead of an object detector, and we'll use [fast.ai](fast.ai).   

## Install

### Preliminaries

Ubuntu (& probably other Linuxes):
```bash
$ sudo apt-get install python3-tk
```

Mac (with [Homebrew](https://brew.sh/))
```bash
$ brew install python3-tk
```

Then on all systems, let's set up a virtual environment called `espi`. 
I like to put my environments in `~/envs`:

```
$ mkdir ~/envs; cd ~/envs; python3 -m venv espi; source ~/envs/espi/bin/activate
```
And then you gotta update `pip` or else you're gonna have a bad time:

```bash
$ python3 -m pip install pip --upgrade
```

### Then to install this package all you do is...

```bash
$ pip install espiownage
```

## How to use

### ellipse editor

```bash
ellipse_editor --files=*.csv
```

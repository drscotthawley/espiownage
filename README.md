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
$ mkdir ~/envs; python3 -m venv ~/envs/espi; source ~/envs/espi/bin/activate
```
And then you want/need to update `pip` in case it gave you an ancient version:

```bash
$ python3 -m pip install pip --upgrade
```

### Then to install this package all you do is...

```bash
$ pip install espiownage
```
Note: the requirements on this package follow a "kitchen sink" approach so that everything a student might need gets installed, e.g. `jupyter` and more. (And `wheel` because it speeds up the installations...I think.)

## How to use

### ellipse editor

```bash
ellipse_editor --files=*.csv
```

## Asides

#### Handy tips for students
I can never remember how to start up virtual environments / or I don't *want* to remember. So in my `~/.bashrc` file (you may have a `~/.zshrc`) I put in a line where I define an alias/function I call `gimme`, that reads like so:
```bash
gimme() { source ~/envs/"$1"/bin/activate;  }
```
(note that in order for this alias to be recognized, you need to either logout and log back in or else run `$ source ~/.bashrc`)

Then when I want to load environment like `espi` I just type...
```bash
$ gimme espi
```


--Scott H. Hawley, September 2021

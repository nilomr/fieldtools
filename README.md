![version](https://img.shields.io/badge/package_version-0.1.0-orange)
![PyPI status](https://img.shields.io/pypi/status/ansicolortags.svg)
![license](https://img.shields.io/github/license/mashape/apistatus.svg)
![Open Source Love](https://img.shields.io/badge/open%20source%3F-yes!-lightgrey)
![Python 3.8](https://img.shields.io/badge/python-3.8-brightgreen.svg)
![R](https://img.shields.io/badge/R-3.6.2-informational)

![gif](/fieldtools/src/fieldwork-helper.gif)


## Table of contents

  - [Description](#description)
  - [Installation](#installation)
  - [To-do](#to-do)

## Description

This repository contains three command line applications that I wrote to help with my field work, which involves copying large amounts of data from SD cards.
Most of it is very ugly and hacky, but it does its job and might be useful to someone else

| command            | description                                                  |
| :----------------- | :----------------------------------------------------------- |
| `copy-cards`       | Listens for SD cards and copies and organises their content automatically. |
| `format-cards`     | Format multiple cards at the same time: the program listens for volumes with name matching a pattern and mounts, formats, renames, and unmounts them. Whith an option to check that files have been safely backed up before formatting goes ahead. |
| `fieldwork-helper` | Enter and check data about recorder deployment in nest boxes with known spatial location. It automatically makes .gpx files with a fieldwork plan for the next day based on up-to-date nest progress information. Very specific to my work, but easy to adapt to other sites orprojects. Will not run as is - it needs private files to work. |

## Installation

1. Clone the repository:
```bash 
 git clone https://github.com/nilomr/fieldtools.git
```

2. Navigate to main project folder, then run:

```bash
  conda env create --file requirements.yml && conda activate fieldtools-env
```
3. Install source code: `pip install .` (install) or `pip install -e .` (developer install).
4. Make symlinks to scripts to copy/format cards and enter field data. You should change the paths in the bash script file as needed.

```bash
sudo bash dependencies/fieldwork-setup.sh
```

5. Run `conda deactivate` if you are still in the newly created 'fieldtools-env' environment.

6. You can now run `copy-cards`, `format-cards` or `fieldwork-helper` from any directory.


### To Do

 - [ ] dfdf

***
<p><small>A project by Nilo M. Recalde | 2021</small></p>


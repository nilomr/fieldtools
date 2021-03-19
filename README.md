![version](https://img.shields.io/badge/package_version-0.1.0-orange)
![PyPI status](https://img.shields.io/pypi/status/ansicolortags.svg)
![license](https://img.shields.io/github/license/mashape/apistatus.svg)
![Open Source Love](https://img.shields.io/badge/open%20source%3F-yes!-lightgrey)
![Python 3.6](https://img.shields.io/badge/python-3.6-brightgreen.svg)
![R](https://img.shields.io/badge/R-3.6.2-informational)

***

![Wytham Woods, Oxford](/resources/README_img/wytham_net.jpg)

This repository contains code to segment, label and analyse the songs of great tits (*Parus major*) recorded in Wytham Woods, Oxford, 2020- .

#### Table of contents
  - [Installation](#installation)
  - [Project Organisation](#project-organisation)
  - [Acknowledgements](#acknowledgements)

## Installation

1. Clone the repository:
`git clone https://github.com/nilomr/wytham-maps.git`.
2. Install source code:
`pip install .` (install) or `pip install -e .` (developer install).
3. Follow the instructions in the [docs](/docs) in the correct order.

## Project Organisation


    ├── LICENSE
    │
    ├── README.md          <- The top-level README.
    │
    ├── data               <- Main data folder. It is not version-tracked-the relevant program(s)  
    │   ├── external          create it automatically.
    │   ├── interim        
    │   ├── processed      
    │   └── raw            
    │
    ├── dependencies       <- Files required to reproduce the analysis environment(s).
    │
    ├── docs               <- Project documentation (installation instructions, etc.).
    │
    ├── notebooks          <- Jupyter and Rmd notebooks. Naming convention is number (for ordering),
    |   |                     the creator's initials, and a short `-` delimited description, e.g.
    │   └── ...               `1.0_nmr-label-songs`.  
    │                         
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc. Not currently tracked;
    |   |                     created automatically when needed.
    │   └── figures        <- Generated figures.
    │
    ├── setup.py           <- Makes project pip installable (so src can be imported).
    |
    ├── ...                <- R project, .gitignore, etc.
    │
    └── src                <- Source code. Install with `pip install .` (install) or 
                              `pip install -e .` (developer install).

## Acknowledgements

- `dependencies/AviaNZ-2.1` 
Marsland, S, Priyadarshani, N, Juodakis, J, Castro, I. AviaNZ: A future‐proofed program for annotation and recognition of animal sounds in long‐time field recordings. Methods Ecol Evol. 2019; 10: 1189– 1195. [DOI](https://doi.org/10.1111/2041-210X.13213)

- `Many functions in src/avgn` 
Sainburg T, Thielk M, Gentner TQ (2020) Finding, visualizing, and quantifying latent structure across diverse animal vocal repertoires. PLOS Computational Biology 16(10): e1008228. [DOI](https://doi.org/10.1371/journal.pcbi.1008228)

- `src/vocalseg` Code modified from Tim Sainburg. [Original repository](https://github.com/timsainb/vocalization-segmentation).
- The `dereverberate()` function, [here](https://github.com/nilomr/great-tit-song/blob/24d9527d0512e6d735e9849bc816511c9eb24f99/src/greti/audio/filter.py#L66), is based on code by Robert Lachlan ([Luscinia](https://rflachlan.github.io/Luscinia/)).

--------

<p><small>A project by Nilo M. Recalde | based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>.</small></p>

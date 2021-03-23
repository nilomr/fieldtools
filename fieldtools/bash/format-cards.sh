#!/bin/bash
source activate fieldtools-env 
cd $(dirname -- "$(readlink -f -- "$BASH_SOURCE")")
source paths.sh
python $pyformatcards
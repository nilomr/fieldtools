#!/bin/bash
source activate wytham-fieldwork 
cd "$(dirname "${BASH_SOURCE[0]}")"
source paths.sh
python $pyhelper

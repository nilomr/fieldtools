#!/bin/bash
source activate wytham-fieldwork && python "$(locate great-tit-song/src/greti/fieldwork/format-cards.py)"

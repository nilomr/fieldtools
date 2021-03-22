#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")"
source paths.sh

ln -sf $copycards /usr/sbin/copy-cards 
ln -sf $helper /usr/sbin/fieldwork-helper
ln -sf $formatcards /usr/sbin/format-card

chmod +x $copycards $helper $formatcards
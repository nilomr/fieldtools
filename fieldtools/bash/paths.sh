#!/bin/bash

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
echo $DIR 

copycards="$DIR/copy-cards.sh"
helper="$DIR/fieldwork-helper.sh"
formatcards="$DIR/format-cards.sh"

MAINDIR="$( cd ../main && pwd )"
echo $MAINDIR
pycopycards="$MAINDIR/copy-cards.py"
pyhelper="$MAINDIR/fieldwork-helper.py"
pyformatcards="$MAINDIR/format-cards.py"
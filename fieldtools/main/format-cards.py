#!/usr/bin/env python3

# TODO: mount any unmounted volumes automatically?


import os
import time
from subprocess import PIPE, Popen
import psutil
from fieldtools.src.aesthetics import (
    arrow, asterbar, build_logo, info, tcolor, tstyle)
from fieldtools.src.funs import (clean_vols, ensure_mount, find_sdiskpart,
                                 get_mountedlist, get_wav_filenames,
                                 is_faceplate, umount_and_rmdir)
from fieldtools.src.paths import OUT_DIR, safe_makedir, valid_vols_list
from fieldtools.version import __version__
from pathlib2 import Path

# Settings
skip_empty = False  # Wether to skip already empty cards
safe_copy = False  # Wether to ensure that files exist before allowing formatting
verbose = False
warn_others = False

# Folders of interest (not currently used)
folder_names = ['caca' for i in list(range(1, 61))]

valid_directories = [(name, folder_name)
                     for name, folder_name in zip(valid_vols_list, folder_names)]

# Main

# Make sure paths exist
for path in [OUT_DIR]:
    safe_makedir(path)

# Print logo
build_logo(__version__, logo_text='SD Card Wiper', font='tiny')
print(
    tcolor("""
 = USE AT YOUR OWN RISK =
 This application will automatically format
 any mounted volume with names matching a given
 pattern, currently [AM00, F0000].
""", tstyle.rojoroto)
)
if warn_others:
    if 'nilomr' in str(OUT_DIR):
        print(
            '\n' + info + tstyle.BOLD +
            tcolor("""
 This application will not work until you provide 
 your own paths and settings. See the README.
 """, tstyle.rojoroto))
        os._exit(0)

# Store volumes that have been already formatted
already_done = []
checked_cards = []
devnull = open(os.devnull, 'wb')

# Clean any mounted volumes
clean_vols()

# Counter (for progress bar)
it = 0

while True:
    print(arrow + tcolor('Scanning for cards',
                         tstyle.lightgrey), asterbar[it % len(asterbar)], end="\r")
    time.sleep(.1)
    it += 1

    # Mount any cards not already mounted
    # (sometimes automount does not work)
    checked_cards = ensure_mount(
        valid_directories, 0, checked_cards, already_done, verbose)

    # Now get all valid mounted cards
    mounted = get_mountedlist()
    new_paths = [dev for dev in mounted if not dev in already_done]
    valid_faceplates = [(dev, Path(dev).name)
                        for dev in new_paths if is_faceplate(dev)]
    valid_audiomoths = sum([[(drive, card[0]) for drive in new_paths
                             if card[0] in drive] for card in valid_directories], [])
    valid = valid_faceplates + valid_audiomoths

    # Skip if there are no new cards
    if not valid:
        continue
    else:
        for card in valid:
            if card[1] in already_done:
                continue

            print(
                tcolor('\n' + f'Trying to format {card[1]} ...', tstyle.mustard))

            # List files in card
            files = [os.path.join(card[0], i)
                     for i in os.listdir(card[0])]

            # Skip card if there are no files (optional, default = False)
            if skip_empty:
                if len(files) == 0:
                    print(
                        f'Card {card[1]} seems to be already empty, skipping.')
                    continue

            # Skip card if any WAV files have not yet been copied
            if safe_copy:
                wav_files = get_wav_filenames(card)
                if wav_files:
                    try:
                        with open(OUT_DIR / 'copied.txt', 'r') as cp:
                            copied_list = [filedir.rstrip()
                                           for filedir in cp]
                        if not set(wav_files).issubset(copied_list):
                            print(info +
                                  f'One or more files in {card[1]} have not yet been copied, skipping')
                            continue
                    except:
                        if (OUT_DIR / 'copied.txt').is_file():
                            print(
                                info + tcolor('There is an issue with /copied.txt, skipping.'), tstyle.rojoroto)
                        else:
                            print(info +
                                  tcolor('/copied.txt not found, use the `copy-cards` app at least once. Skipping', tstyle.rojoroto))
                        continue

            # Get volume name
            try:
                p = find_sdiskpart(card[0])
            except psutil.Error:
                print('Something went wrong lol')

            # Unmount card
            umount = f"sudo umount -l {p.device}*"
            proc1 = Popen(["/bin/bash", "-c", umount],
                          stdin=PIPE, stdout=PIPE, stderr=devnull)
            proc1.communicate()

            # Format card
            format = f"sudo mkfs.vfat -F32 -v {p.device}"
            proc2 = Popen(["/bin/bash", "-c", format],
                          stdin=PIPE, stdout=PIPE)
            oin, oout = proc2.communicate()

            # Rename card
            relabel = f"sudo fatlabel {p.device} {card[1]}"
            proc3 = Popen(["/bin/bash", "-c", relabel],
                          stdin=PIPE, stdout=PIPE, stderr=devnull)
            proc3.communicate()

            if proc2.returncode == 0:
                while os.path.exists(card[0]):
                    umount_and_rmdir(0, card)
                    # print('trying to umount again')
                print(info + tstyle.BOLD + tcolor(
                      f'Successfully formatted {card[1]}. You can now remove it', tstyle.teal))
                already_done.append(card[1])
            else:
                print(info + tcolor(
                      f'Error when trying to format {card[1]}. Remove it and try again', tstyle.rojoroto))
                while os.path.exists(card[0]):
                    umount_and_rmdir(0, card)
                already_done.append(card[1])

    time.sleep(0.5)

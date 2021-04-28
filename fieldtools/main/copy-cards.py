#!/usr/bin/env python3

import inspect
import os
import sys
import time
from datetime import date
from subprocess import PIPE, Popen

import pandas as pd
import psutil
from colorama import Back, Fore, Style, init
from fieldtools.src.aesthetics import (arrow, asterbar, build_logo, info,
                                       tcolor, tstyle)
from fieldtools.src.funs import (clean_vols, copy_with_progress, ensure_mount,
                                 fetch_recorder_info, find_sdiskpart,
                                 get_mountedlist, get_nestbox_id, is_faceplate,
                                 umount_and_rmdir)
from fieldtools.src.paths import DATA_DIR, OUT_DIR, safe_makedir, valid_vols_list
from fieldtools.version import __version__
from pathlib2 import Path

init(autoreset=True)

# Settings

# Whether to open a nautilus window when a new cards is mounted
open_origin_window = False
verbose = False  # Whether to print non-critical errors - not complete
check_for_drive = False  # Whether to check if the destination drive is mounted
warn_others = True

# Where to copy the files to (AMs)
DESTINATION_DIR = DATA_DIR / 'raw' / str(date.today().year)

# Folders of interest (not currently used)
folder_names = ['caca' for i in list(range(1, 61))]
valid_directories = [(name, folder_name)
                     for name, folder_name in zip(valid_vols_list, folder_names)]

# Path to info about recorders
recorders_dir = OUT_DIR / 'already-recorded-append.csv'

# Colours
red = Fore.RED + Style.BRIGHT
yellow = Fore.YELLOW + Style.BRIGHT
green = Fore.WHITE + Back.GREEN + Style.BRIGHT

# Main -------------------------------------

# Make sure paths exist
for path in [OUT_DIR, DESTINATION_DIR]:
    safe_makedir(path)

# Print logo
build_logo(__version__, logo_text='SD Card Copier', font='tiny')
print(
    tcolor("""
 = USE AT YOUR OWN RISK =
 Do not run this script until you have entered
 the recorder deployment information. This includes
 manually changing the 'Move_by' date if a recorder
 was left in place for longer than three days.
 Also see: `fieldwork-helper` in the docs
""", tstyle.rojoroto)
)

if warn_others:
    if 'nilomr' in str(OUT_DIR):
        print(
            '\n' + info + tstyle.BOLD +
            tcolor(str(len('This application will not work until you provide your own paths. See the README.')), tstyle.rojoroto))
        os._exit(0)

if check_for_drive:
    while True:
        if DATA_DIR.exists():
            break
        else:
            print(yellow + 'The Data drive is not mounted. Mount it.', end="\r")
            time.sleep(1)

# Store volumes that have been already copied
already_done = []
checked_cards = []

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

    # This is older code and can be made redundant at some point;
    # just take the right devices from the valid_devices list!
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

        if valid_audiomoths:
            # Get updated information about recorders.
            try:
                recorders_info = fetch_recorder_info(recorders_dir)
            except FileNotFoundError as e:
                print(info + tcolor(inspect.cleandoc("""
                You need to have a .csv file with information
                about recorder deployment before you can use this program"""), tstyle.rojoroto))
                sys.exit()

            except IndexError as e:
                print(info + tcolor(inspect.cleandoc(f"""The file {recorders_dir.name} is empty.
                You need to have a .csv file with information
                about recorder deployment before you can use this app"""), tstyle.rojoroto))
                sys.exit()
        # Open nautilus window
        if open_origin_window:
            for card in valid:
                open_window = f"nautilus '{card[0]}'"
                Popen(["/bin/bash", "-c", open_window])
                time.sleep(1)

        for card in valid:
            print(
                tcolor('\n' + f'Trying to copy {card[1]} ...', tstyle.mustard))

            if is_faceplate(card[0]):
                # If this is a faceplate card
                files = [os.path.join(card[0], i)
                         for i in os.listdir(card[0]) if i.endswith('.TXT')]
                # Skip card if there are no files
                if len(files) == 0:
                    print(f'Card {card[1]} seems to be empty, skipping.')
                    already_done.append(card[1])
                    continue
                # Open RT file
                try:
                    path = [
                        file for file in files if file.endswith('RT.TXT')][0]
                except:  # TODO: handle this!
                    print(
                        f'There is no RT file in this faceplate card ({card[1]}), skipping')
                    already_done.append(card[1])
                    continue

                if os.path.isfile(path):
                    tmp = pd.read_csv(path, sep='\s*\t\s*',
                                      header=0, engine='python')
                    cols = [
                        col for col in tmp.columns if 'TagID' in col]
                    if cols:
                        data = tmp.dropna(subset=[cols[0]]).query(
                            'Date != "Date"')
                    else:
                        continue
                else:
                    print('There is no RT file in this faceplate card, skipping')
                    continue
                # This try/except block is temporary /
                # need to add option to ask for faceplating date to avoid this issue
                try:
                    # Get first date in faceplate
                    f_datetime = pd.to_datetime(
                        data['Date']).to_list()[-1].date()

                    # Out folder name
                    faceplate_out = OUT_DIR / 'faceplates' / \
                        f'{str(f_datetime)}_{card[1]}'
                except:
                    faceplate_out = OUT_DIR / 'faceplates' / \
                        f'ENTER_DATE_{card[1]}'

            else:
                # If this is an Audiomoth card
                # List files in card
                files = [os.path.join(card[0], i)
                         for i in os.listdir(card[0]) if i.endswith('.WAV')]
                # Skip card if there are no files
                if len(files) == 0:
                    print(f'Card {card[1]} seems to be empty, skipping.')
                    already_done.append(card[1])
                    continue

                # get AM number
                am = int(card[1][2:4])

            # Otherwise, copy them to the right folder
            copied = []
            for file in files:
                if not is_faceplate(card[0]):
                    # Get date of file
                    filedate = pd.to_datetime(
                        Path(file).stem, format='%Y%m%d_%H%M%S')
                    # Get nestbox
                    nestbox = get_nestbox_id(
                        recorders_dir, recorders_info, card, am, filedate)
                    if not nestbox:
                        continue
                    # Copy file
                    target = DESTINATION_DIR / nestbox
                else:
                    target = faceplate_out

                t_file = target / Path(file).name

                if t_file.exists():
                    print(
                        f'File {Path(file).name} exists in destination {target}; skipping.')
                    continue
                else:
                    # Make sure that directory exists
                    safe_makedir(target)
                    # Copy
                    copy_with_progress(file, target)
                    # Add to copied list
                    copied.append(os.sep.join(
                        os.path.normpath(file).split(os.sep)[-2:]))

            # Successful?
            n_copied = len(copied)
            if n_copied > 0:
                print(
                    Fore.GREEN +
                    Style.BRIGHT +
                    f'\n{n_copied} out of {len(files)} file(s) succesfully copied from {card[1]}')
                # Save to register of copied files
                with open(OUT_DIR / 'copied.txt', 'a') as cp:
                    for item in copied:
                        cp.write("%s\n" % item)
            else:
                print(
                    red + f'\n{n_copied} out of {len(files)} file(s) copied from {card[1]}')

            # Unmount card, remove mount point
            try:
                p = find_sdiskpart(card[0])
            except psutil.Error:
                print('Something went wrong :D')

            while os.path.exists(card[0]):
                umount_and_rmdir(0, card)
                if verbose:
                    print('Trying to umount again')

            print(yellow + f'Done with {card[1]}. It is now safe to remove.\n')

            already_done.append(card[1])

    time.sleep(0.5)

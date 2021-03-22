#!/usr/bin/env python3

# TODO: mount any unmounted volumes automatically?

import inspect
import os
import re
import shutil
import subprocess
import time
from datetime import datetime
from getpass import getpass, getuser
from subprocess import PIPE, Popen, check_output

import pandas as pd
import psutil
from colorama import Back, Fore, Style, init
from pathlib2 import Path, PosixPath

from fieldwork_paths import DATA_DIR, OUT_DIR, PROJECT_DIR, safe_makedir

init(autoreset=True)

# Settings
skip_empty = False  # Wether to open a nautilus window
safe_copy = False  # Wether to ensure that files exist before allowing formatting

# Names to listen for (here AM codes)
AM_list = ['AM' + (str(i) if i > 10 else f"{i:02d}")
           for i in list(range(1, 61))]

# Folders of interest (not currently used)
folder_names = ['caca' for i in list(range(1, 61))]

valid_directories = [(name, folder_name)
                     for name, folder_name in zip(AM_list, folder_names)]

# Where to copy the files to
destination_directory = PROJECT_DIR

# Path to info about recorders
recorders_dir = PROJECT_DIR / 'resources' / 'fieldwork' / \
    str(datetime.now().year) / 'already-recorded.csv'

# Colours
red = Fore.RED + Style.BRIGHT
yellow = Fore.YELLOW + Style.BRIGHT
green = Fore.WHITE + Back.GREEN + Style.BRIGHT

# --


def get_mountedlist():
    return [card[card.find("/"):] for card in subprocess.check_output(
            ["/bin/bash", "-c", "lsblk"]).decode("utf-8").split("\n") if "/" in card]


def is_faceplate(dev):
    try:
        nm = Path(dev).name
        if nm[0] == 'F' and len(nm) == 5 and nm[1:4].isnumeric():
            return True
        else:
            return False
    except:
        return False


def yes_or_no(question):
    while "The answer is invalid":
        reply = str(input(question + " [y/n]: ")).lower().strip()
        if reply[0] == "y":
            return True
        elif reply[0] == "n":
            return False
        else:
            print("The answer is invalid")


bar = [
    "|     ",
    " |    ",
    "  |   ",
    "   |  ",
    "    | ",
    "     |",
    "    | ",
    "   |  ",
    "  |   ",
    " |    ",
]


def find_sdiskpart(path):
    path = os.path.abspath(path)
    while not os.path.ismount(path):
        path = os.path.dirname(path)
    p = [p for p in psutil.disk_partitions(
        all=True) if p.mountpoint == path.__str__()]
    l = len(p)
    if len(p) == 1:
        return p[0]
    raise psutil.Error


def get_wav_filenames(card):
    return [os.sep.join(os.path.normpath(file).split(os.sep)[-2:])
            for file in [os.path.join(card[0], i)
                         for i in os.listdir(card[0])
                         if i.endswith('.WAV')]
            ]


def parse_blkid(valid_directories, output):
    valid_devices = []
    output = [str(i).split(' ') for i in output.split(b'\n') if b'LABEL' in i]
    for ls in output:
        for sbls in ls:
            if sbls.startswith('LABEL'):
                name = re.findall(r'"(.*?)"', sbls)[0]
                if (
                    name[0] == 'F' and len(name) == 5 and
                    name[1:4].isnumeric() or
                    name in [am[0] for am in valid_directories]
                ):
                    devpath = str(ls[0]).replace(
                        ':', '').replace('b\'', '')
                    valid_devices.append([name, devpath])
    return valid_devices


def ensure_mount(valid_directories, password, checked_cards, already_done):
    devnull = open(os.devnull, 'wb')
    mounted = get_mountedlist()
    blkid = "sudo blkid"
    proc1 = Popen(["/bin/bash", "-c", blkid],
                  stdin=PIPE, stdout=PIPE)
    output, err = proc1.communicate(input=password.encode())
    valid_devices = parse_blkid(valid_directories, output)
    if not valid_devices:
        pass
    else:
        for dev in valid_devices:
            if any(dev[0] in s for s in mounted):
                continue
            elif dev[0] in already_done:
                continue
            else:
                # Mkdir
                target_dir = os.path.join(os.sep, 'media', getuser(), dev[0])
                mkdir = f"sudo mkdir -p {target_dir}"
                proc2 = Popen(["/bin/bash", "-c", mkdir],
                              stdin=PIPE, stdout=PIPE, stderr=devnull)
                out2, err2 = proc2.communicate(password.encode())
                # Mount
                dmount = f"sudo mount {dev[1]} {target_dir}"
                proc3 = Popen(["/bin/bash", "-c", dmount],
                              stdin=PIPE, stdout=PIPE, stderr=devnull)
                out3, err3 = proc3.communicate(password.encode())
                checked_cards.append(dev[0])
    return checked_cards


def umount_and_rmdir(password, card):
    devnull = open(os.devnull, 'wb')
    umount = f"sudo umount {card[0]}"
    proc4 = Popen(["/bin/bash", "-c", umount],
                  stdin=PIPE, stdout=PIPE, stderr=devnull)
    proc4.communicate(password.encode())
    # Delete mount point
    delmount = f"sudo rmdir {card[0]}"
    proc5 = Popen(["/bin/bash", "-c", delmount],
                  stdin=PIPE, stdout=PIPE, stderr=devnull)
    proc5.communicate(password.encode())
    # print(f'delete mountpoint returned {proc5.returncode}')

# Main -------------------------------------


print("""
                                  ,,,,
                                %@%&@&%                         
                              *@,    .*                         
                           //((((##,,,                          
                      ,(%#(,&%((#(/,,,                          
                   /((%(%###%&&%.,,,,                           
            ,  *(///.  .,**,..,,,,,,                             
        (/,            . . ,#,.                                 
 ___ ___    ___            ./. /  _   _ 
/ __|   \  | __|__ _ _ _ __  _* _| |_| |_ ___ _ _ 
\__ \ |) | | _/ _ \ '_| '  \/ _` |  _|  _/ -_) '_|
|___/___/  |_|\___/_| |_|_|_\__,_|\__|\__\___|_|  
""")

print(red + """
Warning: This application will automatically format any 
mounted volume with names matching a given pattern, 
currently [AM00, F0000]. USE AT YOUR OWN RISK
""")

while True:
    # some code here
    if yes_or_no('Do you want to continue?'):
        break
    else:
        quit()

# Get password from user
if 'password' not in locals():
    password = getpass("Please enter your password: ")

it = 0

# Store volumes that have been already formatted
already_done = []
checked_cards = []
devnull = open(os.devnull, 'wb')


while True:
    print('Scanning for cards', bar[it % len(bar)], end="\r")
    time.sleep(.1)
    it += 1

    # Mount any cards not already mounted
    # (sometimes automount does not work)
    checked_cards = ensure_mount(
        valid_directories, password, checked_cards, already_done)

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

            print(yellow + '\n' + f'Trying to format {card[1]} ...')

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
                            print(
                                f'One or more files in {card[1]} have not yet been copied, skipping')
                            continue
                    except:
                        if (OUT_DIR / 'copied.txt').is_file():
                            print('There is an issue with /copied.txt, skipping.')
                        else:
                            print(
                                '/copied.txt not found, use the `copy-cards` app at least once. Skipping')
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
            proc1.communicate(password.encode())

            # Format card
            format = f"sudo mkfs.vfat -F32 -v {p.device}"
            proc2 = Popen(["/bin/bash", "-c", format],
                          stdin=PIPE, stdout=PIPE, stderr=devnull)
            proc2.communicate(password.encode())

            # Rename card
            relabel = f"sudo fatlabel {p.device} {card[1]}"
            proc3 = Popen(["/bin/bash", "-c", relabel],
                          stdin=PIPE, stdout=PIPE, stderr=devnull)
            proc3.communicate(password.encode())

            umount_and_rmdir(password, card)

            if proc2.returncode == 0:
                while os.path.exists(card[0]):
                    umount_and_rmdir(password, card)
                    print('trying to umount again')
                print(Fore.GREEN + Style.BRIGHT +
                      f'Successfully formatted {card[1]}. You can now remove it')
                already_done.append(card[1])
            else:
                print(Fore.RED + Style.BRIGHT +
                      f'Error when trying to format {card[1]}. See message above')

    time.sleep(1)

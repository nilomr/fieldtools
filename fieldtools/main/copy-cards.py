#!/usr/bin/env python3

from fieldtools.version import __version__
from pathlib2 import Path, PosixPath
from colorama import Back, Fore, Style, init
import psutil
import pandas as pd
from datetime import datetime
import time
from subprocess import PIPE, Popen, check_output
import shutil
import os
from getpass import getpass, getuser
import re
import inspect
import glob
from sh import mount
from fieldtools.src.paths import DATA_DIR, OUT_DIR, PROJECT_DIR, safe_makedir


init(autoreset=True)

# Settings
open_origin_window = False  # Whether to open a nautilus window
verbose = False  # Whether to print errors for debugging

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
    return [card[card.find("/"):] for card in check_output(
            ["/bin/bash", "-c", "lsblk"]).decode("utf-8").split("\n") if "/" in card]


def progress_percentage(perc, width=None):
    # By flutefreak7,
    # https://stackoverflow.com/a/48450305
    # This will only work for python 3.3+ due to use of
    # os.get_terminal_size the print function etc.

    FULL_BLOCK = '█'
    # this is a gradient of incompleteness
    INCOMPLETE_BLOCK_GRAD = ['░', '▒', '▓']

    assert(isinstance(perc, float))
    assert(0. <= perc <= 100.)
    # if width unset use full terminal
    if width is None:
        width = os.get_terminal_size().columns
    # progress bar is block_widget separator perc_widget : ####### 30%
    max_perc_widget = '[100.00%]'  # 100% is max
    separator = ' '
    blocks_widget_width = width - len(separator) - len(max_perc_widget)
    assert(blocks_widget_width >= 10)  # not very meaningful if not
    perc_per_block = 100.0/blocks_widget_width
    # epsilon is the sensitivity of rendering a gradient block
    epsilon = 1e-6
    # number of blocks that should be represented as complete
    full_blocks = int((perc + epsilon)/perc_per_block)
    # the rest are "incomplete"
    empty_blocks = blocks_widget_width - full_blocks

    # build blocks widget
    blocks_widget = ([FULL_BLOCK] * full_blocks)
    blocks_widget.extend([INCOMPLETE_BLOCK_GRAD[0]] * empty_blocks)
    # marginal case - remainder due to how granular our blocks are
    remainder = perc - full_blocks*perc_per_block
    # epsilon needed for rounding errors (check would be != 0.)
    # based on reminder modify first empty block shading
    # depending on remainder
    if remainder > epsilon:
        grad_index = int((len(INCOMPLETE_BLOCK_GRAD)
                          * remainder)/perc_per_block)
        blocks_widget[full_blocks] = INCOMPLETE_BLOCK_GRAD[grad_index]

    # build perc widget
    str_perc = '%.2f' % perc
    # -1 because the percentage sign is not included
    perc_widget = '[%s%%]' % str_perc.ljust(len(max_perc_widget) - 3)

    # form progressbar
    progress_bar = '%s%s%s' % (''.join(blocks_widget), separator, perc_widget)
    # return progressbar as string
    return ''.join(progress_bar)


def copy_progress(copied, total):
    print('\r' + progress_percentage(100*copied/total, width=30), end='')


def fetch_recorder_info(recorders_dir):
    recorders_info = pd.read_csv(
        recorders_dir).query('Nestbox != "Nestbox"')
    # Stop if no info on file
    if len(recorders_info) == 0:
        print(IndexError(f'{recorders_dir.name} is empty'))

    recorders_info['Deployed'] = pd.to_datetime(
        recorders_info['Deployed'], format='%Y-%m-%d')
    recorders_info['Move_by'] = pd.to_datetime(
        recorders_info['Move_by'], format='%Y-%m-%d')

    return recorders_info


def copyfile(src, dst, *, follow_symlinks=True):
    """Copy data from src to dst.

    If follow_symlinks is not set and src is a symbolic link, a new
    symlink will be created instead of copying the file it points to.

    """
    # By flutefreak7,
    # https://stackoverflow.com/a/48450305
    if shutil._samefile(src, dst):
        raise shutil.SameFileError(
            "{!r} and {!r} are the same file".format(src, dst))

    for fn in [src, dst]:
        try:
            st = os.stat(fn)
        except OSError:
            # File most likely does not exist
            pass
        else:
            # XXX What about other special files? (sockets, devices...)
            if shutil.stat.S_ISFIFO(st.st_mode):
                raise shutil.SpecialFileError("`%s` is a named pipe" % fn)

    if not follow_symlinks and os.path.islink(src):
        os.symlink(os.readlink(src), dst)
    else:
        size = os.stat(src).st_size
        with open(src, 'rb') as fsrc:
            with open(dst, 'wb') as fdst:
                copyfileobj(fsrc, fdst, callback=copy_progress, total=size)
    return dst


def copyfileobj(fsrc, fdst, callback, total, length=16*1024):
    copied = 0
    while True:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)
        copied += len(buf)
        callback(copied, total=total)


def copy_with_progress(src, dst, *, follow_symlinks=True):

    if type(dst) == PosixPath:
        dst = str(dst)
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
        print(f'\n{Path(dst).name}')

    copyfile(src, dst, follow_symlinks=follow_symlinks)
    shutil.copymode(src, dst)
    return dst


def is_faceplate(dev):
    try:
        nm = Path(dev).name
        if nm[0] == 'F' and len(nm) == 5 and nm[1:4].isnumeric():
            return True
        else:
            return False
    except:
        return False


def get_nestbox_id(recorders_dir, recorders_info, card, am, filedate):
    nestbox = recorders_info[(recorders_info['AM'] == str(am)) | (recorders_info['AM'] == int(am)) &
                             (recorders_info['Deployed'] < filedate) &
                             (recorders_info['Move_by'] >= filedate)]['Nestbox']
    if len(nestbox) == 1:
        nestbox = nestbox.iat[0]
        return nestbox
    elif len(nestbox) > 1:
        print('\n\n' + inspect.cleandoc(f"""
                There are more than one row compatible with this
                AM / date combination ({card[1]}, {filedate})"""))
    else:
        print('\n\n' + inspect.cleandoc(f"""
                There are no rows compatible with this
                AM / date combination ({card[1]}, {filedate}).
                Check that you have entered the deployment information in
                {recorders_dir}"""))


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
    "|=          |",
    "| =         |",
    "|  =        |",
    "|   =       |",
    "|    =      |",
    "|     =     |",
    "|      =    |",
    "|       =   |",
    "|        =  |",
    "|         = |",
    "|          =|",
    "|         = |",
    "|        =  |",
    "|       =   |",
    "|      =    |",
    "|     =     |",
    "|    =      |",
    "|   =       |",
    "|  =        |",
    "| =         |",
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
 ___ ___     ___    ./.   _
/ __|   \   / __|___ _*__(_)___ _ _
\__ \ |) | | (__/ _ \ '_ \ / -_) '_|
|___/___/   \___\___/ .__/_\___|_|
                    |_|
""")

print(red + """
Warning: Do not run this script until you have
already entered and checked the relevant recorder
deployment information. Crucially, this includes
manually changing the 'Move_by' date if a recorder
was left in place for longer than three days.
Also see: `fieldwork-helper` in the docs.\n
""")

while True:
    if yes_or_no('Do you want to continue?'):
        break
    else:
        quit()

# while True:
#     if DATA_DIR.exists():
#         break
#     else:
#         print(yellow + 'The Data drive is not mounted. Mount it.', end="\r")
#         time.sleep(1)

# Ensure that destination exists
safe_makedir(destination_directory)

# Store volumes that have been already copied
already_done = []
checked_cards = []

# Counter (for progress bar)
it = 0

# Get password from user
if 'password' not in locals():
    password = getpass("Please enter your password: ")


while True:
    print('Scanning for cards', bar[it % len(bar)], end="\r")
    time.sleep(.1)
    it += 1

    # Mount any cards not already mounted
    # (sometimes automount does not work)
    checked_cards = ensure_mount(
        valid_directories, password, checked_cards, already_done)

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
        # Get updated information about recorders.
        try:
            recorders_info = fetch_recorder_info(recorders_dir)
        except FileNotFoundError as e:
            print(e, """\nYou need to have a .csv file with information 
        about recorder deployment before you can use this program""")

        # Open nautilus window
        if open_origin_window:
            for card in valid:
                open_window = f"nautilus '{card[0]}'"
                Popen(["/bin/bash", "-c", open_window])
                time.sleep(1)

        for card in valid:

            print(yellow + f'\nTrying to copy {card[1]} ...')

            if is_faceplate(card[0]):
                # If this is a faceplate card
                files = [os.path.join(card[0], i)
                         for i in os.listdir(card[0]) if i.endswith('.TXT')]
                # Skip card if there are no files
                if len(files) == 0:
                    print(f'Card {card[0]} seems to be empty, skipping.')
                    continue
                # Open RT file
                path = [file for file in files if file.endswith('RT.TXT')][0]
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
                # Get first date in faceplate
                f_datetime = pd.to_datetime(data['Date']).to_list()[-1].date()

                # Out folder name
                faceplate_out = OUT_DIR / 'faceplates' / \
                    f'{str(f_datetime)}_{card[1]}'

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
                    target = destination_directory / nestbox
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
                umount_and_rmdir(password, card)
                if verbose:
                    print('Trying to umount again')

            print(yellow + f'Done with {card[1]}. It is now safe to remove.\n')

            already_done.append(card[1])

    time.sleep(1)

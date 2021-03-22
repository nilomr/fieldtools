
# Note:
# This will only work if observations are 'sandwiched' between field worker IDs.

# Libraries
import os
import pandas as pd
from itertools import islice
from pathlib2 import Path
import numpy as np
from paths import DATA_PATH

# Paths
PROJECT_DIR = Path("__file__").resolve().parents[3]  # ! Ego = notebook
txt_dir = PROJECT_DIR / 'resources' / 'faceplate_samples'

# Get file names
try:
    txt_files = [file for file in os.listdir(
        txt_dir) if file.endswith('.txt') or file.endswith('.TXT')]
except:
    raise FileNotFoundError('There are no .txt files in this directory')

# Input
id_code = '01103FD3FB'  # TODO: store this and use, give option to change
nestbox_list = ['A1', 'A2', 'A3']
min_time_diff = 0.5

# Read files
for file in txt_files:
    path = os.path.join(txt_dir, file)
    if os.path.isfile(path):
        tmp = pd.read_csv(path, sep='\s*\t\s*', header=0)
        if 'TagID_1' in tmp.columns:
            data = tmp  # tmp.dropna(subset=['TagID_1'])
            del(tmp)
        else:
            del(tmp)
            continue


data['Date'] = pd.to_datetime(data['Date'])
date2 = pd.Series(data['Date'][1:], name='Date2')
date2.reset_index(drop=True, inplace=True)
date2.rename({'Date': 'Date2'}, axis='columns', inplace=True)

data = pd.concat([data, date2], axis=1)


data['Time_diff'] = data['Date2'] - data['Date']
data['Time_diff'] = data['Time_diff']/np.timedelta64(1, 'm')


id_list = data['TagID_1'].to_list()
diffs_list = data['Time_diff'].to_list()


def get_ids(input=[str], separator=str, data=data):
    separator_indexes = [index for index,
                         word in enumerate(input) if word == separator]
    ids = []
    indices = []
    diffs = []

    for start, end in zip(separator_indexes[:-1], separator_indexes[1:]):
        id = list(input[start + 1:end])
        diff = data['Time_diff'][start:end].tolist()
        if id or any(d > min_time_diff for d in diff):
            if not id:
                ids.append(np.nan)
            else:
                ids.append(id[0] if len(id) == 1 else id)
            indices.append((start, end))
            diffs.append(diff)

    return ids, indices, diffs


# Get IDs between field worker ID
ids, indices, diffs = get_ids(input=id_list, separator=id_code)

# Make df with relevant information
if len(nestbox_list) == len(ids):
    id_dict = {nestbox: id for nestbox, id in zip(nestbox_list, ids)}
    times = []
    for index in indices:
        times.append(data['Date'][index[0]+1])
    df = pd.DataFrame([id_dict], ['id']).T
    df = df.rename_axis('nestbox').reset_index()
    df['time'] = times
elif len(nestbox_list) > len(id_list):
    raise IndexError('There are more nestboxes than readings')
else:
    raise IndexError('There are more readings than nestboxes')

# TODO:
# Save df separatedly and also append to master lists
# - one with detected birds
# - one with nestboxes to be recorded that can be used by the other program
# - print and save this batch only for record-keeping and for manual upload to database
# Retrieve master list and

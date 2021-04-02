#!/usr/bin/env python3

# Dependencies --------------------------

import numpy as np
import subprocess
import time
from datetime import date, datetime, timedelta
from pprint import pprint
from textwrap import dedent

import pandas as pd
import pygsheets
from fieldtools.src.aesthetics import (arrow, asterbar, build_logo, info,
                                       menu_aes, print_dict, qmark, tcolor,
                                       tstyle)
from fieldtools.src.funs import (get_nestbox_update, get_recorded_gretis,
                                 get_single_gsheet, order, reconstruct_path,
                                 split_path, workers, write_gpx, yes_or_no)
from fieldtools.src.paths import (DATA_DIR, EGO_DIR, OUT_DIR, PROJECT_DIR,
                                  safe_makedir)
from fieldtools.version import __version__
from pathlib2 import Path
from PyInquirer import prompt
from tabulate import tabulate

# Options

verbose = False


# Paths

FIELD_DIR = DATA_DIR / "resources" / "fieldwork" / str(date.today().year)
# Might want to save to FIELD_DIR instead for easy backup
GPX_DIR = OUT_DIR / "gpx-files"

RPLOTS = EGO_DIR / "plot-new-boxes.R"
coords_csv = PROJECT_DIR / "resources" / \
    'nestboxes' / "nestbox_coords_transformed.csv"
recorded_csv = OUT_DIR / "already-recorded.csv"


class Error(Exception):
    pass


# Main

# Make sure paths exist
for path in [OUT_DIR, FIELD_DIR]:
    safe_makedir(path)

# Print logo
logo_text = 'Fieldwork helper_'
font = 'tiny'
build_logo(__version__, logo_text, font)


while True:

    # Get coordinates for all nestboxes
    nestbox_coords = pd.read_csv(coords_csv)  # .query('`box type` == "GT"')
    nestbox_coords["Nestbox"] = nestbox_coords["nestbox"].str.upper()

    # First menu
    print('')
    questions = [
        {
            'type': 'list',
            'message': ' Options',
            'name': 'option',
            'choices': [
                {'name': 'Get a progress report'},
                {'name': 'Enter deployment data'},
                {'name': 'Prepare faceplating plan'},
                {'name': 'Exit the app'},
            ],
            'validate': lambda answer: 'You must choose one option.'
            if len(answer) == 0 else True
        }
    ]

    answer = prompt(questions, style=menu_aes)['option']
    print('')

    if answer == 'Exit the app':
        break

    elif answer == 'Enter deployment data':  # Enter new nestboxes and recorders
        # * Enter recorder data while loop
        while True:

            # * Enter nestboxes while loop
            print(qmark + tstyle.BOLD +
                  tcolor(
                      'Please enter all nestbox names separated by a single space:', tstyle.mustard) +
                  '\ne.g., SW84A EX20 C47'
                  )
            while True:

                names = input().upper().strip().split(" ")

                if len(names) == sum(nestbox_coords["Nestbox"].isin(names)):
                    print("All nestbox names exist")
                    break
                else:
                    nwrong = str(len(names) -
                                 sum(nestbox_coords["Nestbox"].isin(names)))
                    print(
                        tcolor(
                            f'{nwrong} out of {str(len(names))} entered names do not exist, try again:', tstyle.rojoroto)
                    )
                    continue

            # * Enter recorders while loop
            print('')
            print(qmark + tstyle.BOLD +
                  tcolor(
                      'Now enter the recorder numbers, also separated by spaces:', tstyle.mustard) +
                  '\ne.g., 01 23 15'
                  )
            while True:

                recorders = input().upper().strip().split(" ")

                try:
                    kk = pd.to_numeric(recorders)
                except:
                    print(
                        tcolor(
                            "The string contains non-numerical characters, try again:", tstyle.rojoroto)
                    )
                    continue

                if len(names) != len(recorders):
                    print(
                        tcolor(
                            "The number of recorders does not match the number of nestboxes, try again:", tstyle.rojoroto)
                    )
                    continue
                elif any(len(str(i)) != 2 for i in recorders):
                    print(
                        tcolor(
                            "Recorder numbers can only have two digits, try again:", tstyle.rojoroto)
                    )
                    continue
                else:
                    break

            user_entered = dict(zip(names, recorders))
            print('You have entered:')
            print_dict(user_entered)
            question = '\n' + qmark + tstyle.BOLD + \
                tcolor('Is this correct?', tstyle.mustard)
            print('')
            if yes_or_no(question):
                break
            else:
                continue

        # * End of recorder data enter loop

        # * Enter date block
        print('')
        if not yes_or_no(qmark + tstyle.BOLD +
                         tcolor(
                             f"Is {str(date.today())} the date when you deployed these recorders?", tstyle.mustard)):
            print("Enter the correct date in the same format:")
            day = input()
            day = datetime.strptime(day, "%Y-%m-%d").date()
        else:
            day = date.today()

        # Get coordinates, add date added, add recorder number and append
        new_boxes = nestbox_coords.query(
            "Nestbox in @names")[["Nestbox", "longitude", "latitude"]]
        new_boxes["AM"] = new_boxes["Nestbox"].map(user_entered)
        new_boxes["Deployed"] = str(day)
        new_boxes["Move_by"] = str(day + timedelta(days=3))
        new_boxes = order(new_boxes, ["Nestbox", "AM"])

        with open(recorded_csv, 'a') as f:
            new_boxes.to_csv(f, header=True, index=False)

        print(tstyle.BOLD +
              tcolor(
                  f"Done. You can check all added nestboxes at {str(recorded_csv.name)}", tstyle.teal)
              )
        continue

    elif answer == 'Get a progress report':  # * get nestboxes to be visited

        # Get updated list of nestboxes from google sheets
        which_greati = get_nestbox_update().replace(
            'nan', 0).fillna(0).replace('n/a', 0)
        # TODO: get number of blutis and gretis separatedly
        already_recorded, diff_df = get_recorded_gretis(
            recorded_csv, nestbox_coords, which_greati)

        # Print basic info
        print(
            '\n' + info + tstyle.BOLD +
            tcolor(str(len(already_recorded)), tstyle.teal) + " already recorded\n" +
            info + tstyle.BOLD +
            tcolor(str(len(diff_df)), tstyle.teal) + " to be recorded\n"
        )
        # Go back to main menu if there is nothing to see
        if len(already_recorded) == 0 and len(diff_df) == 0:
            continue

        # Fix and print new great tit data
        table_p = diff_df.drop(["longitude", "latitude", 'x', 'y', 'nestbox',
                                'box type', 'Added'], 1).rename(columns={"section": "Section"})
        print(tabulate(table_p, headers="keys",
                       showindex=False, tablefmt="simple").replace('\n', '\n  ').replace('Nestbox', '  Nestbox'))

        # Save to a .csv
        newpath = OUT_DIR / str("new_" + str(date.today()) + ".csv")
        diff_df.to_csv(newpath)
        diff_df.to_csv(str(OUT_DIR / "toberecorded.csv"), index=False)

        # Second menu
        print('')
        questions = [
            {
                'type': 'list',
                'message': 'Options',
                'name': 'option',
                'choices': [
                    {'name': 'Prepare fieldwork plan and maps'},
                    {'name': 'Go back to the main menu'},
                    {'name': 'Exit the app'},
                ],
                'validate': lambda answer: 'You must choose one option.'
                if len(answer) == 0 else True
            }
        ]

        answer = prompt(questions, style=menu_aes)['option']
        print('')

        if answer == 'Exit the app':
            break

        elif answer == 'Go back to the main menu':
            continue

        elif answer == 'Prepare fieldwork plan and maps':
            # Plot with R + ggplot2
            diff_df.to_csv(str(OUT_DIR / "toberecorded.csv"), index=False)
            it = 0
            proc1 = subprocess.Popen(
                ["Rscript", str(RPLOTS)], shell=False, stdout=subprocess.PIPE)
            while proc1.poll() is None:
                print('Making and saving plots',
                      asterbar[it % len(asterbar)], end="\r")
                time.sleep(.1)
                it += 1
            outdir = reconstruct_path(split_path(str(OUT_DIR))[-4:])
            print(tstyle.BOLD +
                  tcolor(
                      f"Done. You can check your plots at {outdir}", tstyle.teal)
                  )

            # Export gpx
            while True:
                today = str(date.today())
                tomorrow = str(date.today() + timedelta(days=1))
                # GPX file menu
                print('')
                questions = [
                    {
                        'type': 'list',
                        'message': 'Which .gpx file do you want?',
                        'name': 'option',
                        'choices': [
                            {'name': f"Today's ({today})"},
                            {'name': f"Tomorrow's ({tomorrow})"},
                            {'name': 'None'},
                        ],
                        'validate': lambda answer: 'You must choose one option.'
                        if len(answer) == 0 else True
                    }
                ]
                answer = prompt(questions, style=menu_aes)['option']
                print('')

                if answer == f"Today's ({today})":
                    move_today = (
                        pd.read_csv(recorded_csv)
                        .query('Nestbox != "Nestbox"')
                        .query("Move_by == @today")
                    )
                    write_gpx(GPX_DIR / str(str(today) + ".gpx"),
                              diff_df, move_today)

                    outdir = reconstruct_path(split_path(str(GPX_DIR))[-5:])
                    print(tstyle.BOLD +
                          tcolor(f"Done. You can find your .gpx file at {outdir}", tstyle.teal))
                    break

                elif answer == f"Tomorrow's ({tomorrow})":
                    move_tomorrow = (
                        pd.read_csv(recorded_csv)
                        .query('Nestbox != "Nestbox"')
                        .query("Move_by == @tomorrow")
                    )
                    write_gpx(
                        GPX_DIR / str(str(tomorrow) +
                                      ".gpx"), diff_df, move_tomorrow
                    )
                    outdir = reconstruct_path(split_path(str(GPX_DIR))[-5:])
                    print(tstyle.BOLD +
                          tcolor(f"Done. You can find your .gpx file at {outdir}", tstyle.teal))
                    break

                elif answer == "None":
                    break
            continue

    elif answer == 'Prepare faceplating plan':

        # Area menu
        print('')
        questions = [
            {
                'type': 'list',
                'message': 'Select a nest round',
                'name': 'option',
                'choices': [
                    {'name': 'Bean'},
                    {'name': 'Broad Oak'},
                    {'name': 'Common Piece'},
                    {'name': 'Extra'},
                    {'name': 'Great Wood'},
                    {'name': 'Marley'},
                    {'name': 'Marley Plantation'},
                    {'name': 'Singing Way'},
                    {'name': 'None: Go back to the main menu'},
                ],
                'validate': lambda answer: 'You must choose one option.'
                if len(answer) == 0 else True
            }
        ]

        answer = prompt(questions, style=menu_aes)['option']
        print('')

        if answer == 'None: Go back to the main menu':
            continue

        # Get the data frm the selected round
        name = workers.rounds_dict[answer]
        roundkey = workers.gdict[name]
        round_df = get_single_gsheet(name, roundkey)

        # Get the data from faceplating
        def get_full_faceplate_info():
            gc = pygsheets.authorize(
                service_file=str(PROJECT_DIR / "private" /
                                 "client_secret.json")
            )
            facekey = '1NToFktrKMan-jlGYnASMM_AXSv1gwG2dYqjTGCY-6lw'  # The faceplating sheet
            faceplate_info = (
                gc.open_by_key(facekey)[0]
                .get_as_df(has_header=True, include_tailing_empty=False))
            return faceplate_info
        faceplate_df = get_full_faceplate_info().query('Nestbox == Nestbox')
        idd = faceplate_df.query('Species == "g" or Species == "b"')[
            'Nestbox'].tolist()
        # Get blue tit only boxes
        bluti_boxes = nestbox_coords.query('`box type` == "BT"')[
            'Nestbox'].tolist()

        # Get already recorded boxes
        if not Path(recorded_csv).exists():
            print(info + '.csv file with recorded nestboxes does not exist, creating it.')
            recorded_empty = pd.DataFrame(
                columns=['Nestbox', 'AM', 'longitude', 'latitude', 'Deployed', 'Move_by'])
            recorded_empty.to_csv(recorded_csv, index=False)
        try:
            already_recorded = (
                pd.read_csv(recorded_csv)
                .filter(["Nestbox"])
                .query('Nestbox != "Nestbox"')
                ['Nestbox'].tolist()
            )
        except:
            already_recorded = []

    # Avoid different source formatting issues
    round_df = round_df.astype(str)
    round_df['Nest'] = round_df['Nest'].replace('no', np.nan)
    # Query for relevant data
    result = round_df.query(
        'Nestbox not in @idd and Nestbox not in @bluti_boxes and Nestbox not in @already_recorded and Nest >= "2"')
    # Sort for ease of reading
    result = result.sort_values(
        ['Eggs', 'Nest'], ascending=[False, False])

    print(tabulate(result, headers="keys",
                   showindex=False, tablefmt="simple").replace('\n', '\n  ').replace('Nestbox', '  Nestbox'))
    print('\n  N: ' + str(len(result)))
    continue

    #     .filter(['Nestbox', 'Species'])
    #     .query('Species == "g" or Species == "G" or Species == "sp=g"')
    # )

# print(Fore.BLACK + Back.WHITE + which_greati.groupby(['Owner']).size().to_markdown())

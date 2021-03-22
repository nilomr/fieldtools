#!/usr/bin/env python3

# Dependencies --------------------------

from cfonts import render, say
import os
import subprocess
from datetime import date, datetime, timedelta
from pprint import pprint
from textwrap import dedent
from cfonts.consts import FONTFACES

import numpy as np
import pandas as pd
import pygsheets
from colorama import Back, Fore, Style, init
from openpyxl import load_workbook
from pathlib2 import Path, PosixPath
from PyInquirer import prompt
from tqdm.auto import tqdm
from tabulate import tabulate


from fieldwork_paths import (DATA_DIR, EGO_DIR, OUT_DIR, PROJECT_DIR,
                             safe_makedir)
from aes import tstyle, tcolor, arrow, info, menu_aes

init(autoreset=True)

# Paths -----------------------------------

version = '0.1.0'  # TODO: get this from setup file

FIELD_DIR = DATA_DIR / "resources" / "fieldwork" / str(date.today().year)
# Might want to save to FIELD_DIR instead for easy backup
GPX_DIR = OUT_DIR / "gpx-files"

RPLOTS = EGO_DIR / "plot-new-boxes.R"
coords_csv = PROJECT_DIR / "resources" / \
    'nestboxes' / "nestbox_coords_transformed.csv"
recorded_csv = OUT_DIR / "already-recorded.csv"


class Error(Exception):
    pass


# Functions -------------------------------


def append_df_to_excel(
    filename,
    df,
    sheet_name="Sheet1",
    startrow=None,
    truncate_sheet=False,
    **to_excel_kwargs
):
    """
    Append a DataFrame [df] to existing Excel file [filename]
    into [sheet_name] Sheet.
    If [filename] doesn't exist, then this function will create it.

    Parameters:
      filename : File path or existing ExcelWriter
                 (Example: '/path/to/file.xlsx')
      df : dataframe to save to workbook
      sheet_name : Name of sheet which will contain DataFrame.
                   (default: 'Sheet1')
      startrow : upper left cell row to dump data frame.
                 Per default (startrow=None) calculate the last row
                 in the existing DF and write to the next row...
      truncate_sheet : truncate (remove and recreate) [sheet_name]
                       before writing DataFrame to Excel file
      to_excel_kwargs : arguments which will be passed to `DataFrame.to_excel()`
                        [can be dictionary]

    Returns: None
    """

    # ignore [engine] parameter if it was passed
    if "engine" in to_excel_kwargs:
        to_excel_kwargs.pop("engine")

    writer = pd.ExcelWriter(filename, engine="openpyxl")

    # Python 2.x: define [FileNotFoundError] exception if it doesn't exist
    try:
        FileNotFoundError
    except NameError:
        FileNotFoundError = IOError

    try:
        # try to open an existing workbook
        writer.book = load_workbook(filename)

        # get the last row in the existing Excel sheet
        # if it was not specified explicitly
        if startrow is None and sheet_name in writer.book.sheetnames:
            startrow = writer.book[sheet_name].max_row

        # truncate sheet
        if truncate_sheet and sheet_name in writer.book.sheetnames:
            # index of [sheet_name] sheet
            idx = writer.book.sheetnames.index(sheet_name)
            # remove [sheet_name]
            writer.book.remove(writer.book.worksheets[idx])
            # create an empty sheet [sheet_name] using old index
            writer.book.create_sheet(sheet_name, idx)

        # copy existing sheets
        writer.sheets = {ws.title: ws for ws in writer.book.worksheets}
    except FileNotFoundError:
        # file does not exist yet, we will create it
        pass

    if startrow is None:
        startrow = 0

    # write out the new sheet
    df.to_excel(writer, sheet_name, startrow=startrow, **to_excel_kwargs)

    # save the workbook
    writer.save()


def safe_makedir(FILE_DIR):
    """Make a safely nested directory.
    Args:
        FILE_DIR (str or PosixPath): Path to be created.
    """
    if type(FILE_DIR) == str:
        if "." in os.path.basename(os.path.normpath(FILE_DIR)):
            directory = os.path.dirname(FILE_DIR)
        else:
            directory = os.path.normpath(FILE_DIR)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except FileExistsError as e:
                # multiprocessing can cause directory creation problems
                print(e)
    elif type(FILE_DIR) == PosixPath:
        # if this is a file
        if len(FILE_DIR.suffix) > 0:
            FILE_DIR.parent.mkdir(parents=True, exist_ok=True)
        else:
            try:
                FILE_DIR.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                if e.errno != 17:
                    print("Error:", e)


def yes_or_no(question):
    while "The answer is invalid":
        reply = str(input(question + " (y/n): ")).lower().strip()
        if reply[0] == "y":
            return True
        if reply[0] == "n":
            return False


def write_gpx(filename, newboxes, tocollect):
    """Writes .gpx file to disk, containing 
    a) all great tit nestboxes that haven't been recorded (in green),
    b) nestboxes where recorders need to be collected (in red) and
    c) nestboxes that haven't been recored and have eggs (helipad symbol).

    Args:
        filename (PosixPath): path including filename and extension (.gpx) where to output file.
        newboxes (DataFrame): DataFrame containing all new boxes, with ['Nestbox', 'x', 'y'] columns.
        tocollect (DataFrame): DataFrame containing boxes from n days ago,  with ['Nestbox', 'x', 'y'] columns.
    """
    safe_makedir(filename)
    gpxfile = open(str(filename), "w")
    gpxfile.write(
        '<?xml version="1.0"?><gpx version="1.1" creator="Nilo Merino Recalde" >'
    )

    try:
        allpoints = newboxes.query(
            'Eggs == "no"').filter(["Nestbox", "longitude", "latitude"])
        allpoints_transformed = allpoints.assign(
            **{"lon": allpoints["longitude"], "lat": allpoints["latitude"]}
        ).to_dict(orient="records")

        for box in allpoints_transformed:
            poi = '<wpt lat="{}" lon="{}"><name>{}</name><sym>{}</sym></wpt>'.format(
                box["lat"], box["lon"], box["Nestbox"], "poi_green"
            )
            gpxfile.write(poi)

    except Exception:
        pass

    try:
        eggs = newboxes.query('Eggs != "no"').filter(
            ["Nestbox", "longitude", "latitude"])
        eggs_transformed = eggs.assign(
            **{"lon": eggs["longitude"], "lat": eggs["latitude"]}
        ).to_dict(orient="records")

        for box in eggs_transformed:
            poi = '<wpt lat="{}" lon="{}"><name>{}</name><sym>{}</sym></wpt>'.format(
                box["lat"], box["lon"], box["Nestbox"], "helipad"
            )
            gpxfile.write(poi)

    except Exception:
        pass

    try:
        collect = tocollect.filter(["Nestbox", "longitude", "latitude"])
        collect_transformed = collect.assign(
            **{"lon": collect["longitude"], "lat": collect["latitude"]}
        ).to_dict(orient="records")

        for box in collect_transformed:
            poi = '<wpt lat="{}" lon="{}"><name>{}</name><sym>{}</sym></wpt>'.format(
                box["lat"], box["lon"], box["Nestbox"], "poi_red"
            )
            gpxfile.write(poi)

    except Exception:
        pass

    gpxfile.write("</gpx>")
    gpxfile.close()


def order(frame, var):
    if type(var) is str:
        var = [var]  # let the command take a string or list
    varlist = [w for w in frame.columns if w not in var]
    frame = frame[var + varlist]
    return frame


def get_nestbox_update():
    gc = pygsheets.authorize(
        service_file=str(PROJECT_DIR / "private" / "client_secret.json")
    )
    # Download and append personal sheets
    workerdict = {  # ! Change every year
        "Anett": "1e-So1BfXqhDDSqYSVVDllig_saDUk2d0zwRpwsVi0iI",
        "Joe": "1lOjeo7EHy1qe8rqj-T6QsiTxISLebH-GolJh1DrIWL8",
        "Nilo": "1qII34MKHEq3Sl0a86t2EObqcXii3Sw6x3AlDRaO-caA",
        "Kristina": "1OBjYxloyuCEqpcM_C3cDjNiHb2k1LN7hnthAbKoKhS0",
        "Keith": "1T17oU0sHK3D3ocHSQThXSPy0oZmvcEu0oHE99-Mto7U",
        "Julia": "1E3MkhVZvQXLLd3vuaz4I6mnVFOZbse9Nwbavhqyw8Qw",
        "Carys": "1toHQ4R2btmQdMzVFgtlC6pE67unmHY3i0qp-BOfkjUc",
        "Sam": "1ipjQXcPSe-_-bhDRlLn_TulgyrFGho3VYttn9cOMcbQ",
        # MISSING SAM!!!!!!!!
    }
    which_greati = pd.DataFrame(columns=["Nestbox", "Owner"])

    for worker, googlekey in tqdm(
        workerdict.items(),
        desc=arrow + "Downloading field worker data",
        position=0,
        leave=True,
        bar_format='{desc}: {percentage:3.0f}%'
    ):
        name = worker
        worker = gc.open_by_key(googlekey)[0].get_as_df(has_header=False)
        worker = worker.rename(
            columns=worker.iloc[0]).drop(worker.index[0])
        if "" in worker.columns:
            worker = worker.drop([""], axis=1)
        if name == "Sam":
            worker = (
                worker.rename(columns={"Num eggs": "Eggs"})
                .rename(columns={"number": "Nestbox"})
                .query("Nestbox == Nestbox")
                .query('Species == "g" or Species == "G" or Species == "sp=g"')
                .filter(["Nestbox", "Eggs"])
                .replace("", "no")
            )
            worker.insert(1, "Owner", "Sam Crofts")
        else:
            worker = (
                worker.query("Nestbox == Nestbox")
                .query('Species == "g" or Species == "G" or Species == "sp=g"')
                .filter(["Nestbox", "Owner", "Clutch Size", 'State Code'])
                .rename(columns={"Clutch Size": "Eggs", "State Code": "Nest"})
                .replace("", "no")
            )
        which_greati = which_greati.append(worker)
    return which_greati


# Main ------------------------------------

# Text colours
white = Fore.BLACK + Back.WHITE + Style.BRIGHT
blue = Fore.BLUE + Back.WHITE + Style.BRIGHT
red = Fore.RED + Back.WHITE + Style.BRIGHT
green = Fore.WHITE + Back.GREEN + Style.BRIGHT


# Make sure paths exist
for path in [OUT_DIR, FIELD_DIR]:
    safe_makedir(path)


output = render('Fieldwork helper_', colors=[
                f'#{tstyle.mustard}', f'#{tstyle.teal}'],
                align='left', font='tiny',
                space=False, letter_spacing=1,
                line_height=10, max_length=10)
print(tcolor("""
                                      #&#&#&  
                                    @@@@@&&&%     
                                 *@@  ,#@@@@@/%> 
                             ,/(//@@@.     @@&    
                           (##/##(#(%..*@@@@&     
                      (,#,.%#(%((..,,,....&@&     
                   /,%,%/,@&/&%(****,.....&&.     
              _,%&&&&%((//////*****,,.....@.      
     _-_,((##, .*,*,***/****,******,....&&        
                      *(*****,,**,../&           
                            /*(%/                     
                             #  #                   
                           *-$%~-%=-           """, tstyle.teal))
print(output.replace('\x01', '').replace(' \x1b', '\x1b'))
print(tstyle.BOLD + tcolor(f' version {version}\n', tstyle.teal))

while True:

    # Get coordinates for all nestboxes
    nestbox_coords = pd.read_csv(coords_csv).query('`box type` == "GT"')
    nestbox_coords["Nestbox"] = nestbox_coords["nestbox"].str.upper()

    # First menu
    questions = [
        {
            'type': 'list',
            'message': ' Options',
            'name': 'option',
            'choices': [
                {'name': 'Enter deployment data'},
                {'name': 'Get a progress report'},
                {'name': 'Exit the app'},
            ],
            'validate': lambda answer: 'You must choose one option.'
            if len(answer) == 0 else True
        }
    ]

    answer = prompt(questions, style=menu_aes)
    print('')

    if answer['option'] == 'Exit the app':
        break

    elif answer['option'] == 'Enter deployment data':  # Enter new nestboxes and recorders
        # * Enter recorder data while loop
        while True:

            # * Enter nestboxes while loop
            while True:

                print(dedent("""
                Please enter all nestbox names separated by a single space:
                e.g. SW84A EX20 C47
                """
                             ))

                names = input().upper().strip().split(" ")

                if len(names) == sum(nestbox_coords["Nestbox"].isin(names)):
                    print("All nestbox names exist")
                    break
                else:
                    nwrong = str(len(names) -
                                 sum(nestbox_coords["Nestbox"].isin(names)))
                    print(
                        red +
                        f'{nwrong} out of {str(len(names))} entered nestbox names do not exist'
                    )
                    print("\nTry again, you absolute dumbass:")
                    continue

            # * Enter recorders while loop
            while True:

                print(dedent("""
                Now enter the recorder numbers, also separated by spaces:
                e.g. 01 23 15
                """
                             ))

                recorders = input().upper().strip().split(" ")
                recorders = pd.to_numeric(recorders)

                if len(names) != len(recorders):
                    print(
                        red + "The number of recorders does not match the number of nestboxes"
                    )
                    continue
                elif any(len(str(i)) != 2 for i in recorders):
                    print(
                        red + "Recorder numbers can only have two digits"
                    )
                    continue
                else:
                    break

            user_entered = dict(zip(names, recorders))

            question = (dedent(
                f"""You have entered: {str(user_entered)}\nIs this correct?"""
            ))
            if yes_or_no(question):
                break
            else:
                continue

        # * End of recorder data enter loop

        # * Enter date block
        if not yes_or_no(
            f"Is {str(date.today())} the date when you deployed these recorders?"
        ):
            print("Enter the correct date in the same format")
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

        print(
            green + "Done. You can check all added nestboxes at " +
            str(recorded_csv)
        )

        continue

    elif answer['option'] == 'Get a progress report':  # get nestboxes to be visited

        # Get updated list of nestboxes from google sheets
        which_greati = get_nestbox_update()

        # Add coordinates & date added.
        # (save pickle for the record)
        picklename = OUT_DIR / (
            str(
                f"allrounds_{str(pd.Timestamp('today', tz='UTC').strftime('%Y%m%d'))}.pkl"
            )
        )

        if len(which_greati) == 0:
            raise Error("There are no GRETI nestboxes yet")
        else:
            which_greati = pd.merge(
                which_greati, nestbox_coords, on=["Nestbox"])
            which_greati["Added"] = str(
                pd.Timestamp("today", tz="UTC").strftime("%Y-%m-%d")
            )
            len1 = len(which_greati)

            # Remove Blue tit nestboxes from list
            which_greati = which_greati[which_greati['Nestbox'].isin(
                nestbox_coords["Nestbox"].to_list())]

            len2 = len(which_greati)
            if len1 != len2:
                print(
                    f'Removed {len1 - len2} nestboxes that were of Blue tit type')

            which_greati.to_pickle(str(picklename))

        # Check which nestboxes have already been recorded

        if not Path(recorded_csv).exists():
            print('.csv file with recorded nestboxes does not exist, creating it.')
            recorded_empty = pd.DataFrame(
                columns=['Nestbox', 'AM', 'longitude', 'latitude', 'Deployed', 'Move_by'])
            recorded_empty.to_csv(recorded_csv, index=False)

        try:
            already_recorded = (
                pd.read_csv(recorded_csv)
                .filter(["Nestbox"])
                .query('Nestbox != "Nestbox"')
            )

            diff_df = (
                which_greati.merge(
                    already_recorded, on=["Nestbox"], indicator=True, how="outer"
                )
                .query('_merge != "both"')
                .drop(["_merge"], 1)
                .dropna(thresh=2)
            )

            if {"longitude_x", "latitude_y"}.issubset(diff_df.columns):
                diff_df = diff_df.drop(["longitude_y", "latitude_y"], 1).rename(
                    columns={"longitude_x": "longitude",
                             "latitude_x": "latitude"}
                )

            diff_df = diff_df.sort_values(by="Owner")

        except:
            already_recorded = []
            diff_df = which_greati

        # Print basic info
        print(
            '\n' + info + tstyle.BOLD +
            tcolor(str(len(already_recorded)), tstyle.mustard) + " already recorded\n" +
            info + tstyle.BOLD +
            tcolor(str(len(diff_df)), tstyle.mustard) + " to be recorded\n"
        )
        # Fix and print new great tit data
        table_p = diff_df.drop(["longitude", "latitude", 'x', 'y', 'nestbox',
                                'box type', 'Added'], 1).rename(columns={"section": "Section"})
        print(tabulate(table_p, headers="keys"))

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

        answer = prompt(questions, style=menu_aes)
        print('')

        if answer['option'] == 'Exit the app':
            break

        elif answer['option'] == 'Go back to the main menu':
            continue

        elif answer['option'] == 'Prepare fieldwork plan and maps':
            # Plot with R + ggplot2
            diff_df.to_csv(str(OUT_DIR / "toberecorded.csv"), index=False)
            subprocess.check_call(["Rscript", str(RPLOTS)], shell=False)
            print(green + "Done (1/2). You can check your plots at " + str(OUT_DIR))
            # Export gpx
            while True:

                today = str(date.today())
                tomorrow = str(date.today() + timedelta(days=1))
                print(
                    white
                    + f"Do you want the .gpx file for later today ({today}), tomorrow ({tomorrow}), or none? [today/tomorrow/none]:"
                )
                whichday = input().lower().strip()

                if whichday == "today":
                    move_today = (
                        pd.read_csv(recorded_csv)
                        .query('Nestbox != "Nestbox"')
                        .query("Move_by == @today")
                    )
                    write_gpx(GPX_DIR / str(str(today) + ".gpx"),
                              diff_df, move_today)
                    print(
                        green + "Done (2/2). You can find your .gpx file at " + str(GPX_DIR))
                    break
                elif whichday == "tomorrow":
                    move_tomorrow = (
                        pd.read_csv(recorded_csv)
                        .query('Nestbox != "Nestbox"')
                        .query("Move_by == @tomorrow")
                    )
                    write_gpx(
                        GPX_DIR / str(str(tomorrow) +
                                      ".gpx"), diff_df, move_tomorrow
                    )
                    print(
                        green + "Done (2/2). You can find your .gpx file at " + str(GPX_DIR))
                    break
                elif whichday == "none":
                    break
                else:
                    print(
                        Fore.RED
                        + Style.BRIGHT
                        + "'"
                        + option
                        + "'"
                        + " is not a valid command"
                    )
                    continue
            continue

        else:
            print(
                Fore.RED + Style.BRIGHT + "'" + option + "'" + " is not a valid command"
            )
            continue

# print(Fore.BLACK + Back.WHITE + which_greati.groupby(['Owner']).size().to_markdown())

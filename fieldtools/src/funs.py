
import os
from pprint import pprint
import sys
import pandas as pd
import pygsheets
from fieldtools.src.aesthetics import arrow
from fieldtools.src.paths import OUT_DIR, PROJECT_DIR, safe_makedir
from openpyxl.reader.excel import load_workbook
from pathlib2 import Path, PosixPath
from tqdm.auto import tqdm
import warnings
warnings.simplefilter(action='ignore', category=UserWarning)


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
        "Sam": "1Y8iBGVTm1qw-eIqW2wSn6eG3FK7tVyvN2x2nEiPb-3w",
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
        if name == "Sam":
            worker = gc.open_by_key(googlekey)[0].get_as_df(
                has_header=True, include_tailing_empty=False).loc[:, :'fledge']
            if "" in worker.columns:
                worker = worker.drop([""], axis=1)
            # worker = worker.rename(
            #     columns=worker.iloc[0]).drop(worker.index[0])
            worker = (
                worker.rename(columns={"Num eggs": "Eggs"})
                .rename(columns={"number": "Nestbox", "State code": "Nest"})
                .query("Nestbox == Nestbox")
                .query('Species == "g" or Species == "G" or Species == "sp=g"')
                .filter(["Nestbox", "Eggs"])
                .replace(0, "no")
            )
            worker.insert(1, "Owner", "Sam")
        else:
            worker = gc.open_by_key(googlekey)[0].get_as_df(
                has_header=False, include_tailing_empty=False)
            worker = worker.rename(
                columns=worker.iloc[0]).drop(worker.index[0])
            if "" in worker.columns:
                worker = worker.drop([""], axis=1)
            worker = (
                worker.query("Nestbox == Nestbox")
                .query('Species == "g" or Species == "G" or Species == "sp=g"')
                .filter(["Nestbox", "Owner", "Clutch Size", 'State Code'])
                .rename(columns={"Clutch Size": "Eggs", "State Code": "Nest"})
                .replace("", "no")
            )
        which_greati = which_greati.append(worker)
    return which_greati


def get_recorded_gretis(recorded_csv, nestbox_coords, which_greati):
    picklename = OUT_DIR / (
        str(
            f"allrounds_{str(pd.Timestamp('today', tz='UTC').strftime('%Y%m%d'))}.pkl"
        )
    )
    if len(which_greati) == 0:
        print("There are no GRETI nestboxes yet")
        return [], []
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
        diff_df = diff_df.sort_values(
            ['Eggs', 'Nest'], ascending=[False, False])
    except:
        already_recorded = []
        diff_df = which_greati

    return already_recorded, diff_df


def split_path(path):
    folders = []
    drive, path = os.path.splitdrive(path)
    while True:
        path, folder = os.path.split(path)

        if folder:
            folders.append(folder)
        else:
            if path:
                folders.append(path)
            break

    if drive:
        folders.append(drive)
    return folders[::-1]


def reconstruct_path(folders):
    folders = folders[:]
    path = ""

    # On windows, pop off the drive if there is one. Affects handling of relative vs rooted paths
    if sys.platform == 'win32' and ':' == folders[0][-1]:
        path = folders[0]
        del folders[0]
    if folders and folders[0] == os.sep:
        path += folders[0]
        del folders[0]
    path += os.sep.join(folders)
    return path

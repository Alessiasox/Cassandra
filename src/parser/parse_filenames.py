# parse_filenames.py

import os
import re
from datetime import datetime
from typing import Optional, Dict

def parse_filename(filename: str) -> Optional[Dict]:
    """
    Parses filenames like:
      ExperimentalG4_HiRest_180420UTC150040.jpg
      ExperimentalG4_LoRest_180420UTC0100.jpg

    Returns a dict:
      {
        "station": "ExperimentalG4",
        "resolution": "HiRes",      # or "LoRes"
        "timestamp": datetime(...),
        "original_filename": "..."
      }
    or None if it doesn’t match.
    """
    base = os.path.basename(filename)
    # 1) station = alphanumeric (e.g. ExperimentalG4)
    # 2) resolution = LoRes or HiRes
    # 3) literal 't'
    # 4) underscore + dt_str (6-digit date + 'UTC' + 4–6 digit time)
    pat = r'^([A-Za-z0-9]+)_(LoRes|HiRes)t_(\d{6}UTC\d{4,6})\.jpg$'
    m = re.match(pat, base)
    if not m:
        return None

    station = m.group(1)             # e.g. ExperimentalG4
    resolution = m.group(2)          # "LoRes" or "HiRes"
    dt_str = m.group(3)              # e.g. "180420UTC150040" or "180420UTC0100"

    # Split into date & time
    date_part, time_part = dt_str.split('UTC')
    # date_part: 6 digits = ddmmyy
    dd = int(date_part[0:2])
    mm = int(date_part[2:4])
    yy = int(date_part[4:6])
    year = 2000 + yy                 # Assuming all dates are in 21st century

    # time_part: either HHMM (4 digits) or HHMMSS (6 digits)
    if len(time_part) == 4:
        hh = int(time_part[0:2])
        mi = int(time_part[2:4])
        ss = 0
    elif len(time_part) == 6:
        hh = int(time_part[0:2])
        mi = int(time_part[2:4])
        ss = int(time_part[4:6])
    else:
        # unrecognised time format
        return None

    try:
        ts = datetime(year, mm, dd, hh, mi, ss)
    except ValueError:
        return None

    return {
        "station": station,
        "resolution": resolution,
        "timestamp": ts,
        "original_filename": base
    }
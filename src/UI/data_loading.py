import os
from datetime import datetime
from typing import Dict, List

from parser.index_local import index_local_images

def load_images(src: str, stn: str):
    lo = index_local_images(os.path.join(src, "LoRes"))
    hi = index_local_images(os.path.join(src, "HiRes"))
    return [x for x in lo if stn in x["station"]], [x for x in hi if stn in x["station"]]

def load_wavs(src: str, stn: str) -> List[Dict]:
    wav_dir = os.path.join(src, "Wav")
    out = []
    if os.path.isdir(wav_dir):
        for fn in os.listdir(wav_dir):
            if fn.endswith(".wav") and stn in fn:
                full = os.path.join(wav_dir, fn)
                out.append({
                    "path": full,
                    "timestamp": datetime.fromtimestamp(os.path.getmtime(full)),
                    "filename": fn
                })
    return out
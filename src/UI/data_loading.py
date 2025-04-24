import os
import yaml
from datetime import datetime, timezone 
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
import streamlit as st

from parser.index_local import index_local_images
from ssh.fetcher_remote import RemoteVLFClient

# Load remote‐station configs from your top‐level ssh/stations.yml
load_dotenv()
_CFG_PATH = Path(__file__).parents[2] / "src" / "ssh" / "stations.yml"
with open(_CFG_PATH) as f:
    _REMOTE_STATIONS: Dict[str,Dict] = yaml.safe_load(f)

def load_data(
    station: str,
    src_folder: str
) -> (List[Dict], List[Dict], List[Dict], bool, Optional[RemoteVLFClient]):
    """
    Returns (lores, hires, wavs, is_remote, client).
    If `station` appears in stations.yml, we SSH; else local disk.
    """

    # ─── Remote path? ────────────────────────────────────────────
    if station in _REMOTE_STATIONS:
        cfg = _REMOTE_STATIONS[station]

        # Gather exactly the args RemoteVLFClient expects:
        host       = cfg["host"]
        port       = cfg["port"]
        user       = cfg["username"]
        # key comes from your .env:
        key_path = os.path.expanduser(os.getenv("SSH_KEY_PATH", "~/.ssh/id_ed25519")) 
        if not key_path:
            raise RuntimeError("SSH_KEY_PATH not set in environment")
        remote_base = cfg["remote_base"]

        client = RemoteVLFClient(
            host=host,
            port=port,
            username=user,
            key_path=key_path,
            remote_base=remote_base
        )

        lores = client.list_images("LoRes")
        hires = client.list_images("HiRes")
        wavs  = client.list_wavs()

        st.sidebar.caption(
            f"Data range: {lores[0]['timestamp']:%Y-%m-%d} → "
            f"{lores[-1]['timestamp']:%Y-%m-%d}"
        )

        return lores, hires, wavs, True, client
    

    # ─── Local fallback ───────────────────────────────────────────
    lo_dir = os.path.join(src_folder, "LoRes")
    hi_dir = os.path.join(src_folder, "HiRes")

    lo = index_local_images(lo_dir) if os.path.isdir(lo_dir) else []
    hi = index_local_images(hi_dir) if os.path.isdir(hi_dir) else []
    lores = [img for img in lo if station in img["station"]]
    hires = [img for img in hi if station in img["station"]]


    # local WAVs
    wavs = []
    wav_dir = os.path.join(src_folder, "Wav")
    if os.path.isdir(wav_dir):
        for fn in os.listdir(wav_dir):
            if fn.lower().endswith(".wav") and station in fn:
                p = os.path.join(wav_dir, fn)
                wavs.append({
                    "path":      p,
                    "timestamp": datetime.fromtimestamp(os.path.getmtime(p), tz=timezone.utc),
                    "filename":  fn
                })

    return lores, hires, wavs, False, None
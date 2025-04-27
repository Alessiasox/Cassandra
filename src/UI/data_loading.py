# src/ui/data_loading.py

import os
import yaml
import streamlit as st
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv

# local‐only image indexer
from parser.index_local import index_local_images
# your SSH‐based fallback client
from ssh.fetcher_remote   import RemoteVLFClient

# for Postgres listing
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

# load your station→SSH config
_CFG_PATH = Path(__file__).parents[2] / "src" / "ssh" / "stations.yml"
with open(_CFG_PATH, "r") as f:
    _REMOTE_STATIONS: Dict[str, Dict] = yaml.safe_load(f)


def _list_frames_from_db(
    station: str,
    resolution: str,
) -> List[Dict]:
    """
    Query Postgres 'frames' table for all rows matching station + resolution,
    returning list of dicts: {station, resolution, timestamp, key}.
    Assumes your frames table has columns:
      - station TEXT
      - resolution TEXT
      - timestamp TIMESTAMP WITH TIME ZONE
      - key TEXT      ← S3 key or remote path
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")

    # connect & fetch
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT station,
                       resolution,
                       timestamp,
                       key AS remote_path
                FROM frames
                WHERE station = %s
                  AND resolution = %s
                ORDER BY timestamp ASC
                """,
                (station, resolution),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    # convert psycopg rows into the dicts UI expects
    out = []
    for r in rows:
        out.append({
            "station":       r["station"],
            "resolution":    r["resolution"],
            "timestamp":     r["timestamp"],        # should already be tz-aware
            "remote_path":   r["remote_path"],      # key (e.g. s3://… or SFTP path)
            # if you need full_path for local case, DB only supports remote listing
        })
    return out


def load_data(
    station: str,
    src_folder: str,
) -> (List[Dict], List[Dict], List[Dict], bool, Optional[RemoteVLFClient]):
    """
    Returns (lores, hires, wavs, is_remote, client_or_none).

    1) If DATABASE_URL is set, we pull *all* LoRes/HiRes/Wav rows from Postgres.
    2) Else if station∈_REMOTE_STATIONS, we SSH-list via RemoteVLFClient.
    3) Otherwise we index local disk.
    """

    # ─── 1) Try Postgres first ────────────────────────────────────────
    if os.getenv("DATABASE_URL"):
        try:
            lores = _list_frames_from_db(station, "LoRes")
            hires = _list_frames_from_db(station, "HiRes")
            wavs  = _list_frames_from_db(station, "Wav")
            st.sidebar.caption(
                f"Data (via Postgres): {lores[0]['timestamp']:%Y-%m-%d} → "
                f"{lores[-1]['timestamp']:%Y-%m-%d}"
            )
            return lores, hires, wavs, True, None
        except Exception as e:
            st.warning(f"Postgres listing failed, falling back to SSH/local: {e}")

    # ─── 2) SSH remote listing ─────────────────────────────────────────
    if station in _REMOTE_STATIONS:
        cfg = _REMOTE_STATIONS[station]
        key_path = os.path.expanduser(os.getenv("SSH_KEY_PATH", "~/.ssh/id_ed25519"))
        if not key_path:
            raise RuntimeError("SSH_KEY_PATH not set")

        client = RemoteVLFClient(
            host        = cfg["host"],
            port        = cfg["port"],
            username    = cfg["username"],
            key_path    = key_path,
            remote_base = cfg["remote_base"],
        )

        lores = client.list_images("LoRes")
        hires = client.list_images("HiRes")
        wavs  = client.list_wavs()

        st.sidebar.caption(
            f"Data (via SSH): {lores[0]['timestamp']:%Y-%m-%d} → "
            f"{lores[-1]['timestamp']:%Y-%m-%d}"
        )
        return lores, hires, wavs, True, client

    # ─── 3) Local disk fallback ────────────────────────────────────────
    lo_dir = os.path.join(src_folder, "LoRes")
    hi_dir = os.path.join(src_folder, "HiRes")
    lo    = index_local_images(lo_dir) if os.path.isdir(lo_dir) else []
    hi    = index_local_images(hi_dir) if os.path.isdir(hi_dir) else []
    lores = [img for img in lo if station in img["station"]]
    hires = [img for img in hi if station in img["station"]]

    # local WAVs
    wavs = []
    wav_dir = os.path.join(src_folder, "Wav")
    if os.path.isdir(wav_dir):
        for fn in os.listdir(wav_dir):
            if fn.lower().endswith(".wav") and station in fn:
                full = os.path.join(wav_dir, fn)
                wavs.append({
                    "path":      full,
                    "timestamp": datetime.fromtimestamp(
                                      os.path.getmtime(full),
                                      tz=timezone.utc
                                  ),
                    "filename":  fn,
                })

    return lores, hires, wavs, False, None
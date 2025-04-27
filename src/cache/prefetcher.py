# ─── NEW  file:  src/cache/prefetcher.py ──────────────────────────────
from __future__ import annotations
import os, io, concurrent.futures
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st
from PIL import Image

from ssh.fetcher_remote import RemoteVLFClient

CACHE_DIR = Path.home() / ".vlf_cache"
THUMB_SIZE = 32_000                       # first 32 kB per JPEG

def _month_key(ts: datetime) -> str:
    return ts.strftime("%Y-%m")

# ---------- internal helpers -----------------------------------------
def _meta_path(stn: str, month: str):
    p = CACHE_DIR / stn / month
    p.mkdir(parents=True, exist_ok=True)
    return p / f"meta_{month}.parquet"

def _thumb_path(stn: str, month: str, fname: str):
    p = CACHE_DIR / stn / month / "thumbs"
    p.mkdir(parents=True, exist_ok=True)
    return p / fname

def _save_thumb(stn, month, fname, raw):
    _thumb_path(stn, month, fname).write_bytes(raw[:THUMB_SIZE])

# ---------- public API ------------------------------------------------
@st.cache_data(ttl=3600)
def month_listing(_stn: str, _month: str, _cfg: Dict) -> pd.DataFrame:
    """Return LoRes+HiRes listing for one month (cached 1 h)."""
    meta_file = _meta_path(_stn, _month)
    if meta_file.exists():
        return pd.read_parquet(meta_file)

    cli = RemoteVLFClient(
        host=_cfg["host"],
        port=_cfg["port"],
        username=_cfg["username"],
        key_path=os.getenv("SSH_KEY_PATH", "~/.ssh/id_ed25519"),
        remote_base=_cfg["remote_base"],
    )

    # 1 Fetch listings once
    df = pd.DataFrame(cli.list_images("LoRes") + cli.list_images("HiRes"))
    df = df[df["timestamp"].dt.strftime("%Y-%m") == _month]      # keep month
    df.to_parquet(meta_file, index=False)

    # 2 Download thumbnails concurrently (only if missing)
    to_dl = [
        row for _, row in df.iterrows()
        if not _thumb_path(_stn, _month, row.original_filename).exists()
    ]
    def _grab(row):
        raw = cli.fetch_image_bytes(row.remote_path)
        _save_thumb(_stn, _month, row.original_filename, raw)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        ex.map(_grab, to_dl)

    cli.close()
    return df

def load_thumb(stn: str, ts: datetime, fname: str) -> bytes | None:
    month = _month_key(ts)
    p = _thumb_path(stn, month, fname)
    return p.read_bytes() if p.exists() else None
# src/ui/main.py

import os
from datetime import datetime, timedelta
from typing import List, Dict

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy.io import wavfile
from PIL import Image

from parser.index_local import index_local_images
from ui.controls import (
    select_station_folder_mode,
    select_date_time,
    render_download_buttons,
)
from ui.data_loading import load_images, load_wavs
from ui.viewer_utils import generate_timeline, closest_match
from ui.tabs.spectrograms import render_spectrograms_tab
from ui.tabs.waveform import render_waveform_tab
from ui.tabs.logs import render_logs_tab

# ─────────── Page config ───────────
st.set_page_config(
    page_title="INGV Cassandra Project",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────── Title & Caption ───────────
st.title("🛰️  INGV Cassandra Project")
st.caption(
    """
**Cassandra** is an internal visualization and analysis toolkit developed for the
INGV Experimental VLF Network.

It allows you to:
- Browse spectrograms from multiple stations (LoRes: hourly, HiRes: ~40s)
- Explore and play raw waveform `.wav` audio files
- Run (or simulate) AI-based signal classification
- Download any combination of files for offline use

Use the control panel on the left to configure your source folders, time ranges, and station of interest.
"""
)

def main():
    # ───────── Sidebar • Station/Folder/Mode ─────────
    station, src_folder, mode = select_station_folder_mode()

    # ───────── Sidebar • Download Buttons ─────────
    render_download_buttons()

    # ───────── Load & index data ─────────
    lores, hires = load_images(src_folder, station)
    wavs         = load_wavs(src_folder, station)
    all_ts       = [item["timestamp"] for item in lores + hires + wavs]
    if not all_ts:
        st.error("No data found for this station/folder.")
        return

    # ───────── Sidebar • Date & Time Pickers ─────────
    sel_date, start_t, end_t = select_date_time(all_ts)

    # ───────── Session‑state Defaults ─────────
    ss = st.session_state
    dt0 = datetime.combine(sel_date, start_t)
    dt1 = datetime.combine(sel_date, end_t)
    ss.setdefault("range_slider", (dt0, dt0 + timedelta(hours=1)))
    ss.setdefault("lores_hour",   dt0.replace(minute=0, second=0, microsecond=0))
    ss.setdefault("logs",         [])

    # ───────── Build Timeline ─────────
    timeline = generate_timeline(dt0, dt1, 5)
    if not timeline:
        st.error("Start Time must be before End Time.")
        return

    # ───────── Active Window ─────────
    if mode == "Use slider":
        rng_start, rng_end = st.slider(
            "Time window",
            min_value=timeline[0],
            max_value=timeline[-1],
            value=ss["range_slider"],
            step=timedelta(minutes=5),
            format="YYYY-MM-DD HH:mm",
            key="range_slider",
        )
        # keep the hourly picker in sync
        ss["lores_hour"] = rng_start.replace(minute=0, second=0, microsecond=0)
    else:
        # hour‑picker mode
        lo_hours = sorted({
            lo["timestamp"].replace(minute=0, second=0, microsecond=0)
            for lo in lores if lo["timestamp"].date() == sel_date
        })
        if ss["lores_hour"] not in lo_hours:
            ss["lores_hour"] = lo_hours[0]

        col_l, col_m, col_r = st.columns([1,6,1], gap="small")
        with col_l:
            st.button(
                "◀ 1 h earlier",
                disabled=ss["lores_hour"]==lo_hours[0],
                on_click=lambda: ss.update(
                    lores_hour=lo_hours[lo_hours.index(ss["lores_hour"]) - 1]
                ),
                use_container_width=True
            )
        with col_m:
            ss["lores_hour"] = st.selectbox(
                "LoRes hour",
                lo_hours,
                index=lo_hours.index(ss["lores_hour"]),
                format_func=lambda dt: dt.strftime("%H:%M"),
                label_visibility="collapsed",
                key="lores_picker"
            )
        with col_r:
            st.button(
                "1 h later ▶",
                disabled=ss["lores_hour"]==lo_hours[-1],
                on_click=lambda: ss.update(
                    lores_hour=lo_hours[lo_hours.index(ss["lores_hour"]) + 1]
                ),
                use_container_width=True
            )

        rng_start = ss["lores_hour"]
        rng_end   = rng_start + timedelta(hours=1)

    # mirror window in sidebar
    st.sidebar.markdown(
        f"**Window:** {rng_start.strftime('%H:%M')} → {rng_end.strftime('%H:%M')}"
    )

    # ───────── Tabs ─────────
    tab_spec, tab_wav, tab_logs = st.tabs(
        ["📊 Spectrograms", "🔊 Waveform + AI", "📜 Logs"]
    )

    with tab_spec:
        render_spectrograms_tab(
            lores=lores,
            hires=hires,
            sel_date=sel_date,
            mode=mode,
            rng_start=rng_start,
            rng_end=rng_end,
            ss=ss
        )

    with tab_wav:
        render_waveform_tab(
            wavs=wavs,
            rng_start=rng_start,
            rng_end=rng_end,
            ss=ss
        )

    with tab_logs:
        render_logs_tab(ss=ss)

if __name__ == "__main__":
    main()
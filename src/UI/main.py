
import os
import streamlit as st

# ─────────── Page config & Header ───────────
st.set_page_config(
    page_title="INGV Cassandra Project",
    layout="wide",
    initial_sidebar_state="expanded"
)


from datetime import datetime, timedelta

from ui.controls      import (
    select_station_folder_mode,
    select_date_time,
    render_download_buttons
)
from ui.data_loading import (
    load_data,
)
from ui.viewer_utils import generate_timeline, closest_match
from ui.tabs.spectrograms import render_spectrograms_tab
from ui.tabs.waveform     import render_waveform_tab
from ui.tabs.logs         import render_logs_tab

 
# ─────────── Title & Caption ───────────
st.title("🛰️ INGV Cassandra Project")
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
    # 1) Controls
    station, src_folder, mode = select_station_folder_mode()
    render_download_buttons()

    # 2) Load data (local or SSH)
    lores, hires, wavs, is_remote, client = load_data(station, src_folder)

    # 3) Collect all timestamps
    all_ts = [item["timestamp"] for item in lores + hires + wavs]
    if not all_ts:
        st.error("No data found for this station/folder."); return

    # 4) Date/time pickers
    sel_date, start_t, end_t = select_date_time(all_ts)

    # 5) Session defaults & timeline
    ss  = st.session_state
    dt0 = datetime.combine(sel_date, start_t)
    dt1 = datetime.combine(sel_date, end_t)
    ss.setdefault("range_slider", (dt0, dt0 + timedelta(hours=1)))
    ss.setdefault("lores_hour",   dt0.replace(minute=0, second=0, microsecond=0))
    ss.setdefault("logs",         [])

    timeline = generate_timeline(dt0, dt1, 5)
    if not timeline:
        st.error("Start Time must be before End Time."); return

    # 6) Active window
    if mode == "Use slider":
        rng_start, rng_end = st.slider(
            "Time window",
            min_value=timeline[0],
            max_value=timeline[-1],
            value=ss["range_slider"],
            step=timedelta(minutes=5),
            format="YYYY-MM-DD HH:mm",
            key="range_slider"
        )
        ss["lores_hour"] = rng_start.replace(minute=0, second=0, microsecond=0)
    else:
        lo_hours = sorted({
            lo["timestamp"].replace(minute=0, second=0, microsecond=0)
            for lo in lores if lo["timestamp"].date() == sel_date
        })
        if ss["lores_hour"] not in lo_hours:
            ss["lores_hour"] = lo_hours[0]

        c1, c2, c3 = st.columns([1,6,1], gap="small")
        with c1:
            st.button(
                "◀ 1 h earlier",
                disabled=ss["lores_hour"]==lo_hours[0],
                on_click=lambda: ss.update(
                    lores_hour=lo_hours[lo_hours.index(ss["lores_hour"])-1]
                ),
                use_container_width=True
            )
        with c2:
            ss["lores_hour"] = st.selectbox(
                "LoRes hour",
                lo_hours,
                index=lo_hours.index(ss["lores_hour"]),
                format_func=lambda dt: dt.strftime("%H:%M"),
                label_visibility="collapsed",
                key="lores_picker"
            )
        with c3:
            st.button(
                "1 h later ▶",
                disabled=ss["lores_hour"]==lo_hours[-1],
                on_click=lambda: ss.update(
                    lores_hour=lo_hours[lo_hours.index(ss["lores_hour"])+1]
                ),
                use_container_width=True
            )

        rng_start = ss["lores_hour"]
        rng_end   = rng_start + timedelta(hours=1)

    st.sidebar.markdown(f"**Window:** {rng_start.strftime('%H:%M')} → {rng_end.strftime('%H:%M')}")

    # 7) Tabs
    tab_spec, tab_wav, tab_logs = st.tabs(
        ["📊 Spectrograms", "🔊 Waveform + AI", "📜 Logs"]
    )

    with tab_spec:
        render_spectrograms_tab(
            low_res_images  = lores,
            high_res_images = hires,
            control_mode    = mode,
            window_start    = rng_start,
            window_end      = rng_end,
            session_state   = ss,
            is_remote       = is_remote,
            client          = client,
        )

    with tab_wav:
        render_waveform_tab(
            wavs=wavs,
            rng_start=rng_start,
            rng_end=rng_end,
            ss=ss,
            is_remote=is_remote,
            client=client
        )

    with tab_logs:
        render_logs_tab(ss=ss)

if __name__ == "__main__":
    main()
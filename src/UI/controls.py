# src/ui/controls.py

import streamlit as st

def select_station_folder_mode():
    """
    Sidebar section: pick station, source folder, and control mode.
    """
    st.sidebar.header("Control Panel")

    station = st.sidebar.selectbox(
        "Station",
        [
            "ExperimentalG4",
            "Duronia",
            "ForcaCanapine",
            "Grottaminarda",
        ],
        index=0,  # default to ExperimentalG4
    )

    src_folder = st.sidebar.text_input(
        "Source Folder",
        value="VLF/"  # you can change per‐station defaults later if you like
    )

    mode = st.sidebar.radio(
        "Control mode",
        ["Use slider", "Use hour picker"],
        horizontal=True
    )

    return station, src_folder, mode


def select_date_time(all_ts):
    """
    Sidebar section: pick date, start and end times.
    """
    dates = sorted({ts.date() for ts in all_ts})
    sel_date = st.sidebar.date_input(
        "Date",
        value=dates[0],
        min_value=dates[0],
        max_value=dates[-1]
    )

    times = sorted({ts.time() for ts in all_ts if ts.date() == sel_date})
    start_t = st.sidebar.time_input(
        "Start Time",
        value=times[0]
    )
    end_t = st.sidebar.time_input(
        "End Time",
        value=times[-1]
    )

    return sel_date, start_t, end_t


def render_download_buttons():
    """
    Sidebar section: download buttons for specs and WAVs.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📥 Download Options")

    st.sidebar.button("📦 Download All Files", use_container_width=True)
    st.sidebar.button("🎧 Download All WAV Files", use_container_width=True)
    st.sidebar.button("🗜️ Download LoRes WAV", use_container_width=True)
    st.sidebar.button("🗜️ Download HiRes WAV", use_container_width=True)
    st.sidebar.button("🖼️ Download LoRes Spec", use_container_width=True)
    st.sidebar.button("🖼️ Download HiRes Spec", use_container_width=True)
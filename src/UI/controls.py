import streamlit as st
from typing import List
from datetime import datetime, date, timedelta


_STATION_DEFAULTS = {
    "ExperimentalG4": "VLF/",
    "Duronia":        "C:/htdocs/VLF",
    "ForcaCanapine":  "C:/htdocs/VLF",
    "Grottaminarda":  "C:/htdocs/VLF",
}

def select_station_folder_mode():
    """
    Sidebar: pick station, source folder, and control mode.
    Avoid clobbering session_state.src_folder directly.
    """
    st.sidebar.header("Control Panel")

    # 1) Station selector
    station = st.sidebar.selectbox(
        "Station",
        list(_STATION_DEFAULTS.keys()),
        index=0,
        key="station"
    )

    # 2) Compute the initial default for src_folder:
    prev = st.session_state.get("prev_station")
    if prev != station:
        # first time selecting this station: use its default
        default_folder = _STATION_DEFAULTS[station]
    else:
        # preserve whatever the user typed last
        default_folder = st.session_state.get(
            "src_folder",
            _STATION_DEFAULTS[station]
        )

    # 3) text_input takes ownership of session_state["src_folder"]
    src_folder = st.sidebar.text_input(
        "Source Folder",
        value=default_folder,
        key="src_folder"
    )
    st.session_state.prev_station = station

    # 4) Control mode
    mode = st.sidebar.radio(
        "Control mode",
        ["Use slider", "Use hour picker"],
        horizontal=True,
        key="mode"
    )

    return station, src_folder, mode


def select_date_time(all_ts):
    """
    Calendar date-picker that *looks* free-form but snaps to the
    closest available day if the user picks an empty one.
    """
    # all unique UTC dates that really exist
    valid_days = sorted({ts.date() for ts in all_ts})

    min_day, max_day = valid_days[0], valid_days[-1]

    # ── calendar widget
    picked = st.sidebar.date_input(
        "Date",
        value=max_day,             # pre-select the latest
        min_value=min_day,
        max_value=max_day
    )

    # ── snap to nearest valid day if necessary
    if picked not in valid_days:
        # find the closest existing day
        # (simple linear search – list is small)
        nearest = min(valid_days, key=lambda d: abs(d - picked))
        st.sidebar.warning(
            f"No data for {picked:%Y-%m-%d}. "
            f"Jumped to closest available day ({nearest:%Y-%m-%d}).",
            icon="⚠️",
        )
        picked = nearest

    # ── build the list of valid times *for that day* --------------
    times_for_day = sorted({ts.time() for ts in all_ts if ts.date() == picked})

    start_t = st.sidebar.time_input("Start Time", value=times_for_day[0])
    end_t   = st.sidebar.time_input("End Time",   value=times_for_day[-1])

    # guarantee chronological order
    if start_t >= end_t:
        end_t = (datetime.combine(date.min, start_t) + timedelta(minutes=5)).time()

    return picked, start_t, end_t



def render_download_buttons():
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📥 Download Options")
    st.sidebar.button("📦 Download All Files",     use_container_width=True)
    st.sidebar.button("🎧 Download All WAV Files", use_container_width=True)
    st.sidebar.button("🗜️ Download LoRes WAV",     use_container_width=True)
    st.sidebar.button("🗜️ Download HiRes WAV",     use_container_width=True)
    st.sidebar.button("🖼️ Download LoRes Spec",    use_container_width=True)
    st.sidebar.button("🖼️ Download HiRes Spec",    use_container_width=True)
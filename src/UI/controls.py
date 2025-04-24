import streamlit as st
from typing import List
from datetime import datetime, date, time


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


def select_date_time(all_timestamps: List[datetime]) -> tuple[date, time, time]:
    if not all_timestamps:
        st.sidebar.error("No timestamps!")
        return date.today(), time(0, 0), time(23, 59)

    # 1) date dropdown limited to available days
    available_dates = sorted({ts.date() for ts in all_timestamps})
    sel_date = st.sidebar.selectbox("Date", available_dates, index=len(available_dates) - 1)

    # 2) only times from that day
    day_times = sorted({ts.time() for ts in all_timestamps if ts.date() == sel_date})
    if not day_times:                               # shouldn’t happen now
        st.sidebar.warning("No data for that day")
        return sel_date, time(0, 0), time(0, 0)

    # use <selectbox> instead of <time_input> so users can’t pick missing times
    start_t = st.sidebar.selectbox("Start time", day_times, index=0,
                                   format_func=lambda t: t.strftime("%H:%M"))
    end_t   = st.sidebar.selectbox("End time",   day_times, index=len(day_times) - 1,
                                   format_func=lambda t: t.strftime("%H:%M"))

    # keep start ≤ end
    if start_t > end_t:
        start_t, end_t = end_t, start_t

    return sel_date, start_t, end_t



def render_download_buttons():
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📥 Download Options")
    st.sidebar.button("📦 Download All Files",     use_container_width=True)
    st.sidebar.button("🎧 Download All WAV Files", use_container_width=True)
    st.sidebar.button("🗜️ Download LoRes WAV",     use_container_width=True)
    st.sidebar.button("🗜️ Download HiRes WAV",     use_container_width=True)
    st.sidebar.button("🖼️ Download LoRes Spec",    use_container_width=True)
    st.sidebar.button("🖼️ Download HiRes Spec",    use_container_width=True)
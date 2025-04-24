import streamlit as st

_STATION_DEFAULTS = {
    "ExperimentalG4": "VLF/",
    "Duronia":        "VLF/Duronia/",
    "ForcaCanapine":  "VLF/ForcaCanapine/",
    "Grottaminarda":  "VLF/Grottaminarda/",
}

import streamlit as st

_STATION_DEFAULTS = {
    "ExperimentalG4": "VLF/",
    "Duronia":        "VLF/Duronia/",
    "ForcaCanapine":  "VLF/ForcaCanapine/",
    "Grottaminarda":  "VLF/Grottaminarda/",
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
    dates = sorted({ts.date() for ts in all_ts})
    sel_date = st.sidebar.date_input(
        "Date",
        value=dates[0],
        min_value=dates[0],
        max_value=dates[-1],
        key="sel_date"
    )

    times = sorted({ts.time() for ts in all_ts if ts.date() == sel_date})
    start_t = st.sidebar.time_input(
        "Start Time",
        value=times[0],
        key="start_t"
    )
    end_t = st.sidebar.time_input(
        "End Time",
        value=times[-1],
        key="end_t"
    )

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
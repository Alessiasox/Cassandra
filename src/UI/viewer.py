import os
from datetime import datetime, timedelta
from parser.index_local import index_local_images
from typing import Dict, List

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from scipy.io import wavfile

from UI.viewer_utils import closest_match, generate_timeline

# ───────── Page config ─────────
st.set_page_config(page_title="INGV Cassandra Project", layout="wide")
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

# ───────── Sidebar ─────────
st.sidebar.header("Control Panel")
station = st.sidebar.selectbox("Station", ["ExperimentalG4"])
src_folder = st.sidebar.text_input("Source Folder", "VLF/")
mode = st.sidebar.radio(
    "Control mode", ["Use slider", "Use hour picker"], horizontal=True
)


# ───────── Data loading (cached) ─────────
@st.cache_data(show_spinner=False)
def load_images(src, stn):
    lo = index_local_images(os.path.join(src, "LoRes"))
    hi = index_local_images(os.path.join(src, "HiRes"))
    return [x for x in lo if stn in x["station"]], [
        y for y in hi if stn in y["station"]
    ]


@st.cache_data(show_spinner=False)
def load_wavs(src, stn):
    wav_dir = os.path.join(src, "Wav")
    out: List[Dict] = []
    if os.path.isdir(wav_dir):
        for fn in os.listdir(wav_dir):
            if fn.endswith(".wav") and stn in fn:
                full = os.path.join(wav_dir, fn)
                out.append(
                    {
                        "path": full,
                        "timestamp": datetime.fromtimestamp(os.path.getmtime(full)),
                        "filename": fn,
                    }
                )
    return out


lores, hires = load_images(src_folder, station)
wavs = load_wavs(src_folder, station)
all_ts = [z["timestamp"] for z in lores + hires + wavs]
if not all_ts:
    st.error("No data found.")
    st.stop()

# ───────── Date/time pickers ─────────
dates = sorted({ts.date() for ts in all_ts})
sel_date = st.sidebar.date_input(
    "Date", value=dates[0], min_value=dates[0], max_value=dates[-1]
)
day_times = sorted({ts.time() for ts in all_ts if ts.date() == sel_date})
start_t = st.sidebar.time_input("Start", day_times[0])
end_t = st.sidebar.time_input("End", day_times[-1])

start_dt, end_dt = datetime.combine(sel_date, start_t), datetime.combine(
    sel_date, end_t
)
timeline = generate_timeline(start_dt, end_dt, 5)
if not timeline:
    st.error("Start must be < End")
    st.stop()

# ─────────── Downloads (GUI-inspired layout but to check out again) ───────────
st.sidebar.markdown("### 📥 Download Options")

st.sidebar.button("📦 Download All Files", use_container_width=True)
st.sidebar.button("🎧 Download All WAV Files", use_container_width=True)

st.sidebar.button("⬇ Download LoRes WAV", use_container_width=True)
st.sidebar.button("⬇ Download HiRes WAV", use_container_width=True)

st.sidebar.button("🖼️ Download LoRes Spec", use_container_width=True)
st.sidebar.button("🖼️ Download HiRes Spec", use_container_width=True)

st.sidebar.button("📁 Download All LoRes Specs", use_container_width=True)
st.sidebar.button("📁 Download All HiRes Specs", use_container_width=True)

# Optional dropdown like original
st.sidebar.selectbox("High Spectrum Mode", ["All Spectra", "Mode 1", "Mode 2"])

# ───────── Session‑state defaults ─────────
ss = st.session_state
ss.setdefault("range_slider", (timeline[0], timeline[0] + timedelta(hours=1)))
ss.setdefault("lores_hour", timeline[0].replace(minute=0, second=0, microsecond=0))
ss.setdefault("logs", [])

# ========== ACTIVE TIME WINDOW (depends on mode) ==========
if mode == "Use slider":
    rng_start, rng_end = st.slider(
        "Time window",
        min_value=timeline[0],
        max_value=timeline[-1],
        value=ss["range_slider"],
        step=timedelta(minutes=5),
        format="YYYY‑MM‑DD HH:mm",
        key="range_slider",
    )
    ss["lores_hour"] = rng_start.replace(minute=0, second=0, microsecond=0)

else:  # hour‑picker
    lo_hours = sorted(
        {
            lo["timestamp"].replace(minute=0, second=0, microsecond=0)
            for lo in lores
            if lo["timestamp"].date() == sel_date
        }
    )
    if ss["lores_hour"] not in lo_hours:
        ss["lores_hour"] = lo_hours[0]

    # wider middle column (6) keeps dropdown centred, arrows equal on sides
    col_l, col_mid, col_r = st.columns([2, 6, 2], gap="small")

    with col_l:
        st.button(
            "◀ 1 h",
            help="Previous LoRes hour",
            use_container_width=True,
            disabled=ss["lores_hour"] == lo_hours[0],
            on_click=lambda: ss.update(
                lores_hour=lo_hours[lo_hours.index(ss["lores_hour"]) - 1]
            ),
        )

    with col_mid:
        ss["lores_hour"] = st.selectbox(
            "LoRes hour",
            lo_hours,
            index=lo_hours.index(ss["lores_hour"]),
            format_func=lambda dt: dt.strftime("%H:%M"),
            label_visibility="collapsed",
            key="lores_picker",
        )

    with col_r:
        st.button(
            "1 h ▶",
            help="Next LoRes hour",
            use_container_width=True,
            disabled=ss["lores_hour"] == lo_hours[-1],
            on_click=lambda: ss.update(
                lores_hour=lo_hours[lo_hours.index(ss["lores_hour"]) + 1]
            ),
        )

    rng_start = ss["lores_hour"]
    rng_end = rng_start + timedelta(hours=1)
    ss["range_slider"] = (rng_start, rng_end)  # safe: slider not instantiated this run

# mirror window
st.sidebar.markdown(
    f"**Window:** {rng_start.strftime('%H:%M')} – {rng_end.strftime('%H:%M')}"
)

# ───────── Tabs ─────────
tab_spec, tab_wav, tab_logs = st.tabs(["📊 Spectrograms", "🔊 Waveform", "📜 Logs"])

# ----------------- TAB 1: Spectrograms -----------------
with tab_spec:

    # LoRes display
    if mode == "Use slider":
        lo_sel = [lo for lo in lores if rng_start <= lo["timestamp"] <= rng_end]
        st.subheader(f"LoRes frames in window ({len(lo_sel)})")
        for lo in sorted(lo_sel, key=lambda x: x["timestamp"]):
            st.image(
                lo["full_path"],
                use_container_width=True,
                caption=lo["timestamp"].strftime("%Y-%m-%d %H:%M"),
            )
    else:
        lo_img = next(
            (
                lo
                for lo in lores
                if lo["timestamp"].replace(minute=0, second=0, microsecond=0)
                == ss["lores_hour"]
            ),
            None,
        )
        if lo_img:
            st.image(
                lo_img["full_path"],
                use_container_width=True,
                caption=lo_img["timestamp"].strftime("%Y-%m-%d %H:%M"),
            )
        else:
            st.warning("LoRes missing for that hour")

    st.divider()

    # HiRes display
    if mode == "Use hour picker":
        col_b, col_a = st.columns(2)
        with col_b:
            mins_before = st.number_input("Minutes before", 0, 60, 0, 5)
        with col_a:
            mins_after = st.number_input("Minutes after", 0, 60, 60, 5)
        hi_start, hi_end = (
            ss["lores_hour"] - timedelta(minutes=int(mins_before)),
            ss["lores_hour"] + timedelta(minutes=int(mins_after)),
        )
    else:
        hi_start, hi_end = rng_start, rng_end

    hi_sel = [h for h in hires if hi_start <= h["timestamp"] < hi_end]
    st.subheader(
        f"HiRes between {hi_start.strftime('%H:%M')} – {hi_end.strftime('%H:%M')}  ({len(hi_sel)})"
    )
    if hi_sel:
        cols = st.columns(4)
        for i, h in enumerate(sorted(hi_sel, key=lambda x: x["timestamp"])):
            with cols[i % 4]:
                st.image(
                    h["full_path"],
                    use_container_width=True,
                    caption=h["timestamp"].strftime("%H:%M:%S"),
                )
    else:
        st.info("No HiRes frames in this interval.")

# ---------- TAB 2 • Wave + AI ----------
with tab_wav:
    wav_window = [w for w in wavs if rng_start <= w["timestamp"] <= rng_end]
    wav_file = (
        closest_match(wav_window, rng_start)
        if wav_window
        else (wavs[0] if wavs else None)
    )

    if wav_file:
        st.markdown(f"**Waveform:** {wav_file['filename']}")
        sr, data = wavfile.read(wav_file["path"])
        t_axis = np.arange(len(data)) / sr

        # if st.checkbox("Interactive zoom", True):
        fig = go.Figure(go.Scatter(x=t_axis, y=data, line=dict(width=1)))
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=10, b=40),
            xaxis_title="Time (s)",
            yaxis_title="Amplitude",
        )
        st.plotly_chart(fig, use_container_width=True)
        # else:
        #     fig = px.line(x=t_axis, y=data)
        #     fig.update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0))
        #     st.plotly_chart(fig, use_container_width=True)

        st.audio(wav_file["path"])
    else:
        st.info("No .wav files available.")

    st.divider()
    st.subheader("🤖  AI Inference (stub)")
    model = st.selectbox("Model", ["1‑D CNN", "Simple RNN", "Transformer"])
    if st.button("Run Inference"):
        st.success("Finished (mock). Check Logs tab.")
        st.session_state.setdefault("logs", []).extend(
            [
                f"🟢  {datetime.utcnow():%H:%M:%S} UTC — Started {model} inference",
                "🟡  00:00:01 UTC — No peaks found (stub)",
                "🟢  00:00:02 UTC — Finished inference (stub)",
            ]
        )

# ---------- TAB 3 • Logs ----------
with tab_logs:
    st.subheader("Runtime Log")
    for line in st.session_state.get("logs", []):
        color = (
            "limegreen"
            if line.startswith("🟢")
            else "orange" if line.startswith("🟡") else "red"
        )
        st.markdown(
            f"<span style='color:{color}'>{line}</span>", unsafe_allow_html=True
        )
    if not st.session_state.get("logs"):
        st.info("Everything working; images & waveforms loaded successfully.")

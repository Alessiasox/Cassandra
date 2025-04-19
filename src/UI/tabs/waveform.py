# src/ui/tabs/waveform.py

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.io import wavfile
from datetime import datetime
from ui.viewer_utils import closest_match

# Original version (commented out) for reference:
# def render_waveform_tab(wavs, rng_start, rng_end, ss):
#     st.subheader("🔊 Waveform + AI Inference")
#
#     # filter to the selected window
#     window = [w for w in wavs if rng_start <= w["timestamp"] <= rng_end]
#     if not window:
#         return st.info("No .wav files in this window.")
#
#     # pick the closest file to rng_start
#     wav_file = closest_match(window, rng_start)
#     st.markdown(f"**File:** `{wav_file['filename']}`")
#
#     # load and plot
#     sr, data = wavfile.read(wav_file["path"])
#     times = np.arange(len(data)) / sr
#     fig = go.Figure(go.Scatter(x=times, y=data, line=dict(width=1)))
#     fig.update_layout(
#         height=300,
#         margin=dict(l=0, r=0, t=10, b=40),
#         xaxis_title="Time (s)",
#         yaxis_title="Amplitude"
#     )
#     st.plotly_chart(fig, use_container_width=True)
#     st.audio(wav_file["path"])
#
#     st.divider()
#     st.subheader("🤖 AI Inference (stub)")
#     model = st.selectbox("Model", ["1-D CNN","Simple RNN","Transformer"])
#     if st.button("Run Inference"):
#         now = datetime.utcnow().strftime("%H:%M:%S UTC")
#         st.success("Inference complete (mock). See Logs.")
#         ss["logs"].extend([
#             f"🟢 {now} — Started {model}",
#             "🟡 00:00:01 — No peaks found (stub)",
#             "🟢 00:00:02 — Finished (stub)"
#         ])

def render_waveform_tab(wavs, rng_start, rng_end, ss):
    st.subheader("🔊 Waveform + AI Inference")

    # 1) Gather all WAVs in the selected window
    window = [w for w in wavs if rng_start <= w["timestamp"] <= rng_end]

    # 2) Pick closest if any, otherwise fall back to the first available WAV
    wav_file = (
        closest_match(window, rng_start)
        if window
        else (wavs[0] if wavs else None)
    )

    # 3) Plot + play audio if we have a file
    if wav_file:
        st.markdown(f"**File:** `{wav_file['filename']}`")
        sr, data = wavfile.read(wav_file["path"])
        times = np.arange(len(data)) / sr

        fig = go.Figure(go.Scatter(x=times, y=data, line=dict(width=1)))
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=10, b=40),
            xaxis_title="Time (s)",
            yaxis_title="Amplitude"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.audio(wav_file["path"])
    else:
        st.info("No .wav files available.")

    # 4) Always show the AI‑stub section
    st.divider()
    st.subheader("🤖 AI Inference (stub)")
    model = st.selectbox("Model", ["1-D CNN", "Simple RNN", "Transformer"])
    if st.button("Run Inference"):
        now = datetime.utcnow().strftime("%H:%M:%S UTC")
        st.success("Inference complete (mock). See Logs.")
        ss["logs"].extend([
            f"🟢 {now} — Started {model}",
            "🟡 00:00:01 — No peaks found (stub)",
            "🟢 00:00:02 — Finished (stub)"
        ])
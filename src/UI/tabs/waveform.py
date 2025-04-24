# src/ui/tabs/waveform.py
import io
from datetime import datetime
from typing import List, Dict, Optional

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from scipy.io import wavfile

from ui.viewer_utils import closest_match
from ssh.fetcher_remote import RemoteVLFClient


def render_waveform_tab(
    wavs: List[Dict],
    rng_start,
    rng_end,
    ss,
    is_remote: bool = False,
    client: Optional[RemoteVLFClient] = None,
):
    """
    Display one waveform and the AI inference stub.

    If `is_remote` the .wav is streamed with client.fetch_wav_bytes(path).
    """
    st.subheader("🔊 Waveform + AI Inference")

    # All wavs in window; choose the one closest to rng_start
    window = [w for w in wavs if rng_start <= w["timestamp"] <= rng_end]
    wav_meta = closest_match(window, rng_start) if window else (wavs[0] if wavs else None)

    if not wav_meta:
        st.info("No .wav files in this window.")
        _ai_stub(ss)           # still show the AI controls
        return

    st.markdown(f"**File:** `{wav_meta['filename']}`")

    # ---------- Load audio ----------
    if is_remote and client:
        raw_bytes = client.fetch_wav_bytes(wav_meta["remote_path"])
        sr, data  = wavfile.read(io.BytesIO(raw_bytes))
        st.audio(raw_bytes, format="audio/wav")
    else:
        sr, data = wavfile.read(wav_meta["path"])
        st.audio(wav_meta["path"])

    # ---------- Plot ----------
    t = np.arange(len(data)) / sr
    fig = go.Figure(go.Scatter(x=t, y=data, line=dict(width=1)))
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=10, b=40),
        xaxis_title="Time (s)",
        yaxis_title="Amplitude",
    )
    st.plotly_chart(fig, use_container_width=True)

    _ai_stub(ss)


# ----------------------------------------------------------------------
def _ai_stub(ss):
    """Simple AI inference mock that logs to session_state."""
    st.divider()
    st.subheader("🤖 AI Inference (stub)")
    model = st.selectbox("Model", ["1 D CNN", "Simple RNN", "Transformer"])
    if st.button("Run Inference"):
        now = datetime.utcnow().strftime("%H:%M:%S UTC")
        st.success("Inference complete (mock). See Logs tab.")
        ss["logs"].extend(
            [
                f"🟢 {now} — Started {model}",
                "🟡 00:00:01 — No peaks found (stub)",
                "🟢 00:00:02 — Finished (stub)",
            ]
        )
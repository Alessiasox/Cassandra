import io
import warnings
from datetime import datetime, timezone
from typing import Dict, List, Optional

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from scipy.io import wavfile
from scipy.io.wavfile import WavFileWarning

from ui.viewer_utils   import closest_match
from ssh.fetcher_remote import RemoteVLFClient

warnings.filterwarnings("ignore", category=WavFileWarning)


def _load_wav(
    meta: Dict,
    *,
    is_remote: bool,
    client: Optional[RemoteVLFClient],
) -> tuple[np.ndarray, int]:
    """
    Return (signal, sample_rate) for the given WAV metadata, fetching
    over SSH when needed.
    """
    if is_remote and client:
        raw = client.fetch_wav_bytes(meta["remote_path"])
        data, sr = wavfile.read(io.BytesIO(raw))
    else:
        sr, data = wavfile.read(meta["path"])
    return data, sr


# ─────────────────────────────────────────────────────────────────────
def render_waveform_tab(
    wavs:        List[Dict],
    rng_start,
    rng_end,
    ss,
    *,
    is_remote: bool = False,
    client:    Optional[RemoteVLFClient] = None,
) -> None:
    """Waveform + AI tab (local **and** remote)."""

    st.subheader("🔊 Waveform + AI Inference")

    # ensure both sides are tz-aware UTC
    if rng_start.tzinfo is None:
        rng_start = rng_start.replace(tzinfo=timezone.utc)
        rng_end   = rng_end.replace(tzinfo=timezone.utc)

    window = [w for w in wavs if rng_start <= w["timestamp"] <= rng_end]

    wav_file = (
        closest_match(window, rng_start)
        if window
        else (wavs[0] if wavs else None)
    )

    if wav_file:
        st.markdown(f"**File:** `{wav_file['filename']}`")

        signal, sr = _load_wav(wav_file, is_remote=is_remote, client=client)
        t_axis = np.arange(len(signal)) / sr

        fig = go.Figure(go.Scatter(x=t_axis, y=signal, line=dict(width=1)))
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=10, b=40),
            xaxis_title="Time (s)",
            yaxis_title="Amplitude",
        )
        st.plotly_chart(fig, use_container_width=True)

        if is_remote and client:          # play from bytes
            st.audio(io.BytesIO(client.fetch_wav_bytes(wav_file["remote_path"])))
        else:
            st.audio(wav_file["path"])
    else:
        st.info("No .wav files in this window.")

    # ── AI-stub (unchanged) ─────────────────────────────────────────
    st.divider()
    st.subheader("🤖 AI Inference (stub)")
    model = st.selectbox("Model", ["1-D CNN", "Simple RNN", "Transformer"])
    if st.button("Run Inference"):
        now = datetime.utcnow().strftime("%H:%M:%S UTC")
        st.success("Inference complete (mock). See Logs.")
        ss.setdefault("logs", []).extend(
            [
                f"🟢 {now} — Started {model}",
                "🟡 00:00:01 — No peaks found (stub)",
                "🟢 00:00:02 — Finished (stub)",
            ]
        )
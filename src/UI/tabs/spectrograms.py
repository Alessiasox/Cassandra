"""
Compact Spectrograms tab
────────────────────────
• Works for both local & remote images (uses `RemoteVLFClient`)
• Supports the two interaction modes you already had
• Injects a tiny bit of CSS so the whole layout is tighter
"""

from __future__ import annotations

import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import plotly.express as px
import streamlit as st
from PIL import Image

from ui.viewer_utils import closest_match          # still used by Waveform tab
from ssh.fetcher_remote import RemoteVLFClient     # <-- keep remote support


# ─── one-shot CSS to make the tab look denser ────────────────────────────
_COMPACT_CSS = """
<style>
/* remove the default ~16-20 px vertical padding Streamlit adds */
section.main > div               { padding-top: .25rem; padding-bottom: .25rem; }
/* smaller caption line */
.stCaption                       { margin-top: .25rem; font-size: .75rem; }
/* slimmer hr() spacing */
hr                               { margin: .5rem 0 .75rem 0 !important; }
</style>
"""
st.markdown(_COMPACT_CSS, unsafe_allow_html=True)


# ────────────────────────── public API ░ render tab ░──────────────────────────
def render_spectrograms_tab(
    *,
    low_res_images:     List[Dict],
    high_res_images:    List[Dict],
    control_mode: str,          # "Use slider" | "Use hour picker"
    window_start:   datetime,
    window_end:     datetime,
    session_state:          Dict,          # streamlit.session_state
    is_remote:   bool = False,
    client:      Optional[RemoteVLFClient] = None,
) -> None:
    """Main entry for the Spectrograms tab."""

    st.subheader("📊 Spectrograms")

    # ───────────────────── LoRes section ─────────────────────
    if control_mode == "Use slider":
        lo_to_show = [
            img for img in low_res_images
            if window_start <= img["timestamp"] <= window_end
        ]
        st.markdown(f"**LoRes frames in window:** {len(lo_to_show)}")
        for img in sorted(lo_to_show, key=lambda x: x["timestamp"]):
            _show_image(img, is_remote, client,
                        caption=img["timestamp"].strftime("%H:%M"))

    else:  # hour-picker: exactly one low-res frame
        target_hour = session_state["lores_hour"]
        img = next(
            (im for im in low_res_images
             if im["timestamp"].replace(minute=0, second=0, microsecond=0) == target_hour),
            None
        )
        if img:
            _show_image(img, is_remote, client,
                        caption=img["timestamp"].strftime("%H:%M"))
        else:
            st.warning("No LoRes frame for selected hour.")

    st.divider()

    # ───────────────────── HiRes section ─────────────────────
    if control_mode == "Use hour picker":
        col_b, col_a = st.columns(2)
        with col_b:
            mins_before = st.number_input("Minutes before", 0, 60, 0, 5, key="mins_b")
        with col_a:
            mins_after  = st.number_input("Minutes after",  0, 60, 60, 5, key="mins_a")
        hi_start = session_state["lores_hour"] - timedelta(minutes=int(mins_before))
        hi_end   = session_state["lores_hour"] + timedelta(minutes=int(mins_after))
    else:
        hi_start, hi_end = window_start, window_end

    hi_to_show = [
        img for img in high_res_images
        if hi_start <= img["timestamp"] < hi_end
    ]
    st.markdown(
        f"**HiRes between {hi_start:%H:%M} – {hi_end:%H:%M} "
        f"({len(hi_to_show)})**"
    )

    if hi_to_show:
        cols = st.columns(4, gap="small")
        for idx, img in enumerate(sorted(hi_to_show, key=lambda x: x["timestamp"])):
            with cols[idx % 4]:
                _show_image(img, is_remote, client,
                            caption=img["timestamp"].strftime("%H:%M:%S"))
    else:
        st.info("No HiRes frames in this interval.")


# ───────────────────────── helper: render one image ──────────────────────────
def _show_image(
    img_meta: Dict,
    is_remote: bool,
    client: Optional[RemoteVLFClient],
    *,
    caption: str,
) -> None:
    """Load (stream if remote) and plot a single spectrogram frame."""

    if is_remote and client:
        raw_bytes = client.fetch_image_bytes(img_meta["remote_path"])
        pil_img   = Image.open(io.BytesIO(raw_bytes))
    else:
        pil_img   = Image.open(img_meta["full_path"])

    fig = px.imshow(pil_img, binary_string=True)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_showscale=False,
    )
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)

    st.plotly_chart(fig, use_container_width=True)
    st.caption(caption)
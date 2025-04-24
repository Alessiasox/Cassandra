# ── src/ui/tabs/spectrograms.py ─────────────────────────────────────────
from __future__ import annotations

import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import streamlit as st
import plotly.express as px
from PIL import Image

from ssh.fetcher_remote import RemoteVLFClient   # ➜ remote streaming support


# ───────── helpers ────────────────────────────────────────────────────
def _load_pillow(img_meta: Dict,
                 is_remote: bool,
                 client: Optional[RemoteVLFClient]) -> Image.Image:
    """Return a Pillow image – stream via SSH if `is_remote`."""
    if is_remote and client:
        raw = client.fetch_image_bytes(img_meta["remote_path"])
        return Image.open(io.BytesIO(raw))
    return Image.open(img_meta["full_path"])


def _plotly_img(pil_img: Image.Image):
    fig = px.imshow(pil_img, binary_string=True)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                      coloraxis_showscale=False)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    return fig


# ───────── public tab renderer ────────────────────────────────────────
def render_spectrograms_tab(
    *,
    low_res_images:  List[Dict],
    high_res_images: List[Dict],
    control_mode:    str,              # "Use slider" | "Use hour picker"
    window_start:    datetime,
    window_end:      datetime,
    session_state:   Dict,             # st.session_state
    is_remote:       bool = False,
    client:          Optional[RemoteVLFClient] = None,
) -> None:
    """Compact Spectrograms tab - local & SSH aware."""
    st.subheader("📊 Spectrograms")

    # ── LoRes section ───────────────────────────────────────────────
    if control_mode == "Use slider":
        lo_sel = [img for img in low_res_images
                  if window_start <= img["timestamp"] <= window_end]
        st.write(f"LoRes frames: {len(lo_sel)}")
        for img in sorted(lo_sel, key=lambda x: x["timestamp"]):
            pil = _load_pillow(img, is_remote, client)
            st.image(pil,
                     caption=img["timestamp"].strftime("%H:%M"),
                     use_container_width=True)

    else:  # hour picker → single frame
        target_hour = session_state["lores_hour"]
        img = next(
            (im for im in low_res_images
             if im["timestamp"].replace(minute=0, second=0, microsecond=0)
                == target_hour),
            None
        )
        if img:
            pil = _load_pillow(img, is_remote, client)
            st.image(pil,
                     caption=img["timestamp"].strftime("%H:%M"),
                     use_container_width=True)
        else:
            st.warning("No LoRes frame for this hour.")

    st.divider()

    # ── HiRes section ───────────────────────────────────────────────
    if control_mode == "Use hour picker":
        c_bef, c_aft = st.columns(2)
        with c_bef:
            mins_before = st.number_input("Minutes before", 0, 60, 0, 5,
                                          key="mins_before")
        with c_aft:
            mins_after  = st.number_input("Minutes after",  0, 60, 60, 5,
                                          key="mins_after")
        hi_start = session_state["lores_hour"] - timedelta(minutes=int(mins_before))
        hi_end   = session_state["lores_hour"] + timedelta(minutes=int(mins_after))
    else:
        hi_start, hi_end = window_start, window_end

    hi_sel = sorted(
        [img for img in high_res_images
         if hi_start <= img["timestamp"] < hi_end],
        key=lambda x: x["timestamp"]
    )
    st.write(f"HiRes frames: {len(hi_sel)} "
             f"({hi_start:%H:%M}-{hi_end:%H:%M})")

    if hi_sel:
        cols = st.columns(4)
        for idx, img in enumerate(hi_sel):
            with cols[idx % 4]:
                pil = _load_pillow(img, is_remote, client)
                st.plotly_chart(_plotly_img(pil), use_container_width=True)
                st.caption(img["timestamp"].strftime("%H:%M:%S"))
    else:
        st.info("No HiRes frames in this interval.")
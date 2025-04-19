import streamlit as st
from datetime import timedelta
from ui.viewer_utils import closest_match
from PIL import Image
import plotly.express as px

def render_spectrograms_tab(lores, hires, sel_date, mode, rng_start, rng_end, ss):
    st.subheader("📊 Spectrograms")

    # LoRes display
    if mode == "Use slider":
        lo_sel = [l for l in lores if rng_start <= l["timestamp"] <= rng_end]
        st.write(f"LoRes frames: {len(lo_sel)}")
        for lo in sorted(lo_sel, key=lambda x: x["timestamp"]):
            st.image(lo["full_path"], caption=lo["timestamp"].strftime("%H:%M"), use_container_width=True)
    else:
        lo_img = next(
            (l for l in lores if l["timestamp"].replace(minute=0,second=0,microsecond=0)==ss["lores_hour"]),
            None
        )
        if lo_img:
            st.image(lo_img["full_path"], caption=lo_img["timestamp"].strftime("%H:%M"), use_container_width=True)
        else:
            st.warning("No LoRes frame for this hour.")

    st.divider()

    # HiRes display
    if mode == "Use hour picker":
        colb, cola = st.columns(2)
        with colb:
            mins_before = st.number_input("Minutes before", 0, 60, 0, 5)
        with cola:
            mins_after  = st.number_input("Minutes after", 0, 60, 60, 5)
        hi_start = ss["lores_hour"] - timedelta(minutes=mins_before)
        hi_end   = ss["lores_hour"] + timedelta(minutes=mins_after)
    else:
        hi_start, hi_end = rng_start, rng_end

    hi_sel = sorted([h for h in hires if hi_start <= h["timestamp"] < hi_end],
                    key=lambda x: x["timestamp"])
    st.write(f"HiRes frames: {len(hi_sel)} ({hi_start.strftime('%H:%M')}–{hi_end.strftime('%H:%M')})")
    if hi_sel:
        cols = st.columns(4)
        for idx,h in enumerate(hi_sel):
            with cols[idx % 4]:
                img = Image.open(h["full_path"])
                fig = px.imshow(img, binary_string=True)
                fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
                st.caption(h["timestamp"].strftime("%H:%M:%S"))
    else:
        st.info("No HiRes frames in this interval.")
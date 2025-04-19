import streamlit as st

def render_logs_tab(ss):
    st.subheader("📜 Runtime Logs")
    logs = ss.get("logs", [])
    if logs:
        for line in logs:
            color = ("limegreen" if line.startswith("🟢")
                     else "orange" if line.startswith("🟡")
                     else "red")
            st.markdown(f"<span style='color:{color}'>{line}</span>", unsafe_allow_html=True)
    else:
        st.info("No log entries yet.")
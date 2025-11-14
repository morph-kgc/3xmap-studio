import streamlit as st
from streamlit_js_eval import streamlit_js_eval
import base64


# Config---------------------------------------------------
if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
    st.set_page_config(page_title="3xmap Studio", layout="wide",
        page_icon="logo/fav_icon.png")
    color = "#511D66"
else:
    st.set_page_config(page_title="3xmap Studio", layout="wide",
        page_icon="logo/fav_icon_inverse.png")
    color = "#d8c3f0"

# Automatic detection of dark mode-------------------------
if "dark_mode_flag" not in st.session_state or st.session_state["dark_mode_flag"] is None:
    st.session_state["dark_mode_flag"] = streamlit_js_eval(js_expressions="window.matchMedia('(prefers-color-scheme: dark)').matches",
        key="dark_mode")


image_path = "logo/logo_inverse.png" if st.session_state["dark_mode_flag"] else "logo/logo.png"
with open(image_path, "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()
st.markdown(
    f"""
    <div style="display:flex; justify-content:flex-end;">
        <img src="data:image/png;base64,{image_base64}" alt="Logo"
             style="height:100px; margin-right:70px; border-radius:8px;" />
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(f"""
<h1>Welcome to <span style='color:{color};'>3Xmap Studio</span></h1>
""", unsafe_allow_html=True)
st.write("Use sidebar to work with existing or new mapping.")

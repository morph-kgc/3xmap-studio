import streamlit as st


if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
    st.set_page_config(page_title="3Xmap Studio", layout="wide",
        page_icon="logo/fav_icon.png")
else:
    st.set_page_config(page_title="3Xmap Studio", layout="wide",
        page_icon="logo/fav_icon_inverse.png")


# st.sidebar.title("Menu")
# st.sidebar.write("Select a page")



st.title("Welcome to 3Xmap Studio")
st.write("Use sidebar to work with existing or new mapping")

import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle
from rdflib.namespace import split_uri


st.title("Display mapping")

col1,col2 = st.columns([2,1.5])
if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
    with col1:
        st.markdown(f"""
        <div style="background-color:#f8d7da; padding:1em;
                    border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
            ❗ You need to create or load a mapping. Please go to the
            <b style="color:#a94442;">Global Configuration page</b>.
        </div>
        """, unsafe_allow_html=True)
        st.stop()

st.markdown(f"""
    <div style="background-color:#fff3cd; padding:1em;
    border-radius:5px; color:#856404; border:1px solid #ffeeba;">
        ⚠️ This panel is not ready yet, temporary display.</div>
""", unsafe_allow_html=True)

st.write("")
st.write("")


#_______________________________________
#Output the mapping as Turtle
# if st.button("Serialise"):
#     print(g.serialize(format="turtle"))

for s, p, o in st.session_state["g_mapping"]:
    st.write(f"🔹 ({s}, {p}, {o})")

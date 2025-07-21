import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle
from rdflib.namespace import split_uri


st.title("Display mapping")

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

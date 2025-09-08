import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace
import utils

st.title("Manage Logical Sources")

col1, col2 = st.columns([2,1])
with col1:
    st.markdown(f"""
    <div style="background-color:#f8d7da; padding:1em;
                border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
        ❌ This panel is not ready yet.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

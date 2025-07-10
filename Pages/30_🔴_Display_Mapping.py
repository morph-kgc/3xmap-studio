import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle
from rdflib.namespace import split_uri


#_______________________________________
#Output the mapping as Turtle
# if st.button("Serialise"):
#     print(g.serialize(format="turtle"))

for s, p, o in st.session_state["g_mapping"]:
    st.write(f"🔹 ({s}, {p}, {o})")

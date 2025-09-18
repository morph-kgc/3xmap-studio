import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle
from rdflib.namespace import split_uri

# Header
st.markdown("""<div style="display:flex; align-items:center; background-color:#f0f0f0; padding:12px 18px;
    border-radius:8px; margin-bottom:16px;">
    <span style="font-size:1.7rem; margin-right:18px;">🔮</span><div>
        <h3 style="margin:0; font-size:1.75rem;">
            <span style="color:#511D66; font-weight:bold; margin-right:12px;">◽◽◽◽◽</span>
            Materialise Graph
            <span style="color:#511D66; font-weight:bold; margin-left:12px;">◽◽◽◽◽</span>
        </h3>
        <p style="margin:0; font-size:0.95rem; color:#555;">
            Use <b>Morph-KGC</b> to materialise a graph from <b>mappings</b> and <b>data sources</b>.
        </p>
    </div></div>""", unsafe_allow_html=True)

#____________________________________________
#PRELIMINARY

# Import style
utils.import_st_aesthetics()
st.write("")

# Namespaces
RML, RR, QL = utils.get_required_ns().values()


# Initialise session state variables
#TAB1
if "morph-kgc_ds_dict" not in st.session_state:
    st.session_state["morph-kgc_ds_dict"] = {}


#____________________________________________________________
# PANELS OF THE PAGE (tabs)

tab1, tab2, tab3 = st.tabs(["Materialise", "Add Data Sources", "Add Mappings"])


#________________________________________________
# MANAGE SQL DATA SOURCES
with tab1:

    col1, col2 = st.columns([2,1.5])

    with col1:
        col1a, col1b = st.columns([2,1])

    # PURPLE HEADING - ADD DATA SOURCE
    with col1:
        st.markdown("""<div class="purple-heading">
                📊 Configure Data Source
            </div>""", unsafe_allow_html=True)
        st.write("")

        with col1:
            col1a, col1b = st.columns([2,1])

        with col1a:
            mk_ds_label = st.text_input("⌨️ Enter data source label:*", key="key_mk_ds_label")

        with col1b:
            st.write("")
            mk_ds_type = st.radio("🖱️ Select an option:*", ["📊 SQL Database", "🛢️ Non-SQL data"],
                label_visibility="collapsed", key="key_mk_ds_type")

    # PURPLE HEADING - ADD OPTIONS
    with col1:
        st.write("_______")
        st.markdown("""<div class="purple-heading">
                ⚙️ Configure Options
            </div>""", unsafe_allow_html=True)
        st.write("")

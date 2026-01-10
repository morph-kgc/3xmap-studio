import base64
from collections import defaultdict
import configparser
import elementpath
import io
import json
import jsonpath_ng
import networkx as nx
import os
import pandas as pd
from PIL import Image   # for logo rendering
import plotly.express as px
from pymongo import MongoClient
from pyvis.network import Network
import rdflib
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import split_uri
from rdflib.namespace import DC, DCTERMS, OWL, RDF, RDFS, XSD
import re
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ArgumentError
import sqlglot
import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from streamlit.runtime.uploaded_file_manager import UploadedFile
from urllib.parse import urlparse, urlunparse
import utils
import uuid
import xml.etree.ElementTree as ET


# REQUIRED NS===================================================================
#_____________________________________________________
# Funtion to get dictionary with default namespaces (DO NOT MODIFY LIST)
# Default namespaces are automatically added to the g namespace manager by rdflib
# For clarity, we bind them and don't allow to remove
def get_default_ns_dict():

    default_ns_dict = {"brick": URIRef("https://brickschema.org/schema/Brick#"),
        "csvw": URIRef("http://www.w3.org/ns/csvw#"),
        "dc": URIRef("http://purl.org/dc/elements/1.1/"),
        "dcam": URIRef("http://purl.org/dc/dcam/"),
        "dcat": URIRef("http://www.w3.org/ns/dcat#"),
        "dcmitype": URIRef("http://purl.org/dc/dcmitype/"),
        "dcterms": URIRef("http://purl.org/dc/terms/"),
        "doap": URIRef("http://usefulinc.com/ns/doap#"),
        "foaf": URIRef("http://xmlns.com/foaf/0.1/"),
        "geo": URIRef("http://www.opengis.net/ont/geosparql#"),
        "odrl": URIRef("http://www.w3.org/ns/odrl/2/"),
        "org": URIRef("http://www.w3.org/ns/org#"),
        "owl": URIRef("http://www.w3.org/2002/07/owl#"),
        "prof": URIRef("http://www.w3.org/ns/dx/prof/"),
        "prov": URIRef("http://www.w3.org/ns/prov#"),
        "qb": URIRef("http://purl.org/linked-data/cube#"),
        "rdf": URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
        "rdfs": URIRef("http://www.w3.org/2000/01/rdf-schema#"),
        "schema": URIRef("https://schema.org/"),
        "sh": URIRef("http://www.w3.org/ns/shacl#"),
        "skos": URIRef("http://www.w3.org/2004/02/skos/core#"),
        "sosa": URIRef("http://www.w3.org/ns/sosa/"),
        "ssn": URIRef("http://www.w3.org/ns/ssn/"),
        "time": URIRef("http://www.w3.org/2006/time#"),
        "vann": URIRef("http://purl.org/vocab/vann/"),
        "void": URIRef("http://rdfs.org/ns/void#"),
        "wgs": URIRef("https://www.w3.org/2003/01/geo/wgs84_pos#"),
        "xml": URIRef("http://www.w3.org/XML/1998/namespace"),
        "xsd": URIRef("http://www.w3.org/2001/XMLSchema#")}

    return default_ns_dict
#_______________________________________________________

#________________________________________________________
# Function to retrieve namespaces which are needed for our code
def get_required_ns_dict():

    required_ns_dict = {"rml": Namespace("http://w3id.org/rml/"),
        "ql": Namespace("http://semweb.mmlab.be/ns/ql#")}

    return required_ns_dict
#________________________________________________________

#________________________________________________________
# Retrieving necessary namespaces for UTILS page
RML, QL = get_required_ns_dict().values()
#________________________________________________________


# DEFAULT VARIABLES (CAN BE CUSTOMISED)=========================================
#________________________________________________________
# Function to get the name of the used folders (only one argument should be True)
# Used in 🌍 Global Configuration, 🛢️ Data Files pages and 🔮 Materialise Graph
def get_folder_name(saved_sessions=False, data_sources=False, temp_materialisation_files=False):

    if saved_sessions:
        return "saved_sessions"

    elif data_sources:
        return "data_sources"

    elif temp_materialisation_files:
        return "materialisation_files_temp"
#________________________________________________________

#_____________________________________________________
# Function to get the default base iri for the base components
# Used in 🌍 Global Configuration page
def get_default_base_ns():

    return ["map3x", Namespace("http://3xmap.org/mapping/")]
#________________________________________________________

#_____________________________________________________
# Function to get dictionary with predefined namespaces so that they can be easily bound
# Used in 🌍 Global Configuration page
def get_predefined_ns_dict():

    predefined_ns_dict = {
        "rdf": URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
        "rdfs": URIRef("http://www.w3.org/2000/01/rdf-schema#"),
        "owl": URIRef("http://www.w3.org/2002/07/owl#"),
        "xsd": URIRef("http://www.w3.org/2001/XMLSchema#"),
        "foaf": URIRef("http://xmlns.com/foaf/0.1/"),
        "dc": URIRef("http://purl.org/dc/elements/1.1/"),
        "dcterms": URIRef("http://purl.org/dc/terms/"),
        "skos": URIRef("http://www.w3.org/2004/02/skos/core#"),
        "time": URIRef("http://www.w3.org/2006/time#"),
        "prov": URIRef("http://www.w3.org/ns/prov#")}

    default_dict = get_default_ns_dict()
    filtered_ns_dict = {}  # filter out the default namespaces
    for k, v in predefined_ns_dict.items():
        if v not in default_dict.values():
            filtered_ns_dict[k] = v

    return filtered_ns_dict
#_____________________________________________________

#______________________________________________
# Funtion to get list of datatypes
def get_default_datatypes_dict():

    datatype_dict = {"xsd:string": XSD.string, "xsd:integer": XSD.integer,
        "xsd:decimal": XSD.decimal, "xsd:float": XSD.float,
        "xsd:double": XSD. double, "xsd:boolean": XSD.boolean,
        "xsd:date": XSD.date, "xsd:dateTime": XSD.dateTime,
        "xsd:time": XSD.time, "xsd:anyURI": XSD.anyURI,
        "rdf:XMLLiteral": XSD.XMLLiteral, "rdf:HTML": RDF.HTML,
        "rdf:JSON": RDF.JSON}

    return datatype_dict
#______________________________________________

#______________________________________________
# Funtion to get list of language tags (should be valid BCP 47 language tags)
def get_default_language_tags_list():

    language_tags_list = ["en", "es", "fr", "de",
        "ja", "pt", "en-US", "en-GB", "ar", "ru", "hi", "zh", "sr"]

    return language_tags_list
#______________________________________________

# AESTHETICS====================================================================
#______________________________________________________
# Function to render logo in sidebar
def render_sidebar_logo(dark_mode=False):

    resize_factor = 0.35
    image_path = "logo/logo_inverse.png" if dark_mode else "logo/logo.png"

    # open and resize image
    with open(image_path, "rb") as img_file:
        image = Image.open(img_file).copy()
    width, height = image.size
    resized_image = image.resize((int(width * resize_factor), int(height * resize_factor)))

    # convert to base64
    buf = io.BytesIO()
    resized_image.save(buf, format="PNG")
    image_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    # display image
    st.sidebar.markdown(f"""<div style="text-align: center;">
            <img src="data:image/png;base64,{image_base64}" style="margin-top:10px; border-radius:8px;" />
        </div>""", unsafe_allow_html=True)
#______________________________________________________

#______________________________________________________
# Function to import style
def import_st_aesthetics():

    return """<style>

    /* TABS */
        /* Style tab buttons inside stTabs */
        div[data-testid="stTabs"] button[data-baseweb="tab"] {flex: 1 1 auto;
            background-color: #555555; color: white; font-size: 25px;
            padding: 1.2em; border-radius: 5px; border: none;
            margin: 6px;}

        /* Hover effect for tab buttons */
        div[data-testid="stTabs"] button[data-baseweb="tab"]:hover {
            background-color: #7a4c8f;}

        /* Style tab label text */
        div[data-testid="stTabs"] button[data-baseweb="tab"] > div > span {
            font-size: 36px !important;}

        /* Style selected tab */
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
            background-color: #9871b5; color: white; font-weight: bold;
            box-shadow: 0 0 10px #9871b5;}

    /* MAIN BUTTONS (AND DOWNLOAD BUTTON) */
        div.stButton > button,
        div.stDownloadButton > button {background-color: #555555; color: white;
            height: 2.4em; width: auto; border-radius: 6px;
            border: 1px solid #333333; font-size: 16px;
            padding: 0.4em 1em; transition: background-color 0.2s ease;}

        div.stButton > button:hover,
        div.stDownloadButton > button:hover {background-color: #FF4B4B;
            color: white;}

    /* MULTISELECT */
        div[data-baseweb="select"] > div {color: black !important;}

        div[data-baseweb="select"] span {background-color: #d3d3d3 !important;
        color: black !important;}

     /* FILE UPLOADER */
        div[data-testid="stFileUploader"] > div {
        flex-wrap: wrap; justify-content: space-between;}

        div[data-testid="stFileUploader"] button {flex: 0 0 auto;
        background-color: #555555; color: white; height: 2.4em; font-size: 15px;
        padding: 1.2em; border-radius: 5px; border: none;margin: 4px;}

        div[data-testid="stFileUploader"] button div span {font-size: 30px !important;}

        div[data-testid="stFileUploader"] button:hover {background-color: #FF4B4B; color: white}

        div[data-testid="stFileUploader"] button[aria-selected="true"] {
            background-color: #9871b5; color: white; font-weight: bold;
            box-shadow: 0 0 10px #9871b5;}

        /* Uploaded file info */
        div[data-testid="stFileUploader"] ul {font-size: 14px !important;}

        /* x button size */
        div[data-testid="stFileUploader"] ul button {
        padding: 1px 5px !important; height: 22px !important;
        line-height: 1 !important; min-height: 0 !important;}

        /* x button icon */
        div[data-testid="stFileUploader"] ul button svg {width: 14px !important;
            height: 14px !important;}

    /* PURPLE HEADINGS */
            .purple-heading {background-color:#e6e6fa; border-bottom:4px solid #511D66;
                border-radius:5px; padding:10px; margin-bottom:8px;
                font-size:1.1rem; font-weight:600; color:#511D66;}

    /* GRAY HEADINGS */
            .gray-heading {background-color:#f2f2f2; border-bottom:4px solid #777777;
                border-radius:5px; padding:6px; margin-bottom:8px;
                font-size:1rem; font-weight:600; color:#333333;}

    /* GRAY PREVIEW MESSAGE */
            .gray-preview-message {background-color:#f9f9f9; padding:0.7em; border-radius:5px;
            color:#333333; border:1px solid #e0e0e0; font-size: 0.92em; word-wrap: break-word;}

    /* BLUE PREVIEW MESSAGE */
            .blue-preview-message {background-color: #eaf4ff; padding:0.7em; border-radius:5px;
            color:#0c5460; border:1px solid #d0e4ff; font-size: 0.92em; word-wrap: break-word;}

    /* SUCCESS MESSAGE FLAG */
        .success-message-flag {background-color: #d4edda; padding: 1em;
            border-radius: 5px; color: #155724; word-wrap: break-word;}

        .success-message-flag b {color: #0f5132;}

    /* SUCCESS MESSAGE */
    .success-message {border-left: 4px solid #155724;
        ;padding: 0.4em 0.6em;
        color: #155724; font-size: 0.85em; font-family: "Source Sans Pro", sans-serif;
        margin: 0.5em 0; background-color: #edf7f1;
        border-radius: 4px; box-sizing: border-box; word-wrap: break-word;}

    .success-message b {color: #0f5132; font-weight:600;}

    /* WARNING MESSAGE*/
        .warning-message {border-left: 4px solid #6c5e2e;
            ; padding: 0.4em 0.6em;
            color: #6c5e2e; font-size: 0.85em; font-family: "Source Sans Pro", sans-serif;
            margin: 0.5em 0; background-color: #fff7db;
            border-radius: 4px; box-sizing: border-box; word-wrap: break-word;}

        .warning-message b {color: #cc9a06; font-weight: 600;}

    /* ERROR MESSAGE */
        .error-message {border-left: 4px solid #7a2e33;
            padding: 0.4em 0.6em; color: #7a2e33; font-size: 0.85em;
            font-family: "Source Sans Pro", sans-serif; margin: 0.5em 0;
            background-color: #fbe6e8; border-radius: 4px;
            box-sizing: border-box; word-wrap: break-word;}

        .error-message b {color: #a94442; font-weight: 600;}

    /* INFO MESSAGE GRAY */
    .info-message-gray {border-left: 4px solid #777777;
        ;padding: 0.4em 0.6em;
        color: #4d4d4d; font-size: 0.85em; font-family: "Source Sans Pro", sans-serif;
        margin: 0.5em 0; background-color: #f5f5f5;
        border-radius: 4px; box-sizing: border-box; word-wrap: break-word;}

    .info-message-gray b {
        color: #111111; font-weight:600;}

    /* INFO MESSAGE BLUE */
    .info-message-blue {border-left: 4px solid #0c5460;
        ;padding: 0.4em 0.6em;
        color: #0c5460; font-size: 0.85em; font-family: "Source Sans Pro", sans-serif;
        margin: 0.5em 0; background-color: #eaf4ff;
        border-radius: 4px; box-sizing: border-box; word-wrap: break-word;}

    .info-message-blue b {
        color: #003366; font-weight:600;}

    /* SMALL HEADING FOR SUBSECTIONS */
    .small-subsection-heading {font-size: 13px; font-weight: 500;
        margin-top: 10px; margin-bottom: 6px; border-top: 0.5px solid #ccc;
        padding-bottom: 4px;}

    /* VERY SMALL INFO */
    .very-small-info {text-align: right; font-size: 10.5px;
        margin-top: -10px;}

    /* VERY SMALL INFO TOP */
    .very-small-info-top {font-size: 10.5px;
        margin-bottom: -10px;}

    </style>"""
#_______________________________________________________

#_______________________________________________________
# Function to import style - dark mode
def import_st_aesthetics_dark_mode():

    return """<style>

    /* TABS - dark mode*/
        /* Style tab buttons inside stTabs */
        div[data-testid="stTabs"] button[data-baseweb="tab"] {flex: 1 1 auto;
            background-color: #222222; color: white; font-size: 25px;
            padding: 1.2em; border-radius: 5px; border: none;
            margin: 6px;}

        /* Hover effect for tab buttons */
        div[data-testid="stTabs"] button[data-baseweb="tab"]:hover {
            background-color: #47295c;}

        /* Style tab label text */
        div[data-testid="stTabs"] button[data-baseweb="tab"] > div > span {
            font-size: 36px !important;}

        /* Style selected tab */
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
            background-color: #281634; color: white; font-weight: bold;
            box-shadow: 0 0 10px #9871b5;}

    /* MAIN BUTTONS (AND DOWNLOAD BUTTON) */
        div.stButton > button,
        div.stDownloadButton > button {background-color: #555555; color: white;
            height: 2.4em; width: auto; border-radius: 6px;
            border: 1px solid #333333; font-size: 16px;
            padding: 0.4em 1em; transition: background-color 0.2s ease;}

        div.stButton > button:hover,
        div.stDownloadButton > button:hover {background-color: #FF4B4B;
            color: white;}

    /* SELECTBOX - Dark Mode */
        div[data-baseweb="select"] {background-color: #1c1c1c !important;
          border-radius: 5px; border: 1px solid #444 !important;
          color: #ddd !important;}

        /* Dropdown arrow and text */
        div[data-baseweb="select"] div {color: #ddd !important;}

        /* Selected option */
        div[data-baseweb="select"] > div {background-color: #1c1c1c !important;
          color: #ddd !important;}

        /* Options in dropdown */
        ul[role="listbox"] {background-color: #2a2a2a !important;
          color: #eee !important;}

        /* Individual option hover */
        li[role="option"]:hover {background-color: #444 !important;
          color: #fff !important;}

    /* MULTISELECT */
        div[data-baseweb="select"] > div {color: black !important;}

        div[data-baseweb="select"] span {background-color: #d3d3d3 !important;
        color: black !important;}

     /* FILE UPLOADER */
        div[data-testid="stFileUploader"] > div {
        flex-wrap: wrap; justify-content: space-between;}

        div[data-testid="stFileUploader"] button {flex: 0 0 auto;
        background-color: #555555; color: white; height: 2.4em; font-size: 15px;
        padding: 1.2em; border-radius: 5px; border: none;margin: 4px;}

        div[data-testid="stFileUploader"] button div span {font-size: 30px !important;}

        div[data-testid="stFileUploader"] button:hover {background-color: #FF4B4B; color: white}

        div[data-testid="stFileUploader"] button[aria-selected="true"] {
            background-color: #9871b5; color: white; font-weight: bold;
            box-shadow: 0 0 10px #9871b5;}

        /* Uploaded file info */
        div[data-testid="stFileUploader"] ul {font-size: 14px !important;}

        /* x button size */
        div[data-testid="stFileUploader"] ul button {
        padding: 1px 5px !important; height: 22px !important;
        line-height: 1 !important; min-height: 0 !important;}

        /* x button icon */
        div[data-testid="stFileUploader"] ul button svg {width: 14px !important;
            height: 14px !important;}

    /* PURPLE HEADINGS — Dark Mode */
        .purple-heading {background-color: #281634; border-bottom: 4px solid #d8c3f0;
          border-radius: 5px; padding: 10px; margin-bottom: 8px;
          font-size: 1.1rem; font-weight: 600; color: #d8c3f0;}

    /* GRAY HEADINGS — Dark Mode */
        .gray-heading {background-color: #1e1e1e; border-bottom: 4px solid #999999;
          border-radius: 5px;   padding: 6px; margin-bottom: 8px; font-size: 1rem;
          font-weight: 600; color: #dddddd;}

    /* GRAY PREVIEW MESSAGE — Dark Mode */
        .gray-preview-message {background-color: #1c1c1c; padding: 0.7em;
          border-radius: 5px; color: #dddddd; border: 1px solid #444444; font-size: 0.92em;
          word-wrap: break-word;}

    /* BLUE PREVIEW MESSAGE - Dark Mode*/
            .blue-preview-message {background-color: #0b1c2d; padding:0.7em; border-radius:5px;
            color:#b3d9ff; border:1px solid #060e1a; font-size: 0.92em; word-wrap: break-word;}

    /* SUCCESS MESSAGE FLAG — Dark Mode */
        .success-message-flag {background-color: #1e2e24; padding: 1em;
          border-radius: 5px; color: #b2e3c7; word-wrap: break-word;}

        .success-message-flag b {color: #7fc89e;}

    /* SUCCESS MESSAGE — Dark Mode */
    .success-message {border-left: 4px solid #b2e3c7; padding: 0.4em 0.6em;
      color: #b2e3c7; font-size: 0.85em; font-family: "Source Sans Pro", sans-serif;
      margin: 0.5em 0; background-color: #1e2e24; border-radius: 4px;
      box-sizing: border-box; word-wrap: break-word;}

    .success-message b {color: #c6edd4; font-weight: 600;}

    /* WARNING MESSAGE — Dark Mode */
        .warning-message {border-left: 4px solid #e0c36d; padding: 0.4em 0.6em;
          color: #e0c36d; font-size: 0.85em; font-family: "Source Sans Pro", sans-serif;
          margin: 0.5em 0; background-color: #2f2a1e; border-radius: 4px;
          box-sizing: border-box; word-wrap: break-word;}

    .warning-message b {color: #c6edd4; font-weight: 600;}

    /* ERROR MESSAGE — Dark Mode */
        .error-message {border-left: 4px solid #e89ca0; padding: 0.4em 0.6em;
          color: #e89ca0; font-size: 0.85em; font-family: "Source Sans Pro", sans-serif;
          margin: 0.5em 0; background-color: #2d1e1f; border-radius: 4px;
          box-sizing: border-box; word-wrap: break-word;}

        .error-message b {color: #f2b6b9; font-weight: 600;}

    /* INFO MESSAGE GRAY — Dark Mode */
        .info-message-gray {border-left: 4px solid #999999; padding: 0.4em 0.6em;
          color: #cccccc; font-size: 0.85em;font-family: "Source Sans Pro", sans-serif;
          margin: 0.5em 0; background-color: #1e1e1e; border-radius: 4px;
          box-sizing: border-box; word-wrap: break-word;}

        .info-message-gray b {color: #eeeeee; font-weight: 600;}

    /* INFO MESSAGE BLUE — Dark Mode */
        .info-message-blue {border-left: 4px solid #6ea6c9;
          padding: 0.4em 0.6em; color: #b3d9ff; font-size: 0.85em;
          font-family: "Source Sans Pro", sans-serif; margin: 0.5em 0;
          background-color: #0b1c2d; border-radius: 4px;
          box-sizing: border-box; word-wrap: break-word;}

        .info-message-blue b {color: #dceeff; font-weight: 600;}

    /* SMALL HEADING FOR SUBSECTIONS */
    .small-subsection-heading {font-size: 13px; font-weight: 500;
        margin-top: 10px; margin-bottom: 6px; border-top: 0.5px solid #ccc;
        padding-bottom: 4px;}

    /* VERY SMALL INFO */
    .very-small-info {font-size: 10.5px;
        margin-top: -10px;}

    /* VERY SMALL INFO TOP*/
    .very-small-info-top {font-size: 10.5px;
        margin-bottom: -10px;}

    </style>"""
#______________________________________________________

#_______________________________________________________
# Colors for network display
# 0. s_node      1. p_edge          2. o_node
# 3. p_edge_label         4. background          5. legend font
def get_colors_for_network():

    colors_for_network_list = []

    if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
        colors_for_network_list.append("#ff7a7a")
        colors_for_network_list.append("#D3D3D3")
        colors_for_network_list.append("#7A4A8C")
        colors_for_network_list.append("#888888")
        colors_for_network_list.append("#f5f5f5")
        colors_for_network_list.append("#888888")

    else:
        colors_for_network_list.append("#7A4A8C")
        colors_for_network_list.append("#ff7a7a")
        colors_for_network_list.append("#D3D3D3")
        colors_for_network_list.append("#222222")
        colors_for_network_list.append("#222222")
        colors_for_network_list.append("#888888")

    return colors_for_network_list
#_________________________________________________

#_________________________________________________
# Colors for STATS dict
def get_colors_for_stats_dict():

    colors_for_stats_dict = {}

    if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
        colors_for_stats_dict["purple"] = "#7A4A8C"
        colors_for_stats_dict["salmon"] = "#ff7a7a"
        colors_for_stats_dict["blue"] = "#336699"
        colors_for_stats_dict["gray"] = "#D3D3D3"

    else:
        colors_for_stats_dict["purple"] = "#d8c3f0"
        colors_for_stats_dict["salmon"] = "#b34747"
        colors_for_stats_dict["blue"] = "#1f3f5f"
        colors_for_stats_dict["gray"] = "#696969"

    return colors_for_stats_dict
#_______________________________________________________

#______________________________________________________
# Function to get time to display success messages
def get_success_message_time():

    return 2
#______________________________________________________

#______________________________________________________
# Function to get panel layout
def get_panel_layout(narrow=False):

    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])

    if narrow:
        with col2:
            col2a, col2b = st.columns([1, 2])
    else:
        with col2:
            col2a, col2b = st.columns([0.5, 2])

    return col1, col2, col2a, col2b
#______________________________________________________

#______________________________________________________
# Function to get error message to indicate a g_mapping or ontology must be imported
# Only one option must be True
def get_missing_element_error_message(ontology=False, mapping=False, databases=False, hierarchical_files=False, different_page=False):

    if mapping:
        if not different_page:
            st.markdown(f"""<div class="error-message">
                ❌ You need to create or import a mapping from the
                <b>Select Mapping</b> panel.
            </div>""", unsafe_allow_html=True)

        else:
            st.markdown(f"""<div class="error-message">
                ❌ You need to create or import a mapping from the
                <b>🌍 Global Configuration</b> page <small>(<b>Select Mapping</b> panel).</small>
            </div>""", unsafe_allow_html=True)

    elif ontology:
        if not different_page:
            st.markdown(f"""<div class="error-message">
                ❌ You need to import at least one ontology from the <b>Import Ontology</b> panel.
            </div>""", unsafe_allow_html=True)

        else:
            st.markdown(f"""<div class="error-message">
                ❌ You need to import at least one ontology from the <b>🧩 Ontologies</b> page
                <small>(<b>Import Ontology</b> panel).</small>
            </div>""", unsafe_allow_html=True)

    elif databases:
        st.markdown(f"""<div class="error-message">
            ❌ <b>No connections to databases have been configured.</b> <small>You can add them in the
            <b>Manage Connections</b> panel.</small>
        </div>""", unsafe_allow_html=True)

    elif hierarchical_files:
        st.markdown(f"""<div class="error-message">
            ❌ <b>No hierarchical files have been loaded </b>
            <small><i>({format_list_for_display(get_supported_formats(hierarchical_files=True), disjunctive=True)})</i>.
            You can add them in the
            <b>Manage Files</b> panel.</small>
        </div>""", unsafe_allow_html=True)
#______________________________________________________

#______________________________________________________
# Function to get the mapping+ontology corner status message in the different panels
def get_corner_status_message(mapping_info=False, ontology_info=False):

    inner_html = ""

    # Mapping message
    if mapping_info:
        if st.session_state["g_label"]:
            inner_html += f"""🗺️ Mapping <b style="color:#F63366;">{st.session_state["g_label"]}</b><br>"""
        else:
            inner_html += f"""🚫 <b>No mapping</b> is loaded.<br>"""

    # Add spacing if needed
    if ontology_info and inner_html:
        inner_html += "<br>"

    # Ontology message
    if ontology_info:
        if st.session_state["g_ontology"]:
            if len(st.session_state["g_ontology_components_dict"]) > 1:
                ontology_items = ''.join([f"""<div style="margin-left:15px;"><small>
                            <b>· {ont}</b> <b style="color:#F63366;">[{st.session_state["g_ontology_components_tag_dict"][ont]}]</b>
                        </small></div>""" for ont in st.session_state["g_ontology_components_dict"]])
                inner_html += f"""🧩 Ontologies:<br>
                    {ontology_items}"""
            else:
                ont = next(iter(st.session_state["g_ontology_components_dict"]))
                inner_html += f"""🧩 Ontology: <small><b>{ont}</b>
                        <b style="color:#F63366;">[{st.session_state["g_ontology_components_tag_dict"][ont]}]</b></small>"""
        else:
            inner_html += f"""🚫 <b>No ontology</b> has been imported."""

    # Render
    if inner_html:
        st.html(f"""<div class="gray-preview-message">
                {inner_html}
            </div>""")
#______________________________________________________

#______________________________________________________
# Function to format a list
def format_list_for_display(xlist, disjunctive=False):

    if not xlist:
        formatted_list = ""
    elif len(xlist) == 1:
        formatted_list = xlist[0]
    else:
        particle = " and " if not disjunctive else " and/or "
        formatted_list = ", ".join(xlist[:-1]) + particle + xlist[-1]

    return formatted_list
#______________________________________________________

#______________________________________________________
# Funtion to get label of a node   #RFTAG
def get_node_label(node, iri_prefix=True, short_BNode=False):

    # BNode
    if isinstance(node, BNode):
        label = "_:" + str(node)[:7] + "..." if short_BNode else str(node)

    # URIRef or Other (check is valid uri and split, else node)
    elif node:
        if is_valid_iri(node, delimiter_ending=False):
            try:
                label = st.session_state["g_mapping"].namespace_manager.qname(URIRef(node))
            except ValueError:
                label = str(node)
        else:
            label = str(node)

    elif node:
        is_valid_iri_flag = is_valid_iri(node, delimiter_ending=False)


    # Empty node
    else:
        label = ""

    return label
#______________________________________________________


#______________________________________________________
# Funtion to format number
def format_number_for_display(number):

    if number >= 10*10**6:    # >10 M  (ex 21M)
        number_for_display = f"{int(number/ 10**6)}M"

    elif number >= 10**6:    # 1-10 M  (ex 3.4M)
        number_for_display = f"{round(number / 10**6, 1)}M"

    elif number >= 10*10**3:    # 10k-1M  (ex 23k)
        number_for_display = f"{int(number / 1000)}k"

    elif number >= 10**3:    # 1k-10k  (ex 2.9k)
        number_for_display = f"{round(number / 1000, 1)}k"

    elif number >= 10:    # 10-1k  (ex 545)
        number_for_display = f"{int(number)}"

    elif number >= 1:    # 1-10  (ex 7.4)
        number_for_display = f"{round(number, 1)}"

    elif number >= 0.1:    # 0.1-1  (ex 0.32)
        number_for_display = f"{round(number, 2)}"

    elif number == 0:    # 0
        number_for_display = 0

    elif number < 0.001:    # <0.001
        number_for_display = "< 0.001"

    elif number < 0.01:    # 0.001-0.01
        number_for_display = "< 0.01"

    else:    # 0.01-0.1
        number_for_display = "< 0.1"

    return number_for_display
#______________________________________________________

#______________________________________________________
# Function to get the max_length for the display options
# 0. Complete dataframes      1. Last added dataframes
# 2. Dataframe display (rows)    3. Dataframe display (columns)
# 4. List of multiselect items for hard display     # 5 Long lists for soft display
# 6. Label in network visualisation (characters)
# 7. Suggested mapping label (characters)    8. URL for display (characters)
# 9. Max characters when displaying ontology/mapping serialisation (ttl or nt)
# 10. Query/path text for display    RFTAG check everything is used
# 11. Max characters in a rule before using small fint size
def get_max_length_for_display():

    return [50, 10, 100, 20, 8, 10, 20, 15, 40, 100000, 10, 40]
#_______________________________________________________

#______________________________________________________
# Function to display limited dataframed in right column
# info namespaces / db_connections / saved_views / file_ds / triplesmaps
def display_right_column_df(info, text, complete=True, display=True):

    max_length = get_max_length_for_display()[1]

    # Create the dataframe
    if info == "namespaces":
        session_state_dict = st.session_state["last_added_ns_list"]
        mapping_ns_dict = get_g_ns_dict(st.session_state["g_mapping"])
        rows = [{"Prefix": prefix, "Namespace": mapping_ns_dict.get(prefix, "")}
            for prefix in reversed(list(st.session_state["last_added_ns_list"]))]

    elif info == "custom_terms":
        session_state_dict = st.session_state["custom_terms_dict"]
        rows = [{"Term": get_node_label(term_iri), "Type": st.session_state["custom_terms_dict"][term_iri]}
            for term_iri in reversed(list(st.session_state["custom_terms_dict"]))]

    elif info == "db_connections":
        session_state_dict = st.session_state["db_connections_dict"]
        rows = [{"Label": label, "Engine": st.session_state["db_connections_dict"][label][0],
                "Database": st.session_state["db_connections_dict"][label][3],
                "Status": st.session_state["db_connection_status_dict"][label][0]}
                for label in reversed(list(st.session_state["db_connections_dict"].keys()))]

    elif info == "saved_views":
        session_state_dict = st.session_state["saved_views_dict"]
        rows = []
        for label in reversed(list(st.session_state["saved_views_dict"].keys())):
            connection = st.session_state["saved_views_dict"][label][0]
            database =  st.session_state["db_connections_dict"][connection][3]

            query_or_collection = st.session_state["saved_views_dict"][label][1]
            max_length = get_max_length_for_display()[10]
            query_or_collection = query_or_collection[:max_length] + "..." if len(query_or_collection) > max_length else query_or_collection

            rows.append({"Label": label, "Source": connection,
                    "Database": database, "Query/Collection": query_or_collection})

    elif info == "file_ds":
        session_state_dict = st.session_state["ds_files_dict"]
        rows = []
        ds_files = list(st.session_state["ds_files_dict"].items())
        ds_files.reverse()

        for filename, file_obj in ds_files:
            base_name = filename.split(".")[0]
            file_format = filename.split(".")[-1]

            if hasattr(file_obj, "size"):               # Streamlit UploadedFile
                file_size_kb = file_obj.size / 1024
            elif hasattr(file_obj, "fileno"):                 # File object from open(path, "rb")
                file_size_kb = os.fstat(file_obj.fileno()).st_size / 1024
            else:
                file_size_kb = None  # Unknown format

            if not file_size_kb:
                file_size = None
            elif file_size_kb < 1:
                file_size = f"""{int(file_size_kb*1024)} bytes"""
            elif file_size_kb < 1024:
                file_size = f"""{int(file_size_kb)} kB"""
            else:
                file_size = f"""{int(file_size_kb/1024)} MB"""

            row = {"Filename": base_name, "Format": file_format,
                "Size": file_size if file_size_kb is not None else "N/A"}
            rows.append(row)

    elif info == "saved_paths":
        session_state_dict = st.session_state["saved_paths_dict"]
        rows = []
        for label in reversed(list(st.session_state["saved_paths_dict"].keys())):
            filename = st.session_state["saved_paths_dict"][label][0]
            path = st.session_state["saved_paths_dict"][label][1]
            max_length = get_max_length_for_display()[10]
            path = path[:max_length] + "..." if len(path) > max_length else path

            rows.append({"Label": label, "Data file": filename,
                    "Path": path})

    elif info == "triplesmaps":
        session_state_dict = st.session_state["last_added_tm_list"]
        rows = [{"TriplesMap": tm, "Data Source": utils.get_tm_info_for_display(tm)[1],
            "Table/View": utils.get_tm_info_for_display(tm)[2],
            "Logical Source": utils.get_tm_info_for_display(tm)[0]} for tm in st.session_state["last_added_tm_list"]]

    elif info == "subject_maps":
        session_state_dict = st.session_state["last_added_sm_list"]
        sm_dict = get_sm_dict()
        rows = [{"Triplesmap": triples_map, "Rule": sm_dict[subject_map][2],
            "Type": sm_dict[subject_map][1], "Subject Map": sm_dict[subject_map][0],}
            for subject_map, triples_map in st.session_state["last_added_sm_list"]
            if subject_map in sm_dict]

    elif info == "predicate-object_maps":
        session_state_dict =  st.session_state["last_added_pom_list"]
        pom_dict = get_pom_dict()
        rows = [{"Rule": pom_dict[pom_iri][5], "Type": pom_dict[pom_iri][4],
            "Predicate(s)": utils.format_list_for_display(pom_dict[pom_iri][1]),
            "TriplesMap": utils.get_node_label(tm_iri)}
            for pom_iri, tm_iri in st.session_state["last_added_pom_list"]
            if pom_iri in pom_dict]

    else:
        rows = []

    df = pd.DataFrame(rows)

    # Clean the dataframe (remove empty columns, including placeholder "---")
    placeholder = "---"
    cols_to_drop = []
    for col in df.columns:
        if df[col].isna().all():           # check if all values are NaN
            cols_to_drop.append(col)
        elif (df[col] == placeholder).all():   # check if all values equal the placeholder string
            cols_to_drop.append(col)
    df = df.drop(columns=cols_to_drop)

    # Display the dataframe
    if display:
        if session_state_dict:
            limited_df = df.head(max_length)

            if len(session_state_dict) < max_length:
                st.markdown(f"""<div style='text-align: right; font-size: 14px; color: grey;'>
                        🔎 {text}
                    </div>""", unsafe_allow_html=True)
                st.markdown("<div style='margin-top:0px;'></div>",
                    unsafe_allow_html=True)
            else:
                st.markdown(f"""<div style='text-align: right; font-size: 14px; color: grey;'>
                        🔎 {text}
                    </div>""", unsafe_allow_html=True)
                st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        (complete list below)
                    </div>""", unsafe_allow_html=True)

            st.dataframe(limited_df, hide_index=True)

        # Option to display complete dataframe if it was shortened   HERE LIMIT MAX LENGTH?
        if complete and session_state_dict and len(session_state_dict) > max_length:
            st.write("")
            with st.expander(f"🔎 Show all {text}"):
                st.dataframe(df, hide_index=True)

    return df
#______________________________________________________


# SUPPORTED FORMATS ============================================================
#_______________________________________________________
# List of allowed mapping file formats
def get_supported_formats(mapping=False, ontology=False, databases=False, data_files=False, hierarchical_files=False):

    if mapping:
        allowed_formats = {"turtle": ".ttl",
            "ntriples": ".nt"}

    elif ontology:
        allowed_formats = {"owl": ".owl", "turtle": ".ttl", "longturtle": ".ttl", "n3": ".n3",
        "ntriples": ".nt", "nquads": "nq", "trig": ".trig", "jsonld": ".jsonld",
        "xml": ".xml", "pretty-xml": ".xml", "trix": ".trix"}

    elif databases:
        allowed_formats = ["PostgreSQL", "MySQL", "SQL Server", "MariaDB", "Oracle", "MongoDB"]

    if data_files:
        allowed_formats = [".csv", ".tsv", ".xls", ".xlsx", ".parquet", ".feather",
            ".orc", ".ods", ".json", ".xml"]

    if hierarchical_files:
        allowed_formats = ["json", "xml"]

    return allowed_formats
#_______________________________________________________


# INITIALISE PAGES =============================================================
#________________________________________________________
# Function to initialise all session state variables
def init_session_state_variables():

    if "session_initialised_ok_flag" not in st.session_state:

        st.session_state["session_initialised_ok_flag"] = True

        # 🌍 GLOBAL CONFIGURATION_________________
        # TAB1
        st.session_state["g_mapping"] = Graph()
        st.session_state["g_label"] = ""
        st.session_state["g_label_temp_new"] = ""
        st.session_state["key_mapping_uploader"] = None
        st.session_state["g_label_temp_existing"] = ""
        st.session_state["g_mapping_source_cache"] = ["",""]
        st.session_state["original_g_size_cache"] = 0
        st.session_state["original_g_mapping_ns_dict"] = {}
        st.session_state["candidate_g_mapping"] = Graph()
        st.session_state["new_g_mapping_created_ok_flag"] = False
        st.session_state["existing_g_mapping_loaded_ok_flag"] = False
        st.session_state["session_retrieved_ok_flag"] = False
        st.session_state["cached_mapping_retrieved_ok_flag"] = False
        st.session_state["g_label_changed_ok_flag"] = False
        st.session_state["everything_reseted_ok_flag"] = False
        # TAB2
        st.session_state["last_added_ns_list"] = []
        st.session_state["base_ns"] = get_default_base_ns()
        st.session_state["ns_bound_ok_flag"] = False
        st.session_state["ns_unbound_ok_flag"] = False
        st.session_state["base_ns_changed_ok_flag"] = False
        st.session_state["ontology_downloaded_ok_flag"] = False
        # TAB3
        st.session_state["progress_saved_ok_flag"] = False
        st.session_state["mapping_downloaded_ok_flag"] = False
        st.session_state["session_saved_ok_flag"] = False
        st.session_state["session_removed_ok_flag"] = False

        # 🧩 ONTOLOGIES_______________________________________
        # TAB1
        st.session_state["g_ontology"] = Graph()
        st.session_state["g_ontology_label"] = ""
        st.session_state["ontology_link"] = ""
        st.session_state["key_ontology_uploader"] = None
        st.session_state["ontology_file"] = None
        st.session_state["g_ontology_from_file_candidate"] = Graph()
        st.session_state["g_ontology_from_link_candidate"] = Graph()
        st.session_state["g_ontology_components_dict"] = {}
        st.session_state["g_ontology_components_tag_dict"] = {}
        st.session_state["g_ontology_loaded_ok_flag"] = False
        st.session_state["g_ontology_reduced_ok_flag"] = False
        # TAB4
        st.session_state["custom_terms_dict"] = {}
        st.session_state["custom_term_saved_ok_flag"] = False
        st.session_state["custom_terms_removed_ok_flag"] = False

        # 📊 SQL DATABASES____________________________________
        # TAB1
        st.session_state["db_connections_dict"] = {}
        st.session_state["db_connection_status_dict"] = {}
        st.session_state["db_connection_saved_ok_flag"] = False
        st.session_state["db_connection_removed_ok_flag"] = False
        st.session_state["db_connection_status_updated_ok_flag"] = False
        #TAB3
        st.session_state["saved_views_dict"] = {}
        st.session_state["view_saved_ok_flag"] = False
        st.session_state["view_removed_ok_flag"] = False

        # 🛢️ DATA FILES
        # TAB1
        st.session_state["key_ds_uploader"] = str(uuid.uuid4())
        st.session_state["ds_files_dict"] = {}
        st.session_state["large_ds_files_dict"] = {}
        st.session_state["ds_file_saved_ok_flag"] = False
        st.session_state["ds_file_removed_ok_flag"] = False
        # TAB3
        st.session_state["path_saved_ok_flag"] = False
        st.session_state["saved_paths_dict"] = {}
        st.session_state["path_removed_ok_flag"] = False

        # 🏗️ BUILD MAPPING
        # TAB1
        st.session_state["key_ds_uploader"] = str(uuid.uuid4())
        st.session_state["last_added_tm_list"] = []
        st.session_state["tm_label"] = ""
        st.session_state["tm_saved_ok_flag"] = False
        # TAB2
        st.session_state["key_ds_uploader_for_sm"] = str(uuid.uuid4())
        st.session_state["last_added_sm_list"] = []
        st.session_state["tm_label_for_sm"] = False
        st.session_state["sm_template_list"] = []
        st.session_state["sm_iri"] = None
        st.session_state["sm_template_is_iri_flag"] = False
        st.session_state["multiple_subject_class_list"] = []
        st.session_state["sm_template_variable_part_flag"] = False
        st.session_state["sm_saved_ok_flag"] = False
        # TAB3
        st.session_state["key_ds_uploader_for_pom"] = str(uuid.uuid4())
        st.session_state["om_template_is_iri_flag"] = False
        st.session_state["om_template_list"] = []
        st.session_state["last_added_pom_list"] = []
        st.session_state["pom_saved_ok_flag"] = False
        st.session_state["om_template_variable_part_flag"] = False
        # TAB4
        st.session_state["tm_removed_ok_flag"] = False
        st.session_state["sm_unassigned_ok_flag"] = False
        st.session_state["g_mapping_cleaned_ok_flag"]  = False
        st.session_state["pom_removed_ok_flag"] = False

        # 🔮 MATERIALISE GRAPH
        # TAB1
        st.session_state["mkgc_config"] = configparser.ConfigParser()
        st.session_state["autoconfig_active_flag"] = True
        st.session_state["autoconfig_generated_ok_flag"] = False
        st.session_state["config_file_reset_ok"] = False
        st.session_state["mkgc_g_mappings_dict"] = {}
        st.session_state["key_mapping_uploader"] = str(uuid.uuid4())
        st.session_state["manual_config_enabled_ok_flag"] = False
        st.session_state["ds_for_mkgcgc_saved_ok_flag"] = False
        st.session_state["ds_for_mkgcgc_removed_ok_flag"] = False
        st.session_state["configuration_for_mkgcgc_saved_ok_flag"] = False
        st.session_state["configuration_for_mkgcgc_removed_ok_flag"] = False
        st.session_state["additional_mapping_added_ok_flag"] = False
        st.session_state["additional_mapping_removed_ok_flag"] = False
        st.session_state["materialised_g_mapping_file"] = None
        st.session_state["materialised_g_mapping"] = Graph()
        st.session_state["graph_materialised_ok_flag"] = False
        st.session_state["error_during_materialisation_flag"] = False
        # TAB2
        st.session_state["g_mapping_cleaned_ok_flag"]

#______________________________________________________

#______________________________________________________
# Function to initialise page
def init_page():

    # automatic detection of dark mode
    if "dark_mode_flag" not in st.session_state or st.session_state["dark_mode_flag"] is None:
        st.session_state["dark_mode_flag"] = streamlit_js_eval(js_expressions="window.matchMedia('(prefers-color-scheme: dark)').matches",
            key="dark_mode")

    # sidebar logo
    dark_mode = False if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"] else True
    utils.render_sidebar_logo(dark_mode=dark_mode)

    # import style
    style_container = st.empty()
    if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
        style_container.markdown(import_st_aesthetics(), unsafe_allow_html=True)
    else:
        style_container.markdown(import_st_aesthetics_dark_mode(), unsafe_allow_html=True)

    # initialise session state variables
    init_session_state_variables()
#______________________________________________________


# GLOBAL FUNCTIONS==============================================================
#______________________________________________________
# Function to check whether a label is valid
def is_valid_label(label, hard=False, display_option=True, blank_space=False):

    valid_letters = ["a","b","c","d","e","f","g","h","i","j","k","l","m",
        "n","o","p","q","r","s","t","u","v","w","x","y","z",
        "A","B","C","D","E","F","G","H","I","J","K","L","M",
        "N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]

    valid_digits = ["0","1","2","3","4","5","6","7","8","9","_","-"]

    # disallow empty label
    if not label:
        return False

    # disallow spaces
    if re.search(r"[ \t\n\r]", label):    # disallow spaces
        if display_option:
            if blank_space:
                st.write("")
            st.markdown(f"""<div class="error-message">
                ❌ <b> Invalid label. </b>
                <small>Please make sure it does not contain any spaces.</small>
            </div>""", unsafe_allow_html=True)
        return False

    # disallow unescaped characters
    if not hard and re.search(r"[<>\"{}|\\^`]", label):
        if display_option:
            if blank_space:
                st.write("")
            st.markdown(f"""<div class="error-message">
                ❌ <b> Invalid label. </b>
                <small>Please make sure it does not contain any invalid characters (&lt;&gt;"{{}}|\\^`).</small>
            </div>""", unsafe_allow_html=True)
        return False

    # allow only safe characters if hard
    if hard:
        for letter in label:
            if letter not in valid_letters and letter not in valid_digits:
                if display_option:
                    if blank_space:
                        st.write("")
                    st.markdown(f"""<div class="error-message">
                        ❌ <b> Invalid label. </b>
                        <small>Please make sure it contains only safe characters (a-z, A-Z, 0-9, -, _).</small>
                    </div>""", unsafe_allow_html=True)
                return False

    # disallow trailing puntuation if hard
    if hard and label.endswith("_") or label.endswith("-"):
        if display_option:
            if blank_space:
                st.write("")
            st.markdown(f"""<div class="error-message">
                ❌ <b> Invalid label. </b>
                <small>Please make sure it does not end with puntuation.</small>
            </div>""", unsafe_allow_html=True)
        return False

    # warning if long
    if len(label) > 20 and display_option:
        if blank_space:
            st.write("")
        st.markdown(f"""<div class="warning-message">
            ⚠️ A <b>shorter label</b> is recommended.
        </div>""", unsafe_allow_html=True)

    return True
#_______________________________________________________

#_____________________________________________________
# Funtion to get dictionary {prefix: namespace} bound in a graph g
def get_g_ns_dict(g):

    ns_dict = dict(g.namespace_manager.namespaces())

    return ns_dict
#_____________________________________________________

#__________________________________________________________
# Function to unbind namespaces from g mapping
# Namespaces cannot be removed by rdflib, so the mapping is rebuilt completely
# Duplicated prefixes will be renamed, duplicated namespaces will be ignored
def unbind_namespaces(ns_to_unbind_list):

    # build new graph as copy of old graph
    if ns_to_unbind_list:
        old_graph = st.session_state["g_mapping"]
        ns_to_remove = set(ns_to_unbind_list)
        new_graph = Graph()   # create a new graph and copy triples
        for triple in old_graph:
            new_graph.add(triple)

        # rebind the namespaces without the deleted ones
        for prefix, ns in old_graph.namespace_manager.namespaces():
            if prefix not in ns_to_remove:
                new_graph.namespace_manager.bind(prefix, ns, replace=True)

        # replace the old graph with the new one
        st.session_state["g_mapping"] = new_graph

        # update last added list
        for prefix in ns_to_unbind_list:
            if prefix in st.session_state["last_added_ns_list"]:
                st.session_state["last_added_ns_list"].remove(prefix)
#_________________________________________________________

#_________________________________________________________
# Function to bind namespaces to g mapping
# Duplicated prefixes will be renamed
# Duplicated namespaces will be overwritten (overwrite=True) or ignored (overwrite=False)
def bind_namespace(prefix, namespace, overwrite=True):

    mapping_ns_dict = get_g_ns_dict(st.session_state["g_mapping"])

    # for overwrite option, if namespace already bound to a different prefix, unbind it
    if overwrite and URIRef(namespace) in mapping_ns_dict.values():
        old_prefix_list = [k for k, v in mapping_ns_dict.items() if v == URIRef(namespace)]
        for old_prefix in old_prefix_list:
            if old_prefix in st.session_state["last_added_ns_list"]:
                st.session_state["last_added_ns_list"].remove(old_prefix)
        unbind_namespaces(old_prefix_list)

    # for overwrite option, or if namespace not in mapping
    if overwrite or not namespace in mapping_ns_dict.values():

        # bind the new namespace
        st.session_state["g_mapping"].bind(prefix, namespace)

        # find actual prefix (it may have been auto-renamed)
        actual_prefix = None
        for pr, ns in st.session_state["g_mapping"].namespace_manager.namespaces():
            if str(ns) == str(namespace):
                actual_prefix = pr
                break
        if actual_prefix:
            st.session_state["last_added_ns_list"].insert(0, actual_prefix)
#_________________________________________________________

#_________________________________________________________
#Function to check whether an IRI is valid
def is_valid_iri(iri, delimiter_ending=True):

    valid_iri_schemes = ("http://", "https://", "ftp://", "mailto:",
        "urn:", "tag:", "doi:", "data:")

    iri = str(iri) if isinstance(iri, URIRef) else iri

    # must start with valid scheme
    if not iri.startswith(valid_iri_schemes):
        return False

    try:
        parsed = urlparse(iri)
    except:
        return False
    schemes_with_netloc = {"http", "https", "ftp"}
    if parsed.scheme in schemes_with_netloc and not parsed.netloc:
        return False

    # disallow spaces or unescaped characters
    if re.search(r"[ \t\n\r<>\"{}|\\^`]", iri):
        return False

    # enforce ASCII only
    if not all(ord(c) < 128 for c in iri):
        return False

    # must end with a recognized delimiter (can be switched off)
    if delimiter_ending and not iri[-1] in ("/", "#", ":"):
        return False

    return True
#_________________________________________________________



# PAGE: 🌍 GLOBAL CONFIGURATION ================================================
# PANEL: SELECT MAPPING---------------------------------------------------------
#_______________________________________________________
# Function to format the suggested label for an imported mapping
def format_suggested_mapping_label(label):

    max_length = get_max_length_for_display()[7]

    label = label.replace(' ', '_')
    label = re.sub(r'[<>"{}|\\^`]', '', label)
    label = re.sub(r'[.-]+$', '', label)
    label = re.sub(r'[^A-Za-z0-9_]', '', label)
    label = label[:max_length] if len(label) > max_length else label

    return label
#_____________________________________________________

#_______________________________________________________
# Function to import mapping from link
def load_mapping_from_link(url, display=True):

    g = Graph()

    try:
        g.parse(url, format="turtle")
        return g

    except:
        if display:
            st.markdown(f"""<div class="error-message">
                ❌ Failed to parse <b>mapping</b>.
                <small>Please check your URL and/or your mapping.</small>
            </div>""", unsafe_allow_html=True)
        return None
#_____________________________________________________

#_______________________________________________________
# Function to import mapping from file (f is a file object)
# This should work for all mapping formats in get_supported_formats
def load_mapping_from_file(f):

    ext = os.path.splitext(f.name)[1].lower()  #file extension

    if ext in [".ttl", ".rdf", ".xml", ".nt", ".n3", ".trig", ".trix"]:
        rdf_format_dict = {".ttl": "turtle", ".rdf": "xml", ".xml": "xml",
            ".nt": "nt", ".n3": "n3", ".trig": "trig", ".trix": "trix"}
        g = Graph()
        content = f.read().decode("utf-8")
        try:
            g.parse(data=content, format=rdf_format_dict[ext])
            prefixes = re.findall(r"@prefix\s+(\w+):\s+<([^>]+)>", content)
            for prefix, uri in prefixes:
                ns = Namespace(uri)
                g.bind(prefix, ns)
            return g
        except:
            st.markdown(f"""<div class="error-message">
                ❌ Failed to parse <b>mapping</b>.
                <small> Please check your mapping.</small>
            </div>""", unsafe_allow_html=True)
            return False

    else:   # error message (should not happen)
        st.markdown(f"""<div class="error-message">
            ❌ Unsupported file extension <b>{ext}</b>.
        </div>""", unsafe_allow_html=True)
        return False
#_____________________________________________________

#_____________________________________________________
# Function to get the number of TriplesMaps in a mapping
def get_number_of_tm(g):

    triplesmaps = [s for s in g.subjects(predicate=RML.logicalSource, object=None)]

    return len(triplesmaps)
#_________________________________________________________

#_____________________________________________________
# Function to get the base namespace of an imported mapping
def get_g_mapping_base_ns():

    prefix = ""
    base_ns = ""

    # Look for base ns of the mapping
    for s, p, o in st.session_state["g_mapping"]:
        if isinstance(s, URIRef):
            if p in [RML.logicalSource, RML.subjectMap, RML.predicateObjectMap, RML.objectMap]:
                base_ns = split_uri(s)[0]
                if is_valid_iri(base_ns):
                    break

    # Look for prefix of the base namespace (else assign "base")
    prefix = "base"
    for pr, ns in st.session_state["g_mapping"].namespaces():
        if str(base_ns) == str(ns):
            prefix = pr
            break

    if is_valid_iri(base_ns):
        return [prefix, Namespace(base_ns)]
    else:
        return get_default_base_ns()
#_________________________________________________________

#_________________________________________________________
# Function to change the base namespace in a mapping
# Changes the ns of all tm, sm, pom and om
def change_g_mapping_base_ns(prefix, namespace):

    base_ns = [prefix, namespace]
    updated_nodes_dict = {}
    updated_g = Graph()
    updated_g.bind(base_ns[0], base_ns[1])

    # bind the namespaces of the mapping into the updated version
    for prefix, namespace in st.session_state["g_mapping"].namespaces():
        updated_g.bind(prefix, namespace)

    # look for the tm, sm, pom and om and create dictionary with updated iris
    for s, p, o in st.session_state["g_mapping"]:
        if isinstance(s, URIRef):
            if p in [RML.logicalSource, RML.subjectMap, RML.predicateObjectMap, RML.objectMap]:
                updated_nodes_dict[s] = URIRef(base_ns[1] + split_uri(s)[1])

    # for all triples, change if necessary and add to updated graph
    for s, p, o in st.session_state["g_mapping"]:
        s = updated_nodes_dict[s] if s in updated_nodes_dict else s
        o = updated_nodes_dict[o] if o in updated_nodes_dict else o
        updated_g.add((s, p, o))

    # consolidate updated graph
    st.session_state["g_mapping"] = updated_g
#_________________________________________________________

#_______________________________________________________
# Function to empty all lists that store last added stuff
def empty_last_added_lists():
    st.session_state["last_added_ns_list"] = []
    st.session_state["last_added_tm_list"] = []
    st.session_state["last_added_sm_list"] = []
    st.session_state["last_added_pom_list"] = []
#_____________________________________________________

#_____________________________________________________
# Function to completely reset cache
# Mapping, data sources, ontologies and last added lists
def full_reset():

    # reset mapping
    st.session_state["g_mapping"] = Graph()
    st.session_state["g_label"] = ""

    # reset data sources
    st.session_state["db_connections_dict"] = {}
    st.session_state["db_connection_status_dict"] = {}
    st.session_state["saved_views_dict"] = {}
    st.session_state["ds_files_dict"] = {}

    # reset ontology
    st.session_state["g_ontology_components_dict"] = {}
    st.session_state["g_ontology_components_tag_dict"] = {}
    st.session_state["g_ontology"] = Graph()

    # reset last added lists
    empty_last_added_lists()
#_____________________________________________________

# PANEL: CONFIGURE NAMESPACES --------------------------------------------------
#_____________________________________________________
# Funtion to get dictionary {prefix: namespace} of namespaces used in a mapping g
def get_used_g_ns_dict(g):

    used_namespaces_set = set()
    used_namespaces_dict = {}
    ns_dict = get_g_ns_dict(g)

    # add the namespaces used in all nodes of all triples
    for s, p, o in g:
        for term in [s, p, o]:
            if isinstance(term, URIRef):
                try:
                    ns, _ = split_uri(term)
                    used_namespaces_set.add(ns)
                except ValueError:
                    pass

    # add prefix:ns to dictionary
    for k, v in ns_dict.items():
        for namespace in used_namespaces_set:
            if str(v) == namespace:
                used_namespaces_dict[k] = v

    return used_namespaces_dict
#_________________________________________________________

#_________________________________________________________
#Function to check whether a prefix is valid
def is_valid_prefix(prefix):

    valid_letters = ["a","b","c","d","e","f","g","h","i","j","k","l","m",
        "n","o","p","q","r","s","t","u","v","w","x","y","z",
        "A","B","C","D","E","F","G","H","I","J","K","L","M",
        "N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]

    valid_digits = ["0","1","2","3","4","5","6","7","8","9","_"]

    # disallow empty prefix
    if not prefix:
        return False

    # disallow spaces
    if re.search(r"[ \t\n\r]", prefix):
        st.markdown(f"""<div class="error-message">
            ❌ <b> Invalid prefix.</b>
            <small>Please make sure it does not contain any spaces.</small>
        </div>""", unsafe_allow_html=True)
        return False

    # safe characters only
    for letter in prefix:
        if letter not in valid_letters and letter not in valid_digits:
            st.markdown(f"""<div class="error-message">
                ❌ <b> Invalid prefix. </b>
                <small>Please make sure it only contains safe characters (a-z, A-Z, 0-9, _).</small>
            </div>""", unsafe_allow_html=True)
            return False

    # start with a letter
    if prefix[0] not in valid_letters:
        st.markdown(f"""<div class="error-message">
            ❌ <b> Invalid prefix. </b>
            <small>Please start with a letter.</small>
        </div>""", unsafe_allow_html=True)
        return False

    # warning if long or uppercase used
    inner_html = ""
    if len(prefix) > 10:
        inner_html += f"""A <b>shorter prefix</b> is recommended. """
    if prefix.lower() != prefix:
        inner_html += f"""The use of <b>uppercase</b> letters is discouraged."""
    if inner_html:
        st.markdown(f"""<div class="warning-message">
            ⚠️ {inner_html}
        </div>""", unsafe_allow_html=True)

    return True
#_________________________________________________________

#_________________________________________________________
# Function to check whether any prefixes of a ns dictionary are not bound in g mapping
def are_there_unbound_ns(ns_dict):

    mapping_ns_dict = get_g_ns_dict(st.session_state["g_mapping"])
    there_are_ns_unbound_flag = False

    for pr, ns in ns_dict.items():
        if not ns in mapping_ns_dict.values():
            there_are_ns_unbound_flag = True
            continue

    return there_are_ns_unbound_flag
#_________________________________________________

#_________________________________________________
# Function to get previsualisation of Prefix -> Namespace
def get_ns_previsualisation_message(ns_to_bind_list, ns_dict):

    inner_html = ""
    max_length = get_max_length_for_display()[4]

    for prefix in ns_to_bind_list[:max_length]:
        inner_html += f"""<div style="margin-bottom:6px;">
            <b>🔗 {prefix}</b> → {ns_dict[prefix]}
        </div>"""

    if len(ns_to_bind_list) > max_length:
        inner_html += f"""<div style="margin-bottom:6px;">
            🔗 ... <b>(+{len(ns_to_bind_list[max_length:])})</b>
        </div>"""

    st.markdown(f"""<div class="info-message-gray">
            <small>{inner_html}</small>
        </div>""", unsafe_allow_html=True)
#_________________________________________________

#_________________________________________________
# Function to get warning messages when binding namespaces
def get_ns_warning_message(ns_to_bind_list):

    mapping_ns_dict = get_g_ns_dict(st.session_state["g_mapping"])
    already_used_prefix_list = []
    for pr in ns_to_bind_list:
        if pr in mapping_ns_dict:
            already_used_prefix_list.append(pr)

    if len(already_used_prefix_list) == 1:
        st.markdown(f"""<div class="warning-message">
                    ⚠️ Prefix <b>{utils.format_list_for_display(already_used_prefix_list)}</b> is already in use<small>
                    and will be auto-renamed with a numeric suffix.</small>
            </div>""", unsafe_allow_html=True)

    elif already_used_prefix_list:
        st.markdown(f"""<div class="warning-message">
                    ⚠️ Prefixes <b>{utils.format_list_for_display(already_used_prefix_list)}</b> are already in use
                    <small>and will be auto-renamed with a numeric suffix.</small>
            </div>""", unsafe_allow_html=True)
#_________________________________________________

# PANEL: SAVE MAPPING-----------------------------------------------------------
#_________________________________________________
#Funtion to create the list that stores the state of the project
def save_session_state():

    # list to save session
    project_state_list = []
    project_state_list.append(st.session_state["g_label"])
    project_state_list.append(st.session_state["g_mapping"])
    project_state_list.append(st.session_state["g_ontology"])
    project_state_list.append(st.session_state["g_ontology_components_dict"])
    project_state_list.append(st.session_state["g_ontology_components_tag_dict"])
    project_state_list.append(st.session_state["base_ns"])
    project_state_list.append(st.session_state["db_connections_dict"])
    project_state_list.append(st.session_state["db_connection_status_dict"])
    project_state_list.append(st.session_state["ds_files_dict"])
    project_state_list.append(st.session_state["saved_views_dict"])
    project_state_list.append(st.session_state["g_mapping_source_cache"])
    project_state_list.append(st.session_state["original_g_size_cache"])
    project_state_list.append(st.session_state["original_g_mapping_ns_dict"])
    project_state_list.append(st.session_state["custom_terms_dict"])

    return project_state_list
#______________________________________________________

#_________________________________________________
# Funtion to retrieve the session state
def retrieve_session_state(project_state_list):

    st.session_state["g_label"] = project_state_list[0]
    st.session_state["g_mapping"] = project_state_list[1]
    st.session_state["g_ontology"] = project_state_list[2]
    st.session_state["g_ontology_components_dict"] = project_state_list[3]
    st.session_state["g_ontology_components_tag_dict"] = project_state_list[4]
    st.session_state["base_ns"] = project_state_list[5]
    st.session_state["db_connections_dict"] = project_state_list[6]
    st.session_state["db_connection_status_dict"] = project_state_list[7]
    st.session_state["ds_files_dict"] = project_state_list[8]
    st.session_state["saved_views_dict"] = project_state_list[9]
    st.session_state["g_mapping_source_cache"] = project_state_list[10]
    st.session_state["original_g_size_cache"] = project_state_list[11]
    st.session_state["original_g_mapping_ns_dict"] = project_state_list[12]
    st.session_state["custom_terms_dict"] = project_state_list[13]

    for conn in st.session_state["db_connection_status_dict"]:
        update_db_connection_status_dict(conn)
#______________________________________________________

#_________________________________________________
#Funtion to check whether a filename is valid
def is_valid_filename(filename, extension=False):

    excluded_characters = r"[\\/:*?\"<>|]"
    windows_reserved_names = ["CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]

    # no trailing dot
    if filename.endswith("."):
        st.markdown(f"""<div class="error-message">
            ❌ <b>Trailing "."</b> in filename.
            <small> Please remove it.</small>
        </div>""", unsafe_allow_html=True)
        return False

    # no spaces
    elif re.search(r"\s", filename):
        st.markdown(f"""<div class="error-message">
                ❌ <b>Invalid filename</b>.
                <small> Make sure it does not contain any <b>spaces</b>.</b>
            </div>""", unsafe_allow_html=True)
        return False

    # no extension allowed (if extension=False)
    elif os.path.splitext(filename)[1] and not extension:
        st.markdown(f"""<div class="error-message">
                ❌ The filename seems to include an <b>extension</b>.
                <small> Please remove it.</b>
            </div>""", unsafe_allow_html=True)
        return False

    # disallow forbidden characters
    elif re.search(excluded_characters, filename):
        st.markdown(f"""<div class="error-message">
            ❌ <b>Forbidden character</b> in filename.
            <small> Please pick a valid filename.</small>
        </div>""", unsafe_allow_html=True)
        return False

    # disallow windows reserved names
    else:
        for item in windows_reserved_names:
            if item == os.path.splitext(filename)[0].upper():
                st.markdown(f"""<div class="error-message">
                    ❌ <b>Reserved filename.</b><br>
                    <small>Please pick a different filename.</small>
                </div>""", unsafe_allow_html=True)
                return False
                break

    return True
#______________________________________________________


# PAGE: 🧩 ONTOLOGIES===========================================================
# PANEL: IMPORT ONTOLOGY--------------------------------------------------------
#______________________________________________________
# Function to parse an ontology to an initially empty graph
@st.cache_resource
def parse_ontology(source):

    # if source is a file-like object
    if isinstance(source, io.IOBase):
        content = source.read()
        source.seek(0)  # reset index so that file can be reused
        for fmt in ["xml", "turtle", "jsonld", "ntriples", "trig", "trix"]:
            g = Graph()
            try:
                g.parse(data=content, format=fmt)
                if len(g) != 0:
                    return [g, fmt]
            except:
                continue

        # try to auto-detect format
        try:
            g = Graph()
            g.parse(data=content, format=None)
            if len(g) != 0:
                return [g, "auto"]
        except:
            pass
        return [Graph(), None]

    # if source is a string (URL or raw RDF)
    for fmt in ["xml", "turtle", "jsonld", "ntriples", "trig", "trix"]:
        g = Graph()
        try:
            g.parse(source, format=fmt)
            if len(g) != 0:
                return [g, fmt]
        except:
            continue

    # try auto-detect format
    try:
        g = Graph()
        g.parse(source, format=None)
        if len(g) != 0:
            return [g, "auto"]
    except:
        pass

    # next option: try downloading the content and parsing from raw bytes
    for fmt in ["xml", "turtle", "jsonld", "ntriples", "trig", "trix"]:
        try:
            response = requests.get(source)
            g = Graph()
            g.parse(data=response.content, format=fmt)  # use raw bytes
            if len(g) != 0:
                return [g, fmt]
        except:
            continue

    # final fallback: auto-detect from downloaded content
    try:
        response = requests.get(source)
        g = Graph()
        g.parse(data=response.content, format=None)
        if len(g) != 0:
            return [g, "auto"]
    except:
        pass

    # if nothing works
    return [Graph(), "error"]
#______________________________________________________

#______________________________________________________
# Function to get the human-readable name of an ontology
def get_ontology_human_readable_name(g, source_link=None, source_file=None):

    g_ontology_iri = next(g.subjects(RDF.type, OWL.Ontology), None)

    # first option: look for ontology self-contained label
    if g_ontology_iri:
        g_ontology_label = (
            g.value(g_ontology_iri, RDFS.label) or
            g.value(g_ontology_iri, DC.title) or
            g.value(g_ontology_iri, DCTERMS.title) or
            split_uri(g_ontology_iri)[1])    # look for ontology label; if there isnt one just select the ontology iri
        return g_ontology_label

    # second option: use source as label (link or file)
    elif source_link:
        try:
            return split_uri(source_link)[1]
        except:
            return source_link.rstrip('/').split('/')[-1]

    elif source_file:
        return os.path.splitext(source_file.name)[0]

    # final fallback: auto-label using subject of first triple (if it is iri)
    else:
        for s in g.subjects(None, None):
            if isinstance(s, URIRef):
                return "Auto-label: " + split_uri(s)[1]

    # if nothing works
    return "Unlabelled ontology"
#______________________________________________________

#______________________________________________________
# Function to check whether an ontology is valid
# Considered valid if it includes at least one class or property
def is_valid_ontology(g):

    try:
        classes = list(g.subjects(RDF.type, OWL.Class)) + list(g.subjects(RDF.type, RDFS.Class))
        properties = (list(g.subjects(RDF.type, RDF.Property)) + list(g.subjects(RDF.type, OWL.DatatypeProperty)) +
            list(g.subjects(RDF.type, OWL.ObjectProperty)) + list(g.subjects(RDF.type, OWL.AnnotationProperty)))
        return bool(classes or properties)  # consider it valid if it defines at least one class or property

    except:
        return False
#______________________________________________________

#______________________________________________________
def get_candidate_ontology_info_messages(g, g_label, g_format):

    valid_ontology_flag = True
    error_html = ""
    warning_html = ""
    success_html = ""

    # error message
    if not utils.is_valid_ontology(g):
        error_html += f"""❌ URL <b>does not</b> link to a valid ontology."""
        valid_ontology_flag = False

    if g_label in st.session_state["g_ontology_components_dict"]:
        error_html = f"""❌ The ontology <b>
                    {g_label}</b>
                    has already been imported.</div>"""
        valid_ontology_flag = False

    if valid_ontology_flag:

        # warning message
        ontology_ns_dict = get_g_ns_dict(g)
        mapping_ns_dict = get_g_ns_dict(st.session_state["g_mapping"])
        already_used_prefix_list = []
        already_bound_ns_list = []

        for pr, ns in ontology_ns_dict.items():
            if ns in mapping_ns_dict.values() and (pr not in mapping_ns_dict or str(mapping_ns_dict[pr]) != str(ns)):
                already_bound_ns_list.append(ns)
            elif pr in mapping_ns_dict and str(ns) != str(mapping_ns_dict[pr]):
                already_used_prefix_list.append(pr)

        if utils.check_ontology_overlap(g, st.session_state["g_ontology"]):
            warning_html += f"""⚠️ <b>Ontologies overlap</b>. <small>Check them
                        externally to make sure they are aligned and compatible.</small><br>"""

        if already_used_prefix_list or already_bound_ns_list:
            warning_html += f"""⚠️ <b>Duplicated namespaces</b> <small>handled automatically.</small>"""

        # success message
        success_html += f"""✔️ <b>Valid ontology:</b> <b style="color:#F63366;">
                {g_label}</b>
                <small>(parsed successfully with format
                <b>{g_format}</b>).</small>"""

    return [valid_ontology_flag, success_html, warning_html, error_html]

#______________________________________________________

#______________________________________________________
# Function to check whether two ontologies overlap
# Ontology overlap definition - if they share rdfs:label
def check_ontology_overlap(g1, g2):

    labels1 = set()
    for s, p, o in g1.triples((None, RDFS.label, None)):
        labels1.add(str(o))

    labels2 = set()
    for s, p, o in g2.triples((None, RDFS.label, None)):
        labels2.add(str(o))

    common = labels1 & labels2
    return bool(common)
#______________________________________________________

#______________________________________________________
# Function to get the tag of an ontology
# Ensures uniqueness by adding numeric suffix if necessary
def get_unique_ontology_tag(g_label):

    tag=""
    g = st.session_state["g_ontology_components_dict"][g_label]
    g_ontology_iri = next(g.subjects(RDF.type, OWL.Ontology), None)
    forbidden_tags_beginning = [f"ns{i}" for i in range(1, 10)]

    # first option: prefix of the base ns
    if g_ontology_iri:
        prefix = g.namespace_manager.compute_qname(g_ontology_iri)[0]
        if not any(prefix.startswith(tag) for tag in forbidden_tags_beginning):
            tag=prefix

    # second option: use 4 first characters of ontology name
    tag = g_label[:4] if not tag else tag

    # ensure tag is unique
    if not tag in st.session_state["g_ontology_components_tag_dict"].values():
        return tag

    # else make unique by adding numeric suffix
    i = 1
    while f"{tag}{i}" in st.session_state["g_ontology_components_tag_dict"].values():
        i += 1

    return f"{tag}{i}"

#______________________________________________________


# PAGE: 📊 DATABASES============================================================
# PANEL: MANAGE CONNECTIONS-----------------------------------------------------
#________________________________________________________
# Dictionary with default ports for the different engines
def get_default_ports():

    default_ports_dict = {"PostgreSQL": 5432, "MySQL": 3306,
    "MariaDB": 3306, "SQL Server": 1433, "Oracle": 1521, "MongoDB": 27017}

    return default_ports_dict
#______________________________________________________

#______________________________________________________
# Funtion to censor the password or a url_str
def censor_url_str(url_str):

    try:
        parsed = urlparse(url_str)
        if "@" in parsed.netloc:
            creds, hostpart = parsed.netloc.split("@", 1)
            if ":" in creds:
                user, _ = creds.split(":", 1)
                netloc = f"{user}:*****@{hostpart}"
            else:
                netloc = creds + "@" + hostpart
            parsed = parsed._replace(netloc=netloc)
        censored_url_str = urlunparse(parsed)

    except:
        censored_url_str = url_str

    return censored_url_str
#______________________________________________________

#______________________________________________________
# Funtion to get db_url string of an already saved connection
def get_db_url_str(conn_label, censor=False):

    engine, host, port, database, user, password = st.session_state["db_connections_dict"][conn_label]

    if engine == "Oracle":
        db_url_str = f"oracle+oracledb://{user}:{password}@{host}:{port}/{database}"
    elif engine == "SQL Server":
        db_url_str = f"mssql+pyodbc://{user}:{password}@{host}:{port}/{database}?driver=SQL+Server"
    elif engine == "PostgreSQL":
        db_url_str = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"
    elif engine == "MySQL":
        db_url_str = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    elif engine == "MariaDB":
        db_url_str = f"mariadb+pymysql://{user}:{password}@{host}:{port}/{database}"
    elif engine == "MongoDB":
        if user and password:
            db_url_str = f"mongodb://{user}:{password}@{host}:{port}/{database}"
        else:
            db_url_str = f"mongodb://{host}:{port}/{database}"
    else:
        return None

    if censor:
        return censor_url_str(db_url_str)

    return db_url_str
#______________________________________________________

#______________________________________________________
# Funtion to get db_url string of an already saved connection
def get_db_url_str_from_input(engine, host, port, database, user, password):

    if engine == "Oracle":
        db_url_str = f"oracle+oracledb://{user}:{password}@{host}:{port}/{database}"
    elif engine == "SQL Server":
        db_url_str = f"mssql+pyodbc://{user}:{password}@{host}:{port}/{database}?driver=SQL+Server"  # recommended driver for SQLAlchemy
    elif engine == "PostgreSQL":
        db_url_str = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"
    elif engine == "MySQL":
        db_url_str = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    elif engine == "MariaDB":
        db_url_str = f"mariadb+pymysql://{user}:{password}@{host}:{port}/{database}"
    elif engine == "MongoDB":
        if user and password:
            db_url_str = f"mongodb://{user}:{password}@{host}:{port}/{database}"
        else:
            db_url_str = f"mongodb://{host}:{port}/{database}"
    else:
        return None

    return db_url_str
#______________________________________________________

#________________________________________________________
# Funtion to check connection to a database
def try_connection_to_db(db_connection_type, host, port, database, user, password, display_msg=True):

    url_str = get_db_url_str_from_input(db_connection_type, host, port, database, user, password)

    # Special case for MongoDB
    if db_connection_type == "MongoDB":
        try:
            client = MongoClient(url_str, serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            client.close()
            return True

        except Exception as e:
            if display_msg:
                st.markdown(f"""<div class="error-message">
                    ❌ <b>Connection failed.</b>
                    <small><i><b>Full error</b>: {str(e)}</i></small>
                </div>""", unsafe_allow_html=True)
                return False
            else:
                return e

    # SQL databases
    try:
        engine = create_engine(url_str)
        with engine.connect() as conn:
            pass
        return True

    except OperationalError as e:
        if display_msg:
            st.markdown(f"""<div class="error-message">
                ❌ <b>Connection failed.</b>
                <small><i><b>Full error</b>: {str(e)}</i></small>
            </div>""", unsafe_allow_html=True)
            return False
        else:
            return e

    except ArgumentError as e:
        if display_msg:
            st.markdown(f"""<div class="error-message">
                ❌ <b>Invalid connection string.</b><br>
                <small><i><b>Full error</b>: {str(e)}</i></small>
            </div>""", unsafe_allow_html=True)
            return False
        else:
            return e

    except Exception as e:
        if display_msg:
            st.markdown(f"""<div class="error-message">
                ❌ <b>Unexpected error.</b><br>
                <small><i><b>Full error</b>: {str(e)}</i></small>
            </div>""", unsafe_allow_html=True)
            return False
        else:
            return e
#________________________________________________________

#______________________________________________________
# Funtion to make a connection to a database
def make_connection_to_db(connection_label):

    url_str = get_db_url_str(connection_label)
    engine, host, port, database, user, password = st.session_state["db_connections_dict"][connection_label]
    timeout = 3

    # Special case for MongoDB
    if engine == "MongoDB":
        client = MongoClient(url_str, serverSelectionTimeoutMS=timeout * 1000)
        client.admin.command("ping")   # to get error if connection is down
        return client

    else:
        engine = create_engine(url_str, connect_args={"connect_timeout": timeout})
        conn = engine.connect()   # returns a Connection object
        return conn
#______________________________________________________

#______________________________________________________
# Funtion to make a connection to a database
def check_connection_to_db(connection_label, different_page=False):

    try:
        conn = utils.make_connection_to_db(connection_label)
        connection_ok_flag = True
    except:
        if not different_page:
            st.markdown(f"""<div class="error-message">
                ❌ The connection <b>{connection_label}</b> is not working.
                <small>Please check it in the <b>Manage Connections</b> panel.</small>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="error-message">
                ❌ The connection <b>{connection_label}</b> is not working.
                <small>Please check it in the <b>📊 Databases</b> page.</small>
            </div>""", unsafe_allow_html=True)
        connection_ok_flag = False
        conn = None

    return conn, connection_ok_flag
#______________________________________________________

#______________________________________________________
# Funtion to update the connection status dict
def update_db_connection_status_dict(conn_label):

    engine, host, port, database, user, password = st.session_state["db_connections_dict"][conn_label]
    status_flag = try_connection_to_db(engine, host, port, database, user, password, display_msg=False)

    if status_flag == True:
        st.session_state["db_connection_status_dict"][conn_label] = ["🔌", ""]
        return True
    else:
        st.session_state["db_connection_status_dict"][conn_label] = ["🚫", status_flag]
        return False
#______________________________________________________

# PANEL: INSPECT DATA-----------------------------------------------------------
#________________________________________________________
# Function to get all tables/collections in a database
def get_tables_from_db(connection_label):

    conn = utils.make_connection_to_db(connection_label)
    engine = st.session_state["db_connections_dict"][connection_label][0]
    database = st.session_state["db_connections_dict"][connection_label][3]

    if engine == "PostgreSQL":
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
        """))
        return result

    elif engine in ("MySQL", "MariaDB"):
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :db AND table_type = 'BASE TABLE';
        """), {"db": database})
        return result.fetchall()

    elif engine == "Oracle":
        result = conn.execute(text("""
            SELECT table_name
            FROM all_tables
            WHERE owner NOT IN (
                'SYS','SYSTEM','XDB','CTXSYS','MDSYS','ORDDATA','ORDSYS',
                'OUTLN','DBSNMP','APPQOSSYS','WMSYS','OLAPSYS','EXFSYS',
                'DVSYS','GGSYS','OJVMSYS','LBACSYS','AUDSYS',
                'REMOTE_SCHEDULER_AGENT')
        """))
        return result.fetchall()

    elif engine == "SQL Server":
        result = conn.execute(text("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
              AND TABLE_CATALOG = :db
        """), {"db": database})
        return result.fetchall()

    elif engine == "MongoDB":
        db = conn[database]    # conn is a MongoClient
        collections = db.list_collection_names()
        collections = [name for name in collections if not name.startswith("system.")]
        return [(name,) for name in collections]

    else:
        return None
#______________________________________________________

#______________________________________________________
# Function to build the dataframe of a database (for display)
def get_df_from_db(connection_label, db_table):

    conn = utils.make_connection_to_db(connection_label)
    engine = st.session_state["db_connections_dict"][connection_label][0]
    database = st.session_state["db_connections_dict"][connection_label][3]

    # Query Mongo collection
    if engine == "MongoDB":
        db = conn[database]
        rows = list(db[db_table].find())
        df = pd.DataFrame(rows)

    # Query SQL table
    else:
        result = conn.execute(text(f"SELECT * FROM {db_table}"))
        rows = result.fetchall()
        columns = result.keys()
        df = pd.DataFrame(rows, columns=columns)

    return df
#______________________________________________________

#______________________________________________________
# Funtion to display limited dataframe
def display_limited_df(df, title, display=True):

    table_len = f"{len(df)} rows" if len(df) != 1 else f"{len(df)} row"
    if title:
        inner_html = f"""📅 <b style="color:#F63366;"> {title} <small>({table_len}):</small></b>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"""
    else:
        inner_html = f"""📅 <b style="color:#F63366;"> CONTENT <small>({table_len}):</small></b>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"""

    max_rows = utils.get_max_length_for_display()[2]
    max_cols = utils.get_max_length_for_display()[3]

    limited_df = df.iloc[:, :max_cols]   # limit number of columns

    # Slice rows if needed
    if len(df) == 0:
        text = f"""⚠️ <b>{title} <small>(no results).</small></b>""" if title else "⚠️ No results."
        st.markdown(f"""<div class="warning-message">
                {text}
            </div>""", unsafe_allow_html=True)

    else:
        if len(df) > max_rows and df.shape[1] > max_cols:
            inner_html += f"""<small>Showing the <b>first {max_rows} rows</b> (out of {len(df)})
                and the <b>first {max_cols} columns</b> (out of {df.shape[1]}).</small>"""
        elif len(df) > max_rows:
            inner_html += f"""<small>Showing the <b>first {max_rows} rows</b> (out of {len(df)}).</small>"""
        elif df.shape[1] > max_cols:
            inner_html += f"""<small>Showing the <b>first {max_cols} columns</b> (out of {df.shape[1]}).</small>"""

    limited_df = limited_df.head(max_rows)

    if not limited_df.empty:
        st.markdown(f"""<div class="info-message-blue">
                {inner_html}
            </div>""", unsafe_allow_html=True)
        if display:
            st.dataframe(limited_df, hide_index=True)

    return limited_df.head(max_rows)
#______________________________________________________

# PANEL: MANAGE VIEWS-----------------------------------------------------------
#______________________________________________________
# Function to run a query on SQL or MongoDB
def run_query(connection_label, query_or_collection):

    conn = utils.make_connection_to_db(connection_label)
    engine, host, port, database, user, password = st.session_state["db_connections_dict"][connection_label]

    try:
        if engine == "MongoDB":
            db = conn[database]
            rows = list(db[query_or_collection].find())  # list of dicts
            df = pd.DataFrame(rows)

        else:
            result = conn.execute(text(query_or_collection))
            rows = result.fetchall()
            columns = result.keys()
            df = pd.DataFrame(rows, columns=columns)

        view_ok_flag = True
        error = None

    except Exception as e:
        df = None
        view_ok_flag = False
        error =  str(e)

    return df, view_ok_flag, error
#______________________________________________________

#______________________________________________________
#Function to display view results
def display_db_view_results(view):

    connection_label = st.session_state["saved_views_dict"][view][0]
    engine = st.session_state["db_connections_dict"][connection_label][0]
    conn, connection_ok_flag = check_connection_to_db(connection_label)
    query_or_collection = st.session_state["saved_views_dict"][view][1] if engine != "MongoDB" else view

    if connection_ok_flag:
        df, view_ok_flag, error = run_query(connection_label, query_or_collection)

        if not view_ok_flag:
            st.markdown(f"""<div class="error-message">
                ❌ <b>Invalid syntax</b>. <small>Please check your query or collection.
                <i><b>Full error:</b> {error}</i></small>
            </div>""", unsafe_allow_html=True)
        else:
            display_limited_df(df, "Results")

        return view_ok_flag

    return False
#______________________________________________________

#______________________________________________________
#Function to display view results
def remove_view_from_db(view):

    connection_label = st.session_state["saved_views_dict"][view][0]
    engine = st.session_state["db_connections_dict"][connection_label][0]

    # remove the view from the Mongo database (if connected ok)
    if engine == "MongoDB":
        conn, connection_ok_flag = check_connection_to_db(connection_label)
        if connection_ok_flag:
            database = st.session_state["db_connections_dict"][connection_label][3]
            db = conn[database]    # conn is a MongoClient
            db.drop_collection(view)
#______________________________________________________


# PAGE: 🛢️ DATA FILES===========================================================
# PANEL: MANAGE FILES-----------------------------------------------------------
#_________________________________________________
# Funtion to read data files
# For already saved files, takes the filename
# For unsaved files, takes the file itself
def read_data_file(file_input, unsaved=False):

    if unsaved:
        file = file_input
        filename = file_input.name
        file_format = filename.split(".")[-1].lower()
    else:
        filename = file_input
        file = st.session_state["ds_files_dict"][filename]
        file_format = filename.split(".")[-1].lower()

    if file_format == "csv":
        read_content = pd.read_csv(file)

    elif file_format == "tsv":
        read_content = pd.read_csv(file, sep="\t")

    elif file_format in ["xls", "xlsx", "ods"]:
        read_content = pd.read_excel(file)

    elif file_format == "parquet":
        read_content = pd.read_parquet(file)

    elif file_format == "feather":
        read_content = pd.read_feather(file)

    elif file_format == "orc":
        import pyarrow.orc as orc
        orc_file = orc.ORCFile(file)
        read_content = orc_file.read().to_pandas()

    elif file_format == "dta":
        read_content, _ = pyreadstat.read_dta(file)

    elif file_format == "sas7bdat":
        read_content, _ = pyreadstat.read_sas7bdat(file)

    elif file_format == "sav":
        read_content, _ = pyreadstat.read_sav(file)

    elif file_format == "json":
        read_content = pd.read_json(file)

    elif file_format == "xml":
        raw_bytes = file.getvalue() # get full contents safely
        read_content = pd.read_xml(io.BytesIO(raw_bytes), parser="etree")

    file.seek(0)

    return read_content
#_________________________________________________

# PANEL: DISPLAY DATA-----------------------------------------------------------
#_________________________________________________
# Funtion to check whether a hierarchical file is flat
def is_flat_file(data, file_format):
    if file_format == "json":
        if isinstance(data, list):
            return all(
                isinstance(item, dict) and
                all(not isinstance(v, (dict, list)) for v in item.values())
                for item in data
            )
        if isinstance(data, dict):
            return all(not isinstance(v, (dict, list)) for v in data.values())
        return False

    elif file_format == "xml":
        children = list(data)
        if not children:
            return False

        # Case: root has repeating children (like <user>)
        # Each of those children should only have simple text children (no deeper nesting)
        for child in children:
            grandkids = list(child)
            if not grandkids:
                # leaf node → fine
                continue
            # if grandchildren themselves have children → nested → not flat
            if any(len(list(gc)) > 0 for gc in grandkids):
                return False
        return True
#_________________________________________________

#_________________________________________________
# Funtion to safely convert json matches into dataframe
# Handles dicts, scalars, lists, and mixed type
def display_path_dataframe(filename, path_expr, display=True):

    file_format = filename.split(".")[-1].lower()
    flag = find_matches(filename, path_expr)[0]

    if not flag:
        error = find_matches(filename, path_expr)[1]
        if display:
            st.markdown(f"""<div class="error-message">
                ❌ <b>Error applying path:</b> <small><i><b>Full error: </b>{error}</i></small>
            </div>""", unsafe_allow_html=True)
        return False

    else:
        matches = find_matches(filename, path_expr)[1]
        df = matches_to_dataframe(matches, file_format)
        if display:
            display_limited_df(df, "")
        return True
#_________________________________________________

#_________________________________________________
# Funtion to find matches for a hierarchical data file
def find_matches(filename, path_expr):

    # Get info
    file = st.session_state["ds_files_dict"][filename]
    file_format = filename.split(".")[-1].lower()

    # Get file content
    try:
        if file_format == "json":
            raw_bytes = file.getvalue()
            data = json.loads(raw_bytes.decode("utf-8"))
            expr = jsonpath_ng.parse(path_expr)
            matches = [match.value for match in expr.find(data)]

        elif file_format == "xml":
            raw_bytes = file.getvalue()
            tree = ET.parse(io.BytesIO(raw_bytes))
            root = tree.getroot()
            matches = elementpath.select(root, path_expr)

        return True, matches

    except Exception as e:
        return False, e
#_________________________________________________

#_________________________________________________
# Funtion to safely convert json/xml matches into dataframe
# Handles dicts, scalars, lists, and mixed type
def matches_to_dataframe(matches, file_format, default_col="value"):

    if not matches:
        return pd.DataFrame()

    if file_format == "json":

        # Case 1: all dicts → normalize into columns
        if all(isinstance(m, dict) for m in matches):
            return pd.json_normalize(matches)

        # Case 2: all scalars → one-column DataFrame
        if all(not isinstance(m, (dict, list)) for m in matches):
            return pd.DataFrame(matches, columns=[default_col])

        # Case 3: all lists → explode into rows
        if all(isinstance(m, list) for m in matches):
            # flatten nested lists
            flat = [item for sublist in matches for item in sublist]
            # recurse to handle scalars/dicts inside
            return matches_to_dataframe(flat, default_col=default_col)

        # Case 4: mixed types → coerce everything into dicts
        coerced = []
        for m in matches:
            if isinstance(m, dict):
                coerced.append(m)
            elif isinstance(m, list):
                coerced.append({default_col: m})
            else:
                coerced.append({default_col: m})
        return pd.json_normalize(coerced)

    elif file_format == "xml":

        rows = []

        for m in matches:
            if isinstance(m, ET.Element):
                row = dict(m.attrib)   # include attributes
                for child in list(m):   # include child tags
                    row[child.tag] = child.text
                if (not list(m)) and m.text and m.text.strip():   # if element has direct text and no children
                    row[default_col] = m.text.strip()
                rows.append(row)
            else:
                rows.append({default_col: m})    # scalar (string, number, etc.)

        return pd.DataFrame(rows)

    return df
#_________________________________________________

# PANEL: MANAGE PATHS-----------------------------------------------------------
#______________________________________________________
#Function to display path results
def display_path_results(path):

    filename = st.session_state["saved_paths_dict"][path][0]
    path_expression = st.session_state["saved_paths_dict"][path][1]
    file = st.session_state["ds_files_dict"][filename]

    df, view_ok_flag, error = run_query(connection_label, query_or_collection)

    if not view_ok_flag:
        st.markdown(f"""<div class="error-message">
            ❌ <b>Invalid syntax</b>. <small>Please check your path.
            <i><b>Full error:</b> {error}</i></small>
        </div>""", unsafe_allow_html=True)
    else:
        display_limited_df(df, "Results")
#______________________________________________________


# PAGE: 🏗️ BUILD MAPPING========================================================
# PANEL: ADD TRIPLESMAP---------------------------------------------------------
#______________________________________________________
# Funtion to get the dictionary of the TriplesMaps
#{tm_label: tm}
def get_tm_dict():

    if st.session_state["g_label"]:

        tm_dict = {}
        triples_maps = list(st.session_state["g_mapping"].subjects(RML.logicalSource, None))

        for tm in triples_maps:
            tm_label = get_node_label(tm)
            tm_dict[tm_label] = tm
        return tm_dict

    else:
        return {}
#______________________________________________________

#______________________________________________________
# Funtion to get the all info of a TriplesMap
# 0. TriplesMap iri     1. Logical Source iri        2. Data Source
def get_tm_info(tm_label):

    tm_dict = get_tm_dict()
    tm_iri = tm_dict[tm_label]
    ls_iri = next(st.session_state["g_mapping"].objects(tm_iri, RML.logicalSource), None)
    ds = str(next(st.session_state["g_mapping"].objects(ls_iri, RML.source), None))

    # Return info
    return tm_iri, ls_iri, ds
#______________________________________________________

#______________________________________________________
# Funtion to get the all info of a TriplesMap
# 0. Logical Source     1. Data Source        2. Table/View
def get_tm_info_for_display(tm_label):

    # TriplesMap and Logical Source
    tm_iri, ls_iri, ds_raw = get_tm_info(tm_label)
    ls_label = get_node_label(ls_iri)

    # Data Source (look for label if connection is saved, else give censored url_str)
    saved_conn_flag = False
    for conn_label in st.session_state["db_connections_dict"]:
        if str(get_db_url_str(conn_label)) == str(ds_raw):
            ds = conn_label
            saved_conn_flag = True
            break

    if not saved_conn_flag:
        ds = censor_url_str(ds_raw)

    # View or table
    max_length = get_max_length_for_display()[10]
    query = st.session_state["g_mapping"].value(subject=ls_iri, predicate=RML.query)
    if query:
        query = query[:max_length] + "..." if len(query) > max_length else query
    table_name = st.session_state["g_mapping"].value(subject=ls_iri, predicate=RML.tableName)
    source_def = query or table_name or "---"

    # Return info
    return ls_label, ds, source_def
#______________________________________________________

#______________________________________________________
# Get content from table
def get_db_table_df(conn_label, table):

    conn = utils.make_connection_to_db(conn_label)
    engine = st.session_state["db_connections_dict"][conn_label][0]
    database = st.session_state["db_connections_dict"][conn_label][3]

    # SQL databases
    if engine != "MongoDB":
        result = conn.execute(text(f"SELECT * FROM {table}"))
        rows = result.fetchall()
        columns = result.keys()
        df = pd.DataFrame(rows, columns=columns)

    # MongoDB
    else:
        db = conn[database]
        collection = db[table]
        docs = list(collection.find())
        df = pd.DataFrame(docs) if docs else pd.DataFrame()

    return df
#______________________________________________________

#______________________________________________________
# Function to get reference formulation dict
# Should cover all formats in get_supported_formats(data_files=True)
def get_reference_formulation_dict():

    reference_formulation_dict = {"csv": QL.CSV, "tsv": QL.CSV,
        "xls": QL.Excel, "xlsx": QL.Excel, "ods": QL.Excel,
        "parquet": QL.Parquet,"feather": QL.Feather, "orc": QL.ORC,
        "json": QL.JSONPath, "xml": QL.XPath}

    return reference_formulation_dict

#______________________________________________________

# PANEL: ADD SUBJECT MAP--------------------------------------------------------
#______________________________________________________
# Function get the column list of the data source of a tm
# It also gives warning and info messages
def get_column_list_and_give_info(tm_label, template=False):

    term = "reference" if not template else "template placeholder"

    # Get required info
    tm_iri, ls_iri, ds = get_tm_info(tm_label)
    reference_formulation = next(st.session_state["g_mapping"].objects(ls_iri, QL.referenceFormulation), None)
    view_as_ds = next(st.session_state["g_mapping"].objects(ls_iri, RML.query), None)
    table_name_as_ds = next(st.session_state["g_mapping"].objects(ls_iri, RML.tableName), None)

    # Initialise variables
    inner_html = ""
    column_list = []
    ds_available_flag = True

    # Check whether the data source is a saved database
    selected_conn_label = ""
    for conn_label in st.session_state["db_connections_dict"]:
        url_str = get_db_url_str(conn_label)
        if str(ds) == str(url_str):
            selected_conn_label = conn_label

    # Saved data files
    if ds in st.session_state["ds_files_dict"]:
        df = read_data_file(ds)
        column_list = df.columns.tolist()
        ds_for_display = f"""🛢️ <b>{ds}</b>"""

    # Saved database
    elif selected_conn_label:
        engine = st.session_state["db_connections_dict"][selected_conn_label][0]
        database = st.session_state["db_connections_dict"][selected_conn_label][3]
        ds_for_display = f"""📊 <b>{selected_conn_label}</b>"""

        if view_as_ds or table_name_as_ds:
            try:
                conn = utils.make_connection_to_db(selected_conn_label)
                if view_as_ds:
                    result = conn.execute(text(view_as_ds))
                elif table_name_as_ds:
                    if engine != "MongoDB":       # SQL databases
                        result = conn.execute(text(f"SELECT * FROM {table_name_as_ds} LIMIT 0"))
                    else:          # MongoDB case
                        db = conn[database]
                        collection = db[table_name_as_ds]
                        result = collection.find_one()
                column_list = list(result.keys()) if result is not None else []
                if not column_list:
                    inner_html = f"""⚠️ <b>Data source is empty</b>
                    <small>Check it in the <b>📊 Databases</b> page.
                    Manual {term} entry is discouraged.</small>"""

            except Exception as e:
                inner_html = f"""⚠️ Connection to database <b>{selected_conn_label}</b> failed
                    <small>(check it in the <b>📊 Databases</b> page).
                    Manual {term} entry is discouraged.{e}{table_name_as_ds}</small>"""
                ds_available_flag = False
        else:
            inner_html = f"""⚠️ <b>Column detection not possible:</b>
                Missing <code>RML.query</code> or <code>RML.tableName</code> in mapping.
                <small>Manual {term} entry is discouraged.</small>"""

    # Data source is a view but connection is not saved (try to find the columns in the view)
    elif view_as_ds:
        parsed = sqlglot.parse_one(view_as_ds)
        column_list = [str(col) for col in parsed.find_all(sqlglot.expressions.Column)]

        if column_list:
            inner_html = f"""⚠️ No information on the <b>source database</b> is given in
                mapping <b>{st.session_state["g_label"]}</b>.
                <small>Data columns have been inferred from the view.</small>"""
        else:
            inner_html = f"""⚠️ No information on the <b>source database</b> is given in
                mapping <b>{st.session_state["g_label"]}</b>.
                Manual {term} entry is enabled.</small>"""
        ds_for_display = ""

    else:                                                           # data source not saved
        if reference_formulation == QL.SQL:
            inner_html = f"""⚠️ <b>{ds}</b> is unavailable.
                <small>Connect via <b>📊 Databases</b> page to enable column detection.
                Manual {term} entry is discouraged.</small>"""
            ds_for_display = f"""📊 <b>{ds}</b>"""
            ds_available_flag = False

        else:
            inner_html = f"""⚠️ <b>{ds}</b> is unavailable.
                <small>Add the data source via the <b>📊 Databases</b> or <b>🛢️ Data Files</b> pages to enable column detection.
                Manual {term} entry is discouraged.</small>"""
            ds_available_flag = False
        ds_for_display = f"""<b>{ds}</b>"""

    return [column_list, inner_html, ds_for_display, ds_available_flag]
#______________________________________________________

#______________________________________________________
# Function get very small info message on data sources when building mapping
def get_very_small_ds_info(column_list, inner_html, ds_for_display, ds_available_flag):
    if not column_list:   #data source is not available (load)
        if not ds_available_flag:
            text = f"""🚫Data source not available (<b>{ds_for_display}</b>)""" if ds_for_display else f"""🚫Data source not available"""
            st.markdown(f"""<div class="very-small-info">
                {text}
            </div>""", unsafe_allow_html=True)
        else:
            text = f"""🚫Data source not available (<b>{ds_for_display}</b>)""" if ds_for_display else f"""🚫Data source not available"""
            st.markdown(f"""<div class="very-small-info">
                Data source: <b>{ds_for_display}</b>
            </div>""", unsafe_allow_html=True)

    else:
        if ds_for_display:
            st.markdown(f"""<div class="very-small-info">
                Data source: <b>{ds_for_display}</b>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="very-small-info">
                Data source: <b>unknown</b>
            </div>""", unsafe_allow_html=True)
#_____________________________________________________

#______________________________________________________
# Get classes of an ontology
# Option to give the custom classes (g_ont="custom")
# Option to give the superclasses of an ontology
def get_ontology_class_dict(g_ont, superclass=False):

    # Custom classes
    if g_ont == "custom":
        custom_class_dict = {}          # dictionary for custom classes
        for k, v in st.session_state["custom_terms_dict"].items():
            if v == "🏷️ Class":
                custom_class_dict[utils.get_node_label(k)] = k
        return custom_class_dict

    # Ontology classes
    ontology_class_dict = {}

    class_triples = set()
    class_triples |= set(g_ont.triples((None, RDF.type, OWL.Class)))   #collect owl:Class definitions
    class_triples |= set(g_ont.triples((None, RDF.type, RDFS.Class)))    # collect rdfs:Class definitions

    for s, p, o in class_triples:   #we add to dictionary removing the BNodes
        if not isinstance(s, BNode):
            ontology_class_dict[utils.get_node_label(s)] = s

    # Superclasses
    if superclass:
        superclass_dict = {}
        for s, p, o in list(set(g_ont.triples((None, RDFS.subClassOf, None)))):
            if not isinstance(o, BNode) and o not in superclass_dict.values():
                superclass_dict[utils.get_node_label(o)] = o
        return superclass_dict

    return ontology_class_dict
#______________________________________________________

#______________________________________________________
# Funtion to get the dictionary of the graph maps existing in mapping
def get_graph_map_dict():

    graph_map_dict = {}
    graph_map_list = list(st.session_state["g_mapping"].objects(None, RML.graphMap))

    for gm in graph_map_list:
        graph_map_dict[get_node_label(gm)] = gm

    return graph_map_dict
#______________________________________________________

# PANEL: ADD PREDICATE-OBJECT MAP-----------------------------------------------
#______________________________________________________
# Function to get properties of an ontology
# Strict filter (since properties will be used as predicates)
# Option to give the custom properties (g_ont="custom")
# Option to give the superproperties of an ontology
def get_ontology_property_dict(g_ont, superproperty=False):

    # Custom properties
    if g_ont == "custom":
        custom_property_dict = {}
        for k, v in st.session_state["custom_terms_dict"].items():
            if v == "🔗 Property":
                custom_property_dict[utils.get_node_label(k)] = k
        return custom_property_dict

    # Ontology properties
    ontology_property_dict = {}
    ontology_base_iri_list = get_ontology_base_iri(g_ont)
    p_types_list = [RDF.Property, OWL.ObjectProperty, OWL.DatatypeProperty]
    p_exclusion_list = [RDFS.label, RDFS.comment, OWL.versionInfo, OWL.deprecated, RDF.type]

    prop_triples = set()

    for s, p, o in g_ont.triples((None, RDF.type, None)):
        if o in p_types_list:
            if ontology_base_iri_list:
                if str(s).startswith(tuple(ontology_base_iri_list)) and s not in p_exclusion_list:
                    prop_triples.add(s)
            else:
                if s not in p_exclusion_list:
                    prop_triples.add(s)

    ontology_property_dict = {get_node_label(p):p for p in prop_triples}

    # Ontology superproperties
    if superproperty:
        ontology_superproperty_dict = {}
        for s, p, o in g_ont.triples((None, RDFS.subPropertyOf, None)):
            if not isinstance(o, BNode):
                if ontology_base_iri_list:
                    if str(o).startswith(tuple(ontology_base_iri_list)) and o not in p_exclusion_list:
                        ontology_superproperty_dict[utils.get_node_label(o)] = o
                else:
                    if o not in p_exclusion_list:
                        ontology_superproperty_dict[utils.get_node_label(o)] = o
        return ontology_superproperty_dict

    return ontology_property_dict
#______________________________________________________

#_________________________________________________________
# Function to get the ontology base iri
# Returns a list because the ontology can have several components
def get_ontology_base_iri(g_ont):

    base_iri_list = []

    for s in g_ont.subjects(RDF.type, OWL.Ontology):
        try:
            split_uri(s)
            if is_valid_iri(split_uri(s)[0]):
                base_iri_list.append(split_uri(s)[0])
        except:
            if is_valid_iri(s):
                base_iri_list.append(s)

    return base_iri_list
#________________________________________________________

#______________________________________________________
# Funtion to get list of datatypes (including possible dt defined by mapping)
def get_datatype_dict():

    datatype_dict = get_default_datatypes_dict()
    mapping_defined_datatype_list = list(st.session_state["g_mapping"].objects(None, RML.datatype))

    for dt in mapping_defined_datatype_list:
        if not get_node_label(dt) in datatype_dict:
            datatype_dict[utils.get_node_label(dt)] = dt

    return datatype_dict
#______________________________________________________

#______________________________________________________
# Funtion to get list of language tags
def get_language_tags_list():

    language_tags_list = get_default_language_tags_list()

    # Add mapping-defined language tags
    for s, p, o in st.session_state["g_mapping"]:
        if isinstance(o, Literal) and o.language and o.language not in language_tags_list:
            language_tags_list.append(o.language)

    return language_tags_list
#______________________________________________________

#______________________________________________________
# Funtion to prepare a node for the rule preview
def prepare_node_for_rule_preview(node, subject=False, predicate=False, object=False):

    # Subject (node = tm)
    if subject:
        sm_iri_for_pom = next(st.session_state["g_mapping"].objects(node, RML.subjectMap), None)

        if sm_iri_for_pom:
            template_sm_for_pom = next(st.session_state["g_mapping"].objects(sm_iri_for_pom, RML.template), None)
            constant_sm_for_pom = next(st.session_state["g_mapping"].objects(sm_iri_for_pom, RML.constant), None)
            reference_sm_for_pom = next(st.session_state["g_mapping"].objects(sm_iri_for_pom, RML.reference), None)

            if template_sm_for_pom:
                sm_rule = template_sm_for_pom
            elif constant_sm_for_pom:
                sm_rule = constant_sm_for_pom
            elif reference_sm_for_pom:
                sm_rule = reference_sm_for_pom

            if isinstance(sm_rule, URIRef):
                sm_rule = utils.get_node_label(sm_rule)

        else:
            sm_rule = """No Subject Map"""
#______________________________________________________

#______________________________________________________
# Function to display a rule when creating it (in 🏗️_Build_Mapping page)
def preview_rule(tm_iri_for_pom, predicate_list, om_rule, o_is_reference=False, datatype=None, language_tag=None):

    max_length = get_max_length_for_display()[11]   # to adjust font size
    inner_html = ""
    small_header = """<small><b style="color:#F63366; font-size:10px;margin-top:8px; margin-bottom:8px; display:block;">🏷️ Subject → 🔗 Predicate → 🎯 Object</b></small>"""

    # Get subject and prepare for display
    sm_iri_for_pom = next(st.session_state["g_mapping"].objects(tm_iri_for_pom, RML.subjectMap), None)

    if sm_iri_for_pom:
        template_sm_for_pom = next(st.session_state["g_mapping"].objects(sm_iri_for_pom, RML.template), None)
        constant_sm_for_pom = next(st.session_state["g_mapping"].objects(sm_iri_for_pom, RML.constant), None)
        reference_sm_for_pom = next(st.session_state["g_mapping"].objects(sm_iri_for_pom, RML.reference), None)

        s_for_display = template_sm_for_pom or constant_sm_for_pom or reference_sm_for_pom or ""

        if isinstance(s_for_display, URIRef):
            s_for_display = get_node_label(s_for_display)

        if (None, RML.reference, Literal(s_for_display)) in st.session_state["g_mapping"]:  # if reference, add {}
            formatted_s = f"{{{s_for_display}}}"

    else:
        s_for_display = """No Subject Map"""

    # Get object and prepare for display
    o_for_display = get_node_label(om_rule)

    o_for_display = f"{{{o_for_display}}}" if o_is_reference else o_for_display     # if reference, add {}
    o_for_display = f"""{o_for_display}^^{get_node_label(datatype)}""" if datatype else o_for_display    # add datatype
    o_for_display = f"""{o_for_display}@{language_tag}""" if language_tag else o_for_display    # add language tag

    # Adjust font size based on length
    s_for_display = f"""<small>{s_for_display}</small>""" if len(s_for_display) > max_length else s_for_display
    o_for_display = f"""<small>{o_for_display}</small>""" if len(o_for_display) > max_length else o_for_display

    for p in predicate_list:
        p_for_display = f"""<small>{p}</small>""" if len(p) > max_length else p    # adjust font size
        inner_html += f"""<div style="display:flex; justify-content:space-between; align-items:center; gap:10px; margin-top:0px;">
                <div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                    <div style="margin-top:1px; font-size:13px; line-height:1.2;"><b>{s_for_display}</b></div>
                </div>
                <div style="flex:0; font-size:18px;">🡆</div>
                <div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                    <div style="margin-top:1px; font-size:13px; line-height:1.2;"><b>{p_for_display}</b></div>
                </div>
                <div style="flex:0; font-size:18px;">🡆</div>
                <div style="flex:1; min-width:140px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                    <div style="margin-top:1px; font-size:13px; line-height:1.2;"><b>{o_for_display}</b></div>
                </div>
            </div><br>"""

    st.markdown(f"""<div class="blue-preview-message" style="margin-top:0px; padding-top:4px;">
            {small_header}{inner_html}
        </div>""", unsafe_allow_html=True)
#______________________________________________________

#______________________________________________________
# Funtion to get the dictionary of the Subject Maps
# {sm_iri: [LIST]}
# the keys are a list of:
# 0. sm label     1. sm type (template, constant or reference)
# 2. sm_id_iri      # 3. sm_id_label    (info on the id)
# 4. List of all tm to which sm is assigned
def get_sm_dict():

    sm_dict = {}

    tm_list = list(st.session_state["g_mapping"].subjects(RML.logicalSource, None))
    for tm in tm_list:
        tm_label = get_node_label(tm)
        sm_iri = st.session_state["g_mapping"].value(tm, RML.subjectMap)

        template = st.session_state["g_mapping"].value(sm_iri, RML.template)
        constant = st.session_state["g_mapping"].value(sm_iri, RML.constant)
        reference = st.session_state["g_mapping"].value(sm_iri, RML.reference)

        sm_id_iri = None
        sm_type = None
        sm_id_label = None

        if sm_iri:

            sm_label = get_node_label(sm_iri, short_BNode=True)

            if template:
                sm_type = "template"
                sm_id_iri = str(template)
                matches = re.findall(r"{([^}]+)}", template)   #splitting template is not so easy but we try
                if matches:
                    sm_id_label = str(matches[-1])
                else:
                    sm_id_label = str(template)

            elif constant:
                sm_type = "constant"
                sm_id_iri = str(constant)
                sm_id_label = str(split_uri(constant)[1])

            elif reference:
                sm_type = "reference"
                sm_id_iri = str(reference)
                sm_id_label = str(reference)

            if sm_iri not in sm_dict:
                sm_dict[sm_iri] = [sm_label, sm_type, sm_id_iri, sm_id_label, [tm_label]]
            else:
                sm_dict[sm_iri][4].append(tm_label)

    return sm_dict
#______________________________________________________

#______________________________________________________
# Funtion to get the dictionary of the Predicate-Object Maps
# {pom_iri: [LIST]}
# the keys are a list of:
# 0. tm    1. tm_label
# 2. pom label     3. predicate iri     4. predicate label
# 5. om label      6. om type (template, constant or reference)
# 7. om_id_iri      # 8. om_id_label    (info on the id)

# 0. tm      1. predicate list     2. pom iri        3. om iri
# 4. om type (template, constant or reference)    5. om rule
def get_pom_dict():

    pom_dict = {}
    pom_list = list(st.session_state["g_mapping"].objects(None, RML.predicateObjectMap))

    for pom_iri in pom_list:

        tm_iri = next(st.session_state["g_mapping"].subjects(RML.predicateObjectMap, pom_iri), None)
        predicate_list = list(st.session_state["g_mapping"].objects(pom_iri, RML.predicate))
        om_iri = st.session_state["g_mapping"].value(pom_iri, RML.objectMap)

        template = st.session_state["g_mapping"].value(om_iri, RML.template)
        constant = st.session_state["g_mapping"].value(om_iri, RML.constant)
        reference = st.session_state["g_mapping"].value(om_iri, RML.reference)

        if template:
            om_type = "template"
            om_rule = str(template)

        elif constant:
            om_type = "constant"
            om_rule = str(constant)

        elif reference:
            om_type = "reference"
            om_rule = str(reference)

        else:
            om_type = "---"
            om_rule = "---"

        predicate_label_list = []
        for p_iri in predicate_list:
            predicate_label_list.append(get_node_label(p_iri))


        pom_dict[pom_iri] = [tm_iri, predicate_label_list, pom_iri, om_iri, om_type, om_rule]

    return pom_dict
#______________________________________________________

# PANEL: MANAGE MAPPING---------------------------------------------------------
#______________________________________________________
# Preview tm to be removed (tm/sm/pom)
def display_tm_info_for_removal(tm_to_remove_list):

    tm_dict = get_tm_dict()
    sm_dict = get_sm_dict()
    inner_html = f"""<div style="margin-bottom:1px;">
        <small> <b style="color:#F63366;">TriplesMap</b> <span style="color:#F63366;">
        (Subject Map | Predicate-Object Maps)</span> </small> </div>"""
    max_length = utils.get_max_length_for_display()[4]

    # Show tm uo to max_length
    for tm in sorted(tm_to_remove_list)[:max_length]:
        inner_html += f"""<b>🗺️ {tm}</b> ("""
        tm_iri = tm_dict[tm]
        sm_to_remove_tm = next((o for o in st.session_state["g_mapping"].objects(tm_iri, RML.subjectMap)), None)
        if sm_to_remove_tm:
            inner_html += f"""<span style="font-size:0.85em;">🏷️ {sm_dict[sm_to_remove_tm][0]} | </span>"""
        else:
            inner_html += f"""<span style="font-size:0.85em;">🏷️ No Subject Map | </span>"""
        pom_to_remove_tm_list = list(st.session_state["g_mapping"].objects(tm_iri, RML.predicateObjectMap))
        if len(pom_to_remove_tm_list) == 1:
            inner_html += f"""<span style="font-size:0.85em;">🔗 {len(pom_to_remove_tm_list)} Predicate-Object Map)<br></span>"""
        elif pom_to_remove_tm_list:
            inner_html += f"""<span style="font-size:0.85em;">🔗 {len(pom_to_remove_tm_list)} Predicate-Object Maps)<br></span>"""
        else:
            inner_html += f"""<span style="font-size:0.85em;">🔗 No Predicate-Object Maps)<br></span>"""

    # Add "..." if there are more tm
    if len(tm_to_remove_list) > max_length:
        inner_html += f"""🗺️ ..."""

    # Display
    if tm_to_remove_list:
        st.markdown(f"""<div class="info-message-gray">
                {inner_html}
            <div>""", unsafe_allow_html=True)
#______________________________________________________

#______________________________________________________
# Function to completely remove a triplesmap
# Remove primary and secondary triples, but dont remove any triples that are used by another triplesmap
def remove_triplesmap(tm_label):

    tm_dict = get_tm_dict()
    tm_iri = tm_dict[tm_label]   #get tm iri
    g = st.session_state["g_mapping"]  #for convenience

    # Remove ls if not reused
    logical_source = g.value(subject=tm_iri, predicate=RML.logicalSource)
    if logical_source:
        ls_reused = any(s != tm_iri for s, p, o in g.triples((None, RML.logicalSource, logical_source)))
        if not ls_reused:
            g.remove((logical_source, None, None))

    # Remove sm if not reused
    subject_map = g.value(subject=tm_iri, predicate=RML.subjectMap)
    if subject_map:
        sm_reused = any(s != tm_iri for s, p, o in g.triples((None, RML.subjectMap, subject_map)))
        if not sm_reused:
            g.remove((subject_map, None, None))

    # Remove all associated pom (and om)
    pom_iri_list = list(g.objects(subject=tm_iri, predicate=RML.predicateObjectMap))
    for pom_iri in pom_iri_list:
        om_to_delete = st.session_state["g_mapping"].value(subject=pom_iri, predicate=RML.objectMap)
        st.session_state["g_mapping"].remove((pom_iri, None, None))
        st.session_state["g_mapping"].remove((om_to_delete, None, None))

    # Remove from last added tm list if it is there
    if tm_label in st.session_state["last_added_tm_list"]:
        st.session_state["last_added_tm_list"].remove(tm_label)       # if it is in last added list, remove

    g.remove((tm_iri, None, None))   # remove tm triple
#______________________________________________________

#______________________________________________________
# Preview tm to be removed (tm/sm/pom)
def display_sm_info_for_removal(tm_to_unassign_sm_list):

    max_length = utils.get_max_length_for_display()[4]
    tm_dict = get_tm_dict()
    sm_dict = get_sm_dict()
    inner_html = f"""<div style="margin-bottom:1px;">
            <small><span style="color:#F63366;">TriplesMap → </span>
            <b style="color:#F63366;">Subject Map</b></small>
        </div>"""

    # Display sm up to max_length
    for tm in sorted(tm_to_unassign_sm_list)[:max_length]:
        tm_iri = tm_dict[tm]
        sm_iri = st.session_state["g_mapping"].value(subject=tm_iri, predicate=RML.subjectMap)
        sm_label_to_unassign = sm_dict[sm_iri][0]
        inner_html += f"""<div style="margin-bottom:1px;">
            <small>🗺️ {tm} →  🏷️ <b>{sm_label_to_unassign}</b></small>
        </div>"""

    # Add "..." if there are more sm
    if len(tm_to_unassign_sm_list) > max_length:   # many sm to remove
        inner_html += f"""<div style="margin-bottom:1px;">
            <small>🗺️ ... (+{len(tm_to_unassign_sm_list[:max_length])})</small>
        </div>"""

    # Display
    if tm_to_unassign_sm_list:
        st.markdown(f"""<div class="info-message-gray">
                {inner_html}
            </div>""", unsafe_allow_html=True)
#______________________________________________________

#______________________________________________________
# Function to check if mapping is complete
def check_g_mapping(g, warning=False):

    tm_dict = get_tm_dict()
    max_length = utils.get_max_length_for_display()[5]

    tm_wo_sm_list = []   # list of all tm with assigned sm
    tm_wo_pom_list = []
    for tm_label, tm_iri in tm_dict.items():
        if not any(g.triples((tm_iri, RML.subjectMap, None))):
            tm_wo_sm_list.append(tm_label)
    for tm_label, tm_iri in tm_dict.items():
        if not any(g.triples((tm_iri, RML.predicateObjectMap, None))):
            tm_wo_pom_list.append(tm_label)

    pom_wo_om_list = []
    pom_wo_predicate_list = []
    for pom_iri in g.subjects(RDF.type, RML.PredicateObjectMap):
        pom_label = get_node_label(pom_iri)
        if not any(g.triples((pom_iri, RML.objectMap, None))):
            pom_wo_om_list.append(pom_label)
        if not any(g.triples((pom_iri, RML.predicate, None))):
            pom_wo_predicate_list.append(pom_label)

    tm_wo_pom_list_display = utils.format_list_for_display(tm_wo_pom_list)
    tm_wo_sm_list_display = utils.format_list_for_display(tm_wo_sm_list)
    pom_wo_om_list_display = utils.format_list_for_display(pom_wo_om_list)
    pom_wo_predicate_list_display = utils.format_list_for_display(pom_wo_predicate_list)

    inner_html = ""
    heading_html = ""
    g_mapping_complete_flag = True

    if tm_wo_sm_list or tm_wo_pom_list or pom_wo_om_list or pom_wo_predicate_list_display:

        max_length = get_max_length_for_display()[5]
        if g == st.session_state["g_mapping"] and not warning:
            heading_html += f"""ℹ️ Mapping <b style="color:#F63366;">{st.session_state["g_label"]}</b> is incomplete."""
        elif g == st.session_state["g_mapping"] and warning:
            heading_html += f"""⚠️ Mapping <b>{st.session_state["g_label"]}</b> is incomplete."""
        elif not warning:
            heading_html += f"""ℹ️ The <b>Mapping</b> is incomplete."""
        elif warning:
            heading_html += f"""⚠️ The <b>Mapping</b> is incomplete."""

        if tm_wo_sm_list:
            g_mapping_complete_flag = False
            if len(tm_wo_sm_list) < max_length:
                inner_html += f"""<div style="margin-left: 20px">
                <small>· TriplesMap(s) without a Subject Map: <b>
                {tm_wo_sm_list_display}</b></small><br></div>"""
            else:
                inner_html += f"""<div style="margin-left: 20px">
                <small><b>· {len(tm_wo_sm_list)}
                TriplesMaps</b> without
                a Subject Map.</small><br></div>"""

        if tm_wo_pom_list:
            g_mapping_complete_flag = False
            if len(tm_wo_pom_list) < max_length:
                tm_wo_pom_list_display = utils.format_list_for_display(tm_wo_pom_list)
                inner_html += f"""<div style="margin-left: 20px">
                <small>· TriplesMap(s) without Predicate-Object Maps
                <b>{tm_wo_pom_list_display}</b></small><br></div>"""
            else:
                inner_html += f"""<div style="margin-left: 20px">
                <small>· <b>{len(tm_wo_pom_list)}
                TriplesMap(s)</b> without Predicate-Object Maps</small><br></div>"""

        if pom_wo_om_list:
            g_mapping_complete_flag = False
            if len(pom_wo_om_list) < max_length:
                inner_html += f"""<div style="margin-left: 20px">
                <small>· Predicate-Object Map(s) without an Object Map:
                <b>{pom_wo_om_list_display}</b></small><br></div>"""
            else:
                inner_html += f"""<div style="margin-left: 20px">
                <small>· <b>{len(pom_wo_om_list_display)}
                Predicate-Object Maps</b> without
                an Object Map.</small><br></div>"""

        if pom_wo_predicate_list:
            g_mapping_complete_flag = False
            if len(pom_wo_om_list) < max_length:
                inner_html += f"""<div style="margin-left: 20px">
                <small>· Predicate-Object Map(s) without a predicate
                <b>{pom_wo_predicate_list_display}</b></small><br></div>"""
            else:
                inner_html += f"""<div style="margin-left: 20px">
                <small>· <b>{len(pom_wo_predicate_list_display)}
                Predicate-Object Maps</b> without
                a predicate.</small><br></div>"""

    return g_mapping_complete_flag, heading_html, inner_html, tm_wo_sm_list, tm_wo_pom_list, pom_wo_om_list, pom_wo_predicate_list
#_________________________________________________


# PAGE: 🔍 EXPLORE MAPPING======================================================
# PANEL: NETWORK----------------------------------------------------------------
#_________________________________________________
# Funtion to get the rule associated to a subject map
# 0. subject          1. predicate      2. object          3. TriplesMap
def get_rules_for_sm(sm_iri):

    sm_rules_list = []

    g = st.session_state["g_mapping"]

    for pred in [RML.constant, RML.template, RML.reference]:
        sm_for_display = g.value(subject=sm_iri, predicate=pred)
        if sm_for_display:
            break

    tm = g.value(predicate=RML.subjectMap, object=sm_iri)

    for pom in g.objects(subject=tm, predicate=RML.predicateObjectMap):
        om = g.value(subject=pom, predicate=RML.objectMap)
        p_for_display = g.value(subject=pom, predicate=RML.predicate)
        for pred in [RML.constant, RML.template, RML.reference]:
            om_for_display = g.value(subject=om, predicate=pred)
            if om_for_display:
                break

        sm_for_display = get_node_label(sm_for_display)
        p_for_display = get_node_label(p_for_display)
        om_for_display = get_node_label(om_for_display)

        sm_rules_list.append([sm_for_display, p_for_display, om_for_display, get_node_label(tm)])

    return sm_rules_list
#_________________________________________________

#_________________________________________________
# Funtion to get the rule associated to a subject map
# 0. subject          1. predicate      2. object          3. TriplesMap
def display_g_mapping_network(tm_for_network_list):

    sm_rules_list = []

    g = st.session_state["g_mapping"]

    for pred in [RML.constant, RML.template, RML.reference]:
        sm_for_display = g.value(subject=sm_iri, predicate=pred)
        if sm_for_display:
            break

    tm = g.value(predicate=RML.subjectMap, object=sm_iri)

    for pom in g.objects(subject=tm, predicate=RML.predicateObjectMap):
        om = g.value(subject=pom, predicate=RML.objectMap)
        p_for_display = g.value(subject=pom, predicate=RML.predicate)
        for pred in [RML.constant, RML.template, RML.reference]:
            om_for_display = g.value(subject=om, predicate=pred)
            if om_for_display:
                break

        sm_for_display = get_node_label(sm_for_display)
        p_for_display = get_node_label(p_for_display)
        om_for_display = get_node_label(om_for_display)

        sm_rules_list.append([sm_for_display, p_for_display, om_for_display, get_node_label(tm)])

    return sm_rules_list
#_________________________________________________

#_________________________________________________
# Funtion to get unique node label for network display
# Takes the legend dict and updates it
# constant_string is "s", "p" or "o"
def get_unique_node_label(complete_node_id, constant_string, legend_dict):

    max_length=utils.get_max_length_for_display()[6]

    # Get proposed unique short label (ex. "s3")
    i = 1
    while f"{constant_string}{i}" in legend_dict:
        i += 1
    label = f"{constant_string}{i}"

    # Use short label if complete_node_id is too long (avoid duplication)
    if complete_node_id and len(complete_node_id) > max_length:        # assign label and update legend_dict
        if complete_node_id not in legend_dict.values():
            node_id = label
            legend_dict[node_id] = complete_node_id
        else:              # look for already existing label
            for k, v in legend_dict.items():
                if v == complete_node_id:
                    node_id = k
    else:
        node_id = str(complete_node_id)

    return [node_id, legend_dict]
#_________________________________________________

#_________________________________________________
# Function to create network and legend
def create_g_mapping_network(tm_for_network_list):

    max_length=utils.get_max_length_for_display()[6]
    (s_node_color, p_edge_color, o_node_color, p_edge_label_color,
        background_color, legend_font_color) = get_colors_for_network()

    # Get sm list
    sm_for_network_list = []
    for sm in st.session_state["g_mapping"].objects(predicate=RML.subjectMap):
        for rule in utils.get_rules_for_sm(sm):
            if rule[3] in tm_for_network_list:
                sm_for_network_list.append(sm)
                break

    # Create network and legend
    G = nx.DiGraph()
    legend_dict = {}
    for sm in sm_for_network_list:
        for rule in utils.get_rules_for_sm(sm):
            s, p, o, tm = rule

            s_id, legend_dict = get_unique_node_label(s, "s", legend_dict)        # get unique label if too long
            p_label, legend_dict = get_unique_node_label(p, "p", legend_dict)
            o_id, legend_dict = get_unique_node_label(o, "o", legend_dict)

            G.add_node(s_id, label=s_id, color=s_node_color, shape="ellipse")  # add nodes and edge
            if o_id not in G:
                G.add_node(o_id, label=o_id, color=o_node_color, shape="ellipse")  # conditional so that if node is also sm it will have s_node_color
            G.add_edge(s_id, o_id, label=p_label, color=p_edge_color, font={"color": p_edge_label_color})

    # Create Pyvis network
    G_net = Network(height="600px", width="100%", directed=True)
    G_net.from_nx(G)

    # Optional: improve layout and styling
    G_net.repulsion(node_distance=200, central_gravity=0.3, spring_length=200, spring_strength=0.05)
    G_net.set_options("""{
        "nodes": {"shape": "ellipse", "borderWidth": 0,
            "font": {"size": 14, "face": "arial", "align": "center",
              "color": "#ffffff"},
            "color": {"background": "#87cefa", "border": "#87cefa"}},
         "edges": {"width": 3, "arrows":
            {"to": {"enabled": true, "scaleFactor": 0.5}},
            "color": {"color": "#1e1e1e"},
            "font": {"size": 10, "align": "middle", "color": "#1e1e1e"},
            "smooth": false},
          "physics": {"enabled": true},
          "interaction": {"hover": true},
          "layout": {"improvedLayout": true}
        }""")

    # Get network and legend
    network_flag = False
    network_html = ""
    legend_flag = False
    legend_html = ""
    legend_html_list = []

    if sm_for_network_list:
        network_flag = True
        network_html = G_net.generate_html()           # generate HTML string
        network_html = network_html.replace('<div id="mynetwork"',            # inject background color
            f'<div id="mynetwork" style="background-color: {background_color};"')

        # Create and display legend
        for letter in ["s", "p", "o"]:
            legend_html = "<div style='font-family: sans-serif; font-size: 14px;'>"
            if letter == "s":
                legend_html += "<p>🔑 Subject legend</p>"
                object_color = s_node_color
            elif letter == "p":
                legend_html += "<p>🔑 Predicate legend</p>"
                object_color = p_edge_color
            elif letter == "o":
                legend_html += "<p>🔑 Object legend</p>"
                object_color = o_node_color

            for key, value in legend_dict.items():
                if key.startswith(letter):
                    legend_html += ("<div style='display: flex; align-items: flex-start; margin-bottom: 4px;'>"
                        f"<div style='min-width: 60px; font-weight: bold;'><code>{str(key)}</code></div>"
                        f"<div style='flex: 1; max-width: 100%; word-break: break-word; white-space: normal; font-size: 12px;'>{str(value)}</div>"
                        "</div>")
                    legend_flag = True

            legend_html += "</div>"

            legend_html = f"""<div style='border-left: 4px solid {object_color}; padding: 0.4em 0.6em;
                color: {legend_font_color}; font-size: 0.85em; font-family: "Source Sans Pro", sans-serif;
                margin: 0.5em 0; background-color: {background_color}; border-radius: 4px; box-sizing: border-box;
                word-wrap: break-word;'>
                    {legend_html}
                </div>"""

            legend_html_list.append(legend_html)

    return network_flag, network_html, legend_flag, legend_html_list
#__________________________________________________

# PANEL: PREDEFINED SEARCHES----------------------------------------------------
#_________________________________________________
# Function to display a rule
def display_rule(s_for_display, p_for_display, o_for_display):

    small_header = """<small><b style="color:#F63366; font-size:10px;margin-top:8px; margin-bottom:8px; display:block;">
        🏷️ Subject → 🔗 Predicate → 🎯 Object</b></small>"""

    inner_html = ""
    max_length = get_max_length_for_display()[11]

    s_for_display = "" if not s_for_display else s_for_display
    p_for_display = "" if not p_for_display else p_for_display
    o_for_display = "" if not o_for_display else o_for_display

    # Remove {} if reference
    if o_for_display.startswith("{") and o_for_display.endswith("}"):
        o_for_display = o_for_display[1:-1]

    datatype = ""
    for object_type in [RML.template, RML.constant, RML.reference]:
        for s, p, o in st.session_state["g_mapping"].triples((None, object_type, None)):
            if isinstance(o, Literal) and str(o) == o_for_display:
                for _, _, o2 in st.session_state["g_mapping"].triples((s, RML.datatype, None)):
                    datatype = o2
                    break
                if datatype:
                    break
        if datatype:
            break

    language_tag = ""
    for object_type in [RML.template, RML.constant, RML.reference]:
        for s, p, o in st.session_state["g_mapping"].triples((None, object_type, None)):
            if isinstance(o, Literal) and str(o) == o_for_display:
                for _, _, o2 in st.session_state["g_mapping"].triples((s, RML.language, None)):
                    language_tag = o2
                    break
                if language_tag:
                    break
        if language_tag:
            break

    if (None, RML.reference, Literal(s_for_display)) in st.session_state["g_mapping"]:  # reference
        formatted_s = f"""{{{s_for_display}}}"""
    else:
        formatted_s = s_for_display
    formatted_p = p_for_display
    if (None, RML.reference, Literal(o_for_display)) in st.session_state["g_mapping"]:  # reference
        formatted_o = f"""{{{o_for_display}}}"""
    else:
        formatted_o = o_for_display

    formatted_o = formatted_o + f"^^{utils.get_node_label(datatype)}" if datatype else formatted_o
    formatted_o = f"{formatted_o}@{language_tag}" if language_tag else formatted_o

    formatted_s = f"""<small>{formatted_s}</small>""" if len(formatted_s) > max_length else formatted_s
    formatted_p = f"""<small>{formatted_p}</small>""" if len(formatted_p) > max_length else formatted_p
    formatted_o = f"""<small>{formatted_o}</small>""" if len(formatted_o) > max_length else formatted_o

    inner_html += f"""<div style="display:flex; justify-content:space-between; align-items:center; gap:10px; margin-top:0px;">
            <div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                <div style="margin-top:1px; font-size:13px; line-height:1.2;"><b>{formatted_s}</b></div>
            </div>
            <div style="flex:0; font-size:18px;">🡆</div>
            <div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                <div style="margin-top:1px; font-size:13px; line-height:1.2;"><b>{formatted_p}</b></div>
            </div>
            <div style="flex:0; font-size:18px;">🡆</div>
            <div style="flex:1; min-width:140px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                <div style="margin-top:1px; font-size:13px; line-height:1.2;"><b>{formatted_o}</b></div>
            </div>
        </div><br>"""

    return [small_header, inner_html]
#_________________________________________________

#_________________________________________________
# Function to get limit/offset/order inputs
def limit_offset_order(col, list, four_columns=False):

    if not four_columns:
        with col:
            col1a, col1b, col1c = st.columns(3)
    else:
        with col:
            col1a, col1b, col1c, col1d = st.columns(4)

    with col1a:
        limit = st.text_input("🎚️ Limit (opt):", key="key_limit", placeholder="🎚️ Limit",
            label_visibility="collapsed")
        limit = "" if not limit.isdigit() else int(limit)
    with col1b:
        offset = st.text_input("🎚️ Offset (opt):", key="key_offset", placeholder="🎚️ Offset",
            label_visibility="collapsed")
        offset = "" if not offset.isdigit() else int(offset)
    with col1c:
        order_clause = st.selectbox("🎚️ Order (opt):", list,
            key="key_order_clause", label_visibility="collapsed")

    if not four_columns:
        return limit, offset, order_clause

    else:
        with col1d:
            visualisation_option = st.radio("", ["👁️ Visual", "📅 Table"], label_visibility="collapsed",
                key="key_visualisation_option")
        return limit, offset, order_clause, visualisation_option

#_________________________________________________

#_________________________________________________
# Function to add {} to references
def add_braces_to_reference(reference):

    if (None, RML.reference, Literal(reference)) in st.session_state["g_mapping"]:
        return "{" + f"""{reference}"""  + "}"

    return reference
#_________________________________________________

#_________________________________________________
# Function to add datatype or language tag to object
def add_datatype_or_language_tag(om, object_):

    datatype = ""
    language_tag = ""
    for s, p, o in st.session_state["g_mapping"].triples((om, RML.datatype, None)):
        datatype = o
        break
    for s, p, o in st.session_state["g_mapping"].triples((om, RML.language, None)):
        language_tag = o
        break

    if language_tag:
        object_ = utils.get_node_label(object_) + "@" + language_tag
    if datatype:
        object_ = utils.get_node_label(object_) + "^^" + utils.get_node_label(datatype)

    return object_
#_________________________________________________

#________________________________________________
# Function to perform predefined query and get results
def get_predefined_search_results(selected_predefined_search, order_clause):

    if selected_predefined_search == "Rules":
        query = """PREFIX rml: <http://w3id.org/rml/>

            SELECT DISTINCT ?tm ?sm ?pom ?om ?subject_value ?predicate ?object_value WHERE {
              ?tm rml:subjectMap ?sm .
              ?tm rml:predicateObjectMap ?pom .
              ?pom rml:predicate ?predicate .
              ?pom rml:objectMap ?om .

              OPTIONAL { ?sm rml:template ?subject_value . }
              OPTIONAL { ?sm rml:constant ?subject_value . }
              OPTIONAL { ?sm rml:reference ?subject_value . }

              OPTIONAL { ?om rml:template ?object_value . }
              OPTIONAL { ?om rml:constant ?object_value . }
              OPTIONAL { ?om rml:reference ?object_value . }
            }"""

        if order_clause == "⮝ Subject":
            query += f"ORDER BY ASC(?subject_value) "
        elif order_clause == "⮟ Subject":
            query += f"ORDER BY DESC(?subject_value) "
        elif order_clause == "⮝ TriplesMap":
            query += f"ORDER BY ASC(?tm) "
        elif order_clause == "⮟ TriplesMap":
            query += f"ORDER BY DESC(?tm) "

    elif selected_predefined_search == "TriplesMaps":
        query = """PREFIX rml: <http://w3id.org/rml/>
            SELECT ?tm ?logicalSource ?source ?referenceFormulation ?iterator ?tableName ?sqlQuery WHERE {
              ?tm rml:logicalSource ?logicalSource .
              OPTIONAL { ?logicalSource rml:source ?source }
              OPTIONAL { ?logicalSource rml:referenceFormulation ?referenceFormulation }
              OPTIONAL { ?logicalSource rml:iterator ?iterator }
              OPTIONAL { ?logicalSource rml:tableName ?tableName }
              OPTIONAL { ?logicalSource rml:query ?sqlQuery }
            }"""

        if order_clause == "⮝ TriplesMap":
            query += f"ORDER BY ASC(?tm) "
        elif order_clause == "⮟ TriplesMap":
            query += f"ORDER BY DESC(?tm) "

    elif selected_predefined_search == "Subject Maps":
        query = f"""PREFIX rml: <http://w3id.org/rml/>
        SELECT ?tm ?subjectMap ?template ?constant ?reference
               (COALESCE(?template, ?constant, ?reference, "") AS ?rule)
               ?termType ?graph (GROUP_CONCAT(?class; separator=", ") AS ?classes)
        WHERE {{
          ?tm rml:subjectMap ?subjectMap .
          OPTIONAL {{ ?subjectMap rml:template ?template }}
          OPTIONAL {{ ?subjectMap rml:constant ?constant }}
          OPTIONAL {{ ?subjectMap rml:reference ?reference }}
          OPTIONAL {{ ?subjectMap rml:class ?class }}
          OPTIONAL {{ ?subjectMap rml:termType ?termType }}
          OPTIONAL {{ ?subjectMap rml:graph ?graph }}
        }}
        GROUP BY ?tm ?subjectMap ?rule ?termType ?graph
        """

        if order_clause == "⮝ Subject":
            query += f"ORDER BY ASC(?rule) "
        elif order_clause == "⮟ Subject":
            query += f"ORDER BY DESC(?rule) "
        elif order_clause == "⮝ TriplesMap":
            query += f"ORDER BY ASC(?tm) "
        elif order_clause == "⮟ TriplesMap":
            query += f"ORDER BY DESC(?tm) "

    elif selected_predefined_search == "Predicate-Object Maps":
        query = f"""PREFIX rml: <http://w3id.org/rml/>
            SELECT ?tm ?pom ?predicate ?objectMap ?template ?constant ?reference ?termType ?datatype ?language ?graphMap WHERE {{
              ?tm rml:predicateObjectMap ?pom .
              OPTIONAL {{ ?pom rml:predicate ?predicate }}
              OPTIONAL {{ ?pom rml:objectMap ?objectMap }}
              OPTIONAL {{ ?objectMap rml:template ?template }}
              OPTIONAL {{ ?objectMap rml:constant ?constant }}
              OPTIONAL {{ ?objectMap rml:reference ?reference }}
              OPTIONAL {{ ?objectMap rml:termType ?termType }}
              OPTIONAL {{ ?objectMap rml:datatype ?datatype }}
              OPTIONAL {{ ?objectMap rml:language ?language }}
              OPTIONAL {{ ?objectMap rml:graphMap ?graphMap }}
              OPTIONAL {{ ?pom rml:constant ?constant }}
              OPTIONAL {{ ?pom rml:template ?template }}
              OPTIONAL {{ ?pom rml:reference ?reference }}
            }}"""

        if order_clause == "⮝ Predicate":
            query += f"ORDER BY ASC(?predicate) "
        elif order_clause == "⮟ Predicate":
            query += f"ORDER BY DESC(?predicate) "
        elif order_clause == "⮝ TriplesMap":
            query += f"ORDER BY ASC(?tm) "
        elif order_clause == "⮟ TriplesMap":
            query += f"ORDER BY DESC(?tm) "

    elif selected_predefined_search == "Used Properties":
        query = """PREFIX rml: <http://w3id.org/rml/>
        SELECT DISTINCT ?tm ?pom ?predicate WHERE {
          ?tm rml:predicateObjectMap ?pom .
          ?pom rml:predicate ?predicate .
        }"""

        if order_clause == "⮝ Property":
            query += f"ORDER BY ASC(?predicate) "
        elif order_clause == "⮟ Property":
            query += f"ORDER BY DESC(?predicate) "
        elif order_clause == "⮝ TriplesMap":
            query += f"ORDER BY ASC(?tm) "
        elif order_clause == "⮟ TriplesMap":
            query += f"ORDER BY DESC(?tm) "

    elif selected_predefined_search == "Used Classes":
        query = """PREFIX rml: <http://w3id.org/rml/>
            SELECT DISTINCT ?tm ?sm ?class WHERE {
              ?tm rml:subjectMap ?sm .
              ?sm rml:class ?class .
            }"""

        if order_clause == "⮝ Class":
            query += f"ORDER BY ASC(?class) "
        elif order_clause == "⮟ Class":
            query += f"ORDER BY DESC(?class) "
        elif order_clause == "⮝ TriplesMap":
            query += f"ORDER BY ASC(?tm) "
        elif order_clause == "⮟ TriplesMap":
            query += f"ORDER BY DESC(?tm) "

    elif selected_predefined_search == "Incomplete TriplesMaps":

        query = """PREFIX rml: <http://w3id.org/rml/>
         SELECT DISTINCT ?tm WHERE {
          {?tm rml:logicalSource ?ls .
            FILTER NOT EXISTS { ?tm rml:subjectMap ?sm . }
          }
          UNION
          {?tm rml:logicalSource ?ls .
            FILTER NOT EXISTS { ?tm rml:predicateObjectMap ?pom . }
          }}"""

        if order_clause == "⮝ TriplesMap":
            query += f"ORDER BY ASC(?tm) "
        elif order_clause == "⮟ TriplesMap":
            query += f"ORDER BY DESC(?tm) "

    elif selected_predefined_search == "All Triples":
        query = """SELECT ?s ?p ?o WHERE {
            ?s ?p ?o .}"""

        if order_clause == "⮝ Subject":
            query += f"ORDER BY ASC(?s) "
        elif order_clause == "⮟ Subject":
            query += f"ORDER BY DESC(?s) "
        elif order_clause == "⮝ Predicate":
            query += f"ORDER BY ASC(?p) "
        elif order_clause == "⮟ Predicate":
            query += f"ORDER BY DESC(?p) "
        elif order_clause == "⮝ Object":
            query += f"ORDER BY ASC(?o) "
        elif order_clause == "⮟ Object":
            query += f"ORDER BY DESC(?o) "

    return st.session_state["g_mapping"].query(query)
#_________________________________________________

#_________________________________________________
# Function to create, format and display Dataframe with query results
def display_predefined_search_df(df_data, limit, offset, display=True):

    df = pd.DataFrame(df_data)
    df = df.loc[:, df.apply(lambda col: col.replace('', pd.NA).notna().any())]    # drop empty columns
    if offset or limit:   # apply offset/limit pagination
        start = offset if offset else 0
        end = start + limit if limit else None
        df = df.iloc[start:end].reset_index(drop=True)
    elif limit == 0:
        df = pd.DataFrame(columns=df.columns)

    if display:
        if not df.empty:
            st.markdown(f"""<div class="info-message-blue">
                <b>RESULTS ({len(df)}):</b>
            </div>""", unsafe_allow_html=True)
            st.dataframe(df, hide_index=True)
        else:
            st.markdown(f"""<div class="warning-message">
                ⚠️ No results.
            </div>""", unsafe_allow_html=True)

    else:
        return df
#_________________________________________________

#_________________________________________________
# Funtion to check whether a term (class or property) belongs to an imported ontology
def identify_term_ontology(term_label):

    for ont_label, g_ont in st.session_state["g_ontology_components_dict"].items():   # check if class belongs to an imported ontology
        ontology_class_dict = get_ontology_class_dict(g_ont)
        ontology_property_dict = get_ontology_property_dict(g_ont)
        if term_label in ontology_class_dict or term_label in ontology_property_dict:
            ont_tag = st.session_state["g_ontology_components_tag_dict"][ont_label]
            return ont_tag

    return False
#_________________________________________________


# PAGE: 🔬 ONTOLOGY-MAPPING LENS================================================
# PANEL: MAPPING COMPOSITION----------------------------------------------------
#_________________________________________________
# Funtion to get ontology composition by class
def get_mapping_composition_by_class_donut_chart():

    colors = get_colors_for_stats_dict()

    # Count classes classified by ontology
    frequency_dict = {}
    for ont_label, ont in st.session_state["g_ontology_components_dict"].items():
        ont_tag = st.session_state["g_ontology_components_tag_dict"][ont_label]
        ontology_used_classes_count_dict = get_ontology_used_classes_count_by_rules_dict(ont)
        total_count = sum(ontology_used_classes_count_dict.values())
        if total_count:
            frequency_dict[ont_tag] = total_count

    # Count classes from external ontologies (not imported)
    all_used_class_dict = {}
    for s, p, o in st.session_state["g_mapping"].triples((None, RML["class"], None)):
        if isinstance(o, URIRef):
            all_used_class_dict[get_node_label(o)] = o

    other_ontologies_list = []
    for class_label, class_iri in all_used_class_dict.items():
        other_ontologies_flag = True
        for ont_label, g_ont in st.session_state["g_ontology_components_dict"].items():   # check if class belongs to an imported ontology
            ontology_class_dict = get_ontology_class_dict(g_ont)
            if class_iri in ontology_class_dict.values():
                other_ontologies_flag = False
        if other_ontologies_flag:    # class belongs to external ontology
            other_ontologies_list.append(class_iri)

    if other_ontologies_list:   # count times external classes are used
        number_of_rules = 0
        for class_iri in other_ontologies_list:
            for s, p, o in st.session_state["g_mapping"].triples((None, RML["class"], class_iri)):
                sm_iri = s
                rule_list = get_rules_for_sm(sm_iri)
                number_of_rules += len(rule_list)
        if number_of_rules:
            frequency_dict["Other"] = number_of_rules

    # Donut chart
    if frequency_dict:
        # Create donut chart
        data = {"Ontology": list(frequency_dict.keys()),
            "UsageCount": list(frequency_dict.values())}
        fig = px.pie(data, names="Ontology", values="UsageCount", hole=0.4)

        # Donut chart colors
        custom_colors = [colors["salmon"], colors["purple"], colors["blue"]]
        fallback = px.colors.qualitative.Pastel
        color_map = {}
        for label in frequency_dict.keys():
            if label == "Other":
                color_map[label] = colors["gray"]
            else:
                color_map[label] = custom_colors.pop(0) if custom_colors else fallback.pop(0)

        # Donut chart legend
        fig.update_traces(textinfo='label+value', textposition="inside",
            marker=dict(colors=[color_map[label] for label in data["Ontology"]]))

        # Donut chart style
        fig.update_layout(title=dict(
            text="Mapping composition <br>by 🏷️ Class",
            font=dict(size=14),
            x=0.5, xanchor="center", y=0.9, yanchor="bottom"),
            width=400, height=300, margin=dict(t=60, b=20, l=20, r=20),
            showlegend=True,
            legend=dict(orientation="h", yanchor="top", y=0,
                xanchor="center", x=0.5))

        # Render donut chart
        st.plotly_chart(fig)
        return True

    else:
        st.write("")
        st.markdown(f"""<div class="gray-preview-message">
                🔒 <b>No <b style="color:#F63366;">classes</b> used in rules.</b>
            </div>""", unsafe_allow_html=True)
        return False
#_________________________________________________

#_________________________________________________
# Funtion to get the dictionary of the count of the ontology classes used by the mapping (by rules)
# Look for the sm which corresponds to a class and count the number of times that sm is used in a rule
# {class: count}
def get_ontology_used_classes_count_by_rules_dict(g_ont):

    ontology_class_dict = get_ontology_class_dict(g_ont)
    usage_count_dict = {}

    for class_label, class_iri in ontology_class_dict.items():
        for s, p, o in st.session_state["g_mapping"].triples((None, RML["class"], URIRef(class_iri))):
            sm_iri = s
            sm_iri_rule_list = get_rules_for_sm(sm_iri)
            if sm_iri_rule_list:
                usage_count_dict[class_label] = len(sm_iri_rule_list)

    return dict(usage_count_dict)
#_________________________________________________

#_________________________________________________
# Funtion to get ontology composition by property
def get_mapping_composition_by_property_donut_chart():

    colors = get_colors_for_stats_dict()

    # Count properties classified by ontology
    frequency_dict = {}
    for ont_label, ont in st.session_state["g_ontology_components_dict"].items():
        ont_tag = st.session_state["g_ontology_components_tag_dict"][ont_label]
        ontology_used_properties_count_dict = get_ontology_used_properties_count_dict(ont)
        total_count = sum(ontology_used_properties_count_dict.values())
        if total_count:
            frequency_dict[ont_tag] = total_count

    # Count classes from external ontologies (not imported)
    all_used_property_dict = {}
    for s, p, o in st.session_state["g_mapping"].triples((None, RML["predicate"], None)):
        if isinstance(o, URIRef):
            all_used_property_dict[get_node_label(o)] = o

    other_ontologies_list = []
    for prop_label, prop_iri in all_used_property_dict.items():
        other_ontologies_flag = True
        for ont_label, g_ont in st.session_state["g_ontology_components_dict"].items():  # check if property belongs to an imported ontology
            ontology_property_dict = get_ontology_property_dict(g_ont)
            if prop_iri in ontology_property_dict.values():
                other_ontologies_flag = False
        if other_ontologies_flag:     # property belongs to external ontology
            other_ontologies_list.append(prop_iri)

    if other_ontologies_list:  # count times external properties are used
        frequency_dict["Other"] = len(other_ontologies_list)

    # Donut chart
    if frequency_dict:
        # Create donut chart
        data = {"Ontology": list(frequency_dict.keys()),
            "UsageCount": list(frequency_dict.values())}
        fig = px.pie(data, names="Ontology", values="UsageCount", hole=0.4)

        # Donut chart colors
        custom_colors = [colors["salmon"], colors["purple"], colors["blue"]]
        fallback = px.colors.qualitative.Pastel
        color_map = {}
        for label in frequency_dict.keys():
            if label == "Other":
                color_map[label] = colors["gray"]
            else:
                color_map[label] = custom_colors.pop(0) if custom_colors else fallback.pop(0)

        # Donut chart legend
        fig.update_traces(textinfo='label+value', textposition="inside",
            marker=dict(colors=[color_map[label] for label in data["Ontology"]]))

        # Donut chart style
        fig.update_layout(title=dict(
            text="Mapping composition <br>by 🔗 Properties",
            font=dict(size=14),
            x=0.5, xanchor="center", y=0.9, yanchor="bottom"),
            width=400, height=300, margin=dict(t=60, b=20, l=20, r=20),
            showlegend=True,
            legend=dict(orientation="h", yanchor="top", y=0,               # center vertically
                xanchor="center", x=0.5))

        # Render donut chart
        st.plotly_chart(fig)
        return True

    else:
        st.write("")
        st.markdown(f"""<div class="gray-preview-message">
                🔒 <b>No <b style="color:#F63366;">properties</b> used in rules.</b>
            </div>""", unsafe_allow_html=True)
        return False
#_________________________________________________

#_________________________________________________
# Funtion to get the dictionary of the count of the ontology properties used by the mapping (by rules)
# Look for the number of times a property is used as a predicate
# {property: count}
def get_ontology_used_properties_count_dict(g_ont):

    ontology_property_dict = get_ontology_property_dict(g_ont)
    usage_count_dict = defaultdict(int)

    for prop_label, prop_iri in ontology_property_dict.items():
        for triple in st.session_state["g_mapping"].triples((None, RML["predicate"], URIRef(prop_iri))):
            usage_count_dict[prop_label] += 1

    return dict(usage_count_dict)
#_________________________________________________

#_________________________________________________
# Funtion to get the metric "number of tm"
def get_tm_number_metric():

    tm_dict= get_tm_dict()
    number_of_tm = len(tm_dict)

    number_of_tm_for_display = format_number_for_display(number_of_tm)

    st.markdown("""<style>[data-testid="stMetricDelta"] svg {
            display: none;
        }</style>""", unsafe_allow_html=True)
    st.metric(label="#TriplesMap", value=f"{number_of_tm_for_display}")
#_________________________________________________

#_________________________________________________
# Funtion to get the metric "number of rules"
def get_rules_number_metric():

    sm_dict= get_sm_dict()
    number_of_rules = 0
    for sm_iri in sm_dict:
        rule_list = get_rules_for_sm(sm_iri)
        number_of_rules += len(rule_list)

    number_of_rules_for_display = format_number_for_display(number_of_rules)

    st.markdown("""<style>[data-testid="stMetricDelta"] svg {
            display: none;
        }</style>""", unsafe_allow_html=True)
    st.metric(label="#Rules", value=f"{number_of_rules_for_display}",
        delta=f"(s → p → o)", delta_color="off")
#_________________________________________________

# PANEL: PROPERTY USAGE---------------------------------------------------------
#_________________________________________________
# Function to get filter info message
def get_filter_info_message_for_lens(ontology_filter_tag, superfilter):
    inner_html = ""
    if ontology_filter_tag != "No filter":
        inner_html += f"""🧩 <b style="color:#F63366;">{ontology_filter_tag}</b></span><br>"""
    else:
        ont_list = list(st.session_state["g_ontology_components_tag_dict"].values())
        inner_html += f"""🧩 <b style="color:#F63366;">{"+".join(ont_list)}</b></span><br>"""

    if superfilter and superfilter != "No filter":
        inner_html += f"""<small>[📡 <b>{superfilter}</b>]</small></span><br>"""
    else:
        inner_html += f"""<small>[📡 <b>No filter</b>]</small></span><br>"""

    st.write("")
    st.markdown(f"""<div class="gray-preview-message">
            {inner_html}
        </div>""", unsafe_allow_html=True)
#_________________________________________________

#_________________________________________________
# Funtion to get the metric "used properties" or "used classes"
def get_used_ontology_terms_metric(g_ont, superfilter=None, class_=False):

    # Filtered property dictionaries___________________________
    if not class_: # properties
        ontology_term_dict = get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=superfilter)[0]
        ontology_used_term_dict = get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=superfilter)[1]
        label = "Used properties"
    elif class_:
        ontology_term_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superfilter)[0]
        ontology_used_term_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superfilter)[1]
        label = "Used classes"

    # Calculate
    percentage = len(ontology_used_term_dict)/len(ontology_term_dict)*100 if ontology_term_dict else 0
    percentage_for_display = format_number_for_display(percentage)

    # Render
    st.markdown("""<style>[data-testid="stMetricDelta"] svg {
            display: none;
        }</style>""", unsafe_allow_html=True)
    st.metric(label=label, value=f"{len(ontology_used_term_dict)}/{len(ontology_term_dict)}",
        delta=f"({percentage_for_display}%)", delta_color="off")
#_________________________________________________

#_________________________________________________
# Funtion to get the metric "average frequency use" (for properties or classes)
def get_average_ontology_term_frequency_metric(g_ont, superfilter=None, type="used", class_=False):

    # Count
    if not class_:  # properties
        ontology_property_dict = get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=superfilter)[0]
        ontology_used_property_dict = get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=superfilter)[1]
        ontology_used_properties_count_dict = get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=superfilter)[2]
        label = "properties"

        number_of_rules = sum(ontology_used_properties_count_dict.values())
        number_of_used_terms = len(ontology_used_property_dict)
        number_of_terms = len(ontology_property_dict)

    else:
        ontology_class_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superfilter)[0]
        ontology_used_class_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superfilter)[1]
        ontology_used_classes_count_by_rules_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superfilter)[3]
        label = "classes"

        number_of_rules = sum(ontology_used_classes_count_by_rules_dict.values())
        number_of_used_terms = len(ontology_used_class_dict)
        number_of_terms = len(ontology_class_dict)

    # Calculate and display
    st.markdown("""<style>[data-testid="stMetricDelta"] svg {
            display: none;
        }</style>""", unsafe_allow_html=True)
    if type == "used":
        average_use = number_of_rules/number_of_used_terms if number_of_used_terms != 0 else 0
        st.metric(label="Average freq", value=f"{format_number_for_display(average_use)}",
            delta=f"(over used {label})", delta_color="off")
    if type == "all":
        average_use = number_of_rules/number_of_terms if number_of_terms != 0 else 0
        st.metric(label="Average freq", value=f"{format_number_for_display(average_use)}",
            delta=f"(over all {label})", delta_color="off")
#_________________________________________________

#_________________________________________________
# Funtion to get the property dictionaries with sueprproperty filter
def get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=None):

    # Property dictionaries
    ontology_property_dict = utils.get_ontology_property_dict(g_ont)
    ontology_used_property_dict = utils.get_ontology_used_property_dict(g_ont)
    ontology_used_properties_count_dict = utils.get_ontology_used_properties_count_dict(g_ont)

    # Adding superproperty filter to dictionaries
    if superproperty_filter and superproperty_filter != "No filter":

        properties_in_superproperty_dict = {}
        for s, p, o in list(set(g_ont.triples((None, RDFS.subPropertyOf, superproperty_filter)))):
            properties_in_superproperty_dict[get_node_label(s)] = s

        ontology_property_dict = {class_label:class_iri for class_label, class_iri in ontology_property_dict.items()
            if class_iri in properties_in_superproperty_dict.values()}
        ontology_used_property_dict = {class_label:class_iri for class_label, class_iri in ontology_used_property_dict.items()
            if class_iri in properties_in_superproperty_dict.values()}
        ontology_used_properties_count_dict = {class_label:ontology_used_properties_count_dict[class_label]
            for class_label, class_iri in ontology_used_property_dict.items()}

    return [ontology_property_dict, ontology_used_property_dict,
        ontology_used_properties_count_dict]
#_________________________________________________

#_________________________________________________
# Funtion to get the dictionary of the properties of an ontology which are used in the mapping
def get_ontology_used_property_dict(g_ont):

    ontology_property_dict = get_ontology_property_dict(g_ont)
    ontology_used_property_dict = {}

    for prop_label, prop_iri in ontology_property_dict.items():
        if (None, RML.predicate, URIRef(prop_iri)) in st.session_state["g_mapping"]:
            ontology_used_property_dict[prop_label] = prop_iri

    return ontology_used_property_dict
#_________________________________________________



#........................................................................
    colors = get_colors_for_stats_dict()

    ontology_class_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superclass_filter)[0]
    ontology_used_classes_count_by_rules_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superclass_filter)[3]

    nb_used_clases = len(ontology_used_classes_count_by_rules_dict)
    nb_unused_classes = len(ontology_class_dict) - nb_used_clases
    data = {"Category": ["Used classes", "Unused classes"],
        "Value": [nb_used_clases, nb_unused_classes]}

    fig = px.pie(names=data["Category"],values=data["Value"], hole=0.4)

    fig.update_traces(textinfo='value', textposition='inside',
        marker=dict(colors=[colors["purple"], colors["gray"]]))

    fig.update_layout(width=400, height=300, margin=dict(t=20, b=20, l=20, r=20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=0,               # center vertically
            xanchor="center", x=0.5))

    st.plotly_chart(fig)

#........................................................................
#_________________________________________________
# Funtion to get used properties donut chart
def get_used_ontology_terms_donut_chart(g_ont, superfilter=None, class_=False):

    # Get info
    if not class_:  # properties
        ontology_property_dict = get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=superfilter)[0]
        ontology_used_property_dict = get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=superfilter)[1]
        used = len(ontology_used_property_dict)
        unused = len(ontology_property_dict) - len(ontology_used_property_dict)
    else:
        ontology_class_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superfilter)[0]
        ontology_used_classes_count_by_rules_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superfilter)[3]
        used = len(ontology_used_classes_count_by_rules_dict)
        unused = len(ontology_class_dict) - used

    # Data
    data = {"Category": ["Used properties", "Unused properties"],
        "Value": [used, unused]}

    # Create donut chart and style
    colors = get_colors_for_stats_dict()
    fig = px.pie(names=data["Category"],values=data["Value"], hole=0.4)
    fig.update_traces(textinfo='value', textposition='inside',
        marker=dict(colors=[colors["purple"], colors["gray"]]))
    fig.update_layout(width=400, height=300, margin=dict(t=20, b=20, l=20, r=20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=0,               # center vertically
            xanchor="center", x=0.5))

    # Render
    st.plotly_chart(fig)
#_________________________________________________

#_________________________________________________
# Funtion to get property frequency bar plot
def get_ontology_term_frequency_bar_plot(g_ont, selected_terms, superfilter=None, class_=False):

    colors = get_colors_for_stats_dict()

    if not class_:   # properties
        used_ontology_terms_count_dict = utils.get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=superfilter)[2]
    else:
        used_ontology_terms_count_dict = utils.get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superfilter)[3]

    if not selected_terms:  # if none selected, plot 10 most used
        display_list = sorted(used_ontology_terms_count_dict.items(), key=lambda x: x[1], reverse=True)[:10]
    else:
        display_list = sorted([(term, used_ontology_terms_count_dict[term])
            for term in selected_terms], key=lambda x: x[1], reverse=True )

    if display_list:
        # Build plot__
        labels, counts = zip(*display_list)
        fig = px.bar(x=labels,y=counts,text=counts)

        # Style the chart
        fig.update_traces(marker_color=colors["purple"], textposition="inside", width=0.7)
        fig.update_layout(xaxis_title=None, yaxis_title="property frequency",
            yaxis=dict(showticklabels=False, ticks="", showgrid=True,
                gridcolor="lightgray", title_standoff=5),
            height=300, margin=dict(t=20, b=20, l=20, r=20))

        # Render
        st.plotly_chart(fig, use_container_width=True)
#_________________________________________________

#_________________________________________________
# Function to display a rule
def display_rule_list(rule_list):

    max_length = get_max_length_for_display()[11]

    if not rule_list:
        st.markdown(f"""<div class="warning-message">
            ⚠️ <b>No rules.</b>
        </div>""", unsafe_allow_html=True)
    else:
        inner_html = f"""<b>RULES ({len(rule_list)}):</b>
        &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp
        <small>🏷️ Subject → 🔗 Predicate → 🎯 Object</b></small><br>"""

        for rule in rule_list:
            formatted_s = rule[0]
            formatted_p = rule[1]
            formatted_o = rule[2]

            formatted_s = f"""<small>{formatted_s}</small>""" if len(formatted_s) > max_length else formatted_s
            formatted_p = f"""<small>{formatted_p}</small>""" if len(formatted_p) > max_length else formatted_p
            formatted_o = f"""<small>{formatted_o}</small>""" if len(formatted_o) > max_length else formatted_o

            inner_html += f"""<div style="display:flex; justify-content:space-between; align-items:center; gap:10px; margin-top:10px;">"""

            inner_html += f"""<div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                <div style="margin-top:1px; font-size:13px; line-height:1.4;"><b>{formatted_s}</b></div></div>"""

            inner_html += f"""<div style="flex:0; font-size:18px;">🡆</div>"""

            inner_html += f"""<div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                <div style="margin-top:1px; font-size:13px; line-height:1.4;"><b>{formatted_p}</b></div></div>"""

            inner_html += f"""<div style="flex:0; font-size:18px;">🡆</div>"""

            inner_html += f"""<div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                <div style="margin-top:1px; font-size:13px; line-height:1.4;"><b>{formatted_o}</b></div></div><br>
                </div>"""

        st.markdown(f"""<div class="info-message-blue">
            {inner_html}
        </div>""", unsafe_allow_html=True)
#_________________________________________________

# PANEL: CLASS USAGE------------------------------------------------------------
#_________________________________________________
# Funtion to get the dictionary of the count of the ontology classes used by the mapping
def get_ontology_used_classes_count_dict(g_ont):

    ontology_class_dict = get_ontology_class_dict(g_ont)
    usage_count_dict = defaultdict(int)

    for class_label, class_iri in ontology_class_dict.items():
        for triple in st.session_state["g_mapping"].triples((None, RML["class"], URIRef(class_iri))):
            usage_count_dict[class_label] += 1

    return dict(usage_count_dict)
#_________________________________________________

#_________________________________________________
# Funtion to get the dictionary of the ontology classes used by the mapping
def get_ontology_used_class_dict(g_ont):

    ontology_class_dict = get_ontology_class_dict(g_ont)
    ontology_used_class_dict = {}

    for class_label, class_iri in ontology_class_dict.items():
        if (None, RML["class"], URIRef(class_iri)) in st.session_state["g_mapping"]:
            ontology_used_class_dict[class_label] = class_iri

    return ontology_used_class_dict
#_________________________________________________

#_________________________________________________
# Funtion to get the class dictionaries with superclass filter
def get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=None):
    # Class dictionaries
    ontology_class_dict = utils.get_ontology_class_dict(g_ont)
    ontology_used_class_dict = utils.get_ontology_used_class_dict(g_ont)
    ontology_used_classes_count_dict = utils.get_ontology_used_classes_count_dict(g_ont)
    ontology_used_classes_count_by_rules_dict = utils.get_ontology_used_classes_count_by_rules_dict(g_ont)

    # Adding superclass filter to dictionaries
    if superclass_filter and superclass_filter != "No filter":

        classes_in_superclass_dict = {}
        for s, p, o in list(set(g_ont.triples((None, RDFS.subClassOf, superclass_filter)))):
            classes_in_superclass_dict[split_uri(s)[1]] = s

        ontology_class_dict = {class_label:class_iri for class_label, class_iri in ontology_class_dict.items()
            if class_iri in classes_in_superclass_dict.values()}
        ontology_used_class_dict = {class_label:class_iri for class_label, class_iri in ontology_used_class_dict.items()
            if class_iri in classes_in_superclass_dict.values()}
        ontology_used_classes_count_dict = {class_label:ontology_used_classes_count_dict[class_label]
            for class_label, class_iri in ontology_used_class_dict.items()}
        ontology_used_classes_count_by_rules_dict = {class_label:ontology_used_classes_count_by_rules_dict[class_label]
            for class_label, class_iri in ontology_used_class_dict.items() if class_label in ontology_used_classes_count_by_rules_dict}

    return [ontology_class_dict, ontology_used_class_dict,
        ontology_used_classes_count_dict, ontology_used_classes_count_by_rules_dict]
#_________________________________________________


# PAGE: 🔮 MATERIALISE GRAPH====================================================
# PANEL: MATERIALISE------------------------------------------------------------
#_________________________________________________
# Function to get the Autoconfig file
def get_autoconfig_file():

    # Temporal folder
    temp_folder_path = get_folder_name(temp_materialisation_files=True)

    # Reset config dict
    st.session_state["mkgc_config"] = configparser.ConfigParser()

    # List to manage data source labels
    base_label = "DataSource"
    used_data_source_labels_list = []

    # Autoconfig SQL data sources
    for ds in st.session_state["db_connections_dict"]:
        i = 1
        while f"{base_label}{i}" in used_data_source_labels_list:
            i += 1
        mkgc_ds_label = f"{base_label}{i}"
        used_data_source_labels_list.append(mkgc_ds_label)
        db_url = utils.get_db_url_str(ds)
        mkgc_mappings_str = str(os.path.join(temp_folder_path, st.session_state["g_label"] + ".ttl"))
        st.session_state["mkgc_config"][mkgc_ds_label] = {"db_url": db_url,
            "mappings": mkgc_mappings_str}

    # Autoconfig FILE data sources
    for ds_label in st.session_state["ds_files_dict"]:
        i = 1
        while f"{base_label}{i}" in used_data_source_labels_list:
            i += 1
        mkgc_ds_label = f"{base_label}{i}"
        used_data_source_labels_list.append(mkgc_ds_label)
        mkgc_tab_ds_file_path = os.path.join(temp_folder_path, ds_label)
        mkgc_mappings_str = str(os.path.join(temp_folder_path, st.session_state["g_label"] + ".ttl"))
        st.session_state["mkgc_config"][mkgc_ds_label] = {"file_path": mkgc_tab_ds_file_path,
            "mappings": mkgc_mappings_str}
#_________________________________________________

#_________________________________________________
# Funtion to get list of all used mappings
def get_all_mappings_used_for_materialisation():

    mkgc_used_mapping_list = []
    for section in st.session_state["mkgc_config"].sections():
        if section != "CONFIGURATION" and section != "DEFAULT":
            mapping_path_list_string = st.session_state["mkgc_config"].get(section, "mappings", fallback="")
            if mapping_path_list_string:
                for mapping_path in mapping_path_list_string.split(","):
                    mapping_path = mapping_path.strip()
                    g_label = next((key for key, value in st.session_state["mkgc_g_mappings_dict"].items()
                        if value == mapping_path), os.path.splitext(os.path.basename(mapping_path))[0])
                    if g_label not in mkgc_used_mapping_list:   # only save if not duplicated
                        mkgc_used_mapping_list.append(g_label)

    return mkgc_used_mapping_list
#_________________________________________________

#_________________________________________________
# Funtion to get list of all used file data sources
def get_all_tab_ds_used_for_materialisation():

    mkgc_used_tab_ds_list = []
    for section in st.session_state["mkgc_config"].sections():
        if section != "CONFIGURATION" and section != "DEFAULT":
            file_path = st.session_state["mkgc_config"].get(section, "file_path", fallback="")
            if file_path:
                filename = os.path.basename(file_path)
                if filename not in mkgc_used_tab_ds_list:
                    mkgc_used_tab_ds_list.append(filename)

    return mkgc_used_tab_ds_list
#_________________________________________________

#_________________________________________________
# Function to check everything is ready for materialisation
def check_issues_for_materialisation():

    # Initialise variables
    everything_ok_flag = True
    g_mapping_ok_flag = True
    inner_html_success = ""
    inner_html_error = ""

    # Check if config file is empty
    config_string = io.StringIO()
    st.session_state["mkgc_config"].write(config_string)
    if config_string.getvalue() == "":
        everything_ok_flag = False
        inner_html_error += f"""· The Config file is empty.<br>"""

    # List of all used mappings
    mkgc_used_mapping_list = get_all_mappings_used_for_materialisation()

    # List of all used sql databases
    mkgc_used_db_conn_list = []
    for section in st.session_state["mkgc_config"].sections():
        if section != "CONFIGURATION" and section != "DEFAULT":
            used_db_url = st.session_state["mkgc_config"].get(section, "db_url", fallback="")
            if used_db_url and used_db_url not in mkgc_used_db_conn_list:
                mkgc_used_db_conn_list.append(used_db_url)

    # List of all used file data sources
    mkgc_used_tab_ds_list = get_all_tab_ds_used_for_materialisation()

    # Check g_mapping if used (additional mappings checked before adding)
    if st.session_state["g_label"] in mkgc_used_mapping_list:
        if st.session_state["g_label"]:
            g_mapping_complete_flag, heading_html, inner_html, tm_wo_sm_list, tm_wo_pom_list, pom_wo_om_list, pom_wo_predicate_list = utils.check_g_mapping(st.session_state["g_mapping"])
            if not g_mapping_complete_flag:
                inner_html_error += f"""· Mapping <b>{st.session_state["g_label"]}</b> is incomplete
                    <small>(<b> 🧹 clean below</b>).</small><br>"""
                everything_ok_flag = False
                g_mapping_ok_flag = False
            else:
                inner_html_success += f"""· Mapping <b>{st.session_state["g_label"]}</b>
                    is complete.<br>"""

    # Check links to additional mappings from urls (in case they broke after importing - unlikely)
    mkgc_not_working_url_mappings_list = []
    for section in st.session_state["mkgc_config"].sections():
        if section != "CONFIGURATION" and section != "DEFAULT":
            mapping_path_list_string = st.session_state["mkgc_config"].get(section, "mappings", fallback="")
            if mapping_path_list_string:
                for mapping_path in mapping_path_list_string.split(","):
                    if mapping_path in st.session_state["mkgc_g_mappings_dict"].values(): # these are the URL additional mappings
                        if not utils.load_mapping_from_link(mapping_path, display=False):
                            mkgc_not_working_url_mappings_list.append(mapping_path)

    mkgc_used_additional_mapping_list = mkgc_used_mapping_list.copy()
    if st.session_state["g_label"] in mkgc_used_additional_mapping_list:
        mkgc_used_additional_mapping_list.remove(st.session_state["g_label"])
    if mkgc_used_additional_mapping_list and not mkgc_not_working_url_mappings_list:
        inner_html_success += f"""· All <b>additional mappings</b> ({len(mkgc_used_additional_mapping_list)}) are valid.<br>"""
    elif mkgc_used_additional_mapping_list:
        everything_ok_flag = False
        inner_html_error += f"""· Some URL to <b>additional mappings</b> ({len(mkgc_not_working_url_mappings_list)}) not working.<br>"""

    # Check at least a data source is included
    if not mkgc_used_db_conn_list and not mkgc_used_tab_ds_list:
        everything_ok_flag = False
        inner_html_error += f"""· The <b>Config file</b> must contain at least one <b>data source</b>.<br>"""

    # Check connections to db if used
    not_working_db_conn_list = []
    for connection_string in mkgc_used_db_conn_list:
        timeout = 3
        try:
            engine = create_engine(connection_string, connect_args={"connect_timeout": timeout})
            conn = engine.connect()
        except Exception as e:
            not_working_db_conn_list.append(connection_string)
    if not not_working_db_conn_list and mkgc_used_db_conn_list:
        inner_html_success += f"""· All <b>connections to databases</b> ({len(mkgc_used_db_conn_list)}) of the Config file are working.<br>"""
    elif not_working_db_conn_list:
        everything_ok_flag = False
        if len(not_working_db_conn_list) == 1:
            inner_html_error += f"""· A <b>connection to database</b> of the Config file is not working
                <small>(go to <b>📊 Databases</b> page).</small><br>"""
        else:
            inner_html_error += f"""· Several <b>connections to databases</b> ({len(not_working_db_conn_list)})
                of the Config file are not working
                <small>(go to <b>📊 Databases</b> page).</small><br>"""

    # Check all file sources are loaded
    not_loaded_ds_list = []
    for ds_filename in mkgc_used_tab_ds_list:
        if not ds_filename in st.session_state["ds_files_dict"]:
            not_loaded_ds_list.append(ds_filename)

    if not not_loaded_ds_list and mkgc_used_tab_ds_list:
        inner_html_success += f"""· All <b>data source files</b> ({len((mkgc_used_tab_ds_list))})
            of the Config file are loaded.<br>"""
    elif mkgc_used_tab_ds_list:
        everything_ok_flag = False
        if len(not_loaded_ds_list) == 1:
            inner_html_error += f"""· A <b>data file</b> of the Config file is not loaded
                <small>(go to <b>🛢️ Data Files</b> page).</small><br>"""
        else:
            inner_html_error += f"""· Several <b>data files</b> ({len(not_loaded_ds_list)})
                of the Config file are not loaded
                <small>(go to <b>🛢️Data Files</b> page).</small><br>"""


    # Check if there are explicitely declared data sources in any mapping that are not declared in the Config file
    missing_explicit_ds_list_g_mapping = []
    explicit_ds = get_all_explicit_datasources(st.session_state["g_mapping"])
    for ds in explicit_ds:
        if ds not in mkgc_used_db_conn_list and ds not in mkgc_used_tab_ds_list and ds not in missing_explicit_ds_list_g_mapping:
            missing_explicit_ds_list_g_mapping.append(ds)

    missing_explicit_ds_list_additional_mappings = []
    for additional_mapping_label in mkgc_used_additional_mapping_list:
        explicit_ds = get_all_explicit_datasources(st.session_state["mkgc_g_mappings_dict"][additional_mapping_label])
        for ds in explicit_ds:
            if ds not in mkgc_used_db_conn_list and ds not in mkgc_used_tab_ds_list and ds not in missing_explicit_ds_list_additional_mappings:
                missing_explicit_ds_list_additional_mappings.append(ds)

    if missing_explicit_ds_list_g_mapping:
        everything_ok_flag = False
        if len(missing_explicit_ds_list_g_mapping) == 1:
            inner_html_error += f"""· A <b>data source</b> is explicitely declared in mapping <b>{st.session_state["g_label"]}</b>
                <small>but not in the Config file.</small><br>"""
        else:
            inner_html_error += f"""· Several <b>data sources</b> ({len(_missing_explicit_ds_list_g_mapping)})
                are explicitely declared in mapping <b>{st.session_state["g_label"]}</b>
                <small>but not in the Config file.</small><br>"""

    if missing_explicit_ds_list_additional_mappings:
        everything_ok_flag = False
        censored_missing_explicit_ds_list_additional_mappings = [utils.censor_url_str(ds) for ds in missing_explicit_ds_list_additional_mappings]
        if len(missing_explicit_ds_list_additional_mappings) == 1:
            inner_html_error += f"""· A <b>data source</b> is explicitely declared in the <b>additional mapping(s)</b>
                <small>but not in the Config file.</small><br>"""
        else:
            inner_html_error += f"""· Several <b>data sources</b> ({len(missing_explicit_ds_list_additional_mappings)})
                are explicitely declared in the <b>additional mapping(s)</b>
                <small>but not in the Config file.</small><br>"""

    # Ds expicitely used by additional mappings
    data_sources_list = mkgc_used_db_conn_list + mkgc_used_tab_ds_list
    explicit_ds_g_mapping = get_all_explicit_datasources(st.session_state["g_mapping"])
    explicit_ds_additional_mappings = []
    for additional_mapping_label in mkgc_used_additional_mapping_list:
        explicit_ds = get_all_explicit_datasources(st.session_state["mkgc_g_mappings_dict"][additional_mapping_label])
        for ds in explicit_ds:
            if ds not in explicit_ds_additional_mappings:
                explicit_ds_additional_mappings.append(ds)

    # Build INFO TABLE
    info_table_html = """<b style="display:block; margin-bottom:10px;">ℹ️ INFO TABLE</b><small><table>"""

    if mkgc_used_db_conn_list and not not_working_db_conn_list:
        censored_mkgc_used_db_conn_list = [censor_url_str(conn) for conn in mkgc_used_db_conn_list]
        info_table_html += f"""<thead><tr>
                                        <th>📊 Databases</th>
                                        <td>{format_list_for_display(mkgc_used_db_conn_list)}</td>
                                    </tr></thead><tbody>"""

    if not_working_db_conn_list:
        working_db_conn_list = [conn for conn in mkgc_used_db_conn_list if conn not in not_working_db_conn_list]
        censored_working_db_conn_list = [censor_url_str(conn) for conn in working_db_conn_list]
        censored_not_working_db_conn_list = [censor_url_str(conn) for conn in not_working_db_conn_list]
        if working_db_conn_list:
            info_table_html += f"""<thead><tr>
                                            <th>📊 Databases (working)</th>
                                            <td>{format_list_for_display(censored_working_db_conn_list)}</td>
                                        </tr></thead><tbody>"""
        info_table_html += f"""<thead><tr>
                                        <th>📊 Databases (not working)</th>
                                        <td>{format_list_for_display(censored_not_working_db_conn_list)}</td>
                                    </tr></thead><tbody>"""

    if mkgc_used_tab_ds_list and not not_loaded_ds_list:
        info_table_html += f"""<thead><tr>
                                        <th>🛢️ Data files</th>
                                        <td>{format_list_for_display(mkgc_used_tab_ds_list)}</td>
                                    </tr></thead><tbody>"""

    if not_loaded_ds_list:
        loaded_ds_list = [ds for ds in mkgc_used_tab_ds_list if ds not in not_loaded_ds_list]
        if loaded_ds_list:
            info_table_html += f"""<thead><tr>
                                            <th>🛢️ Data_files (not loaded)</th>
                                            <td>{format_list_for_display(loaded_ds_list)}</td>
                                        </tr></thead><tbody>"""
        info_table_html += f"""<thead><tr>
                                        <th>🛢️ Data_files (not loaded)</th>
                                        <td>{format_list_for_display(not_loaded_ds_list)}</td>
                                    </tr></thead><tbody>"""

    if mkgc_used_additional_mapping_list:
        info_table_html += f"""<thead><tr>
                                        <th>🗺️ Additional Mappings</th>
                                        <td>{format_list_for_display(mkgc_used_additional_mapping_list)}</td>
                                    </tr></thead><tbody>"""

    if explicit_ds_g_mapping:
        info_table_html += f"""<thead><tr>
                                        <th>📌 Explicit data sources (mapping {st.session_state["g_label"]})</th>
                                        <td>{format_list_for_display(explicit_ds_g_mapping)}</td>
                                    </tr></thead><tbody>"""

    if explicit_ds_additional_mappings:
        info_table_html += f"""<thead><tr>
                                        <th>📌 Explicit data sources (additional mappings)</th>
                                        <td>{format_list_for_display(explicit_ds_additional_mappings)}</td>
                                    </tr></thead><tbody>"""

    info_table_html += "</table></small>"

    # Return everything
    return everything_ok_flag, inner_html_success, inner_html_error, info_table_html
#_________________________________________________

#_________________________________________________
# Function to get all data sources used in the mappings
def get_all_explicit_datasources(g_item):

    if isinstance(g_item, Graph):
        g = g_item
    elif isinstance(g_item, str):
        g = Graph()
        g.parse(g_item, format="turtle")
    elif isinstance(g_item, UploadedFile):
        g = Graph()
        g.parse(data=g_item.getvalue().decode("utf-8"), format="turtle")
    else:
        return []

    sources = set()
    for s, p, o in g.triples((None, RML.source, None)):
        sources.add(str(o))

    return list(sources)
#_________________________________________________

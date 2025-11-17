import streamlit as st
import os
import utils
import pandas as pd
import pickle
from rdflib import Graph, URIRef, Literal, Namespace, BNode
from rdflib.namespace import split_uri
from rdflib.namespace import RDF, RDFS, DC, DCTERMS, OWL, XSD
import time   # for success messages
import re
import uuid   # to handle uploader keys
import io
from io import IOBase
import psycopg
import pymysql    # another option mysql-connector-python
import oracledb
import pyodbc
import sqlglot
import requests
import base64
from collections import defaultdict
import plotly.express as px
from PIL import Image   # for logo rendering
import configparser

from concurrent.futures import ThreadPoolExecutor, TimeoutError

import json
import csv
import rdflib
from collections import Counter
from urllib.parse import urlparse

from streamlit_js_eval import streamlit_js_eval

# REQUIRED NS===================================================================
#________________________________________________________
# Function to retrieve namespaces which are needed for our code
def get_required_ns_dict():

    required_ns_dict = {"rml": Namespace("http://w3id.org/rml/"),
        "ql": Namespace("http://semweb.mmlab.be/ns/ql#")}

    return required_ns_dict

#_______________________________________________________

#________________________________________________________
# Retrieving necessary namespaces for UTILS page here
RML, QL = get_required_ns_dict().values()
#________________________________________________________


# AESTHETICS====================================================================
#______________________________________________________
# Function to render headers (UNUSED)
def render_header(title, description, dark_mode: bool = False):

    # get logo
    image_path = "logo/logo_inverse.png" if dark_mode else "logo/logo.png"
    with open(image_path, "rb") as img_file:
        image_base64 = base64.b64encode(img_file.read()).decode()

    # set colors
    bg_color = "#1e1e1e" if dark_mode else "#f0f0f0"
    title_color = "#d8c3f0" if dark_mode else "#511D66"
    desc_color = "#999999" if dark_mode else "#555"

    # return header
    return f"""<div style="display:flex; align-items:center; background-color:{bg_color}; padding:16px 20px;
                border-radius:12px; box-shadow:0 2px 6px rgba(0,0,0,0.1);">
        <img src="data:image/png;base64,{image_base64}" alt="Logo"
             style="height:74px; margin-right:70px; border-radius:8px;" />
        <div style="display:flex; flex-direction:column;">
        <div style="font-size:1.4rem; font-weight:600; color:{title_color}; margin-bottom:4px;">
            {title}
        </div>
        <div style="font-size:0.95rem; color:{desc_color};">
            {description}
        </div></div></div>"""
#______________________________________________________

#______________________________________________________
# Function to render logo in sidebar
def render_sidebar_logo(dark_mode: bool = False):

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

    </style>"""
#_______________________________________________________

#________________________________________________
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

    </style>"""
#______________________________________________________

#______________________________________________________
# Function to get time to display success messages
def get_success_message_time():

    return 2
#______________________________________________________

#______________________________________________________
# Function to get error message to indicate a g_mapping must be created/imported
def get_missing_g_mapping_error_message():

    st.markdown(f"""<div class="error-message">
        ❌ You need to create or import a mapping from the
        <b>Select Mapping</b> pannel.
    </div>""", unsafe_allow_html=True)
#______________________________________________________

#______________________________________________________
# Function to get error message to indicate a g_mapping must be created/imported
def get_missing_g_mapping_error_message_different_page():

    st.markdown(f"""<div class="error-message">
        ❌ You need to create or import a mapping from the
        <b>🌍 Global Configuration</b> page <small>(<b>Select Mapping</b> pannel).</small>
    </div>""", unsafe_allow_html=True)
#______________________________________________________

#______________________________________________________
# Function to get the mapping+ontology corner status message in the different panels
def get_corner_status_message():

    inner_html = ""

    # mapping message
    if st.session_state["g_label"]:
        inner_html += f"""<img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                style="vertical-align:middle; margin-right:8px; height:18px;">
                 Mapping <b style="color:#F63366;">{st.session_state["g_label"]}</b><br>"""
    else:
        inner_html += f"""🚫 <b>No mapping</b> is loaded.<br>"""

    inner_html += "<br>"

    # ontology message
    if st.session_state["g_ontology"]:
        if len(st.session_state["g_ontology_components_dict"]) > 1:
            ontology_items = '\n'.join([f"""<li><b>{ont}
            <b style="color:#F63366;">[{st.session_state["g_ontology_components_tag_dict"][ont]}]</b>
            </b></li>""" for ont in st.session_state["g_ontology_components_dict"]])
            inner_html += f"""🧩 <b>Ontologies</b>:
                <ul style="font-size:0.85rem; margin:6px 0 0 15px; padding-left:10px;">
                    {ontology_items}
                </ul>"""
        else:
            ont = next(iter(st.session_state["g_ontology_components_dict"]))
            inner_html += f"""🧩 Ontology: <b><br>
                    {ont}</b>
                    <b style="color:#F63366;">[{st.session_state["g_ontology_components_tag_dict"][ont]}]</b>."""
    else:
        inner_html += f"""🚫 <b>No ontology</b> has been imported."""

    # render
    st.markdown(f"""<div class="gray-preview-message">
            {inner_html}
        </div>""", unsafe_allow_html=True)
#______________________________________________________

#______________________________________________________
# Function to get the mapping corner status message
def get_corner_status_message_mapping():

    if st.session_state["g_label"]:
        st.markdown(f"""<div class="gray-preview-message">
                <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                style="vertical-align:middle; margin-right:8px; height:18px;">
                 Mapping <b style="color:#F63366;">{st.session_state["g_label"]}</b><br>
                <small style="margin-left:26px;">{utils.get_number_of_tm(st.session_state["g_mapping"])} TriplesMaps </small>
            </div>""", unsafe_allow_html=True)

    else:
        st.markdown(f"""<div class="gray-preview-message">
                <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                style="vertical-align:middle; margin-right:8px; height:20px;">
                🚫 <b>No mapping</b> is loaded.
            </div>
        """, unsafe_allow_html=True)
#______________________________________________________

#_______________________________________________________
# Function to get the ontology status message in the different panels
def get_corner_status_message_ontology():

    if st.session_state["g_ontology"]:

        if len(st.session_state["g_ontology_components_dict"]) > 1:
            ontology_items = '\n'.join([f"""<li><b>{ont}
            <b style="color:#F63366;">[{st.session_state["g_ontology_components_tag_dict"][ont]}]</b>
            </b></li>""" for ont in st.session_state["g_ontology_components_dict"]])
            st.markdown(f"""<div class="gray-preview-message">
                    🧩 <b>Ontologies</b>:
                <ul style="font-size:0.85rem; margin:6px 0 0 15px; padding-left:10px;">
                    {ontology_items}
                </ul></div>""", unsafe_allow_html=True)

        else:
            ont = next(iter(st.session_state["g_ontology_components_dict"]))
            st.markdown(f"""<div class="gray-preview-message">
                    🧩 Ontology: <b><br>
                    {ont}</b>
                    <b style="color:#F63366;">[{st.session_state["g_ontology_components_tag_dict"][ont]}]</b>.
                </div>""", unsafe_allow_html=True)

    else:
        st.markdown(f"""<div class="gray-preview-message">
                🚫 <b>No ontology</b> has been imported.
            </div>
        """, unsafe_allow_html=True)

#______________________________________________________

#______________________________________________________
# Function to format a list
def format_list_for_markdown(xlist):

    if not xlist:
        formatted_list = ""
    elif len(xlist) == 1:
        formatted_list = xlist[0]
    else:
        formatted_list = ", ".join(xlist[:-1]) + " and " + xlist[-1]

    return formatted_list
#______________________________________________________

#_________________________________________________
# Funtion to get label of a node
def get_node_label(node):

    if isinstance(node, URIRef):
        label = split_uri(node)[1]
    elif isinstance(node, BNode):
        label = "_:" + str(node)[:7] + "..."
    elif node:
        label = str(node)
    else:
        label = ""

    return label
#_________________________________________________

#_________________________________________________
# Funtion to get label of a node
def format_iri_to_prefix_label(node):

    if isinstance(node, BNode):
        return node

    try:
        prefix, ns, local = st.session_state["g_mapping"].namespace_manager.compute_qname(node)
        return prefix + ": " + local
    except Exception:
        return get_node_label(node)

    return get_node_label(node)   # return label without prefix
#_________________________________________________

#______________________________________________________
# Funtion to get the used classes metric
def format_number_for_display(number):

    # >10 M  eg. 21M
    if number >= 10*10**6:
        number_for_display = f"{int(number/ 10**6)}M"

    # 1-10 M  eg. 3.4M
    elif number >= 10**6:
        number_for_display = f"{round(number / 10**6, 1)}M"

    # 10k-1M  eg. 23k
    elif number >= 10*10**3:
        number_for_display = f"{int(number / 1000)}k"

    # 1k-10k  eg. 2.9k
    elif number >= 10**3:
        number_for_display = f"{round(number / 1000, 1)}k"

    # 10-1k  eg. 545
    elif number >= 10:
        number_for_display = f"{int(number)}"

    # 1-10  eg. 7.4
    elif number >= 1:
        number_for_display = f"{round(number, 1)}"

    # 0.1-1  eg. 0.32
    elif number >= 0.1:
        number_for_display = f"{round(number, 2)}"

    # 0
    elif number == 0:
        number_for_display = 0

    # <0.001
    elif number < 0.001:
        number_for_display = "< 0.001"

    # <0.01
    elif number < 0.01:
        number_for_display = "< 0.01"

    # <0.1
    else:
        number_for_display = "< 0.1"

    return number_for_display
#______________________________________________________

#______________________________________________________
# Function to get the max_length for the display options
# 0. complete dataframes      1. last added dataframes
# 2. Query display (rows)    3. Query display (columns)
# 4. List of multiselect items for hard display     # 5 Long lists for soft display
# 6. Label in network visualisation (characters)
# 7. Suggested mapping label (characters)    8. URL for display (characters)
# 9. Max characters when displaying ontology/mapping serialisation (ttl or nt)
# 10. Query for display
def get_max_length_for_display():

    return [50, 10, 100, 20, 5, 5, 20, 15, 40, 100000, 30]
#_______________________________________________________


# INITIALISE PAGES =============================================================
#________________________________________________________
# Function to retrieve namespaces which are needed for our code
def init_session_state_variables():

    if "session_initialised_ok_flag" not in st.session_state:

        st.session_state["session_initialised_ok_flag"] = True

        # 🌍 GLOBAL CONFIGURATION_________________
        # TAB1
        st.session_state["g_mapping"] = Graph()
        st.session_state["g_label"] = ""
        st.session_state["g_label_temp_new"] = ""
        st.session_state["new_g_mapping_created_ok_flag"] = False
        st.session_state["key_mapping_uploader"] = None
        st.session_state["g_label_temp_existing"] = ""
        st.session_state["existing_g_mapping_loaded_ok_flag"] = False
        st.session_state["session_retrieved_ok_flag"] = False
        st.session_state["g_mapping_source_cache"] = ["",""]
        st.session_state["original_g_size_cache"] = 0
        st.session_state["original_g_mapping_ns_dict"] = {}
        st.session_state["cached_mapping_retrieved_ok_flag"] = False
        st.session_state["everything_reseted_ok_flag"] = False
        st.session_state["g_label_changed_ok_flag"] = False
        st.session_state["candidate_g_mapping"] = Graph()
        # TAB2
        st.session_state["ns_bound_ok_flag"] = False
        st.session_state["base_ns"] = get_default_base_ns()
        st.session_state["base_ns_changed_ok_flag"] = False
        st.session_state["ns_unbound_ok_flag"] = False
        st.session_state["last_added_ns_list"] = []
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
        st.session_state["g_ontology_loaded_ok_flag"] = False
        st.session_state["ontology_link"] = ""
        st.session_state["key_ontology_uploader"] = None
        st.session_state["ontology_file"] = None
        st.session_state["g_ontology_from_file_candidate"] = Graph()
        st.session_state["g_ontology_from_link_candidate"] = Graph()
        st.session_state["g_ontology_components_dict"] = {}
        st.session_state["g_ontology_components_tag_dict"] = {}
        st.session_state["g_ontology_reduced_ok_flag"] = False

        # 📊 SQL DATABASES____________________________________
        # TAB1
        st.session_state["db_connections_dict"] = {}
        st.session_state["db_connection_status_dict"] = {}
        st.session_state["db_connection_saved_ok_flag"] = False
        st.session_state["db_connection_removed_ok_flag"] = False
        st.session_state["db_connection_status_updated_ok_flag"] = False
        #TAB3
        st.session_state["sql_queries_dict"] = {}
        st.session_state["sql_query_saved_ok_flag"] = False
        st.session_state["sql_query_removed_ok_flag"] = False

        # 🛢️ TABULAR DATA
        # TAB1
        st.session_state["key_ds_uploader"] = str(uuid.uuid4())
        st.session_state["ds_files_dict"] = {}
        st.session_state["large_ds_files_dict"] = {}
        st.session_state["ds_file_saved_ok_flag"] = False
        st.session_state["ds_file_removed_ok_flag"] = False

        # 🏗️ BUILD MAPPING
        # TAB1
        st.session_state["key_ds_uploader"] = str(uuid.uuid4())
        st.session_state["last_added_tm_list"] = []
        st.session_state["tm_label"] = ""
        st.session_state["tm_saved_ok_flag"] = False
        # TAB2
        st.session_state["key_ds_uploader_for_sm"] = str(uuid.uuid4())
        st.session_state["last_added_sm_list"] = []
        st.session_state["sm_label"] = ""
        st.session_state["tm_label_for_sm"] = False
        st.session_state["sm_template_list"] = []
        st.session_state["sm_saved_ok_flag"] = False
        st.session_state["sm_iri"] = None
        st.session_state["sm_template_prefix"] = ""
        st.session_state["sm_template_variable_part_flag"] = False
        st.session_state["multiple_subject_class_list"] = []
        # TAB3
        st.session_state["key_ds_uploader_for_pom"] = str(uuid.uuid4())
        st.session_state["om_template_ns_prefix"] = ""
        st.session_state["template_om_is_iri_flag"] = False
        st.session_state["pom_saved_ok_flag"] = False
        st.session_state["om_template_list"] = []
        st.session_state["last_added_pom_list"] = []
        st.session_state["om_template_variable_part_flag"] = False
        # TAB4
        st.session_state["tm_deleted_ok_flag"] = False
        st.session_state["sm_unassigned_ok_flag"] = False
        st.session_state["g_mapping_cleaned_ok_flag"]  = False
        st.session_state["pom_deleted_ok_flag"] = False

        # 🔮 MATERIALISE GRAPH
        # TAB1
        st.session_state["mkgc_config"] = configparser.ConfigParser()
        st.session_state["autoconfig_active_flag"] = False
        st.session_state["autoconfig_generated_ok_flag"] = False
        st.session_state["config_file_reset_ok_flag_tab1"] = False
        # TAB2
        st.session_state["mkgc_g_mappings_dict"] = {}
        st.session_state["manual_config_enabled_ok_flag"] = False
        st.session_state["ds_for_mkgcgc_saved_ok_flag"] = False
        st.session_state["ds_for_mkgcgc_removed_ok_flag"] = False
        st.session_state["configuration_for_mkgcgc_saved_ok_flag"] = False
        st.session_state["configuration_for_mkgcgc_removed_ok_flag"] = False
        st.session_state["additional_mapping_added_ok_flag"] = False
        st.session_state["key_mapping_uploader"] = str(uuid.uuid4())
        st.session_state["additional_mapping_for_mkgcgc_saved_ok_flag"] = False
        st.session_state["additional_mapping_removed_ok_flag"] = False
        st.session_state["config_file_reset_ok_flag_tab2"] = False
        # TAB3
        st.session_state["materialised_g_mapping_file"] = None
        st.session_state["materialised_g_mapping"] = Graph()
        st.session_state["graph_materialised_ok_flag"] = False

#______________________________________________________

#______________________________________________________
#Function to initialise page
def init_page():

    # Automatic detection of dark mode
    if "dark_mode_flag" not in st.session_state or st.session_state["dark_mode_flag"] is None:
        st.session_state["dark_mode_flag"] = streamlit_js_eval(js_expressions="window.matchMedia('(prefers-color-scheme: dark)').matches",
            key="dark_mode")

    # Sidebar logo
    dark_mode = False if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"] else True
    utils.render_sidebar_logo(dark_mode=dark_mode)

    # Import style
    style_container = st.empty()
    if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
        style_container.markdown(import_st_aesthetics(), unsafe_allow_html=True)
    else:
        style_container.markdown(import_st_aesthetics_dark_mode(), unsafe_allow_html=True)

    # Initialise session state variables
    init_session_state_variables()
#______________________________________________________


# PAGE: GLOBAL CONFIGURATION ===================================================
# PANNEL: SELECT MAPPING--------------------------------------------------------
#______________________________________________________
#Function to check whether a label is valid
def is_valid_label(label):

    if not label:
        return False

    valid_letters = ["a","b","c","d","e","f","g","h","i","j","k","l","m",
        "n","o","p","q","r","s","t","u","v","w","x","y","z",
        "A","B","C","D","E","F","G","H","I","J","K","L","M",
        "N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]

    valid_digits = ["0","1","2","3","4","5","6","7","8","9","_","-"]

    # disallow spaces
    if re.search(r"[ \t\n\r]", label):    # disallow spaces
        st.markdown(f"""<div class="error-message">
            ❌ <b> Invalid label. </b>
            <small>Please make sure it does not contain any spaces.</small>
        </div>""", unsafe_allow_html=True)
        return False

    # disallow unescaped characters
    if re.search(r"[<>\"{}|\\^`]", label):
        st.markdown(f"""<div class="error-message">
            ❌ <b> Invalid label. </b>
            <small>Please make sure it does not contain any invalid characters (&lt;&gt;"{{}}|\\^`).</small>
        </div>""", unsafe_allow_html=True)
        return False

    # warning if long
    inner_html = ""
    if len(label) > 20:
        st.markdown(f"""<div class="warning-message">
            ⚠️ A <b>shorter label</b> is recommended.
        </div>""", unsafe_allow_html=True)

    return True
#_______________________________________________________

#_______________________________________________________
# Function to check whether a label is valid with harder conditions
def is_valid_label_hard(label, display_option=True):

    if not label:
        return False

    valid_letters = ["a","b","c","d","e","f","g","h","i","j","k","l","m",
        "n","o","p","q","r","s","t","u","v","w","x","y","z",
        "A","B","C","D","E","F","G","H","I","J","K","L","M",
        "N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]

    valid_digits = ["0","1","2","3","4","5","6","7","8","9","_","-"]

    # disallow spaces
    if re.search(r"[ \t\n\r]", label):
        if display_option:
            st.markdown(f"""<div class="error-message">
                ❌ <b> Invalid label. </b>
                <small>Please make sure it does not contain any spaces.</small>
            </div>""", unsafe_allow_html=True)
        return False

    # allow only safe characters
    for letter in label:
        if letter not in valid_letters and letter not in valid_digits:
            if display_option:
                st.markdown(f"""<div class="error-message">
                    ❌ <b> Invalid label. </b>
                    <small>Please make sure it contains only safe characters (a-z, A-Z, 0-9, -, _).</small>
                </div>""", unsafe_allow_html=True)
            return False

    # disallow trailing puntuation
    if label.endswith("_") or label.endswith("-"):
        if display_option:
            st.markdown(f"""<div class="error-message">
                ❌ <b> Invalid label. </b>
                <small>Please make sure it does not end with puntuation.</small>
            </div>""", unsafe_allow_html=True)
        return False

    # warning if long
    inner_html = ""
    if len(label) > 20:
        if display_option:
            st.markdown(f"""<div class="warning-message">
                ⚠️ A <b>shorter label</b> is recommended.
            </div>""", unsafe_allow_html=True)
            inner_html += f"""A shorter label is recommended. """

    return True
#_______________________________________________________

#_______________________________________________________
# List of allowed mapping file formats
# HERE - Expand options, now reduced version
def get_g_mapping_file_formats_dict():

    allowed_format_dict = {"turtle": ".ttl",
        "ntriples": ".nt", "jsonld": ".jsonld"}

    return allowed_format_dict
#_______________________________________________________

#_______________________________________________________
# Function to empty all lists that store last added stuff
def empty_last_added_lists():
    st.session_state["last_added_ns_list"] = []
    st.session_state["last_added_tm_list"] = []
    st.session_state["last_added_sm_list"] = []
    st.session_state["last_added_pom_list"] = []
#_____________________________________________________

#_____________________________________________________
# Function to completely reset cache (last added dictionaries and ontology dictionaries)
# Mapping, data sources, ontologies and last added lists
def full_reset():

    # reset mapping
    st.session_state["g_mapping"] = Graph()
    st.session_state["g_label"] = ""

    # reset data sources
    st.session_state["db_connections_dict"] = {}
    st.session_state["db_connection_status_dict"] = {}
    st.session_state["sql_queries_dict"] = {}
    st.session_state["ds_files_dict"] = {}

    # reset ontology
    st.session_state["g_ontology_components_dict"] = {}
    st.session_state["g_ontology_components_tag_dict"] = {}
    st.session_state["g_ontology"] = Graph()

    # reset last added lists
    empty_last_added_lists()
#_____________________________________________________

#_______________________________________________________
# Function to format the suggested mapping label
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
# Function to load mapping from link
def load_mapping_from_link(url):

    g = Graph()

    try:
        g.parse(url, format="turtle")
        return g

    except Exception as e:
        st.markdown(f"""<div class="error-message">
            ❌ Failed to parse <b>mapping</b>.
            <small>Please check your URL and your mapping.</small>
        </div>""", unsafe_allow_html=True)
        return None
#_____________________________________________________

#_______________________________________________________
# Function to load mapping from file (f is a file object)
# This should work for all formats in get_g_mapping_file_formats_dict
# HERE - Check all formats work
def load_mapping_from_file(f):

    ext = os.path.splitext(f.name)[1].lower()  #file extension

    # pkl
    if ext == ".pkl":
        return pickle.load(f)

    # json
    elif ext in [".json", ".jsonld"]:
        text = f.read().decode("utf-8")
        return json.loads(text)

    # csv
    elif ext == ".csv":
        text = f.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        return [row for row in reader]

    # ttl, xml, nt, etc
    elif ext in [".ttl", ".rdf", ".xml", ".nt", ".n3", ".trig", ".trix"]:
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
                <small> Please, check your mapping.</small>
            </div>""", unsafe_allow_html=True)
            return False

    # error message
    else:
        st.markdown(f"""<div class="error-message">
            ❌ Unsupported file extension <b>{ext}</b>. # should not happen
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

    for s, p, o in st.session_state["g_mapping"]:
        if isinstance(s, URIRef):
            if p in [RML.logicalSource, RML.subjectMap, RML.predicateObjectMap, RML.objectMap]:
                base_ns = split_uri(s)[0]
                break

    prefix = "base"
    for pr, ns in st.session_state["g_mapping"].namespaces():
        if str(base_ns) == str(ns):
            prefix = pr
            break

    return [prefix, base_ns]
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


# PANNEL: CONFIGURE NAMESPACES -------------------------------------------------
#_____________________________________________________
# Function to get the default base iri for the base components
def get_default_base_ns():

    return ["map3x", URIRef("http://3xmap.org/mapping/")]
#_____________________________________________________

#_____________________________________________________
# Funtion to get dictionary with default namespaces
# Default namespaces are automatically added to the g namespace manager by rdflib
# For clarity, we bind them and don't allow to remove
# DO NOT MODIFY LIST
def get_default_ns_dict():

    default_ns_dict = {
        "brick": URIRef("https://brickschema.org/schema/Brick#"),
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
#_____________________________________________________

#_____________________________________________________
# Function to get dictionary with predefined namespaces so that they can be easily bound
# LIST CAN BE CHANGED
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
    filtered_ns_dict = {}
    for k, v in predefined_ns_dict.items():
        if v not in default_dict.values():
            filtered_ns_dict[k] = v

    predefined_ns_dict = filtered_ns_dict

    return predefined_ns_dict
#_____________________________________________________

#_____________________________________________________
# Funtion to get dictionary {prefix: namespace} bound in a graph g
def get_g_ns_dict(g):

    ns_dict = dict(g.namespace_manager.namespaces())

    return ns_dict
#_____________________________________________________

#_____________________________________________________
# Funtion to get dictionary {prefix: namespace} used in a mapping g
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
# Duplicated prefixes will be renamed, duplicated namespaces will be overwritten
def bind_namespace(prefix, namespace):

    mapping_ns_dict = get_g_ns_dict(st.session_state["g_mapping"])

    # if namespace already bound to a different prefix, unbind it
    if URIRef(namespace) in mapping_ns_dict.values():
        old_prefix_list = [k for k, v in mapping_ns_dict.items() if v == URIRef(namespace)]
        for old_prefix in old_prefix_list:
            if old_prefix in st.session_state["last_added_ns_list"]:
                st.session_state["last_added_ns_list"].remove(old_prefix)
        unbind_namespaces(old_prefix_list)

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

#__________________________________________________________
# Function to bind namespaces to g mapping without overwriting
# Duplicated prefixes will be renamed, duplicated namespaces will be ignored
def bind_namespace_wo_overwriting(prefix, namespace):

    mapping_ns_dict = get_g_ns_dict(st.session_state["g_mapping"])

    if not namespace in mapping_ns_dict.values():

        # bind the new namespace
        st.session_state["g_mapping"].bind(prefix, namespace)

        # find actual prefix (it might have been auto-renamed)
        actual_prefix = None
        for pr, ns in st.session_state["g_mapping"].namespace_manager.namespaces():
            if str(ns) == namespace:
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

    if isinstance(iri, URIRef):
        iri = str(iri)

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

    # must end with a recognized delimiter (can be switched off)
    if delimiter_ending and not iri[-1] in ("/", "#", ":"):
        return False

    return True
#_________________________________________________________

#_________________________________________________________
#Function to check whether a prefix is valid
def is_valid_prefix(prefix):

    if not prefix:
        return False

    valid_letters = ["a","b","c","d","e","f","g","h","i","j","k","l","m",
        "n","o","p","q","r","s","t","u","v","w","x","y","z",
        "A","B","C","D","E","F","G","H","I","J","K","L","M",
        "N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]

    valid_digits = ["0","1","2","3","4","5","6","7","8","9","_"]

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
        inner_html += f"""A shorter prefix is recommended. """
    if prefix.lower() != prefix:
        inner_html += f"""The use of uppercase letters is discouraged."""
    if inner_html:
        st.markdown(f"""<div class="warning-message">
            ⚠️ {inner_html}
        </div>""", unsafe_allow_html=True)

    return True
#_________________________________________________________

#_________________________________________________________
# Function to check whether any prefixes of a ns dictionary are not bound in mapping
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
#Function to get previsualisation message of mapping/ontology/predefined namespaces
# and when unbinding namespaces
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
# Function to get warning messages when binding mapping/ontology/predefined namespaces
# and when unbinding namespaces
def get_ns_warning_message(ns_to_bind_list):

    mapping_ns_dict = get_g_ns_dict(st.session_state["g_mapping"])
    already_used_prefix_list = []
    for pr in ns_to_bind_list:
        if pr in mapping_ns_dict:
            already_used_prefix_list.append(pr)

    if len(already_used_prefix_list) == 1:
        st.markdown(f"""<div class="warning-message">
                    ⚠️ Prefix <b>{utils.format_list_for_markdown(already_used_prefix_list)}</b> is already in use<small>
                    and will be auto-renamed with a numeric suffix.</small>
            </div>""", unsafe_allow_html=True)

    elif already_used_prefix_list:
        st.markdown(f"""<div class="warning-message">
                    ⚠️ Prefixes <b>{utils.format_list_for_markdown(already_used_prefix_list)}</b> are already in use
                    <small>and will be auto-renamed with a numeric suffix.</small>
            </div>""", unsafe_allow_html=True)
#_________________________________________________


# PANNEL: SAVE MAPPING----------------------------------------------------------
#_________________________________________________
#Funtion to create the list that stores the state of the project
# project_state_list
# 0. [g_label, g_mapping]     1. g_ontology_components_dict      2. base_ns_dict
# 3. db_connections_dict       4. db_connection_status_dict
# 5. ds_files_dict                6. sql_queries_dict
def save_project_state():

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
    project_state_list.append(st.session_state["sql_queries_dict"])
    project_state_list.append(st.session_state["g_mapping_source_cache"])
    project_state_list.append(st.session_state["original_g_size_cache"])
    project_state_list.append(st.session_state["original_g_mapping_ns_dict"])

    return project_state_list
#______________________________________________________

#_________________________________________________
#Funtion to retrieve the project state
def retrieve_project_state(project_state_list):

    st.session_state["g_label"] = project_state_list[0]
    st.session_state["g_mapping"] = project_state_list[1]
    st.session_state["g_ontology"] = project_state_list[2]
    st.session_state["g_ontology_components_dict"] = project_state_list[3]
    st.session_state["g_ontology_components_tag_dict"] = project_state_list[4]
    st.session_state["base_ns"] = project_state_list[5]
    st.session_state["db_connections_dict"] = project_state_list[6]
    st.session_state["db_connection_status_dict"] = project_state_list[7]
    st.session_state["ds_files_dict"] = project_state_list[8]
    st.session_state["sql_queries_dict"] = project_state_list[9]
    st.session_state["g_mapping_source_cache"] = project_state_list[10]
    st.session_state["original_g_size_cache"] = project_state_list[11]
    st.session_state["original_g_mapping_ns_dict"] = project_state_list[12]

    for conn in st.session_state["db_connection_status_dict"]:
        update_db_connection_status_dict(conn)
#______________________________________________________

#_________________________________________________
#Funtion to check whether a filename is valid
def is_valid_filename(filename):  #HEREIGO

    excluded_characters = r"[\\/:*?\"<>| ]"
    windows_reserved_names = ["CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]

    # no trailing dot
    if filename.endswith("."):
        st.markdown(f"""<div class="error-message">
            ❌ <b>Trailing "."</b> in filename.
            <small> Please, remove it.</small>
        </div>""", unsafe_allow_html=True)
        return False

    # no dot
    elif "." in filename:
        st.markdown(f"""<div class="error-message">
                ❌ The filename seems to include an <b>extension</b>.
                <small> Please, remove it.</b>
            </div>""", unsafe_allow_html=True)
        return False

    # disallow forbidden characters
    elif re.search(excluded_characters, filename):
        st.markdown(f"""<div class="error-message">
            ❌ <b>Forbidden character</b> in filename.
            <small> Please, pick a valid filename.</small>
        </div>""", unsafe_allow_html=True)
        return False

    # disallow windows reserved names
    else:
        for item in windows_reserved_names:
            if item == os.path.splitext(filename)[0].upper():
                st.markdown(f"""<div class="error-message">
                    ❌ <b>Reserved filename.</b><br>
                    <small>Please, pick a different filename.</small>
                </div>""", unsafe_allow_html=True)
                return False
                break

    return True
#______________________________________________________


# PAGE: ONTOLOGIES==============================================================
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
# Function to parse an ontology to an initially empty graph
@st.cache_resource
def parse_ontology(source):

    # If source is a file-like object
    if isinstance(source, IOBase):
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

        # Try auto-detecting format
        try:
            g = Graph()
            g.parse(data=content, format=None)
            if len(g) != 0:
                return [g, "auto"]
        except:
            pass
        return [Graph(), None]

    # If source is a string (URL or raw RDF)
    for fmt in ["xml", "turtle", "jsonld", "ntriples", "trig", "trix"]:
        g = Graph()
        try:
            g.parse(source, format=fmt)
            if len(g) != 0:
                return [g, fmt]
        except:
            continue

    # Try auto-detecting format
    try:
        g = Graph()
        g.parse(source, format=None)
        if len(g) != 0:
            return [g, "auto"]
    except:
        pass

    # Try downloading the content and parsing from raw bytes
    for fmt in ["xml", "turtle", "jsonld", "ntriples", "trig", "trix"]:
        try:
            response = requests.get(source)
            g = Graph()
            g.parse(data=response.content, format=fmt)  # use raw bytes
            if len(g) != 0:
                return [g, fmt]
        except:
            continue

    # Final fallback: auto-detect from downloaded content
    try:
        response = requests.get(source)
        g = Graph()
        g.parse(data=response.content, format=None)
        if len(g) != 0:
            return [g, "auto"]
    except:
        pass

    return [Graph(), "error"]
#______________________________________________________

#______________________________________________________
#Function to check whether an ontology is valid
def is_valid_ontology(g):

    try:
        # check for presence of OWL or RDFS classes
        classes = list(g.subjects(RDF.type, OWL.Class)) + list(g.subjects(RDF.type, RDFS.Class))
        properties = (list(g.subjects(RDF.type, RDF.Property)) + list(g.subjects(RDF.type, OWL.DatatypeProperty)) +
            list(g.subjects(RDF.type, OWL.ObjectProperty)) + list(g.subjects(RDF.type, OWL.AnnotationProperty)))
        return bool(classes or properties)  # consider it valid if it defines at least one class or property

    except:
        return False
#______________________________________________________

#______________________________________________________
#Function to get the human-readable name of an ontology
def get_ontology_human_readable_name(g, source_link=None, source_file=None):

    g_ontology_iri = next(g.subjects(RDF.type, OWL.Ontology), None)

    if g_ontology_iri:     # first option: look for ontology self-contained label
        g_ontology_label = (
            g.value(g_ontology_iri, RDFS.label) or
            g.value(g_ontology_iri, DC.title) or
            g.value(g_ontology_iri, DCTERMS.title) or
            split_uri(g_ontology_iri)[1])    # look for ontology label; if there isnt one just select the ontology iri
        return g_ontology_label

    elif source_link:               # if ontology is not self-labeled, use source as label (link)
        try:
            return split_uri(source_link)[1]
        except:
            return source_link.rstrip('/').split('/')[-1]

    elif source_file:               # if ontology is not self-labeled, use source as label (file)
        return os.path.splitext(source_file.name)[0]

    else:                                 # if no source is given, auto-label using subject of first triple (if it is iri)
        for s in g.subjects(None, None):
            if isinstance(s, URIRef):
                return "Auto-label: " + split_uri(s)[1]

    return "Unlabelled ontology"  #if nothing works
#______________________________________________________

#______________________________________________________
#Function to get the human-readable name of an ontology
def get_ontology_tag(g_label):

    forbidden_tags_beginning = [f"ns{i}" for i in range(1, 10)]

    g = st.session_state["g_ontology_components_dict"][g_label]
    g_ontology_iri = next(g.subjects(RDF.type, OWL.Ontology), None)

    if g_ontology_iri:
        prefix = g.namespace_manager.compute_qname(g_ontology_iri)[0]
        if not any(prefix.startswith(tag) for tag in forbidden_tags_beginning):
            return prefix   # return prefix of the base ns

    return g_label[:4]    # return 4 first characters of ont name
#______________________________________________________

#______________________________________________________
# Function to get the human-readable name of an ontology
# Ensures uniqueness by adding numeric suffix
def get_unique_ontology_tag(g_label):

    tag = get_ontology_tag(g_label)

    if not tag in st.session_state["g_ontology_components_tag_dict"].values():
        return tag

    i = 1
    while f"{tag}{i}" in st.session_state["g_ontology_components_tag_dict"].values():
        i += 1

    return f"{tag}{i}"
#______________________________________________________

#______________________________________________________
#Function to get all allowed formats for ontology files
def get_g_ontology_file_formats_dict():

    allowed_format_dict = {"owl": ".owl", "turtle": ".ttl", "longturtle": ".ttl", "n3": ".n3",
    "ntriples": ".nt", "nquads": "nq", "trig": ".trig", "jsonld": ".jsonld",
    "xml": ".xml", "pretty-xml": ".xml", "trix": ".trix"}

    return allowed_format_dict
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
def get_candidate_ontology_info_messages(g, g_label):

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
                {st.session_state["g_ontology_from_link_candidate_label"]}</b>
                <small>(parsed successfully with format
                <b>{st.session_state["g_ontology_from_link_candidate_fmt"]}</b>).</small>"""

    return [valid_ontology_flag, success_html, warning_html, error_html]

#______________________________________________________


# PAGE: SQL DATABASES===========================================================
#______________________________________________________
# Funtion to get jdbc str from connection
def get_jdbc_str(conn):

    if conn in st.session_state["db_connections_dict"]:
        [engine, host, port, database, user, password] = st.session_state["db_connections_dict"][conn]

        if engine == "Oracle":
            jdbc_str = f"jdbc:oracle:thin:@{host}:{port}:{database}"
        elif engine == "SQL Server":
            jdbc_str = f"jdbc:sqlserver://{host}:{port};databaseName={database}"
        elif engine == "PostgreSQL":
            jdbc_str = f"jdbc:postgresql://{host}:{port}/{database}"
        elif engine == "MySQL":
            jdbc_str = f"jdbc:mysql://{host}:{port}/{database}"
        elif engine =="MariaDB":
            jdbc_str = f"jdbc:mariadb://{host}:{port}/{database}"
        else:
            return None

    else:
        return None

    return jdbc_str
#______________________________________________________

#_________________________________________________
# Funtion to get db_url string
def get_db_url_str(conn):

    [engine, host, port, database, user, password] = st.session_state["db_connections_dict"][conn]

    if engine == "Oracle":
        db_url_str = f"oracle+oracledb://{user}:{password}@{host}:{port}/{database}"
    elif engine == "SQL Server":
        db_url_str = f" mssql+pymssql://{user}:{password}@{host}:{port}/{database}"
    elif engine == "PostgreSQL":
        db_url_str = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"
    elif engine == "MySQL":
        db_url_str = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    elif engine =="MariaDB":
        db_url_str = f"mariadb+pymysql://{user}:{password}@{host}:{port}/{database}"
    else:
        return None

    return db_url_str

#_________________________________________________
#______________________________________________________
# Funtion to make a connection to a database
def make_connection_to_db(connection_label):
    engine, host, port, database, user, password = st.session_state["db_connections_dict"][connection_label]
    timeout = 3

    if engine == "PostgreSQL":
        conn = psycopg.connect(host=host, port=port,
            dbname=database, user=user, password=password,
            connect_timeout=timeout)

    elif engine in ("MySQL", "MariaDB"):
        conn = pymysql.connect(host=host, port=int(port), user=user,
            password=password, database=database, connect_timeout=timeout)

    elif engine == "Oracle":
        conn = oracledb.connect(user=user, password=password,
            dsn=f"{host}:{port}/{database}", timeout=timeout)

    elif engine == "SQL Server":
        conn = pyodbc.connect(
            f"DRIVER={{SQL Server}};"
            f"SERVER={host},{port};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password}", timeout=timeout)

    else:
        conn = None

    return conn
#______________________________________________________

#______________________________________________________
# Funtion to update the connection status dict
def update_db_connection_status_dict(conn_label):

    try:
        conn = utils.make_connection_to_db(conn_label)
        if conn:
            conn.close()
        st.session_state["db_connection_status_dict"][conn_label] = ["✔️", ""]

    except Exception as e:
        st.session_state["db_connection_status_dict"][conn_label] = ["🚫", e]

#______________________________________________________

#________________________________________________________
# Dictionary with default ports for the different engines
def get_default_ports():

    default_ports_dict = {"PostgreSQL": 5432, "MySQL": 3306,
    "MariaDB": 3306, "SQL Server": 1433, "Oracle": 1521}

    return default_ports_dict
#______________________________________________________

#________________________________________________________
# Funtion to check connection to a database
def try_connection(db_connection_type, host, port, database, user, password):

    if db_connection_type == "PostgreSQL":
        try:
            conn = psycopg.connect(host=host, port=port,
                dbname=database, user=user, password=password)
            conn.close() # optional: close immediately or keep open for queries
            return True

        except psycopg.OperationalError as e:
            st.markdown(f"""<div class="error-message">
                ❌ <b>Connection failed.</b><br>
                <small><b>Full error</b>: {e.args[0]} </small>
            </div>""", unsafe_allow_html=True)
            st.write("")
            return False

        except Exception as e:
            st.markdown(f"""<div class="error-message">
                ❌ <b>Unexpected error.</b><br>
                <small><b>Full error</b>: {str(e)} </small>
            </div>""", unsafe_allow_html=True)
            st.write("")
            return False

    if db_connection_type in ("MySQL", "MariaDB"):
        try:
            conn = pymysql.connect(host=host, port=int(port), user=user,
                password=password, database=database)
            conn.close() # optional: close immediately or keep open for queries
            return True

        except pymysql.MySQLError as e:
            st.markdown(f"""<div class="error-message">
                ❌ <b>Connection failed.</b><br>
                <small><b>Full error</b>: {e.args[0]} </small>
            </div>""", unsafe_allow_html=True)
            st.write("")
            return False

        except Exception as e:
            st.markdown(f"""<div class="error-message">
                ❌ <b>Unexpected error.</b><br>
                <small><b>Full error</b>: {str(e)} </small>
            </div>""", unsafe_allow_html=True)
            st.write("")
            return False

    if db_connection_type == "Oracle":
        try:
            conn = oracledb.connect(user=user, password=password,
                dsn=f"{host}:{port}/{database}")
            conn.close()  # optional: close immediately or keep open for queries
            return True

        except oracledb.OperationalError as e:
            st.markdown(f"""<div class="error-message">
                ❌ <b>Connection failed.</b><br>
                <small><b>Full error</b>: {e.args[0]} </small>
            </div>""", unsafe_allow_html=True)
            st.write("")
            return False

        except Exception as e:
            st.markdown(f"""<div class="error-message">
                ❌ <b>Unexpected error.</b><br>
                <small><b>Full error</b>: {str(e)} </small>
            </div>""", unsafe_allow_html=True)
            st.write("")
            return False

    if db_connection_type == "SQL Server":
        try:
            conn = pyodbc.connect(
                f"DRIVER={{SQL Server}};"
                f"SERVER={host},{port};"
                f"DATABASE={database};"
                f"UID={user};"
                f"PWD={password}")
            conn.close()
            return True

        except pyodbc.OperationalError as e:
            st.markdown(f"""<div class="error-message">
                ❌ <b>Connection failed.</b><br>
                <small><b>Full error</b>: {e.args[0]} </small>
            </div>""", unsafe_allow_html=True)
            st.write("")
            return False

        except Exception as e:
            st.markdown(f"""<div class="error-message">
                ❌ <b>Unexpected error.</b><br>
                <small><b>Full error</b>: {str(e)} </small>
            </div>""", unsafe_allow_html=True)
            st.write("")
            return False
#______________________________________________________

#________________________________________________________
# Funtion to get all tables in a database
def get_tables_from_db(engine, cur, database):

    if engine == "PostgreSQL":
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
        """)

    elif engine in ("MySQL", "MariaDB"):
        cur.execute(f"""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = '{database}' AND table_type = 'BASE TABLE';
        """)

    elif engine == "Oracle":
        cur.execute("""
            SELECT table_name
            FROM all_tables
            WHERE owner NOT IN (
                'SYS', 'SYSTEM', 'XDB', 'CTXSYS', 'MDSYS', 'ORDDATA', 'ORDSYS',
                'OUTLN', 'DBSNMP', 'APPQOSSYS', 'WMSYS', 'OLAPSYS', 'EXFSYS',
                'DVSYS', 'GGSYS', 'OJVMSYS', 'LBACSYS', 'AUDSYS',
                'REMOTE_SCHEDULER_AGENT')""")  # filter out system tables

    elif engine == "SQL Server":
        cur.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
              AND TABLE_CATALOG = ?
        """, (database,))

    else:
        pass
#______________________________________________________



# HEREIGO - REFACTORING

#________________________________________________________
# Funtion to get the name of the folder to save large files
def get_ds_folder_name():

        return "data_sources"
#________________________________________________________

#________________________________________________________
# Funtion to get the dictionary of the TriplesMaps
#{tm_label: tm}
def get_tm_dict():

    if st.session_state["g_label"]:

        tm_dict = {}
        triples_maps = list(st.session_state["g_mapping"].subjects(RML.logicalSource, None))

        for tm in triples_maps:
            tm_label = split_uri(tm)[1]
            tm_dict[tm_label] = tm
        return tm_dict

    else:
        return {}
#________________________________________________________

#_________________________________________________
# Funtion to get the logical soruce of a TriplesMap
def get_ls(tm_label):
    tm_dict = get_tm_dict()
    tm_iri = tm_dict[tm_label]
    ls = st.session_state["g_mapping"].value(subject=tm_iri, predicate=RML.logicalSource)
    if isinstance(ls, URIRef):
        try:
            ls_label = split_uri(ls)[1]
        except:
            ls_label = ls
    elif isinstance(ls, BNode):
        ls_label = "_:" + str(ls)[:7] + "..."
    return ls_label
#_________________________________________________

#_________________________________________________
# Funtion to get the logical source of a TriplesMap
def get_ds(tm_label):
    tm_dict = get_tm_dict()
    tm_iri = tm_dict[tm_label]
    ls = st.session_state["g_mapping"].value(subject=tm_iri, predicate=RML.logicalSource)
    ds = st.session_state["g_mapping"].value(subject=ls, predicate=RML.source)
    return ds
#_________________________________________________

#_________________________________________________________________________________
# Function to completely remove a triplesmap
# Remove primary and secondary triples, but dont remove any triples that are used by another triplesmap
def remove_triplesmap(tm_label):

    tm_dict = get_tm_dict()
    tm_iri = tm_dict[tm_label]   #get tm iri
    g = st.session_state["g_mapping"]  #for convenience

    # remove ls if not reused
    logical_source = g.value(subject=tm_iri, predicate=RML.logicalSource)
    if logical_source:
        ls_reused = any(s != tm_iri for s, p, o in g.triples((None, RML.logicalSource, logical_source)))
        if not ls_reused:
            g.remove((logical_source, None, None))

    # remove sm if not reused
    subject_map = g.value(subject=tm_iri, predicate=RML.subjectMap)
    if subject_map:
        sm_reused = any(s != tm_iri for s, p, o in g.triples((None, RML.subjectMap, subject_map)))
        if not sm_reused:
            g.remove((subject_map, None, None))

    # remove all associated pom (and om)
    pom_iri_list = list(g.objects(subject=tm_iri, predicate=RML.predicateObjectMap))
    for pom_iri in pom_iri_list:
        om_to_delete = st.session_state["g_mapping"].value(subject=pom_iri, predicate=RML.objectMap)
        st.session_state["g_mapping"].remove((pom_iri, None, None))
        st.session_state["g_mapping"].remove((om_to_delete, None, None))

    g.remove((tm_iri, None, None))   # remove tm triple
#______________________________________________________

#______________________________________________________
# Function get the column list of the data source of a tm
# It also gives warning and info messages
def get_column_list_and_give_info(tm_iri):

    ls_iri = next(st.session_state["g_mapping"].objects(tm_iri, RML.logicalSource), None)
    ds = str(next(st.session_state["g_mapping"].objects(ls_iri, RML.source), None))
    reference_formulation = next(st.session_state["g_mapping"].objects(ls_iri, QL.referenceFormulation), None)
    query_as_ds = next(st.session_state["g_mapping"].objects(ls_iri, RML.query), None)
    table_name_as_ds = next(st.session_state["g_mapping"].objects(ls_iri, RML.tableName), None)

    inner_html = ""
    column_list_ok_flag = False

    jdbc_dict = {}
    for conn in st.session_state["db_connections_dict"]:
        jdbc_str = get_jdbc_str(conn)
        jdbc_dict[conn] = jdbc_str

    if ds in st.session_state["ds_files_dict"]:   # saved non-sql data source

        df = utils.read_tab_file(ds)
        column_list = df.columns.tolist()

        inner_html = f"""🛢️ The data source is <b>{ds}</b>."""
        column_list_ok_flag = True

    elif ds in jdbc_dict.values():        # saved sql data source

        for i_conn, i_jdbc_str in jdbc_dict.items():
            if  i_jdbc_str == ds:
                [engine, host, port, i_database, user, password] = st.session_state["db_connections_dict"][conn]
                conn_label = i_conn
                jdbc_str = i_jdbc_str
                database = i_database
                break


        if query_as_ds:
            try:
                conn = utils.make_connection_to_db(conn_label)
                cur = conn.cursor()
                cur.execute(query_as_ds)
                column_list = [description[0] for description in cur.description]
                conn.close() # optional: close immediately or keep open for queries
                if not column_list:
                    inner_html = f"""⚠️ <b>No columns found</b> in logical source query.
                    <small>Go to <b>📊 SQL Databases</b> page to fix it.
                    <b>Manual reference entry is discouraged.</b></small>"""

                else:
                    inner_html = f"""📊 The data source is the database <b style="color:#F63366;">{database}</b>.<br>
                        <small>🔌 {conn_label} → <b>{jdbc_str}</b></small>"""
                    column_list_ok_flag = True

            except:
                inner_html = f"""⚠️ Connection to database <b>{database}</b> failed.
                    <small>Check <b>📊 SQL Databases</b> page to fix it.
                    <b>Manual reference entry is discouraged.</b></small>"""
                column_list = []

        elif table_name_as_ds:
            try:
                conn = utils.make_connection_to_db(conn_label)
                cur = conn.cursor()

                cur.execute(f"SELECT * FROM {table_name_as_ds} LIMIT 0")
                column_list = [desc[0] for desc in cur.description]

                conn.close()

                if not column_list:
                    inner_html = f"""⚠️ <b>{table_name_as_ds}</b> has no columns.
                        <small>Check <b>📊 SQL Databases</b> page to fix it.
                        <b>Manual reference entry is discouraged.</b></small>"""

                else:
                    inner_html = f"""📊 The data source is the database <b style="color:#F63366;">{database}</b>.<br>
                             <small>🔌 {conn_label} → <b>{jdbc_str}</b></small>"""
                    column_list_ok_flag = True

            except:
                inner_html = f"""⚠️ <b>Connection failed</b> for table <b>{table_name_as_ds}</b>.
                    <small>Check it in <b>📊 SQL Databases</b> page to enable column detection.
                    <b>Manual reference entry is discouraged.</b></small>"""
                column_list = []

        else:
            inner_html = f"""⚠️ Missing <code>RML.query</code> or <code>RML.tableName</code>.
                <small>Check the <b>Logical Source</b> to enable column detection.
                <b>Manual reference entry is discouraged.</b></small>"""
            column_list = []

    elif query_as_ds:    # try to look for the columns in the query
        parsed = sqlglot.parse_one(query_as_ds)
        column_list = [str(col) for col in parsed.find_all(sqlglot.expressions.Column)]

        if column_list:
            inner_html = f"""⚠️ <b>{ds}</b> is unavailable. Columns were inferred from the logical source query.
                <small><b>Connecting to the database</b> is still recommended.</small>"""
        else:
            inner_html = f"""⚠️ <b>{ds}</b> is unavailable.
                <small>Load it via <b>📊 SQL Databases</b> page to enable column detection.
                <b>Manual reference entry is discouraged.</b></small>"""


    else:                                                           # data source not saved
        if reference_formulation == QL.SQL:
            inner_html = f"""⚠️ <b>{ds}</b> is unavailable.
                <small>Connect via <b>📊 SQL Databases</b> page to enable column detection.
                <b>Manual reference entry is discouraged.</b></small>"""

        else:
            inner_html = f"""⚠️ <b>{ds}</b> is unavailable.
                <small>Load it via <b>📊 SQL Databases</b> page to enable column detection.
                <b>Manual reference entry is discouraged.</b></small>"""
        column_list = []

    return [column_list, column_list_ok_flag, inner_html]
#________________________________________________________

#______________________________________________________
# Function get the column list of the data source of a tm
def get_column_list(tm_iri):

    ls_iri = next(st.session_state["g_mapping"].objects(tm_iri, RML.logicalSource), None)
    ds = str(next(st.session_state["g_mapping"].objects(ls_iri, RML.source), None))
    reference_formulation = next(st.session_state["g_mapping"].objects(ls_iri, QL.referenceFormulation), None)
    query_as_ds = next(st.session_state["g_mapping"].objects(ls_iri, RML.query), None)
    table_name_as_ds = next(st.session_state["g_mapping"].objects(ls_iri, RML.tableName), None)

    jdbc_dict = {}
    for conn in st.session_state["db_connections_dict"]:
        [engine, host, port, database, user, password] = st.session_state["db_connections_dict"][conn]
        if engine == "Oracle":
            jdbc_str = f"jdbc:oracle:thin:@{host}:{port}:{database}"
            jdbc_dict[conn] = jdbc_str
        elif engine == "SQL Server":
            jdbc_str = f"jdbc:sqlserver://{host}:{port};databaseName={database}"
            jdbc_dict[conn] = jdbc_str
        elif engine == "PostgreSQL":
            jdbc_str = f"jdbc:postgresql://{host}:{port}/{database}"
            jdbc_dict[conn] = jdbc_str
        elif engine == "MySQL":
            jdbc_str = f"jdbc:mysql://{host}:{port}/{database}"
            jdbc_dict[conn] = jdbc_str
        elif engine =="MariaDB":
            jdbc_str = f"jdbc:mariadb://{host}:{port}/{database}"
            jdbc_dict[conn] = jdbc_str

    if ds in st.session_state["ds_files_dict"]:   # saved non-sql data source

        df = utils.read_tab_file(ds)
        column_list = df.columns.tolist()


    elif ds in jdbc_dict.values():        # saved sql data source

        for i_conn, i_jdbc_str in jdbc_dict.items():
            if  i_jdbc_str == ds:
                [engine, host, port, i_database, user, password] = st.session_state["db_connections_dict"][conn]
                conn_label = i_conn
                jdbc_str = i_jdbc_str
                database = i_database
                break


        if query_as_ds:
            try:
                conn = utils.make_connection_to_db(conn_label)
                cur = conn.cursor()
                cur.execute(query_as_ds)
                column_list = [description[0] for description in cur.description]
                conn.close() # optional: close immediately or keep open for queries

            except:
                column_list = []

        elif table_name_as_ds:
            try:
                conn = utils.make_connection_to_db(conn_label)
                cur = conn.cursor()
                cur.execute(f"SELECT * FROM {table_name_as_ds} LIMIT 0")
                column_list = [desc[0] for desc in cur.description]
                conn.close()


            except:
                column_list = []

        else:
            column_list = []

    elif query_as_ds:    # try to look for the columns in the query
        parsed = sqlglot.parse_one(query_as_ds)
        column_list = [str(col) for col in parsed.find_all(sqlglot.expressions.Column)]


    else:                                                           # data source not saved
        column_list = []

    return column_list
#________________________________________________________


#________________________________________________________
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
        tm_label = split_uri(tm)[1]
        sm_iri = st.session_state["g_mapping"].value(tm, RML.subjectMap)

        template = st.session_state["g_mapping"].value(sm_iri, RML.template)
        constant = st.session_state["g_mapping"].value(sm_iri, RML.constant)
        reference = st.session_state["g_mapping"].value(sm_iri, RML.reference)

        sm_id_iri = None
        sm_type = None
        sm_id_label = None

        if sm_iri:

            if isinstance(sm_iri, URIRef):
                sm_label = split_uri(sm_iri)[1]
            elif isinstance(sm_iri, BNode):
                sm_label = "_:" + str(sm_iri)[:7] + "..."
            else:
                sm_label = "Unlabelled"

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
#___________________________________________

#______________________________________________
# Funtion to get list of datatypes
def get_datatypes_dict():

    # datatype_list = ["Select datatype", "Natural language tag", "xsd:string",
    #     "xsd:integer", "xsd:decimal", "xsd:float", "xsd:double",
    #     "xsd:boolean", "xsd:date", "xsd:dateTime", "xsd:time",
    #     "xsd:anyURI", "rdf:XMLLiteral", "rdf:HTML", "rdf:JSON"]

    datatype_dict = {"Select datatype" : "", "Natural language tag": "",
        "xsd:string": XSD.string, "xsd:integer": XSD.integer,
        "xsd:decimal": XSD.decimal, "xsd:float": XSD.float,
        "xsd:double": XSD. double, "xsd:boolean": XSD.boolean,
        "xsd:date": XSD.date, "xsd:dateTime": XSD.dateTime,
        "xsd:time": XSD.time, "xsd:anyURI": XSD.anyURI,
        "rdf:XMLLiteral": XSD.XMLLiteral, "rdf:HTML": RDF.HTML,
        "rdf:JSON": RDF.JSON}


    return datatype_dict
#______________________________________________

#______________________________________________
# Funtion to get list of language tags
def get_language_tags_list():

    language_tags_list = ["Select language tag", "en", "es", "fr", "de", "zh",
        "ja", "pt-BR", "en-US", "ar", "ru", "hi", "zh-Hans", "sr-Cyrl"]

    return language_tags_list
#______________________________________________

#________________________________________________________
# Funtion to get the dictionary of the Predicate-Object Maps
# {pom_iri: [LIST]}
# the keys are a list of:
# 0. tm    1. tm_label
# 2. pom label     3. predicate iri     4. predicate label
# 5. om label      6. om type (template, constant or reference)
# 7. om_id_iri      # 8. om_id_label    (info on the id)
def get_pom_dict():

    pom_dict = {}
    pom_list = list(st.session_state["g_mapping"].objects(None, RML.predicateObjectMap))

    for pom_iri in pom_list:

        tm_iri = next(st.session_state["g_mapping"].subjects(RML.predicateObjectMap, pom_iri), None)
        tm_label = split_uri(tm_iri)[1]
        predicate = st.session_state["g_mapping"].value(pom_iri, RML.predicate)
        om_iri = st.session_state["g_mapping"].value(pom_iri, RML.objectMap)

        template = st.session_state["g_mapping"].value(om_iri, RML.template)
        constant = st.session_state["g_mapping"].value(om_iri, RML.constant)
        reference = st.session_state["g_mapping"].value(om_iri, RML.reference)

        pom_id_iri = None
        pom_type = None
        pom_id_label = None

        if isinstance(pom_iri, URIRef):
            pom_label = split_uri(pom_iri)[1]
        elif isinstance(pom_iri, BNode):
            pom_label = "_:" + str(pom_iri)[:7] + "..."
        else:
            pom_label = "Unlabelled"

        if isinstance(om_iri, URIRef):
            om_label = split_uri(om_iri)[1]
        elif isinstance(om_iri, BNode):
            om_label = "_:" + str(om_iri)[:7] + "..."
        else:
            om_label = "Unlabelled"

        try:
            predicate_label = split_uri(predicate)[1]
        except:
            predicate_label = ""

        if template:
            om_type = "template"
            om_id_iri = str(template)
            matches = re.findall(r"{([^}]+)}", template)   #splitting template is not so easy but we try
            if matches:
                om_id_label = str(matches[-1])
            else:
                om_id_label = str(template)

        elif constant:
            om_type = "constant"
            om_id_iri = str(constant)
            if isinstance(constant, URIRef):
                om_id_label = str(split_uri(constant)[1])
            else:
                om_id_label = constant

        elif reference:
            om_type = "reference"
            om_id_iri = str(reference)
            om_id_label = str(reference)

        else:
            om_type = "None"
            om_id_iri = ""
            om_id_label = ""

        pom_dict[pom_iri] = [tm_iri, tm_label, pom_label, predicate, predicate_label, om_label, om_type, om_id_iri, om_id_label]

    return pom_dict
#___________________________________________


#_________________________________________________
# Funtion to get the allowed format for the data sources
def get_ds_allowed_tab_formats():

    allowed_tab_formats_list = [".csv", ".tsv", ".xls",
    ".xlsx", ".parquet", ".feather", ".orc", ".dta",
    ".sas7bdat", ".sav", ".ods"]

    return allowed_tab_formats_list
#_________________________________________________

#_________________________________________________
# Funtion to read tabular data
def read_tab_file(filename):

    file = st.session_state["ds_files_dict"][filename]
    file_format = filename.split(".")[-1]

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

    else:
        read_content = ""   # should not occur

    file.seek(0)

    return read_content
#_________________________________________________

#_________________________________________________
# Funtion to read tabular data
# for files that are not yet saved
# HERE - Leave only this one and change name
def read_tab_file_unsaved(file):

    filename = file.name
    file_format = filename.split(".")[-1]

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

    else:
        read_content = ""   # should not occur

    file.seek(0)

    return read_content
#_________________________________________________

#_______________________________________________
# Function to check mapping before materialisation
def check_g_mapping(g):

    tm_dict = {}
    for tm in g.subjects(RML.logicalSource, None):
        tm_label = split_uri(tm)[1]
        tm_dict[tm_label] = tm

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

    tm_wo_pom_list_display = utils.format_list_for_markdown(tm_wo_pom_list)
    tm_wo_sm_list_display = utils.format_list_for_markdown(tm_wo_sm_list)
    pom_wo_om_list_display = utils.format_list_for_markdown(pom_wo_om_list)
    pom_wo_predicate_list_display = utils.format_list_for_markdown(pom_wo_predicate_list)

    if tm_wo_sm_list or tm_wo_pom_list or pom_wo_om_list or pom_wo_predicate_list_display:

        max_length = utils.get_max_length_for_display()[5]

        inner_html = f"""The <b>mapping</b> is incomplete!
            <br>"""

        if tm_wo_sm_list:
            if len(tm_wo_sm_list) == 1:
                inner_html += f"""<div style="margin-left: 20px"><small>The TriplesMap <b>
                {tm_wo_sm_list_display}</b> has not been assigned
                a Subject Map.</small><br></div>"""
            elif len(tm_wo_sm_list) < max_length:
                inner_html += f"""<div style="margin-left: 20px"><small>The TriplesMaps
                <b>{tm_wo_sm_list_display}</b> have not been assigned
                a Subject Map.</small><br></div>"""
            else:
                inner_html += f"""<div style="margin-left: 20px"><small><b>{len(tm_wo_sm_list)}
                TriplesMaps</b> have not been assigned
                a Subject Map.</small><br></div>"""

        if tm_wo_pom_list:
            if len(tm_wo_pom_list) == 1:
                tm_wo_pom_list_display = utils.format_list_for_markdown(tm_wo_pom_list)
                inner_html += f"""<div style="margin-left: 20px"><small>The TriplesMap
                <b>{tm_wo_pom_list_display}</b> has not been assigned
                a Predicate-Object Map.</small><br></div>"""
            elif len(tm_wo_pom_list) < max_length:
                tm_wo_pom_list_display = utils.format_list_for_markdown(tm_wo_pom_list)
                inner_html += f"""<div style="margin-left: 20px"><small>The TriplesMaps
                <b>{tm_wo_pom_list_display}</b> have not been assigned
                a Predicate-Object Map.</small><br></div>"""
            else:
                inner_html += f"""<div style="margin-left: 20px"><small><b>{len(tm_wo_pom_list)}
                TriplesMaps</b> have not been assigned
                a Predicate-Object Map.</small><br></div>"""

        if pom_wo_om_list:
            if len(pom_wo_om_list) == 1:
                inner_html += f"""<div style="margin-left: 20px"><small>The Predicate-Object Map
                <b>{pom_wo_om_list_display}</b> has not been assigned
                an Object Map.</small><br></div>"""
            elif len(pom_wo_om_list) < max_length:
                inner_html += f"""<div style="margin-left: 20px"><small>The Predicate-Object Maps
                <b>{pom_wo_om_list_display}</b> have not been assigned
                an Object Map.</small><br></div>"""
            else:
                inner_html += f"""<div style="margin-left: 20px"><small><b>{len(pom_wo_om_list_display)}
                Predicate-Object Maps</b> have not been assigned
                an Object Map.</small><br></div>"""

        if pom_wo_predicate_list:
            if len(pom_wo_om_list) == 1:
                inner_html += f"""<div style="margin-left: 20px"><small>The Predicate-Object Map
                <b>{pom_wo_predicate_list_display}</b> has not been assigned
                a predicate.</small><br></div>"""
            elif len(pom_wo_om_list) < max_length:
                inner_html += f"""<div style="margin-left: 20px"><small>The Predicate-Object Maps
                <b>{pom_wo_predicate_list_display}</b> have not been assigned
                a predicate.</small><br></div>"""
            else:
                inner_html += f"""<div style="margin-left: 20px"><small><b>{len(pom_wo_predicate_list_display)}
                Predicate-Object Maps</b> have not been assigned
                a predicate.</small><br></div>"""

        return inner_html

    return ""

#_________________________________________________

#_________________________________________________
# Funtion to check a mapping loaded from URL is ok
def is_valid_url_mapping(mapping_url, show_info):
    mapping_url_ok_flag = True

    try:
        # Fetch content
        response = requests.get(mapping_url)
        response.raise_for_status()
        url_mapping = response.text

        # Check extension
        if mapping_url.endswith((".ttl", ".rml.ttl", ".r2rml.ttl", ".fnml.ttl", ".rml-star.ttl")):
            # Step 3a: Parse as RDF
            g = rdflib.Graph()
            g.parse(data=url_mapping, format="turtle")

            # Look for RML/R2RML predicates
            rml_predicates = [
                rdflib.URIRef("http://semweb.mmlab.be/ns/rml#logicalSource"),
                rdflib.URIRef("http://www.w3.org/ns/r2rml#subjectMap"),
                rdflib.URIRef("http://www.w3.org/ns/r2rml#predicateObjectMap")]

            found = any(p in [pred for _, pred, _ in g] for p in rml_predicates)

            if not found:
                if show_info:
                    st.markdown(f"""<div class="error-message">
                            ❌ Link working, but <b>no RML structure found</b>.
                            <small>Please, check your mapping content.</small>
                        </div>""", unsafe_allow_html=True)
                mapping_url_ok_flag = False

        elif url.endswith((".yaml", ".yml")):
            # Parse as YAML
            data = yaml.safe_load(url_mapping)

            # Check for YARRRML structure
            if not "mappings" in data and isinstance(data["mappings"], dict):
                if show_info:
                    st.markdown(f"""<div class="error-message">
                            ❌ Link working, but <b>no YARRRML structure found</b>.
                            <small>Please, check your mapping content.</small>
                        </div>""", unsafe_allow_html=True)
                mapping_url_ok_flag = False

        else:
            if show_info:
                st.markdown(f"""<div class="error-message">
                    ❌ <b>Extension is not valid</b>.
                </div>""", unsafe_allow_html=True)
            mapping_url_ok_flag = False

    except Exception as e:
        if show_info:
            st.markdown(f"""<div class="error-message">
                ❌ <b>Validation failed.</b><br>
                <small><b>Full error:</b> {e}</small>
            </div>""", unsafe_allow_html=True)
        mapping_url_ok_flag = False

    return mapping_url_ok_flag

#_________________________________________________

#________________________________________________
# Function to display a rule
def preview_rule(s_for_display, p_for_display, o_for_display):

    inner_html = ""
    max_length = 40

    s_for_display = "" if not s_for_display else s_for_display
    p_for_display = "" if not p_for_display else p_for_display
    o_for_display = "" if not o_for_display else o_for_display

    formatted_s = f"""{s_for_display}""" if len(s_for_display) < max_length else "<small>" + f"""{s_for_display}""" + "</small>"
    formatted_p = f"""{p_for_display}""" if len(p_for_display) < max_length else "<small>" + f"""{p_for_display}""" + "</small>"
    formatted_o = f"""{o_for_display}""" if len(o_for_display) < max_length else "<small>" + f"""{o_for_display}""" + "</small>"

    st.markdown(f"""<div class="blue-preview-message" style="margin-top:0px; padding-top:4px;">
        <small><b style="color:#F63366; font-size:10px; margin-top:0px;">🏷️ Subject → 🔗 Predicate → 🎯 Object</b></small>
        <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; margin-top:0px;">
            <div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                <div style="margin-top:1px; font-size:13px; line-height:1.4;"><b>{formatted_s}</b></div>
            </div>
            <div style="flex:0; font-size:18px;">🡆</div>
            <div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                <div style="margin-top:1px; font-size:13px; line-height:1.4;"><b>{formatted_p}</b></div>
            </div>
            <div style="flex:0; font-size:18px;">🡆</div>
            <div style="flex:1; min-width:140px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                <div style="margin-top:1px; font-size:13px; line-height:1.4;"><b><small>{formatted_o}</small></b></div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)
#_________________________________________________

#________________________________________________
# Function to display a rule
def preview_rule_list(s_for_display, p_for_display, o_for_display):

    small_header = """<small><b style="color:#F63366; font-size:10px;margin-top:8px; margin-bottom:8px; display:block;">🏷️ Subject → 🔗 Predicate → 🎯 Object</b></small>"""

    inner_html = ""
    max_length = 40

    s_for_display = "" if not s_for_display else s_for_display
    p_for_display = "" if not p_for_display else p_for_display
    o_for_display = "" if not o_for_display else o_for_display

    formatted_s = f"""{s_for_display}""" if len(s_for_display) < max_length else "<small>" + f"""{s_for_display}""" + "</small>"
    formatted_p = f"""{p_for_display}""" if len(p_for_display) < max_length else "<small>" + f"""{p_for_display}""" + "</small>"
    formatted_o = f"""{o_for_display}""" if len(o_for_display) < max_length else "<small>" + f"""{o_for_display}""" + "</small>"

    inner_html += f"""<div style="display:flex; justify-content:space-between; align-items:center; gap:10px; margin-top:0px;">
            <div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                <div style="margin-top:1px; font-size:13px; line-height:1.4;"><b>{formatted_s}</b></div>
            </div>
            <div style="flex:0; font-size:18px;">🡆</div>
            <div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                <div style="margin-top:1px; font-size:13px; line-height:1.4;"><b>{formatted_p}</b></div>
            </div>
            <div style="flex:0; font-size:18px;">🡆</div>
            <div style="flex:1; min-width:140px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                <div style="margin-top:1px; font-size:13px; line-height:1.4;"><b><small>{formatted_o}</small></b></div>
            </div>
        </div><br>"""

    return [small_header, inner_html]
#_________________________________________________


#________________________________________________
# Function to display a rule
def display_rules(rule_list):

    if not rule_list:
        st.markdown(f"""<div class="warning-message">
            <b>No rules.</b>
        </div>""", unsafe_allow_html=True)
    else:
        inner_html = f"""<b>RULES ({len(rule_list)}):</b>
        &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp
        <small>🏷️ Subject → 🔗 Predicate → 🎯 Object</b></small><br>"""

        for rule in rule_list:
            sm_rule_for_display = rule[0]
            selected_p_for_display = rule[1]
            om_iri_for_display = rule[2]

            inner_html += f"""<div style="display:flex; justify-content:space-between; align-items:center; gap:10px; margin-top:10px;">"""

            if len(sm_rule_for_display) < 40:
                inner_html += f"""<div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                    <div style="margin-top:1px; font-size:13px; line-height:1.4;"><b>{sm_rule_for_display}</b></div></div>"""
            else:
                inner_html += f"""<div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                    <div style="margin-top:1px; font-size:13px; line-height:1.4;"><b><small>{sm_rule_for_display}</small></b></div></div>"""

            inner_html += f"""<div style="flex:0; font-size:18px;">🡆</div>"""

            if len(selected_p_for_display) < 40:
                inner_html += f"""<div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                    <div style="margin-top:1px; font-size:13px; line-height:1.4;"><b>{selected_p_for_display}</b></div></div>"""
            else:
                inner_html += f"""<div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                    <div style="margin-top:1px; font-size:13px; line-height:1.4;"><b><small>{selected_p_for_display}</small></b></div></div>"""

            inner_html += f"""<div style="flex:0; font-size:18px;">🡆</div>"""

            if len(om_iri_for_display) < 40:
                inner_html += f"""<div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                    <div style="margin-top:1px; font-size:13px; line-height:1.4;"><b>{om_iri_for_display}</b></div></div><br>
                    </div>"""
            else:
                inner_html += f"""<div style="flex:1; min-width:120px; text-align:center; border:0.5px solid black; padding:5px; border-radius:5px; word-break:break-word;">
                    <div style="margin-top:1px; font-size:13px; line-height:1.4;"><b><small>{om_iri_for_display}</small></b></div></div><br>
                    </div>"""

        st.markdown(f"""<div class="info-message-blue">
            {inner_html}
        </div>""", unsafe_allow_html=True)

#_________________________________________________

#_________________________________________________
# Funtion to get the rule associated to a subject map
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

        sm_for_display = format_iri_to_prefix_label(sm_for_display)
        p_for_display = format_iri_to_prefix_label(p_for_display)
        om_for_display = format_iri_to_prefix_label(om_for_display)

        sm_rules_list.append([sm_for_display, p_for_display, om_for_display, format_iri_to_prefix_label(tm)])

    return sm_rules_list
#_________________________________________________







# FUNCTIONS TO DISPLAY STATS-----------------------------------------------
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

#_________________________________________________

#_________________________________________________
# Funtion to get the number of tm metric
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
# Funtion to get the number of tm metric
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

#________________________________________________________
# Funtion to get the dictionary of the superclasses in the ontology
def get_ontology_superclass_dict(g_ont):

    superclass_dict = {}
    for s, p, o in list(set(g_ont.triples((None, RDFS.subClassOf, None)))):
        if not isinstance(o, BNode) and o not in superclass_dict.values():
            superclass_dict[o.split("/")[-1].split("#")[-1]] = o

    return superclass_dict
#________________________________________________________

#________________________________________________________
# Funtion to get the dictionary of the classes in the ontology
def get_ontology_classes_dict(g_ont):

    ontology_classes_dict = {}
    class_triples = set()
    class_triples |= set(g_ont.triples((None, RDF.type, OWL.Class)))   #collect owl:Class definitions
    class_triples |= set(g_ont.triples((None, RDF.type, RDFS.Class)))    # collect rdfs:Class definitions

    for s, p, o in class_triples:   #we add to dictionary removing the BNodes
        if not isinstance(s, BNode):
            ontology_classes_dict[split_uri(s)[1]] = s

    return ontology_classes_dict
#________________________________________________________

#________________________________________________________
# Funtion to get the dictionary of the ontology classes used by the mapping
def get_ontology_used_classes_dict(g_ont):

    ontology_classes_dict = get_ontology_classes_dict(g_ont)
    ontology_used_classes_dict = {}

    for class_label, class_iri in ontology_classes_dict.items():
        if (None, RML["class"], URIRef(class_iri)) in st.session_state["g_mapping"]:
            ontology_used_classes_dict[class_label] = class_iri

    return ontology_used_classes_dict
#________________________________________________________

#________________________________________________________
# Funtion to get the dictionary of the count of the ontology classes used by the mapping
def get_ontology_used_classes_count_dict(g_ont):

    ontology_classes_dict = get_ontology_classes_dict(g_ont)
    usage_count_dict = defaultdict(int)

    for class_label, class_iri in ontology_classes_dict.items():
        for triple in st.session_state["g_mapping"].triples((None, RML["class"], URIRef(class_iri))):
            usage_count_dict[class_label] += 1

    return dict(usage_count_dict)
#________________________________________________________

#________________________________________________________
# Funtion to get the dictionary of the count of the ontology classes used by the mapping by rules
def get_ontology_used_classes_count_by_rules_dict(g_ont):

    ontology_classes_dict = get_ontology_classes_dict(g_ont)
    usage_count_dict = {}

    for class_label, class_iri in ontology_classes_dict.items():
        for s, p, o in st.session_state["g_mapping"].triples((None, RML["class"], URIRef(class_iri))):
            sm_iri = s
            sm_iri_rule_list = get_rules_for_sm(sm_iri)
            if sm_iri_rule_list:
                usage_count_dict[class_label] = len(sm_iri_rule_list)

    return dict(usage_count_dict)
#________________________________________________________

#_________________________________________________
# Funtion to get the class dictionaries with sueprclass filter
def get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=None):
    # Class dictionaries___________________________
    ontology_classes_dict = utils.get_ontology_classes_dict(g_ont)
    ontology_used_classes_dict = utils.get_ontology_used_classes_dict(g_ont)
    ontology_used_classes_count_dict = utils.get_ontology_used_classes_count_dict(g_ont)
    ontology_used_classes_count_by_rules_dict = utils.get_ontology_used_classes_count_by_rules_dict(g_ont)

    # Adding superclass filter to dictionaries
    if superclass_filter and superclass_filter != "No filter":

        classes_in_superclass_dict = {}
        for s, p, o in list(set(g_ont.triples((None, RDFS.subClassOf, superclass_filter)))):
            classes_in_superclass_dict[split_uri(s)[1]] = s

        ontology_classes_dict = {class_label:class_iri for class_label, class_iri in ontology_classes_dict.items()
            if class_iri in classes_in_superclass_dict.values()}
        ontology_used_classes_dict = {class_label:class_iri for class_label, class_iri in ontology_used_classes_dict.items()
            if class_iri in classes_in_superclass_dict.values()}
        ontology_used_classes_count_dict = {class_label:ontology_used_classes_count_dict[class_label]
            for class_label, class_iri in ontology_used_classes_dict.items()}
        ontology_used_classes_count_by_rules_dict = {class_label:ontology_used_classes_count_by_rules_dict[class_label]
            for class_label, class_iri in ontology_used_classes_dict.items() if class_label in ontology_used_classes_count_by_rules_dict}

    return [ontology_classes_dict, ontology_used_classes_dict,
        ontology_used_classes_count_dict, ontology_used_classes_count_by_rules_dict]
#_________________________________________________


#_________________________________________________
# Funtion to get the used classes metric
def get_used_classes_metric(g_ont, superclass_filter=None):

    # Filtered class dictionaries___________________________
    ontology_classes_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superclass_filter)[0]
    ontology_used_classes_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superclass_filter)[1]

    # Calculate and render_______________________
    if len(ontology_classes_dict) != 0:
        percentage = len(ontology_used_classes_dict)/len(ontology_classes_dict)*100
    else:
        percentage = 0
    percentage_for_display = format_number_for_display(percentage)

    st.markdown("""<style>[data-testid="stMetricDelta"] svg {
            display: none;
        }</style>""", unsafe_allow_html=True)
    st.metric(label="Used classes", value=f"{len(ontology_used_classes_dict)}/{len(ontology_classes_dict)}",
        delta=f"({percentage_for_display}%)", delta_color="off")
#_________________________________________________

#_________________________________________________
# Funtion to get the used classes metric
def get_average_class_frequency_metric(g_ont, superclass_filter=None, type="used_classes"):

    # Filtered class dictionaries___________________________
    ontology_classes_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superclass_filter)[0]
    ontology_used_classes_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superclass_filter)[1]
    ontology_used_classes_count_by_rules_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superclass_filter)[3]

    number_of_rules = sum(ontology_used_classes_count_by_rules_dict.values())
    number_of_used_classes = len(ontology_used_classes_dict)
    number_of_classes = len(ontology_classes_dict)

    if type == "used_classes":
        average_class_use = number_of_rules/number_of_used_classes if number_of_used_classes != 0 else 0
    if type == "all_classes":
        average_class_use = number_of_rules/number_of_classes if number_of_classes != 0 else 0

    st.markdown("""<style>[data-testid="stMetricDelta"] svg {
            display: none;
        }</style>""", unsafe_allow_html=True)
    if type == "used_classes":
        st.metric(label="Average class freq", value=f"{format_number_for_display(average_class_use)}",
            delta=f"(over used classes)", delta_color="off")
    if type == "all_classes":
        st.metric(label="Average class freq", value=f"{format_number_for_display(average_class_use)}",
            delta=f"(over all classes)", delta_color="off")
#_________________________________________________

#_________________________________________________
# Funtion to get used classses donut chart
def get_used_classes_donut_chart(g_ont, superclass_filter=None):

    colors = get_colors_for_stats_dict()

    ontology_classes_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superclass_filter)[0]
    ontology_used_classes_count_by_rules_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superclass_filter)[3]

    nb_used_clases = len(ontology_used_classes_count_by_rules_dict)
    nb_unused_classes = len(ontology_classes_dict) - nb_used_clases
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
#_________________________________________________

#_________________________________________________
# Funtion to get class frequency bar plot
def get_class_frequency_bar_plot(g_ont, selected_classes, superclass_filter=None):

    colors = get_colors_for_stats_dict()

    ontology_used_classes_count_by_rules_dict = utils.get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superclass_filter)[3]

    # Selected classes for display__________________________
    if not selected_classes:  # plot 15 most used
        classes_for_display_list = sorted(ontology_used_classes_count_by_rules_dict.items(), key=lambda x: x[1], reverse=True)[:10]
    else:
        classes_for_display_list = [(cls, ontology_used_classes_count_by_rules_dict[cls]) for cls in selected_classes]

    if classes_for_display_list:
        # Build plot_______________________________________________
        labels, counts = zip(*classes_for_display_list)
        fig = px.bar(x=labels,y=counts,text=counts)

        # Style the chart_________________________________
        fig.update_traces(marker_color=colors["purple"], textposition="inside", width=0.7)
        fig.update_layout(xaxis_title=None, yaxis_title="Class frequency",
            yaxis=dict(showticklabels=False, ticks="", showgrid=True,
                gridcolor="lightgray", title_standoff=5),
            height=300, margin=dict(t=20, b=20, l=20, r=20))


        # Render___________________________
        st.plotly_chart(fig, use_container_width=True)

#_________________________________________________

#_________________________________________________
# Funtion to get ontology composition
def get_mapping_composition_by_class_donut_chart():

    colors = get_colors_for_stats_dict()

    # classify ontology classes
    frequency_dict = {}
    for ont_label, ont in st.session_state["g_ontology_components_dict"].items():
        ont_tag = st.session_state["g_ontology_components_tag_dict"][ont_label]
        ontology_used_classes_count_dict = get_ontology_used_classes_count_by_rules_dict(ont)
        total_count = sum(ontology_used_classes_count_dict.values())
        if total_count:
            frequency_dict[ont_tag] = total_count

    # get classes from other ontologies
    all_used_classes_dict = {}
    for s, p, o in st.session_state["g_mapping"].triples((None, RML["class"], None)):
        if isinstance(o, URIRef):
            all_used_classes_dict[split_uri(o)[1]] = o

    other_ontologies_list = []
    for class_label, class_iri in all_used_classes_dict.items():
        other_ontologies_flag = True
        for ont_label, g_ont in st.session_state["g_ontology_components_dict"].items():
            ontology_classes_dict = get_ontology_classes_dict(g_ont)
            if class_iri in ontology_classes_dict.values():
                other_ontologies_flag = False
        if other_ontologies_flag:
            other_ontologies_list.append(class_iri)
    if other_ontologies_list:
        number_of_rules = 0
        for class_iri in other_ontologies_list:
            for s, p, o in st.session_state["g_mapping"].triples((None, RML["class"], class_iri)):
                sm_iri = s
                rule_list = get_rules_for_sm(sm_iri)
                number_of_rules += len(rule_list)
        if number_of_rules:
            frequency_dict["Other"] = number_of_rules

    if frequency_dict:
        # Create and style donut chart
        data = {"Ontology": list(frequency_dict.keys()),
            "UsageCount": list(frequency_dict.values())}
        fig = px.pie(data, names="Ontology", values="UsageCount", hole=0.4)

        custom_colors = [colors["salmon"], colors["purple"], colors["blue"]]
        fallback = px.colors.qualitative.Pastel

        color_map = {}
        for label in frequency_dict.keys():
            if label == "Other":
                color_map[label] = colors["gray"]
            else:
                color_map[label] = custom_colors.pop(0) if custom_colors else fallback.pop(0)

        fig.update_traces(
            textinfo='label+value', textposition="inside",
            marker=dict(colors=[color_map[label] for label in data["Ontology"]]))

        fig.update_layout(title=dict(
            text="Mapping composition <br>by 🏷️ Class",
            font=dict(size=14),
            x=0.5, xanchor="center", y=0.9, yanchor="bottom"),
            width=400, height=300, margin=dict(t=60, b=20, l=20, r=20),
            showlegend=True,
            legend=dict(orientation="h", yanchor="top", y=0,
                xanchor="center", x=0.5))

        # Render
        st.plotly_chart(fig)
        return True

    else:
        st.write("")
        st.markdown(f"""<div class="gray-preview-message">
                <b>No <b style="color:#F63366;">classes</b> used in rules</b.
            </div>""", unsafe_allow_html=True)
        return False
#_________________________________________________

#________________________________________________________
# Funtion to get the dictionary of the superclasses in the ontology
def get_ontology_superproperty_dict(g_ont):

    superproperty_dict = {}
    for s, p, o in set(g_ont.triples((None, RDFS.subPropertyOf, None))):
        if not isinstance(o, BNode) and o not in superproperty_dict.values():
            superproperty_dict[o.split("/")[-1].split("#")[-1]] = o

    return superproperty_dict
#________________________________________________________

#________________________________________________________
# Funtion to get the predicates defined by an ontology
def get_ontology_properties_dict(g_ont):
    ontology_base_iri_list = get_ontology_base_iri(g_ont)
    p_types_list = [RDF.Property, OWL.ObjectProperty, OWL.DatatypeProperty]
    p_exclusion_list = [RDFS.label, RDFS.comment, OWL.versionInfo, OWL.deprecated, RDF.type]

    p_set = set()

    for s, p, o in g_ont.triples((None, RDF.type, None)):
        if o in p_types_list:
            if ontology_base_iri_list:
                if str(s).startswith(tuple(ontology_base_iri_list)) and s not in p_exclusion_list:
                    p_set.add(s)
            else:
                if s not in p_exclusion_list:
                    p_set.add(s)

    ontology_p_dict = {split_uri(p)[1]: p for p in p_set}

    return ontology_p_dict
#______________________________________________

#________________________________________________________
# Funtion to get the dictionary of the superclasses in the ontology
def get_ontology_used_properties_dict(g_ont):

    ontology_properties_dict = get_ontology_properties_dict(g_ont)
    ontology_used_properties_dict = {}

    for prop_label, prop_iri in ontology_properties_dict.items():
        if (None, RML.predicate, URIRef(prop_iri)) in st.session_state["g_mapping"]:
            ontology_used_properties_dict[prop_label] = prop_iri

    return ontology_used_properties_dict
#________________________________________________________

#________________________________________________________
# Funtion to get the dictionary of the count of the ontology properties used by the mapping
# In the case of properties, the count by rules is the same as the count by number
def get_ontology_used_properties_count_dict(g_ont):

    ontology_properties_dict = get_ontology_properties_dict(g_ont)
    usage_count_dict = defaultdict(int)

    for prop_label, prop_iri in ontology_properties_dict.items():
        for triple in st.session_state["g_mapping"].triples((None, RML["predicate"], URIRef(prop_iri))):
            usage_count_dict[prop_label] += 1

    return dict(usage_count_dict)
#________________________________________________________

#_________________________________________________
# Funtion to get the class dictionaries with sueprclass filter
def get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=None):
    # Property dictionaries___________________________
    ontology_properties_dict = utils.get_ontology_properties_dict(g_ont)
    ontology_used_properties_dict = utils.get_ontology_used_properties_dict(g_ont)
    ontology_used_properties_count_dict = utils.get_ontology_used_properties_count_dict(g_ont)

    # Adding superclass filter to dictionaries
    if superproperty_filter and superproperty_filter != "No filter":

        properties_in_superclass_dict = {}
        for s, p, o in list(set(g_ont.triples((None, RDFS.subPropertyOf, superproperty_filter)))):
            properties_in_superclass_dict[split_uri(s)[1]] = s

        ontology_properties_dict = {class_label:class_iri for class_label, class_iri in ontology_properties_dict.items()
            if class_iri in properties_in_superclass_dict.values()}
        ontology_used_properties_dict = {class_label:class_iri for class_label, class_iri in ontology_used_properties_dict.items()
            if class_iri in properties_in_superclass_dict.values()}
        ontology_used_properties_count_dict = {class_label:ontology_used_properties_count_dict[class_label]
            for class_label, class_iri in ontology_used_properties_dict.items()}

    return [ontology_properties_dict, ontology_used_properties_dict,
        ontology_used_properties_count_dict]
#_________________________________________________

#_________________________________________________
# Funtion to get the used properties metric
def get_used_properties_metric(g_ont, superproperty_filter=None):

    # Filtered property dictionaries___________________________
    ontology_properties_dict = get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=superproperty_filter)[0]
    ontology_used_properties_dict = get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=superproperty_filter)[1]

    # Calculate and render_______________________
    if ontology_properties_dict:
        percentage = len(ontology_used_properties_dict)/len(ontology_properties_dict)*100
    else:
        percentage = 0
    percentage_for_display = format_number_for_display(percentage)

    st.markdown("""<style>[data-testid="stMetricDelta"] svg {
            display: none;
        }</style>""", unsafe_allow_html=True)
    st.metric(label="Used properties", value=f"{len(ontology_used_properties_dict)}/{len(ontology_properties_dict)}",
        delta=f"({percentage_for_display}%)", delta_color="off")
#_________________________________________________

#_________________________________________________
# Funtion to get the used properties metric
def get_average_property_frequency_metric(g_ont, superproperty_filter=None, type="used_properties"):

    # Filtered property dictionaries___________________________
    ontology_properties_dict = get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=superproperty_filter)[0]
    ontology_used_properties_dict = get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=superproperty_filter)[1]
    ontology_used_properties_count_dict = get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=superproperty_filter)[2]

    number_of_rules = sum(ontology_used_properties_count_dict.values())
    number_of_used_properties = len(ontology_used_properties_dict)
    number_of_properties = len(ontology_properties_dict)

    if type == "used_properties":
        average_property_use = number_of_rules/number_of_used_properties if number_of_used_properties != 0 else 0
    if type == "all_properties":
        average_property_use = number_of_rules/number_of_properties if number_of_properties != 0 else 0

    st.markdown("""<style>[data-testid="stMetricDelta"] svg {
            display: none;
        }</style>""", unsafe_allow_html=True)
    if type == "used_properties":
        st.metric(label="Average freq", value=f"{format_number_for_display(average_property_use)}",
            delta=f"(over used properties)", delta_color="off")
    if type == "all_properties":
        st.metric(label="Average freq", value=f"{format_number_for_display(average_property_use)}",
            delta=f"(over all properties)", delta_color="off")
#_________________________________________________

#_________________________________________________
# Funtion to get the used classes metric
def get_average_class_frequency_metric(g_ont, superclass_filter=None, type="used_classes"):

    # Filtered class dictionaries___________________________
    ontology_classes_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superclass_filter)[0]
    ontology_used_classes_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superclass_filter)[1]
    ontology_used_classes_count_by_rules_dict = get_class_dictionaries_filtered_by_superclass(g_ont, superclass_filter=superclass_filter)[3]

    number_of_rules = sum(ontology_used_classes_count_by_rules_dict.values())
    number_of_used_classes = len(ontology_used_classes_dict)
    number_of_classes = len(ontology_classes_dict)

    if type == "used_classes":
        average_class_use = number_of_rules/number_of_used_classes if number_of_used_classes != 0 else 0
    if type == "all_classes":
        average_class_use = number_of_rules/number_of_classes if number_of_classes != 0 else 0

    st.markdown("""<style>[data-testid="stMetricDelta"] svg {
            display: none;
        }</style>""", unsafe_allow_html=True)
    if type == "used_classes":
        st.metric(label="Average freq.", value=f"{format_number_for_display(average_class_use)}",
            delta=f"(over used classes)", delta_color="off")
    if type == "all_classes":
        st.metric(label="Average freq.", value=f"{format_number_for_display(average_class_use)}",
            delta=f"(over all classes)", delta_color="off")
#_________________________________________________

#_________________________________________________
# Funtion to get used properties donut chart
def get_used_properties_donut_chart(g_ont, superproperty_filter=None):

    colors = get_colors_for_stats_dict()

    ontology_properties_dict = get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=superproperty_filter)[0]
    ontology_used_properties_dict = get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=superproperty_filter)[1]

    nb_used_clases = len(ontology_used_properties_dict)
    nb_unused_properties = len(ontology_properties_dict) - len(ontology_used_properties_dict)
    data = {"Category": ["Used properties", "Unused properties"],
        "Value": [nb_used_clases, nb_unused_properties]}

    fig = px.pie(names=data["Category"],values=data["Value"], hole=0.4)

    fig.update_traces(textinfo='value', textposition='inside',
        marker=dict(colors=[colors["purple"], colors["gray"]]))

    fig.update_layout(width=400, height=300, margin=dict(t=20, b=20, l=20, r=20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=0,               # center vertically
            xanchor="center", x=0.5))

    st.plotly_chart(fig)
#_________________________________________________

#_________________________________________________
# Funtion to get property frequency bar plot
def get_property_frequency_bar_plot(g_ont, selected_properties, superproperty_filter=None):

    colors = get_colors_for_stats_dict()

    ontology_used_properties_count_dict = utils.get_property_dictionaries_filtered_by_superproperty(g_ont, superproperty_filter=superproperty_filter)[2]

    # Selected properties for display__________________________
    if not selected_properties:  # plot 15 most used
        properties_for_display_list = sorted(ontology_used_properties_count_dict.items(), key=lambda x: x[1], reverse=True)[:10]
    else:
        properties_for_display_list = [(cls, ontology_used_properties_count_dict[cls]) for cls in selected_properties]

    if properties_for_display_list:
        # Build plot_______________________________________________
        labels, counts = zip(*properties_for_display_list)
        fig = px.bar(x=labels,y=counts,text=counts)

        # Style the chart_________________________________
        fig.update_traces(marker_color=colors["purple"], textposition="inside", width=0.7)
        fig.update_layout(xaxis_title=None, yaxis_title="property frequency",
            yaxis=dict(showticklabels=False, ticks="", showgrid=True,
                gridcolor="lightgray", title_standoff=5),
            height=300, margin=dict(t=20, b=20, l=20, r=20))


        # Render___________________________
        st.plotly_chart(fig, use_container_width=True)

#_________________________________________________

#_________________________________________________
# Funtion to get ontology composition
def get_mapping_composition_by_property_donut_chart():

    colors = get_colors_for_stats_dict()

    # classify ontology properties
    frequency_dict = {}
    for ont_label, ont in st.session_state["g_ontology_components_dict"].items():
        ont_tag = st.session_state["g_ontology_components_tag_dict"][ont_label]
        ontology_used_properties_count_dict = get_ontology_used_properties_count_dict(ont)
        total_count = sum(ontology_used_properties_count_dict.values())
        if total_count:
            frequency_dict[ont_tag] = total_count

    # get properties from other ontologies
    all_used_properties_dict = {}
    for s, p, o in st.session_state["g_mapping"].triples((None, RML["predicate"], None)):
        if isinstance(o, URIRef):
            all_used_properties_dict[split_uri(o)[1]] = o

    other_ontologies_list = []
    for prop_label, prop_iri in all_used_properties_dict.items():
        other_ontologies_flag = True
        for ont_label, g_ont in st.session_state["g_ontology_components_dict"].items():
            ontology_properties_dict = get_ontology_properties_dict(g_ont)
            if prop_iri in ontology_properties_dict.values():
                other_ontologies_flag = False
        if other_ontologies_flag:
            other_ontologies_list.append(prop_iri)
    if other_ontologies_list:
        frequency_dict["Other"] = len(other_ontologies_list)

    if frequency_dict:
        # Create and style donut chart
        data = {"Ontology": list(frequency_dict.keys()),
            "UsageCount": list(frequency_dict.values())}
        fig = px.pie(data, names="Ontology", values="UsageCount", hole=0.4)

        custom_colors = [colors["salmon"], colors["purple"], colors["blue"]]
        fallback = px.colors.qualitative.Pastel

        color_map = {}
        for label in frequency_dict.keys():
            if label == "Other":
                color_map[label] = colors["gray"]
            else:
                color_map[label] = custom_colors.pop(0) if custom_colors else fallback.pop(0)

        fig.update_traces(
            textinfo='label+value', textposition="inside",
            marker=dict(colors=[color_map[label] for label in data["Ontology"]]))

        # Layout and legend
        fig.update_layout(title=dict(
            text="Mapping composition <br>by 🔗 Properties",
            font=dict(size=14),
            x=0.5, xanchor="center", y=0.9, yanchor="bottom"),
            width=400, height=300, margin=dict(t=60, b=20, l=20, r=20),
            showlegend=True,
            legend=dict(orientation="h", yanchor="top", y=0,               # center vertically
                xanchor="center", x=0.5))
        # Render
        st.plotly_chart(fig)
        return True

    else:
        st.write("")
        st.markdown(f"""<div class="gray-preview-message">
                <b>No <b style="color:#F63366;">properties</b> in mapping</b.
            </div>""", unsafe_allow_html=True)
        return False

#_________________________________________________

#_________________________________________________
# Funtion to get unique node label for network display
# Takes the legend dict and updates it
# Max length can be modified, default given
def get_unique_node_label(complete_node_id, constant_string, legend_dict, max_length=utils.get_max_length_for_display()[6]):

    i = 1
    while f"{constant_string}{i}" in legend_dict:
        i += 1
    label = f"{constant_string}{i}"

    if complete_node_id and len(complete_node_id) > max_length:
        if complete_node_id not in legend_dict.values():
            node_id = label
            legend_dict[node_id] = complete_node_id
        else:
            for k, v in legend_dict.items():
                if v == complete_node_id:
                    node_id = k
    else:
        node_id = str(complete_node_id)

    return [node_id, legend_dict]
#_________________________________________________

#_________________________________________________
# Colors for STATS dict
def get_colors_for_network_dict():

    colors_for_network_dict = {}

    if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
        colors_for_network_dict["o_node_color"] = "#7A4A8C"# "#d8c3f0"
        colors_for_network_dict["s_node_color"] = "#ff7a7a" #"#ff9999"
        colors_for_network_dict["p_edge_color"] = "#D3D3D3"
        colors_for_network_dict["p_edge_label_color"] = "#888888"
        colors_for_network_dict["background_color"] = "#f5f5f5"
        colors_for_network_dict["legend_font_color"] = "#888888"

    else:
        colors_for_network_dict["o_node_color"] = "#7A4A8C"
        colors_for_network_dict["s_node_color"] = "#ff7a7a"
        colors_for_network_dict["p_edge_color"] = "#D3D3D3"
        colors_for_network_dict["p_edge_label_color"] = "#222222"
        colors_for_network_dict["background_color"] = "#222222"
        colors_for_network_dict["legend_font_color"] = "#888888"

    return colors_for_network_dict

#_________________________________________________

#_________________________________________________
# Function to check conn status and show error
def check_conn_status(conn_label):

    try:
        conn = utils.make_connection_to_db(conn_label)
        connection_ok_flag = True

    except:
        conn = None
        connection_ok_flag = False

    return [conn, connection_ok_flag]
#_________________________________________________

#_________________________________________________
#Function to display view results
def display_db_view_results(view):

    connection_for_query = st.session_state["sql_queries_dict"][view][0]
    conn, connection_ok_flag = check_conn_status(connection_for_query)

    if connection_ok_flag:

        max_length = utils.get_max_length_for_display()[10]
        query_for_display = st.session_state["sql_queries_dict"][view][1]
        query_for_display = query_for_display[:max_length] + "..." if len(query_for_display) > max_length else query_for_display

        cur = conn.cursor()   # create a cursor

        try:
            cur.execute(st.session_state["sql_queries_dict"][view][1])
            sql_query_ok_flag = True

        except Exception as e:
            with col1:
                st.markdown(f"""<div class="error-message">
                    ❌ <b>Invalid SQL syntax</b>. Please check your query.<br>
                    <small><b> Full error:</b> {e}</small>
                </div>""", unsafe_allow_html=True)
                st.write("")
            sql_query_ok_flag = False

        if sql_query_ok_flag:
            rows = cur.fetchall()
            engine = st.session_state["db_connections_dict"][connection_for_query][0]
            if engine == "SQL Server":
                rows = [tuple(row) for row in rows]   # for SQL Server rows are of type <class 'pyodbc.Row'> -> convert to tuple
            columns = [desc[0] for desc in cur.description]
            df = pd.DataFrame(rows, columns=columns)

            max_rows = utils.get_max_length_for_display()[2]
            max_cols = utils.get_max_length_for_display()[3]

            limited_df = df.iloc[:, :max_cols]   # limit number of columns

            # Slice rows if needed
            if len(df) > max_rows and df.shape[1] > max_cols:
                st.markdown(f"""<div class="warning-message">
                    ⚠️ Showing the <b>first {max_rows} rows</b> (out of {len(df)})
                    and the <b>first {max_cols} columns</b> (out of {df.shape[1]}).
                </div>""", unsafe_allow_html=True)
                st.write("")
            elif len(df) > max_rows:
                st.markdown(f"""<div class="warning-message">
                    ⚠️ Showing the <b>first {max_rows} rows</b> (out of {len(df)}).
                </div>""", unsafe_allow_html=True)
                st.write("")
            elif df.shape[1] > max_cols:
                st.markdown(f"""<div class="warning-message">
                    ⚠️ Showing the <b>first {max_cols} columns</b> (out of {df.shape[1]}).
                </div>""", unsafe_allow_html=True)
                st.write("")

            st.markdown(f"""<div class="info-message-blue">
                    🖼️ <b style="color:#F63366;"> View results ({len(df)}):</b>
                    <small>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                    (<b>Query:</b> {query_for_display})</small>
                </div></div>""", unsafe_allow_html=True)
            st.dataframe(limited_df.head(max_rows), hide_index=True)

    return connection_ok_flag
#_________________________________________________

#_________________________________________________
#Function to display database table
def display_db_table(table, conn_label):

    conn, connection_ok_flag = check_conn_status(conn_label)

    if connection_ok_flag:

        cur.execute(f"SELECT * FROM {selected_db_table}")
        rows = cur.fetchall()
        if engine == "SQL Server":
            rows = [tuple(row) for row in rows]   # rows are of type <class 'pyodbc.Row'> -> convert to tuple
        columns = [desc[0] for desc in cur.description]

        df = pd.DataFrame(rows, columns=columns)

        max_rows = utils.get_max_length_for_display()[2]
        max_cols = utils.get_max_length_for_display()[3]

        limited_df = df.iloc[:, :max_cols]   # limit number of columns

        # Slice rows if needed
        if len(df) > max_rows and df.shape[1] > max_cols:
            st.markdown(f"""<div class="warning-message">
                ⚠️ Showing the <b>first {max_rows} rows</b> (out of {len(df)})
                and the <b>first {max_cols} columns</b> (out of {df.shape[1]}).
            </div>""", unsafe_allow_html=True)
            st.write("")
        elif len(df) > max_rows:
            st.markdown(f"""<div class="warning-message">
                ⚠️ Showing the <b>first {max_rows} rows</b> (out of {len(df)}).
            </div>""", unsafe_allow_html=True)
            st.write("")
        elif df.shape[1] > max_cols:
            st.markdown(f"""<div class="warning-message">
                ⚠️ Showing the <b>first {max_cols} columns</b> (out of {df.shape[1]}).
            </div>""", unsafe_allow_html=True)
            st.write("")

        table_len = f"{len(df)} rows" if len(df) != 1 else f"{len(df)} row"
        st.markdown(f"""<div class="info-message-blue">
                🖼️ <b style="color:#F63366;"> Table ({table_len}):</b>
                <small>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                <b>({selected_db_table})</b></small>
            </div></div>""", unsafe_allow_html=True)
        st.dataframe(limited_df.head(max_rows), hide_index=True)


        cur.close()
        conn.close()

    return connection_ok_flag
#_________________________________________________


#HEREIGO






#F63366 Streamlit salmon
#f26a7e Streamlit salmon less saturated
#ff7a7a lighter streamlit salmon

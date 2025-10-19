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

from concurrent.futures import ThreadPoolExecutor, TimeoutError

import json
import csv
import rdflib
from collections import Counter
from urllib.parse import urlparse


# AESTHETICS-------------------------------------------------------------------------------------

#________________________________________________
# Function to import Logo
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
#__________________________________________________

#________________________________________________
# Function to render headers
def render_header(title, description, dark_mode: bool = False):
    image_path = "logo/logo_inverse.png" if dark_mode else "logo/logo.png"
    image_base64 = get_base64_image(image_path)

    bg_color = "#1e1e1e" if dark_mode else "#f0f0f0"
    title_color = "#d8c3f0" if dark_mode else "#511D66"
    desc_color = "#999999" if dark_mode else "#555"

    return f"""
    <div style="display:flex; align-items:center; background-color:{bg_color}; padding:16px 20px;
                border-radius:12px; box-shadow:0 2px 6px rgba(0,0,0,0.1);">
        <img src="data:image/png;base64,{image_base64}" alt="Logo"
             style="height:74px; margin-right:70px; border-radius:8px;" />
        <div style="display:flex; flex-direction:column;">
            <div style="font-size:1.4rem; font-weight:600; color:{title_color}; margin-bottom:4px;">
                {title}
            </div>
            <div style="font-size:0.95rem; color:{desc_color};">
                {description}
            </div>
        </div>
    </div>
    """
#________________________________________________

#________________________________________________
# Function to import style
def import_st_aesthetics():

    #TIME FOR MESSAGES
    st.session_state["success_display_time"] = 2

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

    /* SUBSECTION */
        .subsection {background-color: #dcdcdc;
            border: 1px solid #e0e0e0; border-radius: 5px;
            font-size: 0.9rem; padding: 2px 6px;
            margin-top: 2px; margin-bottom: 2px;}

    /* GRAY PREVIEW MESSAGE */
            .gray-preview-message {background-color:#f9f9f9; padding:0.7em; border-radius:5px;
            color:#333333; border:1px solid #e0e0e0; font-size: 0.92em; word-wrap: break-word;}

    /* BLUE PREVIEW MESSAGE */
            .blue-preview-message {background-color: #eaf4ff; padding:0.7em; border-radius:5px;
            color:#0c5460; border:1px solid #d0e4ff; font-size: 0.92em; word-wrap: break-word;}

    /* BLUE STATUS MESSAGE */
            .blue-status-message {background-color: #eaf4ff; padding: 0.6em;
            border-radius: 5px; color: #0c5460; border-left: 4px solid #0c5460;
            word-wrap: break-word; line-height: 1.5; font-size: 0.92em;}

            .blue-status-message b {color: #0c5460;}

    /* GRAY STATUS MESSAGE */
            .gray-status-message {background-color:#f5f5f5; padding: 0.6em;
            border-radius:5px; color:#2a0134; border-left:4px solid #2a0134;
            word-wrap: break-word; line-height: 1.5; font-size: 0.92em;}

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

    /* INFO TABLE GRAY */
    .info-table-gray {border-collapse: collapse; width: 100%;
        background-color: #f5f5f5; border-radius: 5px; table-layout: auto;
        max-width: 100%; word-break: break-word;}

    .info-table-gray td {padding: 4px 8px; vertical-align: top;
        font-size: 0.85rem; word-wrap: break-word; white-space: normal;
        overflow-wrap: anywhere;}

    /* TITLE ROW */
    .title-row td {font-size: 0.9rem; font-weight: bold; text-align: center;
        padding-bottom: 6px;}

/* Reduce font size of checkbox label text */
div[data-testid="stCheckbox"] > label > div > span {
    font-size: 0.5rem !important;
    line-height: 1.2;
    color: #333;
    white-space: normal;
    word-break: break-word;
    overflow-wrap: anywhere;
}

    </style>"""
#_______________________________________________________

#________________________________________________
# Function to import style
def import_st_aesthetics_dark_mode():

    #TIME FOR MESSAGES
    st.session_state["success_display_time"] = 2

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

    /* SUBSECTION */
        .subsection {background-color: #dcdcdc;
            border: 1px solid #e0e0e0; border-radius: 5px;
            font-size: 0.9rem; padding: 2px 6px;
            margin-top: 2px; margin-bottom: 2px;}

    /* GRAY PREVIEW MESSAGE — Dark Mode */
        .gray-preview-message {background-color: #1c1c1c; padding: 0.7em;
          border-radius: 5px; color: #dddddd; border: 1px solid #444444; font-size: 0.92em;
          word-wrap: break-word;}

    /* BLUE PREVIEW MESSAGE - Dark Mode*/
            .blue-preview-message {background-color: #0b1c2d; padding:0.7em; border-radius:5px;
            color:#b3d9ff; border:1px solid #060e1a; font-size: 0.92em; word-wrap: break-word;}

    /* BLUE STATUS MESSAGE — Dark Mode */
        .blue-status-message {background-color: #0b1c2d; padding: 0.6em;
            border-radius: 5px; color: #b3d9ff; border-left: 4px solid #b3d9ff;
            word-wrap: break-word; line-height: 1.5; font-size: 0.92em;}

        .blue-status-message b {color: #dceeff;}

    /* GRAY STATUS MESSAGE — Dark Mode */
        .gray-status-message {background-color: #1e1e1e;
            padding: 0.6em; border-radius: 5px; color: #dddddd;
            border-left: 4px solid #999999; word-wrap: break-word;
             line-height: 1.5; font-size: 0.92em;}

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

    /* INFO TABLE GRAY — Dark Mode */
        .info-table-gray {border-collapse: collapse; width: 100%;
          background-color: #1e1e1e; border-radius: 5px;
          table-layout: auto; max-width: 100%; word-break: break-word;}

        .info-table-gray td {padding: 4px 8px; vertical-align: top;
          font-size: 0.85rem; word-wrap: break-word; white-space: normal;
          overflow-wrap: anywhere; color: #dddddd;}

    /* TITLE ROW */
    .title-row td {font-size: 0.9rem; font-weight: bold; text-align: center;
        padding-bottom: 6px;}

    </style>"""


#_______________________________________________________
# Function to get error message to indicate a g_mapping must be loaded
def get_missing_g_mapping_error_message():
    st.markdown(f"""<div class="error-message">
        ❌ You need to create or load a mapping in the
        <b style="color:#a94442;">Select mapping option</b>.
    </div>
    """, unsafe_allow_html=True)
#_______________________________________________________

#_______________________________________________________
# Function to get the corner status message in the different panels
def get_corner_status_message():
    if st.session_state["g_ontology"]:
        if len(st.session_state["g_ontology_components_dict"]) > 1:
            ontology_items = '\n'.join([f"""<li><b>{ont}</b></li>""" for ont in st.session_state["g_ontology_components_dict"]])
            st.markdown(f"""<div class="blue-status-message">
                    <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                    style="vertical-align:middle; margin-right:8px; height:20px;">
                    You are working with mapping
                    <b>{st.session_state["g_label"]}</b>.<br> <br>
                    🧩 You are working with the <b>ontologies</b>:
                    <ul style="font-size:0.85rem; margin:6px 0 0 15px; padding-left:10px;">
                <ul>
                    {ontology_items}
                </ul></div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="blue-status-message">
                    <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                    style="vertical-align:middle; margin-right:8px; height:20px;">
                    You are working with mapping
                    <b>{st.session_state["g_label"]}</b>.<br> <br>
                    🧩 The ontology <b>
                    {next(iter(st.session_state["g_ontology_components_dict"]))}</b>
                    is loaded.
                </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class="blue-status-message">
                <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                style="vertical-align:middle; margin-right:8px; height:20px;">
                You are working with mapping
                <b>{st.session_state["g_label"]}</b>.<br> <br>
                🚫 <b>No ontology</b> is loaded.
            </div>
        """, unsafe_allow_html=True)

#_______________________________________________________

#__________________________________________________
def get_corner_status_message_or_error():
    if not st.session_state["g_label"]:
        col1, col2 = st.columns([2,1.5])
        with col1:
            utils.get_missing_g_mapping_error_message()

    else:   #only allow to continue if mapping is loaded
        col1,col2 = st.columns([2,1.5])

        with col2:
            col2a,col2b = st.columns([1,2])
        with col2b:
            utils.get_corner_status_message()
#_______________________________________________________

#_______________________________________________________
# Function to format a list
def format_list_for_markdown(xlist):

    if not xlist:
        formatted_list = ""
    elif len(xlist) == 1:
        formatted_list = xlist[0]
    else:
        formatted_list = ", ".join(xlist[:-1]) + " and " + xlist[-1]

    return formatted_list

#_______________________________________________________

#_______________________________________________________
# Function to get the max_length for the display options
# 0. complete dataframes      1. last added dataframes
# 2. Queries display (rows)    3. Queries display (columns)
# 4. List of multiselect items for hard display     # 5 Long lists for soft display
def get_max_length_for_display():

    return [50, 10, 100, 20, 5, 5]

#_______________________________________________________


# GLOBAL CONFIGURATION - CONFIGURE NAMESPACES ---------------------------------------------------
# We define these first because they will be needed in this page
#_________________________________________________________
# Function to get a base iri for our application
def get_3xmap_base_iri():
    return "http://3xmap.org/mapping/"
#________________________________________________________

#_________________________________________________________
# Function to get the default base iri for the structural components
def get_default_structural_ns():

    default_structural_ns = utils.get_3xmap_base_iri()

    return ["3xmap", Namespace(default_structural_ns)]
#________________________________________________________

#_________________________________________________________
# Funtion to get dictionary with default namespaces
# The default namespaces are automatically bound to g by rdflib (DO NOT MODIFY LIST)
def get_default_ns_dict():
    return {
    "brick": Namespace("https://brickschema.org/schema/Brick#"),
    "csvw": Namespace("http://www.w3.org/ns/csvw#"),
    "dc": Namespace("http://purl.org/dc/elements/1.1/"),
    "dcam": Namespace("http://purl.org/dc/dcam/"),
    "dcat": Namespace("http://www.w3.org/ns/dcat#"),
    "dcmitype": Namespace("http://purl.org/dc/dcmitype/"),
    "dcterms": Namespace("http://purl.org/dc/terms/"),
    "doap": Namespace("http://usefulinc.com/ns/doap#"),
    "foaf": Namespace("http://xmlns.com/foaf/0.1/"),
    "geo": Namespace("http://www.opengis.net/ont/geosparql#"),
    "odrl": Namespace("http://www.w3.org/ns/odrl/2/"),
    "org": Namespace("http://www.w3.org/ns/org#"),
    "owl": Namespace("http://www.w3.org/2002/07/owl#"),
    "prof": Namespace("http://www.w3.org/ns/dx/prof/"),
    "prov": Namespace("http://www.w3.org/ns/prov#"),
    "qb": Namespace("http://purl.org/linked-data/cube#"),
    "rdf": Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
    "rdfs": Namespace("http://www.w3.org/2000/01/rdf-schema#"),
    "schema": Namespace("https://schema.org/"),
    "sh": Namespace("http://www.w3.org/ns/shacl#"),
    "skos": Namespace("http://www.w3.org/2004/02/skos/core#"),
    "sosa": Namespace("http://www.w3.org/ns/sosa/"),
    "ssn": Namespace("http://www.w3.org/ns/ssn/"),
    "time": Namespace("http://www.w3.org/2006/time#"),
    "vann": Namespace("http://purl.org/vocab/vann/"),
    "void": Namespace("http://rdfs.org/ns/void#"),
    "wgs": Namespace("https://www.w3.org/2003/01/geo/wgs84_pos#"),
    "xml": Namespace("http://www.w3.org/XML/1998/namespace"),
    "xsd": Namespace("http://www.w3.org/2001/XMLSchema#")}
#________________________________________________________

#_________________________________________________________
# Dictionary with predefined namespaces
# These are predefined so that they can be easily bound
# It will ignore the default namespaces
# LIST CAN BE CHANGED but should keep the namespaces used in get_required_ns()
def get_predefined_ns_dict():

    all_predefined_ns_dict = {
        get_default_structural_ns()[0]: get_default_structural_ns()[1],
        "class": Namespace(get_3xmap_base_iri() + "class#"),
        "gtfs": Namespace("http://vocab.gtfs.org/terms#"),   #DELETE
        "ql": Namespace("http://semweb.mmlab.be/ns/ql#"),
        "logicalSource": Namespace(get_3xmap_base_iri() + "/logicalSource#"),
        "map": Namespace(get_3xmap_base_iri() + "mapping#"),
        "resource": Namespace(get_3xmap_base_iri() + "resource#"),
        "rml": Namespace("http://semweb.mmlab.be/ns/rml#"),
        "rr": Namespace("http://www.w3.org/ns/r2rml#"),
        "schema1": Namespace("http://schema.org2/")}

    default_ns_dict = get_default_ns_dict()
    predefined_ns_dict = {k: Namespace(v) for k, v in all_predefined_ns_dict.items() if (k not in default_ns_dict)}

    return predefined_ns_dict
#________________________________________________________

#________________________________________________________
# Function to retrieve namespaces which are needed for our code
def get_required_ns():
    ns = get_predefined_ns_dict()
    return {"RML": ns["rml"], "RR": ns["rr"], "QL": ns["ql"]}
#_______________________________________________________

#________________________________________________________
# retrieving necessary namespaces for this page here
RML, RR, QL = get_required_ns().values()
#________________________________________________________


#_________________________________________________________
# Funtion to get dictionary {prefix: namespace} bound in the ontology
# It will ignore the default namespaces
def get_ontology_ns_dict():

    default_ns_dict = get_default_ns_dict()
    all_ontology_ns_dict = dict(st.session_state["g_ontology"].namespace_manager.namespaces())
    ontology_ns_dict = {k: Namespace(v) for k, v in all_ontology_ns_dict.items() if (k not in default_ns_dict)}

    return ontology_ns_dict
#_________________________________________________________

#_________________________________________________________
# Funtion to get dictionary {prefix: namespace} bound in the ontology
# It will ignore the default namespaces
def get_ontology_component_ns_dict(g_ont_component):

    default_ns_dict = get_default_ns_dict()
    ontology_component_ns_dict = dict(g_ont_component.namespace_manager.namespaces())
    ontology_component_ns_dict = {k: Namespace(v) for k, v in ontology_component_ns_dict.items() if (k not in default_ns_dict)}

    return ontology_component_ns_dict
#_________________________________________________________

#_________________________________________________________
# Funtion to get dictionary {prefix: namespace} bound in the ontology
# It will ignore the default namespaces
def get_mapping_ns_dict():

    mapping_ns_dict = dict(st.session_state["g_mapping"].namespace_manager.namespaces())

    return mapping_ns_dict
#_________________________________________________________

#_________________________________________________________
# Funtion to get dictionary {prefix: namespace} bound in the ontology
# It will ignore the default namespaces
def get_used_mapping_ns_dict():

    used_namespaces_set = set()
    used_namespaces_dict = {}
    mapping_ns_dict = get_mapping_ns_dict()

    for s, p, o in st.session_state["g_mapping"]:
        for term in [s, p, o]:
            if isinstance(term, URIRef):
                try:
                    ns, _ = split_uri(term)
                    used_namespaces_set.add(ns)
                except ValueError:
                    pass

    for k, v in mapping_ns_dict.items():
        for namespace in used_namespaces_set:
            if str(v) == namespace:
                used_namespaces_dict[k] = v

    return used_namespaces_dict
#_________________________________________________________

#__________________________________________________________
# Function to unbind namespaces from g mapping
# Duplicated prefixes will be renamed, duplicated namespaces will be ignored
# namespaces cannot be removed, so the mapping is rebuilt completely
def unbind_namespaces(ns_to_unbind_list):

    if ns_to_unbind_list:
        old_graph = st.session_state["g_mapping"]
        ns_to_remove = set(ns_to_unbind_list)
        new_graph = Graph()   # create a new graph and copy triples
        for triple in old_graph:
            new_graph.add(triple)

        for prefix, ns in old_graph.namespace_manager.namespaces():      # rebind the namespaces without the deleted ones
            if prefix not in ns_to_remove:
                new_graph.namespace_manager.bind(prefix, ns, replace=True)

        st.session_state["g_mapping"] = new_graph        # replace the old graph with the new one

        for prefix in ns_to_unbind_list:         # update last added list
            if prefix in st.session_state["last_added_ns_list"]:
                st.session_state["last_added_ns_list"].remove(prefix)
#____________________________________________________________

#__________________________________________________________
# Function to bind namespaces to g mapping
# Duplicated prefixes will be renamed, duplicated namespaces will be overwritten
def bind_namespace(prefix, namespace):

    mapping_ns_dict = get_mapping_ns_dict()

    # if namespace already bound to a different prefix, unbind it
    if namespace in mapping_ns_dict.values():
        old_prefix_list = [k for k, v in mapping_ns_dict.items() if v == namespace]
        unbind_namespaces(old_prefix_list)

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
#______________________________________________________

#__________________________________________________________
# Function to bind namespaces to g mapping without overwriting
# Duplicated prefixes will be renamed, duplicated namespaces will be ignored
def bind_namespace_wo_overwriting(prefix, namespace):

    mapping_ns_dict = get_mapping_ns_dict()

    # if namespace already bound to a different prefix, unbind it
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

#____________________________________________________________


#_________________________________________________
#Function to check whether an IRI is valid
def is_valid_iri(iri):
    valid_iri_schemes = ("http://", "https://", "ftp://", "mailto:",
        "urn:", "tag:", "doi:", "data:")

    if isinstance(iri, URIRef):
        iri = str(iri)

    if not iri.startswith(valid_iri_schemes):
        return False

    try:
        parsed = urlparse(iri)
    except:
        return False
    schemes_with_netloc = {"http", "https", "ftp"}
    if parsed.scheme in schemes_with_netloc and not parsed.netloc:
        return False

    if re.search(r"[ \t\n\r<>\"{}|\\^`]", iri):    # disallow spaces or unescaped characters
        return False

    if not iri[-1] in ("/", "#", ":"):
        return False  # must end with a recognized delimiter

    return True
#__________________________________________________


# GLOBAL CONFIGURATION - SELECT MAPPING -------------------------------------------------------------
#_______________________________________________________
# List of allowed mapping file format
# HERE expand options, now reduced version
def get_g_mapping_file_formats_dict():

    allowed_format_dict = {"turtle": ".ttl",
        "ntriples": ".nt", "trig": ".trig", "jsonld": ".jsonld"}    # missing hdt, nquads

    return allowed_format_dict
#_______________________________________________________

#_______________________________________________________
# Function to empty all lists that store last added stuff
def empty_last_added_lists():
    st.session_state["last_added_ns_list"] = []
    st.session_state["last_added_tm_list"] = []
    st.session_state["last_added_sm_list"] = []
    st.session_state["last_added_pom_list"] = []

#_______________________________________________________
#Funcion to load mapping from file
#f is a file object
#HERE check all formats work
def load_mapping_from_file(f):

    ext = os.path.splitext(f.name)[1].lower()  #file extension

    if ext == ".pkl":
        return pickle.load(f)

    elif ext in [".json", ".jsonld"]:
        text = f.read().decode("utf-8")
        return json.loads(text)

    elif ext == ".csv":
        text = f.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        return [row for row in reader]

    elif ext in [".ttl", ".rdf", ".xml", ".nt", ".n3", ".trig", ".trix"]:
        rdf_format_dict = {".ttl": "turtle", ".rdf": "xml", ".xml": "xml",
            ".nt": "nt", ".n3": "n3", ".trig": "trig", ".trix": "trix"}
        g = Graph()
        content = f.read().decode("utf-8")
        g.parse(data=content, format=rdf_format_dict[ext])
        return g

    else:
        raise ValueError(f"Unsupported file extension: {ext}")  # should not happen

#__________________________________________________

#_______________________________________________________
#Function to get the number of TriplesMaps in a mapping
def get_number_of_tm(g):
    triplesmaps = [s for s in g.subjects(predicate=RML.logicalSource, object=None)]
    return len(triplesmaps)
#_________________________________________________________



# GLOBAL CONFIGURATION - SAVE MAPPING
#_________________________________________________
#Funtion to create the list that stores the state of the project
# project_state_list
# 0. [g_label, g_mapping]     1. g_ontology_components_dict      2. structural_ns_dict
# 3. db_connections_dict       4. db_connection_status_dict
# 5. ds_files_dict                6. sql_queries_dict
def save_project_state():

    # list to save the mapping
    mapping_list = []
    mapping_list.append(st.session_state["g_label"])
    mapping_list.append(st.session_state["g_mapping"])

    # list to save session
    project_state_list = []
    project_state_list.append(mapping_list)
    project_state_list.append(st.session_state["g_ontology_components_dict"])
    project_state_list.append(st.session_state["structural_ns"])
    project_state_list.append(st.session_state["db_connections_dict"])
    project_state_list.append(st.session_state["db_connection_status_dict"])
    project_state_list.append(st.session_state["ds_files_dict"])
    project_state_list.append(st.session_state["sql_queries_dict"])

    return project_state_list

#______________________________________________________

#_________________________________________________
#Funtion to retrieve the project state
def retrieve_project_state(project_state_list):

    st.session_state["g_mapping"] = project_state_list[0][1]
    st.session_state["g_label"] = project_state_list[0][0]
    st.session_state["g_ontology_components_dict"] = project_state_list[1]
    st.session_state["structural_ns"] = project_state_list[2]
    st.session_state["db_connections_dict"] = project_state_list[3]
    st.session_state["db_connection_status_dict"] = project_state_list[4]
    st.session_state["ds_files_dict"] = project_state_list[5]
    st.session_state["sql_queries_dict"] = project_state_list[6]

#______________________________________________________

#_________________________________________________
#Funtion to check that a filename is valid
def is_valid_filename(filename):  #HEREIGO

    excluded_characters = r"[\\/:*?\"<>| ]"
    windows_reserved_names = ["CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]

    if filename.endswith("."):
        st.markdown(f"""<div class="error-message">
            ❌ <b>Trailing "."</b> in filename.
            <small> Please, remove it.</small>
        </div>""", unsafe_allow_html=True)
        return False
    elif "." in filename:
        st.markdown(f"""<div class="error-message">
                ❌ The filename seems to include an <b>extension</b>.
                <small> Please, remove it.</b>
            </div>""", unsafe_allow_html=True)
        return False
    elif re.search(excluded_characters, filename):
        st.markdown(f"""<div class="error-message">
            ❌ <b>Forbidden character</b> in filename.
            <small> Please, pick a valid filename.</small>
        </div>""", unsafe_allow_html=True)
        return False
    else:
        for item in windows_reserved_names:
            if item == os.path.splitext(filename)[0].upper():
                st.markdown(f"""<div class="error-message">
                    ❌ <b>Reserved filename.</b><br>
                    <small>Please, pick a different filename.</small>
                </div>""", unsafe_allow_html=True)
                return False
                break  # Stop checking after first match

    return True

#______________________________________________________

# ONTOLOGIES----------------------------------------------------------------
#_________________________________________________________
# Function to get the ontology base iri
# Returns a list because the ontology can have several components
def get_ontology_base_iri():
    base_iri_list = []
    for s in st.session_state["g_ontology"].subjects(RDF.type, OWL.Ontology):
        try:
            split_uri(s)
            if is_valid_iri(split_uri(s)[0]):
                base_iri_list.append(split_uri(s)[0])
        except:
            if is_valid_iri(s):
                base_iri_list.append(s)

    return base_iri_list
#________________________________________________________

# GLOBAL CONFIGURATION - LOAD ONTOLOGY ----------------------------------------------------------
#___________________________________________________________________________________
#Function to parse an ontology to an initially empty graph
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

    return [Graph(), None]

#___________________________________________________________________________________

#___________________________________________________________________________________
#Function to check whether an ontology is valid
def is_valid_ontology(g):
    try:
        # check for presence of OWL or RDFS classes
        classes = list(g.subjects(RDF.type, OWL.Class)) + list(g.subjects(RDF.type, RDFS.Class))
        properties = (list(g.subjects(RDF.type, RDF.Property)) + list(g.subjects(RDF.type, OWL.DatatypeProperty)) +
            list(g.subjects(RDF.type, OWL.ObjectProperty)) + list(g.subjects(RDF.type, OWL.AnnotationProperty)))
        return bool(classes or properties)  # consider it valid if it defines at least one class or property

    except:           # if failed to parse ontology
        return False
#___________________________________________________________________________________

#___________________________________________________________________________________
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
#___________________________________________________________________________________

#___________________________________________________________________________________
#Function to get the human-readable name of an ontology
def get_ontology_tag(g_label):

    g = st.session_state["g_ontology_components_dict"][g_label]
    g_ontology_iri = next(g.subjects(RDF.type, OWL.Ontology), None)

    if g_ontology_iri:
        prefix = g.namespace_manager.compute_qname(g_ontology_iri)[0]
        return prefix

    return g_label[:4]
#___________________________________________________________________________________

#___________________________________________________________________________________
#Function to get all allowed formats for ontology files
def get_g_ontology_file_formats_dict():

    allowed_format_dict = {"owl": ".owl", "turtle": ".ttl", "longturtle": ".ttl", "n3": ".n3",
    "ntriples": ".nt", "nquads": "nq", "trig": ".trig", "jsonld": ".jsonld",
    "xml": ".xml", "pretty-xml": ".xml", "trix": ".trix"}

    return allowed_format_dict

#___________________________________________________________________________________

#___________________________________________________________________________________
#Function to check whether two ontologies overlap
#Ontology overlap definition - if they share rdfs:label
def check_ontology_overlap(g1, g2):
    labels1 = set()
    for s, p, o in g1.triples((None, RDFS.label, None)):
        labels1.add(str(o))

    labels2 = set()
    for s, p, o in g2.triples((None, RDFS.label, None)):
        labels2.add(str(o))

    common = labels1 & labels2
    return bool(common)
#___________________________________________________________________________________

#___________________________________________________________________________________
#Function to find duplicated namespaces
def get_duplicated_ns(d):
    value_to_keys = {}
    for key, value in d.items():
        if value in value_to_keys:
            value_to_keys[value].append(key)
        else:
            value_to_keys[value] = [key]

    # Filter to values that appear more than once
    duplicates = {value: keys for value, keys in value_to_keys.items() if len(keys) > 1}
    return duplicates
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
# Funtion to get the logical soruce of a TriplesMap
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
    subject_map = g.value(subject=tm_iri, predicate=RR.subjectMap)
    if subject_map:
        sm_reused = any(s != tm_iri for s, p, o in g.triples((None, RR.subjectMap, subject_map)))
        if not sm_reused:
            g.remove((subject_map, None, None))

    # remove all associated pom (and om)
    pom_iri_list = list(g.objects(subject=tm_iri, predicate=RR.predicateObjectMap))
    for pom_iri in pom_iri_list:
        om_to_delete = st.session_state["g_mapping"].value(subject=pom_iri, predicate=RR.objectMap)
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
    table_name_as_ds = next(st.session_state["g_mapping"].objects(ls_iri, RR.tableName), None)

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

        st.markdown(f"""<div class="info-message-blue">
                🛢️ The data source is <b>{ds}</b>.
            </div>""", unsafe_allow_html=True)

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
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ Logical source's query yielded no columns. <small>Please,
                        check the query in the <b>📊 Manage Logical Sources</b> page
                        to enable automatic column detection.
                        Manual entry of column references is discouraged.</small>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="info-message-blue">
                            📊 The data source is the database <b style="color:#F63366;">{database}</b>.<br>
                             <small>🔌 {conn_label} → <b>{jdbc_str}</b></small>
                        </div>""", unsafe_allow_html=True)

            except:
                st.markdown(f"""<div class="warning-message">
                    ⚠️ Connection to database or logical source's query failed.
                    <small>Please, check them in the <b>📊 Manage Logical Sources</b> page
                    to enable automatic column detection.
                    Manual entry of column references is discouraged.</small>

                </div>""", unsafe_allow_html=True)
                column_list = []

        elif table_name_as_ds:
            try:
                conn = utils.make_connection_to_db(conn_label)
                cur = conn.cursor()

                cur.execute(f"SELECT * FROM {table_name_as_ds} LIMIT 0")
                column_list = [desc[0] for desc in cur.description]

                conn.close()

                if not column_list:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ Table <b>{table_name_as_ds}</b> contains no columns.
                        <small>Please check the table definition in the <b>📊 Manage Logical Sources</b> page
                        to enable automatic column detection.
                        Manual entry of column references is discouraged.</small>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="info-message-blue">
                            📊 The data source is the database <b style="color:#F63366;">{database}</b>.<br>
                             <small>🔌 {conn_label} → <b>{jdbc_str}</b></small>
                        </div>""", unsafe_allow_html=True)

            except:
                st.markdown(f"""<div class="warning-message">
                    ⚠️ Failed to connect to the database or access table <b>{table_name_as_ds}</b>.
                    <small>Please verify the connection and table name in the <b>📊 Manage Logical Sources</b> page
                    to enable automatic column detection.
                    Manual entry of column references is discouraged.</small>
                </div>""", unsafe_allow_html=True)
                column_list = []

        else:
            st.markdown(f"""<div class="warning-message">
                ⚠️ Triple indicating either <code>RML.query</code> or <code>RR.tableName</code>
                is missing.<br>
                <small>Please check the <b>Logical Source</b> of the TriplesMap
                to enable automatic column detection.
                Manual entry of column references is discouraged.</small>
            </div>""", unsafe_allow_html=True)
            column_list = []

    elif query_as_ds:    # try to look for the columns in the query
        parsed = sqlglot.parse_one(query_as_ds)
        column_list = [str(col) for col in parsed.find_all(sqlglot.expressions.Column)]

        if column_list:
            st.markdown(f"""<div class="warning-message">
                    ⚠️ The data source <b>{ds}</b> is not available,
                    but column references have been taken from the
                    logical source's query.<br>
                    <small> However, connecting to the database is still recommended.</small>
                </div>""", unsafe_allow_html=True)

        else:
            st.markdown(f"""<div class="warning-message">
                    ⚠️ The data source <b>{ds}</b> is not available.
                    <small>Please load it in the <b>📊 Manage Logical Sources</b> page
                    to enable automatic column detection.
                    Manual entry of column references is strongly discouraged.</small>
                </div>""", unsafe_allow_html=True)


    else:                                                           # data source not saved
        if reference_formulation == QL.SQL:
            st.markdown(f"""<div class="warning-message">
                    ⚠️ The data source <b>{ds}</b> is not available.<br>
                    <small>Please connect to the database in the <b>📊 Manage Logical Sources</b> page
                    to enable automatic column detection.
                    Manual entry of column references is strongly discouraged.</small>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="warning-message">
                    ⚠️ The data source <b>{ds}</b> is not available.
                    <small>Please load it in the <b>📊 Manage Logical Sources</b> page
                    to enable automatic column detection.
                    Manual entry of column references is strongly discouraged.</small>
                </div>""", unsafe_allow_html=True)
        column_list = []

    return column_list
#________________________________________________________

#______________________________________________________
# Function get the column list of the data source of a tm
def get_column_list(tm_iri):

    ls_iri = next(st.session_state["g_mapping"].objects(tm_iri, RML.logicalSource), None)
    ds = str(next(st.session_state["g_mapping"].objects(ls_iri, RML.source), None))
    reference_formulation = next(st.session_state["g_mapping"].objects(ls_iri, QL.referenceFormulation), None)
    query_as_ds = next(st.session_state["g_mapping"].objects(ls_iri, RML.query), None)
    table_name_as_ds = next(st.session_state["g_mapping"].objects(ls_iri, RR.tableName), None)

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
        sm_iri = st.session_state["g_mapping"].value(tm, RR.subjectMap)

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

#________________________________________________________
# Funtion to get the dictionary of the superclasses in the ontology
def get_ontology_superclass_dict():
    pass


#________________________________________________________

#________________________________________________________
# Funtion to get exclusions when looking for predicates in an ontology
def get_exclusion_list_for_p_search():

    excluded_types = {
        # OWL structural types
        OWL.Class, OWL.Ontology, OWL.Restriction, OWL.FunctionalProperty,
        OWL.AnnotationProperty, OWL.ObjectProperty, OWL.DatatypeProperty,
        OWL.SymmetricProperty, OWL.TransitiveProperty, OWL.InverseFunctionalProperty,

        # RDF/RDFS structural types
        RDF.Property, RDF.Statement, RDF.List, RDF.Seq, RDF.Bag,
        RDF.Alt, RDF.XMLLiteral, RDFS.Class, RDFS.Resource, RDFS.Container,
        RDFS.ContainerMembershipProperty,
        URIRef("http://www.w3.org/2000/01/rdf-schema#Datatype"),

        # Legacy or datatype URIs
        XSD.string, XSD.integer, XSD.date, XSD.boolean, XSD.float, XSD.double}

    return excluded_types
#________________________________________________________

#________________________________________________________
# Funtion to identify the ontology from which a predicate was taken
def get_ontology_identifier(ns):

    parts = ns.rstrip("/").split("/")
    if len(parts) >= 2:
        return parts[-2]  # Last segment
    return None

#________________________________________________________

#________________________________________________________
# Funtion to get the predicates defined by the ontology
def get_ontology_defined_p():
    ontology_base_iri_list = get_ontology_base_iri()
    p_types_list = [RDF.Property, OWL.ObjectProperty, OWL.DatatypeProperty]
    p_exclusion_list = [RDFS.label, RDFS.comment, OWL.versionInfo, OWL.deprecated, RDF.type]

    p_set = set()

    for s, p, o in st.session_state["g_ontology"].triples((None, RDF.type, None)):
        if o in p_types_list:
            if ontology_base_iri_list:
                if str(s).startswith(tuple(ontology_base_iri_list)) and s not in p_exclusion_list:
                    p_set.add(s)
            else:
                if s not in p_exclusion_list:
                    p_set.add(s)

    return sorted(list(p_set))
#______________________________________________

#________________________________________________________
# Funtion to get the predicates defined by the ontology
def get_ontology_component_defined_p(ont):
    ontology_base_iri_list = get_ontology_base_iri()
    p_types_list = [RDF.Property, OWL.ObjectProperty, OWL.DatatypeProperty]
    p_exclusion_list = [RDFS.label, RDFS.comment, OWL.versionInfo, OWL.deprecated, RDF.type]

    p_set = set()

    for s, p, o in ont.triples((None, RDF.type, None)):
        if o in p_types_list:
            if ontology_base_iri_list:
                if str(s).startswith(tuple(ontology_base_iri_list)) and s not in p_exclusion_list:
                    p_set.add(s)
            else:
                if s not in p_exclusion_list:
                    p_set.add(s)

    return sorted(list(p_set))
#______________________________________________


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
    pom_list = list(st.session_state["g_mapping"].objects(None, RR.predicateObjectMap))

    for pom_iri in pom_list:

        tm_iri = next(st.session_state["g_mapping"].subjects(RR.predicateObjectMap, pom_iri), None)
        tm_label = split_uri(tm_iri)[1]
        predicate = st.session_state["g_mapping"].value(pom_iri, RR.predicate)
        om_iri = st.session_state["g_mapping"].value(pom_iri, RR.objectMap)

        template = st.session_state["g_mapping"].value(om_iri, RR.template)
        constant = st.session_state["g_mapping"].value(om_iri, RR.constant)
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

        pom_dict[pom_iri] = [tm_iri, tm_label, pom_label, predicate, predicate_label, om_label, om_type, om_id_iri, om_id_label]

    return pom_dict
#___________________________________________

#________________________________________________________
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

#___________________________________________

#________________________________________________________
# Funtion to update the connection status dict
def update_db_connection_status_dict(connection_label):

    try:
        conn = utils.make_connection_to_db(connection_label)
        if conn:
            conn.close() # optional: close immediately or keep open for queries
        st.session_state["db_connection_status_dict"][connection_label] = ["✔️", ""]

    except Exception as e:
        st.session_state["db_connection_status_dict"][connection_label] = ["❌", e]

#___________________________________________

#________________________________________________________
# Dictionary with default ports for the different engines
def get_default_ports():

    default_ports_dict = {"PostgreSQL": 5432, "MySQL": 3306,
    "MariaDB": 3306, "SQL Server": 1433, "Oracle": 1521}

    return default_ports_dict
#___________________________________________

#________________________________________________________
# Funtion with the default users for the different engines
def get_default_users():

    default_users_dict = {"PostgreSQL": "postgres", "MySQL": "root",
    "MariaDB": "root", "SQL Server": "sa", "Oracle": "system"}

    return default_users_dict
#___________________________________________

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
#___________________________________________

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
# Funtion to get jdbc str from connection
def get_jdbc_str(conn):

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

    return jdbc_str

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

    return db_url_str

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
        if not any(g.triples((tm_iri, RR.subjectMap, None))):
            tm_wo_sm_list.append(tm_label)
    for tm_label, tm_iri in tm_dict.items():
        if not any(g.triples((tm_iri, RR.predicateObjectMap, None))):
            tm_wo_pom_list.append(tm_label)

    pom_wo_om_list = []
    pom_wo_predicate_list = []
    for pom_iri in g.subjects(RDF.type, RR.PredicateObjectMap):
        pom_label = get_node_label(pom_iri)
        if not any(g.triples((pom_iri, RR.objectMap, None))):
            pom_wo_om_list.append(pom_label)
        if not any(g.triples((pom_iri, RR.predicate, None))):
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

#HEREIGO






#F63366 Streamlit salmon
#f26a7e Streamlit salmon less saturated
#ff7a7a lighter streamlit salmon

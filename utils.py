import streamlit as st
import os
import pandas as pd
import re
from collections import Counter
from urllib.parse import urlparse
import pickle
import json
import csv
import rdflib
from rdflib import Graph, URIRef, Literal, Namespace, BNode
from rdflib.namespace import split_uri
from rdflib.namespace import RDF, RDFS, DC, DCTERMS, OWL


#________________________________________________
# Function to import style
def import_st_aesthetics():
    ##ff7a7a lighter streamlit salmon

    # TABS ----------------------------------
    st.markdown("""<style>

        div[data-testid="stTabs"] > div {
        flex-wrap: wrap; justify-content: space-between;}

        div[data-testid="stTabs"] button {flex: 1 1 auto;
        background-color: #555555; color: white; font-size: 25px;
        padding: 1.2em; border-radius: 5px; border: none;margin: 6px;}

        div[data-testid="stTabs"] button div span {font-size: 36px !important;}

        div[data-testid="stTabs"] button:hover {background-color: #7a4c8f;}

        div[data-testid="stTabs"] button[aria-selected="true"] {
            background-color: #9871b5; color: white; font-weight: bold;
            box-shadow: 0 0 10px #9871b5;}

        </style>""", unsafe_allow_html=True)

    # MAIN BUTTONS ---------------------------
    st.markdown("""<style>

        div.stButton > button {
            background-color: #555555;
            color: white;
            height: 2.4em;
            width: auto;
            border-radius: 6px;
            border: 1px solid #FFD3C4;
            font-size: 16px;
            padding: 0.4em 1em;
            transition: background-color 0.2s ease;
        }

        div.stButton > button:hover {
            background-color: #FF4B4B;  /* Streamlit salmon orange */
            color: white;
        }

    </style>""", unsafe_allow_html=True)

    # MULTISELECT --------------------------------------
    st.markdown("""
        <style>
        div[data-baseweb="select"] > div {
        color: black !important;
        }
        div[data-baseweb="select"] span {
        background-color: #d3d3d3 !important;  /* Light gray */
        color: black !important;
        }
        </style>
        """, unsafe_allow_html=True)

    # PURPLE HEADINGS ----------------------------------
    st.markdown("""
        <style>
            .purple_heading {background-color:#e6e6fa; border:1px solid #511D66;
                border-radius:5px; padding:10px; margin-bottom:8px;
                font-size:1.1rem; font-weight:600; color:#511D66;}
        </style>
    """, unsafe_allow_html=True)

    # FILE UPLOADER -------------------------------------
    st.markdown("""<style>

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

        </style>""", unsafe_allow_html=True)


#_______________________________________________________


#_______________________________________________________
#List of allowed mapping file format
#HERE expand options, now reduced version
def get_g_mapping_file_formats_dict():
    # allowed_format_dict = {"pickle": ".pkl", "turtle": ".ttl", "rdf": ".rdf","xml": ".xml",
    #     "json": ".json", "json-ld": ".jsonld", "n-triples": ".nt",
    #     "n3": ".n3","trig": ".trig","trix": ".trix"}

    allowed_format_dict = {"pickle": ".pkl", "turtle": ".ttl"}

    return allowed_format_dict
#_______________________________________________________

#_______________________________________________________
#Funcion to save mapping to file
#HERE check all formats work
def save_mapping_to_file(filename):

    save_mappings_folder = os.path.join(os.getcwd(), "saved_mappings")  #folder to save mappings
    if not os.path.isdir(save_mappings_folder):   # create folder if it does not exist
        os.makedirs(save_mappings_folder)

    ext = os.path.splitext(filename)[1].lower()  #file extension

    file_path = save_mappings_folder + "\\" + filename

    if ext == ".pkl":
        with open(file_path, "wb") as f:    # save current mapping to pkl file
            pickle.dump(st.session_state["g_mapping"], f)

    elif ext in [".json", ".jsonld"]:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(st.session_state["g_mapping"], f, indent=2)

    elif ext in [".ttl", ".rdf", ".xml", ".nt", ".n3", ".trig", ".trix"]:
        rdf_format_dict = {".ttl": "turtle", ".rdf": "xml",
            ".xml": "xml", ".nt": "nt", ".n3": "n3",
            ".trig": "trig", ".trix": "trix"}

        st.session_state["g_mapping"].serialize(destination=file_path, format=rdf_format_dict[ext])

    else:
        raise ValueError(f"Unsupported file extension: {ext}")   #should not occur

#__________________________________________________



#_______________________________________________________
#Funcion to load mapping from file
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

#___________________________________________________________________________________
#Function to parse an ontology to an initially empty graph
@st.cache_resource
def parse_ontology(source):
    g = Graph()
    for fmt in ["xml", "turtle", "json-ld", "ntriples", "trig", "trix"]:
        try:
            g.parse(source, format=fmt)
            if len(g) != 0:
                return g
        except:
            continue
    return g
#___________________________________________________________________________________

#___________________________________________________________________________________
#Function to check whether an ontology is valid
def is_valid_ontology(url: str):
    try:
        g = parse_ontology(url)

        # Check for presence of OWL or RDFS classes
        classes = list(g.subjects(RDF.type, OWL.Class)) + list(g.subjects(RDF.type, RDFS.Class))
        properties = list(g.subjects(RDF.type, RDF.Property))

        # Consider it valid if it defines at least one class or property
        return bool(classes or properties)

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
        return source_file
    else:                                 # if no source is given, auto-label using subject of first triple (if it is iri)
        for s in g.subjects(None, None):
            if isinstance(s, URIRef):
                return "Auto-label: " + split_uri(s)[1]
    return "Unlabelled ontology"  #if nothing works
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


#HEREIGO

#_________________________________________________________
def get_ontology_base_iri():
    for s in st.session_state["g_ontology"].subjects(RDF.type, OWL.Ontology):
        try:
            split_uri(s)
            if is_valid_iri(split_uri(s)[0]):
                return split_uri(s)[0]
        except:
            if is_valid_iri(s):
                return s

    return get_rdfolio_base_iri()

#________________________________________________________

#_________________________________________________________
def get_rdfolio_base_iri():
    return "http://rdfolio.org/"

#________________________________________________________


#_________________________________________________________
#Dictionary with predefined namespaces
def get_predefined_ns_dict():
    return {
        "rml": Namespace("http://semweb.mmlab.be/ns/rml#"),
        "rr": Namespace("http://www.w3.org/ns/r2rml#"),
        "xsd": Namespace("http://www.w3.org/2001/XMLSchema#"),
        "rdf": Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
        "ql": Namespace(get_rdfolio_base_iri() + "/ql#"),
        "map": Namespace(get_rdfolio_base_iri() + "/mapping#"),
        "class": Namespace(get_rdfolio_base_iri() + "/class#"),
        "resource": Namespace(get_rdfolio_base_iri() + "/resource#"),
        "logicalSource": Namespace(get_rdfolio_base_iri() + "/logicalSource#")
    }

namespaces = get_predefined_ns_dict()
RML = namespaces["rml"]
RR = namespaces["rr"]
QL = namespaces["ql"]
MAP = namespaces["map"]
CLASS = namespaces["class"]
LS = namespaces["logicalSource"]
#________________________________________________________

#______________________________________________
#Directories    #REFACTORING - Unused, but could be interesting to check if the permissions are correct
def check_directories():
    save_progress_folder = os.path.join(os.getcwd(), "saved_mappings")  #folder to save mappings (pkl)
    export_folder = os.path.join(os.getcwd(), "exported_mappings")    #filder to export mappings (ttl and others)
    if not os.path.exists(save_progress_folder):
        st.markdown(f"""<div style="background-color:#f8d7da; padding:1em;
            border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
            🚫 The folder <b style="color:#c82333;">
            saved_mappings</b> does not exist and must be created!
            </div>""", unsafe_allow_html=True)
        st.stop()

    if not os.access(save_progress_folder, os.R_OK | os.W_OK):
        st.markdown(f"""
            <div style="background-color:#f8d7da; padding:1em;
            border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
            🚫 No read/write permission for <b style="color:#c82333;">
            saved_mappings</b> folder!
            </div>""", unsafe_allow_html=True)
        st.stop()

    if not os.path.exists(export_folder):
        st.markdown(f"""
            <div style="background-color:#f8d7da; padding:1em;
            border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
            🚫 The folder <b style="color:#c82333;">
            exported_mappings</b> does not exist and must be created!
            </div>""", unsafe_allow_html=True)
        st.stop()

    if not os.access(export_folder, os.R_OK | os.W_OK):
        st.markdown(f"""
            <div style="background-color:#f8d7da; padding:1em;
            border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
            🚫 No read/write permission for <b style="color:#c82333;">
            export</b> folder!
            </div>""", unsafe_allow_html=True)
        st.stop()

#__________________________________________

#_________________________________________________________
#Confirm button
def get_confirm_button():
    col1,col2,col3 = st.columns([1,1,10])
    with col1:
        button_YES = st.button("Yes")
    with col2:
        button_NO = st.button("No")
    if button_YES:
        return True
    if button_NO:
        return False


#_________________________________________________________
#Dictionary with predefined namespaces
def get_default_ns_dict():
    return {
    "brick": "https://brickschema.org/schema/Brick#",
    "csvw": "http://www.w3.org/ns/csvw#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcam": "http://purl.org/dc/dcam/",
    "dcat": "http://www.w3.org/ns/dcat#",
    "dcmitype": "http://purl.org/dc/dcmitype/",
    "dcterms": "http://purl.org/dc/terms/",
    "doap": "http://usefulinc.com/ns/doap#",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "geo": "http://www.opengis.net/ont/geosparql#",
    "odrl": "http://www.w3.org/ns/odrl/2/",
    "org": "http://www.w3.org/ns/org#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "prof": "http://www.w3.org/ns/dx/prof/",
    "prov": "http://www.w3.org/ns/prov#",
    "qb": "http://purl.org/linked-data/cube#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "sdo": "https://schema.org/",
    "sh": "http://www.w3.org/ns/shacl#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "sosa": "http://www.w3.org/ns/sosa/",
    "ssn": "http://www.w3.org/ns/ssn/",
    "time": "http://www.w3.org/2006/time#",
    "vann": "http://purl.org/vocab/vann/",
    "void": "http://rdfs.org/ns/void#",
    "xml": "http://www.w3.org/XML/1998/namespace",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "schema": "https://schema.org/",
    "wgs": "https://www.w3.org/2003/01/geo/wgs84_pos#"
    }
#________________________________________________________


#_________________________________________________________
#Dictionary with predefined namespaces  HERE NOT USED
def get_inverse_dict(my_dict):
    return {v: k for k, v in my_dict.items()}
#_________________________________________________________

#_________________________________________________
#Function to check whether an IRI is valid
def is_valid_iri(iri):
    valid_iri_schemes = ("http://", "https://", "ftp://", "mailto:",
    "urn:", "tag:", "doi:", "data:"
    )
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

#_________________________________________________
#Allowed data formats
def get_ds_allowed_formats():
    allowed_formats_list = (".csv",".json", ".xml")
    return allowed_formats_list


#_________________________________________________


#________________________________________________
#Update DICTIONARIES
def update_dictionaries():

    st.session_state["tmap_dict"] = {}
    st.session_state["data_source_dict"] = {}
    st.session_state["subject_dict"] = {}
    st.session_state["ns_dict"] = {}

    if st.session_state["g_label"]:

        #{TripleMap label: TripleMap}
        triples_maps = list(st.session_state["g_mapping"].subjects(RML.logicalSource, None))
        for tm in triples_maps:
            tm_label = split_uri(tm)[1]
            st.session_state["tmap_dict"][tm_label] = tm

        #{TripleMap label: data source}
        for tmap_label, tmap_node in st.session_state["tmap_dict"].items():
            data_source = get_data_source_file(st.session_state["g_mapping"], tmap_node)
            st.session_state["data_source_dict"][tmap_label] = data_source

        #{prefix: namespace} only custom
        default_ns_dict = get_default_ns_dict()
        all_mapping_ns_dict = dict(st.session_state["g_mapping"].namespace_manager.namespaces())
        st.session_state["mapping_ns_dict"] = {k: v for k, v in all_mapping_ns_dict.items() if (k not in default_ns_dict and v != URIRef("None"))}

        #{prefix: namespace} only ontology
        st.session_state["ontology_ns_dict"] = dict(st.session_state["g_ontology"].namespace_manager.namespaces())

        #{prefix: namespace} custom+ontology
        st.session_state["ns_dict"] = st.session_state["mapping_ns_dict"] | st.session_state["ontology_ns_dict"]

        #subject dictionary   {tm label: [subject_label, subject_id, subject_type]}
        st.session_state["subject_dict"] = {}
        triples_maps = list(st.session_state["g_mapping"].subjects(RML.logicalSource, None))
        for tm in triples_maps:
            tm_label = split_uri(tm)[1]
            subject_map = st.session_state["g_mapping"].value(tm, RR.subjectMap)

            subject = None
            subject_type = None
            subject_id = None

            template = st.session_state["g_mapping"].value(subject_map, RR.template)
            constant = st.session_state["g_mapping"].value(subject_map, RR.constant)
            reference = st.session_state["g_mapping"].value(subject_map, RML.reference)

            if isinstance(subject_map, URIRef):
                subject_label = split_uri(subject_map)[1]
            elif isinstance(subject_map, BNode):
                subject_label = "_:" + str(subject_map)[:7] + "..."
            else:
                subject_label = "Unlabelled"

            if template:
                matches = re.findall(r"{([^}]+)}", template)   #splitting template is not so easy but we try
                if matches:
                    subject = str(template)
                    subject_type = "template"
                    subject_id = str(matches[-1])
                else:
                    subject = str(template)
                    subject_type = "template"
                    subject_id = str(template)

            elif constant:
                subject = str(constant)
                subject_type = "constant"
                subject_id = str(split_uri(constant)[1])

            elif reference:
                subject = str(reference)
                subject_type = "reference"
                subject_id = str(reference)

            st.session_state["subject_dict"][tm_label] = [subject, subject_id, subject_type, subject_label]   # add to dict
#___________________________________________


#___________________________________________________________________________________
#Functions to get the file name and path of the data source files  HERE FIX

def get_ds_full_path(filename):
    folder_path = get_ds_folder_path()
    full_path = os.path.join(folder_path, filename)
    return full_path

def get_ds_folder_path():
    folder_path = os.path.abspath(".\\data_sources")
    return folder_path

def get_g_full_path(filename):
    folder_path = get_g_folder_path()
    full_path = os.path.join(folder_path, filename)
    return full_path

def get_g_folder_path():
    folder_path = os.path.abspath(".\\saved_mappings")
    return folder_path

def show_ds_file_path_success():   #FIX HERE
    graph_filename = get_filename()
    st.markdown(
    f"""<span style="color:grey; font-size:16px;">
    <div style="line-height: 1.5;border: 1px solid blue; padding: 10px; border-radius: 5px;">
    You are currently working with the file
    <span style="color:blue; font-weight:bold;">{graph_filename}</span>.
    To change the file go to \"Select graph\".</div></span>
    """,
    unsafe_allow_html=True)

#___________________________________________



#___________________________________________________________________________________
#Function to save new maps in a dictionary: {map name: map}
def get_map_dict(map_label, map_dict):   #HERE FIX

    if map_label in map_dict:
        st.warning("Map label already in use, please pick another label.")
        st.stop()

    map_dict[map_label] = BNode()

    return map_dict



#___________________________________________________________________________________
#Function to create new map: assign name, data source and data format
#It also builds a dictionary to save the new maps: {map name: map}
def add_logical_source(g, tmap_label, source_file, logical_source_iri):

    tmap_iri = MAP[f"{tmap_label}"]

    g.add((tmap_iri, RML.logicalSource, logical_source_iri))    #bind to logical source
    g.add((logical_source_iri, RML.source, Literal(source_file)))    #bind to source file

    file_extension = source_file.rsplit(".", 1)[-1]    # bind to reference formulation
    if file_extension.lower() == "csv":
        g.add((logical_source_iri, QL.referenceFormulation, QL.CSV))
    elif file_extension.lower() == "json":
        g.add((logical_source_iri, QL.referenceFormulation, QL.JSONPath))
    elif file_extension.lower() == "xml":
        g.add((logical_source_iri, QL.referenceFormulation, QL.XPath))
    else:
        raise ValueError(f"Unsupported format: {file_extension}")   #this wont happen, since only allowed extensions are given in selectbox

#___________________________________________________________________________________


#___________________________________________________________________________________
#Function to get the data source file of a given map
def get_data_source_file(g, map_node):

    logical_source = next(g.objects(map_node, RML.logicalSource), None)

    source_file = None          # get the associated source file (if found)
    if logical_source:
        source_file_literal = next(g.objects(logical_source, RML.source), None)
        if isinstance(source_file_literal, Literal):
            source_file = str(source_file_literal)

    return source_file


#_____________________________________________________________________________

#___________________________________________________________________________________
#Function to remove a map from the graph
def remove_map(g, map_label, map_dict):

    map_node = map_dict[map_label]

    map_logical_source = next(g.objects(map_node, RML.logicalSource), None)

    g.remove((map_node, None, None))   #remove the triplet of the map
    g.remove((map_logical_source, None, None))   #remove triplets of the map logical source
    map_dict.pop(map_label, None)

    return map_dict

#___________________________________________________________________________________


#___________________________________________________________________________________
#Function to add subjects
def add_subject_map_template(g, tmap_label, smap_label, s_generation_type, subject_id):   #HERE DELETE

    tmap_iri = st.session_state["tmap_dict"][tmap_label]
    smap_iri = MAP[f"{smap_label}"]

    g.add((tmap_iri, RR.subjectMap, smap_iri))
    g.add((smap_iri, RR.template, Literal(f"http://example.org/resource/{subject_id}")))

#___________________________________________________________________________________

#___________________________________________________________________________________
#Function to build triplesmap dataframe
def build_tmap_df():

    update_dictionaries()
    tmap_rows = []

    if not st.session_state["tmap_dict"]:   #if there is no triplesmap in g
        tmap_rows.append({
            "TriplesMap Label": None,
            "Data Source": None,
            "Logical Source Label": None,
            "TriplesMap IRI": None,
        })

    else:

        for tmap_label, tmap_iri in st.session_state["tmap_dict"].items():

            ls_iri = st.session_state["g_mapping"].value(subject=tmap_iri, predicate=RML.logicalSource)
            if isinstance(ls_iri, URIRef):
                ls_label = split_uri(ls_iri)[1]
            elif isinstance(ls_iri, BNode):
                ls_label = "_:" + str(ls_iri)[:7] + "..."
            else:
                ls_label = "Unlabelled"

            data_source = st.session_state["g_mapping"].value(subject=ls_iri, predicate=RML.source)

            tmap_rows.append({
                "TriplesMap Label": tmap_label,
                "Logical Source Label": ls_label,
                "Data Source": data_source,
                "TriplesMap IRI": tmap_iri,
            })

    return pd.DataFrame(tmap_rows).iloc[::-1]

#___________________________________________________________________________________



#___________________________________________________________________________________
#Function to build subject dataframe
def build_subject_df():

    update_dictionaries()
    subject_rows = []

    if not st.session_state["tmap_dict"]:   #if there is no triplesmap in g
        subject_rows.append({
            "TriplesMap Label": None,
            "Data Source": None,
            "Subject Label": None,
            "Subject Rule": None,
            "Subject": None,
            "TriplesMap IRI": None
        })

    else:

        for tmap_label in st.session_state["tmap_dict"]:
            subject_info = st.session_state["subject_dict"].get(tmap_label, ["", "", ""])
            if subject_info[1]:
                subject_rows.append({
                    "TriplesMap Label": tmap_label,
                    "Data Source": st.session_state["data_source_dict"].get(tmap_label, ""),
                    "Subject Label": subject_info[3],
                    "Subject Rule": subject_info[2],
                    "Subject": subject_info[1],
                    "TriplesMap IRI": st.session_state["tmap_dict"][tmap_label]
                })

    return pd.DataFrame(subject_rows).iloc[::-1]

#___________________________________________________________________________________


#___________________________________________________________________________________
#Function to build subject dataframe (complete)
def build_complete_subject_df():

    subject_rows = []
    for tmap_label, tmap_iri in st.session_state["tmap_dict"].items():

        subject_bnode = st.session_state["g_mapping"].value(subject=tmap_iri, predicate=RR.subjectMap)
        subject_class = st.session_state["g_mapping"].value(subject=subject_bnode, predicate=RR["class"])
        if subject_class:
            subject_class = split_uri(subject_class)[1]


        subject_term_type = st.session_state["g_mapping"].value(subject=subject_bnode, predicate=RR.termType)
        if subject_term_type:
            subject_term_type = split_uri(subject_term_type)[1]

        subject_graph = st.session_state["g_mapping"].value(subject=subject_bnode, predicate=RR.graph)
        if subject_graph:
            subject_graph = split_uri(subject_graph)[1]

        subject_info = st.session_state["subject_dict"].get(tmap_label, ["", "", ""])
        if subject_info[1]:
            subject_rows.append({
                "TriplesMap Label": tmap_label,
                "Data Source": st.session_state["data_source_dict"].get(tmap_label, ""),
                "Subject Label": subject_info[3],
                "Subject Rule": subject_info[2],
                "Subject": subject_info[1],
                "Subject class": subject_class,
                "Subject term type": subject_term_type,
                "Subject graph": subject_graph
            })

    return pd.DataFrame(subject_rows)

#___________________________________________________________________________________



#_________________________________________________________________________________
#Function to get primary triples of a node
#primary triples are the ones for which the node is either a subject or a predicate
def get_primary_triples(x_node):

    update_dictionaries()   #create a list with all triplesmaps
    g = st.session_state["g_mapping"]   #for convenience

    primary_triples = list(g.triples((x_node, None, None))) + list(g.triples((None, None, x_node)))

    return primary_triples
#______________________________________________________


#_________________________________________________________________________________
#Function to get secondary triples of a node
#secondary triples are recursively related to the node, but are not primary triples
def get_secondary_triples(x_node):

    update_dictionaries()   #create a list with all triplesmaps
    g = st.session_state["g_mapping"]   #for convenience

    primary_triples = get_primary_triples(x_node)

    #look for secondary triples recursively
    secondary_triples = []
    visited_nodes = set()
    stack_nodes = [x_node]

    #step 1: collect primary and related nodes
    while stack_nodes:
        current = stack_nodes.pop()
        if current in visited_nodes:
            continue
        visited_nodes.add(current)

        #collect predicates and objects for outgoing triples
        for p, o in g.predicate_objects(current):
            if isinstance(o, (BNode, URIRef)) and o not in visited_nodes:
                stack_nodes.append(o)
                if (current, p, o) not in primary_triples:
                    secondary_triples.append((current, p, o))

        #collect subjects and predicates for incoming triples
        for s, p in g.subject_predicates(current):
            if isinstance(s, (BNode, URIRef)) and s not in visited_nodes:
                stack_nodes.append(s)
                if (s, p, current) not in primary_triples:
                    secondary_triples.append((s, p, current))

    return secondary_triples
#______________________________________________________

#_________________________________________________________________________________
#Function to get triples derived from a triplesmap
#derived triples are defined for the tmap case
def get_tmap_derived_triples(x_tmap_label):

    # #list of all triplesmaps
    # tm_iri_list = []
    # for tm_iri in st.session_state["tmap_dict"].values():
    #     tm_list.append(tm_iri)

    x_tmap_iri = st.session_state["tmap_dict"][x_tmap_label]   #get tmap iri
    update_dictionaries()   #create a list with all triplesmaps
    g = st.session_state["g_mapping"]   #for convenience
    derived_triples = set()

    #get subjectMap and logicalSource directly
    for p, o in g.predicate_objects(x_tmap_iri):
        if p in [RR.subjectMap, RML.logicalSource]:
            derived_triples.add((x_tmap_iri, p, o))

            #follow the blank node (or URI) and extract its internal triples
            if isinstance(o, (BNode, URIRef)):
                for sp, so in g.predicate_objects(o):
                    #focus only on expected predicates inside subjectMap
                    if sp in [RR["class"], RR.termType, RR.graphMap, RR.template, RR.constant, RML.reference, QL.referenceFormulation]:
                        derived_triples.add((o, sp, so))

                        #optionally follow graphMap HERE FURTHER WORK
                        # if sp == RR.graphMap and isinstance(so, (BNode, URIRef)):
                        #     for gp, go in g.predicate_objects(so):
                        #         derived_triples.add((so, gp, go))

    return list(derived_triples)
#______________________________________________________


#_________________________________________________________________________________
#Function to get triples derived from a triplesmap that are not derived from any other triplesmap
def get_tmap_exclusive_derived_triples(x_tmap_label):

    x_tmap_iri = st.session_state["tmap_dict"][x_tmap_label]   #get tmap iri
    update_dictionaries()   #create a list with all triplesmaps
    g = st.session_state["g_mapping"]   #for convenience
    x_derived_triples_list = get_tmap_derived_triples(x_tmap_label) #triples derived from x_tmap


    y_derived_triples_list = []
    for y_tmap_label in st.session_state["tmap_dict"]:
        if y_tmap_label != x_tmap_label:   #skip x_tmap_label
            y_derived_triples_list += get_tmap_derived_triples(y_tmap_label)

    exclusive_derived_triples_list = [item for item in x_derived_triples_list if item not in y_derived_triples_list]

    return exclusive_derived_triples_list
#______________________________________________________



#_________________________________________________________________________________
#Function to completely remove a triplesmap
#remove primary and secondary triples, but dont remove any triples that are used by another triplesmap
def remove_triplesmap(tmap_label):

    tmap = st.session_state["tmap_dict"][tmap_label]   #get tmap iri
    g = st.session_state["g_mapping"]  #for convenience
    removed_triples=[]

    logical_source = g.value(subject=tmap, predicate=RML.logicalSource)
    subject_map = g.value(subject=tmap, predicate=RR.subjectMap)

    triples = list(g.triples((tmap, None, None)))
    removed_triples += list(g.triples((tmap, None, None)))
    g.remove((tmap, None, None))

    if logical_source:
        ls_reused = any(s != tmap for s, p, o in g.triples((None, RML.logicalSource, logical_source)))
        if not ls_reused:
            removed_triples += list(g.triples((logical_source, None, None)))
            g.remove((logical_source, None, None))

    if subject_map:
        sm_reused = any(s != tmap for s, p, o in g.triples((None, RR.subjectMap, subject_map)))
        if not sm_reused:
            removed_triples += list(g.triples((subject_map, None, None)))
            g.remove((subject_map, None, None))

    return removed_triples

#______________________________________________________



#_____________________________________________________________________________

#SPECIAL BUTTON (GREY)
# st.markdown('<span id="custom-style-marker"></span>', unsafe_allow_html=True)
# s_show_info_button = st.button("ℹ️ Show information")
# st.markdown("""
#     <style>
#     .element-container:has(#custom-style-marker) + div button {
#         background-color: #eee;
#         font-size: 0.75rem;
#         color: #444;
#     }
#     </style>
# """, unsafe_allow_html=True)

#___________________________________________________________________________________
#FORMAT GLOSSARY

#Custom success
# st.markdown(f"""
# <div style="background-color:#d4edda; padding:1em;
# border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
#     ✅ The mapping <b style="color:#007bff;">{st.session_state["candidate_g_label"]}
#     </b> has been created! <br> (and mapping
#     <b style="color:#0f5132;"> {st.session_state["g_label"]} </b>
#     has been overwritten).  </div>
# """, unsafe_allow_html=True)

#Custom warning
# st.markdown(f"""
#     <div style="background-color:#fff3cd; padding:1em;
#     border-radius:5px; color:#856404; border:1px solid #ffeeba;">
#         ⚠️ The mapping <b style="color:#cc9a06;">{st.session_state["g_label"]}</b> is already loaded! <br>
#         If you continue, it will be overwritten.</div>
# """, unsafe_allow_html=True)

#Custom error
# st.markdown(f"""
# <div style="background-color:#f8d7da; padding:1em;
#             border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
#     ❌ File <b style="color:#a94442;">{save_g_filename + ".pkl"}</b> already exists!<br>
#     Please choose a different filename.
# </div>
# """, unsafe_allow_html=True)

#information box
# st.markdown(f"""
#     <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
#         <span style="font-size:0.95rem;">
#             <b> 📐 Template use case </b>: <br>Dynamically construct the subject IRI using data values.
#         </span>
#     </div>
#     """, unsafe_allow_html=True)

#🛈
#Neutral blue for text: #007bff

#___________________________________________________________________________________

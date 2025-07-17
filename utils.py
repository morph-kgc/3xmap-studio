import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
from collections import Counter
import re
from urllib.parse import urlparse
import pandas as pd
from rdflib.namespace import split_uri
from rdflib.namespace import RDF, RDFS, OWL
OWL_NS = OWL


#_________________________________________________________
#Dictionary with predefined namespaces
def get_predefined_ns_dict():
    return {
        "rr": Namespace("http://www.w3.org/ns/r2rml#"),
        "rml": Namespace("http://semweb.mmlab.be/ns/rml#"),
        "ql": Namespace("http://semweb.mmlab.be/ns/ql#"),
        "map": Namespace("http://example.org/mapping#"),
        "subj": Namespace("http://example.org/subject#"),
        "ex": Namespace("http://example.org/ns#"),
        "class": Namespace("http://example.org/class#"),
        "resource": Namespace("http://example.org/resource#"),
        "logicalSource": Namespace("http://example.org/logicalSource#"),
        "foaf": Namespace("http://xmlns.com/foaf/0.1/")
    }

namespaces = get_predefined_ns_dict()
RML = namespaces["rml"]
RR = namespaces["rr"]
QL = namespaces["ql"]
MAP = namespaces["map"]
SUBJ = namespaces["subj"]
EX = namespaces["ex"]
CLASS = namespaces["class"]
#________________________________________________________


#______________________________________________
#Directories
def check_directories():
    save_progress_folder = os.path.join(os.getcwd(), "saved_mappings")  #folder to save mappings (pkl)
    export_folder = os.path.join(os.getcwd(), "exported_mappings")    #filder to export mappings (ttl and others)
    if not os.path.exists(save_progress_folder):
        st.markdown(f"""
            <div style="background-color:#f8d7da; padding:1em;
                        border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                🚫 The folder <b style="color:#c82333;">
                saved_mappings</b> does not exist and must be created!
            </div>
        """, unsafe_allow_html=True)
        st.stop()

    if not os.access(save_progress_folder, os.R_OK | os.W_OK):
        st.markdown(f"""
            <div style="background-color:#f8d7da; padding:1em;
                        border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                🚫 No read/write permission for <b style="color:#c82333;">
                saved_mappings</b> folder!
            </div>
        """, unsafe_allow_html=True)
        st.stop()

    if not os.path.exists(export_folder):
        st.markdown(f"""
            <div style="background-color:#f8d7da; padding:1em;
                        border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                🚫 The folder <b style="color:#c82333;">
                exported_mappings</b> does not exist and must be created!
            </div>
        """, unsafe_allow_html=True)
        st.stop()

    if not os.access(export_folder, os.R_OK | os.W_OK):
        st.markdown(f"""
            <div style="background-color:#f8d7da; padding:1em;
                        border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                🚫 No read/write permission for <b style="color:#c82333;">
                export</b> folder!
            </div>
        """, unsafe_allow_html=True)
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

        #{prefix: namespace}
        default_ns_dict = get_default_ns_dict()
        all_ns_dict = dict(st.session_state["g_mapping"].namespace_manager.namespaces())
        st.session_state["ns_dict"] = {k: v for k, v in all_ns_dict.items() if k not in default_ns_dict}

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

            st.session_state["subject_dict"][tm_label] = [subject, subject_id, subject_type]   # add to dict
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
def add_logical_source(g, tmap_label, source_file):

    namespaces = get_predefined_ns_dict()
    RML = namespaces["rml"]
    QL = namespaces["ql"]
    MAP = namespaces["map"]
    LS = namespaces["logicalSource"]

    # tmap_iri = MAP[f"{tmap_label}TriplesMap"]      #in case we want to add TriplesMap (but not necessary since namespace)
    # logical_source_iri = MAP[f"{tmap_label}LogicalSource"]

    tmap_iri = MAP[f"{tmap_label}"]
    logical_source_iri = LS[f"{tmap_label}"]    #HERE this could be a BNode

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

    namespaces = get_predefined_ns_dict()
    RML = namespaces["rml"]
    QL = namespaces["ql"]

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

    namespaces = get_predefined_ns_dict()
    RML = namespaces["rml"]
    QL = namespaces["ql"]

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

    namespaces = get_predefined_ns_dict()
    RML = namespaces["rml"]
    RR = namespaces["rr"]
    QL = namespaces["ql"]
    MAP = namespaces["map"]
    SUBJ = namespaces["subj"]
    EX = namespaces["ex"]
    CLASS = namespaces["class"]
    RESOURCE = namespaces["resource"]

    tmap_iri = st.session_state["tmap_dict"][tmap_label]
    smap_iri = SUBJ[f"{smap_label}"]


    g.add((tmap_iri, RR.subjectMap, smap_iri))
    g.add((smap_iri, RR.template, Literal(f"http://example.org/resource/{subject_id}")))
    # g.add((smap_iri, RR.template, Literal("http://example.org/{subject_map_node}/{subject_id}")))
    # g.add((smap_iri, RR["class"], CLASS[subject_class]))

#___________________________________________________________________________________

#___________________________________________________________________________________
#Function to build subject dataframe
def build_subject_df():

    subject_rows = []
    for tmap_label in st.session_state["tmap_dict"]:
        subject_info = st.session_state["subject_dict"].get(tmap_label, ["", "", ""])
        subject_rows.append({
            "TriplesMap Label": tmap_label,
            "Data Source": st.session_state["data_source_dict"].get(tmap_label, ""),
            "Subject Rule": subject_info[2],
            "Subject": subject_info[1]
        })

    return pd.DataFrame(subject_rows)

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
        subject_rows.append({
            "TriplesMap Label": tmap_label,
            "Data Source": st.session_state["data_source_dict"].get(tmap_label, ""),
            "Subject Rule": subject_info[2],
            "Subject": subject_info[1],
            "Subject class": subject_class,
            "Subject term type": subject_term_type,
            "Subject graph": subject_graph
        })

    return pd.DataFrame(subject_rows)

#___________________________________________________________________________________

#___________________________________________________________________________________
#Function to check whether an ontology is valid
def is_valid_ontology(url: str):
    try:
        g = Graph()
        g.parse(url, format="xml")

        # Check for presence of OWL or RDFS classes
        classes = list(g.subjects(RDF.type, OWL_NS.Class)) + list(g.subjects(RDF.type, RDFS.Class))
        properties = list(g.subjects(RDF.type, RDF.Property))

        # Consider it valid if it defines at least one class or property
        return bool(classes or properties)

    except:           #if failed to parse ontology
        return False

        #HERE ERROR - I have to load namespaces
#___________________________________________________________________________________


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

#___________________________________________________________________________________

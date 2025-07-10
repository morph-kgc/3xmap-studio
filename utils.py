import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
from collections import Counter
import re
from urllib.parse import urlparse

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
def get_predefined_ns_dict():
    return {
        "rr": Namespace("http://www.w3.org/ns/r2rml#"),
        "rml": Namespace("http://semweb.mmlab.be/ns/rml#"),
        "ql": Namespace("http://semweb.mmlab.be/ns/ql#"),
        "map": Namespace("http://example.org/mapping#"),
        "subj": Namespace("http://example.org/subject#"),
        "ex": Namespace("http://example.org/ns#"),
        "class": Namespace("http://example.org/class#")
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

    parsed = urlparse(iri)
    if not parsed.netloc:
        return False  # e.g. 'http://'

    # Disallow spaces or unescaped characters
    if re.search(r"[ \t\n\r<>\"{}|\\^`]", iri):
        return False

    return True
#__________________________________________________

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
def add_logical_source(g, map_label, source_file, map_dict):

    namespaces = get_predefined_ns_dict()
    RML = namespaces["rml"]
    QL = namespaces["ql"]
    MAP = namespaces["map"]


    new_map = MAP[f"{map_label}TriplesMap"]
    logical_source = MAP[f"{map_label}LogicalSource"]

    g.add((new_map, RML.logicalSource, logical_source))
    g.add((logical_source, RML.source, Literal(source_file)))

    # Pick the reference formulation
    file_extension = source_file.rsplit(".", 1)[-1]
    if file_extension.lower() == "csv":
        g.add((logical_source, QL.referenceFormulation, QL.CSV))
    elif file_extension.lower() == "json":
        g.add((logical_source, QL.referenceFormulation, QL.JSONPath))
    elif file_extension.lower() == "xml":
        g.add((logical_source, QL.referenceFormulation, QL.XPath))
    else:
        raise ValueError(f"Unsupported format: {file_extension}")

    map_dict[map_label] = new_map

    return map_dict

#___________________________________________________________________________________


#___________________________________________________________________________________
#Function to get the data source file of a given map
def get_data_source_file(g, map_node):

    namespaces = get_predefined_ns_dict()
    RML = namespaces["rml"]
    QL = namespaces["ql"]

    logical_source = next(g.objects(map_node, RML.logicalSource), None)

    # Get the associated source file (if found)
    source_file = None
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
def add_subject_map(g, map_label, subject_map_label, subject_class, subject_id):

    namespaces = get_predefined_ns_dict()
    RML = namespaces["rml"]
    RR = namespaces["rr"]
    QL = namespaces["ql"]
    MAP = namespaces["map"]
    SUBJ = namespaces["subj"]
    EX = namespaces["ex"]
    CLASS = namespaces["class"]

    map_node = st.session_state["map_dict"][map_label]
    subject_map_node = SUBJ[f"{subject_map_label}Subject"]

    g.add((map_node, RR.subjectMap, subject_map_node))
    g.add((subject_map_node, RR.template, Literal("http://example.org/{subject_map_node}/{subject_id}")))
    g.add((subject_map_node, RR["class"], CLASS[subject_class]))

#___________________________________________________________________________________









#
#
# # Namespaces
# RR = Namespace("http://www.w3.org/ns/r2rml#")
# RML = Namespace("http://semweb.mmlab.be/ns/rml#")
# QL = Namespace("http://semweb.mmlab.be/ns/ql#")
#
# def add_source_block(graph, triples_map_node, source, format_="CSV", use_sql=False, sql_query=None):
#     """
#     Adds either an RML logical source (e.g., CSV, JSON) or an R2RML logical table (relational).
#
#     Parameters:
#     - graph: your rdflib Graph
#     - triples_map_node: BNode representing the TriplesMap
#     - source: filename (for files) or table name (for SQL)
#     - format_: format of the source (CSV, JSON, XML)
#     - use_sql: True if using relational DB
#     - sql_query: optional raw SQL query (takes precedence over table name)
#     """
#     if use_sql:
#         logical_table = BNode()
#         graph.add((triples_map_node, RR.logicalTable, logical_table))
#
#         if sql_query:
#             graph.add((logical_table, RR.sqlQuery, Literal(sql_query)))
#         else:
#             graph.add((logical_table, RR.tableName, Literal(source)))
#     else:
#         logical_source = BNode()
#         graph.add((triples_map_node, RML.logicalSource, logical_source))
#         graph.add((logical_source, RML.source, Literal(source)))
#
#         fmt = format_.lower()
#         if fmt == "csv":
#             graph.add((logical_source, QL.referenceFormulation, QL.CSV))
#         elif fmt == "json":
#             graph.add((logical_source, QL.referenceFormulation, QL.JSONPath))
#         elif fmt == "xml":
#             graph.add((logical_source, QL.referenceFormulation, QL.XPath))
#         else:
#             raise ValueError(f"Unsupported non-relational format: {format_}")

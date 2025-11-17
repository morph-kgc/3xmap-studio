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
import sqlglot
from streamlit_js_eval import streamlit_js_eval

# Config-----------------------------------
if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
    st.set_page_config(page_title="3Xmap Studio", layout="wide",
        page_icon="logo/fav_icon.png")
else:
    st.set_page_config(page_title="3Xmap Studio", layout="wide",
        page_icon="logo/fav_icon_inverse.png")

# Initialise page---------------------------------------------------------------
utils.init_page()
RML, QL = utils.get_required_ns_dict().values()

#define on_click functions-----------------------------------------------
# TAB1
def save_tm_w_existing_ls():
    # add triples___________________
    NS = st.session_state["base_ns"][1]
    tm_iri = NS[f"{st.session_state['tm_label']}"]  # change so that is can be defined by user
    NS = st.session_state["base_ns"][1]
    ls_iri =  NS[f"{existing_ls}"]   # idem ns
    st.session_state["g_mapping"].add((tm_iri, RML.logicalSource, ls_iri))    #bind to logical source
    st.session_state["g_mapping"].add((tm_iri, RDF.type, RML.TriplesMap))
    # store information________________
    st.session_state["tm_saved_ok_flag"] = True  # for success message
    st.session_state["last_added_tm_list"].insert(0, st.session_state["tm_label"])    # to display last added tm
    # reset fields_____________________
    st.session_state["key_tm_label_input"] = ""

def save_tm_w_tabular_ls():
    # add triples__________________
    NS = st.session_state["base_ns"][1]
    tm_iri = NS[f"{st.session_state['tm_label']}"]
    ds_filename = ds_file.name
    if ls_label:
        NS = st.session_state["base_ns"][1]
        ls_iri = NS[f"{ls_label}"]
    else:
        ls_iri = BNode()
    st.session_state["g_mapping"].add((tm_iri, RML.logicalSource, ls_iri))    #bind to logical source
    st.session_state["g_mapping"].add((ls_iri, RML.source, Literal(ds_filename)))    #bind ls to source file
    file_extension = ds_filename.rsplit(".", 1)[-1]    # bind to reference formulation
    if file_extension.lower() in ["csv", "tsv"]:
        st.session_state["g_mapping"].add((ls_iri, QL.referenceFormulation, QL.CSV))
    elif file_extension.lower() == "xlsx":
        st.session_state["g_mapping"].add((ls_iri, QL.referenceFormulation, QL.Excel))
    elif file_extension.lower() == "parquet":
        st.session_state["g_mapping"].add((ls_iri, QL.referenceFormulation, QL.Parquet))
    elif file_extension.lower() == "orc":
        st.session_state["g_mapping"].add((ls_iri, QL.referenceFormulation, QL.ORC))
    st.session_state["g_mapping"].add((tm_iri, RDF.type, RML.TriplesMap))
    # store information____________________
    st.session_state["tm_saved_ok_flag"] = True  # for success message
    st.session_state["last_added_tm_list"].insert(0, st.session_state["tm_label"])    # to display last added tm
    # reset fields_______________________
    st.session_state["key_tm_label_input"] = ""

def save_tm_w_query():
    [engine, host, port, database, user, password] = st.session_state["db_connections_dict"][db_connection_for_ls]
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
    # add triples__________________
    NS = st.session_state["base_ns"][1]
    tm_iri = NS[f"{st.session_state['tm_label']}"]
    if label_ls_option == "Yes (add label)":
        NS = st.session_state["base_ns"][1]
        ls_iri = NS[f"{ls_label}"]
    else:
        ls_iri = BNode()
    st.session_state["g_mapping"].add((tm_iri, RML.logicalSource, ls_iri))    #bind to logical source
    st.session_state["g_mapping"].add((ls_iri, RML.source, Literal(jdbc_str)))    #bind ls to source file
    st.session_state["g_mapping"].add((ls_iri, RML.referenceFormulation, QL.SQL))
    st.session_state["g_mapping"].add((ls_iri, RML.query, Literal(sql_query)))
    st.session_state["g_mapping"].add((tm_iri, RDF.type, RML.TriplesMap))
    # store information____________________
    st.session_state["tm_saved_ok_flag"] = True  # for success message
    st.session_state["last_added_tm_list"].insert(0, st.session_state["tm_label"])    # to display last added tm
    # reset fields_______________________
    st.session_state["key_tm_label_input"] = ""

def save_tm_w_table_name():
    [engine, host, port, database, user, password] = st.session_state["db_connections_dict"][db_connection_for_ls]
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
    # add triples__________________
    NS = st.session_state["base_ns"][1]
    tm_iri = NS[f"{st.session_state['tm_label']}"]
    if label_ls_option == "Yes (add label)":
        NS = st.session_state["base_ns"][1]
        ls_iri = NS[f"{ls_label}"]
    else:
        ls_iri = BNode()
    st.session_state["g_mapping"].add((tm_iri, RML.logicalSource, ls_iri))    #bind to logical source
    st.session_state["g_mapping"].add((ls_iri, RML.source, Literal(jdbc_str)))    #bind ls to source file
    st.session_state["g_mapping"].add((ls_iri, RML.referenceFormulation, QL.SQL))
    st.session_state["g_mapping"].add((ls_iri, RML.tableName, Literal(selected_table_for_ls)))
    st.session_state["g_mapping"].add((tm_iri, RDF.type, RML.TriplesMap))
    # store information____________________
    st.session_state["tm_saved_ok_flag"] = True  # for success message
    st.session_state["last_added_tm_list"].insert(0, st.session_state["tm_label"])    # to display last added tm
    # reset fields_______________________
    st.session_state["key_tm_label_input"] = ""

# TAB2
def save_sm_existing():
    # add triples____________________
    st.session_state["g_mapping"].add((tm_iri_for_sm, RML.subjectMap, st.session_state["sm_iri"]))
    # store information__________________
    st.session_state["last_added_sm_list"].insert(0, [st.session_state["sm_iri"], tm_label_for_sm])
    st.session_state["sm_saved_ok_flag"] = True

def add_ns_to_sm_template():
    # update template and store information_________
    if not st.session_state["sm_template_prefix"]:    # no ns added yet
        st.session_state["sm_template_list"].insert(0, sm_template_ns)
    elif not st.session_state["sm_template_list"]:
        st.session_state["sm_template_list"] = [sm_template_ns]
    else:   # a ns was added (replace)
        st.session_state["sm_template_list"][0] = sm_template_ns
    # reset fields_____________
    st.session_state["sm_template_prefix"] = sm_template_ns_prefix if sm_template_ns_prefix else utils.get_g_ns_dict(st.session_state["g_mapping"])[sm_template_ns_prefix]
    st.session_state["key_sm_template_ns_prefix"] = "Select a namespace"
    st.session_state["key_build_template_action_sm"] = "🔒 Fixed part"

def save_sm_template_fixed_part():
    # update template_____________
    st.session_state["sm_template_list"].append(sm_template_fixed_part)
    # reset fields_____________
    st.session_state["key_build_template_action_sm"] = "📈 Variable part"

def save_sm_template_variable_part():
    # update template_____________
    st.session_state["sm_template_list"].append("{" + sm_template_variable_part + "}")
    # store information
    st.session_state["sm_template_variable_part_flag"] = True
    # reset fields_____________
    st.session_state["key_build_template_action_sm"] = "🔒 Fixed part"

def reset_sm_template():
    # reset template___________________-
    st.session_state["sm_template_list"] = []
    # store information____________________
    st.session_state["sm_template_prefix"] = ""
    st.session_state["template_sm_is_iri_flag"] = False
    st.session_state["sm_template_variable_part_flag"] = False
    # reset fields_____________
    st.session_state["key_build_template_action_sm"] = "🔒 Fixed part"

def add_subject_class():
    # add subject class____________________
    st.session_state["multiple_subject_class_list"].append(subject_class_iri)
    # reset fields___________________
    st.session_state["key_add_subject_class_option"] = "🔢 Multiple Classes"
    st.session_state["key_add_multiple_subject_class_option"] = "✔️ Ready"

def key_remove_multiple_subject_classes():
    # remove subject classes____________________
    if "Select all" in subject_class_to_remove_list:
        st.session_state["multiple_subject_class_list"] = []
    else:
        for class_iri in st.session_state["multiple_subject_class_list"]:
            if split_uri(class_iri)[1] in subject_class_to_remove_list:
                st.session_state["multiple_subject_class_list"].remove(class_iri)
    # reset fields___________________
    st.session_state["key_add_subject_class_option"] = "🔢 Multiple Classes"
    st.session_state["key_add_multiple_subject_class_option"] = "✔️ Ready" if st.session_state["multiple_subject_class_list"] else "🧩 Add Ontology Class"

def save_sm_template():   #function to save subject map (template option)
    # add triples____________________
    if not sm_label:
        sm_iri = BNode()
        st.session_state["sm_label"] = "_:" + str(sm_iri)[:7] + "..."   # to be displayed
    else:
        NS = st.session_state["base_ns"][1]
        sm_iri = NS[sm_label]
    st.session_state["g_mapping"].add((tm_iri_for_sm, RML.subjectMap, sm_iri))
    st.session_state["g_mapping"].add((sm_iri, RDF.type, RML.SubjectMap))
    st.session_state["g_mapping"].add((sm_iri, RML.template, Literal(sm_template)))
    if add_subject_class_option != "No Class":
        for subject_class_iri in st.session_state["multiple_subject_class_list"]:
            st.session_state["g_mapping"].add((sm_iri, RML["class"], subject_class_iri))
    if add_sm_graph_map_option == "Add Graph Map" and subject_graph:
        st.session_state["g_mapping"].add((sm_iri, RML["graph"], subject_graph))
    if sm_term_type == "🌐 IRI":
        st.session_state["g_mapping"].add((sm_iri, RML.termType, RML.IRI))
    elif sm_term_type == "👻 BNode":
        st.session_state["g_mapping"].add((sm_iri, RML.termType, RML.BlankNode))
    # store information__________________
    st.session_state["last_added_sm_list"].insert(0, [sm_iri, tm_label_for_sm])
    st.session_state["sm_saved_ok_flag"] = True
    # reset fields____________________
    st.session_state["multiple_subject_class_list"] = []
    st.session_state["sm_template_list"] = []
    st.session_state["sm_template_prefix"] = ""
    st.session_state["key_tm_label_input_for_sm"] = "Select a TriplesMap"

def save_sm_constant():   #function to save subject map (constant option)
    # add triples________________________
    if not sm_label:
        sm_iri = BNode()
        st.session_state["sm_label"] = utils.get_node_label(sm_iri)   # to be displayed
    else:
        NS = st.session_state["base_ns"][1]
        sm_iri = NS[sm_label]
    st.session_state["g_mapping"].add((tm_iri_for_sm, RML.subjectMap, sm_iri))
    st.session_state["g_mapping"].add((sm_iri, RDF.type, RML.SubjectMap))
    if sm_constant_ns_prefix != "Select a namespace":
        sm_constant_ns = mapping_ns_dict[sm_constant_ns_prefix]
        NS = Namespace(sm_constant_ns)
        sm_constant_iri = NS[sm_constant]
    else:
        sm_constant_iri = URIRef(sm_constant)
    st.session_state["g_mapping"].add((sm_iri, RML.constant, sm_constant_iri))
    if add_subject_class_option != "No Class":
        for subject_class_iri in st.session_state["multiple_subject_class_list"]:
            st.session_state["g_mapping"].add((sm_iri, RML["class"], subject_class_iri))
    if add_sm_graph_map_option == "Add Graph Map" and subject_graph:
        st.session_state["g_mapping"].add((sm_iri, RML["graph"], subject_graph))
    st.session_state["g_mapping"].add((sm_iri, RML.termType, RML.IRI))
    # store information____________________
    st.session_state["last_added_sm_list"].insert(0, [sm_iri, tm_label_for_sm])
    st.session_state["sm_saved_ok_flag"] = True
    # reset fields_________________________
    st.session_state["multiple_subject_class_list"] = []
    st.session_state["sm_template_list"] = []   # in case it is not empty
    st.session_state["key_tm_label_input_for_sm"] = "Select a TriplesMap"

def save_sm_reference():   #function to save subject map (reference option)
    # add triples____________________
    if not sm_label:
        sm_iri = BNode()
        st.session_state["sm_label"] = "_:" + str(sm_iri)[:7] + "..."   # to be displayed
    else:
        NS = st.session_state["base_ns"][1]
        sm_iri = NS[sm_label]
    st.session_state["g_mapping"].add((tm_iri_for_sm, RML.subjectMap, sm_iri))
    st.session_state["g_mapping"].add((sm_iri, RDF.type, RML.SubjectMap))
    st.session_state["g_mapping"].add((sm_iri, RML.reference, Literal(sm_column_name)))    #HERE change to RML.column in R2RML
    if add_subject_class_option != "No Class":
        for subject_class_iri in st.session_state["multiple_subject_class_list"]:
            st.session_state["g_mapping"].add((sm_iri, RML["class"], subject_class_iri))
    if add_sm_graph_map_option == "Add Graph Map" and subject_graph:
        st.session_state["g_mapping"].add((sm_iri, RML["graph"], subject_graph))
    if sm_term_type == "🌐 IRI":
        st.session_state["g_mapping"].add((sm_iri, RML.termType, RML.IRI))
    elif sm_term_type == "👻 BNode":
        st.session_state["g_mapping"].add((sm_iri, RML.termType, RML.BlankNode))
    # store information__________________
    st.session_state["last_added_sm_list"].insert(0, [sm_iri, tm_label_for_sm])
    st.session_state["sm_saved_ok_flag"] = True
    # reset fields____________________
    st.session_state["multiple_subject_class_list"] = []
    st.session_state["sm_template_list"] = []   # in case it is not empty
    st.session_state["key_tm_label_input_for_sm"] = "Select a TriplesMap"

# TAB3
def add_ns_to_om_template():
    # update template and store information_________
    if not st.session_state["template_om_is_iri_flag"]:    # no ns added yet
        st.session_state["om_template_list"].insert(0, om_template_ns)
    else:   # a ns was added (replace)
        st.session_state["om_template_list"][0] = om_template_ns
    # reset fields_____________
    st.session_state["om_template_ns_prefix"] = om_template_ns_prefix
    st.session_state["template_om_is_iri_flag"] = True
    st.session_state["key_om_template_ns_prefix"] = "Select a namespace"
    st.session_state["key_build_template_action_om"] = "🔒 Fixed part"

def save_om_template_fixed_part():
    # update template_____________
    st.session_state["om_template_list"].append(om_template_fixed_part)
    # reset fields_____________
    st.session_state["key_build_template_action_om"] = "📈 Variable part"

def save_om_template_variable_part():
    # update template_____________
    st.session_state["om_template_list"].append("{" + om_template_variable_part + "}")
    # store information
    st.session_state["om_template_variable_part_flag"] = True
    # reset fields_____________
    st.session_state["key_build_template_action_om"] = "🔒 Fixed part"

def reset_om_template():
    # reset template
    st.session_state["om_template_list"] = []
    # store information____________________
    st.session_state["om_template_ns_prefix"] = ""
    st.session_state["template_om_is_iri_flag"] = False
    st.session_state["om_template_variable_part_flag"] = False
    # reset fields_____________
    st.session_state["key_build_template_action_om"] = "🔒 Fixed part"

def save_pom_template():
    # add triples pom________________________
    st.session_state["g_mapping"].add((st.session_state["tm_iri_for_pom"], RML.predicateObjectMap, st.session_state["pom_iri_to_create"]))
    st.session_state["g_mapping"].add((st.session_state["pom_iri_to_create"], RML.predicate, selected_p_iri))
    st.session_state["g_mapping"].add((st.session_state["pom_iri_to_create"], RML.objectMap, om_iri))
    st.session_state["g_mapping"].add((st.session_state["pom_iri_to_create"], RDF.type, RML.PredicateObjectMap))
    # add triples om________________________
    st.session_state["g_mapping"].add((om_iri, RDF.type, RML.ObjectMap))
    st.session_state["g_mapping"].add((om_iri, RML.template, Literal(om_template)))
    if om_term_type == "📘 Literal":
        st.session_state["g_mapping"].add((om_iri, RML.termType, RML.Literal))
        if om_datatype != "Select datatype" and om_datatype != "Natural language tag":
            datatype_dict = utils.get_datatypes_dict()
            st.session_state["g_mapping"].add((om_iri, RML.datatype, datatype_dict[om_datatype]))
        elif om_datatype == "Natural language tag":
            st.session_state["g_mapping"].add((om_iri, RML.language, Literal(om_language_tag)))
    elif om_term_type == "🌐 IRI":
        st.session_state["g_mapping"].add((om_iri, RML.termType, RML.IRI))
    elif om_term_type == "👻 BNode":
        st.session_state["g_mapping"].add((om_iri, RML.termType, RML.BlankNode))
    if add_om_graph_map_option == "Add Graph Map":
        st.session_state["g_mapping"].add((om_iri, RML.graphMap, om_graph))
    # store information________________________
    st.session_state["pom_saved_ok_flag"] = True
    st.session_state["last_added_pom_list"].insert(0, [st.session_state["pom_iri_to_create"], st.session_state["tm_iri_for_pom"]])
    # reset fields_____________________________
    st.session_state["template_om_is_iri_flag"] = False
    st.session_state["key_selected_p_label"] = "Select a predicate"
    st.session_state["key_manual_p_ns_prefix"] = "Select a namespace"
    st.session_state["key_manual_p_label"] = ""
    st.session_state["key_pom_label"] = ""
    st.session_state["key_build_template_action_om"] = "🏷️ Add Namespace"
    st.session_state["key_om_template_ns_prefix"] = "Select a namespace"
    st.session_state["om_template_list"] = []    # reset template
    st.session_state["om_term_type"] = "🌐 IRI"
    st.session_state["key_om_label"] = ""

def save_pom_constant():
    # add triples pom________________________
    st.session_state["g_mapping"].add((st.session_state["tm_iri_for_pom"], RML.predicateObjectMap, st.session_state["pom_iri_to_create"]))
    st.session_state["g_mapping"].add((st.session_state["pom_iri_to_create"], RML.predicate, selected_p_iri))
    st.session_state["g_mapping"].add((st.session_state["pom_iri_to_create"], RML.objectMap, om_iri))
    st.session_state["g_mapping"].add((st.session_state["pom_iri_to_create"], RDF.type, RML.PredicateObjectMap))
    # add triples om________________________
    st.session_state["g_mapping"].add((om_iri, RDF.type, RML.ObjectMap))
    if om_term_type == "🌐 IRI":
        om_constant_ns = mapping_ns_dict[om_constant_ns_prefix]
        NS = Namespace(om_constant_ns)
        om_constant_iri = NS[om_constant]
        st.session_state["g_mapping"].add((om_iri, RML.constant, om_constant_iri))
        st.session_state["g_mapping"].add((om_iri, RML.termType, RML.IRI))
    elif om_term_type == "📘 Literal":
        st.session_state["g_mapping"].add((om_iri, RML.constant, Literal(om_constant)))
        st.session_state["g_mapping"].add((om_iri, RML.termType, RML.Literal))
        if om_datatype != "Select datatype" and om_datatype != "Natural language tag":
            datatype_dict = utils.get_datatypes_dict()
            st.session_state["g_mapping"].add((om_iri, RML.datatype, datatype_dict[om_datatype]))
        elif om_datatype == "Natural language tag":
            st.session_state["g_mapping"].add((om_iri, RML.language, Literal(om_language_tag)))
    if add_om_graph_map_option == "Add Graph Map":
        st.session_state["g_mapping"].add((om_iri, RML.graphMap, om_graph))
    # store information________________________
    st.session_state["pom_saved_ok_flag"] = True
    st.session_state["last_added_pom_list"].insert(0, [st.session_state["pom_iri_to_create"], st.session_state["tm_iri_for_pom"]])
    # reset fields_____________________________
    st.session_state["key_selected_p_label"] = "Select a predicate"
    st.session_state["key_manual_p_ns_prefix"] = "Select a namespace"
    st.session_state["key_manual_p_label"] = ""
    st.session_state["key_pom_label"] = ""
    st.session_state["key_om_constant"] = ""
    st.session_state["om_term_type"] = "📘 Literal"
    st.session_state["key_om_label"] = ""
    st.session_state["key_om_datatype"] = "Select datatype"

def save_pom_reference():
    # add triples pom________________________
    st.session_state["g_mapping"].add((st.session_state["tm_iri_for_pom"], RML.predicateObjectMap, st.session_state["pom_iri_to_create"]))
    st.session_state["g_mapping"].add((st.session_state["pom_iri_to_create"], RML.predicate, selected_p_iri))
    st.session_state["g_mapping"].add((st.session_state["pom_iri_to_create"], RML.objectMap, om_iri))
    st.session_state["g_mapping"].add((st.session_state["pom_iri_to_create"], RDF.type, RML.PredicateObjectMap))
    # add triples om________________________
    st.session_state["g_mapping"].add((om_iri, RDF.type, RML.ObjectMap))
    st.session_state["g_mapping"].add((om_iri, RML.reference, Literal(om_column_name)))    #HERE change to RML.column in R2RML
    if om_term_type == "📘 Literal":
        st.session_state["g_mapping"].add((om_iri, RML.termType, RML.Literal))
        if om_datatype != "Select datatype" and om_datatype != "Natural language tag":
            datatype_dict = utils.get_datatypes_dict()
            st.session_state["g_mapping"].add((om_iri, RML.datatype, datatype_dict[om_datatype]))
        elif om_datatype == "Natural language tag":
            st.session_state["g_mapping"].add((om_iri, RML.language, Literal(om_language_tag)))
    elif om_term_type == "🌐 IRI":
        st.session_state["g_mapping"].add((om_iri, RML.termType, RML.IRI))
    elif om_term_type == "👻 BNode":
        st.session_state["g_mapping"].add((om_iri, RML.termType, RML.BlankNode))
    if add_om_graph_map_option == "Add Graph Map":
        st.session_state["g_mapping"].add((om_iri, RML.graphMap, om_graph))
    # store information________________________
    st.session_state["pom_saved_ok_flag"] = True
    st.session_state["last_added_pom_list"].insert(0, [st.session_state["pom_iri_to_create"], st.session_state["tm_iri_for_pom"]])
    # reset fields_____________________________
    st.session_state["key_selected_p_label"] = "Select a predicate"
    st.session_state["key_manual_p_ns_prefix"] = "Select a namespace"
    st.session_state["key_manual_p_label"] = ""
    st.session_state["key_pom_label"] = ""
    st.session_state["key_om_column_name"] = "Select reference"
    st.session_state["om_term_type"] = "📘 Literal"
    st.session_state["key_om_label"] = ""
    st.session_state["key_om_datatype"] = "Select datatype"


# TAB4
def delete_tm():   #function to delete a TriplesMap
    # remove triples and store information___________
    for tm in tm_to_remove_list:
        utils.remove_triplesmap(tm)      # remove the tm
        if tm in st.session_state["last_added_tm_list"]:
            st.session_state["last_added_tm_list"].remove(tm)       # if it is in last added list, remove
    #store information
    st.session_state["last_added_sm_list"] = [pair for pair in st.session_state["last_added_sm_list"]
        if pair[1] in utils.get_tm_dict()]
    st.session_state["last_added_pom_list"] = [pair for pair in st.session_state["last_added_pom_list"]
        if pair[1] in utils.get_tm_dict()]
    st.session_state["tm_deleted_ok_flag"] = True
    #reset fields_________________________
    st.session_state["key_tm_to_remove_list"] = []

def delete_all_tm():   #function to delete a TriplesMap
    # remove all triples
    st.session_state["g_mapping"] = Graph()
    #store information
    st.session_state["last_added_tm_list"] = []
    st.session_state["last_added_sm_list"] = []
    st.session_state["last_added_pom_list"] = []
    st.session_state["tm_deleted_ok_flag"] = True
    #reset fields_______________________
    st.session_state["key_tm_to_remove_list"] = []

def unassign_sm():
    # remove triples______________________
    for tm in tm_to_unassign_sm_list:
        tm_iri = tm_dict[tm]
        sm_iri = st.session_state["g_mapping"].value(subject=tm_iri, predicate=RML.subjectMap)
        other_tm_with_sm = [split_uri(s)[1] for s, p, o in st.session_state["g_mapping"].triples((None, RML.subjectMap, sm_iri)) if s != tm_iri]
        if len(other_tm_with_sm) != 0:       # just unassign sm from tm (don't remove)
            st.session_state["g_mapping"].remove((tm_iri, RML.subjectMap, None))
        else:       # completely remove sm
            st.session_state["g_mapping"].remove((sm_iri, None, None))
            st.session_state["g_mapping"].remove((None, None, sm_iri))
    # store information__________________
    st.session_state["sm_unassigned_ok_flag"] = True
    st.session_state["last_added_sm_list"] = [pair for pair in st.session_state["last_added_sm_list"]
        if pair[1] not in tm_to_unassign_sm_list]
    # reset fields__________________
    st.session_state["key_map_type_to_remove"] = "🗺️ TriplesMap"

def delete_pom():           #function to delete a Predicate-Object Map
    for pom_iri in pom_to_delete_iri_list:
        om_to_delete = st.session_state["g_mapping"].value(subject=pom_iri, predicate=RML.objectMap)
        # remove triples______________________
        st.session_state["g_mapping"].remove((pom_iri, None, None))
        st.session_state["g_mapping"].remove((None, None, pom_iri))
        st.session_state["g_mapping"].remove((om_to_delete, None, None))
    # store information__________________
    st.session_state["pom_deleted_ok_flag"] = True
    st.session_state["last_added_pom_list"] = [pair for pair in st.session_state["last_added_pom_list"]
        if pair[0] not in pom_to_delete_iri_list]
    # reset fields
    st.session_state["key_map_type_to_remove"] = "🗺️ TriplesMap"

def clean_g_mapping():
    # REMOVE TRIPLESMAPS
    # remove triples and store information___________
    for tm in tm_to_clean_list:
        utils.remove_triplesmap(tm)      # remove the tm
        if tm in st.session_state["last_added_tm_list"]:
            st.session_state["last_added_tm_list"].remove(tm)       # if it is in last added list, remove
    #store information________________________________
    st.session_state["last_added_sm_list"] = [pair for pair in st.session_state["last_added_sm_list"]
        if pair[1] in utils.get_tm_dict()]
    st.session_state["last_added_pom_list"] = [pair for pair in st.session_state["last_added_pom_list"]
        if pair[1] in utils.get_tm_dict()]

    # REMOVE PREDICATE-OBJECT MAPS
    for pom_iri in pom_to_clean_list:
        om_to_delete = st.session_state["g_mapping"].value(subject=pom_iri, predicate=RML.objectMap)
        # remove triples______________________
        st.session_state["g_mapping"].remove((pom_iri, None, None))
        st.session_state["g_mapping"].remove((None, None, pom_iri))
        st.session_state["g_mapping"].remove((om_to_delete, None, None))
    # store information__________________
    st.session_state["last_added_pom_list"] = [pair for pair in st.session_state["last_added_pom_list"]
        if pair[0] not in pom_to_delete_iri_list]

    #GENERAL
    #store information________________________________
    st.session_state["g_mapping_cleaned_ok_flag"] = True

# START PAGE_____________________________________________________________________


#____________________________________________________________
# PANELS OF THE PAGE (tabs)

tab1, tab2, tab3, tab4 = st.tabs(["Add TriplesMap", "Add Subject Map", "Add Predicate-Object Map", "Manage Mapping"])

# ERROR MESSAGE IF NO MAPPING LOADED
col1, col2 = st.columns([2,1])
if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
    with col1:
        utils.get_missing_g_mapping_error_message_different_page()
        st.stop()

#________________________________________________
#ADD TRIPLESMAP
with tab1:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])

    # Display last added namespaces in dataframe (also option to show all ns)
    tm_dict = utils.get_tm_dict()

    with col2:
        col2a, col2b = st.columns([0.5, 2])

    with col2b:
        st.write("")
        st.write("")
        rows = [{"TriplesMap": tm, "Data Source label": utils.get_ls(tm),
                "Data Source": utils.get_ds(tm)} for tm in st.session_state["last_added_tm_list"]]
        last_added_tm_df = pd.DataFrame(rows)
        last_last_added_tm_df = last_added_tm_df.head(utils.get_max_length_for_display()[1])

        max_length = utils.get_max_length_for_display()[0]   # max number of tm shown in dataframe
        if st.session_state["last_added_tm_list"]:
            st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                    🔎 last added TriplesMaps
                </div>""", unsafe_allow_html=True)
            if len(tm_dict) < max_length:
                st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        (complete list below)
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        (longer list below)
                    </div>""", unsafe_allow_html=True)
            st.dataframe(last_last_added_tm_df, hide_index=True)
            st.write("")


        #Option to show all TriplesMaps
        rows = [{"TriplesMap": tm, "LogicalSource": utils.get_ls(tm),
                "DataSource": utils.get_ds(tm)} for tm in reversed(list(tm_dict.keys()))]
        tm_df = pd.DataFrame(rows)
        tm_df_short = tm_df.head(max_length)

        if tm_dict and len(tm_dict) < max_length:
            with st.expander("🔎 Show all TriplesMaps"):
                st.write("")
                st.dataframe(tm_df, hide_index=True)
        elif tm_dict:
            with st.expander("🔎 Show more TriplesMaps"):
                st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        Go to the <b> Display Mapping</b> page for more information.
                    </div>""", unsafe_allow_html=True)
                st.write("")
                st.dataframe(tm_df_short, hide_index=True)


    #PURPLE HEADING - ADD NEW TRIPLESMAP
    with col1:
        st.markdown("""<div class="purple-heading">
                🧱 Add New TriplesMap
            </div>""", unsafe_allow_html=True)
        st.write("")

    if st.session_state["tm_saved_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The TriplesMap <b style="color:#F63366;">{st.session_state["tm_label"]}</b> has been added!
            </div>""", unsafe_allow_html=True)
        st.session_state["tm_saved_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    with col1:
        col1a, col1b = st.columns([1.5,1])
    with col1a:
        tm_label = st.text_input("⌨️ Enter label for the new TriplesMap:*", key="key_tm_label_input")    #user-friendly name for the TriplesMap
        st.session_state["tm_label"] = tm_label
        valid_tm_label = utils.is_valid_label_hard(st.session_state["tm_label"])

    tm_dict = utils.get_tm_dict()
    labelled_ls_list = []      #existing labelled logical sources
    for s, p, o in st.session_state["g_mapping"].triples((None, RML.logicalSource, None)):
        if isinstance(o, URIRef) and split_uri(o)[1] not in labelled_ls_list:
            labelled_ls_list.append(split_uri(o)[1])


    if valid_tm_label:   #after a valid label has been given
        if tm_label in tm_dict:   #if label is already in use
            with col1a:
                st.markdown(f"""<div class="error-message">
                    ❌ TriplesMap label <b style="color:#a94442;">{tm_label}</b> already in use.
                    Please pick a different label.
                </div>""", unsafe_allow_html=True)
                st.write("")

        else:    #if label is valid

            ls_options_list = []
            if st.session_state["db_connections_dict"]:
                ls_options_list.append("📊 SQL Database")
            if st.session_state["ds_files_dict"]:
                ls_options_list.append("🛢️ Tabular data")
            if labelled_ls_list:
                ls_options_list.append("📑 Existing Logical Source")
            if not st.session_state["db_connections_dict"] and not st.session_state["ds_files_dict"]:
                with col1a:
                    st.markdown(f"""<div class="error-message">
                        ❌ No data sources are available. <small>You can add them in the
                        <b>Manage Logical Sources</b> page.</small>
                    </div>""", unsafe_allow_html=True)
                    st.write("")

            if ls_options_list:
                with col1b:
                    ls_option = st.radio("🖱️ Logical Source option:*", ls_options_list, horizontal=True,
                        key="key_ls_option")
            else:
                ls_option = None

            if ls_option == "📑 Existing Logical Source":
                with col1:
                    col1a, col1b = st.columns([2,1])

                with col1a:
                    list_to_choose = list(reversed(labelled_ls_list))
                    list_to_choose.insert(0, "Select a Logical Source")
                    existing_ls = st.selectbox("🖱️ Select an existing Logical Source:*", list_to_choose)

                if existing_ls != "Select a Logical Source":
                    with col1a:
                        save_tm_button_existing_ls = st.button("Save", key="key_save_tm_w_existing_ls", on_click=save_tm_w_existing_ls)


            if ls_option == "📊 SQL Database":

                with col1:
                    col1a, col1b = st.columns([2,1])

                with col1a:
                    list_to_choose = list(reversed(st.session_state["db_connections_dict"].keys()))
                    list_to_choose.insert(0, "Select a connection")
                    db_connection_for_ls = st.selectbox("🖱️ Select connection to Database:*", list_to_choose,
                        key="key_db_connection_for_ls")

                with col1b:
                    label_ls_option = st.selectbox("♻️ Reuse Logical Source:",
                        ["No", "Yes (add label)"], key="key_label_ls_option")
                    valid_ls_label = True

                    if label_ls_option == "Yes (add label)":
                        with col1a:
                            ls_label = st.text_input("⌨️ Enter label for the Logical Source:*")
                        with col1b:
                            st.write("")
                            valid_ls_label = utils.is_valid_label_hard(ls_label)
                            if valid_ls_label and ls_label in labelled_ls_list:
                                st.markdown(f"""<div class="error-message">
                                        ❌ The logical source label <b>{ls_label}</b>
                                        is already in use. <small>Please, pick a different label.</small>
                                    </div>""", unsafe_allow_html=True)
                                valid_ls_label = False

                with col1a:
                    if db_connection_for_ls != "Select a connection":
                        connection_ok_flag = True
                        try:
                            conn = utils.make_connection_to_db(db_connection_for_ls)

                        except Exception as e:
                            conn = ""
                            st.markdown(f"""<div class="error-message">
                                ❌ The connection <b>{db_connection_for_ls}</b> is not working. <small>Please go to the <b>
                                Manage Logical Sources</b> page to manage the connections to Databases.</small>
                            </div>""", unsafe_allow_html=True)
                            connection_ok_flag = False

                        if connection_ok_flag:

                            query_for_selected_db_list = []   # list of queries of the selected connection
                            for query_label, [connection_label, query] in st.session_state["sql_queries_dict"].items():
                                if connection_label == db_connection_for_ls:
                                    query_for_selected_db_list.insert(0, query_label)   # only include queries of the selected connection

                            with col1:
                                col1a, col1b = st.columns(2)
                            with col1b:
                                list_to_choose = ["🖼️ View", "📅 Table"] if query_for_selected_db_list else ["📅 Table"]
                                query_option = st.radio("🖱️ Select option:*", list_to_choose,
                                    horizontal=True, key="key_query_option_radio")

                            if query_option == "🖼️ View" and db_connection_for_ls != "Select a connection" and conn:

                                with col1a:
                                    list_to_choose = query_for_selected_db_list
                                    list_to_choose.insert(0, "Select view")
                                    selected_query_for_ls = st.selectbox("🖱️ Select view:*", list_to_choose,
                                        key="key_selected_query_for_ls")

                                if selected_query_for_ls != "Select view":
                                    sql_query = st.session_state["sql_queries_dict"][selected_query_for_ls][1]
                                    try:
                                        cur = conn.cursor()
                                        cur.execute(sql_query)
                                        sql_query_ok_flag = True
                                    except:
                                        with col1a:
                                            st.markdown(f"""<div class="error-message">
                                                ❌ <b>Invalid SQL syntax</b>. Please check your view.<br>
                                            </div>""", unsafe_allow_html=True)
                                            st.write("")
                                        sql_query_ok_flag = False

                                    if sql_query_ok_flag:

                                        with col1a:
                                            st.button("Save", key="key_save_tm_w_saved_query", on_click=save_tm_w_query)

                                        with col1:
                                            utils.display_db_view_results(selected_query_for_ls)


                            if query_option == "📅 Table" and db_connection_for_ls != "Select a connection" and conn:

                                cur = conn.cursor()   # create a cursor
                                engine = st.session_state["db_connections_dict"][db_connection_for_ls][0]
                                database = st.session_state["db_connections_dict"][db_connection_for_ls][3]
                                utils.get_tables_from_db(engine, cur, database)
                                db_tables = [row[0] for row in cur.fetchall()]

                                with col1a:
                                    list_to_choose = db_tables
                                    list_to_choose.insert(0, "Select a table")
                                    selected_table_for_ls = st.selectbox("🖱️ Select a table:*", list_to_choose,
                                        key="key_selected_table_for_ls")


                                if selected_table_for_ls != "Select a table":
                                    if (label_ls_option == "Yes (add label)" and valid_ls_label) or label_ls_option == "No":
                                        with col1a:
                                            st.button("Save", key="key_save_tm_w_table_name", on_click=save_tm_w_table_name)

                                    cur.execute(f"SELECT * FROM {selected_table_for_ls}")
                                    rows = cur.fetchall()
                                    if engine == "SQL Server":
                                        rows = [tuple(row) for row in rows]   # rows are of type <class 'pyodbc.Row'> -> convert to tuple
                                    columns = [desc[0] for desc in cur.description]

                                    df = pd.DataFrame(rows, columns=columns)

                                    table_len = f"{len(df)} rows" if len(df) != 1 else f"{len(df)} row"
                                    inner_html = f"""📅 <b style="color:#F63366;"> Table ({table_len}):</b>
                                            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"""


                                    with col1:
                                        max_rows = utils.get_max_length_for_display()[2]
                                        max_cols = utils.get_max_length_for_display()[3]
                                        limited_df = df.iloc[:, :max_cols]   # limit number of columns

                                        # Slice rows if needed
                                        if len(df) > max_rows and df.shape[1] > max_cols:
                                            inner_html += f"""<small>Showing the <b>first {max_rows} rows</b> (out of {len(df)})
                                                and the <b>first {max_cols} columns</b> (out of {df.shape[1]}).</small>"""
                                        elif len(df) > max_rows:
                                            inner_html += f"""<small>Showing the <b>first {max_rows} rows</b> (out of {len(df)}).</small>"""
                                        elif df.shape[1] > max_cols:
                                            inner_html += f"""<small>Showing the <b>first {max_cols} columns</b> (out of {df.shape[1]}).</small>"""

                                        st.markdown(f"""<div class="info-message-blue">
                                                {inner_html}
                                            </div>""", unsafe_allow_html=True)
                                        st.dataframe(limited_df.head(max_rows), hide_index=True)

                                    cur.close()
                                    conn.close()



            if ls_option == "🛢️ Tabular data":

                with col1:
                    col1a, col1b = st.columns([2,1])

                with col1a:
                    list_to_choose = list(reversed(st.session_state["ds_files_dict"].keys()))
                    list_to_choose.insert(0, "Select file")
                    ds_filename_for_tm = st.selectbox("🖱️ Select the Logical Source file:*", list_to_choose,
                    key="key_ds_filename_for_tm")

                if ds_filename_for_tm != "Select file":
                    ds_file = st.session_state["ds_files_dict"][ds_filename_for_tm]

                with col1b:
                    label_ls_option = st.selectbox("♻️ Reuse Logical Source:",
                        ["No", "Yes (add label)"], key="key_label_ls_option")

                    if label_ls_option == "Yes (add label)":
                        with col1a:
                            ls_label = st.text_input("⌨️ Enter label for the Logical Source:*")
                            if ls_label in labelled_ls_list:
                                with col1b:
                                    st.markdown(f"""<div class="error-message">
                                            ❌ The logical source label <b>{ls_label}</b>
                                            is already in use. <small>Please, pick a different label.</small>
                                        </div>""", unsafe_allow_html=True)
                                    st.write("")
                    else:
                        ls_label = ""

                    with col1a:
                        if label_ls_option == "Yes (add label)":
                            if ls_label and ls_label not in labelled_ls_list:
                                if ds_filename_for_tm != "Select file":
                                    st.button("Save", key="key_save_tm_w_tabular_ls", on_click=save_tm_w_tabular_ls)
                        else:
                            if ds_filename_for_tm != "Select file":
                                st.button("Save", key="key_save_tm_w_tabular_ls", on_click=save_tm_w_tabular_ls)


    # remove tm success message - show here if "Remove" purple heading is not going to be shown
    if not utils.get_tm_dict() and st.session_state["tm_deleted_ok_flag"]:  # show message here if "Remove" purple heading is going to be shown
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:1em;
            border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                ✅ The <b>Triplesmap/s</b> have been removed.
            </div>""", unsafe_allow_html=True)
            st.write("")
        st.session_state["tm_deleted_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

#________________________________________________



#________________________________________________
#ADD SUBJECT MAP TO MAP
with tab2:

    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])

    # Display last added namespaces in dataframe (also option to show all ns)
    tm_dict = utils.get_tm_dict()
    sm_dict = utils.get_sm_dict()

    with col2:
        col2a, col2b = st.columns([0.5, 2])

#____________________________________

    #PURPLE HEADING - ADD NEW SUBJECT MAP
    with col1:
        st.markdown("""<div class="purple-heading">
                🧱 Add New Subject Map
            </div>""", unsafe_allow_html=True)

    if st.session_state["sm_saved_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>Subject Map</b> has been created!
            </div>""", unsafe_allow_html=True)
        st.session_state["sm_saved_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()


    with col1:
        col1a, col1b = st.columns([2,1.2])

    tm_dict = utils.get_tm_dict()

    #SELECT THE TRIPLESMAP TO WHICH THE SUBJECT MAP WILL BE ADDED___________________________
    #only triplesmaps without subject map can be selected

    tm_wo_sm_list = []          #list of all TriplesMap which do not have a subject yet
    for tm_label, tm_iri in tm_dict.items():
        if not next(st.session_state["g_mapping"].objects(tm_iri, RML.subjectMap), None):   #if there is no subject for that TriplesMap
            tm_wo_sm_list.append(tm_label)


    if not tm_dict:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.markdown(f"""<div class="error-message">
                    ❌ No TriplesMaps in mapping <b>{st.session_state["g_label"]}</b>.
                    <small>You can add new TriplesMaps in the <b>Add TriplesMap</b> panel.</small>
                </div>""", unsafe_allow_html=True)

    elif not tm_wo_sm_list:
        with col1:
            col1a, col2a = st.columns([2,0.5])
        with col1a:
            st.markdown(f"""<div class="info-message-gray">
                🔒 <b>All existing TriplesMaps have already been assigned a Subject Map.</b><br>
                <ul style="margin-top:0.5em; margin-bottom:0; font-size:0.9em; list-style-type: disc; padding-left: 1.2em;">
                    <li>You can add new TriplesMaps in the <b>Add TriplesMap</b> panel.</li>
                    <li>You can remove the Subject Map of a TriplesMap in the <b>Manage Mapping</b> pannel.</li>
                </ul></div>""",unsafe_allow_html=True)
            st.write("")


    else:
        #IF THERE ARE TRIPLESMAPS AVAILABLE___________________________

        #first create dictionary of all the existing Subject Maps

        ns_needed_for_sm_flag = False

        existing_sm_dict = {}
        for sm in st.session_state["g_mapping"].objects(predicate=RML.subjectMap):
            if isinstance(sm, URIRef):
                existing_sm_dict[utils.format_iri_to_prefix_label(sm)] = sm
            # else:
            #     existing_sm_dict[sm] = sm
        existing_sm_list = list(existing_sm_dict.keys())

        with col1:
            col1a, col1b = st.columns(2)
        if st.session_state["last_added_tm_list"] and st.session_state["last_added_tm_list"][0] in tm_wo_sm_list:
            with col1a:
                list_to_choose = list(reversed(tm_wo_sm_list))
                list_to_choose.insert(0, "Select a TriplesMap")
                tm_label_for_sm = st.selectbox("🖱️ Select a TriplesMap:*", list_to_choose, key="key_tm_label_input_for_sm_default",
                    index=list_to_choose.index(st.session_state["last_added_tm_list"][0]))
        else:
            with col1a:
                list_to_choose = list(reversed(tm_wo_sm_list))
                list_to_choose.insert(0, "Select a TriplesMap")
                tm_label_for_sm = st.selectbox("🖱️ Select a TriplesMap:*", list_to_choose, key="key_tm_label_input_for_sm")

        if tm_label_for_sm != "Select a TriplesMap":   #TriplesMap selected
            tm_iri_for_sm = tm_dict[tm_label_for_sm]
            ls_iri_for_sm = next(st.session_state["g_mapping"].objects(tm_iri_for_sm, RML.logicalSource), None)
            ds_for_sm = str(next(st.session_state["g_mapping"].objects(ls_iri_for_sm, RML.source), None))
            column_list = []  # will search only if needed, can be slow if failed connections

            with col1b:
                if existing_sm_list:
                    st.write("")
                    list_to_choose = ["Template 📐", "Constant 🔒", "Reference 📊", "Existing Map 📑"]
                    sm_generation_rule = st.radio("🖱️ Subject Map generation rule:*", list_to_choose,
                        label_visibility="collapsed", horizontal=True, key="key_sm_generation_rule_radio")
                else:
                    list_to_choose = ["Template 📐", "Constant 🔒", "Reference 📊"]
                    sm_generation_rule = st.radio("🖱️ Subject Map generation rule:*", list_to_choose,
                        label_visibility="collapsed", horizontal=False, key="key_sm_generation_rule_radio")


            if sm_generation_rule == "Existing Map 📑":

                with col1a:
                    existing_sm_list.append("Select a Subject Map")
                    sm_label = st.selectbox("🖱️ Select existing Subject Map:*", reversed(existing_sm_list), key="key_sm_label_existing")
                    if sm_label != "Select a Subject Map":
                        sm_iri = existing_sm_dict[sm_label]
                        tm_iri_for_sm = tm_dict[tm_label_for_sm]
                        st.session_state["sm_iri"] = sm_iri
                        st.session_state["sm_label"] = sm_label
                        st.session_state["tm_label_for_sm"] = tm_label_for_sm
                        with col1a:
                            st.button("Save", key="key_save_existing_sm_button", on_click=save_sm_existing)


            else:
                #_______________________________________________
                # SUBJECT MAP - TEMPLATE-VALUED
                if sm_generation_rule == "Template 📐":

                    with col1:
                        st.markdown("""
                        <div style="font-size:13px; font-weight:500; margin-top:10px; margin-bottom:6px; border-top:0.5px solid #ccc; padding-bottom:4px;">
                            <b>📐 Template</b><br>
                        </div>""", unsafe_allow_html=True)

                    with col1:
                        col1a, col1b, col1c = st.columns([0.8, 1.2, 0.5])
                    with col1a:
                        list_to_choose = ["🔒 Fixed part", "📈 Variable part", "🏷️ Fixed namespace", "🗑️ Reset template"]
                        build_template_action_sm = st.selectbox(
                            "🖱️ Add template part:", list_to_choose,
                            label_visibility="collapsed", key="key_build_template_action_sm")


                    if build_template_action_sm == "🔒 Fixed part":
                        with col1b:
                            sm_template_fixed_part = st.text_input("⌨️ Enter fixed part:", key="key_sm_fixed_part",
                                label_visibility="collapsed")
                            if re.search(r"[ \t\n\r<>\"{}|\\^`]", sm_template_fixed_part):
                                st.markdown(f"""<div class="warning-message">
                                        ⚠️ You included a space or an unescaped character, which is discouraged.
                                    </div>""", unsafe_allow_html=True)
                                st.write("")
                        with col1c:
                            if sm_template_fixed_part:
                                st.button("Add", key="key_save_sm_template_fixed_part_button", on_click=save_sm_template_fixed_part)

                    elif build_template_action_sm == "📈 Variable part":

                        column_list = utils.get_column_list_and_give_info(tm_iri_for_sm)[0]
                        column_list_ok_flag = utils.get_column_list_and_give_info(tm_iri_for_sm)[1]
                        inner_column_list_html = utils.get_column_list_and_give_info(tm_iri_for_sm)[2]

                        with col2b:
                            if column_list_ok_flag:
                                st.markdown(f"""<div class="info-message-blue">
                                    {inner_column_list_html}
                                </div>""", unsafe_allow_html=True)
                            else:
                                st.markdown(f"""<div class="warning-message">
                                    {inner_column_list_html}
                                </div>""", unsafe_allow_html=True)

                        if not column_list:   #data source is not available (load)
                            with col1c:
                                sm_template_variable_part = st.text_input("⌨️ Manually enter column of the data source:*",
                                    label_visibility="collapsed")
                                st.markdown("""<div style='text-align: right; font-size: 10.5px; color: #cc9a06; font-weight: bold; margin-top: -10px;'>
                                    ⚠️ discouraged
                                </div>""", unsafe_allow_html=True)
                            with col1c:
                                if sm_template_variable_part:
                                    st.button("Add", key="save_sm_template_variable_part_button", on_click=save_sm_template_variable_part)
                        else:  # data source is available
                            with col1b:
                                list_to_choose = column_list.copy()
                                list_to_choose.insert(0, "Select reference")
                                sm_template_variable_part = st.selectbox("🖱️ Select the column of the data source:", list_to_choose,
                                    label_visibility="collapsed", key="key_sm_template_variable_part")
                            with col1:
                                if st.session_state["sm_template_list"] and st.session_state["sm_template_list"][-1].endswith("}"):
                                    st.markdown(f"""<div class="warning-message">
                                            ⚠️ <b>Best practice:</b> add a fixed part between two variable parts to improve clarity.
                                        </div>""", unsafe_allow_html=True)
                            with col1c:
                                if sm_template_variable_part != "Select reference":
                                    st.button("Add", key="save_sm_template_variable_part_button", on_click=save_sm_template_variable_part)


                    elif build_template_action_sm == "🏷️ Fixed namespace":
                        with col1b:
                            mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
                            list_to_choose = sorted(mapping_ns_dict.keys())
                            list_to_choose.insert(0, "Select a namespace")
                            sm_template_ns_prefix = st.selectbox("🖱️ Select a namespace for the template:", list_to_choose,
                                label_visibility="collapsed", key="key_sm_template_ns_prefix")
                            ns_needed_for_sm_flag = True

                        with col1c:
                            if sm_template_ns_prefix != "Select a namespace":
                                sm_template_ns = mapping_ns_dict[sm_template_ns_prefix]
                                st.button("Add", key="key_add_ns_to_sm_template_button", on_click=add_ns_to_sm_template)


                    elif build_template_action_sm == "🗑️ Reset template":
                        with col1b:
                            st.markdown(f"""<div class="warning-message">
                                    ⚠️ The current template <b>will be deleted</b>.
                                </div>""", unsafe_allow_html=True)
                        with col1c:
                            st.button("Reset", on_click=reset_sm_template)

                    with col1:
                        sm_template = "".join(st.session_state["sm_template_list"])
                        if sm_template:
                            if len(sm_template) < 60:
                                st.markdown(f"""
                                    <div class="gray-preview-message" style="word-wrap:break-word; overflow-wrap:anywhere;">
                                        📐 <b>Your <b style="color:#F63366;">template</b> so far:</b><br>
                                    <div style="margin-top:0.2em; margin-left:20px; font-size:15px;">
                                            {sm_template}
                                    </div></div>""", unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                    <div class="gray-preview-message" style="word-wrap:break-word; overflow-wrap:anywhere;">
                                        📐 <b>Your <b style="color:#F63366;">template</b> so far:</b><br>
                                    <div style="margin-top:0.2em; margin-left:20px; font-size:15px;">
                                            <small>{sm_template}</small>
                                    </div></div>""", unsafe_allow_html=True)
                            st.write("")
                        else:
                            st.markdown(f"""<div class="gray-preview-message">
                                    📐 <b> Build your <b style="color:#F63366;">template</b>
                                    above and preview it here.</b> <small>You can add as many parts as you need.</small></div>""", unsafe_allow_html=True)
                            st.write("")


                #_______________________________________________
                # SUBJECT MAP - CONSTANT-VALUED
                if sm_generation_rule == "Constant 🔒":

                    # with col1:
                    #     st.markdown("""
                    #     <div style="font-size:13px; font-weight:500; margin-top:10px; margin-bottom:6px; border-top:0.5px solid #ccc; padding-bottom:4px;">
                    #         <b>🔒 Constant</b><br>
                    #     </div>""", unsafe_allow_html=True)

                    with col1:
                        col1a, col1b = st.columns([1,2])
                    with col1b:
                        sm_constant = st.text_input("⌨️ Enter constant:*", key="key_sm_constant")

                    mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
                    list_to_choose = sorted(mapping_ns_dict.keys())
                    list_to_choose.insert(0, "Select a namespace")
                    with col1a:
                        sm_constant_ns_prefix = st.selectbox("🖱️ Namespace (opt):", list_to_choose,
                            key="key_sm_constant_ns")

                        if not mapping_ns_dict:
                            ns_needed_for_sm_flag = True

                #_______________________________________________
                #SUBJECT MAP - REFERENCED-VALUED
                if sm_generation_rule ==  "Reference 📊":
                    sm_datatype = ""
                    sm_language_tag = ""
                    sm_ready_flag_reference = False


                    # with col1:
                    #     st.markdown("""
                    #     <div style="font-size:13px; font-weight:500; margin-top:10px; margin-bottom:6px; border-top:0.5px solid #ccc; padding-bottom:4px;">
                    #         <b>📊 Reference</b><br>
                    #     </div>""", unsafe_allow_html=True)
                    with col1:
                        col1a, col1b = st.columns([2,1])
                    with col1a:
                        column_list = utils.get_column_list_and_give_info(tm_iri_for_sm)[0]
                        column_list_ok_flag = utils.get_column_list_and_give_info(tm_iri_for_sm)[1]
                        inner_column_list_html = utils.get_column_list_and_give_info(tm_iri_for_sm)[2]

                        with col2b:
                            if column_list_ok_flag:
                                st.markdown(f"""<div class="info-message-blue">
                                    {inner_column_list_html}
                                </div>""", unsafe_allow_html=True)
                            else:
                                st.markdown(f"""<div class="warning-message">
                                    {inner_column_list_html}
                                </div>""", unsafe_allow_html=True)

                    if not column_list:   #data source is not available (load)
                        with col1a:
                            sm_column_name = st.text_input("⌨️ Manually enter logical source reference:*")
                            st.markdown("""<div style='text-align: right; font-size: 10.5px; color: #cc9a06; font-weight: bold; margin-top: -10px;'>
                                    ⚠️ discouraged
                                </div>""", unsafe_allow_html=True)

                    else:
                        with col1a:
                            list_to_choose = column_list.copy()
                            list_to_choose.insert(0, "Select reference")
                            sm_column_name = st.selectbox(f"""🖱️ Select reference:*""", list_to_choose,
                                key="key_sm_column_name")


                # ADDITIONAL CONFIGURATION
                with col1:
                    st.markdown("""
                    <div style="font-size:13px; font-weight:500; margin-top:10px; margin-bottom:6px; border-top:0.5px solid #ccc; padding-bottom:4px;">
                        <b>⚙️ Additional Configuration</b><br>
                    </div>""", unsafe_allow_html=True)
                with col1:
                    col1a, col1b, col1c = st.columns(3)

                # TERM TYPE
                with col1a:
                    if sm_generation_rule ==  "Constant 🔒":
                        list_to_choose = ["🌐 IRI"]
                    else:
                        list_to_choose = ["🌐 IRI", "👻 BNode"]
                    sm_term_type = st.selectbox("🆔 Select term type:*", list_to_choose,
                        key="key_sm_term_type")

                # SUBJECT MAP LABEL
                with col1a:
                    label_sm_option = st.selectbox("♻️ Reuse Subject Map (opt):", ["No", "Yes (add label)"])
                    if label_sm_option == "Yes (add label)":
                        sm_label = st.text_input("🔖 Enter Subject Map label:*", key="key_sm_label_new")
                        valid_sm_label = utils.is_valid_label_hard(sm_label, display_option=False)
                    else:
                        sm_label = ""
                        sm_iri = BNode()

                # SUBJECT CLASS
                # dictionary for simple classes
                with col1b:
                    ontology_classes_dict = {}
                    class_triples = set()
                    class_triples |= set(st.session_state["g_ontology"].triples((None, RDF.type, OWL.Class)))   #collect owl:Class definitions
                    class_triples |= set(st.session_state["g_ontology"].triples((None, RDF.type, RDFS.Class)))    # collect rdfs:Class definitions
                    for s, p, o in class_triples:   #we add to dictionary removing the BNodes
                        if not isinstance(s, BNode):
                            ontology_classes_dict[split_uri(s)[1]] = s


                    # ONLY SHOW OPTIONS IF THE ONTOLOGY HAS THEM
                    if ontology_classes_dict:   # if the ontology includes at least one class
                        list_to_choose = ["No class", "🧩 Ontology class", "🚫 Class outside ontology", "🔢 Multiple classes"]
                    else:
                        list_to_choose = ["No class", "🚫 Class outside ontology", "🔢 Multiple classes"]

                    add_subject_class_option = st.selectbox("🏷️ Subject class (optional):",
                        list_to_choose, key="key_add_subject_class_option")

                    #ONTOLOGY CLASS
                    if add_subject_class_option == "🧩 Ontology class":

                        # Filter by ontology
                        if len(st.session_state["g_ontology_components_dict"]) > 1:
                            list_to_choose = sorted(st.session_state["g_ontology_components_tag_dict"].values())
                            list_to_choose.insert(0, "Select ontology")
                            ontology_filter_for_subject_class = st.selectbox("⚙️ Filter by ontology (optional):",
                                list_to_choose, key="key_ontology_filter_for_subject_class")

                            if ontology_filter_for_subject_class == "Select ontology":
                                ontology_filter_for_subject_class = st.session_state["g_ontology"]
                            else:
                                for ont_label, ont_tag in st.session_state["g_ontology_components_tag_dict"].items():
                                    if ont_tag == ontology_filter_for_subject_class:
                                        ontology_filter_for_subject_class = st.session_state["g_ontology_components_dict"][ont_label]
                                        break

                        else:
                            ontology_filter_for_subject_class = st.session_state["g_ontology"]

                        # class dictionary filtered by ontology
                        ontology_classes_dict = {}
                        class_triples = set()
                        class_triples |= set(ontology_filter_for_subject_class.triples((None, RDF.type, OWL.Class)))   #collect owl:Class definitions
                        class_triples |= set(ontology_filter_for_subject_class.triples((None, RDF.type, RDFS.Class)))    # collect rdfs:Class definitions
                        for s, p, o in class_triples:   #we add to dictionary removing the BNodes
                            if not isinstance(s, BNode):
                                ontology_classes_dict[split_uri(s)[1]] = s

                        # dictionary for superclasses
                        superclass_dict = {}
                        for s, p, o in list(set(ontology_filter_for_subject_class.triples((None, RDFS.subClassOf, None)))):
                            if not isinstance(o, BNode) and o not in superclass_dict.values():
                                superclass_dict[o.split("/")[-1].split("#")[-1]] = o

                        # Class selection
                        if superclass_dict:   # there exists at least one superclass (show superclass filter)
                            classes_in_superclass_dict = {}
                            superclass_list = sorted(superclass_dict.keys())
                            superclass_list.insert(0, "No filter")
                            superclass = st.selectbox("⚙️ Filter by superclass (opt):", superclass_list,
                                key="key_superclass")   #superclass label
                            if superclass != "No filter":   # a superclass has been selected (filter)
                                classes_in_superclass_dict[superclass] = superclass_dict[superclass]
                                superclass = superclass_dict[superclass] #we get the superclass iri
                                for s, p, o in list(set(st.session_state["g_ontology"].triples((None, RDFS.subClassOf, superclass)))):
                                    classes_in_superclass_dict[split_uri(s)[1]] = s
                                class_list = sorted(classes_in_superclass_dict.keys())
                                class_list.insert(0, "Select class")
                                subject_class = st.selectbox("🖱️ Select class:", class_list,
                                    key="key_subject_class")   #class label

                            else:  #no superclass selected (list all classes)
                                class_list = sorted(ontology_classes_dict.keys())
                                class_list.insert(0, "Select class")
                                subject_class = st.selectbox("🖱️ Select class:*", class_list,
                                    key="key_subject_class")   #class label

                        else:     #no superclasses exist (no superclass filter)
                            class_list = sorted(ontology_classes_dict.keys())
                            class_list.insert(0, "Select class")
                            subject_class = st.selectbox("🖱️ Select class:*", class_list,
                                key="key_subject_class")   #class label

                        if subject_class != "Select class":
                            subject_class_iri = ontology_classes_dict[subject_class] #we get the superclass iri
                            st.session_state["multiple_subject_class_list"] = [subject_class_iri]
                        else:
                            subject_class_iri = ""

                    #CLASS OUTSIDE ONTOLOGY
                    if add_subject_class_option == "🚫 Class outside ontology":

                        mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])

                        subject_class_prefix_list = list(mapping_ns_dict.keys())
                        list_to_choose = sorted(mapping_ns_dict.keys())
                        list_to_choose.insert(0,"Select a namespace")
                        subject_class_prefix = st.selectbox("🖱️ Select a namespace:*", list_to_choose,
                            key="key_subject_class_prefix")

                        ns_needed_for_sm_flag = True
                        if subject_class_prefix != "Select a namespace":
                            NS = Namespace(mapping_ns_dict[subject_class_prefix])
                        subject_class_input = st.text_input("⌨️ Enter subject class:*", key="key_subject_class_input")

                        if subject_class_input and subject_class_prefix != "Select a namespace":
                            subject_class_iri = NS[subject_class_input]
                            st.session_state["multiple_subject_class_list"] = [subject_class_iri]
                        else:
                            subject_class_iri = ""

                    #MULTIPLE SUBJECT CLASSES
                    if add_subject_class_option == "🔢 Multiple classes":

                        if ontology_classes_dict:   # if the ontology includes at least one class
                            list_to_choose = ["🧩 Ontology class", "🚫 Class outside ontology"]
                            if st.session_state["multiple_subject_class_list"]:
                                list_to_choose.insert(0, "✔️ Ready")
                                list_to_choose.append("🗑️ Remove class")
                            add_class_option = st.selectbox("🖱️ Select an option:*", list_to_choose,
                                key="key_add_multiple_subject_class_option")

                        else:
                            add_class_option == "🚫 Class outside ontology"

                        if add_class_option == "🧩 Ontology class":

                            # Filter by ontology
                            if len(st.session_state["g_ontology_components_dict"]) > 1:
                                list_to_choose = sorted(st.session_state["g_ontology_components_tag_dict"].values())
                                list_to_choose.insert(0, "Select ontology")
                                ontology_filter_for_subject_class = st.selectbox("⚙️ Filter by ontology (optional):",
                                    list_to_choose, key="key_ontology_filter_for_subject_class")

                                if ontology_filter_for_subject_class == "Select ontology":
                                    ontology_filter_for_subject_class = st.session_state["g_ontology"]
                                else:
                                    for ont_label, ont_tag in st.session_state["g_ontology_components_tag_dict"].items():
                                        if ont_tag == ontology_filter_for_subject_class:
                                            ontology_filter_for_subject_class = st.session_state["g_ontology_components_dict"][ont_label]
                                            break

                            else:
                                ontology_filter_for_subject_class = st.session_state["g_ontology"]

                            # class dictionary filtered by ontology
                            ontology_classes_dict = {}
                            class_triples = set()
                            class_triples |= set(ontology_filter_for_subject_class.triples((None, RDF.type, OWL.Class)))   #collect owl:Class definitions
                            class_triples |= set(ontology_filter_for_subject_class.triples((None, RDF.type, RDFS.Class)))    # collect rdfs:Class definitions
                            for s, p, o in class_triples:   #we add to dictionary removing the BNodes
                                if not isinstance(s, BNode):
                                    ontology_classes_dict[split_uri(s)[1]] = s

                            # dictionary for superclasses
                            superclass_dict = {}
                            for s, p, o in list(set(ontology_filter_for_subject_class.triples((None, RDFS.subClassOf, None)))):
                                if not isinstance(o, BNode) and o not in superclass_dict.values():
                                    superclass_dict[o.split("/")[-1].split("#")[-1]] = o

                            # Class selection
                            if superclass_dict:   # there exists at least one superclass (show superclass filter)
                                classes_in_superclass_dict = {}
                                list_to_choose = sorted(superclass_dict.keys())
                                list_to_choose.insert(0, "No filter")
                                superclass = st.selectbox("⚙️ Filter by superclass (opt):", list_to_choose,
                                    key="key_superclass")   #superclass label
                                if superclass != "No filter":   # a superclass has been selected (filter)
                                    classes_in_superclass_dict[superclass] = superclass_dict[superclass]
                                    superclass = superclass_dict[superclass] #we get the superclass iri
                                    for s, p, o in list(set(st.session_state["g_ontology"].triples((None, RDFS.subClassOf, superclass)))):
                                        classes_in_superclass_dict[split_uri(s)[1]] = s
                                    list_to_choose = sorted(classes_in_superclass_dict.keys())
                                    list_to_choose.insert(0, "Select class")
                                    subject_class = st.selectbox("🖱️ Select class:", list_to_choose,
                                        key="key_subject_class")   #class label

                                else:  #no superclass selected (list all classes)
                                    list_to_choose = sorted(ontology_classes_dict.keys())
                                    list_to_choose.insert(0, "Select class")
                                    subject_class = st.selectbox("🖱️ Select Class:*", list_to_choose,
                                        key="key_subject_class")   #class label

                            else:     #no superclasses exist (no superclass filter)
                                class_list = sorted(ontology_classes_dict.keys())
                                class_list.insert(0, "Select class")
                                subject_class = st.selectbox("🖱️ Select class:*", class_list,
                                    key="key_subject_class")   #class label

                            if subject_class != "Select class":
                                subject_class_iri = ontology_classes_dict[subject_class] #we get the superclass iri
                                st.button("Add", key="key_add_subject_class_button", on_click=add_subject_class)

                        if add_class_option == "🚫 Class outside ontology":

                            mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])

                            subject_class_prefix_list = list(mapping_ns_dict.keys())
                            list_to_choose = sorted(mapping_ns_dict.keys())
                            list_to_choose.insert(0,"Select a namespace")
                            subject_class_prefix = st.selectbox("🖱️ Select a namespace:*", list_to_choose,
                                key="key_subject_class_prefix")

                            ns_needed_for_sm_flag = True
                            if subject_class_prefix != "Select a namespace":
                                NS = Namespace(mapping_ns_dict[subject_class_prefix])
                            subject_class_input = st.text_input("⌨️ Enter subject class:*", key="key_subject_class_input")

                            if subject_class_input and subject_class_prefix != "Select a namespace":
                                subject_class_iri = NS[subject_class_input]
                                st.button("Add", key="key_add_subject_class_button", on_click=add_subject_class)

                        if add_class_option == "🗑️ Remove class":
                            list_to_choose = []
                            for class_iri in st.session_state["multiple_subject_class_list"]:
                                list_to_choose.append(split_uri(class_iri)[1])
                            if len(list_to_choose) > 1:
                                list_to_choose.insert(0, "Select all")
                            subject_class_to_remove_list = st.multiselect("🖱️ Select classes:*", list_to_choose,
                                key="key_subject_class_to_remove_list")
                            if subject_class_to_remove_list:
                                st.button("Remove", key="key_remove_multiple_subject_classes_button",
                                    on_click=key_remove_multiple_subject_classes)

                        if st.session_state["multiple_subject_class_list"]:
                            list_for_display = []
                            for class_iri in st.session_state["multiple_subject_class_list"]:
                                list_for_display.append(split_uri(class_iri)[1])
                            st.markdown(f"""
                                <div class="gray-preview-message" style="word-wrap:break-word; overflow-wrap:anywhere;">
                                    🏷️ <b style="color:#F63366;">Subject classes:</b><br>
                                 <div style="margin-top:0.2em; margin-left:20px; font-size:15px;">
                                        <small><b>{utils.format_list_for_markdown(list_for_display)}</b></small>
                                </div></div>""", unsafe_allow_html=True)
                            st.write("")


                # GRAPH MAP
                with col1c:
                    list_to_choose = ["Default graph", "Add graph map"]
                    add_sm_graph_map_option = st.selectbox("️🗺️️ Graph map (optional):",
                        list_to_choose, key="key_add_sm_graph_map_option")

                    #GRAPH - If not given, default graph    HERE condider if rr:graphMap option (dynamic) is worth it
                    if add_sm_graph_map_option == "Add graph map":

                        mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
                        list_to_choose = sorted(mapping_ns_dict.keys())
                        list_to_choose.insert(0,"Select namespace")
                        subject_graph_prefix = st.selectbox("🖱️ Select namespace:*", list_to_choose,
                            key="key_subject_graph_prefix")

                        ns_needed_for_sm_flag = True
                        subject_graph_input = st.text_input("🖱️ Enter graph map:*", key="key_subject_graph_input")
                        if subject_graph_prefix != "Select namespace":
                            NS = Namespace(mapping_ns_dict[subject_graph_prefix])

                        if subject_graph_input and subject_graph_prefix != "Select namespace":
                            subject_graph = NS[subject_graph_input]

                        else:
                            subject_graph = ""


                # CHECK EVERYTHING IS READY________________________________
                sm_complete_flag = True
                inner_html_error = ""
                inner_html_warning = ""

                if ns_needed_for_sm_flag and not utils.get_g_ns_dict(st.session_state["g_mapping"]):
                    inner_html_error += f"""<small>· <b>No namespaces available.</b> Go to the
                        <b>Global Configuration</b> page to add them.</small><br>"""


                if sm_generation_rule == "Template 📐":
                    if not sm_template:
                        sm_complete_flag = False
                        inner_html_error += "<small>· The <b>template</b> is empty.</small><br>"
                    elif not st.session_state["sm_template_variable_part_flag"]:
                        inner_html_error += """<small>· The <b>template</b> must contain
                            at least one <b>variable part</b>.</small><br>"""
                        sm_complete_flag = False

                if sm_generation_rule == "Constant 🔒":
                    if not sm_constant:
                        sm_complete_flag = False
                        inner_html_error += "<small>· No <b>constant</b> entered.</small><br>"

                    if not (sm_constant_ns_prefix != "Select a namespace" and sm_constant):
                        if not utils.is_valid_iri(sm_constant, delimiter_ending=False):
                            sm_complete_flag = False
                            inner_html_error += """<small>· If <b>no namespace</b> is selected,
                                the constant must be a <b>valid IRI</b>.</small><br>"""


                if sm_generation_rule == "Reference 📊":
                    if column_list:
                        if sm_column_name == "Select reference":
                            sm_complete_flag = False
                            inner_html_error += "<small>· The <b>reference</b> has not been selected.<small><br>"
                    else:
                        if not sm_column_name:
                            sm_complete_flag = False
                            inner_html_error += "<small>· The <b>reference</b> has not been selected.<small><br>"

                if sm_generation_rule == "Template 📐":
                    if sm_template and sm_term_type == "🌐 IRI":   # if term type is IRI the NS is recommended
                        if not st.session_state["sm_template_prefix"]:
                            inner_html_warning += """<small>· Term type is <b>🌐 IRI</b>.
                                We recommend <b>adding a namespace to the template</b>.</small><br>"""

                if sm_generation_rule == "Reference 📊":
                    if sm_column_name and sm_term_type == "🌐 IRI":
                        inner_html_warning += """<small>· Term type is <b>🌐 IRI</b>.
                                    Make sure the values in the referenced column
                                    are valid IRIs.</small><br>"""


                if add_subject_class_option == "🧩 Ontology class":
                    if subject_class == "Select class":
                        sm_complete_flag = False
                        inner_html_error += "<small>· The <b>subject class</b> has not been selected.</small><br>"
                if add_subject_class_option == "🚫 Class outside ontology":
                    if not subject_class_input:
                        sm_complete_flag = False
                        inner_html_error += """<small>· The <b>subject class</b>
                            has not been given.</small><br>"""
                    if subject_class_prefix == "Select a namespace":
                        inner_html_warning += """<small>· The <b>subject class</b> has no namespace</small><br>"""
                if add_subject_class_option == "🔢 Multiple Classes":
                    if not st.session_state["multiple_subject_class_list"]:
                        sm_complete_flag = False
                        inner_html_error += """<small>· You must add at least one <b>subject class</b>.</small><br>"""

                if add_sm_graph_map_option == "Add graph map":
                    if not subject_graph_input:
                        sm_complete_flag = False
                        inner_html_error += """<small>· The <b>graph map</b>
                            has not been given.</small><br>"""
                    if subject_graph_prefix == "Select namespace":
                        inner_html_warning += """<small>· The <b>graph map</b> has no namespace.</small><br>"""

                if add_subject_class_option == "🚫 Class outside ontology":
                    if st.session_state["g_ontology"] and not ontology_classes_dict: #there is an ontology but it has no classes
                        inner_html_warning += """<small>· Your <b>ontology</b> does not define any classes.
                                      Using an ontology with predefined classes is recommended.</small><br>"""
                    elif st.session_state["g_ontology"]:   #there exists an ontology and it has classes
                        inner_html_warning += """<small>· The option <b>🚫 Class outside Ontology</b> lacks ontology alignment.
                                      An ontology-driven approach is recommended.</small><br>"""
                    else:
                        inner_html_warning += """<small>· You are working <b>without an ontology</b>. Importing an ontology
                                    from the <b> Global Configuration</b> page is encouraged.</small><br>"""


                if label_sm_option == "Yes (add label)":
                    if not sm_label:
                        sm_complete_flag = False
                        inner_html_error += """<small>· The <b>Subject Map label</b>
                            has not been given.</small><br>"""
                    elif not valid_sm_label:
                        sm_complete_flag = False
                        inner_html_error += """<small>· The <b>Subject Map label</b>
                            is not valid (only safe characters allowed and cannot end with puntuation).</small><br>"""
                    else:
                        NS = st.session_state["base_ns"][1]
                        sm_iri = BNode() if not sm_label else NS[sm_label]
                        if next(st.session_state["g_mapping"].triples((None, RML.subjectMap, sm_iri)), None):
                            sm_complete_flag = False
                            inner_html_error += """<small>· That <b>Subject Map label</b> is already in use.
                                Please pick a different label.</small><br>"""


                # INFO AND SAVE BUTTON____________________________________
                with col2b:

                    if inner_html_warning:
                        st.markdown(f"""<div class="warning-message" style="font-size:13px; line-height:1.2;">
                            ⚠️ <b>Caution.</b><br>
                            <div style='margin-left: 1.5em;'>{inner_html_warning}</div>
                        </div>""", unsafe_allow_html=True)

                    if inner_html_error:
                        st.markdown(f"""<div class="error-message" style="font-size:13px; line-height:1.2;">
                                ❌ <b>Subject Map is incomplete.</b><br>
                            <div style='margin-left: 1.5em;'>{inner_html_error}</div>
                            </div>""", unsafe_allow_html=True)

                    if sm_complete_flag:
                        st.markdown(f"""<div class="success-message">
                            ✔️ All <b>required fields (*)</b> are complete.
                            <small>Double-check the information before saving.</smalL> </div>
                        """, unsafe_allow_html=True)

                with col1c:
                    if sm_complete_flag:
                        st.markdown("""
                        <div style="font-size:13px; font-weight:500; margin-top:10px; margin-bottom:6px; border-top:0.5px solid #ccc; padding-bottom:4px;">
                            <b>💾 Save</b><br>
                        </div>""", unsafe_allow_html=True)
                        if sm_generation_rule == "Template 📐":
                            save_sm_template_button = st.button("Save", on_click=save_sm_template, key="key_save_sm_template_button")
                        elif sm_generation_rule == "Constant 🔒":
                            save_sm_constant_button = st.button("Save", on_click=save_sm_constant, key="key_save_sm_constant_button")
                        if sm_generation_rule == "Reference 📊":
                            save_sm_reference_button = st.button("Save", on_click=save_sm_reference, key="key_save_sm_reference_button")


    with col2b:

        st.write("")
        st.write("")

        last_added_sm_df = pd.DataFrame([
            {"Subject Map": sm_dict[subject_map][0], "Assigned to": triples_map,  # Use directly or format if needed
            "Rule": sm_dict[subject_map][1], "Term": sm_dict[subject_map][2]}
            for subject_map, triples_map in st.session_state["last_added_sm_list"]
            if subject_map in sm_dict])

        last_last_added_sm_df = last_added_sm_df.head(utils.get_max_length_for_display()[1])

        max_length = utils.get_max_length_for_display()[0]   # max number of tm shown in dataframe
        if st.session_state["last_added_sm_list"]:
            st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                    🔎 last added Subject Maps
                </div>""", unsafe_allow_html=True)
            if len(sm_dict) < max_length:
                st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        (complete list below)
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        (longer list below)
                    </div>""", unsafe_allow_html=True)
            st.dataframe(last_last_added_sm_df, hide_index=True)
            st.write("")


        #Option to show all TriplesMaps
        sm_df = pd.DataFrame([
            {"Subject Map": v[0], "Assigned to": utils.format_list_for_markdown(v[4]),
                "Rule": v[1], "ID/Constant": v[3]} for k, v in reversed(sm_dict.items())])
        sm_df_short = sm_df.head(max_length)

        if sm_dict and len(sm_dict) < max_length:
            with st.expander("🔎 Show all Subject Maps"):
                st.write("")
                st.dataframe(sm_df, hide_index=True)
        elif sm_dict:
            with st.expander("🔎 Show more Subject Maps"):
                st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        Go to the <b>Display Mapping</b> page for more information.
                    </div>""", unsafe_allow_html=True)
                st.write("")
                st.dataframe(sm_df_short, hide_index=True)



#________________________________________________
#ADD PREDICATE-OBJECT MAP TO MAP
with tab3:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])

    with col2:
        col2a, col2b = st.columns([1,2])

    with col2:
        col2a, col2b = st.columns([0.5, 2])   #HEREHERE


    #PURPLE HEADING - ADD NEW TRIPLESMAP
    with col1:
        st.markdown("""<div class="purple-heading">
                🧱 Add New Predicate-Object Map
            </div>""", unsafe_allow_html=True)
        st.write("")


    #POM_____________________________________________________


    if st.session_state["pom_saved_ok_flag"]:
        with col1:
            col1a, col1b = st.columns(2)
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b style="color:#F63366;">Predicate-Object Map</b> has been created!
            </div>""", unsafe_allow_html=True)
        st.session_state["pom_saved_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    #list of all triplesmaps with assigned Subject Map
    tm_w_sm_list = []
    for tm_label, tm_iri in tm_dict.items():
        if any(st.session_state["g_mapping"].triples((tm_iri, RML.subjectMap, None))):
            tm_w_sm_list.append(tm_label)

    if not tm_dict:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.markdown(f"""<div class="error-message">
                    ❌ No TriplesMaps in mapping <b>{st.session_state["g_label"]}</b>.
                    <small>You can add new TriplesMaps in the <b>Add TriplesMap</b> panel.</small>
                </div>""", unsafe_allow_html=True)

    else:

        with col1:
            col1a, col1b = st.columns(2)

        with col1a:
            if st.session_state["last_added_tm_list"]:
                list_to_choose = list(reversed(tm_dict))
                list_to_choose.insert(0, "Select a TriplesMap")
                tm_label_for_pom = st.selectbox("🖱️ Select a TriplesMap:*", list_to_choose, key="key_tm_label_for_pom",
                    index=list_to_choose.index(st.session_state["last_added_tm_list"][0]))
            else:
                list_to_choose = list(reversed(tm_dict))
                list_to_choose.insert(0, "Select a TriplesMap")
                tm_label_for_pom = st.selectbox("🖱️ Select a TriplesMap:*", list_to_choose, key="key_tm_label_for_pom")

        if tm_label_for_pom != "Select a TriplesMap":

            ns_needed_for_pom_flag = False

            tm_iri_for_pom = tm_dict[tm_label_for_pom]
            pom_iri = BNode()
            om_iri = BNode()
            column_list = [] # will search only if needed, can be slow with failed connections

            # GENERATION RULE

            om_generation_rule_list = ["Template 📐", "Constant 🔒", "Reference 📊"]


            with col1b:
                om_generation_rule = st.radio("🖱️ Object Map generation rule:*", om_generation_rule_list,
                    label_visibility="collapsed", horizontal=False, key="key_om_generation_rule_radio")

            # PREDICATE
            with col1:
                col1a, col1b = st.columns(2)

            with col1a:
                st.markdown("""
                <div style="font-size:13px; font-weight:500; margin-top:10px; margin-bottom:6px; border-top:0.5px solid #ccc; padding-bottom:4px;">
                    <b>🅿️ Predicate</b><br>
                </div>""", unsafe_allow_html=True)

            if st.session_state["g_ontology_components_dict"]:
                ontology_p_dict = utils.get_ontology_properties_dict(st.session_state["g_ontology"])

                if ontology_p_dict:   # if the ontology includes at least one predicate

                    # Filter by ontology
                    if len(st.session_state["g_ontology_components_dict"]) > 1:
                        with col1a:
                            list_to_choose = sorted(st.session_state["g_ontology_components_tag_dict"].values())
                            list_to_choose.insert(0, "Select ontology")
                            ontology_filter_for_predicate = st.selectbox("⚙️ Filter by ontology (optional):",
                                list_to_choose, key="key_ontology_filter_for_predicate")

                        if ontology_filter_for_predicate == "Select ontology":
                            ontology_filter_for_predicate = st.session_state["g_ontology"]
                        else:
                            for ont_label, ont_tag in st.session_state["g_ontology_components_tag_dict"].items():
                                if ont_tag == ontology_filter_for_predicate:
                                    ontology_filter_for_predicate = st.session_state["g_ontology_components_dict"][ont_label]
                                    break

                    else:
                        ontology_filter_for_predicate = st.session_state["g_ontology"]

                    ontology_p_dict = utils.get_ontology_properties_dict(ontology_filter_for_predicate)

            else:     # no ontology predicates
                ontology_p_dict = {}

            with col1a:
                list_to_choose = sorted(ontology_p_dict.keys())
                if ontology_filter_for_predicate == st.session_state["g_ontology"]:
                    list_to_choose.insert(0, "🚫 Predicate outside ontology")
                list_to_choose.insert(0, "Select a predicate")
                selected_p_label = st.selectbox("🖱️ Select a predicate:*", list_to_choose, key="key_selected_p_label")

            if selected_p_label != "Select a predicate" and selected_p_label != "🚫 Predicate outside ontology":
                selected_p_iri = ontology_p_dict[selected_p_label]

            if selected_p_label == "🚫 Predicate outside ontology":

                mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])

                if not mapping_ns_dict:
                    ns_needed_for_pom_flag = True

                with col1a:
                    list_to_choose = sorted(mapping_ns_dict.keys())
                    list_to_choose.insert(0, "Select a namespace")
                    manual_p_ns_prefix = st.selectbox("🖱️ Select a namespace (for the predicate):*", list_to_choose, key="key_manual_p_ns_prefix")
                    manual_p_label = st.text_input("⌨️ Enter a predicate:*", key="key_manual_p_label")

                if manual_p_ns_prefix != "Select a namespace" and manual_p_label:
                    NS = Namespace(mapping_ns_dict[manual_p_ns_prefix])
                    selected_p_iri = NS[manual_p_label]

            #_______________________________________________
            # OBJECT MAP - TEMPLATE-VALUED
            if om_generation_rule == "Template 📐":

                with col1:
                    st.markdown("""
                    <div style="font-size:13px; font-weight:500; margin-top:10px; margin-bottom:6px; border-top:0.5px solid #ccc; padding-bottom:4px;">
                        <b>📐 Template</b><br>
                    </div>""", unsafe_allow_html=True)
                with col1:
                    col1a, col1b, col1c = st.columns([0.8, 1.2, 0.5])

                with col1a:
                    list_to_choose = ["🔒 Fixed part", "📈 Variable part", "🏷️ Fixed namespace", "🗑️ Reset template"]
                    build_template_action_om = st.selectbox("🖱️ Add template part:", list_to_choose,
                        label_visibility="collapsed", key="key_build_template_action_om")


                if build_template_action_om == "🔒 Fixed part":
                    with col1b:
                        om_template_fixed_part = st.text_input("⌨️ Enter fixed part:", key="key_om_fixed_part",
                            label_visibility="collapsed")
                        if re.search(r"[ \t\n\r<>\"{}|\\^`]", om_template_fixed_part):
                            st.markdown(f"""<div class="warning-message">
                                    ⚠️ You included a space or an unescaped character, which is discouraged.
                                </div>""", unsafe_allow_html=True)
                            st.write("")
                    with col1c:
                        if om_template_fixed_part:
                            st.button("Add", key="key_save_om_template_fixed_part_button", on_click=save_om_template_fixed_part)

                elif build_template_action_om == "📈 Variable part":

                    column_list = utils.get_column_list_and_give_info(tm_iri_for_pom)[0]
                    column_list_ok_flag = utils.get_column_list_and_give_info(tm_iri_for_pom)[1]
                    inner_column_list_html = utils.get_column_list_and_give_info(tm_iri_for_pom)[2]

                    with col2b:
                        if column_list_ok_flag:
                            st.markdown(f"""<div class="info-message-blue">
                                {inner_column_list_html}
                            </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown(f"""<div class="warning-message">
                                {inner_column_list_html}
                            </div>""", unsafe_allow_html=True)

                    if not column_list:   #data source is not available (load)
                        with col1b:
                            om_template_variable_part = st.text_input("⌨️ Manually enter reference:*",
                                label_visibility="collapsed", key="key_om_template_variable_part")
                            st.markdown("""<div style='text-align: right; font-size: 10.5px; color: #cc9a06; font-weight: bold; margin-top: -10px;'>
                                ⚠️ discouraged
                            </div>""", unsafe_allow_html=True)
                        if om_template_variable_part:
                            with col1c:
                                save_om_template_variable_part_button = st.button("Add", key="save_om_template_variable_part_button", on_click=save_om_template_variable_part)

                    else:  # data source is available
                        with col1b:
                            list_to_choose = column_list.copy()
                            list_to_choose.insert(0, "Select reference")
                            om_template_variable_part = st.selectbox("🖱️ Select reference:", list_to_choose,
                                label_visibility="collapsed", key="key_om_template_variable_part")
                        if st.session_state["om_template_list"] and st.session_state["om_template_list"][-1].endswith("}"):
                            with col1:
                                st.markdown(f"""<div class="warning-message">
                                        ⚠️ <b>Best practice:</b> add a fixed part between two variable parts to improve clarity.
                                    </div>""", unsafe_allow_html=True)
                        if om_template_variable_part != "Select reference":
                            with col1c:
                                save_om_template_variable_part_button = st.button("Add", key="save_om_template_variable_part_button", on_click=save_om_template_variable_part)


                elif build_template_action_om == "🏷️ Fixed namespace":
                    with col1b:
                        mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
                        list_to_choose = sorted(mapping_ns_dict.keys())
                        list_to_choose.insert(0, "Select a namespace")
                        om_template_ns_prefix = st.selectbox("🖱️ Select a namespace:", list_to_choose,
                            label_visibility="collapsed", key="key_om_template_ns_prefix")
                        if not mapping_ns_dict:
                            ns_needed_for_pom_flag = True

                    with col1c:
                        if om_template_ns_prefix != "Select a namespace":
                            om_template_ns = mapping_ns_dict[om_template_ns_prefix]
                            st.button("Add", key="key_add_ns_to_om_template_button", on_click=add_ns_to_om_template)


                elif build_template_action_om == "🗑️ Reset template":
                    with col1b:
                        st.markdown(f"""<div class="warning-message">
                                ⚠️ The current template will be deleted.
                            </div>""", unsafe_allow_html=True)
                    with col1c:
                        st.button("Reset", on_click=reset_om_template)

                with col1:
                    om_template = "".join(st.session_state["om_template_list"])
                    if om_template:
                        if len(om_template) < 40:
                            st.markdown(f"""
                                <div class="gray-preview-message" style="word-wrap:break-word; overflow-wrap:anywhere;">
                                    📐 <b>Your <b style="color:#F63366;">template</b> so far:</b><br>
                                <div style="margin-top:0.2em; margin-left:20px; font-size:15px;">
                                        {om_template}
                                </div></div>""", unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                                <div class="gray-preview-message" style="word-wrap:break-word; overflow-wrap:anywhere;">
                                    📐 <b>Your <b style="color:#F63366;">template</b> so far:</b><br>
                                <div style="margin-top:0.2em; margin-left:20px; font-size:15px;">
                                        <small>{om_template}</small>
                                </div></div>""", unsafe_allow_html=True)
                        st.write("")
                    else:
                        st.markdown(f"""<div class="gray-preview-message">
                                📐 <b> Build your <b style="color:#F63366;">template</b>
                                above and preview it here.</b> <small>You can add as many parts as you need.</small></div>""", unsafe_allow_html=True)
                        st.write("")


            #_______________________________________________
            # OBJECT MAP - CONSTANT-VALUED
            if om_generation_rule == "Constant 🔒":

                # with col1:
                #     st.markdown("""
                #     <div style="font-size:13px; font-weight:500; margin-top:10px; margin-bottom:6px; border-top:0.5px solid #ccc; padding-bottom:4px;">
                #         <b>🔒 Constant</b><br>
                #     </div>""", unsafe_allow_html=True)

                with col1b:
                    st.markdown("""
                    <div style="font-size:13px; font-weight:500; margin-top:10px; margin-bottom:6px; border-top:0.5px solid #ccc; padding-bottom:4px;">
                        <b>🔒 Constant</b><br>
                    </div>""", unsafe_allow_html=True)
                    om_constant = st.text_input("⌨️ Enter Object Map constant:*", key="key_om_constant")


            #_______________________________________________
            #OBJECT MAP - REFERENCED-VALUED
            if om_generation_rule ==  "Reference 📊":
                om_datatype = ""
                om_language_tag = ""
                om_ready_flag_reference = False

                column_list = utils.get_column_list_and_give_info(tm_iri_for_pom)[0]
                column_list_ok_flag = utils.get_column_list_and_give_info(tm_iri_for_pom)[1]
                inner_column_list_html = utils.get_column_list_and_give_info(tm_iri_for_pom)[2]

                with col2b:
                    if column_list_ok_flag:
                        st.markdown(f"""<div class="info-message-blue">
                            {inner_column_list_html}
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""<div class="warning-message">
                            {inner_column_list_html}
                        </div>""", unsafe_allow_html=True)

                with col1b:
                    st.markdown("""
                    <div style="font-size:13px; font-weight:500; margin-top:10px; margin-bottom:6px; border-top:0.5px solid #ccc; padding-bottom:4px;">
                        <b>📊 Reference</b><br>
                    </div>""", unsafe_allow_html=True)

                if not column_list:   #data source is not available (load)
                    with col1b:
                        om_column_name = st.text_input("⌨️ Enter reference manually:*", key="key_om_column_name")
                        st.markdown("""<div style='text-align: right; font-size: 10.5px; color: #cc9a06; font-weight: bold; margin-top: -10px;'>
                            ⚠️ discouraged
                        </div>""", unsafe_allow_html=True)
                else:
                    with col1b:
                        list_to_choose = column_list.copy()
                        list_to_choose.insert(0, "Select reference")
                        om_column_name = st.selectbox(f"""🖱️ Select reference:*""", list_to_choose,
                            key="key_om_column_name")


            # ADDITIONAL CONFIGURATION
            with col1:
                st.markdown("""
                <div style="font-size:13px; font-weight:500; margin-top:10px; margin-bottom:6px; border-top:0.5px solid #ccc; padding-bottom:4px;">
                    <b>⚙️ Additional Configuration</b><br>
                </div>""", unsafe_allow_html=True)
            with col1:
                col1a, col1b, col1c = st.columns(3)

            #TERM TYPE
            with col1a:
                if om_generation_rule == "Constant 🔒":
                    list_to_choose = ["📘 Literal", "🌐 IRI"]
                else:
                    list_to_choose = ["🌐 IRI", "📘 Literal", "👻 BNode"]

                om_term_type = st.selectbox("🆔 Select term type:*", list_to_choose,
                    key="om_term_type")

            if om_term_type == "📘 Literal":
                rdf_datatypes = list(utils.get_datatypes_dict().keys())

                with col1b:
                    om_datatype = st.selectbox("🖱️ Select datatype (optional):", rdf_datatypes,
                        key="key_om_datatype")

                if om_datatype == "Natural language tag":
                    language_tags = utils.get_language_tags_list()

                    with col1b:
                        om_language_tag = st.selectbox("🖱️ Select language tag:*", language_tags,
                            key="key_om_language_tag")


            # GRAPH MAP
            with col1c:
                list_to_choose = ["Default graph", "Add graph map"]
                add_om_graph_map_option = st.selectbox("️🗺️️ Graph map (optional):",
                    list_to_choose, key="key_add_om_graph_map_option")

                if add_om_graph_map_option == "Add graph map":

                    mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
                    if not mapping_ns_dict:
                        ns_needed_for_pom_flag = True
                    mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
                    list_to_choose = sorted(mapping_ns_dict.keys())
                    list_to_choose.insert(0,"Select namespace")
                    om_graph_prefix = st.selectbox("🖱️ Namespace(opt):", list_to_choose,
                        key="key_om_graph_prefix")
                    om_graph_input = st.text_input("⌨️ Enter graph map:*", key="key_om_graph_input")

                    if om_graph_input and om_graph_prefix != "Select namespace":
                        NS = Namespace(mapping_ns_dict[om_graph_prefix])
                        om_graph = NS[om_graph_input]
                    elif om_graph_input:
                        om_graph = om_graph_input
                    else:
                        om_graph = ""

        if tm_label_for_pom != "Select a TriplesMap":

            # POM MAP ______________________________________
            inner_html_error = ""
            inner_html_warning = ""
            pom_complete_flag = True

            if ns_needed_for_pom_flag:
                inner_html_error += f"""<small>· <b>No namespaces available.</b> Go to the
                    <b>Global Configuration</b> page to add them.</small><br>"""


            if not tm_label_for_pom in tm_w_sm_list:
                inner_html_warning += f"""<small>· TriplesMap <b>{tm_label_for_pom}</b> has no Subject Map.
                            It will be invalid without one.</small><br>"""

            if selected_p_label == "Select a predicate":
                pom_complete_flag = False
                inner_html_error += "<small>· You must select a <b>predicate</b>.</small><br>"

            elif selected_p_label == "🚫 Predicate outside ontology":
                if (not manual_p_label or manual_p_ns_prefix == "Select a namespace"):
                    pom_complete_flag = False
                    inner_html_error += "<small>· The <b>predicate</b> (and/or its namespace) has not been given.</small><br>"

                inner_html_warning += f"""<small>· Manual predicate input is <b>discouraged</b>.
                    Use an ontology for safer results.</small><br>"""

            # OBJECT MAP - TEMPLATE______________________________________________________-
            if om_generation_rule == "Template 📐":
                if not om_template:
                    pom_complete_flag = False
                    inner_html_error += "<small>· The <b>template</b> is empty.</small><br>"
                elif not st.session_state["om_template_variable_part_flag"]:
                    pom_complete_flag = False
                    inner_html_error += """<small>· The <b>template</b> must contain
                        at least one <b>variable part</b>..</small><br>"""

                if om_template and om_term_type == "🌐 IRI":
                    if not st.session_state["template_om_is_iri_flag"]:
                        inner_html_warning += """<small>· Term type is <b>🌐 IRI</b>.
                            We recommend <b>adding a namespace to the template</b>.<br>"""

                if om_template and om_term_type == "📘 Literal":
                    if om_datatype == "Natural language tag" and om_language_tag == "Select language tag":
                        om_complete_flag = False
                        inner_html_error += "<small>· You must select a <b>🌐 language tag</b>.</small><br>"

            # OBJECT MAP - CONSTANT____________________________________________
            if om_generation_rule == "Constant 🔒":
                if not om_constant:
                    pom_complete_flag = False
                    inner_html_error += "<small>· You must enter a <b>constant</b>.</small><br>"

                if om_term_type == "📘 Literal":
                    if om_datatype == "Natural language tag" and om_language_tag == "Select language tag":
                        pom_complete_flag = False
                        inner_html_error += "<small>· You must select a <b>🌐 language tag</b>.</small><br>"

                elif om_term_type == "🌐 IRI":
                    if om_constant and om_constant_ns_prefix == "Select a namespace":
                        inner_html_warning += """<small>· Term type is <b>🌐 IRI</b>.
                            We recommend <b>adding a namespace</b> to the constant.</small><br>"""


            # OBJECT MAP - REFERENCE___________________________
            if om_generation_rule == "Reference 📊":

                if column_list:
                    if om_column_name == "Select reference":
                        pom_complete_flag = False
                        inner_html_error += "<small>· You must select a <b>reference</b>.</small><br>"
                else:
                    if not om_column_name:
                        pom_complete_flag = False
                        inner_html_error += "<small>· You must enter a <b>reference</b>.</small><br>"

                if om_term_type == "📘 Literal":
                    if om_datatype == "Natural language tag" and om_language_tag == "Select language tag":
                        pom_complete_flag = False
                        inner_html_error += "<small>· You must select a <b>🌐 language tag</b>.</small><br>"

                elif om_term_type == "🌐 IRI":
                    inner_html_warning += """<small>· Term type is <b>🌐 IRI</b>.
                                Make sure that the values in the referenced column
                                are valid IRIs.</small><br>"""


            # GRAPH MAP
            if add_om_graph_map_option == "Add Graph Map":
                if om_graph_prefix == "Select a namespace" or not om_graph_input:
                    pom_complete_flag = False
                    inner_html_error += """<small>· The <b>Graph Map</b> (and/or its namespace)
                        has not been given.</small><br>"""

            # INFO AND SAVE BUTTON____________________________________
            with col2b:

                if inner_html_warning:
                    st.markdown(f"""<div class="warning-message" style="font-size:13px; line-height:1.2;">
                        ⚠️ <b>Caution.</b><br>
                        <div style='margin-left: 1.5em;'>{inner_html_warning}</div>
                    </div>""", unsafe_allow_html=True)

                if inner_html_error:
                    st.markdown(f"""<div class="error-message" style="font-size:13px; line-height:1.2;">
                            ❌ <b>Predicate-Object Map is incomplete.</b><br>
                        <div style='margin-left: 1.5em;'>{inner_html_error}</div>
                        </div>""", unsafe_allow_html=True)

                if pom_complete_flag:
                    st.markdown(f"""<div class="success-message">
                        ✔️ All <b>required fields (*)</b> are complete.
                        <small>Double-check the information before saving.</smalL> </div>
                    """, unsafe_allow_html=True)


            if pom_complete_flag:

                # Prepare subject for display
                sm_iri_for_pom = next(st.session_state["g_mapping"].objects(tm_iri_for_pom, RML.subjectMap), None)

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
                        sm_rule_ns = URIRef(split_uri(sm_rule)[0])
                        sm_rule_prefix = st.session_state["g_mapping"].namespace_manager.store.prefix(sm_rule_ns)
                        if sm_rule_prefix:
                            sm_rule = f"{sm_rule_prefix}: {split_uri(sm_rule)[1]}"

                else:
                    sm_rule = """No Subject Map"""

                # Prepare predicate for display
                selected_p_ns = URIRef(split_uri(selected_p_iri)[0])
                selected_p_prefix = st.session_state["g_mapping"].namespace_manager.store.prefix(selected_p_ns)
                if selected_p_prefix:
                    selected_p_for_display = f"{selected_p_prefix}: {split_uri(selected_p_iri)[1]}"
                else:
                    selected_p_for_display = selected_p_iri

                # Prepare object for display
                if om_generation_rule == "Template 📐":
                    om_iri_for_display = Literal(om_template)

                elif om_generation_rule == "Constant 🔒":
                    if om_term_type == "🌐 IRI":
                        om_constant_ns = mapping_ns_dict[om_constant_ns_prefix]
                        NS = Namespace(om_constant_ns)
                        om_iri_for_display = NS[om_constant]
                    elif om_term_type == "📘 Literal":
                        om_iri_for_display = Literal(om_constant)

                elif om_generation_rule == "Reference 📊":
                    om_iri_for_display = Literal(om_column_name)

                om_iri_for_display = utils.format_iri_to_prefix_label(om_iri_for_display)



                with col1:
                    col1a, col1b = st.columns([6,1])
                with col1b:
                    st.markdown("""
                    <div style="font-size:13px; font-weight:500; margin-top:10px; margin-bottom:6px; border-top:0.5px solid #ccc; padding-bottom:4px;">
                        <b>💾 Save</b><br>
                    </div>""", unsafe_allow_html=True)
                    st.session_state["pom_iri_to_create"] = pom_iri    # otherwise it will change value in the on_click function
                    st.session_state["tm_iri_for_pom"] = tm_iri_for_pom
                    if om_generation_rule == "Template 📐":
                        save_pom_template_button = st.button("Save", on_click=save_pom_template, key="key_save_pom_template_button")
                    elif om_generation_rule == "Constant 🔒":
                        save_pom_constant_button = st.button("Save", on_click=save_pom_constant, key="key_save_pom_constant_button")
                    elif om_generation_rule == "Reference 📊":
                        save_pom_reference_button = st.button("Save", on_click=save_pom_reference, key="key_save_pom_reference_button")

                with col1a:
                    st.markdown("""
                    <div style="font-size:13px; font-weight:500; margin-top:10px; margin-bottom:6px; border-top:0.5px solid #ccc; padding-bottom:4px;">
                        <b>🔍 Preview</b><br>
                    </div>""", unsafe_allow_html=True)
                    utils.preview_rule(sm_rule, selected_p_for_display, om_iri_for_display)  # display rule

    with col2b:
        st.markdown("""<div class='info-message-gray'>
                To consult the added Predicate-Object Maps go to the <b>🔎 Explore Mapping</b> page.
            </div>""", unsafe_allow_html=True)



#________________________________________________
# MANAGE MAPPING
with tab4:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])

    tm_dict = utils.get_tm_dict()
    # SUCCESS MESSAGE - TriplesMap removed
    if not tm_dict and st.session_state["tm_deleted_ok_flag"]:  # show message here if "Remove" purple heading is not going to be shown
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:1em;
            border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                ✅ The <b>Triplesmap/s</b> have been removed.
            </div>""", unsafe_allow_html=True)
            st.write("")
        st.session_state["tm_deleted_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    # PURPLE HEADING - REMOVE MAP
    if not tm_dict:     # only show option if there are tm/sm/pom that can be removed
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.markdown(f"""<div class="error-message">
                    ❌ No TriplesMaps in mapping <b>{st.session_state["g_label"]}</b>.
                    <small>You can add new TriplesMaps in the <b>Add TriplesMap</b> panel.</small>
                </div>""", unsafe_allow_html=True)
    else:
        with col1:
            st.markdown("""<div class="purple-heading">
                    🗑️ Remove Map
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["tm_deleted_ok_flag"]:  # show message here if "Remove" purple heading is going to be shown
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ The <b>Triplesmap/s</b> have been removed.
                </div>""", unsafe_allow_html=True)
                st.write("")
            st.session_state["tm_deleted_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        if st.session_state["sm_unassigned_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>Subject Map/s</b> have been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["sm_unassigned_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        if st.session_state["pom_deleted_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>Predicate-Object Map/s</b> have been deleted!
                </div>""", unsafe_allow_html=True)
                st.write("")
            st.session_state["pom_deleted_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        tm_dict = utils.get_tm_dict()
        sm_dict = utils.get_sm_dict()
        sm_list = list(st.session_state["g_mapping"].objects(predicate=RML.subjectMap))
        pom_dict = utils.get_pom_dict()

        if not tm_dict:
            st.markdown(f"""<div class="error-message">
                ❌ Mapping {st.session_state["g_label"]} has no <b>TriplesMaps</b>.
                <small>You can add them in the <b>Add TriplesMap panel</b></small>.
            </div>""", unsafe_allow_html=True)

        with col1:
            col1a, col1b = st.columns([1.5,1])


        with col1b:
            list_to_choose = ["🗺️ TriplesMap"]
            if sm_dict:
                list_to_choose.append("🏷️ Subject Map")
            if pom_dict:
                list_to_choose.append("🔗 Predicate-Object Map")
            st.write("")
            map_type_to_remove = st.radio("🖱️ Select an option:*", list_to_choose,
                label_visibility="collapsed", key="key_map_type_to_remove")

        if map_type_to_remove == "🗺️ TriplesMap":
            tm_list = list(tm_dict)
            if len(tm_list) > 1:
                tm_list.append("Select all")

            with col1a:
                tm_to_remove_list = st.multiselect("🖱️ Select TriplesMaps:*", reversed(tm_list), key="key_tm_to_remove_list")


            if "Select all" not in tm_to_remove_list:
                sm_dict = utils.get_sm_dict()
                inner_html = ""
                max_length = 8
                if len(tm_to_remove_list) < max_length:
                    for tm in tm_to_remove_list:
                        inner_html += f"""<b>🔖 {tm}</b> ("""
                        tm_iri = tm_dict[tm]
                        sm_to_remove_tm = next((o for o in st.session_state["g_mapping"].objects(tm_iri, RML.subjectMap)), None)
                        if sm_to_remove_tm:
                            inner_html += f"""<span style="font-size:0.85em;">Subject Map: {sm_dict[sm_to_remove_tm][0]} | </span>"""
                        else:
                            inner_html += f"""<span style="font-size:0.85em;">No Subject Map | </span>"""
                        pom_to_remove_tm_list = list(st.session_state["g_mapping"].objects(tm_iri, RML.predicateObjectMap))
                        if len(pom_to_remove_tm_list) == 1:
                            inner_html += f"""<span style="font-size:0.85em;">{len(pom_to_remove_tm_list)} Predicate-Object Map)<br></span>"""
                        elif pom_to_remove_tm_list:
                            inner_html += f"""<span style="font-size:0.85em;">{len(pom_to_remove_tm_list)} Predicate-Object Maps)<br></span>"""
                        else:
                            inner_html += f"""<span style="font-size:0.85em;">No Predicate-Object Maps)<br></span>"""
                else:
                    for tm in tm_to_remove_list[:max_length]:
                        inner_html += f"""🔖 <b>{tm}</b> ("""
                        tm_iri = tm_dict[tm]
                        sm_to_remove_tm = next((o for o in st.session_state["g_mapping"].objects(tm_iri, RML.subjectMap)), None)
                        if sm_to_remove_tm:
                            inner_html += f"""<span style="font-size:0.85em;">Subject Map: {sm_dict[sm_to_remove_tm][0]} | </span>"""
                        else:
                            inner_html += f"""<span style="font-size:0.85em;">No Subject Map | </span>"""
                        pom_to_remove_tm_list = list(st.session_state["g_mapping"].objects(tm_iri, RML.predicateObjectMap))
                        if len(pom_to_remove_tm_list) == 1:
                            inner_html += f"""<span style="font-size:0.85em;">{len(pom_to_remove_tm_list)} Predicate-Object Map)<br></span>"""
                        elif pom_to_remove_tm_list:
                            inner_html += f"""<span style="font-size:0.85em;">{len(pom_to_remove_tm_list)} Predicate-Object Maps)<br></span>"""
                        else:
                            inner_html += f"""<span style="font-size:0.85em;">No Predicate-Object Maps)<br></span>"""
                    inner_html += f"""🔖 ..."""


            else:   #Select all option
                sm_dict = utils.get_sm_dict()
                inner_html = ""
                max_length = utils.get_max_length_for_display()[4]
                if len(tm_dict) < max_length:
                    for tm in tm_dict:
                        inner_html += f"""<b>🔖 {tm}</b> ("""
                        tm_iri = tm_dict[tm]
                        sm_to_remove_tm = next((o for o in st.session_state["g_mapping"].objects(tm_iri, RML.subjectMap)), None)
                        if sm_to_remove_tm:
                            inner_html += f"""<span style="font-size:0.85em;">Subject Map: {sm_dict[sm_to_remove_tm][0]} | </span>"""
                        else:
                            inner_html += f"""<span style="font-size:0.85em;">No Subject Map | </span>"""
                        pom_to_remove_tm_list = list(st.session_state["g_mapping"].objects(tm_iri, RML.predicateObjectMap))
                        if len(pom_to_remove_tm_list) == 1:
                            inner_html += f"""<span style="font-size:0.85em;">{len(pom_to_remove_tm_list)} Predicate-Object Map)<br></span>"""
                        elif pom_to_remove_tm_list:
                            inner_html += f"""<span style="font-size:0.85em;">{len(pom_to_remove_tm_list)} Predicate-Object Maps)<br></span>"""
                        else:
                            inner_html += f"""<span style="font-size:0.85em;">No Predicate-Object Maps)<br></span>"""
                else:
                    for tm in list(tm_dict)[:max_length]:
                        inner_html += f"""🔖 <b>{tm}</b> ("""
                        tm_iri = tm_dict[tm]
                        sm_to_remove_tm = next((o for o in st.session_state["g_mapping"].objects(tm_iri, RML.subjectMap)), None)
                        if sm_to_remove_tm:
                            inner_html += f"""<span style="font-size:0.85em;">Subject Map: {sm_dict[sm_to_remove_tm][0]} | </span>"""
                        else:
                            inner_html += f"""<span style="font-size:0.85em;">No Subject Map | </span>"""
                        pom_to_remove_tm_list = list(st.session_state["g_mapping"].objects(tm_iri, RML.predicateObjectMap))
                        if len(pom_to_remove_tm_list) == 1:
                            inner_html += f"""<span style="font-size:0.85em;">{len(pom_to_remove_tm_list)} Predicate-Object Map)<br></span>"""
                        elif pom_to_remove_tm_list:
                            inner_html += f"""<span style="font-size:0.85em;">{len(pom_to_remove_tm_list)} Predicate-Object Maps)<br></span>"""
                        else:
                            inner_html += f"""<span style="font-size:0.85em;">No Predicate-Object Maps)<br></span>"""
                    inner_html += f"""🔖 ..."""

            if tm_to_remove_list:
                if "Select all" not in tm_to_remove_list:
                    with col1a:
                        delete_tm_checkbox = st.checkbox(
                        "🔒 I am sure I want to delete the TriplesMap/s",
                        key="delete_tm_checkbox")
                    if delete_tm_checkbox:
                        with col1a:
                            st.button("Delete", on_click=delete_tm)
                else:   #if "Select all" selected
                    with col1b:
                        st.markdown(f"""<div class="warning-message">
                                ⚠️ If you continue, <b>all TriplesMaps will be deleted</b>.
                                <small>Make sure you want to go ahead.</small>
                            </div>""", unsafe_allow_html=True)
                        st.write("")
                    with col1a:
                        delete_tm_checkbox = st.checkbox(
                        "🔒 I am sure I want to delete all TriplesMaps",
                        key="delete_tm_checkbox")
                    if delete_tm_checkbox:
                        with col1a:
                            st.button("Delete", on_click=delete_all_tm)

                if inner_html:
                    with col1:
                        st.markdown(f"""<div class="info-message-gray">
                                {inner_html}
                            <div>""", unsafe_allow_html=True)
                        st.write("")


        if map_type_to_remove == "🏷️ Subject Map":
            tm_w_sm_list = []
            for tm_label, tm_iri in tm_dict.items():
                if any(st.session_state["g_mapping"].triples((tm_iri, RML.subjectMap, None))):
                    tm_w_sm_list.append(tm_label)

            with col1a:
                tm_w_sm_list_to_choose = list(reversed(tm_w_sm_list))
                if len(tm_w_sm_list_to_choose) > 1:
                    tm_w_sm_list_to_choose.insert(0, "Select all")
                tm_to_unassign_sm_list_input = st.multiselect("🖱️ Select TriplesMaps:*", tm_w_sm_list_to_choose,
                    key="key_tm_to_unassign_sm")

                if "Select all" in tm_to_unassign_sm_list_input:
                    tm_to_unassign_sm_list = tm_w_sm_list
                else:
                    tm_to_unassign_sm_list = tm_to_unassign_sm_list_input


            # create a single info message
            max_length = utils.get_max_length_for_display()[4]
            inner_html = f"""<div style="margin-bottom:1px;">
                    <small><b>TriplesMap</b> → <b>Subject Map</b></small>
                </div>"""

            for tm in tm_to_unassign_sm_list[:max_length]:
                tm_iri = tm_dict[tm]
                sm_iri = st.session_state["g_mapping"].value(subject=tm_iri, predicate=RML.subjectMap)
                sm_label_to_unassign = sm_dict[sm_iri][0]
                inner_html += f"""<div style="margin-bottom:1px;">
                    <small>🔖 {tm} →  <b>{sm_label_to_unassign}</b></small>
                </div>"""

            if len(tm_to_unassign_sm_list) > max_length:   # many sm to remove
                inner_html += f"""<div style="margin-bottom:1px;">
                    <small>🔖 ... (+{len(tm_to_unassign_sm_list[:max_length])})</small>
                </div>"""


            sm_to_completely_remove_list = []
            sm_to_just_unassign_list = []
            for tm in tm_to_unassign_sm_list:
                tm_iri = tm_dict[tm]
                sm_iri = st.session_state["g_mapping"].value(subject=tm_iri, predicate=RML.subjectMap)
                sm_label_to_unassign = sm_dict[sm_iri][0]
                other_tm_with_sm = [split_uri(s)[1] for s, p, o in st.session_state["g_mapping"].triples((None, RML.subjectMap, sm_iri)) if s != tm_iri]
                if all(tm in tm_to_unassign_sm_list for tm in other_tm_with_sm):   # if upon deletion sm is no longer assigned to any tm
                    if sm_label_to_unassign not in sm_to_completely_remove_list:
                        sm_to_completely_remove_list.append(sm_label_to_unassign)
                else:
                    sm_to_just_unassign_list.append(sm_label_to_unassign)


            if "Select all" in tm_to_unassign_sm_list_input:
                with col1b:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ You are deleting <b>all Subject Maps</b>.
                            <small>Make sure you want to go ahead.</small>
                        </div>""", unsafe_allow_html=True)
                with col1:
                    unassign_all_sm_checkbox = st.checkbox(
                    "🔒 I am sure I want to remove all Subject Map/s",
                    key="key_unassign_all_sm_checkbox")
                if unassign_all_sm_checkbox:
                    st.session_state["sm_to_completely_remove_list"] = sm_to_completely_remove_list
                    st.session_state["tm_to_unassign_sm_list"] = tm_to_unassign_sm_list
                    with col1:
                        st.button("Remove", on_click=unassign_sm, key="key_unassign_sm_button")

            elif tm_to_unassign_sm_list:
                with col1:
                    unassign_sm_checkbox = st.checkbox(
                    "🔒 I am sure I want to remove the selected Subject Map/s",
                    key="key_unassign_sm_checkbox")
                if unassign_sm_checkbox:
                    st.session_state["sm_to_completely_remove_list"] = sm_to_completely_remove_list
                    st.session_state["tm_to_unassign_sm_list"] = tm_to_unassign_sm_list
                    with col1:
                        st.button("Remove", on_click=unassign_sm, key="key_unassign_sm_button")

            if tm_to_unassign_sm_list:
                with col1:
                    st.markdown(f"""<div class="info-message-gray">
                            {inner_html}
                        </div>""", unsafe_allow_html=True)


        if map_type_to_remove == "🔗 Predicate-Object Map":

            tm_w_pom_list = []
            for tm_iri in tm_dict:
                for pom_iri in pom_dict:
                    if tm_iri in pom_dict[pom_iri] and tm_iri not in tm_w_pom_list:
                        tm_w_pom_list.append(tm_iri)
                        continue

            with col1a:
                list_to_choose = list(reversed(tm_w_pom_list))
                list_to_choose.insert(0, "Select a TriplesMap")
                tm_to_delete_pom_label = st.selectbox("🖱️ Select a TriplesMap:*", list_to_choose, key="key_tm_to_delete_pom")

            if tm_to_delete_pom_label != "Select a TriplesMap":
                tm_to_delete_pom_iri = tm_dict[tm_to_delete_pom_label]
                pom_of_selected_tm_list = []
                for pom_iri in pom_dict:
                    if pom_dict[pom_iri][0] == tm_to_delete_pom_iri:
                        pom_of_selected_tm_list.append(pom_iri)

                if pom_of_selected_tm_list:

                    with col1a:
                        list_to_choose = []
                        for pom_iri in pom_dict:
                            if pom_dict[pom_iri][0] == tm_to_delete_pom_iri:
                                list_to_choose.append(pom_iri)
                        list_to_choose = sorted(list_to_choose)
                        if len(list_to_choose) > 1:
                            list_to_choose.insert(0, "Select all")
                        pom_to_delete_iri_list = st.multiselect("🖱️ Select a Predicate-Object Map:*", list_to_choose, key="key_pom_to_delete")


                        if "Select all" in pom_to_delete_iri_list:
                            pom_to_delete_iri_list = []
                            for pom_iri in pom_dict:
                                if pom_dict[pom_iri][0] == tm_to_delete_pom_iri:
                                    pom_to_delete_iri_list.append(pom_iri)

                    if pom_to_delete_iri_list and "Select all" not in pom_to_delete_iri_list:
                        with col1:
                            delete_pom_checkbox = st.checkbox(
                            f"""🔒 I am  sure I want to remove the selected Predicate-Object Map/s""",
                            key="key_overwrite_g_mapping_checkbox_new")
                            if delete_pom_checkbox:
                                st.button("Delete", on_click=delete_pom, key="key_delete_pom_button")

                    elif pom_to_delete_iri_list and "Select all" in pom_to_delete_iri_list:
                        with col1:
                            col1a, col1b = st.columns([1,1])
                        with col1b:
                            st.markdown(f"""<div class="warning-message">
                                    ⚠️ You are deleting <b>all Predicate-Object Maps</b>
                                    of the TriplesMap {tm_to_delete_pom_label}.
                                    <small>Make sure you want to go ahead.</small>
                                </div>""", unsafe_allow_html=True)
                            st.write("")
                        with col1a:
                            delete_all_pom_checkbox = st.checkbox(
                            f"""🔒 I am  sure I want to remove all Predicate-Object Maps""",
                            key="key_overwrite_g_mapping_checkbox_new")
                            if delete_all_pom_checkbox:
                                st.button("Delete", on_click=delete_pom, key="key_delete_all_pom_button")


            if tm_to_delete_pom_label != "Select a TriplesMap":


                rows = [{"P-O Map": pom_dict[pom_iri][2],
                        "Predicate": pom_dict[pom_iri][4], "Object Map": pom_dict[pom_iri][5],
                        "Rule": pom_dict[pom_iri][6], "ID/Constant": pom_dict[pom_iri][8]}
                        for pom_iri in pom_of_selected_tm_list]
                pom_of_selected_tm_df = pd.DataFrame(rows)


                st.write("")
                if pom_of_selected_tm_list:
                    with col1:
                        st.write("")
                        st.markdown(f"""<div style='font-size: 14px; color: grey;'>
                                🔎 Predicate-Object Maps of TriplesMap {tm_to_delete_pom_label}
                            </div>""", unsafe_allow_html=True)
                        st.dataframe(pom_of_selected_tm_df, hide_index=True)
                        st.write("")

    #PURPLE HEADING - CLEAN MAPPING
    if st.session_state["g_mapping_cleaned_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The mapping <b>{st.session_state["g_label"]}</b> has been cleaned.
            </div>""", unsafe_allow_html=True)
        st.session_state["g_mapping_cleaned_ok_flag"]  = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    check_g_mapping = utils.check_g_mapping(st.session_state["g_mapping"])
    if check_g_mapping:

        with col1:
            st.write("_________")
            st.markdown("""<div class="purple-heading">
                    🧹 Clean Mapping
                </div>""", unsafe_allow_html=True)

        with col1:
            col1a, col1b = st.columns([2,1])


        tm_dict = {}
        for tm in st.session_state["g_mapping"].subjects(RML.logicalSource, None):
            tm_label = split_uri(tm)[1]
            tm_dict[tm_label] = tm

        pom_dict = {}
        for pom in st.session_state["g_mapping"].subjects(RDF.type, RML.PredicateObjectMap):
            if isinstance(pom, URIRef):
                pom_label = split_uri(tm)[1]
            elif isinstance(pom, BNode):
                pom_label = "_:" + str(pom)[:7] + "..."
            else:
                pom_label = str(pom)
            pom_dict[pom_label] = pom

        tm_wo_sm_list = []   # list of all tm with assigned sm
        tm_wo_pom_list = []
        for tm_label, tm_iri in tm_dict.items():
            if not any(st.session_state["g_mapping"].triples((tm_iri, RML.subjectMap, None))):
                tm_wo_sm_list.append(tm_label)
        for tm_label, tm_iri in tm_dict.items():
            if not any(st.session_state["g_mapping"].triples((tm_iri, RML.predicateObjectMap, None))):
                tm_wo_pom_list.append(tm_label)

        pom_wo_om_list = []
        pom_wo_predicate_list = []
        for pom_iri in st.session_state["g_mapping"].subjects(RDF.type, RML.PredicateObjectMap):
            pom_label = utils.get_node_label(pom_iri)
            if not any(st.session_state["g_mapping"].triples((pom_iri, RML.objectMap, None))):
                pom_wo_om_list.append(pom_label)
            if not any(st.session_state["g_mapping"].triples((pom_iri, RML.predicate, None))):
                pom_wo_predicate_list.append(pom_label)

        tm_to_clean_list = list(set(tm_wo_sm_list).union(tm_wo_pom_list))
        pom_to_clean_list = list(set(pom_wo_om_list).union(pom_wo_predicate_list))

        with col1:
            col1a, col1b = st.columns([1.5,1])
        with col1a:
            clean_g_mapping_checkbox = st.checkbox(
            f"""🔒 I am sure I want to clean mapping {st.session_state["g_label"]}""",
            key="key_clean_g_mapping_checkbox")
        if clean_g_mapping_checkbox:
            with col1a:
                st.button("Clean", key="key_clean_g_mapping_button", on_click=clean_g_mapping)

            max_length = utils.get_max_length_for_display()[5]
            inner_html = "⚠️" + check_g_mapping
            with col1b:
                st.markdown(f"""<div class="warning-message">
                        {inner_html}
                    </div>""", unsafe_allow_html=True)

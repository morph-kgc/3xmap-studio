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

# Header
st.markdown("""
<div style="display:flex; align-items:center; background-color:#f0f0f0; padding:12px 18px;
            border-radius:8px; margin-bottom:16px;">
    <span style="font-size:1.7rem; margin-right:18px;">🏗️</span>
    <div>
        <h3 style="margin:0; font-size:1.75rem;">
            <span style="color:#511D66; font-weight:bold; margin-right:12px;">◽◽◽◽◽</span>
            Build mapping
            <span style="color:#511D66; font-weight:bold; margin-left:12px;">◽◽◽◽◽</span>
        </h3>
        <p style="margin:0; font-size:0.95rem; color:#555;">
            Build your mapping by adding <b>Triple Maps</b>, <b>Subject Maps</b>, and <b>Predicate-Object Maps</b>.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)


#____________________________________________
#PRELIMINARY

# Import style
utils.import_st_aesthetics()
st.write("")

# Namespaces
RML, RR, QL = utils.get_required_ns().values()


# Initialise session state variables
#TAB1
if "key_ds_uploader" not in st.session_state:
    st.session_state["key_ds_uploader"] = str(uuid.uuid4())
if "last_added_tm_list" not in st.session_state:
    st.session_state["last_added_tm_list"] = []
if "tm_label" not in st.session_state:
    st.session_state["tm_label"] = ""
if "tm_saved_ok_flag" not in st.session_state:
    st.session_state["tm_saved_ok_flag"] = False
if "tm_deleted_ok_flag" not in st.session_state:
    st.session_state["tm_deleted_ok_flag"] = False
if "removed_tm_list" not in st.session_state:
    st.session_state["removed_tm_list"] = []

#TAB2
if "key_ds_uploader_for_sm" not in st.session_state:
    st.session_state["key_ds_uploader_for_sm"] = str(uuid.uuid4())
if "last_added_sm_list" not in st.session_state:
    st.session_state["last_added_sm_list"] = []
if "sm_label" not in st.session_state:
    st.session_state["sm_label"] = ""
if "tm_label_for_sm" not in st.session_state:
    st.session_state["tm_label_for_sm"] = False
if "sm_template_list" not in st.session_state:
    st.session_state["sm_template_list"] = []
if "sm_saved_ok_flag" not in st.session_state:
    st.session_state["sm_saved_ok_flag"] = False
if "sm_iri" not in st.session_state:
    st.session_state["sm_iri"] = None
if "labelled_sm_deleted_ok_flag" not in st.session_state:
    st.session_state["labelled_sm_deleted_ok_flag"] = False
if "sm_unassigned_ok_flag" not in st.session_state:
    st.session_state["sm_unassigned_ok_flag"] = False
if "sm_template_prefix" not in st.session_state:
    st.session_state["sm_template_prefix"] = ""

#TAB3
if "key_ds_uploader_for_pom" not in st.session_state:
    st.session_state["key_ds_uploader_for_pom"] = str(uuid.uuid4())
if "om_template_ns_prefix" not in st.session_state:
    st.session_state["om_template_ns_prefix"] = ""
if "template_om_is_iri_flag" not in st.session_state:
    st.session_state["template_om_is_iri_flag"] = False
if "pom_saved_ok_flag" not in st.session_state:
    st.session_state["pom_saved_ok_flag"] = False
if "om_template_list" not in st.session_state:
    st.session_state["om_template_list"] = []
if "last_added_pom_list" not in st.session_state:
    st.session_state["last_added_pom_list"] = []
if "pom_deleted_ok_flag" not in st.session_state:
    st.session_state["pom_deleted_ok_flag"] = False


#define on_click functions
# TAB1
def save_tm_w_existing_ls():
    # add triples___________________
    NS = st.session_state["structural_ns_dict"]["TriplesMap"][1]
    tm_iri = NS[f"{st.session_state["tm_label"]}"]  # change so that is can be defined by user
    NS = st.session_state["structural_ns_dict"]["Logical Source"][1]
    ls_iri =  NS[f"{existing_ls}"]   # idem ns
    st.session_state["g_mapping"].add((tm_iri, RML.logicalSource, ls_iri))    #bind to logical source
    st.session_state["g_mapping"].add((tm_iri, RDF.type, RR.TriplesMap))
    # store information________________
    st.session_state["tm_saved_ok_flag"] = True  # for success message
    st.session_state["last_added_tm_list"].insert(0, st.session_state["tm_label"])    # to display last added tm
    # reset fields_____________________
    st.session_state["key_tm_label_input"] = ""

def save_tm_w_non_relational_ls():
    # add triples__________________
    NS = st.session_state["structural_ns_dict"]["TriplesMap"][1]
    tm_iri = NS[f"{st.session_state["tm_label"]}"]
    ds_filename = ds_file.name
    if logical_source_label:
        NS = st.session_state["structural_ns_dict"]["Logical Source"][1]
        ls_iri = NS[f"{logical_source_label}"]
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
    st.session_state["g_mapping"].add((tm_iri, RDF.type, RR.TriplesMap))   #HEREIGO
    # store information____________________
    st.session_state["tm_saved_ok_flag"] = True  # for success message
    st.session_state["last_added_tm_list"].insert(0, st.session_state["tm_label"])    # to display last added tm
    # reset fields_______________________
    st.session_state["key_tm_label_input"] = ""
    st.session_state["key_ds_uploader"] = str(uuid.uuid4())

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
    NS = st.session_state["structural_ns_dict"]["TriplesMap"][1]
    tm_iri = NS[f"{st.session_state["tm_label"]}"]
    if logical_source_label:
        NS = st.session_state["structural_ns_dict"]["Logical Source"][1]
        ls_iri = NS[f"{logical_source_label}"]
    else:
        ls_iri = BNode()
    st.session_state["g_mapping"].add((tm_iri, RML.logicalSource, ls_iri))    #bind to logical source
    st.session_state["g_mapping"].add((ls_iri, RML.source, Literal(jdbc_str)))    #bind ls to source file
    st.session_state["g_mapping"].add((ls_iri, RML.referenceFormulation, QL.SQL))
    st.session_state["g_mapping"].add((ls_iri, RML.query, Literal(sql_query)))
    st.session_state["g_mapping"].add((tm_iri, RDF.type, RR.TriplesMap))
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
    NS = st.session_state["structural_ns_dict"]["TriplesMap"][1]
    tm_iri = NS[f"{st.session_state["tm_label"]}"]
    if logical_source_label:
        NS = st.session_state["structural_ns_dict"]["Logical Source"][1]
        ls_iri = NS[f"{logical_source_label}"]
    else:
        ls_iri = BNode()
    st.session_state["g_mapping"].add((tm_iri, RML.logicalSource, ls_iri))    #bind to logical source
    st.session_state["g_mapping"].add((ls_iri, RML.source, Literal(jdbc_str)))    #bind ls to source file
    st.session_state["g_mapping"].add((ls_iri, RML.referenceFormulation, QL.SQL))
    st.session_state["g_mapping"].add((ls_iri, RR.tableName, Literal(selected_table_for_ls)))
    st.session_state["g_mapping"].add((tm_iri, RDF.type, RR.TriplesMap))
    # store information____________________
    st.session_state["tm_saved_ok_flag"] = True  # for success message
    st.session_state["last_added_tm_list"].insert(0, st.session_state["tm_label"])    # to display last added tm
    # reset fields_______________________
    st.session_state["key_tm_label_input"] = ""




def delete_tm():   #function to delete a TriplesMap
    # remove triples and store information___________
    st.session_state["removed_tm_list"] = []   # save the tm that have been deleted for display
    for tm in tm_to_remove_list:
        st.session_state["removed_tm_list"].append(tm)
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
    # remove triples and store information___________
    st.session_state["removed_tm_list"] = []    # save the tm that have been deleted for display
    for tm in utils.get_tm_dict():
        st.session_state["removed_tm_list"].append(tm)
    # remove all triples
    st.session_state["g_mapping"] = Graph()
    #store information
    st.session_state["last_added_tm_list"] = []
    st.session_state["last_added_sm_list"] = []
    st.session_state["last_added_pom_list"] = []
    st.session_state["tm_deleted_ok_flag"] = True
    #reset fields_______________________
    st.session_state["key_tm_to_remove_list"] = []

# TAB2
def save_sm_existing():
    # add triples____________________
    st.session_state["g_mapping"].add((tm_iri_for_sm, RR.subjectMap, st.session_state["sm_iri"]))
    # store information__________________
    st.session_state["last_added_sm_list"].insert(0, [st.session_state["sm_iri"], tm_label_for_sm])
    st.session_state["sm_saved_ok_flag"] = True

def add_ns_to_sm_template():
    # update template and store information_________
    if not st.session_state["sm_template_prefix"]:    # no ns added yet
        st.session_state["sm_template_list"].insert(0, sm_template_ns)
    else:   # a ns was added (replace)
        st.session_state["sm_template_list"][0] = sm_template_ns
    # reset fields_____________
    st.session_state["sm_template_prefix"] = sm_template_ns_prefix if sm_template_ns_prefix else utils.get_mapping_ns_dict()[sm_template_ns_prefix]
    st.session_state["key_sm_template_ns_prefix"] = "Select a namespace"
    st.session_state["key_build_template_action_sm"] = "📈 Add variable part"

def save_sm_template_fixed_part():
    # update template_____________
    st.session_state["sm_template_list"].append(sm_template_fixed_part)
    # reset fields_____________
    st.session_state["key_build_template_action_sm"] = "📈 Add variable part"

def save_sm_template_variable_part():
    # update template_____________
    st.session_state["sm_template_list"].append("{" + sm_template_variable_part + "}")
    # reset fields_____________
    st.session_state["key_build_template_action_sm"] = "🔒 Add fixed part"

def reset_sm_template():
    # reset template
    st.session_state["sm_template_list"] = []
    # store information____________________
    st.session_state["sm_template_prefix"] = ""
    st.session_state["template_sm_is_iri_flag"] = False
    # reset fields_____________
    st.session_state["key_build_template_action_sm"] = "🔒 Add fixed part"

def save_sm_template():   #function to save subject map (template option)
    # add triples____________________
    if not sm_label:
        sm_iri = BNode()
        st.session_state["sm_label"] = "_:" + str(sm_iri)[:7] + "..."   # to be displayed
    else:
        NS = st.session_state["structural_ns_dict"]["Subject Map"][1]
        sm_iri = NS[sm_label]
    st.session_state["g_mapping"].add((tm_iri_for_sm, RR.subjectMap, sm_iri))
    st.session_state["g_mapping"].add((sm_iri, RDF.type, RR.SubjectMap))
    st.session_state["g_mapping"].add((sm_iri, RR.template, Literal(sm_template)))
    if sm_term_type_template == "🌐 IRI":
        st.session_state["g_mapping"].add((sm_iri, RR.termType, RR.IRI))
    elif sm_term_type_template == "👻 BNode":
        st.session_state["g_mapping"].add((sm_iri, RR.termType, RR.BlankNode))
    # store information__________________
    st.session_state["last_added_sm_list"].insert(0, [sm_iri, tm_label_for_sm])
    st.session_state["sm_saved_ok_flag"] = True
    # reset fields____________________
    st.session_state["sm_template_list"] = []
    st.session_state["sm_template_prefix"] = ""
    st.session_state["key_tm_label_input_for_sm"] = "Select a TriplesMap"

def save_sm_constant():   #function to save subject map (constant option)
    # add triples________________________
    if not sm_label:
        sm_iri = BNode()
        st.session_state["sm_label"] = "_:" + str(sm_iri)[:7] + "..."   # to be displayed
    else:
        NS = st.session_state["structural_ns_dict"]["Subject Map"][1]
        sm_iri = NS[sm_label]
    st.session_state["g_mapping"].add((tm_iri_for_sm, RR.subjectMap, sm_iri))
    st.session_state["g_mapping"].add((sm_iri, RDF.type, RR.SubjectMap))
    sm_constant_ns = mapping_ns_dict[sm_constant_ns_prefix]
    NS = Namespace(sm_constant_ns)
    sm_constant_iri = NS[sm_constant]
    st.session_state["g_mapping"].add((sm_iri, RR.constant, sm_constant_iri))
    st.session_state["g_mapping"].add((sm_iri, RR.termType, RR.IRI))
    # store information____________________
    st.session_state["last_added_sm_list"].insert(0, [sm_iri, tm_label_for_sm])
    st.session_state["sm_saved_ok_flag"] = True
    # reset fields_________________________
    st.session_state["sm_template_list"] = []   # in case it is not empty
    st.session_state["key_tm_label_input_for_sm"] = "Select a TriplesMap"

def save_sm_reference():   #function to save subject map (reference option)
    # add triples____________________
    if not sm_label:
        sm_iri = BNode()
        st.session_state["sm_label"] = "_:" + str(sm_iri)[:7] + "..."   # to be displayed
    else:
        NS = st.session_state["structural_ns_dict"]["Subject Map"][1]
        sm_iri = NS[sm_label]
    st.session_state["g_mapping"].add((tm_iri_for_sm, RR.subjectMap, sm_iri))
    st.session_state["g_mapping"].add((sm_iri, RDF.type, RR.SubjectMap))
    st.session_state["g_mapping"].add((sm_iri, RR.reference, Literal(sm_column_name)))    #HERE change to RR.column in R2RML
    if sm_term_type_reference == "🌐 IRI":
        st.session_state["g_mapping"].add((sm_iri, RR.termType, RR.IRI))
    elif sm_term_type_reference == "👻 BNode":
        st.session_state["g_mapping"].add((sm_iri, RR.termType, RR.BlankNode))
    # store information__________________
    st.session_state["last_added_sm_list"].insert(0, [sm_iri, tm_label_for_sm])
    st.session_state["sm_saved_ok_flag"] = True
    # reset fields____________________
    st.session_state["sm_template_list"] = []   # in case it is not empty
    st.session_state["key_tm_label_input_for_sm"] = "Select a TriplesMap"

def change_term_type_to_BNode():
    # add triples______________________
    st.session_state["g_mapping"].remove((sm_iri_for_config, RR["termType"], RR.IRI))
    st.session_state["g_mapping"].add((sm_iri_for_config, RR["termType"], RR.BlankNode))

def change_term_type_to_IRI():
    # add triples______________________
    st.session_state["g_mapping"].remove((sm_iri_for_config, RR["termType"], RR.BlankNode))
    st.session_state["g_mapping"].add((sm_iri_for_config, RR["termType"], RR.IRI))

def save_ontology_subject_class():
    # add triples______________________
    st.session_state["g_mapping"].add((sm_iri_for_config, RR["class"], subject_class))

def save_external_subject_class():
    # add triples______________________
    st.session_state["g_mapping"].add((sm_iri_for_config, RR["class"], subject_class))

def delete_subject_class():
    # remove triples______________________
    st.session_state["g_mapping"].remove((sm_iri_for_config, RR["class"], None))

def save_subject_graph():
    # add triples______________________
    st.session_state["g_mapping"].add((sm_iri_for_config, RR["graph"], subject_graph))

def delete_subject_graph():
    # remove triples______________________
    st.session_state["g_mapping"].remove((sm_iri_for_config, RR["graph"], None))

def delete_labelled_sm():   #function to delete a labelled Subject Map
    # remove triples______________________
    for sm in sm_to_remove_iri_list:
        st.session_state["g_mapping"].remove((sm, None, None))
        st.session_state["g_mapping"].remove((None, None, sm))
    # store information__________________
    st.session_state["labelled_sm_deleted_ok_flag"] = True
    st.session_state["last_added_sm_list"] = [pair for pair in st.session_state["last_added_sm_list"]
        if pair[0] not in sm_to_remove_iri_list]
    # reset fields__________________
    st.session_state["key_sm_to_remove_label"] = []

def unassign_sm():
    # remove triples______________________
    for tm in tm_to_unassign_sm_list:
        tm_iri = tm_dict[tm]
        sm_iri = st.session_state["g_mapping"].value(subject=tm_iri, predicate=RR.subjectMap)
        other_tm_with_sm = [split_uri(s)[1] for s, p, o in st.session_state["g_mapping"].triples((None, RR.subjectMap, sm)) if s != tm_iri]
        if len(other_tm_with_sm) != 0:       # just unassign sm from tm (don't remove)
            st.session_state["g_mapping"].remove((tm_iri, RR.subjectMap, None))
        else:       # completely remove sm
            st.session_state["g_mapping"].remove((sm_iri, None, None))
            st.session_state["g_mapping"].remove((None, None, sm_iri))
    # store information__________________
    st.session_state["sm_unassigned_ok_flag"] = True
    st.session_state["last_added_sm_list"] = [pair for pair in st.session_state["last_added_sm_list"]
        if pair[1] not in tm_to_unassign_sm_list]
    # reset fields__________________
    st.session_state["key_tm_to_unassign_sm"] = []

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
    st.session_state["key_build_template_action_om"] = "📈 Add variable part"

def save_om_template_fixed_part():
    # update template_____________
    st.session_state["om_template_list"].append(om_template_fixed_part)
    # reset fields_____________
    st.session_state["key_build_template_action_om"] = "📈 Add variable part"

def save_om_template_variable_part():
    # update template_____________
    st.session_state["om_template_list"].append("{" + om_template_variable_part + "}")
    # reset fields_____________
    st.session_state["key_build_template_action_om"] = "🔒 Add fixed part"

def reset_om_template():
    # reset template
    st.session_state["om_template_list"] = []
    # store information____________________
    st.session_state["om_template_ns_prefix"] = ""
    st.session_state["template_om_is_iri_flag"] = False
    # reset fields_____________
    st.session_state["key_build_template_action_om"] = "🔒 Add fixed part"

def save_pom_template():
    # add triples pom________________________
    st.session_state["g_mapping"].add((st.session_state["tm_iri_for_pom"], RR.predicateObjectMap, st.session_state["pom_iri_to_create"]))
    st.session_state["g_mapping"].add((st.session_state["pom_iri_to_create"], RR.predicate, selected_p_iri))
    st.session_state["g_mapping"].add((st.session_state["pom_iri_to_create"], RR.objectMap, om_iri))
    # add triples om________________________
    st.session_state["g_mapping"].add((om_iri, RDF.type, RR.ObjectMap))
    st.session_state["g_mapping"].add((om_iri, RR.template, Literal(om_template)))
    if om_term_type_template == "📘 Literal":
        st.session_state["g_mapping"].add((om_iri, RR.termType, RR.Literal))
        if om_datatype != "Select datatype" and om_datatype != "Natural language tag":
            datatype_dict = utils.get_datatypes_dict()
            st.session_state["g_mapping"].add((om_iri, RR.datatype, datatype_dict[om_datatype]))
        elif om_datatype == "Natural language tag":
            st.session_state["g_mapping"].add((om_iri, RR.language, om_language_tag))
    elif om_term_type_template == "🌐 IRI":
        st.session_state["g_mapping"].add((om_iri, RR.termType, RR.IRI))
    elif om_term_type_template == "👻 BNode":
        st.session_state["g_mapping"].add((om_iri, RR.termType, RR.BlankNode))
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
    st.session_state["om_term_type_template"] = "🌐 IRI"
    st.session_state["key_om_label"] = ""

def save_pom_constant():
    # add triples pom________________________
    st.session_state["g_mapping"].add((st.session_state["tm_iri_for_pom"], RR.predicateObjectMap, st.session_state["pom_iri_to_create"]))
    st.session_state["g_mapping"].add((st.session_state["pom_iri_to_create"], RR.predicate, selected_p_iri))
    st.session_state["g_mapping"].add((st.session_state["pom_iri_to_create"], RR.objectMap, om_iri))
    # add triples om________________________
    st.session_state["g_mapping"].add((om_iri, RDF.type, RR.ObjectMap))
    if om_term_type_constant == "🌐 IRI":
        om_constant_ns = mapping_ns_dict[om_constant_ns_prefix]
        NS = Namespace(om_constant_ns)
        om_constant_iri = NS[om_constant]
        st.session_state["g_mapping"].add((om_iri, RR.constant, om_constant_iri))
        st.session_state["g_mapping"].add((om_iri, RR.termType, RR.IRI))
    elif om_term_type_constant == "📘 Literal":
        st.session_state["g_mapping"].add((om_iri, RR.constant, Literal(om_constant)))
        st.session_state["g_mapping"].add((om_iri, RR.termType, RR.Literal))
        if om_datatype != "Select datatype" and om_datatype != "Natural language tag":
            datatype_dict = utils.get_datatypes_dict()
            st.session_state["g_mapping"].add((om_iri, RR.datatype, datatype_dict[om_datatype]))
        elif om_datatype == "Natural language tag":
            st.session_state["g_mapping"].add((om_iri, RR.language, om_language_tag))
    # store information________________________
    st.session_state["pom_saved_ok_flag"] = True
    st.session_state["last_added_pom_list"].insert(0, [st.session_state["pom_iri_to_create"], st.session_state["tm_iri_for_pom"]])
    # reset fields_____________________________
    st.session_state["key_selected_p_label"] = "Select a predicate"
    st.session_state["key_manual_p_ns_prefix"] = "Select a namespace"
    st.session_state["key_manual_p_label"] = ""
    st.session_state["key_pom_label"] = ""
    st.session_state["key_om_constant"] = ""
    st.session_state["om_term_type_constant"] = "📘 Literal"
    st.session_state["key_om_label"] = ""

def save_pom_reference():
    # add triples pom________________________
    st.session_state["g_mapping"].add((st.session_state["tm_iri_for_pom"], RR.predicateObjectMap, st.session_state["pom_iri_to_create"]))
    st.session_state["g_mapping"].add((st.session_state["pom_iri_to_create"], RR.predicate, selected_p_iri))
    st.session_state["g_mapping"].add((st.session_state["pom_iri_to_create"], RR.objectMap, om_iri))
    # add triples om________________________
    st.session_state["g_mapping"].add((om_iri, RDF.type, RR.ObjectMap))
    st.session_state["g_mapping"].add((om_iri, RR.reference, Literal(om_column_name)))    #HERE change to RR.column in R2RML
    if om_term_type_reference == "📘 Literal":
        st.session_state["g_mapping"].add((om_iri, RR.termType, RR.Literal))
        if om_datatype_reference != "Select datatype" and om_datatype_reference != "Natural language tag":
            datatype_dict = utils.get_datatypes_dict()
            st.session_state["g_mapping"].add((om_iri, RR.datatype, datatype_dict[om_datatype_reference]))
        elif om_datatype_reference == "Natural language tag":
            st.session_state["g_mapping"].add((om_iri, RR.language, om_language_tag))
    elif om_term_type_reference == "🌐 IRI":
        st.session_state["g_mapping"].add((om_iri, RR.termType, RR.IRI))
    elif om_term_type_reference == "👻 BNode":
        st.session_state["g_mapping"].add((om_iri, RR.termType, RR.BlankNode))
    # store information________________________
    st.session_state["pom_saved_ok_flag"] = True
    st.session_state["last_added_pom_list"].insert(0, [st.session_state["pom_iri_to_create"], st.session_state["tm_iri_for_pom"]])
    # reset fields_____________________________
    st.session_state["key_selected_p_label"] = "Select a predicate"
    st.session_state["key_manual_p_ns_prefix"] = "Select a namespace"
    st.session_state["key_manual_p_label"] = ""
    st.session_state["key_pom_label"] = ""
    st.session_state["key_om_column_name"] = "Select a column"
    st.session_state["om_term_type_reference"] = "📘 Literal"
    st.session_state["key_om_label"] = ""

def delete_pom():           #function to delete a Predicate-Object Map
    for pom_iri in pom_to_delete_iri_list:
        om_to_delete = st.session_state["g_mapping"].value(subject=pom_iri, predicate=RR.objectMap)
        # remove triples______________________
        st.session_state["g_mapping"].remove((pom_iri, None, None))
        st.session_state["g_mapping"].remove((None, None, pom_iri))
        st.session_state["g_mapping"].remove((om_to_delete, None, None))
    # store information__________________
    st.session_state["pom_deleted_ok_flag"] = True
    st.session_state["last_added_pom_list"] = [pair for pair in st.session_state["last_added_pom_list"]
        if pair[0] not in pom_to_delete_iri_list]
    # reset fields
    st.session_state["key_tm_to_delete_pom"] = "Select a TriplesMap"


def delete_all_pom():           #function to delete a Predicate-Object Map
    for pom_iri in pom_to_delete_all_iri_list:
        om_to_delete = st.session_state["g_mapping"].value(subject=pom_iri, predicate=RR.objectMap)
        # remove triples______________________
        st.session_state["g_mapping"].remove((pom_iri, None, None))
        st.session_state["g_mapping"].remove((None, None, pom_iri))
        st.session_state["g_mapping"].remove((om_to_delete, None, None))
    # store information__________________
    st.session_state["pom_deleted_ok_flag"] = True
    st.session_state["last_added_pom_list"] = [pair for pair in st.session_state["last_added_pom_list"]
        if pair[0] not in pom_to_delete_all_iri_list]
    # reset fields
    st.session_state["key_tm_to_delete_pom"] = "Select a TriplesMap"



# START PAGE_____________________________________________________________________


col1, col2 = st.columns([2,1.5])
if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
    with col1:
        st.markdown(f"""
        <div style="background-color:#f8d7da; padding:1em;
                    border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
            ❗ You need to create or load a mapping. Please go to the
            <b style="color:#a94442;">Global Configuration page</b>.
        </div>
        """, unsafe_allow_html=True)
        st.stop()


#____________________________________________________________
# PANELS OF THE PAGE (tabs)

tab1, tab2, tab3 = st.tabs(["Add TriplesMap", "Add Subject Map", "Add Predicate-Object Map"])


#________________________________________________
#ADD TRIPLESMAP
with tab1:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
    with col2b:
        utils.get_corner_status_message()

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
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    with col1:
        col1a, col1b = st.columns([1.5,1])
    with col1a:
        tm_label = st.text_input("⌨️ Enter label for the new TriplesMap:*", key="key_tm_label_input")    #user-friendly name for the TriplesMap
        st.session_state["tm_label"] = tm_label

    tm_dict = utils.get_tm_dict()
    labelled_ls_list = []      #existing labelled logical sources
    for s, p, o in st.session_state["g_mapping"].triples((None, RML.logicalSource, None)):
        if isinstance(o, URIRef) and split_uri(o)[1] not in labelled_ls_list:
            labelled_ls_list.append(split_uri(o)[1])


    if tm_label:   #after a label has been given
        if tm_label in tm_dict:   #if label is already in use
            with col1a:
                st.markdown(f"""<div class="error-message">
                    ❌ TriplesMap label <b style="color:#a94442;">{tm_label}</b> already in use.
                    Please pick a different label.
                </div>""", unsafe_allow_html=True)
                st.write("")

        else:    #if label is valid


            with col1b:

                ls_options_list = []
                if labelled_ls_list:
                    ls_options_list.append("📑 Existing Logical Source")
                if st.session_state["db_connections_dict"]:
                    ls_options_list.append("📊 SQL Database")
                if st.session_state["ds_files_dict"]:
                    ls_options_list.append("🛢️ Tabular data")
                if not st.session_state["db_connections_dict"] and not st.session_state["ds_files_dict"]:
                    with col1a:
                        st.markdown(f"""<div class="error-message">
                            ❌ No data sources are available. <small>You can add them in the
                            <b>Manage Logical Sources</b> page.</small>
                        </div>""", unsafe_allow_html=True)
                        st.write("")

                ls_option = st.radio("🖱️ Choose the logical source option:*", ls_options_list, horizontal=False)
                st.write("")

            if ls_option == "📑 Existing Logical Source":


                labelled_ls_list.insert(0, "Select a Logical Source")
                with col1a:
                    existing_ls = st.selectbox("🖱️ Select an existing Logical Source:*", labelled_ls_list)

                if existing_ls != "Select a Logical Source":
                    with col1a:
                        save_tm_button_existing_ls = st.button("Save", key="key_save_tm_w_existing_ls", on_click=save_tm_w_existing_ls)


            if ls_option == "📊 SQL Database":
                with col1a:
                    logical_source_label = st.text_input("⌨️ Enter label for the logical source (optional):")
                    if logical_source_label in labelled_ls_list:
                        with col1b:
                            st.markdown(f"""<div class="warning-message">
                                    ⚠️ The logical source label <b>{logical_source_label}</b>
                                    is already in use. Please, pick a different label or leave blank.
                                </div>""", unsafe_allow_html=True)
                            st.write("")

                with col1:
                    col1a, col1b = st.columns(2)
                with col1a:
                    if not st.session_state["db_connections_dict"]:
                        st.markdown(f"""<div class="error-message">
                            ❌ No connections to database are available. Please go to the <b>
                            Manage Logical Sources</b> page.
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                    else:
                        list_to_choose = list(reversed(st.session_state["db_connections_dict"].keys()))
                        list_to_choose.insert(0, "Select a connection")
                        with col1a:
                            db_connection_for_ls = st.selectbox("🖱️ Select connection to database:*", list_to_choose,
                                key="key_db_connection_for_ls")

                        if db_connection_for_ls != "Select a connection":
                            try:
                                conn = utils.make_connection_to_db(db_connection_for_ls)

                            except Exception as e:
                                conn = ""
                                st.markdown(f"""<div class="error-message">
                                    ❌ Connection <b>{db_connection_for_ls}</b> is not working. Please go to the <b>
                                    Manage Logical Sources</b> page to manage the connections to Databases.
                                </div>""", unsafe_allow_html=True)

                        with col1b:
                            query_option = st.radio("🖱️ Select option:*", ["❔ Query", "🔖 Table name"],
                                horizontal=True)

                        if query_option == "❔ Query" and db_connection_for_ls != "Select a connection" and conn:

                            with col1a:
                                list_to_choose = []
                                for query_label, [connection_label, query] in st.session_state["sql_queries_dict"].items():
                                    if connection_label == db_connection_for_ls:
                                        list_to_choose.insert(0, query_label)   # only include queries of the selected connection
                                if list_to_choose:
                                    list_to_choose.insert(0, "Enter new query")
                                    list_to_choose.insert(0, "Select a query")
                                    selected_query_for_ls = st.selectbox("🖱️ Choose a query:*", list_to_choose,
                                        key="key_selected_query_for_ls")
                                else:
                                    selected_query_for_ls = "Enter new query"

                            if selected_query_for_ls == "Enter new query":
                                with col1:
                                    sql_query = st.text_area("⌨️ Enter SQL query:*",
                                        height=150, key="key_sql_query")
                                    cur = conn.cursor()   # create a cursor
                                    if sql_query:
                                        try:
                                            cur.execute(sql_query)
                                            sql_query_ok_flag = True
                                        except:
                                            with col1:
                                                st.markdown(f"""<div class="error-message">
                                                    ❌ <b>Invalid SQL syntax</b>. Please check your query.<br>
                                                </div>""", unsafe_allow_html=True)
                                                st.write("")
                                            sql_query_ok_flag = False

                                        if sql_query_ok_flag:
                                            with col1:
                                                col1a, col1b = st.columns(2)
                                            with col1a:
                                                st.button("Save", key="key_save_tm_w_new_query", on_click=save_tm_w_query)

                            elif selected_query_for_ls != "Select a query":
                                sql_query = st.session_state["sql_queries_dict"][selected_query_for_ls][1]
                                try:
                                    cur = conn.cursor()
                                    cur.execute(sql_query)
                                    sql_query_ok_flag = True
                                except:
                                    with col1a:
                                        st.markdown(f"""<div class="error-message">
                                            ❌ <b>Invalid SQL syntax</b>. Please check your query.<br>
                                        </div>""", unsafe_allow_html=True)
                                        st.write("")
                                    sql_query_ok_flag = False

                                if sql_query_ok_flag:
                                    with col1a:
                                        st.button("Save", key="key_save_tm_w_saved_query", on_click=save_tm_w_query)

                        if query_option == "🔖 Table name" and db_connection_for_ls != "Select a connection" and conn:
                            cur = conn.cursor()   # create a cursor
                            engine = st.session_state["db_connections_dict"][db_connection_for_ls][0]
                            database = st.session_state["db_connections_dict"][db_connection_for_ls][3]
                            utils.get_tables_from_db(engine, cur, database)
                            db_tables = [row[0] for row in cur.fetchall()]

                            with col1a:
                                list_to_choose = db_tables
                                list_to_choose.insert(0, "Select a table")
                                selected_table_for_ls = st.selectbox("🖱️ Choose a table:*", list_to_choose,
                                    key="key_selected_table_for_ls")

                                if selected_table_for_ls != "Select a table":
                                    st.button("Save", key="key_save_tm_w_table_name", on_click=save_tm_w_table_name)

            if ls_option == "🛢️ Tabular data":
                with col1a:
                    logical_source_label = st.text_input("⌨️ Enter label for the logical source (optional):")
                    if logical_source_label in labelled_ls_list:
                        with col1b:
                            st.markdown(f"""<div class="error-message">
                                    ❌ The logical source label <b>{logical_source_label}</b>
                                    is already in use. Please, pick a different label or leave blank.
                                </div>""", unsafe_allow_html=True)
                            st.write("")

                    if not st.session_state["ds_files_dict"]:
                        st.markdown(f"""<div class="error-message">
                            ❌ No non-SQL data sources are available. Please go to the <b>
                            Manage Logical Sources</b> page to load the files.
                        </div>""", unsafe_allow_html=True)
                        st.write("")

                    else:
                        list_to_choose = list(reversed(st.session_state["ds_files_dict"].keys()))
                        list_to_choose.insert(0, "Select file")
                        ds_filename_for_tm = st.selectbox("🖱️ Select the data source file:*", list_to_choose,
                        key="key_ds_filename_for_tm")

                        ds_file = None
                        if ds_filename_for_tm != "Select file":
                            ds_file = st.session_state["ds_files_dict"][ds_filename_for_tm]


                        if ds_file and not logical_source_label in labelled_ls_list:
                            st.button("Save", key="key_save_tm_w_non_relational_ls", on_click=save_tm_w_non_relational_ls)


    # remove tm success message - show here if "Remove" purple heading is not going to be shown
    if not utils.get_tm_dict() and st.session_state["tm_deleted_ok_flag"]:  # show message here if "Remove" purple heading is going to be shown
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            formatted_deleted_tm = utils.format_list_for_markdown(st.session_state["removed_tm_list"])
            if len(st.session_state["removed_tm_list"]) == 1:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ The Triplesmap <b style="color:#F63366;">
                    {st.session_state["removed_tm_list"][0]}</b> has been succesfully deleted!  </div>
                """, unsafe_allow_html=True)
            elif len(st.session_state["removed_tm_list"]) < 7:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ The Triplesmaps <b style="color:#F63366;">
                    {formatted_deleted_tm}</b> have been succesfully deleted!  </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ <b style="color:#F63366;">{len(st.session_state["removed_tm_list"])} TriplesMaps
                    </b> have been succesfully deleted!  </div>
                """, unsafe_allow_html=True)
            st.write("")
        st.session_state["tm_deleted_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()



    # PURPLE HEADING - REMOVE EXISTING TRIPLESMAP
    tm_dict = utils.get_tm_dict()
    if tm_dict:     # only show option if there are tm that can be removed
        with col1:
            st.write("________")
            st.markdown("""<div class="purple-heading">
                    🗑️ Remove Existing TriplesMap
                </div>""", unsafe_allow_html=True)
            st.write("")


        if st.session_state["tm_deleted_ok_flag"]:  # show message here if "Remove" purple heading is going to be shown
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                formatted_deleted_tm = ", ".join(st.session_state["removed_tm_list"][:-1]) + " and " + st.session_state["removed_tm_list"][-1]
                if len(st.session_state["removed_tm_list"]) == 1:
                    st.markdown(f"""
                    <div style="background-color:#d4edda; padding:1em;
                    border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                        ✅ The Triplesmap <b style="color:#F63366;">
                        {st.session_state["removed_tm_list"][0]}</b> has been succesfully deleted!  </div>
                    """, unsafe_allow_html=True)
                elif len(st.session_state["removed_tm_list"]) < 7:
                    st.markdown(f"""
                    <div style="background-color:#d4edda; padding:1em;
                    border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                        ✅ The Triplesmaps <b style="color:#F63366;">
                        {formatted_deleted_tm}</b> have been succesfully deleted!  </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background-color:#d4edda; padding:1em;
                    border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                        ✅ <b style="color:#F63366;">{len(st.session_state["removed_tm_list"])} TriplesMaps
                        </b> have been succesfully deleted!  </div>
                    """, unsafe_allow_html=True)
                st.write("")
            st.session_state["tm_deleted_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()

        with col1:
            col1a, col1b = st.columns([2,1])

        tm_list = list(tm_dict)
        if len(tm_list) > 1:
            tm_list.append("Select all")

        with col1a:
            tm_to_remove_list = st.multiselect("🖱️ Select TriplesMap/s:*", reversed(tm_list), key="key_tm_to_remove_list")

        #HEREHEREHERE

        if "Select all" not in tm_to_remove_list:
            sm_dict = utils.get_sm_dict()
            inner_html = ""
            max_length = 8
            if len(tm_to_remove_list) < max_length:
                for tm in tm_to_remove_list:
                    inner_html += f"""<b>🔖 {tm}</b> ("""
                    tm_iri = tm_dict[tm]
                    sm_to_remove_tm = next((o for o in st.session_state["g_mapping"].objects(tm_iri, RR.subjectMap)), None)
                    if sm_to_remove_tm:
                        inner_html += f"""<span style="font-size:0.85em;">Subject Map: {sm_dict[sm_to_remove_tm][0]} | </span>"""
                    else:
                        inner_html += f"""<span style="font-size:0.85em;">No Subject Map | </span>"""
                    pom_to_remove_tm_list = list(st.session_state["g_mapping"].objects(tm_iri, RR.predicateObjectMap))
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
                    sm_to_remove_tm = next((o for o in st.session_state["g_mapping"].objects(tm_iri, RR.subjectMap)), None)
                    if sm_to_remove_tm:
                        inner_html += f"""<span style="font-size:0.85em;">Subject Map: {sm_dict[sm_to_remove_tm][0]} | </span>"""
                    else:
                        inner_html += f"""<span style="font-size:0.85em;">No Subject Map | </span>"""
                    pom_to_remove_tm_list = list(st.session_state["g_mapping"].objects(tm_iri, RR.predicateObjectMap))
                    if len(pom_to_remove_tm_list) == 1:
                        inner_html += f"""<span style="font-size:0.85em;">{len(pom_to_remove_tm_list)} Predicate-Object Map)<br></span>"""
                    elif pom_to_remove_tm_list:
                        inner_html += f"""<span style="font-size:0.85em;">{len(pom_to_remove_tm_list)} Predicate-Object Maps)<br></span>"""
                    else:
                        inner_html += f"""<span style="font-size:0.85em;">No Predicate-Object Maps)<br></span>"""
                inner_html += f"""🔖 ..."""

            if inner_html:
                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    st.markdown(f"""<div class="info-message-gray">
                            {inner_html}
                        <div>""", unsafe_allow_html=True)
                    st.write("")

        else:   #Select all option
            sm_dict = utils.get_sm_dict()
            inner_html = ""
            max_length = utils.get_max_length_for_display()[4]
            if len(tm_dict) < max_length:
                for tm in tm_dict:
                    inner_html += f"""<b>🔖 {tm}</b> ("""
                    tm_iri = tm_dict[tm]
                    sm_to_remove_tm = next((o for o in st.session_state["g_mapping"].objects(tm_iri, RR.subjectMap)), None)
                    if sm_to_remove_tm:
                        inner_html += f"""<span style="font-size:0.85em;">Subject Map: {sm_dict[sm_to_remove_tm][0]} | </span>"""
                    else:
                        inner_html += f"""<span style="font-size:0.85em;">No Subject Map | </span>"""
                    pom_to_remove_tm_list = list(st.session_state["g_mapping"].objects(tm_iri, RR.predicateObjectMap))
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
                    sm_to_remove_tm = next((o for o in st.session_state["g_mapping"].objects(tm_iri, RR.subjectMap)), None)
                    if sm_to_remove_tm:
                        inner_html += f"""<span style="font-size:0.85em;">Subject Map: {sm_dict[sm_to_remove_tm][0]} | </span>"""
                    else:
                        inner_html += f"""<span style="font-size:0.85em;">No Subject Map | </span>"""
                    pom_to_remove_tm_list = list(st.session_state["g_mapping"].objects(tm_iri, RR.predicateObjectMap))
                    if len(pom_to_remove_tm_list) == 1:
                        inner_html += f"""<span style="font-size:0.85em;">{len(pom_to_remove_tm_list)} Predicate-Object Map)<br></span>"""
                    elif pom_to_remove_tm_list:
                        inner_html += f"""<span style="font-size:0.85em;">{len(pom_to_remove_tm_list)} Predicate-Object Maps)<br></span>"""
                    else:
                        inner_html += f"""<span style="font-size:0.85em;">No Predicate-Object Maps)<br></span>"""
                inner_html += f"""🔖 ..."""

            if inner_html:
                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    st.markdown(f"""<div class="info-message-gray">
                            {inner_html}
                        <div>""", unsafe_allow_html=True)
                    st.write("")



        if tm_to_remove_list:
            if "Select all" not in tm_to_remove_list:
                with col1a:
                    delete_tm_checkbox = st.checkbox(
                    ":gray-badge[⚠️ I am sure I want to delete the TriplesMap/s]",
                    key="delete_tm_checkbox")
                if delete_tm_checkbox:
                    with col1:
                        col1a, col1b = st.columns([1,2])
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
                    ":gray-badge[⚠️ I am sure I want to delete all TriplesMaps]",
                    key="delete_tm_checkbox")
                if delete_tm_checkbox:
                    with col1:
                        col1a, col1b = st.columns([1,2])
                    with col1a:
                        st.button("Delete", on_click=delete_all_tm)


#________________________________________________



#________________________________________________
#ADD SUBJECT MAP TO MAP
with tab2:

    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
    with col2b:
        utils.get_corner_status_message()

    # Display last added namespaces in dataframe (also option to show all ns)
    tm_dict = utils.get_tm_dict()
    sm_dict = utils.get_sm_dict()

    with col2:
        col2a, col2b = st.columns([0.5, 2])

    with col2b:

        st.write("")
        st.write("")

        last_added_sm_df = pd.DataFrame([
            {"Subject Map": sm_dict[subject_map][0], "Assigned to": triples_map,  # Use directly or format if needed
            "Rule": sm_dict[subject_map][1], "ID/Constant": sm_dict[subject_map][3]}
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




#____________________________________

    #PURPLE HEADING - ADD NEW SUBJECT MAP
    with col1:
        st.markdown("""<div class="purple-heading">
                🧱 Add New Subject Map
            </div>""", unsafe_allow_html=True)
        st.write("")

    if st.session_state["sm_saved_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>Subject Map</b> has been created!
            </div>""", unsafe_allow_html=True)
        st.session_state["sm_saved_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()


    with col1:
        col1a, col1b = st.columns([2,1.2])

    tm_dict = utils.get_tm_dict()

    #SELECT THE TRIPLESMAP TO WHICH THE SUBJECT MAP WILL BE ADDED___________________________
    #only triplesmaps without subject map can be selected

    tm_wo_sm_list = []          #list of all TriplesMap which do not have a subject yet
    for tm_label, tm_iri in tm_dict.items():
        if not next(st.session_state["g_mapping"].objects(tm_iri, RR.subjectMap), None):   #if there is no subject for that TriplesMap
            tm_wo_sm_list.append(tm_label)


    if not tm_dict:
        with col1a:
            st.markdown(f"""<div class="info-message-gray">
                🔒 No TriplesMaps in mapping {st.session_state["g_label"]}.<br>
                You can add new TriplesMaps in the <b>Add TriplesMap</b> panel.
                    </div>""", unsafe_allow_html=True)
            st.write("")

    elif not tm_wo_sm_list:
        with col1:
            col1a, col2a = st.columns([2,0.5])
        with col1a:
            st.markdown(f"""<div class="info-message-gray">
                🔒 <b>All existing TriplesMaps have already been assigned a Subject Map.</b><br>
                <ul style="margin-top:0.5em; margin-bottom:0; font-size:0.9em; list-style-type: disc; padding-left: 1.2em;">
                    <li>You can add new TriplesMaps in the <b>Add TriplesMap</b> panel.</li>
                    <li>You can remove the Subject Map of a TriplesMap in the <b>🗑️ Remove existing Subject Map</b> option.</li>
                </ul></div>""",unsafe_allow_html=True)
            st.write("")



    else:
        #IF THERE ARE TRIPLESMAPS AVAILABLE___________________________

        #first create dictionary of all the existing Subject Maps

        existing_sm_dict = {}
        for sm in st.session_state["g_mapping"].objects(predicate=RR.subjectMap):
            if isinstance(sm, URIRef):
                existing_sm_dict[split_uri(sm)[1]] = sm
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

        if tm_label_for_sm != "Select a TriplesMap":
            if existing_sm_list:  # if there exist labelled subject maps
                with col1b:
                    sm_options_list = ["🆕 Create new Subject Map", "📑 Select existing Subject Map"]
                    sm_option = st.radio("🖱️ Select an option:*", sm_options_list)

            else:
                    sm_option = "🆕 Create new Subject Map"

            if sm_option == "📑 Select existing Subject Map":

                with col1a:
                    existing_sm_list.append("Select a Subject Map")
                    sm_label = st.selectbox("🖱️ Select an existing Subject Map:*", reversed(existing_sm_list), key="key_sm_label_existing")
                    if sm_label != "Select a Subject Map":
                        sm_iri = existing_sm_dict[sm_label]
                        tm_iri_for_sm = tm_dict[tm_label_for_sm]
                        st.session_state["sm_iri"] = sm_iri
                        st.session_state["sm_label"] = sm_label
                        st.session_state["tm_label_for_sm"] = tm_label_for_sm
                        st.button("Save", key="key_save_existing_sm_button", on_click=save_sm_existing)


            elif sm_option == "🆕 Create new Subject Map":


                if tm_label_for_sm != "Select a TriplesMap":   #TriplesMap selected
                    tm_iri_for_sm = tm_dict[tm_label_for_sm]
                    ls_iri_for_sm = next(st.session_state["g_mapping"].objects(tm_iri_for_sm, RML.logicalSource), None)
                    ds_for_sm = str(next(st.session_state["g_mapping"].objects(ls_iri_for_sm, RML.source), None))

                    with col1b:
                        column_list = utils.get_column_list_and_give_info(tm_iri_for_sm)

                    with col1a:
                        sm_label = st.text_input("⌨️ Enter Subject Map label (optional):", key="key_sm_label_new")
                    NS = st.session_state["structural_ns_dict"]["Subject Map"][1]
                    sm_iri = BNode() if not sm_label else NS[sm_label]
                    if next(st.session_state["g_mapping"].triples((None, RR.subjectMap, sm_iri)), None):
                        with col1a:
                            st.markdown(f"""<div class="error-message">
                                ❌ That <b>Subject Map label</b> is already in use. Please pick another label or leave blank.
                            </div>""", unsafe_allow_html=True)
                            st.write("")

                    with col1:
                        st.write("")
                        st.markdown("""<div class="gray-heading">
                                🏗️ Create the Subject Map</dic><br>
                            """,unsafe_allow_html=True)


                    with col1:
                        sm_generation_rule_list = ["Template 📐", "Constant 🔒", "Reference 📊"]
                        sm_generation_rule = st.radio("🖱️ Define the Subject Map generation rule:*",
                            sm_generation_rule_list, horizontal=True, key="key_sm_generation_rule_radio",
                                label_visibility="collapsed")


                    #_______________________________________________
                    # SUBJECT MAP - TEMPLATE-VALUED
                    if sm_generation_rule == "Template 📐":

                        with col1:
                            col1a, col1b = st.columns([1,1.5])
                        with col1a:
                            build_template_action_sm = st.selectbox(
                                label="🖱️ Add template part:", options=["🏷️ Add Namespace*", "🔒 Add fixed part", "📈 Add variable part", "🗑️ Reset template"],
                                key="key_build_template_action_sm")


                        if build_template_action_sm == "🔒 Add fixed part":
                            with col1b:
                                sm_template_fixed_part = st.text_input("⌨️ Enter fixed part:", key="key_sm_fixed_part")
                                if re.search(r"[ \t\n\r<>\"{}|\\^`]", sm_template_fixed_part):
                                    st.markdown(f"""<div class="warning-message">
                                            ⚠️ You included a space or an unescaped character, which is discouraged.
                                        </div>""", unsafe_allow_html=True)
                                    st.write("")
                                if sm_template_fixed_part:
                                    st.button("Add", key="key_save_sm_template_fixed_part_button", on_click=save_sm_template_fixed_part)

                        elif build_template_action_sm == "📈 Add variable part":
                            with col1b:
                                if not column_list:   #data source is not available (load)
                                    sm_template_variable_part = st.text_input("⌨️ Manually enter column of the data source:*")
                                    st.markdown("""<div style='text-align: right; font-size: 10.5px; color: #cc9a06; font-weight: bold; margin-top: -10px;'>
                                        ⚠️ discouraged
                                    </div>""", unsafe_allow_html=True)
                                    if sm_template_variable_part:
                                        st.button("Add", key="save_sm_template_variable_part_button", on_click=save_sm_template_variable_part)
                                else:  # data source is available
                                    list_to_choose = column_list.copy()
                                    list_to_choose.insert(0, "Select a column")
                                    sm_template_variable_part = st.selectbox("🖱️ Select the column of the data source:", list_to_choose, key="key_sm_template_variable_part")
                                    if st.session_state["sm_template_list"] and st.session_state["sm_template_list"][-1].endswith("}"):
                                        st.markdown(f"""<div class="warning-message">
                                                ⚠️ Including two adjacent variable parts is strongly discouraged.
                                                <small><b>Best practice:</b> Add a separator between variables to improve clarity.</small>
                                            </div>""", unsafe_allow_html=True)
                                        st.write("")
                                    if sm_template_variable_part != "Select a column":
                                        st.button("Add", key="save_sm_template_variable_part_button", on_click=save_sm_template_variable_part)


                        elif build_template_action_sm == "🏷️ Add Namespace*":
                            with col1b:
                                mapping_ns_dict = utils.get_mapping_ns_dict()
                                list_to_choose = list(mapping_ns_dict.keys())
                                list_to_choose.insert(0, "Select a namespace")
                                sm_template_ns_prefix = st.selectbox("🖱️ Select a namespace for the template:", list_to_choose, key="key_sm_template_ns_prefix")
                                if not mapping_ns_dict:
                                    st.markdown(f"""<div class="error-message">
                                            ❌ No namespaces available. You can add namespaces in the
                                             <b>Global Configuration</b> page.
                                        </div>""", unsafe_allow_html=True)


                                if sm_template_ns_prefix != "Select a namespace":
                                    sm_template_ns = mapping_ns_dict[sm_template_ns_prefix]
                                    st.button("Add", key="key_add_ns_to_sm_template_button", on_click=add_ns_to_sm_template)


                        elif build_template_action_sm == "🗑️ Reset template":
                            with col1b:
                                st.write("")
                                st.write("")
                                st.markdown(f"""<div class="warning-message">
                                        ⚠️ The current template will be deleted.
                                    </div>""", unsafe_allow_html=True)
                                st.write("")
                                st.button("Reset", on_click=reset_sm_template)

                        with col1:
                            col1a, col1b = st.columns([3,1])
                        with col1a:
                            sm_template = "".join(st.session_state["sm_template_list"])
                            if sm_template:
                                st.write("")
                                st.markdown(f"""
                                    <div class="gray-preview-message" style="word-wrap:break-word; overflow-wrap:anywhere;">
                                        📐 <b>Your <b style="color:#F63366;">template</b> so far:</b><br>
                                    <div style="margin-top:0.2em; font-size:15px; color:#333;">
                                            {sm_template}
                                    </div></div>""", unsafe_allow_html=True)
                                st.write("")
                            else:
                                st.write("")
                                st.markdown(f"""<div class="gray-preview-message">
                                        📐 <b> Build your <b style="color:#F63366;">template</b> and preview it here.</b> <br>
                                    <div style="font-size:13px; color:#666666; margin-top:0.2em;">
                                        🛈 You can add as many parts as you need.
                                    </div></div>""", unsafe_allow_html=True)
                                st.write("")



                        with col1b:
                            st.write("")
                            sm_term_type_template = st.radio(label="🖱️ Select term type:*", options=["🌐 IRI", "👻 BNode"],
                                key="sm_term_type_template")

                        if sm_term_type_template == "🌐 IRI" and not st.session_state["sm_template_prefix"] and sm_template:
                            with col1a:

                                st.markdown(f"""<div class="error-message">
                                    ❌ Term type is <b>🌐 IRI</b>. <small>You must <b>add a namespace</b>.</small>
                                </div>""", unsafe_allow_html=True)
                                st.write("")


                    #_______________________________________________
                    # SUBJECT MAP - CONSTANT-VALUED
                    if sm_generation_rule == "Constant 🔒":

                        with col1:
                            col1a, col1b = st.columns(2)
                        with col1a:
                            sm_constant = st.text_input("⌨️ Enter constant:*", key="key_sm_constant")

                        with col1b:
                            sm_term_type_constant = st.radio(label="🖱️ Select term type:*", options=["🌐 IRI"], horizontal=True,
                                key="sm_term_type_constant")

                        mapping_ns_dict = utils.get_mapping_ns_dict()
                        list_to_choose = list(mapping_ns_dict.keys())
                        list_to_choose.insert(0, "Select a namespace")
                        with col1a:
                            sm_constant_ns_prefix = st.selectbox("🖱️ Select a namespace for the constant:*", list_to_choose,
                                key="key_sm_constant_ns")

                            if not mapping_ns_dict:
                                with col1b:
                                    st.markdown(f"""<div class="error-message">
                                            ❌ You must add namespaces in
                                            the <b>Global Configuration</b> page.
                                        </div>""", unsafe_allow_html=True)

                        with col1a:
                            st.write("")


                    #_______________________________________________
                    #SUBJECT MAP - REFERENCED-VALUED
                    if sm_generation_rule ==  "Reference 📊":
                        sm_datatype = ""
                        sm_language_tag = ""
                        sm_ready_flag_reference = False


                        with col1:
                            col1a, col1b = st.columns([1,1.2])
                        with col1a:
                            list_to_choose = column_list.copy()
                            list_to_choose.insert(0, "Select a column")

                        with col1b:
                            sm_term_type_reference = st.radio(label="🖱️ Select term type:*", options=["🌐 IRI", "👻 BNode"],
                                horizontal=True, key="sm_term_type_reference")

                        if not column_list:   #data source is not available (load)
                            with col1a:
                                sm_column_name = st.text_input("⌨️ Manually enter column of the data source:*")
                                st.markdown("""<div style='text-align: right; font-size: 10.5px; color: #cc9a06; font-weight: bold; margin-top: -10px;'>
                                    ⚠️ discouraged
                                </div>""", unsafe_allow_html=True)

                            if sm_column_name and sm_term_type_reference == "🌐 IRI":
                                with col1b:
                                    st.markdown(f"""<div class="warning-message">
                                            ⚠️ Term type is <b>🌐 IRI</b>.
                                            <small>Make sure that the values in the referenced column
                                            are valid IRIs.</small>
                                        </div>""", unsafe_allow_html=True)
                                    st.write("")

                        else:
                            with col1a:
                                sm_column_name = st.selectbox(f"""🖱️ Select the column of the data source:*""", list_to_choose,
                                    key="key_sm_column_name")

                            if sm_column_name != "Select a column" and sm_term_type_reference == "🌐 IRI":
                                with col1b:
                                    st.markdown(f"""<div class="warning-message">
                                            ⚠️ Term type is <b>🌐 IRI</b>.
                                            <small>Make sure that the values in the referenced column
                                            are valid IRIs.</small>
                                        </div>""", unsafe_allow_html=True)
                                    st.write("")

                        with col1a:
                            st.write("")

                    # DISPLAY INFO AND SAVE________________________________
                    with col1:
                        st.write("")
                        st.markdown("""<div class="gray-heading">
                                💾 Check and save Subject Map</dic><br>
                            """,unsafe_allow_html=True)

                    if sm_generation_rule == "Template 📐":
                        with col1:
                            col1a, col1b = st.columns([2,1])
                        sm_complete_flag = "✔️ Yes" if sm_template else "❌ No"

                        inner_html = f"""<tr class="title-row"><td colspan="2">🔎 Subject Map</td></tr>"""

                        if next(st.session_state["g_mapping"].triples((None, RR.subjectMap, sm_iri)), None):
                            sm_complete_flag = "❌ No"
                            inner_html += f"""<tr><td><b>Subject Map label</b></td>
                            <td>{sm_label} <span style='font-size:11px; color:#888;'>(❌ already in use)</span></td></tr>"""
                        else:
                            inner_html += f"""<tr><td><b>Subject Map label</b></td><td>{sm_label}</td></tr>"""

                        inner_html += f"""<tr><td><b>Generation rule*</b></td><td>{sm_generation_rule}</td></tr>
                        <tr><td><b>Template*</b></td><td>{sm_template}</td></tr>
                        <tr><td><b>Term type*</b></td><td>{sm_term_type_template}</td></tr>"""

                        if sm_template and sm_term_type_template == "🌐 IRI":
                            sm_template_ns_prefix_display = st.session_state["sm_template_prefix"] if st.session_state["sm_template_prefix"] else ""
                            inner_html += f"""<tr><td><b>Template namespace*</b></td><td>{sm_template_ns_prefix_display}</td></tr>"""
                            sm_complete_flag = "✔️ Yes" if st.session_state["sm_template_prefix"] else "❌ No"

                        inner_html += f"""<tr><td><b>Required fields complete</b></td><td> {sm_complete_flag} </td></tr>"""

                        full_html = f"""<table class="info-table-gray">
                                {inner_html}</table>"""
                        # render
                        with col1:
                            col1a, col1b, col1c = st.columns([1.5,0.2,0.7])
                        with col1a:
                            st.markdown(full_html, unsafe_allow_html=True)


                    if sm_generation_rule == "Constant 🔒":
                        inner_html = f"""<tr class="title-row"><td colspan="2">🔎 Subject Map</td></tr>"""

                        if next(st.session_state["g_mapping"].triples((None, RR.subjectMap, sm_iri)), None):
                            sm_complete_flag = "❌ No"
                            inner_html += f"""<tr><td><b>Subject Map label</b></td>
                            <td>{sm_label} <span style='font-size:11px; color:#888;'>(❌ already in use)</span></td></tr>"""
                        else:
                            inner_html += f"""<tr><td><b>Subject Map label</b></td><td>{sm_label}</td></tr>"""

                        inner_html += f"""<tr><td><b>Generation rule*</b></td><td>{sm_generation_rule}</td></tr>
                        <tr><td><b>Constant*</b></td><td>{sm_constant}</td></tr>
                        <tr><td><b>Term type*</b></td><td>{sm_term_type_constant}</td></tr>"""

                        sm_complete_flag = "✔️ Yes" if (sm_constant_ns_prefix != "Select a namespace" and sm_constant) else "❌ No"
                        sm_constant_ns_prefix_display = sm_constant_ns_prefix if sm_constant_ns_prefix != "Select a namespace" else ""
                        inner_html += f"""<tr><td><b>Constant namespace*</b></td><td>{sm_constant_ns_prefix_display}</td></tr>"""

                        inner_html += f"""<tr><td><b>Required fields complete</b></td><td> {sm_complete_flag} </td></tr>"""

                        full_html = f"""<table class="info-table-gray">
                                {inner_html}</table>"""
                        # render
                        with col1:
                            col1a, col1b, col1c = st.columns([1.5,0.2,0.7])
                        with col1a:
                            st.markdown(full_html, unsafe_allow_html=True)


                    if sm_generation_rule == "Reference 📊":
                        if column_list:
                            sm_complete_flag = "✔️ Yes" if sm_column_name != "Select a column" else "❌ No"
                        else:
                            sm_complete_flag = "✔️ Yes" if sm_column_name else "❌ No"
                        sm_column_name_display = sm_column_name if sm_column_name != "Select a column" else ""

                        inner_html = f"""<tr class="title-row"><td colspan="2">🔎 Subject Map</td></tr>"""

                        if next(st.session_state["g_mapping"].triples((None, RR.subjectMap, sm_iri)), None):
                            sm_complete_flag = "❌ No"
                            inner_html += f"""<tr><td><b>Subject Map label</b></td>
                            <td>{sm_label} <span style='font-size:11px; color:#888;'>(❌ already in use)</span></td></tr>"""
                        else:
                            inner_html += f"""<tr><td><b>Subject Map label</b></td><td>{sm_label}</td></tr>"""

                        inner_html += f"""<tr><td><b>Generation rule*</b></td><td>{sm_generation_rule}</td></tr>
                        <tr><td><b>Data source column*</b></td><td>{sm_column_name_display}</td></tr>
                        <tr><td><b>Term type*</b></td><td>{sm_term_type_reference}</td></tr>"""


                        if sm_column_name != "Select a column" and sm_term_type_reference == "📘 Literal":
                            inner_html += f"""<tr><td><b>Datatype</b></td><td>{sm_datatype}</td></tr>"""
                            if sm_datatype == "Natural language text":
                                sm_complete_flag == "✔️ Yes" if sm_language_tag else "❌ No"
                                inner_html += f"""<tr><td><b>Language tag*</b></td><td>{language_tag}</td></tr>"""

                        inner_html += f"""<tr><td><b>Required fields complete</b></td><td> {sm_complete_flag} </td></tr>"""

                        full_html = f"""<table class="info-table-gray">
                                {inner_html}</table>"""
                        # render
                        with col1:
                            col1a, col1b, col1c = st.columns([1.5,0.2,0.7])
                        with col1a:
                            st.markdown(full_html, unsafe_allow_html=True)


                    # INFO AND SAVE BUTTON____________________________________
                    if sm_complete_flag == "✔️ Yes":
                        with col1c:
                            st.markdown(f"""<div class="success-message">
                                🧐  All <b>required fields (*)</b> are complete.
                                <small>Double-check the information before saving.</smalL> </div>
                            """, unsafe_allow_html=True)
                            st.write("")
                            if sm_generation_rule == "Template 📐":
                                save_sm_template_button = st.button("Save", on_click=save_sm_template, key="key_save_sm_template_button")
                            elif sm_generation_rule == "Constant 🔒":
                                save_sm_constant_button = st.button("Save", on_click=save_sm_constant, key="key_save_sm_constant_button")
                            if sm_generation_rule == "Reference 📊":
                                save_sm_reference_button = st.button("Save", on_click=save_sm_reference, key="key_save_sm_reference_button")

                    else:
                        with col1c:
                            st.markdown(f"""<div class="warning-message">
                                    ⚠️ All <b>required fields (*)</b> must be filled in order to save the Subject Map.
                                </div>""", unsafe_allow_html=True)
                            st.write("")




    # PURPLE HEADING - SUBJECT MAP CONFIGURATION
    sm_list = list(st.session_state["g_mapping"].objects(predicate=RR.subjectMap))
    if sm_list:    # only show option if there are sm to configure
        with col1:
            st.write("______________")
            st.markdown("""<div class="purple-heading">
                    ➕ Subject Map Configuration
                </div>""", unsafe_allow_html=True)
            st.write("")


        # select the sm via a tm to which it is assigned
        tm_dict = utils.get_tm_dict()
        tm_w_sm_list = []   # list of all tm with assigned sm
        for tm_label, tm_iri in tm_dict.items():
            if any(st.session_state["g_mapping"].triples((tm_iri, RR.subjectMap, None))):
                tm_w_sm_list.append(tm_label)

        # select the sm directly (must be labelled)
        labelled_sm_list = []
        for tm_label, tm_iri in tm_dict.items():
            sm_iri = st.session_state["g_mapping"].value(subject=tm_iri, predicate=RR.subjectMap)
            if isinstance(sm_iri, URIRef) and sm_iri not in labelled_sm_list:
                if split_uri(sm_iri)[1] not in labelled_sm_list:
                    labelled_sm_list.append(split_uri(sm_iri)[1])


        with col1:
            col1a, col1b = st.columns([1,1])
        # if there is a cached tm use as default (and give option to select sm instead)
        if st.session_state["last_added_tm_list"] and st.session_state["last_added_tm_list"][0] in tm_w_sm_list:
            tm_w_sm_list.append("Select a labelled Subject Map")
            with col1a:
                tm_label_for_config = st.selectbox("🖱️ Select a TriplesMap:*", reversed(tm_w_sm_list),
                    index=list(reversed(tm_w_sm_list)).index(st.session_state["last_added_tm_list"][0]),
                    key="key_tm_label_for_config")
            tm_iri_for_config = tm_dict[tm_label_for_config] if tm_label_for_config != "Select a labelled Subject Map" else "Select a labelled Subject Map12323"
            sm_iri_for_config = next((o for s, p, o in st.session_state["g_mapping"].triples((tm_iri_for_config, RR.subjectMap, None))), None)
        else:    # if there is no cached tm, just selectbox without default
            tm_w_sm_list.append("Select a TriplesMap")
            with col1a:
                tm_label_for_config = st.selectbox("🖱️ Select a TriplesMap:*", reversed(tm_w_sm_list),
                    key="key_tm_label_for_config")
            tm_iri_for_config = tm_dict[tm_label_for_config] if tm_label_for_config != "Select a TriplesMap" else "Select a TriplesMap123123"
            sm_iri_for_config = next((o for s, p, o in st.session_state["g_mapping"].triples((tm_iri_for_config, RR.subjectMap, None))), None)

        # option to select a labelled sm (instead of a tm) - only if there exist labelled sm
        if (tm_label_for_config == "Select a TriplesMap"
            or tm_label_for_config == "Select a labelled Subject Map" and labelled_sm_list):
            labelled_sm_list.append("Select a Subject Map")
            with col1b:
                sm_label_for_config = st.selectbox("🖱️ or select a labelled Subject Map:", reversed(labelled_sm_list))
            if sm_label_for_config != "Select a Subject Map":
                NS = st.session_state["structural_ns_dict"]["Subject Map"][1]
                sm_iri_for_config = NS[sm_label_for_config]

        if sm_iri_for_config:    # only if the sm has been selected (either way)
            with col1a:
                sm_dict = utils.get_sm_dict()


            sm_label_for_config = sm_dict[sm_iri_for_config][0]
            sm_type = sm_dict[sm_iri_for_config][1]
            sm_id_iri = sm_dict[sm_iri_for_config][2]
            sm_id_label = sm_dict[sm_iri_for_config][3]
            corresponding_tm_list = sm_dict[sm_iri_for_config][4]

            with col1:
                col1a, col1b = st.columns([2,1])
            with col1b:
                if len(corresponding_tm_list) > 1:
                    formatted_corresponding_tm = ", ".join(corresponding_tm_list[:-1]) + " and " + corresponding_tm_list[-1]
                    st.markdown(f"""<div class="info-message-blue">
                            🔖 The Subject Map <b>{sm_label_for_config}</b> is assigned to the TriplesMaps <b>{formatted_corresponding_tm}</b>.
                        </div>""", unsafe_allow_html=True)
                elif len(corresponding_tm_list) == 1:
                    st.markdown(f"""<div class="info-message-blue">
                            🔖 The Subject Map <b>{sm_label_for_config}</b> is assigned to the TriplesMap <b>{corresponding_tm_list[0]}</b>.
                        </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="error-message">
                            ❌ The Subject Map <b>{sm_label_for_config}</b> is not assigned to any TriplesMap. Please check your mapping.
                        </div>""", unsafe_allow_html=True)

            sm_config_options_list = ["🆔 Term type", "🏷️ Subject class", "🗺️️ Graph map"]
            with col1a:
                sm_config_selected_option = st.radio("🖱️ Select an option:*", sm_config_options_list,
                    horizontal=True)

            #TERM TYPE - IRI by default, but can be changed to BNode
            if sm_config_selected_option == "🆔 Term type":

                with col1:
                    col1a, col1b = st.columns([2,1])
                # with col1b:
                #     st.markdown(f"""<div class="info-message-gray">
                #             <b> 🆔 Term type </b>: <br>
                #              Indicates the target graph for the subject map triples.
                #         </div>""", unsafe_allow_html=True)


                if not st.session_state["g_mapping"].value(sm_iri_for_config, RR["termType"]):   # if termType not indicated yet, make it IRI (default)
                    st.session_state["g_mapping"].add((sm_iri_for_config, RR["termType"], RR.IRI))
                sm_term_type = st.session_state["g_mapping"].value(sm_iri_for_config, RR["termType"])


                if split_uri(sm_term_type)[1] == "IRI":
                    with col1a:
                        st.markdown(f"""<div class="gray-preview-message">
                                🔒 Subject term type: <b style="color:#F63366;">IRI</b><br>
                                <small>Click button to change to BNode.</small>
                            </div>""", unsafe_allow_html=True)
                        st.write("")
                        st.button("Change to BNode", on_click=change_term_type_to_BNode)
                else:
                    with col1a:
                        st.markdown(f"""<div class="gray-preview-message">
                                🔒 Subject term type: <b style="color:#F63366;">BNode</b><br>
                                <small>Click button to change to IRI.</small>
                            </div>""", unsafe_allow_html=True)
                        st.write("")
                        st.button("Change to IRI", on_click=change_term_type_to_IRI)


            #SUBJECT CLASS (ontology-based)
            if sm_config_selected_option == "🏷️ Subject class":

                # with col1b:
                #     st.markdown(f"""<div class="info-message-gray">
                #             <b> 🏷️ Subject class </b>: <br>
                #              Declares the ontology-based class of the generated subjects.
                #         </div>""", unsafe_allow_html=True)


                #Check whether the subject map already has a class
                sm_class = st.session_state["g_mapping"].value(sm_iri_for_config, RR["class"])

                if sm_class:   # sm class already exists
                    with col1a:
                        if isinstance(sm_class, URIRef):
                            st.markdown(f"""<div class="gray-preview-message">
                                    🔒 Subject class:
                                    <b style="color:#F63366;">{split_uri(sm_class)[1]}</b><br>
                                    <small>Delete it to assign a different subject class.</small>
                                </div>""", unsafe_allow_html=True)
                        elif isinstance(sm_class, BNode):
                            st.markdown(f"""<div class="gray-preview-message">
                                    🔒 Subject class:
                                    <b style="color:#F63366;">BNode</b><br> ({sm_class})<br>
                                    <small>Delete it to assign a different subject class.</small>
                                </div>""", unsafe_allow_html=True)
                        st.write("")

                        delete_subject_class_checkbox= st.checkbox(
                        ":gray-badge[⚠️ I am completely sure I want to delete the subject class]",
                        key="key_delete_sm_class_checkbox")
                        if delete_subject_class_checkbox:
                            st.button("Delete", on_click=delete_subject_class)


                else:        # subject class does not exist yet
                    with col1a:
                        st.markdown(f"""<div class="gray-preview-message">
                                🔓 Subject class:
                                <b style="color:#F63366;">not given</b><br>
                                <small>Enter below.</small>
                            </div>""", unsafe_allow_html=True)
                        st.write("")

                    # WE ORGANISE THE ONTOLOGY CLASSES IN DIFFERENT DICTIONARIES
                    # dictionary for simple classes
                    ontology_classes_dict = {}
                    class_triples = set()
                    class_triples |= set(st.session_state["g_ontology"].triples((None, RDF.type, OWL.Class)))   #collect owl:Class definitions
                    class_triples |= set(st.session_state["g_ontology"].triples((None, RDF.type, RDFS.Class)))    # collect rdfs:Class definitions
                    for s, p, o in class_triples:   #we add to dictionary removing the BNodes
                        if not isinstance(s, BNode):
                            ontology_classes_dict[split_uri(s)[1]] = s

                    # dictionary for superclasses
                    # superclass_dict = utils.get_ontology_superclass_dict()   # HERE MOVE TO UTILS
                    superclass_dict = {}
                    for s, p, o in list(set(st.session_state["g_ontology"].triples((None, RDFS.subClassOf, None)))):
                        if not isinstance(o, BNode) and o not in superclass_dict.values():
                            superclass_dict[o.split("/")[-1].split("#")[-1]] = o


                    # ONLY SHOW OPTIONS IF THE ONTOLOGY HAS THEM
                    if ontology_classes_dict:   # if the ontology includes at least one class
                        class_type_option_list = ["🧩 Ontology class", "🚫 Class outside ontology"]
                        with col1a:
                            class_type = st.radio("Select an option:", class_type_option_list,
                                label_visibility="collapsed", key="key_class_type_radio")
                    else:
                        class_type = "🚫 Class outside ontology"

                    #ONTOLOGY CLASS
                    if class_type == "🧩 Ontology class":

                        with col1:
                            col1a, col1b = st.columns(2)

                        # Class selection
                        if superclass_dict:   # there exists at least one superclass (show superclass filter)
                            classes_in_superclass_dict = {}
                            with col1a:
                                superclass_list = list(superclass_dict.keys())
                                superclass_list.insert(0, "Select a superclass")
                                superclass = st.selectbox("🖱️ Select a superclass to filter classes (optional):", superclass_list,
                                    key="key_superclass")   #superclass label
                            if superclass != "Select a superclass":   # a superclass has been selected (filter)
                                classes_in_superclass_dict[superclass] = superclass_dict[superclass]
                                superclass = superclass_dict[superclass] #we get the superclass iri
                                for s, p, o in list(set(st.session_state["g_ontology"].triples((None, RDFS.subClassOf, superclass)))):
                                    classes_in_superclass_dict[split_uri(s)[1]] = s
                                class_list = list(classes_in_superclass_dict.keys())
                                class_list.insert(0, "Select a class")
                                with col1b:
                                    subject_class = st.selectbox("🖱️ Select a class:*", class_list,
                                        key="key_subject_class")   #class label
                            else:  #no superclass selected (list all classes)
                                class_list = list(ontology_classes_dict.keys())
                                class_list.insert(0, "Select a class")
                                with col1b:
                                    subject_class = st.selectbox("🖱️ Select a class:*", class_list,
                                        key="key_subject_class")   #class label

                        else:     #no superclasses exist (no superclass filter)
                            class_list = list(ontology_classes_dict.keys())
                            class_list.insert(0, "Select a class")
                            with col1a:
                                subject_class = st.selectbox("🖱️ Select a class:*", class_list,
                                    key="key_subject_class")   #class label

                        if subject_class != "Select a class":
                            subject_class = ontology_classes_dict[subject_class] #we get the superclass iri
                            with col1a:
                                st.button("Save", key="save_subject_class", on_click=save_ontology_subject_class)

                    #CLASS OUTSIDE ONTOLOGY
                    if class_type == "🚫 Class outside ontology":

                        if st.session_state["g_ontology"] and not ontology_classes_dict: #there is an ontology but it has no classes
                            with col1b:
                                st.write("")
                                st.markdown(f"""<div class="warning-message">
                                          ⚠️ Your <b>ontology</b> does not define any classes.
                                          <small>Using an ontology with predefined classes is recommended.</small>
                                    </div>""", unsafe_allow_html=True)
                        elif st.session_state["g_ontology"]:   #there exists an ontology and it has classes
                            with col1b:
                                st.write("")
                                st.markdown(f"""<div class="warning-message">
                                          ⚠️ The option <b>Class outside ontology</b> lacks ontology alignment.
                                          <small>An ontology-driven approach is recommended.</small>
                                    </div>""", unsafe_allow_html=True)
                        else:
                            with col1b:
                                st.write("")
                                st.markdown(f"""<div class="warning-message">
                                        ⚠️ You are working <b>without an ontology</b>. <small>Loading an ontology
                                        from the <b> Global Configuration</b> page is encouraged.</small>
                                    </div>""", unsafe_allow_html=True)

                        mapping_ns_dict = utils.get_mapping_ns_dict()

                        with col1:
                            col1a, col1b = st.columns(2)

                        subject_class_prefix_list = list(mapping_ns_dict.keys())
                        with col1a:
                            subject_class_prefix_list = list(mapping_ns_dict.keys())
                            subject_class_prefix_list.insert(0,"Select a namespace")
                            subject_class_prefix = st.selectbox("🖱️ Select a namespace:*", subject_class_prefix_list,
                                key="key_subject_class_prefix")

                        if not mapping_ns_dict:
                            with col1a:
                                st.write("")
                                st.markdown(f"""<div class="error-message">
                                        ❌ No namespaces available. You can add namespaces in the
                                         <b>Global Configuration</b> page.
                                    </div>""", unsafe_allow_html=True)
                        else:
                            if subject_class_prefix != "Select a namespace":
                                NS = Namespace(mapping_ns_dict[subject_class_prefix])
                            with col1b:
                                subject_class_input = st.text_input("⌨️ Enter subject class:*", key="key_subject_class_input")
                            if subject_class_input and subject_class_prefix != "Select a namespace":
                                subject_class = NS[subject_class_input]
                                with col1a:
                                    st.button("Save", on_click=save_external_subject_class)


            #GRAPH - If not given, default graph    HERE condider if rr:graphMap option (dynamic) is worth it
            if sm_config_selected_option == "🗺️️ Graph map":

                with col1:
                    col1a, col1b = st.columns([2,1])
                # with col1b:
                #     st.markdown(f"""<div class="info-message-gray">
                #             <b> 🗺️️ Graph map </b>: <br>
                #              Indicates the target graph for the subject map triples.
                #         </div>""", unsafe_allow_html=True)
                #     st.write("")


                subject_graph = st.session_state["g_mapping"].value(sm_iri_for_config, RR["graph"])

                if subject_graph:    #subject graph already given
                    with col1a:
                        st.markdown(f"""<div class="gray-preview-message">
                                🔒 Subject graph:
                                <b style="color:#F63366;">{split_uri(subject_graph)[1]}</b><br>
                                <small>Delete it to assign a different subject graph.</small>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        st.write("")

                    with col1a:
                        delete_subject_graph_checkbox = st.checkbox(
                        ":gray-badge[⚠️ I am completely sure I want to delete the subject graph]",
                        key="key_delete_subject_graph_checkbox")
                    if delete_subject_graph_checkbox:
                        with col1a:
                            st.button("Delete", on_click=delete_subject_graph)

                else:       #subject graph not given
                    with col1a:
                        st.markdown(f"""<div class="gray-preview-message">
                                🔓 Subject graph:
                                <b style="color:#F63366;">not given</b><br>
                                <small>Enter below. If no graph map is given, the default graph will be used.
                            </small></div>""", unsafe_allow_html=True)
                        st.write("")

                    with col1:
                        col1a, col1b = st.columns(2)

                    with col1a:
                        mapping_ns_dict = utils.get_mapping_ns_dict()
                        subject_graph_prefix_list = list(mapping_ns_dict.keys())
                        subject_graph_prefix_list.insert(0,"Select a namespace")
                        subject_graph_prefix = st.selectbox("🖱️ Select a namespace:*", subject_graph_prefix_list,
                            key="key_subject_graph_prefix")

                        if not mapping_ns_dict:
                            st.write("")
                            st.markdown(f"""<div class="error-message">
                                    ❌ No namespaces available. You can add namespaces in the
                                     <b>Global Configuration</b> page.
                                </div>""", unsafe_allow_html=True)
                        else:
                            with col1b:
                                subject_graph_input = st.text_input("🖱️ Enter subject graph:*", key="key_subject_graph_input")
                            if subject_graph_prefix != "Select a namespace":
                                NS = Namespace(mapping_ns_dict[subject_graph_prefix])

                            if subject_graph_input and subject_graph_prefix != "Select a namespace":
                                subject_graph = NS[subject_graph_input]
                                with col1a:
                                    st.button("Save", on_click=save_subject_graph, key="key_save_subject_graph_button")




    if st.session_state["labelled_sm_deleted_ok_flag"]:
        with col2b:
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>Subject Map/s</b> have been deleted!
            </div>""", unsafe_allow_html=True)
        st.session_state["labelled_sm_deleted_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()


    if st.session_state["sm_unassigned_ok_flag"]:
        with col2b:
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>Subject Map/s</b> have been unassigned!
            </div>""", unsafe_allow_html=True)
        st.session_state["sm_unassigned_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    # PURPLE HEADING - REMOVE EXISTING SUBJECT MAP
    sm_list = list(st.session_state["g_mapping"].objects(predicate=RR.subjectMap))
    tm_dict = utils.get_tm_dict()
    sm_dict = utils.get_sm_dict()

    if sm_list:    # only show option if there are sm to remove
        with col1:
            st.write("_____")
            st.markdown("""<div class="purple-heading">
                    🗑️ Remove existing Subject Map
                </div>""", unsafe_allow_html=True)
            st.write("")


        tm_w_sm_list = ["Select a TriplesMap"]
        for tm_label, tm_iri in tm_dict.items():
            if any(st.session_state["g_mapping"].triples((tm_iri, RR.subjectMap, None))):
                tm_w_sm_list.append(tm_label)

        with col1:
            col1a, col1b = st.columns([2,1])

        labelled_sm_list = [sm for sm in sm_list if isinstance(sm, URIRef)]
        labelled_sm_dict = {}
        for sm in labelled_sm_list:
            labelled_sm_dict[split_uri(sm)[1]] = sm

        if labelled_sm_list:    # if there exist labelled sm
            remove_sm_options_list = ["🔖 Delete labelled Subject Map", "🎯 Unassign Subject Map of a TriplesMap"]
            with col1a:
                remove_sm_selected_option = st.radio("", remove_sm_options_list, label_visibility="collapsed",
                    key="key_remove_sm_selected_option")
        else:            # no labelled sm
            remove_sm_selected_option = "🎯 Unassign Subject Map of a TriplesMap"


        if remove_sm_selected_option == "🔖 Delete labelled Subject Map":

            sm_to_choose_list = list(reversed(labelled_sm_dict.keys()))
            if len(sm_to_choose_list) > 1:
                sm_to_choose_list.insert(0, "Select all")
            with col1a:
                sm_to_remove_label_list = st.multiselect("🖱️ Select labelled Subject Map/s:*", sm_to_choose_list, key="key_sm_to_remove_label")
            sm_to_remove_iri_list = [labelled_sm_dict[sm] for sm in sm_to_remove_label_list if not sm == "Select all"]

            if "Select all" in sm_to_remove_label_list:
                sm_to_remove_iri_list = labelled_sm_list
                sm_to_remove_label_list = list(reversed(labelled_sm_dict.keys()))

            if not sm_to_remove_label_list:
                with col1b:
                    st.markdown(f"""<div class="info-message-gray">
                            ℹ️ The selected <b>Subject Maps</b> will be deleted
                            <small>(and therefore unassigned from their <b>TriplesMaps</b>).</small>
                        </div>""", unsafe_allow_html=True)
                    st.write("")

            # create a single info message
            max_length = utils.get_max_length_for_display()[4]
            inner_html = f"""<div style="margin-bottom:1px;">
                    <b>Subject Map</b> →
                    <b>TriplesMaps</b>
                </div>"""

            for sm in sm_to_remove_iri_list[:max_length]:
                sm_label_to_remove = sm_dict[sm][0]
                corresponding_tm_list = sm_dict[sm][4]
                if len(corresponding_tm_list) > 1:
                    formatted_corresponding_tm = ", ".join(corresponding_tm_list[:-1]) + " and " + corresponding_tm_list[-1]
                    inner_html += f"""<div style="margin-bottom:1px;">
                        <small>🔖 <b>{sm_label_to_remove}</b> → {formatted_corresponding_tm}</small>
                    </div>"""
                elif len(corresponding_tm_list) == 1:
                    inner_html += f"""<div style="margin-bottom:1px;">
                        <small>🔖 <b>{sm_label_to_remove}</b> → {corresponding_tm_list[0]}</small>
                    </div>"""
                else:
                    inner_html += f"""<div style="margin-bottom:1px;">
                        <small>❌ The Subject Map <b>{sm_label_to_remove}</b> is not assigned to any TriplesMap.
                        Please check your mapping.</small>
                    </div>"""


            if len(sm_to_remove_iri_list) > max_length:   # many sm to remove
                inner_html += f"""<div style="margin-bottom:1px;">
                    <small>🔖 ... (+{len(sm_to_remove_iri_list[:max_length])})</small>
                </div>"""

            # wrap it all in a single info box
            full_html = f"""<div class="info-message-small">
                {inner_html}</div>"""

            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                if sm_to_remove_label_list:
                    st.markdown(f"""<div class="info-message-gray">
                            {inner_html}
                        </div>""", unsafe_allow_html=True)
                    st.write("")

            # render
            if sm_to_remove_iri_list:


                inner_html = ""
                sm_to_remove_label_list_mod = [sm for sm in sm_to_remove_label_list if sm != "Select all"]
                formatted_sm_to_remove = utils.format_list_for_markdown(sm_to_remove_label_list_mod)
                if len(sm_to_remove_label_list_mod) == 1:
                    inner_html += f"""ℹ️ The Subject Map <b>{formatted_sm_to_remove}</b> will be completely removed."""
                elif len(sm_to_remove_label_list_mod) > 1:
                    inner_html += f"""ℹ️ The Subject Maps <b>{formatted_sm_to_remove}</b> will be completely removed."""

                with col1b:
                    st.markdown(f"""<div class="info-message-blue">
                            {inner_html}
                        <div>""", unsafe_allow_html=True)


                if "Select all" in sm_to_remove_label_list:
                    with col1b:
                        st.markdown(f"""<div class="warning-message">
                                ⚠️ You are deleting <b>all labelled Subject Maps</b>.
                                <small>Make sure you want to go ahead.</small>
                            </div>""", unsafe_allow_html=True)
                        st.write("")
                if len(sm_to_remove_iri_list):
                    with col1a:
                        delete_labelled_sm_checkbox = st.checkbox(
                        ":gray-badge[⚠️ I am sure I want to delete the Subject Map/s]",
                        key="delete_labelled_sm_checkbox")
                    if delete_labelled_sm_checkbox:
                        st.session_state["sm_to_remove_label_list"] = sm_to_remove_label_list
                        with col1a:
                            st.button("Delete", on_click=delete_labelled_sm, key="key_delete_labelled_sm_button")

        if remove_sm_selected_option == "🎯 Unassign Subject Map of a TriplesMap":

            tm_w_sm_list = []
            for tm_label, tm_iri in tm_dict.items():
                if any(st.session_state["g_mapping"].triples((tm_iri, RR.subjectMap, None))):
                    tm_w_sm_list.append(tm_label)


            with col1a:
                tm_w_sm_list_to_choose = list(reversed(tm_w_sm_list))
                if len(tm_w_sm_list_to_choose) > 1:
                    tm_w_sm_list_to_choose.insert(0, "Select all")
                tm_to_unassign_sm_list_input = st.multiselect("🖱️ Select TriplesMap/s:*", tm_w_sm_list_to_choose, key="key_tm_to_unassign_sm")

                if "Select all" in tm_to_unassign_sm_list_input:
                    tm_to_unassign_sm_list = tm_w_sm_list
                else:
                    tm_to_unassign_sm_list = tm_to_unassign_sm_list_input

            if not tm_to_unassign_sm_list_input:
                with col1b:
                    st.markdown(f"""<div class="info-message-gray">
                            ℹ️ The selected <b>Subject Maps</b> will be detached from their
                            <b>TriplesMaps</b>, and permanently removed
                            <small>(unless they are assigned to another TriplesMap).</small>
                        </div>""", unsafe_allow_html=True)
                    st.write("")

            # create a single info message
            max_length = utils.get_max_length_for_display()[4]
            inner_html = f"""<div style="margin-bottom:1px;">
                    <b>TriplesMap</b> → <b>Subject Map</b> →
                    <b>Linked TriplesMaps (if any)</b>
                </div>"""

            for tm in tm_to_unassign_sm_list[:max_length]:
                tm_iri = tm_dict[tm]
                sm_iri = st.session_state["g_mapping"].value(subject=tm_iri, predicate=RR.subjectMap)
                sm_label_to_unassign = sm_dict[sm_iri][0]
                other_tm_with_sm = [split_uri(s)[1] for s, p, o in st.session_state["g_mapping"].triples((None, RR.subjectMap, sm_iri)) if s != tm_iri]
                if other_tm_with_sm:
                    if len(other_tm_with_sm) > 1:
                        formatted_corresponding_tm = ", ".join(other_tm_with_sm[:-1]) + " and " + other_tm_with_sm[-1]
                    else:
                        formatted_corresponding_tm = other_tm_with_sm[0]
                    inner_html += f"""<div style="margin-bottom:1px;">
                        <small>🔖 {tm} → <b>{sm_label_to_unassign}</b> → {formatted_corresponding_tm}</small>
                    </div>"""
                else:
                    inner_html += f"""<div style="margin-bottom:1px;">
                        <small>🔖 {tm} →  <b>{sm_label_to_unassign}</b></small>
                    </div>"""

            if len(tm_to_unassign_sm_list) > max_length:   # many sm to remove
                inner_html += f"""<div style="margin-bottom:1px;">
                    <small>🔖 ... (+{len(tm_to_unassign_sm_list[:max_length])})</small>
                </div>"""

            # render
            with col1:
                col1a, col1b = st.columns([2,1])
            if tm_to_unassign_sm_list:
                with col1a:
                    st.markdown(f"""<div class="info-message-gray">
                            {inner_html}
                        </div>""", unsafe_allow_html=True)
            with col1a:
                st.write("")



            sm_to_completely_remove_list = []
            sm_to_just_unassign_list = []
            for tm in tm_to_unassign_sm_list:
                tm_iri = tm_dict[tm]
                sm_iri = st.session_state["g_mapping"].value(subject=tm_iri, predicate=RR.subjectMap)
                sm_label_to_unassign = sm_dict[sm_iri][0]
                other_tm_with_sm = [split_uri(s)[1] for s, p, o in st.session_state["g_mapping"].triples((None, RR.subjectMap, sm_iri)) if s != tm_iri]
                if all(tm in tm_to_unassign_sm_list for tm in other_tm_with_sm):   # if upon deletion sm is no longer assigned to any tm
                    if sm_label_to_unassign not in sm_to_completely_remove_list:
                        sm_to_completely_remove_list.append(sm_label_to_unassign)
                else:
                    sm_to_just_unassign_list.append(sm_label_to_unassign)

            # warning messages
            inner_html = ""
            formatted_tm_to_unassign_sm = utils.format_list_for_markdown(tm_to_unassign_sm_list)
            formatted_sm_to_completely_remove = utils.format_list_for_markdown(sm_to_completely_remove_list)
            formatted_sm_to_just_unassign = utils.format_list_for_markdown(sm_to_just_unassign_list)

            max_length = utils.get_max_length_for_display()[5]
            if len(sm_to_just_unassign_list) == 1:
                inner_html += f"""ℹ️ The Subject Map <b>{formatted_sm_to_just_unassign}</b> will be unassigned from
                its TriplesMap.<br>"""
            elif sm_to_just_unassign_list and len(sm_to_just_unassign_list) < max_length:
                inner_html += f"""ℹ️ The Subject Maps <b>{formatted_sm_to_just_unassign}</b> will be unassigned from
                their TriplesMaps</b>.<br>"""
            elif sm_to_just_unassign_list:
                inner_html += f"""ℹ️ <b>{len(sm_to_just_unassign_list)} Subject Maps</b> will be unassigned from
                their TriplesMaps.<br>"""
            if len(sm_to_completely_remove_list) == 1:
                inner_html += f"""ℹ️ The Subject Map <b>{formatted_sm_to_completely_remove}</b> will be completely removed."""
            elif sm_to_completely_remove_list and len(sm_to_completely_remove_list) < max_length:
                inner_html += f"""ℹ️ The Subject Maps <b>{formatted_sm_to_completely_remove}</b> will be completely removed."""
            elif sm_to_completely_remove_list:
                inner_html += f"""ℹ️ <b>{len(sm_to_completely_remove_list)} Subject Maps</b> will be completely removed."""

            if tm_to_unassign_sm_list:
                with col1b:
                    st.markdown(f"""<div class="info-message-blue">
                            {inner_html}
                        <div>""", unsafe_allow_html=True)


            if "Select all" in tm_to_unassign_sm_list_input:
                with col1b:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ You are deleting <b>all Subject Maps</b>.
                            <small>Make sure you want to go ahead.</small>
                        </div>""", unsafe_allow_html=True)


            if tm_to_unassign_sm_list:
                with col1a:
                    unassign_sm_checkbox = st.checkbox(
                    ":gray-badge[⚠️ I am sure I want to unassign the Subject Map/s]",
                    key="key_unassign_sm_checkbox")
                if unassign_sm_checkbox:
                    st.session_state["sm_to_completely_remove_list"] = sm_to_completely_remove_list
                    st.session_state["tm_to_unassign_sm_list"] = tm_to_unassign_sm_list
                    with col1a:
                        st.button("Unassign", on_click=unassign_sm, key="key_unassign_sm_button")




#________________________________________________
#ADD PREDICATE-OBJECT MAP TO MAP
with tab3:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
    with col2b:
        utils.get_corner_status_message()
        st.write("")

    tm_dict = utils.get_tm_dict()
    pom_dict = utils.get_pom_dict()

    with col2b:
        st.write("")
        rows = [{"TriplesMap": pom_dict[pom_iri][1], "P-O Map": pom_dict[pom_iri][2],
                "Predicate": pom_dict[pom_iri][4], "Object Map": pom_dict[pom_iri][5],
                "Rule": pom_dict[pom_iri][6], "ID/Constant": pom_dict[pom_iri][8]}
                for pom_iri, tm in st.session_state["last_added_pom_list"]]
        last_added_tm_df = pd.DataFrame(rows)
        last_last_added_tm_df = last_added_tm_df.head(utils.get_max_length_for_display()[1])

        if st.session_state["last_added_pom_list"]:
            st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                    🔎 last added Predicate-Object Maps
                </div>""", unsafe_allow_html=True)
            st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                    (complete list in <b>Display Mapping</b> page)
                </div>""", unsafe_allow_html=True)
            st.dataframe(last_last_added_tm_df, hide_index=True)
            st.write("")


    #PURPLE HEADING - ADD NEW TRIPLESMAP
    with col1:
        st.markdown("""<div class="purple-heading">
                🧱 Add New Predicate-Object Map
            </div>""", unsafe_allow_html=True)
        st.write("")



    #POM_____________________________________________________
    with col1:
        col1a, col1b = st.columns(2)


    #list of all triplesmaps with assigned Subject Map
    tm_w_sm_list = []
    for tm_label, tm_iri in tm_dict.items():
        if any(st.session_state["g_mapping"].triples((tm_iri, RR.subjectMap, None))):
            tm_w_sm_list.append(tm_label)

    if not tm_dict:
        with col1a:
            st.markdown(f"""<div class="error-message">
                    ❌ No TriplesMaps in mapping <b>{st.session_state["g_label"]}</b>.
                    You can add new TriplesMaps in the <b>Add TriplesMap</b> option.
                </div>""", unsafe_allow_html=True)
            st.write("")

    else:

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

            tm_iri_for_pom = tm_dict[tm_label_for_pom]

            with col1b:
                st.write("")
                column_list = utils.get_column_list_and_give_info(tm_iri_for_pom)

            sm_dict = utils.get_sm_dict()

            if not tm_label_for_pom in tm_w_sm_list:
                sm_label_for_pom = ""
                with col1a:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ TriplesMap <b>{tm_label_for_pom}</b> has no Subject Map.
                            <small>It will be invalid without one.</small>
                        </div>""", unsafe_allow_html=True)
                    st.write("")
            else:
                for sm in sm_dict:
                    if tm_label_for_pom in sm_dict[sm][4]:
                        sm_label_for_pom = sm_dict[sm][0]
                        break
                    sm_label_for_pom = ""


            # HERE CREATE THE PREDICATE MAP

            col1, col2, col3 = st.columns([1.5,0.2,2])

            with col1:
                st.markdown("""<div class="gray-heading">
                        🏗️ Create the Predicate Map</dic><br>
                    """,unsafe_allow_html=True)
                st.write("")


            with col1:
                col1a, col1b = st.columns([2.5,1])
            with col1a:
                pom_label = st.text_input("⌨️ Enter Predicate-Object Map label (optional):", key= "key_pom_label")
                NS = st.session_state["structural_ns_dict"]["Predicate-Object Map"][1]
                pom_iri = BNode() if not pom_label else NS[pom_label]
            if next(st.session_state["g_mapping"].triples((None, RR.predicateObjectMap, pom_iri)), None):
                with col1a:
                    st.markdown(f"""<div class="error-message">
                        ❌ That <b>Predicate-Object Map label</b> is already in use. Please pick another label or leave blank.
                    </div>""", unsafe_allow_html=True)

            if st.session_state["g_ontology_components_dict"]:
                ontology_p_list = utils.get_ontology_defined_p()

                if ontology_p_list:   # if the ontology includes at least one predicate
                    p_type_option_list = ["🧩 Ontology predicate", "🚫 Predicate outside ontology"]
                    with col1:
                        p_type = st.radio("Select an option:", p_type_option_list,
                            label_visibility="collapsed", key="key_p_type_radio")
                else:
                    p_type = "🚫 Predicate outside ontology"

            else:   # no ontology
                p_type = "🚫 Predicate outside ontology"

            if p_type == "🧩 Ontology predicate":

                with col1:
                    col1a, col1b = st.columns([2,1])

                ontology_p_dict = {split_uri(p)[1]: p for p in ontology_p_list}

                with col1a:
                    list_to_choose = list(ontology_p_dict.keys())
                    list_to_choose.insert(0, "Select a predicate")
                    selected_p_label = st.selectbox("🖱️ Select a predicate:*", list_to_choose, key="key_selected_p_label")

                if selected_p_label != "Select a predicate":
                    selected_p_iri = ontology_p_dict[selected_p_label]

            if p_type == "🚫 Predicate outside ontology":
                mapping_ns_dict = utils.get_mapping_ns_dict()

                if not mapping_ns_dict:
                    with col1:
                        col1a, col1b = st.columns([2,1])
                    with col1:
                        st.markdown(f"""<div class="error-message">
                                ❌ You must add namespaces in the <b>Global Configuration</b> page.
                            </div>""", unsafe_allow_html=True)
                        st.write("")

                with col1:
                    col1a, col1b = st.columns([1,1.5])

                with col1a:
                    list_to_choose = list(mapping_ns_dict.keys())
                    list_to_choose.insert(0, "Select a namespace")
                    manual_p_ns_prefix = st.selectbox("🖱️ Select a namespace:*", list_to_choose, key="key_manual_p_ns_prefix")

                with col1b:
                    manual_p_label = st.text_input("⌨️ Enter a predicate:*", key="key_manual_p_label")

                if manual_p_ns_prefix != "Select a namespace" and manual_p_label:
                    NS = Namespace(mapping_ns_dict[manual_p_ns_prefix])
                    selected_p_iri = NS[manual_p_label]

            if not st.session_state["g_ontology_label"]:
                with col1:
                    st.markdown("""<div class="warning-message">
                            ⚠️ <b>Working without an ontology</b> could result in structural inconsistencies.
                        <small>
                            This is especially discouraged when building Predicate-Object Maps.
                        </small></span>""", unsafe_allow_html=True)


            # BUILD OBJECT MAP_______________________________________________
            with col3:
                st.markdown("""<div class="gray-heading">
                        🏗️ Create the Object Map</div><br>
                    """,unsafe_allow_html=True)


            with col3:
                col3a, col3b = st.columns([2,1])
            with col3a:
                st.write("")
                om_label = st.text_input("⌨️ Enter Object Map label (optional):", key= "key_om_label")
            NS = st.session_state["structural_ns_dict"]["Object Map"][1]
            om_iri = BNode() if not om_label else NS[om_label]
            if next(st.session_state["g_mapping"].triples((None, RR.objectMap, om_iri)), None):
                with col3a:
                    st.markdown(f"""<div class="error-message">
                        ❌ That <b>Object Map label</b> is already in use. Please pick another label or leave blank.
                    </div>""", unsafe_allow_html=True)

            om_generation_rule_list = ["Template 📐", "Constant 🔒", "Reference 📊"]

            with col3:
                om_generation_rule = st.radio("🖱️ Define the Object Map generation rule:*",
                    om_generation_rule_list, horizontal=True, key="key_om_generation_rule_radio")

            #_______________________________________________
            # OBJECT MAP - TEMPLATE-VALUED
            if om_generation_rule == "Template 📐":

                with col3:
                    col3a, col3b = st.columns([1,1.5])
                with col3a:
                    build_template_action_om = st.selectbox("🖱️ Add template part:",
                        ["🏷️ Add Namespace", "🔒 Add fixed part", "📈 Add variable part", "🗑️ Reset template"],
                        key="key_build_template_action_om")


                if build_template_action_om == "🔒 Add fixed part":
                    with col3b:
                        om_template_fixed_part = st.text_input("⌨️ Enter fixed part:", key="key_om_fixed_part")
                        if re.search(r"[ \t\n\r<>\"{}|\\^`]", om_template_fixed_part):
                            st.markdown(f"""<div class="warning-message">
                                    ⚠️ You included a space or an unescaped character, which is discouraged.
                                </div>""", unsafe_allow_html=True)
                            st.write("")
                        if om_template_fixed_part:
                            st.button("Add", key="key_save_om_template_fixed_part_button", on_click=save_om_template_fixed_part)

                elif build_template_action_om == "📈 Add variable part":
                    with col3b:
                        if not column_list:   #data source is not available (load)
                            om_template_variable_part = st.text_input("⌨️ Manually enter column of the data source:*", key="key_om_template_variable_part")
                            st.markdown("""<div style='text-align: right; font-size: 10.5px; color: #cc9a06; font-weight: bold; margin-top: -10px;'>
                                ⚠️ discouraged
                            </div>""", unsafe_allow_html=True)
                            if om_template_variable_part:
                                save_om_template_variable_part_button = st.button("Add", key="save_om_template_variable_part_button", on_click=save_om_template_variable_part)

                        else:  # data source is available
                            list_to_choose = column_list.copy()
                            list_to_choose.insert(0, "Select a column")
                            om_template_variable_part = st.selectbox("🖱️ Select the column of the data source:", list_to_choose, key="key_om_template_variable_part")
                            if st.session_state["om_template_list"] and st.session_state["om_template_list"][-1].endswith("}"):
                                st.markdown(f"""<div class="warning-message">
                                        ⚠️ Including two adjacent variable parts is strongly discouraged.
                                        <small><b>Best practice:</b> Add a separator between variables to improve clarity.</small>
                                    </div>""", unsafe_allow_html=True)
                                st.write("")
                            if om_template_variable_part != "Select a column":
                                save_om_template_variable_part_button = st.button("Add", key="save_om_template_variable_part_button", on_click=save_om_template_variable_part)


                elif build_template_action_om == "🏷️ Add Namespace":
                    with col3b:
                        mapping_ns_dict = utils.get_mapping_ns_dict()
                        list_to_choose = list(mapping_ns_dict.keys())
                        list_to_choose.insert(0, "Select a namespace")
                        om_template_ns_prefix = st.selectbox("🖱️ Select a namespace for the template:", list_to_choose, key="key_om_template_ns_prefix")
                        if not mapping_ns_dict:
                            st.markdown(f"""<div class="error-message">
                                    ❌ No namespaces available. You can add namespaces in the
                                     <b>Global Configuration</b> page.
                                </div>""", unsafe_allow_html=True)


                        if om_template_ns_prefix != "Select a namespace":
                            om_template_ns = mapping_ns_dict[om_template_ns_prefix]
                            st.button("Add", key="key_add_ns_to_om_template_button", on_click=add_ns_to_om_template)


                elif build_template_action_om == "🗑️ Reset template":
                    with col3b:
                        st.write("")
                        st.markdown(f"""<div class="warning-message">
                                ⚠️ The current template will be deleted.
                            </div>""", unsafe_allow_html=True)
                        st.button("Reset", on_click=reset_om_template)

                with col3:
                    col3a, col3b = st.columns([3,1])
                with col3a:
                    om_template = "".join(st.session_state["om_template_list"])
                    if om_template:
                        st.write("")
                        st.markdown(f"""
                            <div class="gray-preview-message" style="word-wrap:break-word; overflow-wrap:anywhere;">
                                📐 <b>Your <b style="color:#F63366;">template</b> so far:</b><br>
                            <div style="margin-top:0.2em; font-size:15px; color:#333;">
                                    {om_template}
                            </div></div>""", unsafe_allow_html=True)
                        st.write("")
                    else:
                        st.write("")
                        st.markdown(f"""<div class="gray-preview-message">
                                📐 <b> Build your <b style="color:#F63366;">template</b> and preview it here.</b> <br>
                            <div style="font-size:13px; color:#666666; margin-top:0.2em;">
                                🛈 You can add as many parts as you need.
                            </div></div>""", unsafe_allow_html=True)
                        st.write("")


                with col3b:
                    st.write("")
                    om_term_type_template = st.radio(label="🖱️ Select term type:*", options=["🌐 IRI", "📘 Literal", "👻 BNode"],
                        key="om_term_type_template")

                if om_term_type_template == "🌐 IRI" and not st.session_state["template_om_is_iri_flag"] and om_template:
                    with col3a:

                        st.markdown(f"""<div class="error-message">
                            ❌ Term type is <b>🌐 IRI</b>. <small>You must <b>add a namespace</b></small>.
                        </div>""", unsafe_allow_html=True)
                        st.write("")

                if om_term_type_template == "📘 Literal":
                    rdf_datatypes = list(utils.get_datatypes_dict().keys())

                    with col3:
                        col3a, col3b = st.columns(2)
                    with col3a:
                        om_datatype = st.selectbox("🖱️ Select datatype (optional):", rdf_datatypes,
                            key="key_om_datatype")

                    if om_datatype == "Natural language text":
                        language_tags = utils.get_language_tags_list()

                        with col3b:
                            st.write("")
                            om_language_tag = st.selectbox("🖱️ Select language tag:*", language_tags,
                                key="key_om_language_tag")



            #_______________________________________________
            # OBJECT MAP - CONSTANT-VALUED
            if om_generation_rule == "Constant 🔒":

                with col3:
                    col3a, col3b = st.columns(2)
                with col3a:
                    om_constant = st.text_input("⌨️ Enter constant:*", key="key_om_constant")

                with col3b:
                    om_term_type_constant = st.radio(label="🖱️ Select term type:*", options=["📘 Literal", "🌐 IRI"], horizontal=True,
                        key="om_term_type_constant")

                if om_constant and om_term_type_constant == "🌐 IRI":
                    mapping_ns_dict = utils.get_mapping_ns_dict()
                    list_to_choose = list(mapping_ns_dict.keys())
                    list_to_choose.insert(0, "Select a namespace")
                    with col3a:
                        om_constant_ns_prefix = st.selectbox("🖱️ Select a namespace for the constant:*", list_to_choose,
                            key="key_om_constant_ns")

                    if not mapping_ns_dict:
                        with col3b:
                            st.markdown(f"""<div class="error-message">
                                    ❌ You must add namespaces in
                                    the <b>Global Configuration</b> page.
                                </div>""", unsafe_allow_html=True)

                if om_term_type_constant == "📘 Literal":
                    rdf_datatypes = list(utils.get_datatypes_dict().keys())


                    with col3:
                        col3a, col3b = st.columns(2)
                    with col3a:
                        om_datatype = st.selectbox("🖱️ Select datatype (optional):", rdf_datatypes,
                            key="key_om_datatype")

                    if om_datatype == "Natural language text":
                        language_tags = utils.get_language_tags_list()

                        with col3b:
                            om_language_tag = st.selectbox("🖱️ Select language tag:*", language_tags,
                                key="key_om_language_tag")

            #_______________________________________________
            #OBJECT MAP - REFERENCED-VALUED
            if om_generation_rule ==  "Reference 📊":
                om_datatype = ""
                om_language_tag = ""
                om_ready_flag_reference = False


                with col3:
                    col3a, col3b, col3c = st.columns([1.5,0.1,1])

                if not column_list:   #data source is not available (load)
                    with col3a:
                        om_column_name = st.text_input("⌨️ Manually enter column of the data source:*", key="key_om_column_name")
                        st.markdown("""<div style='text-align: right; font-size: 10.5px; color: #cc9a06; font-weight: bold; margin-top: -10px;'>
                            ⚠️ discouraged
                        </div>""", unsafe_allow_html=True)
                else:
                    with col3a:
                        list_to_choose = column_list.copy()
                        list_to_choose.insert(0, "Select a column")
                        om_column_name = st.selectbox(f"""🖱️ Select the column of the data source:*""", list_to_choose,
                            key="key_om_column_name")

                # if not column_list:   #data source is not available (load)
                #     with col3b:
                #         st.write("")
                #         if not ds_file_for_pom:
                #             st.markdown(f"""<div class="error-message">
                #                     ❌ You must load the
                #                     <b>data source file</b> to continue.
                #                 </div>""", unsafe_allow_html=True)
                #         else:
                #             st.markdown(f"""<div class="error-message">
                #                 ❌ Please upload the correct <b>data source file</b> to continue.
                #                 </div>""", unsafe_allow_html=True)
                #
                #
                # else:

                with col3c:
                    om_term_type_reference = st.radio(label="🖱️ Select Term type:*", options=["📘 Literal", "🌐 IRI", "👻 BNode"],
                        horizontal=True, key="om_term_type_reference")

                if om_term_type_reference == "📘 Literal":
                    rdf_datatypes = list(utils.get_datatypes_dict().keys())

                    with col3:
                        col3a, col3b = st.columns(2)
                    with col3a:
                        om_datatype_reference = st.selectbox("🖱️ Select datatype (optional):", rdf_datatypes,
                        key="key_om_datatype_reference")

                    if om_datatype_reference == "Natural language text":
                        language_tags = utils.get_language_tags_list()

                        with col3b:
                            om_language_tag_reference = st.selectbox("🖱️ Select language tag*", language_tags,
                                key="key_om_language_tag_reference")

                elif om_column_name != "Select a column" and om_term_type_reference == "🌐 IRI":
                    with col3b:
                        st.markdown(f"""<div class="warning-message">
                                ⚠️ Term type is <b>🌐 IRI</b>.
                                <small>Make sure that the values in the referenced column
                                are valid IRIs.</small>
                            </div>""", unsafe_allow_html=True)
                        st.write("")

        if tm_label_for_pom != "Select a TriplesMap":

            st.write("")
            st.markdown("""<div class="gray-heading">
                💾 Check and save Predicate-Object Map</div><br>
            """, unsafe_allow_html=True)

            if st.session_state["pom_saved_ok_flag"]:
                with col1:
                    st.write("")
                    st.markdown(f"""<div class="success-message-flag">
                        ✅ The <b style="color:#F63366;">Predicate-Object Map</b> has been created!
                    </div>""", unsafe_allow_html=True)
                st.session_state["pom_saved_ok_flag"] = False
                time.sleep(st.session_state["success_display_time"])
                st.rerun()

            col1, col2, col3, col4 = st.columns([1,1,0.2,1])

            # POM MAP ______________________________________
            inner_html = f"""<tr class="title-row"><td colspan="2">🔎 Predicate-Object Map</td></tr>
                <tr><td><b>TriplesMap*:</b></td><td>{tm_label_for_pom}</td></tr>
                <tr><td><b>Subject Map</b></td><td>{sm_label_for_pom}</td></tr>"""

            if next(st.session_state["g_mapping"].triples((None, RR.predicateObjectMap, pom_iri)), None):
                pom_complete_flag = "❌ No"
                inner_html += f"""<tr><td><b>Predicate-Object Map label</b></td>
                <td>{pom_label} <span style='font-size:11px; color:#888;'>(❌ already in use)</span></td></tr>"""
            else:
                inner_html += f"""<tr><td><b>Predicate-Object Map label</b></td><td>{pom_label}</td></tr>"""

            if p_type == "🧩 Ontology predicate":

                pom_complete_flag = "✔️ Yes" if selected_p_label != "Select a predicate" else "❌ No"
                selected_p_label_display = selected_p_label if selected_p_label != "Select a predicate" else ""
                if selected_p_label != "Select a predicate":
                    p_ont = utils.get_ontology_identifier(selected_p_iri)
                    selected_p_label_display += " (" + p_ont + ")" if p_ont else selected_p_label_display

                inner_html += f"""<tr><td><b>Predicate*</b></td><td>{selected_p_label_display}</td></tr>"""

            elif p_type == "🚫 Predicate outside ontology":

                pom_complete_flag = "✔️ Yes" if (manual_p_label and manual_p_ns_prefix != "Select a namespace") else "❌ No"
                manual_p_ns_prefix_display = manual_p_ns_prefix if manual_p_ns_prefix != "Select a namespace" else ""

                inner_html += f"""<tr><td><b>Predicate Namespace*</b></td><td>{manual_p_ns_prefix_display}</td></tr>
                    <tr><td><b>Predicate*</b></td><td>{manual_p_label}</td></tr>"""

            inner_html += f"""<tr><td><b>Required fields complete</b></td><td>{pom_complete_flag}</td></tr>"""

            if p_type == "🚫 Predicate outside ontology":
                inner_html += f"""<tr><td colspan="2" style="font-size:12px; padding-top:6px;">
                    ⚠️ Manual predicate input is <b>discouraged</b>.
                    Use an ontology for safer results.</td></tr>"""

            full_html = f"""<table class="info-table-gray">
                    {inner_html}</table>"""
            # render
            with col1:
                st.markdown(full_html, unsafe_allow_html=True)



            # OBJECT MAP - TEMPLATE______________________________________________________-
            if om_generation_rule == "Template 📐":

                om_complete_flag = "✔️ Yes" if om_template else "❌ No"

                inner_html = f"""<tr class="title-row"><td colspan="2">🔎 Object Map</td></tr>"""

                if next(st.session_state["g_mapping"].triples((None, RR.objectMap, om_iri)), None):
                    om_complete_flag = "❌ No"
                    inner_html += f"""<tr><td><b>Object Map label</b></td>
                    <td>{om_label} <span style='font-size:11px; color:#888;'>(❌ already in use)</span></td></tr>"""
                else:
                    inner_html += f"""<tr><td><b>Object Map label</b></td><td>{om_label}</td></tr>"""


                inner_html += f"""<tr><td><b>Generation rule*</b></td><td>{om_generation_rule}</td></tr>
                <tr><td><b>Template*</b></td><td>{om_template}</td></tr>
                <tr><td><b>Term type*</b></td><td>{om_term_type_template}</td></tr>"""

                if om_term_type_template == "🌐 IRI":
                    om_template_ns_prefix_display = st.session_state["om_template_ns_prefix"] if st.session_state["template_om_is_iri_flag"] else ""
                    inner_html += f"""<tr><td><b>Template namespace*</b></td><td>{om_template_ns_prefix_display}</td></tr>"""
                    om_complete_flag = "❌ No" if not st.session_state["template_om_is_iri_flag"] else om_complete_flag

                if om_template and om_term_type_template == "📘 Literal":
                    om_datatype_display = om_datatype if om_datatype != "Select datatype" else ""
                    inner_html += f"""<tr><td><b>Datatype</b></td><td>{om_datatype_display}</td></tr>"""
                    if om_datatype == "Natural language text":
                        om_language_tag_display = om_language_tag if om_language_tag != "Select language tag" else ""
                        inner_html += f"""<tr><td><b>Language tag*</b></td><td>{om_language_tag_display}</td></tr>"""
                        om_complete_flag = "❌ No" if om_language_tag == "Select language tag" else om_complete_flag

                inner_html += f"""<tr><td><b>Required fields complete</b></td><td> {om_complete_flag} </td></tr>"""

                full_html = f"""<table class="info-table-gray">
                        {inner_html}</table>"""
                # render
                with col2:
                    st.markdown(full_html, unsafe_allow_html=True)


            # OBJECT MAP - CONSTANT____________________________________________
            if om_generation_rule == "Constant 🔒":   #HEREIGO

                om_complete_flag = "✔️ Yes" if om_constant else "❌ No"

                inner_html = f"""<tr class="title-row"><td colspan="2">🔎 Object Map</td></tr>"""

                if next(st.session_state["g_mapping"].triples((None, RR.objectMap, om_iri)), None):
                    om_complete_flag = "❌ No"
                    inner_html += f"""<tr><td><b>Object Map label</b></td>
                    <td>{om_label} <span style='font-size:11px; color:#888;'>(❌ already in use)</span></td></tr>"""
                else:
                    inner_html += f"""<tr><td><b>Object Map label</b></td><td>{om_label}</td></tr>"""

                    inner_html += f"""<tr><td><b>Generation rule*</b></td><td>{om_generation_rule}</td></tr>
                    <tr><td><b>Constant*</b></td><td>{om_constant}</td></tr>
                    <tr><td><b>Term type*</b></td><td>{om_term_type_constant}</td></tr>"""

                if om_term_type_constant == "📘 Literal":
                    om_datatype_display = om_datatype if om_datatype != "Select datatype" else ""
                    inner_html += f"""<tr><td><b>Datatype</b></td><td>{om_datatype_display}</td></tr>"""
                    if om_datatype == "Natural language text":
                        om_language_tag_display = om_language_tag if om_language_tag != "Select language tag" else ""
                        inner_html += f"""<tr><td><b>Language tag*</b></td><td>{om_language_tag_display}</td></tr>"""
                        om_complete_flag = "❌ No" if om_language_tag == "Select language tag" else om_complete_flag

                elif om_term_type_constant == "🌐 IRI":
                    om_complete_flag = "✔️ Yes" if (om_constant_ns_prefix != "Select a namespace" and om_constant) else "❌ No"
                    om_constant_ns_prefix_display = om_constant_ns_prefix if om_constant_ns_prefix != "Select a namespace" else ""
                    inner_html += f"""<tr><td><b>Constant namespace*</b></td><td>{om_constant_ns_prefix_display}</td></tr>"""

                inner_html += f"""<tr><td><b>Required fields complete</b></td><td> {om_complete_flag} </td></tr>"""

                full_html = f"""<table class="info-table-gray">
                        {inner_html}</table>"""
                # render
                with col2:
                    st.markdown(full_html, unsafe_allow_html=True)


            # OBJECT MAP - REFERENCE___________________________
            if om_generation_rule == "Reference 📊":

                if column_list:
                    om_complete_flag = "✔️ Yes" if om_column_name != "Select a column" else "❌ No"
                else:
                    om_complete_flag = "✔️ Yes" if om_column_name else "❌ No"
                om_column_name_display = om_column_name if om_column_name != "Select a column" else ""

                inner_html = f"""<tr class="title-row"><td colspan="2">🔎 Object Map</td></tr>"""

                if next(st.session_state["g_mapping"].triples((None, RR.objectMap, om_iri)), None):
                    om_complete_flag = "❌ No"
                    inner_html += f"""<tr><td><b>Object Map label</b></td>
                    <td>{om_label} <span style='font-size:11px; color:#888;'>(❌ already in use)</span></td></tr>"""
                else:
                    inner_html += f"""<tr><td><b>Object Map label</b></td><td>{om_label}</td></tr>"""

                inner_html += f"""<tr><td><b>Generation rule*</b></td><td>{om_generation_rule}</td></tr>
                <tr><td><b>Data source column*</b></td><td>{om_column_name_display}</td></tr>
                <tr><td><b>Term type*</b></td><td>{om_term_type_reference}</td></tr>"""


                if om_term_type_reference == "📘 Literal":
                    om_datatype_reference_display = om_datatype_reference if om_datatype_reference != "Select datatype" else ""
                    inner_html += f"""<tr><td><b>Datatype</b></td><td>{om_datatype_reference_display}</td></tr>"""
                    if om_datatype_reference == "Natural language text":
                        om_language_tag_reference_display = om_language_tag_reference if om_language_tag_reference != "Select language tag" else ""
                        om_complete_flag = "❌ No" if om_language_tag_reference == "Select language tag" else om_complete_flag
                        inner_html += f"""<tr><td><b>Language tag*</b></td><td>{om_language_tag_reference_display}</td></tr>"""

                inner_html += f"""<tr><td><b>Required fields complete</b></td><td> {om_complete_flag} </td></tr>"""

                full_html = f"""<table class="info-table-gray">
                        {inner_html}</table>"""
                # render
                with col2:
                    st.markdown(full_html, unsafe_allow_html=True)


            # INFO AND SAVE BUTTON____________________________________
            # if not st.session_state["g_ontology_label"]:
            #     with col4:
            #         st.markdown("""<div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
            #             <span style="font-size:0.95rem;">
            #                 🚧 Working without an ontology could result in structural inconsistencies.
            #             <small>
            #                 This is especially discouraged when building Predicate-Object Maps.
            #             </small></span>""", unsafe_allow_html=True)

            if pom_complete_flag == "✔️ Yes" and om_complete_flag == "✔️ Yes":
                with col4:
                    st.markdown(f"""<div class="success-message">
                        🧐  All <b>required fields (*)</b> are complete.
                        <small>Double-check the information before saving.</smalL> </div>
                    """, unsafe_allow_html=True)
                    st.write("")
                    st.session_state["pom_iri_to_create"] = pom_iri    # otherwise it will change value in the on_click function
                    st.session_state["tm_iri_for_pom"] = tm_iri_for_pom
                    if om_generation_rule == "Template 📐":
                        save_pom_template_button = st.button("Save", on_click=save_pom_template, key="key_save_pom_template_button")
                    elif om_generation_rule == "Constant 🔒":
                        save_pom_constant_button = st.button("Save", on_click=save_pom_constant, key="key_save_pom_constant_button")
                    elif om_generation_rule == "Reference 📊":
                        save_pom_reference_button = st.button("Save", on_click=save_pom_reference, key="key_save_pom_reference_button")
                    elif om_generation_rule == "BNode 👻":
                        save_pom_bnode_button = st.button("Save", on_click=save_bnode_bnode, key="key_save_pom_bnode_button")
            else:
                with col4:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ All <b>required fields (*)</b> must be filled in order to save the Subject Map.
                        </div>""", unsafe_allow_html=True)
                    st.write("")




            col1, col2 = st.columns([2,1.5])   # back to the normal structure of columns



    if st.session_state["pom_deleted_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The Predicate-Object Map/s have been deleted!
            </div>""", unsafe_allow_html=True)
            st.write("")
        st.session_state["pom_deleted_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()


    # PURPLE HEADING - REMOVE EXISTING PREDICATE-OBJECT MAP
    tm_dict = utils.get_tm_dict()
    pom_dict = utils.get_pom_dict()

    if pom_dict:
        with col1:
            st.write("________")
            st.markdown("""<div class="purple-heading">
                    🗑️ Remove Existing Predicate-Object Map
                </div>""", unsafe_allow_html=True)
            st.write("") #HERE ONLY IF THERE EXISTS ONE

        with col1:
            col1a, col1b = st.columns(2)

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

                with col1b:
                    list_to_choose = []
                    for pom_iri in pom_dict:
                        if pom_dict[pom_iri][0] == tm_to_delete_pom_iri:
                            list_to_choose.append(pom_dict[pom_iri][2])
                    list_to_choose = list(reversed(list_to_choose))
                    if len(list_to_choose) > 1:
                        list_to_choose.insert(0, "Select all")
                    pom_to_delete_label_list = st.multiselect("🖱️ Select a Predicate-Object Map:*", list_to_choose, key="key_pom_to_delete")
                    pom_to_delete_iri_list = []
                    pom_to_delete_all_iri_list = []
                    for pom_iri in pom_dict:
                        if "Select all" not in pom_to_delete_label_list and pom_dict[pom_iri][2] in pom_to_delete_label_list:
                            pom_to_delete_iri_list.append(pom_iri)
                        if "Select all" in pom_to_delete_label_list and pom_dict[pom_iri][0] == tm_to_delete_pom_iri:
                            pom_to_delete_all_iri_list.append(pom_iri)

                if pom_to_delete_label_list and "Select all" not in pom_to_delete_label_list:
                    with col1a:
                        delete_pom_checkbox = st.checkbox(
                        f""":gray-badge[⚠️ I am  sure I want to permanently remove this/these Predicate-Object Maps]""",
                        key="key_overwrite_g_mapping_checkbox_new")
                        if delete_pom_checkbox:
                            st.button("Delete", on_click=delete_pom, key="key_delete_pom_button")

                elif pom_to_delete_label_list and "Select all" in pom_to_delete_label_list:
                    with col1:
                        col1a, col1b = st.columns([2,1])
                    with col1a:
                        st.markdown(f"""<div class="warning-message">
                                ⚠️ You are deleting <b>all Predicate-Object Maps</b>
                                of the TriplesMap {tm_to_delete_pom_label}.
                                <small>Make sure you want to go ahead.</small>
                            </div>""", unsafe_allow_html=True)
                        st.write("")
                    with col1a:
                        delete_all_pom_checkbox = st.checkbox(
                        f""":gray-badge[⚠️ I am  sure I want to permanently remove all Predicate-Object Maps]""",
                        key="key_overwrite_g_mapping_checkbox_new")
                        if delete_all_pom_checkbox:
                            st.button("Delete", on_click=delete_all_pom, key="key_delete_all_pom_button")


        if tm_to_delete_pom_label != "Select a TriplesMap":


            rows = [{"P-O Map": pom_dict[pom_iri][2],
                    "Predicate": pom_dict[pom_iri][4], "Object Map": pom_dict[pom_iri][5],
                    "Rule": pom_dict[pom_iri][6], "ID/Constant": pom_dict[pom_iri][8]}
                    for pom_iri in pom_of_selected_tm_list]
            pom_of_selected_tm_df = pd.DataFrame(rows)


            st.write("")
            if pom_of_selected_tm_list:
                with col1:
                    st.markdown(f"""<div style='font-size: 14px; color: grey;'>
                            🔎 Predicate-Object Maps of TriplesMap {tm_to_delete_pom_label}
                        </div>""", unsafe_allow_html=True)
                    st.dataframe(pom_of_selected_tm_df, hide_index=True)
                    st.write("")

#________________________________________________

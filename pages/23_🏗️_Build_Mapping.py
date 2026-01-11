import langcodes
import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace, BNode
from rdflib.namespace import split_uri
from rdflib.namespace import RDF, RDFS
import re
import streamlit as st
import time
import utils

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
    # get required info
    NS = st.session_state["base_ns"][1]
    tm_iri = NS[f"{st.session_state['tm_label']}"]
    tm_label = utils.get_node_label(tm_iri)
    ls_iri =  NS[f"{existing_ls}"]
    # add triples___________________
    st.session_state["g_mapping"].add((tm_iri, RML.logicalSource, ls_iri))    # bind to logical source
    st.session_state["g_mapping"].add((tm_iri, RDF.type, RML.TriplesMap))
    # store information________________
    st.session_state["tm_saved_ok_flag"] = True  # for success message
    st.session_state["last_added_tm_list"].insert(0, tm_label)    # to display last added tm
    # reset fields_____________________
    st.session_state["key_tm_label_input"] = ""

def save_tm_w_tab_ls():
    # get required info
    NS = st.session_state["base_ns"][1]
    tm_iri = NS[f"{st.session_state['tm_label']}"]
    tm_label = utils.get_node_label(tm_iri)
    ds_filename = ds_file.name
    ls_iri = NS[f"{ls_label}"] if label_ls_option == "Yes (add label 🔖)" else BNode()
    # add triples__________________
    st.session_state["g_mapping"].add((tm_iri, RML.logicalSource, ls_iri))    # bind to logical source
    st.session_state["g_mapping"].add((ls_iri, RML.source, Literal(ds_filename)))    # bind ls to source file
    file_extension = ds_filename.rsplit(".", 1)[-1].lower()    # bind to reference formulation
    reference_formulation = utils.get_reference_formulation_dict()[file_extension]
    st.session_state["g_mapping"].add((ls_iri, QL.referenceFormulation, reference_formulation))
    st.session_state["g_mapping"].add((tm_iri, RDF.type, RML.TriplesMap))
    # store information____________________
    st.session_state["tm_saved_ok_flag"] = True  # for success message
    st.session_state["last_added_tm_list"].insert(0, tm_label)    # to display last added tm
    # reset fields_______________________
    st.session_state["key_tm_label_input"] = ""

def save_tm_w_view():
    # get required info
    [engine, host, port, database, user, password] = st.session_state["db_connections_dict"][db_connection_for_ls]
    url_str = utils.get_db_url_str(db_connection_for_ls)
    sql_query = st.session_state["saved_views_dict"][selected_view_for_ls][1]
    NS = st.session_state["base_ns"][1]
    tm_iri = NS[f"{st.session_state['tm_label']}"]
    tm_label = utils.get_node_label(tm_iri)
    ls_iri = NS[f"{ls_label}"] if label_ls_option == "Yes (add label 🔖)" else BNode()
    # add triples__________________
    st.session_state["g_mapping"].add((tm_iri, RML.logicalSource, ls_iri))    # bind to logical source
    st.session_state["g_mapping"].add((ls_iri, RML.source, Literal(url_str)))    # bind ls to database
    if engine != "MongoDB":
        st.session_state["g_mapping"].add((ls_iri, RML.referenceFormulation, RML.SQL2008))
    else:
        st.session_state["g_mapping"].add((ls_iri, RML.referenceFormulation, QL.JSONPath))
    st.session_state["g_mapping"].add((ls_iri, RML.query, Literal(sql_query)))
    st.session_state["g_mapping"].add((tm_iri, RDF.type, RML.TriplesMap))
    # store information____________________
    st.session_state["tm_saved_ok_flag"] = True  # for success message
    st.session_state["last_added_tm_list"].insert(0, tm_label)    # to display last added tm
    # reset fields_______________________
    st.session_state["key_tm_label_input"] = ""

def save_tm_w_table_name():
    [engine, host, port, database, user, password] = st.session_state["db_connections_dict"][db_connection_for_ls]
    url_str = utils.get_db_url_str(db_connection_for_ls)
    # add triples__________________
    NS = st.session_state["base_ns"][1]
    tm_iri = NS[f"{st.session_state['tm_label']}"]
    tm_label = utils.get_node_label(tm_iri)
    ls_iri = NS[f"{ls_label}"] if label_ls_option == "Yes (add label 🔖)" else BNode()
    st.session_state["g_mapping"].add((tm_iri, RML.logicalSource, ls_iri))    # bind to logical source
    st.session_state["g_mapping"].add((ls_iri, RML.source, Literal(url_str)))    # bind ls to database
    if engine != "MongoDB":
        st.session_state["g_mapping"].add((ls_iri, RML.referenceFormulation, RML.SQL2008))
    else:
        st.session_state["g_mapping"].add((ls_iri, RML.referenceFormulation, QL.JSONPath))
    st.session_state["g_mapping"].add((ls_iri, RML.tableName, Literal(selected_table_for_ls)))
    st.session_state["g_mapping"].add((tm_iri, RDF.type, RML.TriplesMap))
    # store information____________________
    st.session_state["tm_saved_ok_flag"] = True  # for success message
    st.session_state["last_added_tm_list"].insert(0, tm_label)    # to display last added tm
    # reset fields_______________________
    st.session_state["key_tm_label_input"] = ""

# TAB2
def save_sm_existing():
    # add triples____________________
    st.session_state["g_mapping"].add((tm_iri_for_sm, RML.subjectMap, st.session_state["sm_iri"]))
    # store information__________________
    st.session_state["last_added_sm_list"].insert(0, [st.session_state["sm_iri"], tm_label_for_sm])
    st.session_state["sm_saved_ok_flag"] = True

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

def add_ns_to_sm_template():
    # update template and store information_________
    if not st.session_state["sm_template_list"]:   # template empty yet
        st.session_state["sm_template_list"] = [sm_template_ns]
    elif not st.session_state["sm_template_is_iri_flag"]:    # no ns added yet
        st.session_state["sm_template_list"].insert(0, sm_template_ns)
    else:   # a ns was added (replace)
        st.session_state["sm_template_list"][0] = sm_template_ns
    st.session_state["sm_template_is_iri_flag"] = True
    # reset fields_____________
    st.session_state["key_sm_template_ns_prefix"] = "Select namespace"
    st.session_state["key_build_template_action_sm"] = "🔒 Fixed part"

def remove_ns_from_sm_template():
    # update template and store information_________
    st.session_state["sm_template_list"].pop(0)
    st.session_state["sm_template_is_iri_flag"] = False
    # reset fields_____________
    st.session_state["key_sm_template_ns_prefix"] = "Select namespace"
    st.session_state["key_build_template_action_sm"] = "🔒 Fixed part"

def reset_sm_template():
    # reset template___________________-
    st.session_state["sm_template_list"] = []
    # store information____________________
    st.session_state["sm_template_is_iri_flag"] = False
    st.session_state["sm_template_variable_part_flag"] = False
    # reset fields_____________
    st.session_state["key_build_template_action_sm"] = "🔒 Fixed part"

def save_sm_template():   #function to save subject map (template option)
    # get info_______________________
    NS = st.session_state["base_ns"][1]
    sm_iri = NS[sm_label] if label_sm_option == "Yes (add label 🔖)" else BNode()
    # add triples____________________
    st.session_state["g_mapping"].add((tm_iri_for_sm, RML.subjectMap, sm_iri))
    st.session_state["g_mapping"].add((sm_iri, RDF.type, RML.SubjectMap))
    st.session_state["g_mapping"].add((sm_iri, RML.template, Literal(sm_template)))
    # subject class_____________________
    ontology_class_dict = utils.get_ontology_class_dict(ontology_filter_for_subject_class)
    custom_class_dict = utils.get_ontology_class_dict("custom")
    for class_label in subject_class_list:
        if class_label in ontology_class_dict:
            subject_class_iri = ontology_class_dict[class_label]
        elif class_label in custom_class_dict:
            subject_class_iri = custom_class_dict[class_label]
        subject_class_iri = ontology_class_dict[class_label]
        st.session_state["g_mapping"].add((sm_iri, RML["class"], subject_class_iri))
    # graph map_____________________
    if add_sm_graph_map_option != "Default graph map":
        st.session_state["g_mapping"].add((sm_iri, RML.graphMap, sm_graph))
    # term type__________________________
    if sm_term_type == "🌐 IRI":
        st.session_state["g_mapping"].add((sm_iri, RML.termType, RML.IRI))
    elif sm_term_type == "👻 BNode":
        st.session_state["g_mapping"].add((sm_iri, RML.termType, RML.BlankNode))
    # store information__________________
    st.session_state["last_added_sm_list"].insert(0, [sm_iri, tm_label_for_sm])
    st.session_state["sm_saved_ok_flag"] = True
    st.session_state["sm_template_list"] = []
    st.session_state["sm_template_is_iri_flag"] = False
    st.session_state["sm_template_variable_part_flag"] = False
    # reset fields____________________
    st.session_state["key_tm_label_input_for_sm"] = "Select TriplesMap"

def save_sm_constant():   #function to save subject map (constant option)
    # get info_______________________
    NS = st.session_state["base_ns"][1]
    sm_iri = NS[sm_label] if label_sm_option == "Yes (add label 🔖)" else BNode()
    # add triples________________________
    st.session_state["g_mapping"].add((tm_iri_for_sm, RML.subjectMap, sm_iri))
    st.session_state["g_mapping"].add((sm_iri, RDF.type, RML.SubjectMap))
    if sm_constant_ns_prefix:
        sm_constant_ns = mapping_ns_dict[sm_constant_ns_prefix]
        NS = Namespace(sm_constant_ns)
        sm_constant_iri = NS[sm_constant]
    else:
        sm_constant_iri = URIRef(sm_constant)
    st.session_state["g_mapping"].add((sm_iri, RML.constant, sm_constant_iri))
    # subject class_____________________
    ontology_class_dict = utils.get_ontology_class_dict(ontology_filter_for_subject_class)
    custom_class_dict = utils.get_ontology_class_dict("custom")
    for class_label in subject_class_list:
        if class_label in ontology_class_dict:
            subject_class_iri = ontology_class_dict[class_label]
        elif class_label in custom_class_dict:
            subject_class_iri = custom_class_dict[class_label]
        subject_class_iri = ontology_class_dict[class_label]
        st.session_state["g_mapping"].add((sm_iri, RML["class"], subject_class_iri))
    # graph map_____________________
    if add_sm_graph_map_option != "Default graph map":
        st.session_state["g_mapping"].add((sm_iri, RML.graphMap, sm_graph))
    # term type__________________________
    st.session_state["g_mapping"].add((sm_iri, RML.termType, RML.IRI))
    # store information____________________
    st.session_state["last_added_sm_list"].insert(0, [sm_iri, tm_label_for_sm])
    st.session_state["sm_saved_ok_flag"] = True
    st.session_state["sm_template_list"] = []   # reset template in case it is not empty
    st.session_state["sm_template_prefix"] = ""
    st.session_state["sm_template_variable_part_flag"] = False
    # reset fields_________________________
    st.session_state["key_tm_label_input_for_sm"] = "Select TriplesMap"

def save_sm_reference():   #function to save subject map (reference option)
    # get info_______________________
    NS = st.session_state["base_ns"][1]
    sm_iri = NS[sm_label] if label_sm_option == "Yes (add label 🔖)" else BNode()
    # add triples____________________
    st.session_state["g_mapping"].add((tm_iri_for_sm, RML.subjectMap, sm_iri))
    st.session_state["g_mapping"].add((sm_iri, RDF.type, RML.SubjectMap))
    st.session_state["g_mapping"].add((sm_iri, RML.reference, Literal(sm_column_name)))
    # subject class_____________________
    ontology_class_dict = utils.get_ontology_class_dict(ontology_filter_for_subject_class)
    custom_class_dict = utils.get_ontology_class_dict("custom")
    for class_label in subject_class_list:
        if class_label in ontology_class_dict:
            subject_class_iri = ontology_class_dict[class_label]
        elif class_label in custom_class_dict:
            subject_class_iri = custom_class_dict[class_label]
        subject_class_iri = ontology_class_dict[class_label]
        st.session_state["g_mapping"].add((sm_iri, RML["class"], subject_class_iri))
    # graph map_____________________
    if add_sm_graph_map_option != "Default graph map":
        st.session_state["g_mapping"].add((sm_iri, RML.graphMap, sm_graph))
    # term type__________________________
    if sm_term_type == "🌐 IRI":
        st.session_state["g_mapping"].add((sm_iri, RML.termType, RML.IRI))
    elif sm_term_type == "👻 BNode":
        st.session_state["g_mapping"].add((sm_iri, RML.termType, RML.BlankNode))
    # store information__________________
    st.session_state["last_added_sm_list"].insert(0, [sm_iri, tm_label_for_sm])
    st.session_state["sm_saved_ok_flag"] = True
    st.session_state["sm_template_list"] = []   # reset template in case it is not empty
    st.session_state["sm_template_prefix"] = ""
    st.session_state["sm_template_variable_part_flag"] = False
    # reset fields____________________
    st.session_state["key_tm_label_input_for_sm"] = "Select TriplesMap"

# TAB3
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

def add_ns_to_om_template():
    # update template and store information_________
    if not st.session_state["om_template_list"]:   # empty template yet
        st.session_state["om_template_list"] = [om_template_ns]
    elif not st.session_state["om_template_is_iri_flag"]:    # no ns added yet
        st.session_state["om_template_list"].insert(0, om_template_ns)
    else:   # a ns was added (replace)
        st.session_state["om_template_list"][0] = om_template_ns
    st.session_state["om_template_is_iri_flag"] = True
    # reset fields_____________
    st.session_state["key_om_template_ns_prefix"] = "Select namespace"
    st.session_state["key_build_template_action_om"] = "🔒 Fixed part"

def remove_ns_from_om_template():
    # update template and store information_________
    st.session_state["om_template_list"].pop(0)
    st.session_state["om_template_is_iri_flag"] = False
    # reset fields_____________
    st.session_state["key_om_template_ns_prefix"] = "Select namespace"
    st.session_state["key_build_template_action_om"] = "🔒 Fixed part"

def reset_om_template():
    # reset template
    st.session_state["om_template_list"] = []
    # store information____________________
    st.session_state["om_template_is_iri_flag"] = False
    st.session_state["om_template_variable_part_flag"] = False
    # reset fields_____________
    st.session_state["key_build_template_action_om"] = "🔒 Fixed part"

def save_pom_template():
    # get info______________________________
    pom_iri = BNode()
    om_iri = BNode()
    # add triples pom________________________
    st.session_state["g_mapping"].add((st.session_state["tm_iri_for_pom"], RML.predicateObjectMap, pom_iri))
    for p_iri in predicate_iri_list:
        st.session_state["g_mapping"].add((pom_iri, RML.predicate, p_iri))
    st.session_state["g_mapping"].add((pom_iri, RML.objectMap, om_iri))
    st.session_state["g_mapping"].add((pom_iri, RDF.type, RML.PredicateObjectMap))
    # add triples om________________________
    st.session_state["g_mapping"].add((om_iri, RDF.type, RML.ObjectMap))
    st.session_state["g_mapping"].add((om_iri, RML.template, Literal(om_template)))
    # term type, datatype and language tag
    if om_term_type == "📘 Literal":
        st.session_state["g_mapping"].add((om_iri, RML.termType, RML.Literal))
        if om_datatype_option and om_datatype_option != "🈳 Natural language tag":
            st.session_state["g_mapping"].add((om_iri, RML.datatype, om_datatype_iri))
        elif om_datatype_option == "🈳 Natural language tag":
            st.session_state["g_mapping"].add((om_iri, RML.language, Literal(om_language_tag)))
    elif om_term_type == "🌐 IRI":
        st.session_state["g_mapping"].add((om_iri, RML.termType, RML.IRI))
    elif om_term_type == "👻 BNode":
        st.session_state["g_mapping"].add((om_iri, RML.termType, RML.BlankNode))
    # graph map
    if add_om_graph_map_option != "Default graph map":
        st.session_state["g_mapping"].add((om_iri, RML.graphMap, om_graph))
    # store information________________________
    st.session_state["pom_saved_ok_flag"] = True
    st.session_state["last_added_pom_list"].insert(0, [pom_iri, st.session_state["tm_iri_for_pom"]])
    st.session_state["om_template_list"] = []    # reset template
    st.session_state["om_template_is_iri_flag"] = False
    st.session_state["om_template_variable_part_flag"] = False
    # reset fields_____________________________
    st.session_state["key_tm_label_for_pom"] = tm_label_for_pom   # keep same tm to add more pom
    st.session_state["key_om_generation_rule_radio"] = "Template 📐"
    st.session_state["key_predicate"] = []
    st.session_state["key_build_template_action_om"] = "🔒 Fixed part"
    st.session_state["key_om_term_type"] = "🌐 IRI"
    st.session_state["key_add_om_graph_map_option"] = "Default graph map"

def save_pom_constant():
    # get info______________________________
    pom_iri = BNode()
    om_iri = BNode()
    # add triples pom________________________
    st.session_state["g_mapping"].add((st.session_state["tm_iri_for_pom"], RML.predicateObjectMap, pom_iri))
    for p_iri in predicate_iri_list:
        st.session_state["g_mapping"].add((pom_iri, RML.predicate, p_iri))
    st.session_state["g_mapping"].add((pom_iri, RML.objectMap, om_iri))
    st.session_state["g_mapping"].add((pom_iri, RDF.type, RML.PredicateObjectMap))
    # add triples om________________________
    st.session_state["g_mapping"].add((om_iri, RDF.type, RML.ObjectMap))
    if om_constant_ns_prefix:
        NS = Namespace(mapping_ns_dict[om_constant_ns_prefix])
        om_constant_iri = NS[om_constant]
        st.session_state["g_mapping"].add((om_iri, RML.constant, URIRef(om_constant_iri)))
    else:
        st.session_state["g_mapping"].add((om_iri, RML.constant, Literal(om_constant)))
    # term type, datatype and language tag
    if om_term_type == "📘 Literal":
        st.session_state["g_mapping"].add((om_iri, RML.termType, RML.Literal))
        if om_datatype_option and om_datatype_option != "🈳 Natural language tag":
            st.session_state["g_mapping"].add((om_iri, RML.datatype, om_datatype_iri))
        elif om_datatype_option == "🈳 Natural language tag":
            st.session_state["g_mapping"].add((om_iri, RML.language, Literal(om_language_tag)))
    elif om_term_type == "🌐 IRI":
        st.session_state["g_mapping"].add((om_iri, RML.termType, RML.IRI))
    # graph map
    if add_om_graph_map_option != "Default graph map":
        st.session_state["g_mapping"].add((om_iri, RML.graphMap, om_graph))
    # store information________________________
    st.session_state["pom_saved_ok_flag"] = True
    st.session_state["last_added_pom_list"].insert(0, [pom_iri, st.session_state["tm_iri_for_pom"]])
    st.session_state["om_template_list"] = []    # reset template (in case it was modified)
    st.session_state["om_template_is_iri_flag"] = False
    st.session_state["om_template_variable_part_flag"] = False
    # reset fields_____________________________
    st.session_state["key_tm_label_for_pom"] = tm_label_for_pom   # keep same tm to add more pom
    st.session_state["key_om_generation_rule_radio"] = "Template 📐"
    st.session_state["key_predicate"] = []
    st.session_state["key_build_template_action_om"] = "🔒 Fixed part"
    st.session_state["key_om_term_type"] = "🌐 IRI"
    st.session_state["key_add_om_graph_map_option"] = "Default graph map"

def save_pom_reference():
    # get info______________________________
    pom_iri = BNode()
    om_iri = BNode()
    # add triples pom________________________
    st.session_state["g_mapping"].add((st.session_state["tm_iri_for_pom"], RML.predicateObjectMap, pom_iri))
    for p_iri in predicate_iri_list:
        st.session_state["g_mapping"].add((pom_iri, RML.predicate, p_iri))
    st.session_state["g_mapping"].add((pom_iri, RML.objectMap, om_iri))
    st.session_state["g_mapping"].add((pom_iri, RDF.type, RML.PredicateObjectMap))
    # add triples om________________________
    st.session_state["g_mapping"].add((om_iri, RDF.type, RML.ObjectMap))
    st.session_state["g_mapping"].add((om_iri, RML.reference, Literal(om_column_name)))
    # term type, datatype and language tag
    if om_term_type == "📘 Literal":
        st.session_state["g_mapping"].add((om_iri, RML.termType, RML.Literal))
        if om_datatype_option and om_datatype_option != "🈳 Natural language tag":
            st.session_state["g_mapping"].add((om_iri, RML.datatype, om_datatype_iri))
        elif om_datatype_option == "🈳 Natural language tag":
            st.session_state["g_mapping"].add((om_iri, RML.language, Literal(om_language_tag)))
    elif om_term_type == "🌐 IRI":
        st.session_state["g_mapping"].add((om_iri, RML.termType, RML.IRI))
    elif om_term_type == "👻 BNode":
        st.session_state["g_mapping"].add((om_iri, RML.termType, RML.BlankNode))
    # graph map
    if add_om_graph_map_option != "Default graph map":
        st.session_state["g_mapping"].add((om_iri, RML.graphMap, om_graph))
    # store information________________________
    st.session_state["pom_saved_ok_flag"] = True
    st.session_state["last_added_pom_list"].insert(0, [pom_iri, st.session_state["tm_iri_for_pom"]])
    st.session_state["om_template_list"] = []    # reset template (in case it was modified)
    st.session_state["om_template_is_iri_flag"] = False
    st.session_state["om_template_variable_part_flag"] = False
    # reset fields_____________________________
    st.session_state["key_tm_label_for_pom"] = tm_label_for_pom   # keep same tm to add more pom
    st.session_state["key_om_generation_rule_radio"] = "Template 📐"
    st.session_state["key_predicate"] = []
    st.session_state["key_build_template_action_om"] = "🔒 Fixed part"
    st.session_state["key_om_term_type"] = "🌐 IRI"
    st.session_state["key_add_om_graph_map_option"] = "Default graph map"

# TAB4
def remove_tm():   #function to remove TriplesMaps
    # remove triples and store information___________
    for tm in tm_to_remove_list:
        utils.remove_triplesmap(tm)      # remove the tm
    #store information
    st.session_state["last_added_sm_list"] = [pair for pair in st.session_state["last_added_sm_list"]
        if pair[1] in utils.get_tm_dict()]
    st.session_state["last_added_pom_list"] = [pair for pair in st.session_state["last_added_pom_list"]
        if pair[1] in utils.get_tm_dict()]
    st.session_state["tm_removed_ok_flag"] = True
    #reset fields_________________________
    st.session_state["key_tm_to_remove_list"] = []

def remove_all_tm():   #function to remove all TriplesMaps (empty mapping)
    # remove all triples
    st.session_state["g_mapping"] = Graph()
    #store information
    st.session_state["last_added_tm_list"] = []
    st.session_state["last_added_sm_list"] = []
    st.session_state["last_added_pom_list"] = []
    st.session_state["tm_removed_ok_flag"] = True
    #reset fields_______________________
    st.session_state["key_tm_to_remove_list"] = []

def unassign_sm():
    # remove triples______________________
    tm_dict = utils.get_tm_dict()
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
    st.session_state["key_component_type_to_remove"] = "🗺️ TriplesMap"

def remove_pom():           #function to remove a Predicate-Object Map
    # remove triples______________________
    for pom_iri in pom_to_remove_iri_list:
        om_to_remove = st.session_state["g_mapping"].value(subject=pom_iri, predicate=RML.objectMap)
        st.session_state["g_mapping"].remove((pom_iri, None, None))
        st.session_state["g_mapping"].remove((None, None, pom_iri))
        st.session_state["g_mapping"].remove((om_to_remove, None, None))
    # store information__________________
    st.session_state["pom_removed_ok_flag"] = True
    st.session_state["last_added_pom_list"] = [pair for pair in st.session_state["last_added_pom_list"]
        if pair[0] not in pom_to_remove_iri_list]
    # reset fields_______________________________-
    st.session_state["key_component_type_to_remove"] = "🗺️ TriplesMap"

def clean_g_mapping():
    # remove triples and store information____________________________
    for tm in tm_to_clean_list:
        utils.remove_triplesmap(tm)      # remove the tm
    # remove predicate-object maps
    for pom_iri in pom_to_clean_list:
        om_to_remove = st.session_state["g_mapping"].value(subject=pom_iri, predicate=RML.objectMap)
        st.session_state["g_mapping"].remove((pom_iri, None, None))
        st.session_state["g_mapping"].remove((None, None, pom_iri))
        st.session_state["g_mapping"].remove((om_to_remove, None, None))
    # store information__________________
    st.session_state["last_added_sm_list"] = [pair for pair in st.session_state["last_added_sm_list"]
        if pair[1] in utils.get_tm_dict()]
    st.session_state["last_added_pom_list"] = [pair for pair in st.session_state["last_added_pom_list"]
        if pair[1] in utils.get_tm_dict()]
    st.session_state["last_added_pom_list"] = [pair for pair in st.session_state["last_added_pom_list"]
        if pair[0] not in pom_to_remove_iri_list]
    st.session_state["g_mapping_cleaned_ok_flag"] = True

#_______________________________________________________________________________
# PANELS OF THE PAGE (tabs)
tab1, tab2, tab3, tab4 = st.tabs(["Add TriplesMap", "Add Subject Map", "Add Predicate-Object Map", "Manage Mapping"])

# ERROR MESSAGE IF NO MAPPING LOADED--------------------------------------------
col1, col2 = st.columns([2,1])
if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
    with col1:
        utils.get_missing_element_error_message(mapping=True, different_page=True)
        st.stop()

#_______________________________________________________________________________
# PANEL: ADD TRIPLESMAP
with tab1:
    col1, col2, col2a, col2b = utils.get_panel_layout()
    with col2b:
        utils.get_corner_status_message(mapping_info=True)

    with col2b:
        utils.display_right_column_df("triplesmaps", "last added TriplesMaps")

    #PURPLE HEADING: ADD TRIPLESMAP---------------------------------------------
    with col1:
        st.markdown("""<div class="purple-heading">
                🧱 Add TriplesMap
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
        col1a, col1b = st.columns([1,1])

    with col1a:
        tm_label = st.text_input("🏷️ Enter TriplesMap label:*", key="key_tm_label_input")    # user-friendly name for the TriplesMap
        st.session_state["tm_label"] = tm_label
        valid_tm_label = utils.is_valid_label(tm_label, hard=True)

    tm_dict = utils.get_tm_dict()
    tm_label_list = [split_uri(tm_iri)[1] for tm_label, tm_iri in tm_dict.items()]
    if tm_label in tm_label_list:
        valid_tm_label = False
        with col1a:
            st.markdown(f"""<div class="error-message">
                ❌ Label <b style="color:#a94442;">{tm_label}</b> already <b>in use</b>.
                <small>Please pick a different label.</small>
            </div>""", unsafe_allow_html=True)

    labelled_ls_list = []      # existing labelled logical sources
    for s, p, o in st.session_state["g_mapping"].triples((None, RML.logicalSource, None)):
        if isinstance(o, URIRef) and split_uri(o)[1] not in labelled_ls_list:
            labelled_ls_list.append(split_uri(o)[1])

    if valid_tm_label:   #after a valid label has been given

        ls_options_list = []
        if st.session_state["db_connections_dict"]:
            ls_options_list.append("📊 Database")
        if st.session_state["ds_files_dict"]:
            ls_options_list.append("🛢️ Data file")
        if labelled_ls_list:
            ls_options_list.append("📑 Existing Logical Source")

        with col1b:
            if ls_options_list:
                ls_option = st.radio("🖱️ Logical Source:*", ls_options_list, horizontal=True,
                    key="key_ls_option")
                if not st.session_state["db_connections_dict"] and not st.session_state["ds_files_dict"]:
                    st.markdown(f"""<div class="info-message-gray">
                        ℹ️ To add <b>data sources</b> <small>go to the
                        <b>📊 Databases</b> and/or <b>🛢️ Data Files</b> pages.</small>
                    </div>""", unsafe_allow_html=True)

            else:
                st.markdown(f"""<div class="error-message">
                    ❌ <b>No data sources are available.</b> <small>You can add them in the
                    <b>📊 Databases</b> and/or <b>🛢️ Data Files</b> pages.</small>
                </div>""", unsafe_allow_html=True)
                ls_option = None

        if ls_option == "📑 Existing Logical Source":

            with col1a:
                list_to_choose = sorted(labelled_ls_list)
                list_to_choose.insert(0, "Select Logical Source")
                existing_ls = st.selectbox("🖱️ Select existing Logical Source:*", list_to_choose)

            if existing_ls != "Select Logical Source":
                with col1a:
                    save_tm_button_existing_ls = st.button("Save", key="key_save_tm_w_existing_ls", on_click=save_tm_w_existing_ls)


        if ls_option == "📊 Database":
            with col1:
                col1a, col1b = st.columns([2,1])

            with col1a:
                list_to_choose = sorted(st.session_state["db_connections_dict"].keys())
                list_to_choose.insert(0, "Select connection")
                db_connection_for_ls = st.selectbox("🖱️ Select connection to database:*", list_to_choose,
                    key="key_db_connection_for_ls")

            if db_connection_for_ls != "Select connection":

                with col1a:
                    conn, connection_ok_flag = utils.check_connection_to_db(db_connection_for_ls, different_page=True)

                if connection_ok_flag:
                    with col1b:
                        label_ls_option = st.selectbox("♻️ Reuse Logical Source:",
                            ["No", "Yes (add label 🔖)"], key="key_label_ls_option")
                        valid_ls_label = True

                    if label_ls_option == "Yes (add label 🔖)":
                        with col1a:
                            ls_label = st.text_input("🏷️ Enter label for the Logical Source:*")
                        with col1b:
                            st.write("")
                            valid_ls_label = utils.is_valid_label(ls_label, hard=True)
                            if valid_ls_label and ls_label in labelled_ls_list:
                                st.markdown(f"""<div class="error-message">
                                        ❌ Label <b>{ls_label}</b>
                                        is already <b>in use</b>. <small>Please pick a different label.</small>
                                    </div>""", unsafe_allow_html=True)
                                valid_ls_label = False

                    engine = st.session_state["db_connections_dict"][db_connection_for_ls][0]
                    views_for_selected_db_list = []   # list of queries of the selected connection
                    if engine != "MongoDB":   # for MongoDB, view is stored as a table in the database
                        for view_label, [connection_label, query] in st.session_state["saved_views_dict"].items():
                            if connection_label == db_connection_for_ls:
                                views_for_selected_db_list.insert(0, view_label)   # only include queries of the selected connection

                    with col1:
                        col1a, col1b = st.columns(2)

                    if views_for_selected_db_list:
                        with col1b:
                            list_to_choose = ["🖼️ View", "📅 Table"]
                            query_option = st.radio("🖱️ Select option:*", list_to_choose,
                                horizontal=True, key="key_query_option_radio")
                    else:
                        query_option = "📅 Table"

                    if query_option == "🖼️ View":

                        with col1a:
                            list_to_choose = views_for_selected_db_list
                            list_to_choose.insert(0, "Select view")
                            selected_view_for_ls = st.selectbox("🖼️ Select view:*", list_to_choose,
                                key="key_selected_view_for_ls")

                        if selected_view_for_ls != "Select view":
                            with col1:
                                sql_query_ok_flag = utils.display_db_view_results(selected_view_for_ls)

                            if sql_query_ok_flag:
                                with col1a:
                                    st.button("Save", key="key_save_tm_w_view", on_click=save_tm_w_view)

                    if query_option == "📅 Table":
                        result = utils.get_tables_from_db(db_connection_for_ls)
                        db_tables = [row[0] for row in result]

                        with col1a:
                            list_to_choose = sorted(db_tables)
                            list_to_choose.insert(0, "Select table")
                            selected_table_for_ls = st.selectbox("📅 Select table:*", list_to_choose,
                                key="key_selected_table_for_ls")

                        if selected_table_for_ls != "Select table":
                            if valid_ls_label:
                                with col1a:
                                    st.button("Save", key="key_save_tm_w_table_name", on_click=save_tm_w_table_name)

                            with col1:
                                df = utils.get_db_table_df(db_connection_for_ls, selected_table_for_ls)
                                utils.display_limited_df(df, "Table", display=True)

        if ls_option == "🛢️ Data file":

            with col1:
                col1a, col1b = st.columns([2,1])

            with col1a:
                list_to_choose = sorted(st.session_state["ds_files_dict"].keys())
                list_to_choose.insert(0, "Select file")
                ds_filename_for_tm = st.selectbox("🖱️ Select the Logical Source file:*", list_to_choose,
                key="key_ds_filename_for_tm")

            if ds_filename_for_tm != "Select file":
                ds_file = st.session_state["ds_files_dict"][ds_filename_for_tm]

            with col1b:
                label_ls_option = st.selectbox("♻️ Reuse Logical Source:",
                    ["No", "Yes (add label 🔖)"], key="key_label_ls_option")

                if label_ls_option == "Yes (add label 🔖)":
                    with col1a:
                        ls_label = st.text_input("🏷️ Enter label for the Logical Source:*")
                    with col1b:
                        valid_ls_label_flag = utils.is_valid_label(ls_label, hard=True, blank_space=True)
                        if ls_label in labelled_ls_list:
                            with col1b:
                                st.write("")
                                st.markdown(f"""<div class="error-message">
                                        ❌ Label <b>{ls_label}</b>
                                        is already <b>in use</b>. <small>Please pick a different label.</small>
                                    </div>""", unsafe_allow_html=True)
                            valid_ls_label_flag = False

                else:
                    ls_label = ""

                with col1a:
                    if label_ls_option == "Yes (add label 🔖)":
                        if valid_ls_label_flag:
                            if ds_filename_for_tm != "Select file":
                                st.button("Save", key="key_save_tm_w_tab_ls", on_click=save_tm_w_tab_ls)
                    else:
                        if ds_filename_for_tm != "Select file":
                            st.button("Save", key="key_save_tm_w_tab_ls", on_click=save_tm_w_tab_ls)


#_______________________________________________________________________________
#PANEL: ADD SUBJECT MAP
with tab2:
    col1, col2, col2a, col2b = utils.get_panel_layout()
    with col2b:
        utils.get_corner_status_message(mapping_info=True)

    # Right column info on sm is given later, since validation messages must appear first

    # PURPLE HEADING - ADD SUBJECT MAP-------------------------------------------
    with col1:
        st.markdown("""<div class="purple-heading">
                🧱 Add Subject Map
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

    tm_dict = utils.get_tm_dict()
    tm_wo_sm_list = []          #list of all TriplesMap which do not have a subject yet
    for tm_label, tm_iri in tm_dict.items():
        if not next(st.session_state["g_mapping"].objects(tm_iri, RML.subjectMap), None):   #if there is no subject for that TriplesMap
            tm_wo_sm_list.append(tm_label)

    with col1:
        col1a, col2a = st.columns([2,0.5])

    if not tm_dict:          # no tm in mapping
        with col1a:
            st.write("")
            st.markdown(f"""<div class="error-message">
                    ❌ <b>No TriplesMaps</b> in mapping <b>{st.session_state["g_label"]}</b>.
                    <small>Add them in the <b>Add TriplesMap</b> panel.</small>
                </div>""", unsafe_allow_html=True)

    elif not tm_wo_sm_list:         # all tm have been assigned an sm
        with col1a:
            st.markdown(f"""<div class="info-message-gray">
                🔒 <b>All existing TriplesMaps have already been assigned a Subject Map.</b><br>
                <ul style="margin-top:0.5em; margin-bottom:0; font-size:0.9em; list-style-type: disc; padding-left: 1.2em;">
                    <li>You can add new TriplesMaps in the <b>Add TriplesMap</b> panel.</li>
                    <li>You can remove the Subject Map of a TriplesMap in the <b>Manage Mapping</b> pannel.</li>
                </ul></div>""",unsafe_allow_html=True)
            st.write("")

    else:            # tm available

        with col1:
            col1a, col1b = st.columns(2)

        with col1a:
            if st.session_state["last_added_tm_list"] and st.session_state["last_added_tm_list"][0] in tm_wo_sm_list:  # Last added tm available (selected by default)
                list_to_choose = sorted(tm_wo_sm_list)
                list_to_choose.insert(0, "Select TriplesMap")
                st.markdown("""
                <div class="small-subsection-heading" style="margin-top:-10px; border-top:none;">
                    <b><span style=" display:inline-block; width:15px; height:15px;
                    background-color:#009933; color:white; border:1px solid black;
                    text-align:center; font-size:10px; line-height:15px;
                        ">T</span> TriplesMap
                    </b></div>""", unsafe_allow_html=True)
                tm_label_for_sm = st.selectbox("🖱️ Select TriplesMap:*", list_to_choose, key="key_tm_label_input_for_sm_default",
                    label_visibility="collapsed", index=list_to_choose.index(st.session_state["last_added_tm_list"][0]))

            else:             # Last added tm not available (no preselected tm)
                list_to_choose = sorted(tm_wo_sm_list)
                list_to_choose.insert(0, "Select TriplesMap")
                tm_label_for_sm = st.selectbox("🖱️ Select TriplesMap:*", list_to_choose, key="key_tm_label_input_for_sm",
                    label_visibility="collapsed")

        if tm_label_for_sm != "Select TriplesMap":

            with col1:
                st.markdown("""<div class="small-subsection-heading">
                </div>""", unsafe_allow_html=True)

            with col1:
                col1a, col1b = st.columns([1,2])
            with col1a:
                st.markdown("""
                <div class="small-subsection-heading" style="margin-top:-10px; border-top:none;">
                    <b><span style=" display:inline-block; width:15px; height:15px;
                    background-color:#e60000; color:white; border:1px solid black;
                    text-align:center; font-size:10px; line-height:15px;
                        ">S</span> Subject
                    </b></div>""", unsafe_allow_html=True)

            tm_iri_for_sm, ls_iri_for_sm, ds_for_sm = utils.get_tm_info(tm_label_for_sm)

            existing_sm_dict = {}
            for sm in st.session_state["g_mapping"].objects(predicate=RML.subjectMap):
                if isinstance(sm, URIRef):
                    existing_sm_dict[utils.get_node_label(sm)] = sm
            existing_sm_list = list(existing_sm_dict.keys())

            with col1b:
                if existing_sm_list:
                    list_to_choose = ["Template 📐", "Constant 🔒", "Reference 📊", "Existing 📑"]
                    sm_generation_rule = st.radio("🖱️ Subject Map generation rule:*", list_to_choose,
                        label_visibility="collapsed", horizontal=True, key="key_sm_generation_rule_radio")
                else:
                    list_to_choose = ["Template 📐", "Constant 🔒", "Reference 📊"]
                    sm_generation_rule = st.radio("🖱️ Subject Map generation rule:*", list_to_choose,
                        label_visibility="collapsed", horizontal=True, key="key_sm_generation_rule_radio")

            # Initialise variables
            column_list = []  # will search only if needed, can be slow if failed connections

            # EXISTING SUBJECT MAP
            if sm_generation_rule == "Existing 📑":

                with col1:
                    col1a, col1b = st.columns(2)
                with col1a:
                    sm_label = st.selectbox("🖱️ Select existing Subject Map:*", sorted(existing_sm_list),
                        placeholder="📑 Select existing Subject Map*", index=None, label_visibility="collapsed", key="key_sm_label_existing")
                    if sm_label:
                        sm_iri = existing_sm_dict[sm_label]
                        st.session_state["sm_iri"] = sm_iri
                        with col1a:
                            st.button("Save", key="key_save_existing_sm_button", on_click=save_sm_existing)

            else:

                # TEMPLATE-VALUED SUBJECT MAP
                if sm_generation_rule == "Template 📐":

                    with col1:
                        col1a, col1b, col1c = st.columns([0.8, 1.2, 0.5])

                    with col1a:
                        list_to_choose = ["🔒 Fixed part", "📈 Variable part", "🏷️ Fixed namespace", "🗑️ Reset template"]
                        build_template_action_sm = st.selectbox("🖱️ Add template part:", list_to_choose,
                            label_visibility="collapsed", key="key_build_template_action_sm")

                    if build_template_action_sm == "🔒 Fixed part":
                        with col1b:
                            sm_template_fixed_part = st.text_input("⌨️ Enter fixed part:", key="key_sm_fixed_part",
                                placeholder="🔒 Enter fixed part", label_visibility="collapsed")
                            if re.search(r"[ \t]", sm_template_fixed_part) and re.search(r"[\n\r<>\"{}|\\^`]", sm_template_fixed_part):
                                st.markdown(f"""<div class="warning-message">
                                    ⚠️ <b>Spaces and unescaped characters</b> are discouraged.
                                </div>""", unsafe_allow_html=True)

                            elif re.search(r"[ \t]", sm_template_fixed_part):
                                st.markdown(f"""<div class="warning-message">
                                    ⚠️ <b>Spaces</b> are discouraged.
                                </div>""", unsafe_allow_html=True)

                            elif re.search(r"[\n\r<>\"{}|\\^`]", sm_template_fixed_part):
                                st.markdown(f"""<div class="warning-message">
                                    ⚠️ <b>Unescaped characters</b> are discouraged.
                                </div>""", unsafe_allow_html=True)

                        with col1c:
                            if sm_template_fixed_part:
                                st.button("Add", key="key_save_sm_template_fixed_part_button", on_click=save_sm_template_fixed_part)

                    elif build_template_action_sm == "📈 Variable part":

                        column_list, inner_html, ds_for_display, ds_available_flag, hierarchical_data_file_flag = utils.get_column_list_and_give_info(tm_label_for_sm, template=True)
                        if not column_list:   #data source is not available (load)
                            with col1b:
                                sm_template_variable_part = st.text_input("⌨️ Manually enter column of the data source:*",
                                    placeholder="📈 Enter template placeholder", key="key_sm_template_variable_part_manual", label_visibility="collapsed")
                                utils.get_very_small_ds_info(column_list, inner_html, ds_for_display, ds_available_flag)
                            with col1c:
                                if sm_template_variable_part:
                                    st.button("Add", key="save_sm_template_variable_part_button", on_click=save_sm_template_variable_part)

                        else:  # data source is available
                            with col1b:
                                list_to_choose = column_list.copy()
                                sm_template_variable_part = st.selectbox("🖱️ Select the column of the data source:", list_to_choose,
                                    placeholder="📈 Select template placeholder", index=None, label_visibility="collapsed", key="key_sm_template_variable_part")
                                utils.get_very_small_ds_info(column_list, inner_html, ds_for_display, ds_available_flag)
                                if sm_template_variable_part and hierarchical_data_file_flag:
                                    sm_template_variable_part = st.session_state["saved_paths_dict"][sm_template_variable_part][1]

                            with col1c:
                                if sm_template_variable_part:
                                    st.button("Add", key="save_sm_template_variable_part_button", on_click=save_sm_template_variable_part)

                        if st.session_state["sm_template_list"] and st.session_state["sm_template_list"][-1].endswith("}"):
                            if inner_html:
                                inner_html += """&nbsp&nbsp&nbsp•&nbsp&nbsp&nbsp <b>Best practice:</b>
                                    Add a fixed part between two variable parts <small>to improve clarity.</small></div>"""
                            else:
                                inner_html += """⚠️ <b>Best practice:</b>
                                    Add a fixed part between two variable parts <small>to improve clarity.</small></div>"""

                        if inner_html:
                            with col1:
                                col1a, col1b = st.columns([2,0.5])
                            with col1a:
                                st.markdown(f"""<div class="warning-message">
                                    {inner_html}
                                </div>""", unsafe_allow_html=True)

                    elif build_template_action_sm == "🏷️ Fixed namespace":
                        with col1b:
                            mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
                            list_to_choose = sorted(mapping_ns_dict.keys())
                            if st.session_state["sm_template_is_iri_flag"]:
                                list_to_choose.insert(0, "Remove namespace")
                            sm_template_ns_prefix = st.selectbox("🖱️ Select a namespace for the template:", list_to_choose,
                                placeholder="Select namespace*", index=None, label_visibility="collapsed", key="key_sm_template_ns_prefix")

                        with col1c:
                            if sm_template_ns_prefix == "Remove namespace":
                                st.button("Remove", key="key_add_ns_to_sm_template_button", on_click=remove_ns_from_sm_template)
                            elif sm_template_ns_prefix:
                                sm_template_ns = mapping_ns_dict[sm_template_ns_prefix]
                                st.button("Add", key="key_add_ns_to_sm_template_button", on_click=add_ns_to_sm_template)

                    elif build_template_action_sm == "🗑️ Reset template":
                        with col1b:
                            st.markdown(f"""<div class="warning-message">
                                    ⚠️ The current template <b>will be removed</b>.
                                </div>""", unsafe_allow_html=True)
                        with col1c:
                            st.button("Reset", key="key_reset_sm_template_button", on_click=reset_sm_template)

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
                        else:
                            st.markdown(f"""<div class="gray-preview-message">
                                    📐 <b> Build your <b style="color:#F63366;">template</b>
                                    above and preview it here.</b> <small>You can add as many parts as you need.</small></div>""", unsafe_allow_html=True)
                        st.write("")

                # CONSTANT-VALUED SUBJECT MAP
                if sm_generation_rule == "Constant 🔒":

                    with col1:
                        col1a, col1b = st.columns(2)
                    with col1b:
                        sm_constant = st.text_input("⌨️ Enter constant:*", key="key_sm_constant",
                            placeholder="🔒 Enter constant*", label_visibility="collapsed")
                        # if sm_constant:
                        #     st.markdown("""<div class="very-small-info">
                        #         🔒 Constant
                        #     </div>""", unsafe_allow_html=True)

                    mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
                    list_to_choose = sorted(mapping_ns_dict.keys())
                    with col1a:
                        sm_constant_ns_prefix = st.selectbox("🖱️ Namespace (opt):", list_to_choose,
                            placeholder="Select namespace (opt)", index=None, label_visibility="collapsed", key="key_sm_constant_ns")

                # REFERENCED-VALUED SUBJECT MAP
                if sm_generation_rule ==  "Reference 📊":

                    with col1:
                        col1a, col1b = st.columns([2,1])

                    column_list, inner_html, ds_for_display, ds_available_flag, hierarchical_data_file_flag = utils.get_column_list_and_give_info(tm_label_for_sm)

                    if not column_list:   #data source is not available (load)
                        with col1a:
                            sm_column_name = st.text_input("⌨️ Manually enter logical source reference:*",
                                placeholder="📊 Enter reference manually", key="key_sm_column_name_manual", label_visibility="collapsed")
                            utils.get_very_small_ds_info(column_list, inner_html, ds_for_display, ds_available_flag)

                    else:
                        with col1a:
                            list_to_choose = column_list.copy()
                            sm_column_name = st.selectbox(f"""🖱️ Select reference:*""", list_to_choose,
                                placeholder="📊 Select reference*", index=None, label_visibility="collapsed", key="key_sm_column_name")
                            utils.get_very_small_ds_info(column_list, inner_html, ds_for_display, ds_available_flag)
                            if sm_column_name and hierarchical_data_file_flag:
                                sm_column_name = st.session_state["saved_paths_dict"][sm_column_name][1]

                    if inner_html:
                        with col1b:
                            st.markdown(f"""<div class="warning-message">
                                {inner_html}
                            </div>""", unsafe_allow_html=True)

                # ADDITIONAL CONFIGURATION
                with col1:
                    st.markdown("""<div class="small-subsection-heading">
                        <b>⚙️ Additional Configuration</b><br>
                    </div>""", unsafe_allow_html=True)
                with col1:
                    col1a, col1b, col1c = st.columns(3)

                # TERM TYPE
                with col1a:
                    st.markdown(f"""<div class="very-small-info-top">
                        🆔 Term type*
                    </div>""", unsafe_allow_html=True)
                    if sm_generation_rule ==  "Constant 🔒":
                        list_to_choose = ["🌐 IRI"]
                    else:
                        list_to_choose = ["🌐 IRI", "👻 BNode"]
                    sm_term_type = st.selectbox("🆔 Select term type:*", list_to_choose,
                        label_visibility="collapsed", key="key_sm_term_type")


                # SUBJECT MAP LABEL
                with col1a:
                    st.markdown(f"""<div class="very-small-info-top">
                        ♻️ Reuse Subject Map*
                    </div>""", unsafe_allow_html=True)
                    label_sm_option = st.selectbox("♻️ Reuse Subject Map (opt):", ["No", "Yes (add label 🔖)"],
                        label_visibility="collapsed")
                    if label_sm_option == "Yes (add label 🔖)":
                        sm_label = st.text_input("🔖 Enter Subject Map label:*", key="key_sm_label_new",
                            placeholder="🔖 Subject Map label*", label_visibility="collapsed")
                        valid_sm_label = utils.is_valid_label(sm_label, hard=True, display=False)
                    else:
                        sm_label = ""
                        sm_iri = BNode()

                # SUBJECT CLASS
                with col1b:
                    st.markdown(f"""<div class="very-small-info-top">
                        🏷️️ Class (opt)
                    </div>""", unsafe_allow_html=True)
                    ontology_class_dict = utils.get_ontology_class_dict(st.session_state["g_ontology"])
                    custom_class_dict =  utils.get_ontology_class_dict("custom")
                    custom_class_dict = {}          # dictionary for custom classes
                    for k, v in st.session_state["custom_terms_dict"].items():
                        if v == "🏷️ Class":
                            custom_class_dict[utils.get_node_label(k)] = k

                    ontology_filter_list = sorted(st.session_state["g_ontology_components_tag_dict"].values())
                    if custom_class_dict:
                        ontology_filter_list.insert(0, "Custom classes")

                    # Filter by ontology
                    if len(ontology_filter_list) > 1:
                        list_to_choose = ontology_filter_list
                        ontology_filter_for_subject_class = st.selectbox("📡 Filter class by ontology (opt):", list_to_choose,
                            placeholder="📡 Ontology filter", index=None, label_visibility="collapsed",
                            key="key_ontology_filter_for_subject_class")

                        if not ontology_filter_for_subject_class:
                            ontology_filter_for_subject_class = st.session_state["g_ontology"]
                        if ontology_filter_for_subject_class == "Custom classes":
                            ontology_filter_for_subject_class = "Custom classes"
                        else:
                            for ont_label, ont_tag in st.session_state["g_ontology_components_tag_dict"].items():
                                if ont_tag == ontology_filter_for_subject_class:
                                    ontology_filter_for_subject_class = st.session_state["g_ontology_components_dict"][ont_label]
                                    break
                    else:
                        ontology_filter_for_subject_class = st.session_state["g_ontology"]

                    if ontology_filter_for_subject_class != "Custom classes":

                        ontology_class_dict = utils.get_ontology_class_dict(ontology_filter_for_subject_class)   # filtered class dictionary
                        ontology_superclass_dict = utils.get_ontology_class_dict(ontology_filter_for_subject_class, superclass=True)

                        if ontology_superclass_dict:   # there exists at least one superclass (show superclass filter)
                            classes_in_ontology_superclass_dict = {}
                            superclass_list = sorted(ontology_superclass_dict.keys())
                            superclass = st.selectbox("📡 Filter by superclass (opt):", superclass_list,
                                placeholder="📡 Superclass filter", index=None, label_visibility="collapsed", key="key_superclass")   # superclass label

                            if superclass:   # a superclass has been selected (filter)
                                classes_in_ontology_superclass_dict[superclass] = ontology_superclass_dict[superclass]
                                superclass = ontology_superclass_dict[superclass] #we get the superclass iri
                                for s, p, o in list(set(st.session_state["g_ontology"].triples((None, RDFS.subClassOf, superclass)))):
                                    classes_in_ontology_superclass_dict[utils.get_node_label(s)] = s
                                class_list = sorted(classes_in_ontology_superclass_dict.keys())
                                subject_class_list = st.multiselect("🏷️️ Select class(es):", class_list,
                                    placeholder="🏷️️ Select class(es)", label_visibility="collapsed", key="key_subject_class")   # class list (labels)

                            else:  #no superclass selected (list all classes)
                                if ontology_filter_for_subject_class == st.session_state["g_ontology"]:
                                    class_list = sorted(list(ontology_class_dict.keys()) + list(custom_class_dict.keys()))
                                else:
                                    class_list = sorted(ontology_class_dict.keys())
                                subject_class_list = st.multiselect("🏷️️ Select class(es):", class_list,
                                    placeholder="🏷️️ Select class(es)", label_visibility="collapsed", key="key_subject_class")    # class list (labels)

                        else:     #no superclasses exist (no superclass filter)
                            if ontology_filter_for_subject_class == st.session_state["g_ontology"]:
                                class_list = sorted(list(ontology_class_dict.keys()) + list(custom_class_dict.keys()))
                            else:
                                class_list = sorted(ontology_class_dict.keys())
                            subject_class_list = st.multiselect("🏷️ Select class(es):", class_list,
                                placeholder="🏷️️ Select class(es)", label_visibility="collapsed", key="key_subject_class")    # class list (labels)

                    elif ontology_filter_for_subject_class == "Custom classes":
                        class_list = sorted(custom_class_dict.keys())
                        class_list.insert(0, "Select class")
                        subject_class_list = st.multiselect("🏷️ Select class(es):", class_list,
                            placeholder="🏷️️ Select class(es)", label_visibility="collapsed", key="key_subject_class")    # class list (labels)

                # GRAPH MAP
                with col1c:

                    st.markdown(f"""<div class="very-small-info-top">
                        🗺️️ Graph map (opt)
                    </div>""", unsafe_allow_html=True)

                    graph_map_dict = utils.get_graph_map_dict()
                    list_to_choose = sorted(graph_map_dict.keys())
                    list_to_choose.insert(0, "✚🗺️️ New graph map")
                    list_to_choose.insert(0, "Default graph map")
                    add_sm_graph_map_option = st.selectbox("️🗺️️ Graph map (optional):", list_to_choose,
                        label_visibility="collapsed", key="key_add_sm_graph_map_option")

                    if add_sm_graph_map_option == "✚🗺️️ New graph map":
                        mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
                        list_to_choose = sorted(mapping_ns_dict.keys())
                        sm_graph_prefix = st.selectbox("🖱️ Namespace (opt):", list_to_choose,
                            placeholder="Select namespace", index=None, label_visibility="collapsed", key="key_sm_graph_prefix")
                        sm_graph_input = st.text_input("⌨️ Enter graph map:*", key="key_sm_graph_input",
                            placeholder="🗺️️ Enter graph map*", label_visibility="collapsed")
                        if sm_graph_prefix:
                            NS = Namespace(mapping_ns_dict[sm_graph_prefix])
                            sm_graph = NS[sm_graph_input]
                        else:
                            sm_graph = sm_graph_input
                    elif add_sm_graph_map_option != "Default graph map":
                        sm_graph = graph_map_dict[add_sm_graph_map_option]

                # CHECK EVERYTHING IS READY
                sm_complete_flag = True
                inner_html_error = ""
                inner_html_warning = ""

                if sm_generation_rule == "Template 📐":
                    if not sm_template:
                        sm_complete_flag = False
                        inner_html_error += "<small>· The <b>template</b> is empty.</small><br>"
                    elif not st.session_state["sm_template_variable_part_flag"]:
                        inner_html_error += """<small>· The <b>template</b> must contain
                            at least one <b>variable part</b>.</small><br>"""
                        sm_complete_flag = False
                    if sm_template and sm_term_type == "🌐 IRI":   # if term type is IRI the NS is recommended
                        if not st.session_state["sm_template_is_iri_flag"]:
                            inner_html_warning += """<small>· Term type is <b>IRI</b>.
                                <b>Adding a namespace to the template</b> is recommended.</small><br>"""

                if sm_generation_rule == "Constant 🔒":
                    if not sm_constant:
                        sm_complete_flag = False
                        inner_html_error += "<small>· No <b>constant</b> entered.</small><br>"

                    if sm_constant and not sm_constant_ns_prefix:
                        if not utils.is_valid_iri(sm_constant, delimiter_ending=False):
                            sm_complete_flag = False
                            inner_html_error += """<small>· If no namespace is selected,
                                the <b>constant</b> must be a <b>valid IRI</b>.</small><br>"""

                if sm_generation_rule == "Reference 📊":
                    if column_list and not sm_column_name:
                        sm_complete_flag = False
                        inner_html_error += "<small>· The <b>reference</b> has not been selected.</small><br>"
                    elif not column_list and not sm_column_name:
                        sm_complete_flag = False
                        inner_html_error += "<small>· The <b>reference</b> has not been entered.</small><br>"
                    else:
                        if sm_term_type == "🌐 IRI":
                            inner_html_warning += """<small>· Term type is <b>IRI</b>.
                                Make sure the values in the referenced column
                                are valid IRIs.</small><br>"""

                if not custom_class_dict and not ontology_class_dict:
                    inner_html_warning += """<small>· </b> No classes available</b>
                        (custom not ontology-defined).</small><br>"""
                elif not subject_class_list:
                    inner_html_warning += """<small>· <b>No class</b> selected (allowed).</small><br>"""
                elif len(subject_class_list) > 1:
                    inner_html_warning += """<small>· <b>More than one class</b> selected (allowed).</small><br>"""
                for class_label in subject_class_list:
                    if class_label in custom_class_dict:
                        inner_html_warning += """<small>· <b>Custom classes</b> lack ontology alignment.
                             An ontology-driven approach is recommended.</small><br>"""
                        break

                if add_sm_graph_map_option == "✚🗺️️ New graph map":
                    if not sm_graph_input:
                        sm_complete_flag = False
                        inner_html_error += """<small>· The <b>graph map</b>
                            has not been given.</small><br>"""
                    else:
                        if not sm_graph_prefix and not utils.is_valid_iri(sm_graph_input, delimiter_ending=False):
                            sm_complete_flag = False
                            inner_html_error += """<small>· If no namespace is selected,
                                the <b>graph map</b> must be a <b>valid IRI</b>.</small><br>"""

                elif add_sm_graph_map_option == "🔄 Existing graph map":
                    if s_existing_graph_label == "Select graph map":
                        sm_complete_flag = False
                        inner_html_error += """<small>· The <b>graph map</b>
                            has not been selected.</small><br>"""

                if label_sm_option == "Yes (add label 🔖)":
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

                # INFO MESSAGES (RIGHT COLUMN)
                with col2b:
                    messages = []
                    if inner_html_error:
                        messages.append(f"""❌ <b>Subject Map is incomplete.</b><br>
                        <div style='margin-left: 1.5em;'>{inner_html_error}</div>""")
                    if inner_html_warning:
                        messages.append(f"""⚠️ <b>Caution.</b><br>
                        <div style='margin-left: 1.5em;'>{inner_html_warning}</div>""")
                    if sm_complete_flag:
                        messages.append("""✔️ All <b>required fields (*)</b> are complete.
                        <small>Double-check the information before saving.</small>""")

                    separator = "<hr style='border:0; border-top:1px solid #999; margin:10px 0;'>"
                    final_message = separator.join(messages)
                    if final_message:
                        st.markdown(f"""<div class="gray-preview-message" style="font-size:13px; line-height:1.2;">
                                {final_message}
                            </div>""", unsafe_allow_html=True)
                        st.write("")
                        st.write("")

                # SAVE BUTTON
                with col1c:
                    if sm_complete_flag:
                        st.markdown("""<div class="small-subheading">
                                <b>💾 Save</b><br>
                            </div>""", unsafe_allow_html=True)
                        if sm_generation_rule == "Template 📐":
                            save_sm_template_button = st.button("Save", on_click=save_sm_template, key="key_save_sm_template_button")
                        elif sm_generation_rule == "Constant 🔒":
                            save_sm_constant_button = st.button("Save", on_click=save_sm_constant, key="key_save_sm_constant_button")
                        if sm_generation_rule == "Reference 📊":
                            save_sm_reference_button = st.button("Save", on_click=save_sm_reference, key="key_save_sm_reference_button")

    with col2b:
        utils.display_right_column_df("subject_maps", "last added Subject Maps")


#_______________________________________________________________________________
# PANEL: ADD PREDICATE-OBJECT MAP
with tab3:
    col1, col2, col2a, col2b = utils.get_panel_layout()
    with col2b:
        utils.get_corner_status_message(mapping_info=True)

    #PURPLE HEADING - ADD TRIPLESMAP
    with col1:
        st.markdown("""<div class="purple-heading">
                🧱 Add Predicate-Object Map
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

    tm_w_sm_list = []            #list of all triplesmaps with assigned Subject Map
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
            st.markdown("""<div class="small-subsection-heading" style="margin-top:-10px; border-top:none;">
                <b><span style=" display:inline-block; width:15px; height:15px;
                background-color:#009933; color:white; border:1px solid black;
                text-align:center; font-size:10px; line-height:15px;
                    ">T</span> TriplesMap
                </b></div>""", unsafe_allow_html=True)
            if st.session_state["last_added_tm_list"]:
                list_to_choose = sorted(tm_dict)
                list_to_choose.insert(0, "Select TriplesMap")
                tm_label_for_pom = st.selectbox("🖱️ Select TriplesMap:*", list_to_choose, key="key_tm_label_for_pom_default",
                    label_visibility="collapsed", index=list_to_choose.index(st.session_state["last_added_tm_list"][0]))
            else:
                list_to_choose = list(reversed(tm_dict))
                list_to_choose.insert(0, "Select TriplesMap")
                tm_label_for_pom = st.selectbox("🖱️ Select TriplesMap:*", list_to_choose, key="key_tm_label_for_pom",
                    label_visibility="collapsed")

        if tm_label_for_pom != "Select TriplesMap":

            tm_iri_for_pom = tm_dict[tm_label_for_pom]
            column_list = [] # will search only if needed, can be slow with failed connections

            # PREDICATE
            with col1:
                st.markdown("""<div class="small-subheading">
                        <b>🅿️ Predicate</b><br>
                    </div>""", unsafe_allow_html=True)

            with col1:
                col1a, col1b = st.columns(2)

            ontology_property_dict = utils.get_ontology_property_dict(st.session_state["g_ontology"])
            custom_property_dict =  utils.get_ontology_property_dict("custom")

            ontology_filter_list = sorted(st.session_state["g_ontology_components_tag_dict"].values())
            if custom_property_dict:
                ontology_filter_list.insert(0, "Custom properties")

            # Filter by ontology
            if len(ontology_filter_list) > 1:
                list_to_choose = ontology_filter_list
                with col1a:
                    ontology_filter_for_predicate = st.selectbox("📡 Filter by ontology (opt):", list_to_choose,
                        placeholder="📡Ontology filter", label_visibility="collapsed", index=None, key="key_ontology_filter_for_predicate")
                    # if ontology_filter_for_predicate:
                    #     st.markdown("""<div class="very-small-info">
                    #         📡 Ontology filter
                    #     </div>""", unsafe_allow_html=True)

                if not ontology_filter_for_predicate:
                    ontology_filter_for_predicate = st.session_state["g_ontology"]
                if ontology_filter_for_predicate == "Custom properties":
                    ontology_filter_for_predicate = "Custom properties"
                else:
                    for ont_label, ont_tag in st.session_state["g_ontology_components_tag_dict"].items():
                        if ont_tag == ontology_filter_for_predicate:
                            ontology_filter_for_predicate = st.session_state["g_ontology_components_dict"][ont_label]
                            break
            else:
                ontology_filter_for_predicate = st.session_state["g_ontology"]

            if not ontology_property_dict and not custom_property_dict:
                with col1b:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ <b>No properties</b> have been added. <small> Go to the <b>🧩 Ontologies</b> page
                        to add ontology and/or custom properties.</small>
                    </div>""", unsafe_allow_html=True)

            if ontology_filter_for_predicate != "Custom properties":

                ontology_property_dict = utils.get_ontology_property_dict(ontology_filter_for_predicate)   # filtered property dictionary
                ontology_superproperty_dict = utils.get_ontology_property_dict(ontology_filter_for_predicate, superproperty=True)

                if ontology_superproperty_dict:   # there exists at least one superproperty (show superproperty filter)
                    with col1a:
                        properties_in_ontology_superproperty_dict = {}
                        superproperties_list = sorted(ontology_superproperty_dict.keys())
                        superproperty = st.selectbox("📡 Filter by superproperty (opt):", superproperties_list,
                            placeholder="📡 Superproperty filter", index=None, label_visibility="collapsed", key="key_superproperty")   # superproperty label
                        # if superproperty:
                        #     st.markdown("""<div class="very-small-info">
                        #         📡 Superproperty filter
                        #     </div>""", unsafe_allow_html=True)


                    if superproperty:   # a superproperty has been selected (filter)
                        properties_in_ontology_superproperty_dict[superproperty] = ontology_superproperty_dict[superproperty]
                        superproperty = ontology_superproperty_dict[superproperty] #we get the superproperty iri
                        for s, p, o in list(set(st.session_state["g_ontology"].triples((None, RDFS.subPropertyOf, superproperty)))):
                            properties_in_ontology_superproperty_dict[utils.get_node_label(s)] = s
                        with col1b:
                            list_to_choose = sorted(properties_in_ontology_superproperty_dict.keys())
                            predicate_list = st.multiselect("🅿️ Select predicate(s):*", list_to_choose,
                                placeholder="🅿️ Select predicates(s)*", label_visibility="collapsed", key="key_predicate")    # predicate list (labels)
                            # if predicate_list:
                            #     st.markdown("""<div class="very-small-info">
                            #         🅿️ Predicates(s)
                            #     </div>""", unsafe_allow_html=True)

                    else:  #no superproperty selected (list all properties)
                        with col1b:
                            if ontology_filter_for_predicate == st.session_state["g_ontology"]:
                                list_to_choose = sorted(list(ontology_property_dict.keys()) + list(custom_property_dict.keys()))
                            else:
                                list_to_choose = sorted(ontology_property_dict.keys())
                            predicate_list = st.multiselect("🅿️ Select predicate(s):*", list_to_choose,
                                placeholder="🅿️ Select predicates(s)*", label_visibility="collapsed", key="key_predicate")    # predicate list (labels)
                            # if predicate_list:
                            #     st.markdown("""<div class="very-small-info">
                            #         🅿️ Predicates(s)
                            #     </div>""", unsafe_allow_html=True)

                else:     #no superproperties exist (no superproperty filter)
                    if len(ontology_filter_list) > 1: # option to filter by ontology
                        with col1b:
                            if ontology_filter_for_predicate == st.session_state["g_ontology"]:
                                list_to_choose = sorted(list(ontology_property_dict.keys()) + list(custom_property_dict.keys()))
                            else:
                                list_to_choose = sorted(ontology_property_dict.keys())
                            predicate_list = st.multiselect("🏷️ Select predicate(s):*", list_to_choose,
                                placeholder="🅿️ Select predicates(s)*", label_visibility="collapsed", key="key_predicate")    # predicate list (labels)
                            # if predicate_list:
                            #     st.markdown("""<div class="very-small-info">
                            #         🅿️ Predicates(s)
                            #     </div>""", unsafe_allow_html=True)

                    else:
                        with col1a:
                            if ontology_filter_for_predicate == st.session_state["g_ontology"]:
                                list_to_choose = sorted(list(ontology_property_dict.keys()) + list(custom_property_dict.keys()))
                            else:
                                list_to_choose = sorted(ontology_property_dict.keys())
                            predicate_list = st.multiselect("🏷️ Select predicate(s):*", list_to_choose,
                                placeholder="🅿️ Select predicates(s)*", label_visibility="collapsed", key="key_predicate")    # predicate list (labels)
                            # if predicate_list:
                            #     st.markdown("""<div class="very-small-info">
                            #         🅿️ Predicates(s)
                            #     </div>""", unsafe_allow_html=True)

            elif ontology_filter_for_predicate == "Custom properties":
                with col1b:
                    list_to_choose = sorted(custom_property_dict.keys())
                    predicate_list = st.multiselect("🏷️ Select predicate(s):*", list_to_choose,
                        placeholder="🅿️ Select predicates(s)*", label_visibility="collapsed", key="key_predicate")   # predicate list (labels)

            predicate_iri_list = []
            for p in predicate_list:        # get the predicates iris
                if p in ontology_property_dict:
                    predicate_iri_list.append(ontology_property_dict[p])
                elif p in custom_property_dict:
                    predicate_iri_list.append(custom_property_dict[p])

            # OBJECT
            with col1:
                st.markdown("""<div class="small-subsection-heading">
                </div>""", unsafe_allow_html=True)

            with col1:
                col1a, col1b = st.columns([1,2])
            with col1a:
                st.markdown("""<div class="small-subsection-heading" style="margin-top:-10px; border-top:none;">
                    <b>🅾️ Object</b>
                </div>""", unsafe_allow_html=True)


            # GENERATION RULE
            with col1b:
                list_to_choose = ["Template 📐", "Constant 🔒", "Reference 📊"]
                om_generation_rule = st.radio("🖱️ Object Map generation rule:*", list_to_choose,
                    horizontal=True, label_visibility="collapsed", key="key_om_generation_rule_radio")

            # TEMPLATE-VALUED OBJECT MAP
            if om_generation_rule == "Template 📐":

                with col1:
                    col1a, col1b, col1c = st.columns([0.8, 1.2, 0.5])

                with col1a:
                    list_to_choose = ["🔒 Fixed part", "📈 Variable part", "🏷️ Fixed namespace", "🗑️ Reset template"]
                    build_template_action_om = st.selectbox("🖱️ Add template part:", list_to_choose,
                        label_visibility="collapsed", key="key_build_template_action_om")

                if build_template_action_om == "🔒 Fixed part":
                    with col1b:
                        om_template_fixed_part = st.text_input("⌨️ Enter fixed part:", key="key_om_fixed_part",
                            placeholder="🔒 Enter fixed part", label_visibility="collapsed")

                        if re.search(r"[ \t]", om_template_fixed_part) and re.search(r"[\n\r<>\"{}|\\^`]", om_template_fixed_part):
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ <b>Spaces and unescaped characters</b> are discouraged.
                            </div>""", unsafe_allow_html=True)

                        elif re.search(r"[ \t]", om_template_fixed_part):
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ <b>Spaces</b> are discouraged.
                            </div>""", unsafe_allow_html=True)

                        elif re.search(r"[\n\r<>\"{}|\\^`]", om_template_fixed_part):
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ <b>Unescaped characters</b> are discouraged.
                            </div>""", unsafe_allow_html=True)

                    with col1c:
                        if om_template_fixed_part:
                            st.button("Add", key="key_save_om_template_fixed_part_button", on_click=save_om_template_fixed_part)

                elif build_template_action_om == "📈 Variable part":

                    column_list, inner_html, ds_for_display, ds_available_flag, hierarchical_data_file_flag = utils.get_column_list_and_give_info(tm_label_for_pom)

                    if not column_list:   #data source is not available (load)
                        with col1b:
                            om_template_variable_part = st.text_input("⌨️ Manually enter column of the data source:*",
                                placeholder="📈 Enter template placeholder", key="key_om_template_variable_part_manual", label_visibility="collapsed")
                            utils.get_very_small_ds_info(column_list, inner_html, ds_for_display, ds_available_flag)
                        with col1c:
                            if om_template_variable_part:
                                st.button("Add", key="save_om_template_variable_part_button", on_click=save_om_template_variable_part)

                    else:  # data source is available
                        with col1b:
                            list_to_choose = column_list.copy()
                            om_template_variable_part = st.selectbox("🖱️ Select the column of the data source:", list_to_choose,
                                placeholder="📈 Select template placeholder", index=None, label_visibility="collapsed", key="key_om_template_variable_part")
                            utils.get_very_small_ds_info(column_list, inner_html, ds_for_display, ds_available_flag)
                            if om_template_variable_part and hierarchical_data_file_flag:
                                om_template_variable_part = st.session_state["saved_paths_dict"][om_template_variable_part][1]

                        with col1c:
                            if om_template_variable_part:
                                st.button("Add", key="save_om_template_variable_part_button", on_click=save_om_template_variable_part)

                    if st.session_state["om_template_list"] and st.session_state["om_template_list"][-1].endswith("}"):
                        if inner_html:
                            inner_html += """&nbsp&nbsp&nbsp•&nbsp&nbsp&nbsp <b>Best practice:</b>
                                Add a fixed part between two variable parts <small>to improve clarity.</small></div>"""
                        else:
                            inner_html += """⚠️ <b>Best practice:</b>
                                Add a fixed part between two variable parts <small>to improve clarity.</small></div>"""

                    if inner_html:
                        with col1:
                            col1a, col1b = st.columns([2,0.5])
                        with col1a:
                            st.markdown(f"""<div class="warning-message">
                                {inner_html}
                            </div>""", unsafe_allow_html=True)

                elif build_template_action_om == "🏷️ Fixed namespace":
                    with col1b:
                        mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
                        list_to_choose = sorted(mapping_ns_dict.keys())
                        if st.session_state["om_template_is_iri_flag"]:
                            list_to_choose.insert(0, "Remove namespace")
                        list_to_choose.insert(0, "Select namespace")
                        om_template_ns_prefix = st.selectbox("🖱️ Select a namespace for the template:", list_to_choose,
                            placeholder="Select namespace*", index=None, label_visibility="collapsed", key="key_om_template_ns_prefix")

                    with col1c:
                        if om_template_ns_prefix == "Remove namespace":
                            st.button("Remove", key="key_add_ns_to_om_template_button", on_click=remove_ns_from_om_template)
                        elif om_template_ns_prefix:
                            om_template_ns = mapping_ns_dict[om_template_ns_prefix]
                            st.button("Add", key="key_add_ns_to_om_template_button", on_click=add_ns_to_om_template)


                elif build_template_action_om == "🗑️ Reset template":
                    with col1b:
                        st.markdown(f"""<div class="warning-message">
                                ⚠️ The current template <b>will be removed</b>.
                            </div>""", unsafe_allow_html=True)
                    with col1c:
                        st.button("Reset", key="key_reset_om_template_button", on_click=reset_om_template)

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

            # CONSTANT-VALUED OBJECT MAP
            if om_generation_rule == "Constant 🔒":

                with col1:
                    col1a, col1b = st.columns(2)

                with col1a:
                    mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
                    list_to_choose = sorted(mapping_ns_dict.keys())
                    list_to_choose.insert(0, "Select namespace (opt)")
                    om_constant_ns_prefix = st.selectbox("🖱️ Select namespace for the constant:", list_to_choose,
                        placeholder="Select namespace (opt)", index=None, label_visibility="collapsed", key="key_om_constant_ns")

                with col1b:
                    om_constant = st.text_input("⌨️ Enter Object Map constant:*", key="key_om_constant",
                        label_visibility="collapsed", placeholder="🔒 Enter constant*")
                    # if om_constant:
                    #     st.markdown("""<div class="very-small-info">
                    #         🔒 Constant
                    #     </div>""", unsafe_allow_html=True)

            # REFERENCED-VALUE OBJECT MAP
            if om_generation_rule ==  "Reference 📊":

                with col1:
                    col1a, col1b = st.columns([2,1])

                column_list, inner_html, ds_for_display, ds_available_flag, hierarchical_data_file_flag = utils.get_column_list_and_give_info(tm_label_for_pom)

                if not column_list:   #data source is not available (load)
                    with col1a:
                        om_column_name = st.text_input("⌨️ Manually enter logical source reference:*",
                            placeholder="📊 Enter reference manually", key="key_om_column_name_manual", label_visibility="collapsed")
                        utils.get_very_small_ds_info(column_list, inner_html, ds_for_display, ds_available_flag)

                else:
                    with col1a:
                        list_to_choose = column_list.copy()
                        list_to_choose.insert(0, "Select reference*")
                        om_column_name = st.selectbox(f"""🖱️ Select reference:*""", list_to_choose,
                            placeholder="📊 Select reference*", index=None, label_visibility="collapsed", key="key_om_column_name")
                        utils.get_very_small_ds_info(column_list, inner_html, ds_for_display, ds_available_flag)
                        if om_column_name and hierarchical_data_file_flag:
                            om_column_name = st.session_state["saved_paths_dict"][om_column_name][1]

                if inner_html:
                    with col1b:
                        st.markdown(f"""<div class="warning-message">
                            {inner_html}
                        </div>""", unsafe_allow_html=True)


            # ADDITIONAL CONFIGURATION
            with col1:
                st.markdown("""<div class="small-subsection-heading">
                    <b>⚙️ Additional Configuration</b><br>
                </div>""", unsafe_allow_html=True)

            with col1:
                col1a, col1b, col1c = st.columns(3)

            # TERM TYPE
            with col1a:
                if om_generation_rule == "Constant 🔒":
                    list_to_choose = ["📘 Literal", "🌐 IRI"]
                else:
                    list_to_choose = ["🌐 IRI", "📘 Literal", "👻 BNode"]

                st.markdown(f"""<div class="very-small-info-top">
                    🆔 Term type*
                </div>""", unsafe_allow_html=True)
                om_term_type = st.selectbox("🆔 Select term type:*", list_to_choose,
                    label_visibility="collapsed", key="key_om_term_type")

            # DATATYPE
            if om_term_type == "📘 Literal":

                with col1b:
                    st.markdown(f"""<div class="very-small-info-top">
                        🔣️ Data type / 🈳 Language tag (opt)
                    </div>""", unsafe_allow_html=True)
                    datatypes_dict = utils.get_datatype_dict()
                    list_to_choose = sorted(datatypes_dict.keys())
                    list_to_choose.insert(0, "🈳 Natural language tag")
                    list_to_choose.insert(0, "✚🔣️ New datatype")
                    om_datatype_option = st.selectbox("🖱️ Select datatype (optional):", list_to_choose,
                        placeholder="No datatype", index=None, label_visibility="collapsed", key="key_om_datatype")

                if om_datatype_option == "✚🔣️ New datatype":
                    with col1b:
                        mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
                        list_to_choose = sorted(mapping_ns_dict.keys())
                        list_to_choose.insert(0, "Select namespace")
                        datatype_prefix = st.selectbox("🖱️ Namespace (opt):", list_to_choose,
                            placeholder="Select namespace", index=None, label_visibility="collapsed", key="key_datatype_prefix")
                        datatype_label = st.text_input("⌨️ Enter datatype:*", key="key_datatype_label",
                            placeholder="Enter datatype*", label_visibility="collapsed")
                        if not datatype_prefix:
                            om_datatype_iri = URIRef(datatype_label)
                        else:
                            NS = Namespace(mapping_ns_dict[datatype_prefix])
                            om_datatype_iri = NS[datatype_label]

                elif om_datatype_option and om_datatype_option != "🈳 Natural language tag":
                    om_datatype_iri = datatypes_dict[om_datatype_option]

                elif om_datatype_option == "🈳 Natural language tag":
                    language_tags_list = utils.get_language_tags_list()

                    with col1b:
                        list_to_choose = sorted(language_tags_list)
                        list_to_choose.insert(0, "✚ New language tag")
                        om_language_tag = st.selectbox("🈳 Select language tag:*", list_to_choose,
                            label_visibility="collapsed", index=list_to_choose.index("en"), key="key_om_language_tag")

                        if om_language_tag == "✚ New language tag":
                            om_language_tag = st.text_input("⌨️ Enter new language tag:*")

            # GRAPH MAP
            col_graph_map = col1c if om_term_type == "📘 Literal" else col1b

            with col_graph_map:
                st.markdown(f"""<div class="very-small-info-top">
                    🗺️️ Graph map (opt)
                </div>""", unsafe_allow_html=True)
                graph_map_dict = utils.get_graph_map_dict()
                list_to_choose = sorted(graph_map_dict.keys())
                list_to_choose.insert(0, "✚🗺️️ New graph map")
                list_to_choose.insert(0, "Default graph map")
                add_om_graph_map_option = st.selectbox("️🗺️️ Graph map (optional):",
                    list_to_choose, label_visibility="collapsed", key="key_add_om_graph_map_option")

            if add_om_graph_map_option == "✚🗺️️ New graph map":
                with col_graph_map:
                    mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
                    list_to_choose = sorted(mapping_ns_dict.keys())
                    om_graph_prefix = st.selectbox("🖱️ Namespace (opt):", list_to_choose,
                        placeholder="Select namespace", index=None, label_visibility="collapsed", key="key_om_graph_prefix")
                    om_graph_input = st.text_input("⌨️ Enter graph map:*", key="key_om_graph_input",
                        placeholder="🗺️️ Enter graph map*", label_visibility="collapsed")
                    if om_graph_prefix:
                        NS = Namespace(mapping_ns_dict[om_graph_prefix])
                        om_graph = NS[om_graph_input]
                    else:
                        om_graph = om_graph_input
            elif add_om_graph_map_option != "Default graph map":
                om_graph = graph_map_dict[add_om_graph_map_option]

        # CHECK EVERYTHING IS READY
        if tm_label_for_pom != "Select TriplesMap":

            pom_complete_flag = True
            inner_html_error = ""
            inner_html_warning = ""

            if not tm_label_for_pom in tm_w_sm_list:
                inner_html_warning += f"""<small>· TriplesMap <b>{tm_label_for_pom}</b> has no Subject Map.
                    It will be invalid without one.</small><br>"""

            if not ontology_property_dict and not custom_property_dict:
                inner_html_error += """<small>· At least one <b>property</b> must be added
                    to allow <b>predicate selection</b>.</small><br>"""
                pom_complete_flag = False
            elif not predicate_list:
                inner_html_error += "<small>· A <b>predicate</b> must be selected.</small><br>"
                pom_complete_flag = False
            elif len(predicate_list) > 1:
                inner_html_warning += """<small>· <b>More than one predicate</b> selected (allowed).</small><br>"""
            for predicate_label in predicate_list:
                if predicate_label in custom_property_dict:
                    inner_html_warning += """<small>· <b>Custom properties</b> lack ontology alignment.
                         An ontology-driven approach is recommended.</small><br>"""
                    break

            if om_generation_rule == "Template 📐":
                if not om_template:
                    inner_html_error += "<small>· The <b>template</b> is empty.</small><br>"
                    pom_complete_flag = False
                elif not st.session_state["om_template_variable_part_flag"]:
                    inner_html_error += """<small>· The <b>template</b> must contain
                        at least one <b>variable part</b>..</small><br>"""
                    pom_complete_flag = False

                if om_template and om_term_type == "🌐 IRI":   # if term type is IRI the NS is recommended
                    if not st.session_state["om_template_is_iri_flag"]:
                        inner_html_warning += """<small>· Term type is <b>IRI</b>.
                            <b>Adding a namespace to the template</b> is recommended.</small><br>"""

                if om_template and om_term_type == "📘 Literal":
                    if st.session_state["om_template_is_iri_flag"]:
                        inner_html_warning += """<small>· Term type is <b>Literal</b>, but you added a <b>namespace</b>
                            to the template.</small><br>"""

            if om_generation_rule == "Constant 🔒":
                if not om_constant:
                    pom_complete_flag = False
                    inner_html_error += "<small>· No <b>constant</b> entered.</small><br>"

                if om_term_type == "📘 Literal":
                    if om_constant_ns_prefix:
                        inner_html_warning += """<small>· Term type is <b>Literal</b>, but you selected a <b>namespace</b>
                            for the constant.</small><br>"""

                elif om_term_type == "🌐 IRI":
                    if om_constant and not om_constant_ns_prefix:
                        if not utils.is_valid_iri(om_constant, delimiter_ending=False):
                            pom_complete_flag = False
                            inner_html_error += """<small>· Term type is <b>IRI</b>.
                                If no namespace is selected, the <b>constant</b> must be a <b>valid IRI</b>.</small><br>"""

            if om_generation_rule == "Reference 📊":
                if column_list and om_column_name == "Select reference*":
                    pom_complete_flag = False
                    inner_html_error += "<small>· The <b>reference</b> has not been selected.</small><br>"
                elif not column_list and not om_column_name:
                    pom_complete_flag = False
                    inner_html_error += "<small>· The <b>reference</b> has not been entered.</small><br>"
                else:
                    if om_term_type == "🌐 IRI":
                        inner_html_warning += """<small>· Term type is <b>IRI</b>.
                            Make sure the values in the referenced column
                            are valid IRIs.</small><br>"""

            if om_term_type == "📘 Literal":

                if om_datatype_option == "✚🔣️ New datatype":
                    if not datatype_label:
                        pom_complete_flag = False
                        inner_html_error += "<small>· You must enter a <b>datatype</b>.</small><br>"
                    else:
                        if not datatype_prefix and not utils.is_valid_iri(datatype_label, delimiter_ending=False):
                            pom_complete_flag = False
                            inner_html_error += """<small>· If no namespace is selected,
                                the <b>datatype</b> must be a <b>valid IRI</b>.</small><br>"""

                elif om_datatype_option == "🈳 Natural language tag":
                    if not om_language_tag:
                        pom_complete_flag = False
                        inner_html_error += "<small>· You must enter a <b>language tag</b>.</small><br>"
                    elif not langcodes.tag_is_valid(om_language_tag):
                        pom_complete_flag = False
                        inner_html_error += """<small>· The <b>language tag</b> is
                            not a <b>valid BCP 47 tag</b>.</small><br>"""

            if add_om_graph_map_option == "✚🗺️️ New graph map":
                if not om_graph_input:
                    pom_complete_flag = False
                    inner_html_error += """<small>· The <b>graph map</b>
                        has not been given.</small><br>"""
                else:
                    if not om_graph_prefix and not utils.is_valid_iri(om_graph_input, delimiter_ending=False):
                        pom_complete_flag = False
                        inner_html_error += """<small>· If no namespace is selected,
                            the <b>graph map</b> must be a <b>valid IRI</b>.</small><br>"""

            # INFO MESSAGES (RIGHT COLUMN)
            with col2b:

                messages = []
                if inner_html_error:
                    messages.append(f"""❌ <b>Predicate-Object Map is incomplete.</b><br>
                    <div style='margin-left: 1.5em;'>{inner_html_error}</div>""")
                if inner_html_warning:
                    messages.append(f"""⚠️ <b>Caution.</b><br>
                    <div style='margin-left: 1.5em;'>{inner_html_warning}</div>""")
                if pom_complete_flag:
                    messages.append("""✔️ All <b>required fields (*)</b> are complete.
                    <small>Double-check the information before saving.</small>""")

                separator = "<hr style='border:0; border-top:1px solid #999; margin:10px 0;'>"
                final_message = separator.join(messages)
                if final_message:
                    st.markdown(f"""<div class="gray-preview-message" style="font-size:13px; line-height:1.2;">
                            {final_message}
                        </div>""", unsafe_allow_html=True)
                    st.write("")
                    st.write("")

            # SAVE BUTTON
            if pom_complete_flag:
                with col1:
                    col1a, col1b = st.columns([6,1])
                with col1b:
                    st.markdown("""<div class="small-subheading">
                            <b>💾 Save</b><br>
                        </div>""", unsafe_allow_html=True)
                    st.session_state["tm_iri_for_pom"] = tm_iri_for_pom             # otherwise it will change value in the on_click function
                    if om_generation_rule == "Template 📐":
                        save_pom_template_button = st.button("Save", on_click=save_pom_template, key="key_save_pom_template_button")
                    elif om_generation_rule == "Constant 🔒":
                        save_pom_constant_button = st.button("Save", on_click=save_pom_constant, key="key_save_pom_constant_button")
                    elif om_generation_rule == "Reference 📊":
                        save_pom_reference_button = st.button("Save", on_click=save_pom_reference, key="key_save_pom_reference_button")

                # PREVIEW
                with col1a:
                    st.markdown("""<div class="small-subheading">
                            <b>🔍 Preview</b><br>
                        </div>""", unsafe_allow_html=True)

                o_is_reference = True if om_generation_rule == "Reference 📊" else False
                language_tag = False
                datatype_iri = False
                if om_term_type == "📘 Literal":
                    if om_datatype_option and om_datatype_option != "🈳 Natural language tag":
                        datatype_iri = om_datatype_iri
                    elif om_datatype_option == "🈳 Natural language tag":
                        language_tag = Literal(om_language_tag)

                # DISPLAY RULE
                is_reference = True if om_generation_rule == "Reference 📊" else False
                if om_generation_rule == "Template 📐":
                    om_rule = om_template
                elif om_generation_rule == "Constant 🔒":
                    om_rule = om_constant
                elif om_generation_rule == "Reference 📊":
                    om_rule = om_column_name
                with col1a:
                    utils.preview_rule(tm_iri_for_pom, predicate_list, om_rule, o_is_reference=o_is_reference,
                        datatype=datatype_iri, language_tag=language_tag)

    # RIGHT COLUMN: SHOW LAST ADDED POM INFO------------------------------------
    with col2b:
        utils.display_right_column_df("predicate-object_maps", "last added Predicate-Object maps")

#_______________________________________________________________________________
# PANEL: MANAGE MAPPING
with tab4:
    col1, col2, col2a, col2b = utils.get_panel_layout()
    with col2b:
        utils.get_corner_status_message(mapping_info=True)

    # SUCCESS MESSAGE: TRIPLESMAP REMOVED---------------------------------------
    # Shows here if "Remove" purple heading is not available
    if not tm_dict and st.session_state["tm_removed_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:1em;
            border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                ✅ The <b>Triplesmap(s)</b> have been removed.
            </div>""", unsafe_allow_html=True)
            st.write("")
        st.session_state["tm_removed_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    # PURPLE HEADING: REMOVE COMPONENT------------------------------------------
    # Only shows if there is at least one TriplesMap
    tm_dict = utils.get_tm_dict()
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
                    🗑️ Remove Component
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["tm_removed_ok_flag"]:  # show message here if "Remove" purple heading is going to be shown
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ The <b>Triplesmap(s)</b> have been removed.
                </div>""", unsafe_allow_html=True)
                st.write("")
            st.session_state["tm_removed_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        if st.session_state["sm_unassigned_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>Subject Map(s)</b> have been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["sm_unassigned_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        if st.session_state["pom_removed_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>Predicate-Object Map(s)</b> have been removed!
                </div>""", unsafe_allow_html=True)
                st.write("")
            st.session_state["pom_removed_ok_flag"] = False
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
            else:
                st.write("")
            if pom_dict:
                list_to_choose.append("🔗 Predicate-Object Map")
            else:
                st.write("")
            component_type_to_remove = st.radio("🖱️ Select an option:*", list_to_choose,
                label_visibility="collapsed", key="key_component_type_to_remove")

        # REMOVE TRIPLESMAPS
        if component_type_to_remove == "🗺️ TriplesMap":
            list_to_choose = sorted(tm_dict.keys())
            if len(list_to_choose) > 1:
                list_to_choose.insert(0, "Select all")
            with col1a:
                tm_to_remove_list = st.multiselect("🖱️ Select TriplesMaps:*", list_to_choose, key="key_tm_to_remove_list")

            if tm_to_remove_list:

                if "Select all" in tm_to_remove_list:
                    deleting_all_tm_flag = True
                    tm_to_remove_list = list(tm_dict.keys())
                    with col1:
                        remove_tm_checkbox = st.checkbox(
                        "🔒 I am sure I want to remove all TriplesMaps",
                        key="remove_tm_checkbox")
                        if remove_tm_checkbox:
                            st.button("Remove", on_click=remove_all_tm)

                else:
                    deleting_all_tm_flag = False
                    with col1:
                        remove_tm_checkbox = st.checkbox(
                        "🔒 I am sure I want to remove the selected TriplesMap(s)",
                        key="remove_tm_checkbox")
                        if remove_tm_checkbox:
                            st.button("Remove", on_click=remove_tm)

                with col1:
                    if deleting_all_tm_flag:
                        st.markdown(f"""<div class="warning-message">
                                ⚠️ If you continue, <b>all TriplesMaps will be removed</b>.
                                <small>Make sure you want to go ahead.</small>
                            </div>""", unsafe_allow_html=True)
                    utils.display_tm_info_for_removal(tm_to_remove_list)

        # REMOVE SUBJECT MAPS
        if component_type_to_remove == "🏷️ Subject Map":
            tm_w_sm_list = []
            for tm_label, tm_iri in tm_dict.items():
                if any(st.session_state["g_mapping"].triples((tm_iri, RML.subjectMap, None))):
                    tm_w_sm_list.append(tm_label)

            with col1a:
                list_to_choose = sorted(tm_w_sm_list)
                if len(list_to_choose) > 1:
                    list_to_choose.insert(0, "Select all")
                tm_to_unassign_sm_list_input = st.multiselect("🖱️ Select TriplesMaps:*", list_to_choose,
                    key="key_tm_to_unassign_sm")

                if "Select all" in tm_to_unassign_sm_list_input:
                    tm_to_unassign_sm_list = tm_w_sm_list
                else:
                    tm_to_unassign_sm_list = tm_to_unassign_sm_list_input

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
                with col1:
                    unassign_all_sm_checkbox = st.checkbox(
                    "🔒 I am sure I want to remove all Subject Map(s)",
                    key="key_unassign_all_sm_checkbox")
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ You are deleting <b>all Subject Maps</b>.
                            <small>Make sure you want to go ahead.</small>
                        </div>""", unsafe_allow_html=True)
                    if unassign_all_sm_checkbox:
                        st.session_state["sm_to_completely_remove_list"] = sm_to_completely_remove_list
                        st.session_state["tm_to_unassign_sm_list"] = tm_to_unassign_sm_list
                        st.button("Remove", on_click=unassign_sm, key="key_unassign_sm_button")

            elif tm_to_unassign_sm_list:
                with col1:
                    unassign_sm_checkbox = st.checkbox(
                    "🔒 I am sure I want to remove the selected Subject Map(s)",
                    key="key_unassign_sm_checkbox")
                if unassign_sm_checkbox:
                    st.session_state["sm_to_completely_remove_list"] = sm_to_completely_remove_list
                    st.session_state["tm_to_unassign_sm_list"] = tm_to_unassign_sm_list
                    with col1:
                        st.button("Remove", on_click=unassign_sm, key="key_unassign_sm_button")

            with col1:
                utils.display_sm_info_for_removal(tm_to_unassign_sm_list)


        # REMOVE PREDICATE-OBJECT MAP
        if component_type_to_remove == "🔗 Predicate-Object Map":

            tm_w_pom_list = []
            for tm_label, tm_iri in tm_dict.items():
                for pom_iri in pom_dict:
                    if tm_iri in pom_dict[pom_iri] and tm_label not in tm_w_pom_list:
                        tm_w_pom_list.append(tm_label)
                        continue

            with col1a:
                list_to_choose = sorted(tm_w_pom_list)
                if len(list_to_choose) > 1:
                    list_to_choose.insert(0, "Select TriplesMap")
                tm_to_remove_pom_label = st.selectbox("🖱️ Select TriplesMap:*", list_to_choose, key="key_tm_to_remove_pom")

            if tm_to_remove_pom_label != "Select TriplesMap":
                tm_to_remove_pom_iri = tm_dict[tm_to_remove_pom_label]
                pom_of_selected_tm_list = []
                for pom_iri in pom_dict:
                    if pom_dict[pom_iri][0] == tm_to_remove_pom_iri:
                        pom_of_selected_tm_list.append(pom_iri)

                if pom_of_selected_tm_list:
                    with col1a:
                        dict_to_choose = {}
                        for pom_iri in pom_dict:
                            if pom_dict[pom_iri][0] == tm_to_remove_pom_iri:
                                dict_to_choose[utils.get_node_label(pom_iri)] = pom_iri
                        list_to_choose = sorted(dict_to_choose.keys())
                        if len(list_to_choose) > 1:
                            list_to_choose.insert(0, "Select all")
                        pom_to_remove_label_list = st.multiselect("🖱️ Select Predicate-Object Maps:*", list_to_choose,
                            key="key_pom_to_remove")

                        if pom_to_remove_label_list:
                            if "Select all" in pom_to_remove_label_list:
                                pom_to_remove_iri_list = []
                                for pom_iri in pom_dict:
                                    if pom_dict[pom_iri][0] == tm_to_remove_pom_iri:
                                        pom_to_remove_iri_list.append(pom_iri)
                                with col1:
                                    remove_all_pom_checkbox = st.checkbox(
                                    f"""🔒 I am  sure I want to remove all Predicate-Object Maps""",
                                    key="key_overwrite_g_mapping_checkbox_new")
                                    if remove_all_pom_checkbox:
                                        st.button("Remove", on_click=remove_pom, key="key_remove_all_pom_button")
                                    st.markdown(f"""<div class="warning-message">
                                            ⚠️ You are deleting <b>all Predicate-Object Maps ({len(pom_to_remove_iri_list)})</b>
                                            of the TriplesMap <b>{tm_to_remove_pom_label}</b>.
                                            <small>Make sure you want to go ahead.</small>
                                        </div>""", unsafe_allow_html=True)

                            else:
                                pom_to_remove_iri_list = []
                                for pom_label in dict_to_choose:
                                    if pom_label in pom_to_remove_label_list:
                                        pom_to_remove_iri_list.append(dict_to_choose[pom_label])
                                with col1:
                                    remove_pom_checkbox = st.checkbox(
                                    f"""🔒 I am  sure I want to remove the selected Predicate-Object Map(s)""",
                                    key="key_overwrite_g_mapping_checkbox_new")
                                    if remove_pom_checkbox:
                                        st.button("Remove", on_click=remove_pom, key="key_remove_pom_button")


            if tm_to_remove_pom_label != "Select TriplesMap":
                rows = [{"Predicate-Object Map": utils.get_node_label(pom_iri),
                    "Rule": pom_dict[pom_iri][5], "Type": pom_dict[pom_iri][4],
                    "Predicate(s)": utils.format_list_for_display(pom_dict[pom_iri][1])}
                    for pom_iri in pom_of_selected_tm_list]
                df = pd.DataFrame(rows)
                df = df.sort_values(by=df.columns[0], ascending=True).reset_index(drop=True)

                if pom_of_selected_tm_list:
                    with col1:
                        st.write("")
                        st.markdown(f"""<div style='font-size: 14px; color: grey;'>
                                🔎 Predicate-Object Maps of TriplesMap <b>{tm_to_remove_pom_label}</b> ({len(df)})
                            </div>""", unsafe_allow_html=True)
                        st.dataframe(df, hide_index=True)


    # SUCCESS MESSAGE: MAPPING CLEANED OK---------------------------------------
    # Before purple heading, since after cleaning, section will not show
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

    # RFBOOKMARK
    # PURPLE HEADING: CLEAN MAPPING---------------------------------------------
    (g_mapping_complete_flag, heading_html, inner_html, tm_wo_sm_list, tm_wo_pom_list,
        pom_wo_om_list, pom_wo_predicate_list) = utils.check_g_mapping(st.session_state["g_mapping"])
    if not g_mapping_complete_flag:
        with col1:
            st.write("_________")
            st.markdown("""<div class="purple-heading">
                    🧹 Clean Mapping
                </div>""", unsafe_allow_html=True)

        tm_to_clean_list = list(set(tm_wo_sm_list).union(tm_wo_pom_list))
        pom_to_clean_list = list(set(pom_wo_om_list).union(pom_wo_predicate_list))

        with col1:
            col1a, col1b = st.columns([3,1])


        with col1b:
            expand_information_toggle = st.toggle(f"""ℹ️ Expand""",
            key="key_expand_information_toggle")
            clean_g_mapping_toggle = st.toggle(f"""🧹 Clean""",
            key="key_clean_g_mapping_toggle")

        with col1a:
            st.write("")
            html_to_show = heading_html + inner_html if expand_information_toggle else heading_html
            st.markdown(f"""<div class="gray-preview-message">
                    {html_to_show}
                </div>""", unsafe_allow_html=True)
            st.write("")


        if clean_g_mapping_toggle:
            clean_g_mapping_checkbox = st.checkbox(
            f"""🔒 I am sure I want to clean mapping {st.session_state["g_label"]}""",
            key="key_clean_g_mapping_checkbox")

            if clean_g_mapping_checkbox:
                st.button("Clean", key="key_clean_g_mapping_button", on_click=clean_g_mapping)

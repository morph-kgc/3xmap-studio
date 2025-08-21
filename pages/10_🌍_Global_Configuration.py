import streamlit as st
import os
import pandas as pd
import time
import re
import pickle
from rdflib import Graph, URIRef, Literal, Namespace, BNode
from rdflib.namespace import split_uri
from rdflib.namespace import RDF, RDFS, DC, DCTERMS, OWL
import utils
import uuid
import io


# Header-----------------------------------
st.markdown("""
<div style="display:flex; align-items:center; background-color:#f0f0f0; padding:12px 18px;
            border-radius:8px; margin-bottom:16px;">
    <img src="https://www.pngmart.com/files/23/Gear-Icon-PNG-Isolated-Photo.png"
         style="width:32px; margin-right:12px;">
    <div>
        <h3 style="margin:0; font-size:1.75rem;">
            <span style="color:#511D66; font-weight:bold; margin-right:12px;">◽◽◽◽◽</span>
            Global Configuration
            <span style="color:#511D66; font-weight:bold; margin-left:12px;">◽◽◽◽◽</span>
        </h3>
        <p style="margin:0; font-size:0.95rem; color:#555;">
            System-wide settings: Load <b>mapping</b> and <b>ontology</b>, and <b>save work</b>.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)
# another option for the icon:
# https://www.clipartmax.com/png/middle/139-1393405_file-gear-icon-svg-wikimedia-commons-gear-icon.png

# Import style-----------------------------
utils.import_st_aesthetics()

# Namespaces-----------------------------------
namespaces = utils.get_predefined_ns_dict()
RML = namespaces["rml"]
RR = namespaces["rr"]
QL = namespaces["ql"]
MAP = namespaces["map"]
CLASS = namespaces["class"]
LS = namespaces["logicalSource"]

# Directories----------------------------------------
#HERE DELETE LAST 2
save_mappings_folder = os.path.join(os.getcwd(), "saved_mappings")  #folder to save mappings (pkl)
if not os.path.isdir(save_mappings_folder):   # create progress folder if it does not exist
    os.makedirs(save_mappings_folder)

export_folder = os.path.join(os.getcwd(), "exported_mappings")    #filder to export mappings (ttl and others)
if not os.path.isdir(export_folder):   # create progress folder if it does not exist
    os.makedirs(export_folder)

ontology_folder = os.path.join(os.getcwd(), "ontologies")
if not os.path.isdir(ontology_folder):   # create progress folder if it does not exist
    os.makedirs(ontology_folder)


# Initialise session state variables----------------------------------------
#TAB1
if "g_mapping" not in st.session_state:
    st.session_state["g_mapping"] = Graph()
if "g_label" not in st.session_state:
    st.session_state["g_label"] = ""
if "g_label_temp_new" not in st.session_state:
    st.session_state["g_label_temp_new"] = ""
if "new_g_mapping_created_ok_flag" not in st.session_state:
    st.session_state["new_g_mapping_created_ok_flag"] = False
if "key_mapping_uploader" not in st.session_state:
    st.session_state["key_mapping_uploader"] = None
if "g_label_temp_existing" not in st.session_state:
    st.session_state["g_label_temp_existing"] = ""
if "existing_g_mapping_loaded_ok_flag" not in st.session_state:
    st.session_state["existing_g_mapping_loaded_ok_flag"] = False
if "g_mapping_source_cache" not in st.session_state:
    st.session_state["g_mapping_source_cache"] = ["",""]
if "original_g_size_cache" not in st.session_state:
    st.session_state["original_g_size_cache"] = 0
if "cached_mapping_retrieved_ok_flag" not in st.session_state:
    st.session_state["cached_mapping_retrieved_ok_flag"] = False

#TAB2
if "g_ontology" not in st.session_state:
    st.session_state["g_ontology"] = Graph()
if "g_ontology_label" not in st.session_state:
    st.session_state["g_ontology_label"] = ""
if "g_ontology_loaded_ok_flag" not in st.session_state:
    st.session_state["g_ontology_loaded_ok_flag"] = False
if "ontology_link" not in st.session_state:
    st.session_state["ontology_link"] = ""
if "key_ontology_uploader" not in st.session_state:
    st.session_state["key_ontology_uploader"] = None
if "ontology_file" not in st.session_state:
    st.session_state["ontology_file"] = None
if "g_ontology_from_file_candidate" not in st.session_state:
    st.session_state["g_ontology_from_file_candidate"] = Graph()
if "g_ontology_from_link_candidate" not in st.session_state:
    st.session_state["g_ontology_from_link_candidate"] = Graph()
if "g_ontology_components_dict" not in st.session_state:
    st.session_state["g_ontology_components_dict"] = {}
if "g_ontology_reduced_ok_flag" not in st.session_state:
    st.session_state["g_ontology_reduced_ok_flag"] = False
if "g_ontology_discarded_ok_flag" not in st.session_state:
    st.session_state["g_ontology_discarded_ok_flag"] = False

#TAB3
if "ns_dict" not in st.session_state:
    st.session_state["ns_dict"] = {}
if "custom_ns_bound_ok_flag" not in st.session_state:
    st.session_state["custom_ns_bound_ok_flag"] = False
if "ns_bound_ok_flag" not in st.session_state:
    st.session_state["ns_bound_ok_flag"] = False
if "ns_unbound_ok_flag" not in st.session_state:
    st.session_state["ns_unbound_ok_flag"] = False
if "last_added_ns_list" not in st.session_state:
    st.session_state["last_added_ns_list"] = []

#TAB4
if "progress_saved_ok_flag" not in st.session_state:
    st.session_state["progress_saved_ok_flag"] = False
if "mapping_downloaded_ok_flag" not in st.session_state:
    st.session_state["mapping_downloaded_ok_flag"] = False


if "overwrite_checkbox" not in st.session_state:
    st.session_state["overwrite_checkbox"] = False
if "new_ns_iri" not in st.session_state:
    st.session_state["new_ns_iri"] = ""
if "new_ns_prefix" not in st.session_state:
    st.session_state["new_ns_prefix"] = ""
if "save_progress_succes" not in st.session_state:
    st.session_state["save_progress_success"] = False
if "export_success" not in st.session_state:
    st.session_state["export_success"] = False
if "export_file" not in st.session_state:
    st.session_state["export_file"] = False
if "save_progress_filename_key" not in st.session_state:
    st.session_state["save_progress_filename_key"] = ""
if "load_success" not in st.session_state:
    st.session_state["load_success"] = ""

if "load_ontology_from_file_button_flag" not in st.session_state:
    st.session_state["load_ontology_from_file_button_flag"] = False
if "ontology_source" not in st.session_state:
    st.session_state["ontology_source"] = ""


# Define on_click functions-------------------------------------------------
#TAB1
def create_new_g_mapping():
    st.session_state["g_label"] = st.session_state["g_label_temp_new"]   # consolidate g_label
    st.session_state["g_mapping"] = Graph()   # create a new empty mapping
    st.session_state["g_mapping_source_cache"] = ["scratch", ""]   #cache info on the mapping source
    st.session_state["new_g_mapping_created_ok_flag"] = True   #flag for success mesagge
    st.session_state["last_added_ns_list"] = []    # empty list of last added ns
    # reset fields___________________________
    st.session_state["key_g_label_temp_new"] = ""

def cancel_create_new_g_mapping():
    # reset fields___________________________
    st.session_state["key_g_label_temp_new"] = ""

def create_new_g_mapping_and_save_current_one():
    # save current mapping to file_____________
    utils.save_mapping_to_file(save_g_filename)
    #create new mapping_________________________
    st.session_state["g_label"] = st.session_state["g_label_temp_new"]
    st.session_state["g_mapping"] = Graph()
    st.session_state["g_mapping_source_cache"] = ["scratch", ""]
    st.session_state["new_g_mapping_created_ok_flag"] = True
    st.session_state["last_added_ns_list"] = []    # empty list of last added ns
    # reset fields___________________________
    st.session_state["key_g_label_temp_new"] = ""

def load_existing_g_mapping():
    st.session_state["g_label"] = st.session_state["g_label_temp_existing"]   # consolidate g_label
    st.session_state["original_g_size_cache"] = utils.get_number_of_tm(st.session_state["candidate_g_mapping"])
    st.session_state["g_mapping"] = st.session_state["candidate_g_mapping"]   # consolidate the loaded mapping
    st.session_state["g_mapping_source_cache"] = ["file", selected_load_file.name]
    st.session_state["existing_g_mapping_loaded_ok_flag"] = True
    st.session_state["last_added_ns_list"] = []    # empty list of last added ns
    # reset fields___________________________
    st.session_state["key_mapping_uploader"] = str(uuid.uuid4())
    st.session_state["key_g_label_temp_existing"] = ""

def cancel_load_existing_g_mapping():
    # reset fields___________________________
    st.session_state["key_mapping_uploader"] = str(uuid.uuid4())
    st.session_state["key_g_label_temp_existing"] = ""

def load_existing_g_mapping_and_save_current_one():
    # save current mapping to file_____________
    utils.save_mapping_to_file(save_g_filename)
    #create new mapping_________________________
    st.session_state["original_g_size_cache"] = utils.get_number_of_tm(st.session_state["candidate_g_mapping"])
    st.session_state["g_label"] = st.session_state["g_label_temp_existing"]   #we consolidate g_label
    st.session_state["g_mapping"] = st.session_state["candidate_g_mapping"]   #we consolidate the loaded mapping
    st.session_state["g_mapping_source_cache"] = ["file", selected_load_file.name]
    st.session_state["existing_g_mapping_loaded_ok_flag"] = True
    st.session_state["last_added_ns_list"] = []    # empty list of last added ns
    # reset fields___________________________
    st.session_state["key_mapping_uploader"] = str(uuid.uuid4())
    st.session_state["key_g_label_temp_existing"] = ""

def retrieve_cached_mapping():
    st.session_state["g_label"] = cached_mapping_name    # g label
    with open(pkl_cache_file_path, "rb") as f:     # load mapping
        st.session_state["g_mapping"] = utils.load_mapping_from_file(f)
    st.session_state["last_added_ns_list"] = []    # empty list of last added ns
    st.session_state["cached_mapping_retrieved_ok_flag"] = True

#TAB2
def load_ontology_from_link():
    st.session_state["g_ontology"] = st.session_state["g_ontology_from_link_candidate"]  # consolidate ontology graph
    st.session_state["g_ontology_label"] = utils.get_ontology_human_readable_name(st.session_state["g_ontology"], source_link=st.session_state["key_ontology_link"])
    st.session_state["g_ontology_loaded_ok_flag"] = True
    # save ontology info to dict___________________________
    st.session_state["g_ontology_components_dict"][st.session_state["g_ontology_label"]]=st.session_state["g_ontology"]
    # reset fields___________________________
    st.session_state["key_ontology_link"] = ""
    st.session_state["ontology_link"] = ""

def load_ontology_from_file():
    st.session_state["g_ontology"] = st.session_state["g_ontology_from_file_candidate"]  # consolidate ontology graph
    st.session_state["g_ontology_label"] = utils.get_ontology_human_readable_name(st.session_state["g_ontology"], source_file=st.session_state["ontology_file"])
    st.session_state["g_ontology_loaded_ok_flag"] = True
    # save ontology info___________________________
    st.session_state["g_ontology_components_dict"][st.session_state["g_ontology_label"]]=st.session_state["g_ontology"]
    # reset fields___________________________
    st.session_state["key_ontology_uploader"] = str(uuid.uuid4())
    st.session_state["ontology_file"] = None

def extend_ontology_from_link():
    g_ontology_new_part = st.session_state["g_ontology_from_link_candidate"]
    g_ontology_new_part_label = utils.get_ontology_human_readable_name(g_ontology_new_part, source_link=st.session_state["key_ontology_link"])
    st.session_state["g_ontology_loaded_ok_flag"] = True
    # save ontology info___________________________
    st.session_state["g_ontology_components_dict"][g_ontology_new_part_label] = g_ontology_new_part
    # merge both ontologies___________________
    for triple in g_ontology_new_part:
        st.session_state["g_ontology"].add(triple)
    # reset fields___________________________
    st.session_state["key_ontology_link"] = ""
    st.session_state["ontology_link"] = ""
    st.session_state["key_extend_ontology_selected_option"] = "🌐 URL"

def extend_ontology_from_file():
    g_ontology_new_part = st.session_state["g_ontology_from_file_candidate"]
    g_ontology_new_part_label = utils.get_ontology_human_readable_name(g_ontology_new_part, source_file=st.session_state["ontology_file"])
    st.session_state["g_ontology_loaded_ok_flag"] = True
    # save ontology info___________________________
    st.session_state["g_ontology_components_dict"][g_ontology_new_part_label] = g_ontology_new_part
    # merge both ontologies___________________
    for triple in g_ontology_new_part:
        st.session_state["g_ontology"].add(triple)
    # reset fields___________________________
    st.session_state["key_ontology_uploader"] = str(uuid.uuid4())
    st.session_state["ontology_file"] = None
    st.session_state["key_extend_ontology_selected_option"] = "📁 File"

def reduce_ontology():
    st.session_state["g_ontology_reduced_ok_flag"] = True
    # drop the given ontology components from the dictionary
    st.session_state["g_ontology_components_dict"] = {label: ont for label, ont in st.session_state["g_ontology_components_dict"].items() if label not in ontologies_to_drop_list}
    # merge remaining ontology components
    st.session_state["g_ontology"] = Graph()
    for label, ont in st.session_state["g_ontology_components_dict"].items():
        st.session_state["g_ontology"] += ont  # merge the graphs using RDFLib's += operator

def discard_ontology():
    st.session_state["g_ontology_discarded_ok_flag"] = True
    st.session_state["g_ontology"] = Graph()
    st.session_state["g_ontology_components_dict"] = {}
    st.session_state["g_ontology_label"] = ""


#TAB3
def bind_custom_namespace():
    st.session_state["g_mapping"].bind(prefix_input, iri_input)  # bind the new namespace
    st.session_state["last_added_ns_list"].insert(0, st.session_state["new_ns_prefix"])  # to display last added ns
    st.session_state["custom_ns_bound_ok_flag"] = True   #for success message
    # reset fields
    st.session_state["key_iri_input"] = ""
    st.session_state["key_prefix_input"] = ""
    st.session_state["key_add_ns_radio"] = "✏️ Custom"

def bind_predefined_namespaces():
    for prefix in predefined_ns_to_bind_list:
        st.session_state["g_mapping"].bind(prefix, predefined_ns_dict[prefix])  # bind the new namespace
        st.session_state["last_added_ns_list"].insert(0, prefix)   # to display last added ns
    st.session_state["ns_bound_ok_flag"] = True    #for success message
    # reset fields
    st.session_state["key_predefined_ns_to_bind_multiselect"] = []
    st.session_state["key_add_ns_radio"] = "📋 Predefined"

def bind_all_predefined_namespaces():
    for prefix in predefined_ns_dict:
        if prefix not in mapping_ns_dict:
            st.session_state["g_mapping"].bind(prefix, predefined_ns_dict[prefix])  # bind the new namespace
            st.session_state["last_added_ns_list"].insert(0, prefix)   # to display last added ns
    st.session_state["ns_bound_ok_flag"] = True   #for success message
    # reset fields
    st.session_state["key_add_ns_radio"] = "✏️ Custom"

def bind_ontology_namespaces():
    for prefix in ontology_ns_to_bind_list:
        st.session_state["g_mapping"].bind(prefix, ontology_ns_dict[prefix])  # bind the new namespace
        st.session_state["last_added_ns_list"].insert(0, prefix)   # to display last added ns
    st.session_state["ns_bound_ok_flag"] = True   # for success message
    # reset fields
    st.session_state["key_ontology_ns_to_bind_multiselect"] = []
    st.session_state["key_add_ns_radio"] = "🧩 Ontology"

def bind_all_ontology_namespaces():
    for prefix in ontology_ns_dict:
        if prefix not in mapping_ns_dict:
            st.session_state["g_mapping"].bind(prefix, ontology_ns_dict[prefix])  # bind the new namespace
            st.session_state["last_added_ns_list"].insert(0, prefix)   # to display last added ns
    st.session_state["ns_bound_ok_flag"] = True   # for success message
    # reset fields
    st.session_state["key_add_ns_radio"] = "✏️ Custom"

def unbind_namespaces():
    for prefix in ns_to_unbind_list:
        st.session_state["g_mapping"].namespace_manager.bind(prefix, None, replace=True)
        if prefix in st.session_state["last_added_ns_list"]:
            st.session_state["last_added_ns_list"].remove(prefix)   # to remove from last added if it is there
    st.session_state["ns_unbound_ok_flag"] = True
    st.session_state["key_unbind_multiselect"] = []   # reset the variables

def unbind_all_namespaces():
    for prefix in mapping_ns_dict:
        st.session_state["g_mapping"].namespace_manager.bind(prefix, None, replace=True)
        if prefix in st.session_state["last_added_ns_list"]:
            st.session_state["last_added_ns_list"].remove(prefix)    # to remove from last added if it is there
    st.session_state["ns_unbound_ok_flag"] = True
    st.session_state["key_unbind_multiselect"] = []   # reset the variables


#TAB4
def save_progress():
    #remove all cache pkl files in cwd
    for file in existing_pkl_file_list:
        filepath = os.path.join(os.getcwd(), file)
        if os.path.isfile(file):
            os.remove(file)
    #save progress
    with open(pkl_cache_filename, "wb") as f:
        pickle.dump(st.session_state["g_mapping"], f)
    st.session_state["overwrite_checkbox"] = False
    #reset fields
    st.session_state["progress_saved_ok_flag"] = True






def export_mapping_to_file():
    st.session_state["g_mapping"].serialize(destination=export_file_path, format=export_format)
    st.session_state["export_file_input"] = ""
    st.session_state["export_success"] = True




#____________________________________________________________
# PANELS OF THE PAGE (tabs)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Select Mapping",
    "Load Ontology", "Configure Namespaces", "Save Mapping", "Set Style"])

#____________________________________________________________
# PANEL: "SELECT MAPPING"
with tab1:
    st.write("")
    st.write("")

    # OPTION: Create new mapping------------------------------
    col1,col2,col3 = st.columns([2,0.5, 1])
    with col1:
        st.markdown("""<div class="purple-heading">
            📄 Create New Mapping
        </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([2,1])

    if st.session_state["new_g_mapping_created_ok_flag"]:
        with col1a:
            st.markdown(f"""<div class="custom-success">
                ✅ The mapping <b>{st.session_state["g_label"]}</b> has been created!
            </div>""", unsafe_allow_html=True)
        st.session_state["new_g_mapping_created_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.cache_data.clear()
        st.rerun()

    with col1a:
        st.session_state["g_label_temp_new"] = st.text_input("⌨️ Enter mapping label:", # just a candidate until confirmed
        key="key_g_label_temp_new")

    # A mapping has not been loaded yet__________
    if not st.session_state["g_mapping"]:   #a mapping has not been loaded yet (or loaded mapping is empty)

        if st.session_state["g_label_temp_new"]:  #after a new label has been given
            with col1a:
                st.button("Create", on_click=create_new_g_mapping)


    # A mapping is currently loaded__________
    else:  #a mapping is currently loaded (ask if overwrite)
        with col1:
            col1a, col1b = st.columns([2,1])
        if st.session_state["g_label_temp_new"]:   #after a label and file have been given
            with col1a:
                st.write("")
                st.markdown(f"""<span style="font-size:1.1em; font-weight:bold;">
                ⚠️ The mapping <b style="color:#F63366;">{st.session_state["g_label"]}</b>
                is already loaded!</span><br>""",
                    unsafe_allow_html=True)
                st.write("")

            with col1:
                col1a, col1b = st.columns([1,2])
            with col1a:
                overwrite_g_selection = st.radio("What would you like to do?:",
                    ["✏️ Overwrite", "💾 Save", "🛑 Cancel"],
                    key="key_overwrite_selection_radio_new")

            if overwrite_g_selection == "✏️ Overwrite":
                with col1b:
                    st.write("")
                    st.markdown(f"""
                        <div style="background-color:#F5F5F5; border:1px dashed #511D66;
                        padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                            🗑️ Mapping <b>{st.session_state["g_label"]}</b> will be overwritten.<br>
                            🆕 Mapping <b>{st.session_state["g_label_temp_new"]}</b> will be created.
                        </span></div>""", unsafe_allow_html=True)
                with col1b:
                    overwrite_g_mapping_checkbox = st.checkbox(
                    f""":gray-badge[⚠️ I am completely sure I want to overwrite mapping {st.session_state["g_label"]}]""",
                    key="key_overwrite_g_mapping_checkbox_new")

                if overwrite_g_mapping_checkbox:
                    with col1b:
                        st.button(f"""Overwrite and create""", on_click=create_new_g_mapping, key="key_overwrite_new_button")

            elif overwrite_g_selection == "🛑 Cancel":
                with col1b:
                    st.write("")
                    st.markdown(f"""<div style="background-color:#F5F5F5; border:1px dashed #511D66;
                        padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                            🛑 Mapping <b>{st.session_state["g_label_temp_new"]}</b> will not be created.<br>
                            🔄 You will keep working with mapping <b>{st.session_state["g_label"]}</b>.
                        </span></div>""", unsafe_allow_html=True)
                with col1b:
                    st.button(f"""Cancel""",  on_click=cancel_create_new_g_mapping, key="key_cancel_new_button")


            elif overwrite_g_selection == "💾 Save": #for the save case we need to ask for the filename before confirming

                if st.session_state["g_mapping_source_cache"][0] == "file":   # if current mapping was loaded from file
                    default_ext = os.path.splitext(st.session_state["g_mapping_source_cache"][1])[1]
                else:
                    default_ext = ".pkl"

                with col1b:
                    save_g_filename = st.text_input(
                    f"⌨️ Enter filename:",
                    value = st.session_state["g_label"])

                with col1b:
                    ext_options = list(utils.get_g_mapping_file_formats_dict().values())
                    default_index = ext_options.index(default_ext)
                    ext = st.selectbox("🖱️ Select file extension", ext_options,
                        index=default_index)
                save_g_filename += ext

                if not save_g_filename.startswith("."):
                    with col1b:
                        st.write("")
                        st.markdown(f"""
                            <div style="background-color:#F5F5F5; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                <span style="font-size:0.95rem;">
                                    💾️ Current mapping will be saved to to file <b>{save_g_filename}</b>.<br>
                                    🆕 Mapping <b>{st.session_state["g_label_temp_new"]}</b> will be created</b>.
                            </span></div>""", unsafe_allow_html=True)

                existing_files_list = [f for f in os.listdir(save_mappings_folder)]

                if save_g_filename in existing_files_list:
                    with col1b:
                        st.markdown(f"""<div style="background-color:#fff3cd; padding:0.8em;
                            border-radius:5px; color:#856404; border:1px solid #ffeeba; font-size:0.92rem;">
                                ⚠️ A file named <b>{save_g_filename}</b> already exists
                                in folder. Please confirm below you want to overwrite it, or enter a different filename.
                            </div>""", unsafe_allow_html=True)
                        st.write("")

                        overwrite_pkl_file_checkbox = st.checkbox(
                            f""":gray-badge[I am completely sure I want to overwrite the file {save_g_filename}]""",
                            key="key_overwrite_pkl_file_checkbox_existing")

                        if overwrite_pkl_file_checkbox:
                            st.button(f"""Save and create""",
                             on_click=create_new_g_mapping_and_save_current_one,  key="key_save_new_button_1")
                else:
                    if save_g_filename:
                        with col1b:
                            st.button(f"""Save and create""",
                             on_click=create_new_g_mapping_and_save_current_one,  key="key_save_new_button_2")

    with col1:
        st.write("______")


    # OPTION: Import existing mapping--------------------------------------
    with col1:
        st.markdown("""<div class="purple-heading">
                📁 Load Existing Mapping
            </div>""", unsafe_allow_html=True)
        st.write("")


    mapping_format_list = list(utils.get_g_mapping_file_formats_dict().values())


    with col1:
        col1a, col1b = st.columns([2,1])

    if st.session_state["existing_g_mapping_loaded_ok_flag"]:
        with col1a:
            st.write("")
            st.markdown(f"""<div class="custom-success">
                ✅ The mapping <b>{st.session_state["g_label"]}</b> has been loaded!
            </div>""", unsafe_allow_html=True)
        st.session_state["existing_g_mapping_loaded_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    with col1a:
        selected_load_file = st.file_uploader(f"""🖱️
        Upload mapping file""", type=mapping_format_list, key=st.session_state["key_mapping_uploader"])

    with col1b:
        if selected_load_file:
            st.session_state["g_label_temp_existing"] = st.text_input("⌨️ Enter mapping label:",   #just candidate until confirmed
                key="key_g_label_temp_existing", value=os.path.splitext(selected_load_file.name)[0])

    if selected_load_file:
        st.session_state["candidate_g_mapping"] = utils.load_mapping_from_file(
            selected_load_file)   #we load the mapping as a candidate (until confirmed)


    # A mapping has not been loaded yet__________
    if not st.session_state["g_mapping"]:   # a mapping has not been loaded yet (or loaded mapping is empty)
        with col1:
            col1a, col1b = st.columns([2,1])

        if st.session_state["g_label_temp_existing"] and selected_load_file:  # after a label and file have been given
            with col1:
                col1a, col1b = st.columns([1,2])
            with col1a:
                st.button("Load", on_click=load_existing_g_mapping, key="key_save_existing_button_1")


    # A mapping is currently loaded__________
    else:  #a mapping is currently loaded (ask if overwrite or save)
        with col1:
            col1a, col1b = st.columns([2,1])
        if st.session_state["g_label_temp_existing"] and selected_load_file:   #after a label and file have been given
            with col1a:
                st.write("")
                st.markdown(f"""<span style="font-size:1.1em; font-weight:bold;">
                ⚠️ The mapping <b style="color:#F63366;">{st.session_state["g_label"]}</b>
                is already loaded!</span><br>""",
                    unsafe_allow_html=True)
                st.write("")


            with col1:
                col1a, col1b = st.columns([1,2])
            with col1a:
                overwrite_g_selection = st.radio("What would you like to do?:",
                    ["✏️ Overwrite", "💾 Save", "🛑 Cancel"],
                    key="key_overwrite_selection_radio_existing")

            if overwrite_g_selection == "✏️ Overwrite":
                with col1b:
                    st.write("")
                    st.markdown(f"""
                        <div style="background-color:#F5F5F5; border:1px dashed #511D66;
                        padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                            🗑️ Mapping <b>{st.session_state["g_label"]}</b> will be overwritten.<br>
                            🆕 Mapping <b>{st.session_state["g_label_temp_existing"]}</b> will be created.
                        </span></div>""", unsafe_allow_html=True)
                with col1b:
                    overwrite_g_mapping_checkbox = st.checkbox(
                    f""":gray-badge[⚠️ I am completely sure I want to overwrite mapping {st.session_state["g_label"]}]""",
                    key="key_overwrite_g_mapping_checkbox_existing")

                if overwrite_g_mapping_checkbox:
                    with col1b:
                        st.button(f"""Overwrite and create""", on_click=load_existing_g_mapping, key="key_overwrite_existing_button")

            elif overwrite_g_selection == "🛑 Cancel":
                with col1b:
                    st.write("")
                    st.markdown(f"""<div style="background-color:#F5F5F5; border:1px dashed #511D66;
                        padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                            🛑 Mapping <b>{st.session_state["g_label_temp_existing"]}</b> will not be created.<br>
                            🔄 You will keep working with mapping <b>{st.session_state["g_label"]}</b>.
                        </span></div>""", unsafe_allow_html=True)
                with col1b:
                    st.button(f"""Cancel""", on_click=cancel_load_existing_g_mapping, key="key_cancel_existing_button")

            elif overwrite_g_selection == "💾 Save": #for the save case we need to ask for the filename before confirming

                if st.session_state["g_mapping_source_cache"][0] == "file":   # if current mapping was loaded from file
                    default_ext = os.path.splitext(st.session_state["g_mapping_source_cache"][1])[1]
                else:
                    default_ext = ".pkl"

                with col1b:
                    save_g_filename = st.text_input(
                    f"⌨️ Enter filename:",
                    value = st.session_state["g_label"])

                with col1b:
                    ext_options = list(utils.get_g_mapping_file_formats_dict().values())
                    default_index = ext_options.index(default_ext)
                    ext = st.selectbox("🖱️ Select file extension", ext_options,
                        index=default_index)
                save_g_filename += ext

                if not save_g_filename.startswith("."):
                    with col1b:
                        st.write("")
                        st.markdown(f"""
                            <div style="background-color:#F5F5F5; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                <span style="font-size:0.95rem;">
                                    💾️ Current mapping will be saved to to file <b>{save_g_filename}</b>.<br>
                                    🆕 Mapping <b>{st.session_state["g_label_temp_existing"]}</b> will be created</b>.
                            </span></div>""", unsafe_allow_html=True)

                existing_files_list = [f for f in os.listdir(save_mappings_folder)]

                if save_g_filename in existing_files_list:
                    with col1b:
                        st.markdown(f"""<div class="custom-warning-small">
                                ⚠️ A file named <b>{save_g_filename}</b> already exists
                                in folder. Please confirm below you want to overwrite it, or enter a different filename.
                            </div>""", unsafe_allow_html=True)
                        st.write("")

                        overwrite_pkl_file_checkbox = st.checkbox(
                            f""":gray-badge[I am completely sure I want to overwrite the file {save_g_filename}]""",
                            key="key_overwrite_pkl_file_checkbox_existing")

                        if overwrite_pkl_file_checkbox:
                            st.button(f"""Save and create""",
                             on_click=load_existing_g_mapping_and_save_current_one,  key="key_save_existing_button_2")
                else:
                    if save_g_filename:
                        with col1b:
                            st.button(f"""Save and create""",
                             on_click=load_existing_g_mapping_and_save_current_one,  key="key_save_existing_button_3")


    if st.session_state["cached_mapping_retrieved_ok_flag"]:
        with col3:
            st.write("")
            st.markdown(f"""<div class="custom-success">
                ✅ Mapping <b>{st.session_state["g_label"]}</b> has been retrieved from cache!
            </div>""", unsafe_allow_html=True)
        st.session_state["cached_mapping_retrieved_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    # g mapping INFORMATION BOX--------------------------------------------
    with col3:
        if st.session_state["g_label"]:
            if st.session_state["g_mapping_source_cache"][0] == "file":
                st.markdown(f"""<div class="green-status-message">
                        <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                        style="vertical-align:middle; margin-right:8px; height:20px;">
                        You are working with mapping
                        <b style="color:#F63366;">{st.session_state["g_label"]}</b>.
                        <ul style="font-size:0.85rem; margin-top:6px; margin-left:15px; padding-left:10px;">
                            <li>Mapping was loaded from file <b>{st.session_state["g_mapping_source_cache"][1]}</b></li>
                            <li>When loaded, mapping had <b>{st.session_state["original_g_size_cache"]} TriplesMaps</b></li>
                            <li>Now mapping has <b>{utils.get_number_of_tm(st.session_state["g_mapping"])} TriplesMaps<b/></li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="green-status-message">
                        <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                        style="vertical-align:middle; margin-right:8px; height:20px;">
                        You are working with mapping
                        <b style="color:#F63366;">{st.session_state["g_label"]}</b>.
                        <ul style="font-size:0.85rem; margin-top:6px; margin-left:15px; padding-left:10px;">
                            <li>Mapping was created <b>from scratch</b></li>
                            <li>Mapping has <b>{utils.get_number_of_tm(st.session_state["g_mapping"])} TriplesMaps<b/></li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)


        else:
            st.markdown("""<div class="gray-status-message">
                ✖️ <b style="color:#511D66;">No mapping</b> has been loaded yet.
            </div>
            """, unsafe_allow_html=True)

    # option to retrieve mapping from cache-----------------------------------
    if not st.session_state["g_label"]:
        pkl_cache_filename = next((f for f in os.listdir() if f.endswith("_cache__.pkl")), None)  # fallback if no match is foun
        pkl_cache_file_path = os.path.join(os.getcwd(), pkl_cache_filename)
        st.write("HERE", pkl_cache_file_path)
        cached_mapping_name = pkl_cache_filename.split("_cache__.pkl")[0]
        cached_mapping_name = cached_mapping_name.split("__")[1]

        if pkl_cache_filename:
            with col3:
                st.write("")
                overwrite_checkbox = st.checkbox(
                    "🗃️ Retrieve cached mapping",
                    key="overwrite_checkbox")
                if overwrite_checkbox:
                    st.markdown(f"""<div class="info-message-small">
                            ℹ️ Mapping <b style="color:#F63366;">
                            {cached_mapping_name}</b> will be loaded.
                        </span></div>""", unsafe_allow_html=True)
                    st.write("")
                    st.button("Load", key="key_retrieve_cached_mapping_button", on_click=retrieve_cached_mapping)


#_______________________________________________________

#________________________________________________
# PANEL: "LOAD ONTOLOGY"
with tab2:

    col1, col2 = st.columns([2,1.5])

    if st.session_state["g_ontology_loaded_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="custom-success">
                ✅ The ontology <b style="color:#F63366;">{st.session_state["g_ontology_label"]}</b> has been loaded!
            </div>""", unsafe_allow_html=True)
        st.session_state["g_ontology_loaded_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    if st.session_state["g_ontology_reduced_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="custom-success">
                ✅ The ontology has been reduced!
            </div>""", unsafe_allow_html=True)
        st.session_state["g_ontology_reduced_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    if st.session_state["g_ontology_discarded_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="custom-success">
                ✅ The ontology has been discarded!
            </div>""", unsafe_allow_html=True)
        st.session_state["g_ontology_discarded_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    with col2:
        col2a,col2b = st.columns([1,2])
        with col2b:
            st.write("")
            st.write("")

            if st.session_state["g_ontology"]:
                if len(st.session_state["g_ontology_components_dict"]) > 1:
                    ontology_items = '\n'.join([f"""<li><b style="color:#F63366;">{ont}</b></li>""" for ont in st.session_state["g_ontology_components_dict"]])
                    st.markdown(f"""<div class="green-status-message">
                            🧩 Your <b>ontology</b> is the merger of:
                        <ul>
                            {ontology_items}
                        </ul></div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="green-status-message">
                            🧩 The ontology <b style="color:#F63366;">
                            {next(iter(st.session_state["g_ontology_components_dict"]))}</b>
                            is loaded.
                        </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="gray-status-message">
                        🚫 <b>No ontology</b> is loaded.
                    </div>
                """, unsafe_allow_html=True)

    with col2:
        col2a,col2b = st.columns([2,1.5])
    with col2b:
        st.write("")
        st.write("")
        st.markdown("""
        <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
            <span style="font-size:0.95rem;">
        🐢 Certain options in this panel can be a bit slow, some patience may be required.
        </span>
        </div>
        """, unsafe_allow_html=True)


    #LOAD ONTOLOGY FROM URL___________________________________
    if not st.session_state["g_ontology"]:   #no ontology is loaded yet
        with col1:
            st.write("")
            st.write("")
            st.markdown("""<div class="purple-heading">
                    🌐 Load Ontology from URL
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a,col1b = st.columns([2,1])

        with col1a:
            ontology_link = st.text_input("⌨️ Enter link to ontology", key="key_ontology_link")
        st.session_state["ontology_link"] = ontology_link if ontology_link else ""

        if ontology_link:

            #http://purl.org/ontology/bibo/
            #http://xmlns.com/foaf/0.1/

            g_candidate, fmt_candidate = utils.parse_ontology(st.session_state["ontology_link"])
            st.session_state["g_ontology_from_link_candidate"] = g_candidate
            st.session_state["g_ontology_from_link_candidate_fmt"] = fmt_candidate
            st.session_state["g_ontology_from_link_candidate_label"] = utils.get_ontology_human_readable_name(st.session_state["g_ontology_from_link_candidate"], source_link=st.session_state["ontology_link"])

            if not utils.is_valid_ontology(g_candidate):
                with col1b:
                    st.write("")
                    st.markdown(f"""<div class="custom-error-small">
                        ❌ URL does not link to a valid ontology.
                    </div>""", unsafe_allow_html=True)
                    st.write("")

            else:

                with col1b:
                    st.write("")
                    st.markdown(f"""<div class="custom-success-small">
                            ✅ Valid ontology: <b style="color:#F63366;">
                            {st.session_state["g_ontology_from_link_candidate_label"]}</b>
                            (parsed successfully with format
                            <b>{st.session_state["g_ontology_from_link_candidate_fmt"]}</b>)
                        </div>""", unsafe_allow_html=True)
                with col1a:
                    st.button("Load", key="key_load_ontology_from_link_button", on_click=load_ontology_from_link)

        with col1:
            st.write("______")

    #LOAD ONTOLOGY FROM FILE___________________________________
    if not st.session_state["g_ontology"]:   #no ontology is loaded yet
        with col1:
            st.markdown("""<div class="purple-heading">
                    📁 Load Ontology from File
                </div>    """, unsafe_allow_html=True)
            st.write("")

        ontology_extension_dict = utils.get_g_ontology_file_formats_dict()   #ontology allowed formats
        ontology_format_list = list(ontology_extension_dict)

        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.session_state["ontology_file"] = st.file_uploader(f"""🖱️
                Upload ontology file""", type=ontology_format_list, key=st.session_state["key_ontology_uploader"])

        if st.session_state["ontology_file"]:

            g_candidate, fmt_candidate = utils.parse_ontology(st.session_state["ontology_file"])
            st.session_state["g_ontology_from_file_candidate"] = g_candidate
            st.session_state["g_ontology_from_file_candidate_fmt"] = fmt_candidate
            st.session_state["g_ontology_from_file_candidate_label"] = utils.get_ontology_human_readable_name(st.session_state["g_ontology_from_file_candidate"], source_file=st.session_state["ontology_file"])


            if not utils.is_valid_ontology(g_candidate):
                with col1b:
                    st.write("")
                    st.write("")
                    st.markdown(f"""<div class="custom-error-small">
                        ❌ File does not contain a valid ontology.
                    </div>""", unsafe_allow_html=True)
                    st.write("")

            else:
                with col1b:
                    st.write("")
                    st.write("")
                    st.markdown(f"""<div class="custom-success-small">
                            ✅ Valid ontology: <b style="color:#F63366;">
                            {st.session_state["g_ontology_from_file_candidate_label"]}</b>
                            (parsed successfully with format
                            <b>{st.session_state["g_ontology_from_file_candidate_fmt"]}</b>)
                        </div>""", unsafe_allow_html=True)

                with col1a:
                    st.button("Load", key="key_load_ontology_from_file_button", on_click=load_ontology_from_file)


    #EXTEND ONTOLOGY___________________________________
    if st.session_state["g_ontology"]:   #ontology loaded
        with col1:
            st.write("")
            st.write("")
            st.markdown("""<div class="purple-heading">
                    ➕ Extend Current Ontology
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a,col1b = st.columns([2,1])
        with col1b:
            extend_ontology_selected_option = st.radio("Load ontology from:", ["🌐 URL", "📁 File"], horizontal=True, key="key_extend_ontology_selected_option")

        if extend_ontology_selected_option == "🌐 URL":
            with col1a:
                ontology_link = st.text_input("⌨️ Enter link to ontology", key="key_ontology_link")
            st.session_state["ontology_link"] = ontology_link if ontology_link else ""

            if ontology_link:

                g_candidate, fmt_candidate = utils.parse_ontology(st.session_state["ontology_link"])
                st.session_state["g_ontology_from_link_candidate"] = g_candidate
                st.session_state["g_ontology_from_link_candidate_fmt"] = fmt_candidate
                st.session_state["g_ontology_from_link_candidate_label"] = utils.get_ontology_human_readable_name(st.session_state["g_ontology_from_link_candidate"], source_link=st.session_state["ontology_link"])

                if not utils.is_valid_ontology(g_candidate):
                    with col1b:
                        st.write("")
                        st.markdown(f"""<div class="custom-error-small">
                            ❌ URL does not link to a valid ontology.
                        </div>""", unsafe_allow_html=True)
                        st.write("")

                elif st.session_state["g_ontology_from_link_candidate_label"] in st.session_state["g_ontology_components_dict"]:
                    with col1b:
                        st.markdown(f"""<div class="custom-warning">
                                ⚠️ The ontology <b style="color:#F63366;">
                                {st.session_state["g_ontology_from_link_candidate_label"]}</b>
                                is already loaded.
                            </div>""", unsafe_allow_html=True)

                else:
                    with col1b:
                        st.write("")
                        st.markdown(f"""<div class="custom-success-small">
                                ✅ Valid ontology: <b style="color:#F63366;">
                                {st.session_state["g_ontology_from_link_candidate_label"]}</b>
                                (parsed successfully with format
                                <b>{st.session_state["g_ontology_from_link_candidate_fmt"]}</b>)
                            </div>""", unsafe_allow_html=True)

                    if utils.check_ontology_overlap(st.session_state["g_ontology_from_link_candidate"], st.session_state["g_ontology"]):
                        with col1a:
                            st.markdown(f"""<div class="custom-warning">
                                    ⚠️ Caution: <b>Ontologies overlap</b>. Check your ontologies
                                    externally to make sure they are aligned and compatible.
                                </div>""", unsafe_allow_html=True)
                            st.write("")
                    with col1a:
                        st.button("Add", key="key_extend_ontology_from_link_button", on_click=extend_ontology_from_link)



        if extend_ontology_selected_option == "📁 File":

            ontology_extension_dict = utils.get_g_ontology_file_formats_dict()   #ontology allowed formats
            ontology_format_list = list(ontology_extension_dict)

            with col1a:
                st.session_state["ontology_file"] = st.file_uploader(f"""🖱️
                    Upload ontology file""", type=ontology_format_list, key=st.session_state["key_ontology_uploader"])

            if st.session_state["ontology_file"]:

                g_candidate, fmt_candidate = utils.parse_ontology(st.session_state["ontology_file"])
                st.session_state["g_ontology_from_file_candidate"] = g_candidate
                st.session_state["g_ontology_from_file_candidate_fmt"] = fmt_candidate
                st.session_state["g_ontology_from_file_candidate_label"] = utils.get_ontology_human_readable_name(st.session_state["g_ontology_from_file_candidate"], source_file=st.session_state["ontology_file"])

                if not utils.is_valid_ontology(g_candidate):
                    with col1b:
                        st.write("")
                        st.write("")
                        st.markdown(f"""<div class="custom-error-small">
                            ❌ File does not contain a valid ontology.
                        </div>""", unsafe_allow_html=True)
                        st.write("")

                elif st.session_state["g_ontology_from_file_candidate_label"] in st.session_state["g_ontology_components_dict"]:
                    with col1b:
                        st.markdown(f"""<div class="custom-warning">
                                ⚠️ The ontology <b style="color:#F63366;">
                                {st.session_state["g_ontology_from_file_candidate_label"]}</b>
                                is already loaded.
                            </div>""", unsafe_allow_html=True)

                else:
                    with col1b:
                        st.write("")
                        st.markdown(f"""<div class="custom-success-small">
                                ✅ Valid ontology: <b style="color:#F63366;">
                                {st.session_state["g_ontology_from_file_candidate_label"]}</b>
                                (parsed successfully with format
                                <b>{st.session_state["g_ontology_from_file_candidate_fmt"]}</b>)
                            </div>""", unsafe_allow_html=True)

                    if utils.check_ontology_overlap(st.session_state["g_ontology_from_file_candidate"], st.session_state["g_ontology"]):
                        with col1a:
                            st.markdown(f"""<div class="custom-warning">
                                    ⚠️ Caution: <b>Ontologies overlap</b>. Check your ontologies
                                    externally to make sure they are aligned and compatible.
                                </div>""", unsafe_allow_html=True)
                            st.write("")
                    with col1a:
                        st.button("Add", key="key_extend_ontology_from_file_button", on_click=extend_ontology_from_file)

        with col1:
            st.write("________")

    #REDUCE ONTOLOGY___________________________________
    if st.session_state["g_ontology"] and len(st.session_state["g_ontology_components_dict"]) != 1:   #ontology loaded and more than 1 component
        with col1:
            st.markdown("""<div class="purple-heading">
                    ➖ Reduce Current Ontology
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            ontology_components_list = list(st.session_state["g_ontology_components_dict"].keys())
            ontologies_to_drop_list = st.multiselect("Select ontologies to be dropped:", ontology_components_list)

        if ontologies_to_drop_list:
            ontologies_to_drop_itemise = '\n'.join([f"""<li><b style="color:#F63366;">{ont}</b></li>""" for ont in ontologies_to_drop_list])
            with col1b:
                st.write("")
                st.markdown(f"""<div class="gray-preview-message">
                        👆 You selected: <ul> {ontologies_to_drop_itemise}
                    </ul></div>""", unsafe_allow_html=True)

        if ontologies_to_drop_list:
            with col1a:
                reduce_ontology_checkbox = st.checkbox(
                ":gray-badge[⚠️ I am completely sure I want to drop the selected ontologies]",
                key="key_reduce_ontology_checkbox")

            if reduce_ontology_checkbox:
                with col1a:
                    st.button("Drop", key="key_reduce_ontology_button", on_click=reduce_ontology)


        with col1:
            st.write("________")

    #DISCARD ONTOLOGY___________________________________
    if st.session_state["g_ontology"]:   #ontology loaded
        with col1:
            st.markdown("""<div class="purple-heading">
                    🗑️ Discard Current Ontology
                </div>""", unsafe_allow_html=True)

        with col1:
            col1a,col1b = st.columns([2,1])
        with col1a:
            st.write("")
            if len(st.session_state["g_ontology_components_dict"]) == 1:
                st.markdown(f"""<div class="gray-preview-message">
                        🔒 Current ontology:
                        <b style="color:#F63366;">{next(iter(st.session_state["g_ontology_components_dict"]))}</b>
                    </div>""",unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="gray-preview-message">
                        🔒 Current ontology is the <b style="color:#F63366;">merger of
                        {len(st.session_state["g_ontology_components_dict"])} sub-ontologies</b>.
                    </div>""",unsafe_allow_html=True)
        with col1a:
            st.write("")
            discard_ontology_checkbox = st.checkbox(
            ":gray-badge[⚠️ I am completely sure I want to discard the ontology]",
            key="key_discard_ontology_checkbox")
            if discard_ontology_checkbox:
                st.button("Discard", key="key_discard_ontology_button", on_click=discard_ontology)


#_____________________________________________




#________________________________________________
#ADD NAMESPACE
# Here we bind the namespaces
with tab3:
    st.write("")
    st.write("")

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


            default_ns_dict = utils.get_default_ns_dict()
            mapping_ns_dict = utils.get_mapping_ns_dict()
            all_mapping_ns_dict = mapping_ns_dict | default_ns_dict

        with col2:
            col2a, col2b = st.columns([0.5, 2])

        with col2b:
            st.write("")
            st.write("")
            last_added_ns_df = pd.DataFrame({
                "Prefix": st.session_state["last_added_ns_list"],
                "Namespace": [mapping_ns_dict.get(prefix, "") for prefix in st.session_state["last_added_ns_list"]]})
            last_last_added_ns_df = last_added_ns_df.head(10)

            if st.session_state["last_added_ns_list"]:
                st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                        🔎 last added namespaces
                    </div>""", unsafe_allow_html=True)
                st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        (complete list below)
                    </div>""", unsafe_allow_html=True)
                st.dataframe(last_last_added_ns_df, hide_index=True)
                st.write("")

            mapping_ns_df = pd.DataFrame(list(mapping_ns_dict.items()), columns=["Prefix", "Namespace"]).iloc[::-1]
            all_ns_df = pd.DataFrame(list(all_mapping_ns_dict.items()), columns=["Prefix", "Namespace"]).iloc[::-1]

            #Option to show bound namespaces
            with st.expander("🔎 Show all namespaces"):
                st.write("")
                st.dataframe(mapping_ns_df, hide_index=True)

            #Option to show all namespaces (including default)
            with st.expander("🔎 Show all namespaces (including default)"):
                st.write("")
                st.dataframe(all_ns_df, hide_index=True)


        with col1:
            st.markdown("""<div class="purple-heading">
                    🆕 Add a New Namespace
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["custom_ns_bound_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="custom-success">
                    ✅ The namespace <b style="color:#F63366;">{st.session_state["new_ns_prefix"]}</b> has been bound!
                </div>""", unsafe_allow_html=True)
            st.session_state["custom_ns_bound_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()

        if st.session_state["ns_bound_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="custom-success">
                    ✅ The namespace/s have been bound!
                </div>""", unsafe_allow_html=True)
            st.session_state["ns_bound_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()

        if st.session_state["g_ontology"]:
            add_ns_options = ["🧩 Ontology", "✏️ Custom", "📋 Predefined"]
        else:
            add_ns_options = ["✏️ Custom", "📋 Predefined"]

        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            add_ns_selected_option = st.radio("", add_ns_options, label_visibility="collapsed", key="key_add_ns_radio", horizontal=True)

        predefined_ns_dict = utils.get_predefined_ns_dict()
        default_ns_dict = utils.get_default_ns_dict()
        ontology_ns_dict = utils.get_ontology_ns_dict()
        mapping_ns_dict = utils.get_mapping_ns_dict()

        if add_ns_selected_option == "✏️ Custom":
            with col1:
                col1a, col1b = st.columns([1,2])

            with col1a:           # prefix and iri input
                prefix_input = st.text_input("Enter prefix: ", key = "key_prefix_input")
            with col1b:
                iri_input = st.text_input("Enter an IRI for the new namespace", key="key_iri_input")
            st.session_state["new_ns_prefix"] = prefix_input if prefix_input else ""
            st.session_state["new_ns_iri"] = iri_input if iri_input else ""

            with col1:
                col1a, col1b = st.columns([2,1])

            if prefix_input:
                valid_prefix_input = False
                if prefix_input in ontology_ns_dict:
                    with col1a:
                        st.markdown(f"""<div class="custom-error-small">
                            ❌ <b> Prefix {prefix_input} is contained in the ontology: </b> <br>
                            You can either choose a different prefix or bind {prefix_input} directly from the ontology namespaces option.
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                elif prefix_input in predefined_ns_dict:
                    with col1a:
                        st.markdown(f"""<div class="custom-error-small">
                            ❌ <b> Prefix {prefix_input} is tied to a predefined namespace: </b> <br>
                            You can either choose a different prefix or bind {prefix_input} directly from the predefined namespaces option.
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                elif prefix_input in default_ns_dict:
                    with col1a:
                        st.markdown(f"""<div class="custom-error-small">
                            ❌ <b> Prefix {prefix_input} is tied to a default namespace: </b> <br>
                            You must choose a different prefix.
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                elif prefix_input in mapping_ns_dict:
                    with col1a:
                        st.markdown(f"""<div class="custom-error-small">
                            ❌ <b> Prefix {prefix_input} is already in use: </b> <br>
                            You can either choose a different prefix or unbind {prefix_input} to reassing it.
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                else:
                    valid_prefix_input = True

            if iri_input:
                valid_iri_input = False
                if iri_input in ontology_ns_dict.values():
                    with col1a:
                        st.markdown(f"""<div class="custom-error-small">
                            ❌ <b> Namespace is contained in the ontology: </b> <br>
                            You can either choose a different IRI or bind {iri_input} directly from the ontology namespaces option.
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                elif iri_input in predefined_ns_dict.values():
                    with col1a:
                        st.markdown(f"""<div class="custom-error-small">
                            ❌ <b> IRI matches a predefined namespace: </b> <br>
                            You can either choose a different IRI or bind {iri_input} directly from the predefined namespaces option.
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                elif iri_input in default_ns_dict.values():
                    with col1a:
                        st.markdown(f"""<div class="custom-error-small">
                            ❌ <b> IRI matches a default namespace: </b> <br>
                            You must choose a different IRI.
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                elif URIRef(iri_input) in mapping_ns_dict.values():
                    with col1a:
                        st.markdown(f"""<div class="custom-error-small">
                            ❌ <b> Namespace is already in use: </b> <br>
                            You can either choose a different IRI or unbind {iri_input} to reassing it.
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                elif not utils.is_valid_iri(iri_input):
                    with col1a:
                        st.markdown(f"""<div class="custom-error-small">
                            ❌ <b> Invalid IRI: </b> <br>
                            Please make sure it statrs with a valid scheme (e.g., http, https), includes no illegal characters
                            and ends with a delimiter (/, # or :).
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                else:
                    valid_iri_input = True

            if iri_input and prefix_input:
                if valid_iri_input and valid_prefix_input:
                    with col1a:
                        st.button("Bind", key="key_bind_custom_ns_button", on_click=bind_custom_namespace)


        if add_ns_selected_option == "📋 Predefined":

            there_are_predefined_ns_unbound_flag = False
            for prefix in predefined_ns_dict:
                if not prefix in mapping_ns_dict:
                    there_are_predefined_ns_unbound_flag = True
                    continue

            if not there_are_predefined_ns_unbound_flag:
                with col1a:
                    st.write("")
                    st.markdown(f"""<div class="custom-error-small">
                        ❌ <b> All predefined namespaces are already bound </b>
                    </div>""", unsafe_allow_html=True)
                    st.write("")
            else:

                with col1a:
                    predefined_ns_list = [key for key in predefined_ns_dict if key not in mapping_ns_dict]
                    if len(predefined_ns_list) > 1:
                        predefined_ns_list.insert(0, "Bind all")
                    predefined_ns_to_bind_list = st.multiselect("Select predefined namespaces:", predefined_ns_list, key="key_predefined_ns_to_bind_multiselect")

                if predefined_ns_to_bind_list:
                    if "Bind all" not in predefined_ns_to_bind_list:   # "Bind all" not selected
                        with col1a:
                            st.button("Bind", key="key_bind_predefined_ns_button", on_click=bind_predefined_namespaces)
                    else:
                        with col1a:
                            overwrite_checkbox = st.checkbox(
                            ":gray-badge[⚠️ I want to bind all predefined namespaces]",
                            key="overwrite_checkbox")
                            if overwrite_checkbox:
                                st.button("Bind", key="key_bind_all_predefined_ns_button", on_click=bind_all_predefined_namespaces)


        if add_ns_selected_option == "🧩 Ontology":

            there_are_ontology_ns_unbound_flag = False
            for prefix in ontology_ns_dict:
                if not prefix in mapping_ns_dict:
                    there_are_ontology_ns_unbound_flag = True
                    continue

            if not there_are_ontology_ns_unbound_flag:
                with col1a:
                    st.write("")
                    st.markdown(f"""<div class="custom-error-small">
                        ❌ <b> All ontology namespaces are already bound </b>
                    </div>""", unsafe_allow_html=True)
                    st.write("")
            else:

                with col1a:
                    ontology_ns_list = [key for key in ontology_ns_dict if key not in mapping_ns_dict]
                    if len(ontology_ns_list) > 1:
                        ontology_ns_list.insert(0, "Bind all")
                    ontology_ns_to_bind_list = st.multiselect("Select ontology namespaces:", ontology_ns_list, key="key_ontology_ns_to_bind_multiselect")

                if ontology_ns_to_bind_list:
                    if "Bind all" not in ontology_ns_to_bind_list:   # "Bind all" not selected
                        with col1a:
                            st.button("Bind", key="key_bind_ontology_ns_button", on_click=bind_ontology_namespaces)
                    else:
                        with col1a:
                            overwrite_checkbox = st.checkbox(
                            ":gray-badge[⚠️ I want to bind all ontology namespaces]",
                            key="overwrite_checkbox")
                            if overwrite_checkbox:
                                st.button("Bind", key="key_bind_all_ontology_ns_button", on_click=bind_all_ontology_namespaces)


        mapping_ns_dict = utils.get_mapping_ns_dict()

        if st.session_state["ns_unbound_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="custom-success">
                    ✅ The namespace/s have been unbound!
                </div>""", unsafe_allow_html=True)
            st.session_state["ns_unbound_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()


        if mapping_ns_dict:   #only if there are namespaces to unbind

            with col1:
                st.write("______")
                st.markdown("""
                <div style="background-color:#e6e6fa; border:1px solid #511D66;
                            border-radius:5px; padding:10px; margin-bottom:8px;">
                    <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                        🗑️Unbind Existing Namespace
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("")

            mapping_ns_dict = utils.get_mapping_ns_dict()
            mapping_ns_list = list(mapping_ns_dict.keys())
            if len(mapping_ns_list) > 1:
                mapping_ns_list.insert(0, "Unbind all")

            with col1:
                col1a, col1b = st.columns([2,1])
                with col1a:
                    ns_to_unbind_list = st.multiselect("Select namespaces to unbind", mapping_ns_list, key="key_unbind_multiselect")

            if ns_to_unbind_list and "Unbind all" not in ns_to_unbind_list:
                with col1a:
                    #create single box for display
                    inner_html = ""
                    for prefix in ns_to_unbind_list:
                        inner_html += f"""<div style="margin-bottom:6px;">
                            <span style="font-size:1rem;">🔗 <strong>{prefix}</strong> → {mapping_ns_dict[prefix]}</span>
                        </div>"""
                    # wrap it all in a single dashed box
                    full_html = f"""<div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        {inner_html}
                    </div>"""
                    # render
                    st.markdown(full_html, unsafe_allow_html=True)

                with col1a:
                    st.write("")
                    st.button(f"Unbind", key="key_unbind_ns_button", on_click=unbind_namespaces)

            elif ns_to_unbind_list:
                with col1a:
                    overwrite_checkbox = st.checkbox(
                    ":gray-badge[⚠️ I want to unbind all namespaces]",
                    key="overwrite_checkbox")
                    if overwrite_checkbox:
                        st.button("Unbind", key="key_unbind_all_ns_button", on_click=unbind_all_namespaces)


#_____________________________________________




#________________________________________________
#SAVE PROGRESS OPTION
with tab4:
    st.write("")
    st.write("")

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

        pkl_cache_filename = "__" + st.session_state["g_label"] + "_cache__.pkl"
        existing_pkl_file_list = [f for f in os.listdir() if f.endswith("_cache__.pkl")]
        with col2b:
            st.write("")
            overwrite_checkbox = st.checkbox(
                "💾 Save progress",
                key="overwrite_checkbox")
            if overwrite_checkbox:
                st.markdown(f"""<div class="info-message-small">
                        ℹ️ Current state of mapping <b style="color:#F63366;">
                        {st.session_state["g_label"]}</b> will be temporarily saved.
                        To retrieve cached work go to the <b>Select Mapping</b> panel.
                    </span></div>""", unsafe_allow_html=True)
                st.write("")
                st.markdown(f"""<div class="custom-warning-small">
                        ⚠️ Any previously cached mapping will be deleted.
                    </div>""", unsafe_allow_html=True)
                st.write("")
                st.button("Save", key="key_save_progress_button", on_click=save_progress)

        if st.session_state["progress_saved_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="custom-success">
                    ✅ Current state of mapping <b>{st.session_state["g_label"]}</b> has been cached!
                </div>""", unsafe_allow_html=True)
            st.session_state["progress_saved_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()

        # with col1:
        #     st.markdown("""<div class="purple-heading">
        #             💾 Save progress
        #         </div>""", unsafe_allow_html=True)
        #     st.write("")
        #
        # with col1:
        #     col1a, col1b = st.columns([2,1])

        # if st.session_state["progress_saved_ok_flag"]:
        #     with col1a:
        #         st.write("")
        #         st.markdown(f"""<div class="custom-success">
        #             ✅ Current state of mapping <b>{st.session_state["g_label"]}</b> has been cached!
        #         </div>""", unsafe_allow_html=True)
        #     st.session_state["progress_saved_ok_flag"] = False
        #     time.sleep(st.session_state["success_display_time"])
        #     st.rerun()


        # with col1a:
        #     st.markdown(f"""<div class="info-message-small">
        #             ℹ️ Current state of mapping <b style="color:#F63366;">
        #             {st.session_state["g_label"]}</b> will be temporarily saved.
        #             To retrieve cached work go to the <b>Select Mapping</b> panel.
        #         </span></div>""", unsafe_allow_html=True)
        #     st.write("")
        # with col1b:
        #     st.markdown(f"""<div class="custom-warning-small">
        #             ⚠️ Any previously cached mapping will be deleted.
        #         </div>""", unsafe_allow_html=True)
        #     st.write("")
        #
        # pkl_cache_filename = "__" + st.session_state["g_label"] + "_cache__.pkl"
        # existing_pkl_file_list = [f for f in os.listdir() if f.endswith("_cache__.pkl")]
        # with col1a:
        #     overwrite_checkbox = st.checkbox(
        #         ":gray-badge[⚠️ I am completely sure I want to continue]",
        #         key="overwrite_checkbox")
        #     if overwrite_checkbox:
        #         st.button("Save", key="key_save_progress_button", on_click=save_progress)

            # pkl_cache_file = next((f for f in os.listdir() if f.endswith("_temp.pkl")), None)

        with col1:
            st.markdown("""<div class="purple-heading">
                    📤 Export mapping
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["mapping_downloaded_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="custom-success">
                    ✅ The mapping <b>{st.session_state["g_label"]}</b> has been exported!
                </div>""", unsafe_allow_html=True)
            st.session_state["key_export_filename_selectbox"] = ""
            st.session_state["mapping_downloaded_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()

        with col1:
            col1a, col1b, col1c = st.columns([1,2,1])

        export_extension_dict = utils.get_g_mapping_file_formats_dict()
        export_format_list = list(export_extension_dict)

        with col1a:
            export_format = st.selectbox("Select exporting format:", export_format_list, key="key_export_format_selectbox")
        export_extension = export_extension_dict[export_format]

        with col1b:
            export_filename = st.text_input("Enter filename (without extension)", key="key_export_filename_selectbox")

        if "." in export_filename:
            with col1c:
                st.markdown(f"""<div class="custom-warning-small">
                        ⚠️ The filename <b style="color:#cc9a06;">{export_filename}</b>
                        seems to include an extension.
                    </div>""", unsafe_allow_html=True)

    with col1:
        col1a, col1b = st.columns([2,1])

    export_filename_complete = export_filename + export_extension if export_filename else ""

    if export_filename_complete:
        with col1a:
            st.markdown(f"""<div class="info-message-small">
                    ℹ️ Current state of mapping <b>
                    {st.session_state["g_label"]}</b> will exported
                    to file <b style="color:#F63366;">{export_filename_complete}</b>.
                </span></div>""", unsafe_allow_html=True)

        if export_format == "pickle":
            buffer = io.BytesIO()
            pickle.dump(st.session_state["g_mapping"], buffer)
            buffer.seek(0)  # Rewind to the beginning
            with col1a:
                st.write("")
                st.session_state["mapping_downloaded_ok_flag"] = st.download_button(label="Export", data=buffer,
                    file_name=export_filename_complete, mime="application/octet-stream")
        else:    # all formats except for pickle
            serialised_data = st.session_state["g_mapping"].serialize(format=export_format)
            with col1a:
                st.write("")
                st.session_state["mapping_downloaded_ok_flag"] = st.download_button(label="Export", data=serialised_data,
                    file_name=export_filename_complete, mime="text/plain")

        if st.session_state["mapping_downloaded_ok_flag"]:
            st.rerun()


#_____________________________________________

#________________________________________________
#EXPORT OPTION
with tab5:

    col1, col2 = st.columns([2,1])
    with col1:
        st.write("")
        st.write("")
        st.markdown(f"""<div class="custom-error-small">
            ❌ Panel <b>not ready</b> yet.
        </div>""", unsafe_allow_html=True)

#_____________________________________________

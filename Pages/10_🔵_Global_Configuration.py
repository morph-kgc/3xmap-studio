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

#________________________________________________________________
# PRELIMINARY

# Aesthetics------------------------------------------

# Header
st.markdown("""
<div style="display:flex; align-items:center; background-color:#f0f0f0; padding:12px 18px;
            border-radius:8px; margin-bottom:16px;">
    <img src="https://www.pngmart.com/files/23/Gear-Icon-PNG-Isolated-Photo.png"
         style="width:32px; margin-right:12px;">
    <div>
        <h3 style="margin:0; font-size:1.75rem;">
            <span style="color:#511D66; font-weight:bold; margin-right:12px;">-----</span>
            Global Configuration
            <span style="color:#511D66; font-weight:bold; margin-left:12px;">-----</span>
        </h3>
        <p style="margin:0; font-size:0.95rem; color:#555;">
            System-wide settings: Load <b>mapping</b> and <b>ontology</b>, and <b>save work</b>.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)
# another option for the icon:
# https://www.clipartmax.com/png/middle/139-1393405_file-gear-icon-svg-wikimedia-commons-gear-icon.png

# Import style
utils.import_st_aesthetics()

# Namespaces-------------------------------------------------------------
namespaces = utils.get_predefined_ns_dict()
RML = namespaces["rml"]
RR = namespaces["rr"]
QL = namespaces["ql"]
MAP = namespaces["map"]
CLASS = namespaces["class"]
LS = namespaces["logicalSource"]

# Directories---------------------------------------------------------------
save_progress_folder = os.path.join(os.getcwd(), "saved_mappings")  #folder to save mappings (pkl)
export_folder = os.path.join(os.getcwd(), "exported_mappings")    #filder to export mappings (ttl and others)
utils.check_directories()

# Initialise session state variables----------------------------------------
#TAB1
if "g_mapping" not in st.session_state:
    st.session_state["g_mapping"] = Graph()
if "g_label" not in st.session_state:
    st.session_state["g_label"] = ""
if "g_label_temp_existing" not in st.session_state:
    st.session_state["g_label_temp_existing"] = ""
if "new_g_mapping_created_ok_flag" not in st.session_state:
    st.session_state["new_g_mapping_created_ok_flag"] = False
if "existing_g_mapping_loaded_ok_flag" not in st.session_state:
    st.session_state["existing_g_mapping_loaded_ok_flag"] = False
if "save_g_filename" not in st.session_state:
    st.session_state["save_g_filename"] = ""
if "selected_load_pkl" not in st.session_state:
    st.session_state["selected_load_pkl"] = "Choose a file"
if "g_mapping_source" not in st.session_state:
    st.session_state["g_mapping_source"] = []
if "original_g_size" not in st.session_state:
    st.session_state["original_g_size"] = 0
g_label_temp = ""
cancel_text = ""
save_text = ""
overwrite_text = ""

if "g_label_temp" not in st.session_state:
    st.session_state["g_label_temp"] = ""
if "overwrite_checkbox" not in st.session_state:
    st.session_state["overwrite_checkbox"] = False
if "new_ns" not in st.session_state:
    st.session_state["new_ns"] = ""
if "new_prefix" not in st.session_state:
    st.session_state["new_prefix"] = ""
if "save_progress_success" not in st.session_state:
    st.session_state["save_progress_success"] = False
if "export_success" not in st.session_state:
    st.session_state["export_success"] = False
if "export_file" not in st.session_state:
    st.session_state["export_file"] = False
if "save_progress_filename_key" not in st.session_state:
    st.session_state["save_progress_filename_key"] = ""
if "load_success" not in st.session_state:
    st.session_state["load_success"] = ""
if "g_ontology" not in st.session_state:
    st.session_state["g_ontology"] = Graph()
if "ontology_label" not in st.session_state:
    st.session_state["ontology_label"] = ""
if "ontology_link" not in st.session_state:
    st.session_state["ontology_link"] = ""
if "ontology_file" not in st.session_state:
    st.session_state["ontology_file"] = ""
if "ontology_file_path" not in st.session_state:
    st.session_state["ontology_file_path"] = ""
if "g_ontology_loaded_from_file" not in st.session_state:
    st.session_state["g_ontology_loaded_from_file"] = False
if "load_ontology_from_file_button_flag" not in st.session_state:
    st.session_state["load_ontology_from_file_button_flag"] = False
if "ontology_source" not in st.session_state:
    st.session_state["ontology_source"] = ""


# Initialise variables -> Move to TAB----------------------------------------
save_file_available = False
selected_pkl = ""     #file from where existing graph is loaded
overwrite_checkbox = False
load_file_ready = False


# Define on_click functions-------------------------------------------------
#TAB1
def create_new_g_mapping():
    st.session_state["g_label"] = st.session_state["g_label_temp_new"]   # consolidate g_label
    st.session_state["g_mapping"] = Graph()   # create a new empty mapping
    st.session_state["new_g_mapping_created_ok_flag"] = True   #flag for success mesagge
    st.session_state["g_mapping_source"] = ["scratch", ""]   #info on the source to be displayed
    # reset fields___________________________
    st.session_state["key_g_label_temp_new"] = ""

def cancel_create_new_g_mapping():
    # reset fields___________________________
    st.session_state["key_g_label_temp_new"] = ""

def create_new_g_mapping_and_save_current_one():
    save_current_mapping_file = save_progress_folder + "\\" + st.session_state["save_g_filename"] + ".pkl"
    with open(save_current_mapping_file, "wb") as f:    # save current mapping to pkl file
        pickle.dump(st.session_state["g_mapping"], f)
    st.session_state["g_label"] = st.session_state["g_label_temp_new"]
    st.session_state["g_mapping"] = Graph()
    st.session_state["new_g_mapping_created_ok_flag"] = True
    st.session_state["g_mapping_source"] = ["scratch", ""]
    # reset fields___________________________
    st.session_state["key_g_label_temp_new"] = ""

def load_existing_g_mapping():
    st.session_state["g_label"] = st.session_state["g_label_temp_existing"]   # consolidate g_label
    st.session_state["original_g_size"] = utils.get_number_of_tm(st.session_state["candidate_g_mapping"])
    st.session_state["g_mapping"] = st.session_state["candidate_g_mapping"]   # consolidate the loaded mapping
    st.session_state["g_mapping_source"] = ["file", st.session_state["selected_load_pkl"]]
    st.session_state["existing_g_mapping_loaded_ok_flag"] = True
    # reset fields___________________________
    st.session_state["key_g_label_temp_existing"] = ""
    st.session_state["key_load_file_selector"] = "Choose a file"

def cancel_load_existing_g_mapping():
    st.session_state["key_g_label_temp_existing"] = ""
    st.session_state["key_load_file_selector"] = "Choose a file"

def load_existing_g_mapping_and_save_current_one():
    save_current_mapping_file = save_progress_folder + "\\" + st.session_state["save_g_filename"] + ".pkl"
    with open(save_current_mapping_file, "wb") as f:
        pickle.dump(st.session_state["g_mapping"], f)
    st.session_state["original_g_size"] = utils.get_number_of_tm(st.session_state["candidate_g_mapping"])
    st.session_state["g_label"] = st.session_state["g_label_temp_existing"]   #we consolidate g_label
    st.session_state["g_mapping"] = st.session_state["candidate_g_mapping"]   #we consolidate the loaded mapping
    st.session_state["key_g_label_temp_existing"] = ""
    st.session_state["existing_g_mapping_loaded_ok_flag"] = True
    st.session_state["key_load_file_selector"] = "Choose a file"
    st.session_state["g_mapping_source"] = ["file", st.session_state["selected_load_pkl"]]





def bind_namespace():
    st.session_state["ns_dict"][st.session_state["new_prefix"]] = st.session_state["new_ns"]    #we update the dictionaries
    st.session_state["all_ns_dict"][st.session_state["new_prefix"]] = st.session_state["new_ns"]
    st.session_state["g_mapping"].bind(prefix_input, iri_input)  #here we bind the new namespace
    st.session_state["iri_input"] = ""   #we reset the variables
    st.session_state["prefix_input"] = ""

def bind_predefined_namespace():
    st.session_state["ns_dict"][st.session_state["new_prefix"]] = st.session_state["new_ns"]    #we update the dictionaries
    st.session_state["all_ns_dict"][st.session_state["new_prefix"]] = st.session_state["new_ns"]
    st.session_state["g_mapping"].bind(st.session_state["new_prefix"], st.session_state["new_ns"])  #here we bind the new namespace
    st.session_state["predefined_ns_selectbox"] = "Select a namespace"   #we reset the selectbox

def bind_all_predefined_namespaces():
    for prefix in predefined_ns_dict:
        st.session_state["ns_dict"][prefix] = predefined_ns_dict[prefix]    #we update the dictionaries
        st.session_state["all_ns_dict"][prefix] = predefined_ns_dict[prefix]
        st.session_state["g_mapping"].bind(prefix, predefined_ns_dict[prefix])  #here we bind the new namespace
    st.session_state["predefined_ns_selectbox"] = "Select a namespace"   #we reset the selectbox

def unbind_namespace():
    st.session_state["g_mapping"].namespace_manager.bind(unbind_ns, None, replace=True)
    st.session_state["unbind_selectbox"] = "Select a namespace"   #we reset the variables

def save_progress():

    with open(save_progress_file, "wb") as f:
        pickle.dump(st.session_state["g_mapping"], f)

    st.session_state["save_progress_filename_key"] = ""
    st.session_state["save_progress_success"] = True

def export_mapping_to_file():
    st.session_state["g_mapping"].serialize(destination=export_file_path, format=export_format)
    st.session_state["export_file_input"] = ""
    st.session_state["export_success"] = True

def load_mapping():
    st.session_state["g_label"] = st.session_state["g_label_temp"]
    with open(load_g_file_full_path, "rb") as f:
        st.session_state["g_mapping"] = pickle.load(f)   #we load the mapping
    st.session_state["load_success"] = True

def load_ontology_from_link_button():
    st.session_state["ontology_link_input"] = ""

def load_ontology_from_file_button():
    st.session_state["ontology_file_input"] = "Select an ontology file"
    st.session_state["load_ontology_from_file_button_flag"] = True
    st.session_state["ontology_source"] = "file"

def discard_ontology():
    st.session_state["g_ontology"] = Graph()
    st.session_state["ontology_label"] = ""


#____________________________________________________________
# PANELS OF THE PAGE (tabs)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Select mapping",
    "Load ontology", "Configure namespaces", "Save progress", "Export mapping"])

#____________________________________________________________
# PANEL: "SELECT MAPPING"
with tab1:
    st.write("")
    st.write("")

    # OPTION: Create new mapping------------------------------
    col1,col2,col3 = st.columns([2,0.5, 1])
    with col1:
        st.markdown("""<div class="purple_heading">
            📄 Create new mapping
        </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([2,1])
    with col1a:
        g_label_temp = st.text_input("⌨️ Enter mapping label:",
        key="key_g_label_temp_new")
    st.session_state["g_label_temp_new"] = g_label_temp    #just a candidate until confirmed

    # A mapping has not been loaded yet__________
    if not st.session_state["g_mapping"]:   #a mapping has not been loaded yet (or loaded mapping is empty)

        if st.session_state["g_label_temp_new"]:  #after a new label has been given
            with col1a:
                st.button("Confirm", on_click=create_new_g_mapping)

        if st.session_state["new_g_mapping_created_ok_flag"]:
            with col1b:
                st.write("")
                st.markdown(f"""
                    <div style="background-color:#d4edda; padding:1em;
                    border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                        ✅ The mapping <b style="color:#0f5132;">
                        {st.session_state["g_label"]}</b> has been created!
                    </div>""", unsafe_allow_html=True)
            st.session_state["new_g_mapping_created_ok_flag"] = False
            time.sleep(2)
            st.cache_data.clear()
            st.rerun()


    # A mapping is currently loaded__________
    else:  #a mapping is currently loaded (ask if overwrite)

        if g_label_temp:   #after a new label has been given
            st.session_state["g_label_temp_new"] = g_label_temp    #just candidate until confirmed

            with col1b:
                st.markdown(f"""
                    <div style="background-color:#fff3cd; padding:0.8em;
                    border-radius:5px; color:#856404; border:1px solid #ffeeba; font-size:0.92rem;">
                        ⚠️ The mapping <b style="color:#cc9a06;">{st.session_state["g_label"]}</b>
                        is already loaded! <br>
                    </div>""", unsafe_allow_html=True)
                st.write("")

            cancel_text = (f"""🛑 Cancel loading mapping {st.session_state["g_label_temp_new"]}""")
            save_text = f"""💾 Save mapping {st.session_state["g_label"]} first"""
            overwrite_text = f"""✏️ Overwrite mapping {st.session_state["g_label"]}"""

            overwrite_g_options = {"opt_overwrite": overwrite_text, "opt_save": save_text,
            "opt_cancel": cancel_text}

            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                overwrite_g_selection = st.radio("What would you like to do?:",
                    list(overwrite_g_options.keys()),
                    format_func=lambda x: overwrite_g_options[x],
                    key="overwrite_selection_radio_new")

            if overwrite_g_selection == "opt_overwrite":
                with col1b:
                    st.write("")
                    st.markdown(f"""
                        <div style="background-color:#F5F5F5; border:1px dashed #511D66;
                        padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                            If you continue:<br>
                        <div style="font-size:0.85rem; margin-top:6px; margin-left:15px; padding-left:10px;">
                            🗑️ Mapping <b>{st.session_state["g_label"]}</b> will be overwritten.<br>
                            🆕 Mapping <b>{st.session_state["g_label_temp_new"]}</b> will be created.
                        </div></span></div>""", unsafe_allow_html=True)
                with col1a:
                    overwrite_g_mapping_checkbox = st.checkbox(
                    f""":gray-badge[⚠️ I am completely sure I want to overwrite mapping {st.session_state["g_label"]}]""",
                    key="key_overwrite_g_mapping_checkbox_new")

                if overwrite_g_mapping_checkbox:
                    with col1a:
                        st.button(f"""Overwrite""", on_click=create_new_g_mapping, key="key_overwrite_new_button")

            elif overwrite_g_selection == "opt_cancel":
                with col1b:
                    st.write("")
                    st.markdown(f"""<div style="background-color:#F5F5F5; border:1px dashed #511D66;
                        padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                            If you continue:<br>
                        <div style="font-size:0.85rem; margin-top:6px; margin-left:15px; padding-left:10px;">
                            🛑 Mapping <b>{st.session_state["g_label_temp_new"]}</b> will not be created.<br>
                            🔄 You will keep working with mapping <b>{st.session_state["g_label"]}</b>.
                        </div></span></div>""", unsafe_allow_html=True)
                with col1a:
                    st.button(f"""Cancel""", on_click=cancel_create_new_g_mapping, key="key_cancel_new_button")

            elif overwrite_g_selection == "opt_save": #for the save case we need to ask for the filename before confirming
                with col1b:
                    st.write("")
                    st.markdown(f"""
                        <div style="background-color:#F5F5F5; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                            <span style="font-size:0.95rem;">
                            If you continue:<br>
                            <div style="font-size:0.85rem; margin-top:6px; margin-left:15px; padding-left:10px;">
                                💾️ Mapping <b>{st.session_state["g_label"]}</b> will be saved to pkl file.<br>
                                🆕 Mapping <b>{st.session_state["g_label_temp_new"]}</b> will be created</b>.
                            </div>
                            </span>
                        </div>""", unsafe_allow_html=True)
                with col1a:
                    save_g_filename = st.text_input(
                    f"⌨️ Enter pkl filename (without extension) for mapping {st.session_state["g_label"]} :")
                    existing_pkl_list = [f for f in os.listdir(save_progress_folder) if f.endswith(".pkl")]

                if (save_g_filename + ".pkl") in existing_pkl_list:
                    with col1a:
                        st.markdown(f"""<div style="background-color:#fff3cd; padding:0.8em;
                            border-radius:5px; color:#856404; border:1px solid #ffeeba; font-size:0.92rem;">
                                ⚠️ A file named <b style="color:#cc9a06;">{save_g_filename + ".pkl"}</b> already exists.
                                If you don't want to overwrite it, enter a different filename.
                            </div>""", unsafe_allow_html=True)
                        st.write("")

                        overwrite_pkl_file_checkbox = st.checkbox(
                            f""":gray-badge[I am completely sure I want to overwrite the file {save_g_filename + ".pkl"}]""",
                            key="key_overwrite_pkl_file_checkbox_new")

                        if overwrite_pkl_file_checkbox:
                            st.button(f"""Save""",
                             on_click=create_new_g_mapping_and_save_current_one,  key="key_save_new_button_1")
                else:
                    st.session_state["save_g_filename"] = save_g_filename
                    if save_g_filename:
                        with col1a:
                            st.button(f"""Save""",
                             on_click=create_new_g_mapping_and_save_current_one,  key="key_save_new_button_2")

    if st.session_state["new_g_mapping_created_ok_flag"]:
        with col1b:
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:1em; border-radius:5px;
            color:#155724; border:1px solid #c3e6cb;">
                ✅ The mapping <b style="color:#0f5132;">
                {st.session_state["g_label"]}</b> has been created!
            </div>""", unsafe_allow_html=True)
        st.session_state["new_g_mapping_created_ok_flag"] = False
        time.sleep(2)
        st.cache_data.clear()
        st.rerun()


    with col1:
        st.write("_____")


    # OPTION: Import existing mapping--------------------------------------
    with col1:
        st.markdown(""" <div class="purple_heading">
                📁 Load existing mapping
            </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([2,1])
    with col1a:
        g_label_temp = st.text_input("⌨️ Enter mapping label:", key="key_g_label_temp_existing")
        st.session_state["g_label_temp_existing"] = g_label_temp    #just candidate until confirmed

    pkl_list = [f for f in os.listdir(save_progress_folder) if f.endswith(".pkl")]
    pkl_list.insert(0, "Choose a file")
    with col1a:
        if st.session_state["g_label_temp_existing"]:
            selected_load_pkl_temp = st.selectbox(f"""🖱️ Select the file that stores mapping
            {st.session_state["g_label_temp_existing"]}
            """, pkl_list, key="key_load_file_selector")
        else:
            selected_load_pkl_temp = st.selectbox(f"""🖱️ Select the file that stores the mapping
            """, pkl_list, key="key_load_file_selector")
        selected_load_pkl = selected_load_pkl_temp if selected_load_pkl_temp != pkl_list[0] else ""
    st.session_state["selected_load_pkl"] = selected_load_pkl

    if st.session_state["selected_load_pkl"]:
        load_g_file_full_path = save_progress_folder + "\\" + st.session_state["selected_load_pkl"]
        load_file_ready = True
        with open(load_g_file_full_path, "rb") as f:
            st.session_state["candidate_g_mapping"] = pickle.load(f)   #we load the mapping as a candidate (until confirmed)


    # A mapping has not been loaded yet__________
    if not st.session_state["g_mapping"]:   # a mapping has not been loaded yet (or loaded mapping is empty)

        if st.session_state["g_label_temp_existing"] and load_file_ready:  # after a label and file have been given
            with col1:
                col1a, col1b = st.columns([1,2])
            with col1a:
                st.button("Confirm", on_click=load_existing_mapping)

        if st.session_state["existing_g_mapping_loaded_ok_flag"]:
            with col1b:
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em; border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ The mapping <b style="color:#0f5132;">{st.session_state["g_label"]}</b> has been loaded!
                </div>
                """, unsafe_allow_html=True)
            st.session_state["existing_g_mapping_loaded_ok_flag"] = False
            time.sleep(2)
            st.cache_data.clear()
            st.rerun()


    # A mapping is currently loaded__________
    else:  #a mapping is currently loaded (ask if overwrite)
        if g_label_temp and load_file_ready:   #after a label and file have been given
            st.session_state["g_label_temp_existing"] = g_label_temp    #just candidate until confirmed

            with col1b:
                st.markdown(f"""
                    <div style="background-color:#fff3cd; padding:0.8em;
                    border-radius:5px; color:#856404; border:1px solid #ffeeba; font-size:0.92rem;">
                        ⚠️ The mapping <b style="color:#cc9a06;">{st.session_state["g_label"]}</b>
                        is already loaded! <br>
                    </div>""", unsafe_allow_html=True)
                st.write("")

            cancel_text = (f"""🛑 Cancel loading mapping {st.session_state["g_label_temp_new"]}""")
            save_text = f"""💾 Save mapping {st.session_state["g_label"]} first"""
            overwrite_text = f"""✏️ Overwrite mapping {st.session_state["g_label"]}"""

            overwrite_g_options = {"opt_overwrite": overwrite_text, "opt_save": save_text,
            "opt_cancel": cancel_text}

            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                overwrite_g_selection = st.radio("What would you like to do?:",
                    list(overwrite_g_options.keys()),
                    format_func=lambda x: overwrite_g_options[x],
                    key="overwrite_selection_radio_existing")

            if overwrite_g_selection == "opt_overwrite":
                with col1b:
                    st.write("")
                    st.markdown(f"""
                        <div style="background-color:#F5F5F5; border:1px dashed #511D66;
                        padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                            If you continue:<br>
                        <div style="font-size:0.85rem; margin-top:6px; margin-left:15px; padding-left:10px;">
                            🗑️ Mapping <b>{st.session_state["g_label"]}</b> will be overwritten.<br>
                            🆕 Mapping <b>{st.session_state["g_label_temp_existing"]}</b> will be created.
                        </div></span></div>""", unsafe_allow_html=True)
                with col1a:
                    overwrite_g_mapping_checkbox = st.checkbox(
                    f""":gray-badge[⚠️ I am completely sure I want to overwrite mapping {st.session_state["g_label"]}]""",
                    key="key_overwrite_g_mapping_checkbox_existing")

                if overwrite_g_mapping_checkbox:
                    with col1a:
                        st.button(f"""Overwrite""", on_click=load_existing_g_mapping, key="key_overwrite_existing_button")

            elif overwrite_g_selection == "opt_cancel":
                with col1b:
                    st.write("")
                    st.markdown(f"""<div style="background-color:#F5F5F5; border:1px dashed #511D66;
                        padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                            If you continue:<br>
                        <div style="font-size:0.85rem; margin-top:6px; margin-left:15px; padding-left:10px;">
                            🛑 Mapping <b>{st.session_state["g_label_temp_existing"]}</b> will not be created.<br>
                            🔄 You will keep working with mapping <b>{st.session_state["g_label"]}</b>.
                        </div></span></div>""", unsafe_allow_html=True)
                with col1a:
                    st.button(f"""Cancel""", on_click=cancel_load_existing_g_mapping, key="key_cancel_existing_button")

            elif overwrite_g_selection == "opt_save": #for the save case we need to ask for the filename before confirming
                with col1b:
                    st.write("")
                    st.markdown(f"""
                        <div style="background-color:#F5F5F5; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                            <span style="font-size:0.95rem;">
                            If you continue:<br>
                            <div style="font-size:0.85rem; margin-top:6px; margin-left:15px; padding-left:10px;">
                                💾️ Mapping <b>{st.session_state["g_label"]}</b> will be saved to pkl file.<br>
                                🆕 Mapping <b>{st.session_state["g_label_temp_existing"]}</b> will be created</b>.
                            </div>
                            </span>
                        </div>""", unsafe_allow_html=True)
                with col1a:
                    save_g_filename = st.text_input(
                    f"⌨️ Enter pkl filename (without extension) for mapping {st.session_state["g_label"]} :")
                    existing_pkl_list = [f for f in os.listdir(save_progress_folder) if f.endswith(".pkl")]

                if (save_g_filename + ".pkl") in existing_pkl_list:
                    with col1a:
                        st.markdown(f"""<div style="background-color:#fff3cd; padding:0.8em;
                            border-radius:5px; color:#856404; border:1px solid #ffeeba; font-size:0.92rem;">
                                ⚠️ A file named <b style="color:#cc9a06;">{save_g_filename + ".pkl"}</b> already exists.
                                If you don't want to overwrite it, enter a different filename.
                            </div>""", unsafe_allow_html=True)
                        st.write("")

                        overwrite_pkl_file_checkbox = st.checkbox(
                            f""":gray-badge[I am completely sure I want to overwrite the file {save_g_filename + ".pkl"}]""",
                            key="key_overwrite_pkl_file_checkbox_existing")

                        if overwrite_pkl_file_checkbox:
                            st.button(f"""Save""",
                             on_click=load_existing_g_mapping_and_save_current_one,  key="key_save_existing_button_1")
                else:
                    st.session_state["save_g_filename"] = save_g_filename
                    if save_g_filename:
                        with col1a:
                            st.button(f"""Save""",
                             on_click=load_existing_g_mapping_and_save_current_one,  key="key_save_existing_button_2")

        if st.session_state["existing_g_mapping_loaded_ok_flag"]:
            with col1b:
                st.write("")
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em; border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ The mapping <b style="color:#0f5132;">{st.session_state["g_label"]}</b> has been loaded!
                </div>
                """, unsafe_allow_html=True)
            st.session_state["existing_g_mapping_loaded_ok_flag"] = False
            time.sleep(2)
            st.rerun()

    # g mapping INFORMATION BOX--------------------------------------------
    with col3:
        if st.session_state["g_label"]:
            if st.session_state["g_mapping_source"][0] == "file":
                st.markdown(f"""
                    <div style="background-color:#f5f5f5; padding:1em; border-radius:5px;
                    color:#2a0134; border:1px solid #511D66;">
                        <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                        style="vertical-align:middle; margin-right:8px; height:20px;">
                        You are currently working with mapping
                        <b style="color:#007bff;">{st.session_state["g_label"]}</b>.
                        <ul style="font-size:0.85rem; margin-top:6px; margin-left:15px; padding-left:10px;">
                            <li>Mapping was loaded from file <b>{st.session_state["g_mapping_source"][1]}</b></li>
                            <li>When loaded, mapping had <b>{st.session_state["original_g_size"]} TriplesMaps</b></li>
                            <li>Now mapping has <b>{utils.get_number_of_tm(st.session_state["g_mapping"])} TriplesMaps<b/></li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style="background-color:#f5f5f5; padding:1em; border-radius:5px;
                    color:#2a0134; border:1px solid #511D66;">
                        <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                        style="vertical-align:middle; margin-right:8px; height:20px;">
                        You are currently working with mapping
                        <b style="color:#F63366;">{st.session_state["g_label"]}</b>.
                        <ul style="font-size:0.85rem; margin-top:6px; margin-left:15px; padding-left:10px;">
                            <li>Mapping was created <b>from scratch</b></li>
                            <li>Mapping has <b>{utils.get_number_of_tm(st.session_state["g_mapping"])} TriplesMaps<b/></li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)


        else:
            st.markdown(f"""
            <div style="background-color:#e6e6fa; padding:1em; border-radius:5px; color:#2a0134; border:1px solid #511D66;">
                ✖️ <b style="color:#511D66;">No mapping</b> has been loaded yet.
            </div>
            """, unsafe_allow_html=True)

    utils.update_dictionaries()   #After mapping is created or loaded, load the DICTIONARIES


#_______________________________________________________

#________________________________________________
# PANEL: "LOAD ONTOLOGY"
with tab2:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])
    with col1:
        if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
            st.markdown(f"""
            <div style="background-color:#f8d7da; padding:1em;
                        border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                ❗ You need to create or load a mapping in the
                <b style="color:#a94442;">Select mapping option</b>."
            </div>
            """, unsafe_allow_html=True)
            st.stop()

    col1,col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
        with col2b:
            st.markdown(f"""
                <div style="background-color:#e6e6fa; padding:1em; border-radius:5px;
                color:#2a0134; border:1px solid #511D66;">
                    <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                    style="vertical-align:middle; margin-right:8px; height:20px;">
                    You are currently working with mapping
                    <b style="color:#007bff;">{st.session_state["g_label"]}</b>.
                </div>
            """, unsafe_allow_html=True)
            st.write("")

            if st.session_state["g_ontology"]:
                if st.session_state["ontology_source"] == "file":
                    st.markdown(f"""
                    <div style="background-color:#d4edda; padding:1em;
                                border-radius:5px; color:#155724; border:1px solid #444;">
                        🧩 The ontology <b style="color:#007bff;">{st.session_state["ontology_label"]}</b> has been loaded!
                        <ul style="font-size:0.85rem; margin-top:6px; margin-left:15px; padding-left:10px;">
                            <li><b>Source:</b> {st.session_state["ontology_file"]}</li>
                            <li><b>{len(st.session_state["g_ontology"])} triples<b/> retrieved 🧩</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                elif st.session_state["ontology_source"] == "link":
                    st.markdown(f"""
                    <div style="background-color:#d4edda; padding:1em;
                                border-radius:5px; color:#155724; border:1px solid #444;">
                        🧩 The ontology <b style="color:#007bff;">{st.session_state["ontology_label"]}</b> has been loaded!
                        <ul style="font-size:0.85rem; margin-top:6px; margin-left:15px; padding-left:10px;">
                            <li><b>Source:</b> {st.session_state["ontology_link_save"]}</li>
                            <li><b>{len(st.session_state["g_ontology"])} triples<b/> retrieved 🧩</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background-color:#f0f0f0; padding:10px; border-radius:5px; margin-bottom:8px; border:1px solid #ccc;">
                    <span style="font-size:0.95rem; color:#333;">
                        🚫 <b>No ontology</b> is loaded.<br>
                    </span>
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
        ℹ️ Certain options in this panel can be a bit slow, some patience may be required 🐢.
        </span>
        </div>
        """, unsafe_allow_html=True)



    #LOAD ONTOLOGY FROM URL___________________________________
    if not st.session_state["g_ontology"]:   #no ontology is loaded yet
        with col1:
            st.markdown("""
                <div style="background-color:#e6e6fa; border:1px solid #511D66;
                            border-radius:5px; padding:10px; margin-bottom:8px;">
                    <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                        🌐 Load ontology from URL
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with col1:
            col1a,col1b = st.columns([2,1])
        with col1a:
            ontology_link_input = st.text_input("Enter link to ontology", key="ontology_link_input")
        if ontology_link_input:
            st.session_state["ontology_link"] = ontology_link_input
            st.session_state["ontology_link_save"] = ontology_link_input

        #http://purl.org/ontology/bibo/

        if st.session_state["ontology_link"] and not utils.is_valid_ontology(st.session_state["ontology_link"]):
            with col1a:
                st.markdown(f"""
                <div style="background-color:#f8d7da; padding:1em;
                            border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                    ❌ URL does not link to a valid ontology.
                </div>
                """, unsafe_allow_html=True)
                st.write("")

        elif st.session_state["ontology_link"]:
            with col1:
                col1a, col1b = st.columns([1,2])
            with col1a:
                load_ontology_from_link_button = st.button("Load ontology", key="load_ontology_from_link_button", on_click=load_ontology_from_link_button)
            if load_ontology_from_link_button:
                st.session_state["g_ontology"] = Graph()
                st.session_state["g_ontology"].parse(st.session_state["ontology_link"], format="xml")  # RDF/XML format
                st.session_state["ontology_link"] = ""
                st.session_state["ontology_source"] = "link"

                #get the ontology human-readable name
                ontology_iri = next(st.session_state["g_ontology"].subjects(RDF.type, OWL.Ontology), None)
                st.session_state["ontology_label"] = (
                    st.session_state["g_ontology"].value(ontology_iri, RDFS.label) or
                    st.session_state["g_ontology"].value(ontology_iri, DC.title) or
                    st.session_state["g_ontology"].value(ontology_iri, DCTERMS.title) or
                    uri_split(ontology_iri)[1])    #look for ontology label; if there isnt one just select the ontology iri
                st.rerun()

    #LOAD ONTOLOGY FROM FILE___________________________________
    if not st.session_state["g_ontology"]:   #no ontology is loaded yet
        with col1:
            st.write("________")
            st.markdown("""
                <div style="background-color:#e6e6fa; border:1px solid #511D66;
                            border-radius:5px; padding:10px; margin-bottom:8px;">
                    <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                        📁 Load ontology from file
                    </div>
                </div>
                """, unsafe_allow_html=True)

        #ontology files
        ontology_extension_dict = {"owl": ".owl", "turtle": ".ttl", "longturtle": ".ttl", "n3": ".n3",
        "ntriples": ".nt", "nquads": "nq", "trig": ".trig", "json-ld": ".jsonld",
        "xml": ".xml", "pretty-xml": ".xml", "trix": ".trix"}
        ontology_format_list = list(ontology_extension_dict)
        ontology_folder = os.path.join(os.getcwd(), "ontologies")
        ontology_file_list = [
            filename for filename in os.listdir(ontology_folder)
            if os.path.isfile(os.path.join(ontology_folder, filename)) and
               any(filename.endswith(ext) for ext in ontology_format_list)
        ]
        ontology_file_list.insert(0, "Select an ontology file")

        with col1:
            col1a,col1b = st.columns([2,1])

        if len(ontology_file_list) == 1:
            with col1a:
                st.markdown(f"""
                    <div style="background-color:#fff3cd; padding:1em;
                    border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                        ⚠️ No valid ontology files in
                         <b style="color:#cc9a06;">ontologies</b> folder. Please add a valid file
                          to continue with this option.</div>
                """, unsafe_allow_html=True)

        else:
            with col1a:
                ontology_file_input = st.selectbox("Select an ontology file", ontology_file_list, key="ontology_file_input")
            if ontology_file_input and ontology_file_input != "Select an ontology file":
                st.session_state["ontology_file"] = ontology_file_input
                st.session_state["ontology_file_path"] = os.path.join(os.getcwd(), "ontologies", st.session_state["ontology_file"])

                try:
                    st.session_state["g_ontology_candidate"] = Graph()
                    st.session_state["g_ontology_candidate"].parse(st.session_state["ontology_file_path"], format="xml")  # RDF/XML format
                    st.session_state["g_ontology_loaded_from_file"] = True
                except:
                    with col1a:
                        st.markdown(f"""
                        <div style="background-color:#f8d7da; padding:1em;
                                    border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                            ❌ <b style="color:#a94442;">Unbound namespaces</b> in ontology file.<br>
                            Make sure the file includes all requires namespace definitions at the top.
                        </div>
                        """, unsafe_allow_html=True)
                        st.session_state["g_ontology_loaded_from_file"] = False


            if st.session_state["g_ontology_loaded_from_file"] == True and ontology_file_input != "Select an ontology file":
                with col1:
                    col1a, col1b = st.columns([1,2])
                with col1a:
                    st.write("")
                    st.button("Load ontology", key="load_ontology_from_file_button", on_click=load_ontology_from_file_button)

            if st.session_state["load_ontology_from_file_button_flag"]:
                #get the ontology human-readable name
                st.session_state["load_ontology_from_file_button_flag"] = False
                st.session_state["g_ontology"] = st.session_state["g_ontology_candidate"]
                ontology_iri = next(st.session_state["g_ontology"].subjects(RDF.type, OWL.Ontology), None)
                st.session_state["ontology_label"] = (
                    st.session_state["g_ontology"].value(ontology_iri, RDFS.label) or
                    st.session_state["g_ontology"].value(ontology_iri, DC.title) or
                    st.session_state["g_ontology"].value(ontology_iri, DCTERMS.title) or
                    split_uri(ontology_iri)[1])    #look for ontology label; if there isnt one just select the ontology iri
                st.rerun()




    #DISCARD ONTOLOGY___________________________________
    if st.session_state["g_ontology"]:   #ontology loaded -> only option to discard
        with col1:
            st.markdown("""
                <div style="background-color:#e6e6fa; border:1px solid #511D66;
                            border-radius:5px; padding:10px; margin-bottom:8px;">
                    <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                        🗑️ Discard current ontology
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with col1:
            col1a,col1b = st.columns([2,1])

        if not st.session_state["g_ontology"]:   #no ontology loaded
            with col1a:
                st.markdown(f"""
                    <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                    🚫 <b> Option not available:</b> No ontology is currently loaded.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

        else:  #an ontology is loaded and can be discarded
            with col1a:
                st.markdown(
                    f"""
                    <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                        🔒 Current ontology:
                        <b style="color:#007bff;">{st.session_state["ontology_label"]}</b><br>
                        <small>Discard to load a new one (only one ontology can be loaded at once).</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.write("")
                discard_ontology_checkbox = st.checkbox(
                ":gray-badge[⚠️ I am completely sure I want to discard the ontology]",
                key="discard_ontology")
            if discard_ontology_checkbox:
                with col1:
                    col1a, col1b = st.columns([1,2])
                with col1a:
                    st.button("Discard ontology", on_click=discard_ontology)


#_____________________________________________




#________________________________________________
#ADD NAMESPACE
#Here we build a dictionary that will store the Namespaces
#it will contain predefined namespaces, along with the ones the user defines
#HERE I want to also give an option to show current namespaces

with tab3:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])
    with col1:
        if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
            st.markdown(f"""
            <div style="background-color:#f8d7da; padding:1em;
                        border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                ❗ You need to create or load a mapping in the
                <b style="color:#a94442;">Select mapping option</b>."
            </div>
            """, unsafe_allow_html=True)
            st.stop()



    if "ns_dict" not in st.session_state:
        #st.session_state["ns_dict"] = utils.get_predefined_ns_dict()   #initial dictionary with predefined namespaces, custom ns will be added
        st.session_state["ns_dict"] = {}
    if "all_ns_dict" not in st.session_state:
        st.session_state["all_ns_dict"] = {}   #dictionary with all bound namespaces (includes the ones which are bound by default)

    col1,col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
        with col2b:
            if st.session_state["g_label"]:
                st.markdown(f"""
                    <div style="background-color:#e6e6fa; padding:1em; border-radius:5px;
                    color:#2a0134; border:1px solid #511D66;">
                        <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                        style="vertical-align:middle; margin-right:8px; height:20px;">
                        You are currently working with mapping
                        <b style="color:#007bff;">{st.session_state["g_label"]}</b>.
                    </div>
                """, unsafe_allow_html=True)


            else:
                st.markdown(f"""
                <div style="background-color:#e6e6fa; padding:1em; border-radius:5px;
                color:#2a0134; border:1px solid #511D66;">
                    ✖️ <b style="color:#511D66;">No mapping</b> has been loaded yet.
                </div>
                """, unsafe_allow_html=True)



        col2a, col2b = st.columns([0.5, 2])

        with col2b:
            st.write("")
            st.write("")
            utils.update_dictionaries()
            ns_df = pd.DataFrame(list(st.session_state["ns_dict"].items()), columns=["Prefix", "Namespace"]).iloc[::-1]
            ns_df_last = ns_df.head(7)
            st.markdown("""
                <div style='text-align: right; font-size: 14px; color: grey;'>
                    last added namespaces
                </div>
            """, unsafe_allow_html=True)
            st.markdown("""
                <div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                    (complete list in 🔎 Show Namespaces)
                </div>
            """, unsafe_allow_html=True)
            st.dataframe(ns_df_last, hide_index=True)
            st.write("")


    with col1:
        st.markdown("""
        <div style="background-color:#e6e6fa; border:1px solid #511D66;
                    border-radius:5px; padding:10px; margin-bottom:8px;">
            <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                🆕 Add a New Namespace
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")
        st.markdown(
            """
                <div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
                </div>
            """,
            unsafe_allow_html=True
        )

        col1a, col1b = st.columns([2,1])


    with col1a:           #PREFIX AND IRI INPUT
        st.markdown(
            """
                <span style="font-size:1.1em; font-weight:bold;">✏️ Enter custom namespace:</span><br>
            """,
            unsafe_allow_html=True
        )
        prefix_input = st.text_input("Enter prefix: ", key = "prefix_input")
        iri_input = st.text_input("Enter an IRI for the new namespace", key="iri_input")
    if prefix_input:
        st.session_state["new_prefix"] = prefix_input
    if iri_input:
        st.session_state["new_ns"] = iri_input

    predefined_ns_dict = utils.get_predefined_ns_dict()

    with col1a:
        if prefix_input:
            valid_prefix_input = False
            if prefix_input in predefined_ns_dict:
                st.markdown(f"""
                <div style="background-color:#f8d7da; padding:1em;
                            border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                    ❌ <b> Prefix {prefix_input} is tied to a predefined namespace: </b> <br>
                    You can either choose a different prefix or bind {prefix_input} directly from the predefined namespaces list.
                </div>
                """, unsafe_allow_html=True)
                st.write("")
            elif prefix_input in st.session_state["ns_dict"] and st.session_state["ns_dict"][prefix_input] != None:
                st.markdown(f"""
                <div style="background-color:#f8d7da; padding:1em;
                            border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                    ❌ <b> Prefix {prefix_input} is already in use: </b> <br>
                    You can either choose a different prefix or unbind {prefix_input} to reassing it.
                </div>
                """, unsafe_allow_html=True)
                st.write("")
            else:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em; border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ Valid prefix
                </div>
                """, unsafe_allow_html=True)
                st.write("")
                valid_prefix_input = True

        if iri_input:
            valid_iri_input = False
            if iri_input in predefined_ns_dict.values():
                st.markdown(f"""
                <div style="background-color:#f8d7da; padding:1em;
                            border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                    ❌ <b> That IRI matches a predefined namespace: </b> <br>
                    You can either choose a different IRI or bind {iri_input} directly from the predefined namespaces list.
                </div>
                """, unsafe_allow_html=True)
                st.write("")
            elif not utils.is_valid_iri(iri_input):
                st.markdown(f"""
                <div style="background-color:#f8d7da; padding:1em;
                            border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                    ❌ <b> Invalid IRI: </b> <br>
                    Please make sure it statrs with a valid scheme (e.g., http, https), includes no illegal characters
                    and ends with a delimiter (/, # or :).
                </div>
                """, unsafe_allow_html=True)
                st.write("")
            elif URIRef(iri_input) in st.session_state["ns_dict"].values():
                st.markdown(f"""
                <div style="background-color:#f8d7da; padding:1em;
                            border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                    ❌ <b> That IRI is already in use: </b> <br>
                    You can either choose a different IRI or unbind {iri_input} to reassing it.
                </div>
                """, unsafe_allow_html=True)
                st.write("")
            else:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em; border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ Valid IRI
                </div>
                """, unsafe_allow_html=True)
                st.write("")
                valid_iri_input = True


    if iri_input and prefix_input:
        if valid_iri_input and valid_prefix_input:
            with col1a:
                save_new_ns = st.button("Bind namespace", on_click=bind_namespace)


    #option to bind predefined namespaces
    predefined_ns_dict = utils.get_predefined_ns_dict()
    predefined_ns_list = list(predefined_ns_dict.keys())
    predefined_ns_list.insert(0, "Select a namespace")
    predefined_ns_list.insert(1, "Bind all predefined namespaces")
    predefined_ns_prefix = "Select a namespace"

    if not iri_input and not prefix_input:
        with col1a:
            st.markdown(
                """
                <div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
                    <span style="font-size:1.1em; font-weight:bold;">📑 Select predefined namespace:</span><br>
                </div>
                """,
                unsafe_allow_html=True
            )
            predefined_ns_prefix = st.selectbox("or select a predefined namespace from list", predefined_ns_list, key="predefined_ns_selectbox")

    if predefined_ns_prefix != "Select a namespace" and predefined_ns_prefix != "Bind all predefined namespaces":
        st.session_state["new_prefix"] = predefined_ns_prefix
        st.session_state["new_ns"] = predefined_ns_dict[predefined_ns_prefix]
        with col1a:
            save_new_ns = st.button(f"Bind predefined namespace {st.session_state["new_prefix"]}", on_click=bind_predefined_namespace)


    if predefined_ns_prefix == "Bind all predefined namespaces":
        with col1a:
            save_new_ns = st.button("Bind all predefined namespaces", on_click=bind_all_predefined_namespaces)

    with col1:
        st.write("---")
        st.markdown("""
        <div style="background-color:#e6e6fa; border:1px solid #511D66;
                    border-radius:5px; padding:10px; margin-bottom:8px;">
            <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                🗑️Unbind Existing Namespace
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")

    unbind_ns_list = list(st.session_state["ns_dict"].keys())
    unbind_ns_list.insert(0, "Select a namespace")

    with col1:
        col1a, col1b = st.columns([2,1])
        with col1a:
            unbind_ns = st.selectbox("Select a namespace", unbind_ns_list, key="unbind_selectbox")

    if unbind_ns != "Select a namespace":
        with col1a:
            st.markdown(f"""
            <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                <span style="font-size:1rem;">🔗 <strong>{unbind_ns}</strong> → {st.session_state["ns_dict"][unbind_ns]}</span>
            </div>
            """, unsafe_allow_html=True)
        with col1a:
            st.write("")
            st.write("")
            st.button(f"Unbind namespace {unbind_ns}", on_click=unbind_namespace)


    with col1:
        st.write("---")
        st.markdown("""
        <div style="background-color:#e6e6fa; border:1px solid #511D66;
                    border-radius:5px; padding:10px; margin-bottom:8px;">
            <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                🔎 Show Namespaces
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")

    #Option to show all custom namespaces
    with col1:
        with st.expander("ℹ️ Show all custom namespaces"):
            st.write("")
            st.dataframe(ns_df, hide_index=True)

    #Option to show all namespaces (including built-in ones)
    st.session_state["all_ns_dict"] = dict(st.session_state["g_mapping"].namespace_manager.namespaces())
    all_ns_df = pd.DataFrame(list(st.session_state["all_ns_dict"].items()), columns=["Prefix", "Namespace"]).iloc[::-1]
    with col1:
        with st.expander("ℹ️ Show all bound namespaces (including built-in ones)"):
            st.write("")
            st.dataframe(all_ns_df, hide_index=True)

#_____________________________________________




#________________________________________________
#SAVE PROGRESS OPTION
with tab4:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])
    with col1:
        if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
            st.markdown(f"""
            <div style="background-color:#f8d7da; padding:1em;
                        border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                ❗ You need to create or load a mapping in the
                <b style="color:#a94442;">Select mapping option</b>."
            </div>
            """, unsafe_allow_html=True)
            st.stop()


    col1,col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
        with col2b:
            if st.session_state["g_label"]:
                st.markdown(f"""
                    <div style="background-color:#e6e6fa; padding:1em; border-radius:5px;
                    color:#2a0134; border:1px solid #511D66;">
                        <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                        style="vertical-align:middle; margin-right:8px; height:20px;">
                        You are currently working with mapping
                        <b style="color:#007bff;">{st.session_state["g_label"]}</b>.
                    </div>
                """, unsafe_allow_html=True)


            else:
                st.markdown(f"""
                <div style="background-color:#e6e6fa; padding:1em; border-radius:5px;
                color:#2a0134; border:1px solid #511D66;">
                    ✖️ <b style="color:#511D66;">No mapping</b> has been loaded yet.
                </div>
                """, unsafe_allow_html=True)

    with col1:
        st.markdown("""
        <div style="background-color:#e6e6fa; border:1px solid #511D66;
                    border-radius:5px; padding:10px; margin-bottom:8px;">
            <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                💾 Save progress
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")


        existing_save_progress_file_list = [f for f in os.listdir(save_progress_folder) if f.endswith(".pkl")]


    with col1:
        col1a, col1b = st.columns([2,1])

    with col1b:
        st.markdown(f"""
        <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
            <span style="font-size:0.95rem;">
                Current state of mapping <b style="color:#007bff;">
                {st.session_state["g_label"]}</b> will be saved in folder
                📁saved_mappings as a <code>.pkl</code> file.
            </span>
        </div>
        """, unsafe_allow_html=True)

    with col1a:
        save_progress_filename = st.text_input(
        f"""Enter the filename to save the mapping {st.session_state["g_label"]}
        (without extension):""", key="save_progress_filename_key")
        if "." in save_progress_filename:
            st.markdown(f"""
                <div style="background-color:#fff3cd; padding:1em;
                border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                    ⚠️ The filename <b style="color:#cc9a06;">{save_progress_filename}</b>
                    seems to include an extension. <br> Please note that the extension <code>.pkl</code>
                    will be added.</div>
            """, unsafe_allow_html=True)
            st.write("")
        if save_progress_filename and (save_progress_filename + ".pkl") in existing_save_progress_file_list:
            st.markdown(f"""
                <div style="background-color:#fff3cd; padding:1em;
                border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                    ⚠️ The file <b style="color:#cc9a06;">{save_progress_filename}.pkl</b>
                    is already in use. <br> Do you want to
                    overwrite it?</div>
            """, unsafe_allow_html=True)
            st.write("")
            overwrite_checkbox = st.checkbox(
            ":gray-badge[⚠️ I am completely sure I want to overwrite it]",
            key="overwrite_checkbox")
        else:
            overwrite_checkbox = True

        save_progress_file = save_progress_folder + "\\" + save_progress_filename + ".pkl"

        if overwrite_checkbox:
            if save_progress_filename:
                st.session_state["save_progress_filename"] = save_progress_filename + ".pkl"
                confirm_button = st.button("Save progress", key="10_save_progress", on_click=save_progress)

    if st.session_state["save_progress_success"]:
        with col1a:
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:1em;
            border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                ✅ The mapping <b style="color:#0f5132;">{st.session_state["g_label"]}
                </b> has been saved to file
                <b style="color:#0f5132;">{st.session_state["save_progress_filename"]}
                </b>.  </div>
            """, unsafe_allow_html=True)
            st.session_state["save_progress_success"] = False
            time.sleep(2)
            st.rerun()

        #     st.success(f"""The mapping {st.session_state["g_label_temp"]}
        #      has been saved to file {st.session_state["save_g_filename"]}.""")

#_____________________________________________

#________________________________________________
#EXPORT OPTION
with tab5:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])
    with col1:
        if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
            st.markdown(f"""
            <div style="background-color:#f8d7da; padding:1em;
                        border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                ❗ You need to create or load a mapping in the
                <b style="color:#a94442;">Select mapping option</b>."
            </div>
            """, unsafe_allow_html=True)
            st.stop()

    col1,col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
        with col2b:
            if st.session_state["g_label"]:
                st.markdown(f"""
                    <div style="background-color:#e6e6fa; padding:1em; border-radius:5px;
                    color:#2a0134; border:1px solid #511D66;">
                        <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                        style="vertical-align:middle; margin-right:8px; height:20px;">
                        You are currently working with mapping
                        <b style="color:#007bff;">{st.session_state["g_label"]}</b>.
                    </div>
                """, unsafe_allow_html=True)


            else:
                st.markdown(f"""
                <div style="background-color:#e6e6fa; padding:1em; border-radius:5px;
                color:#2a0134; border:1px solid #511D66;">
                    ✖️ <b style="color:#511D66;">No mapping</b> has been loaded yet.
                </div>
                """, unsafe_allow_html=True)

    with col1:
        st.markdown("""
        <div style="background-color:#e6e6fa; border:1px solid #511D66;
                    border-radius:5px; padding:10px; margin-bottom:8px;">
            <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                📤 Export mapping
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([2,1])

    with col1b:
        st.markdown(f"""
        <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
            <span style="font-size:0.95rem;">
                Mapping <b style="color:#007bff;"> {st.session_state["g_label"]}</b> will be exported
                as an RDF-formatted file (e.g., <code>.ttl</code>) in folder
                📁exported_mappings.
            </span>
        </div>
        """, unsafe_allow_html=True)

    export_extension_dict = {"turtle": ".ttl", "longturtle": ".ttl", "n3": ".n3",
    "ntriples": ".nt", "nquads": "nq", "trig": ".trig", "json-ld": ".jsonld",
    "xml": ".xml", "pretty-xml": ".xml", "trix": ".trix", "hext": ".hext",
    "patch": ".patch"}

    export_format_list = list(export_extension_dict)

    valid_extensions = tuple(export_extension_dict.values())

    with col1a:
        export_format = st.selectbox("Select format for export file", export_format_list, key="export_format")
    export_extension = export_extension_dict[export_format]

    with col1a:
        export_file_input = st.text_input("Enter export filename (without extension)", key="export_file_input")
        if "." in export_file_input:
            st.markdown(f"""
                <div style="background-color:#fff3cd; padding:1em;
                border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                    ⚠️ The filename <b style="color:#cc9a06;">{export_file_input}</b>
                    seems to include an extension. <br> Please note that the extension
                    <code>{export_extension_dict[export_format]}</code>
                    will be added.</div>
            """, unsafe_allow_html=True)
            st.write("")
    export_file = export_file_input + export_extension


    if export_file_input:
        st.session_state["export_file"] = export_file
    export_file_path = "exported_mappings/" + export_file

    existing_export_file_list = [
        f for f in os.listdir(export_folder)
        if f.endswith(valid_extensions)
        ]

    with col1a:
        if export_file_input and export_file in existing_export_file_list:
            st.markdown(f"""
                <div style="background-color:#fff3cd; padding:1em;
                border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                    ⚠️ The file <b style="color:#cc9a06;">{export_file}</b>
                    is already in use. <br> Do you want to
                    overwrite it?</div>
            """, unsafe_allow_html=True)
            st.write("")
            overwrite_checkbox = st.checkbox(
            ":gray-badge[⚠️ I am completely sure I want to overwrite it]",
            key="overwrite_checkbox")
        else:
            overwrite_checkbox = True

    if export_file_input and overwrite_checkbox:
        with col1a:
            st.button("Export mapping to file", on_click=export_mapping_to_file)

    if st.session_state["export_success"]:
        with col1a:
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:1em;
            border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                ✅ The mapping <b style="color:#0f5132;">{st.session_state["g_label"]}
                </b> has been saved to file
                <b style="color:#0f5132;">{st.session_state["export_file"]}
                </b>.  </div>
            """, unsafe_allow_html=True)
            st.session_state["export_success"] = False
            time.sleep(2)
            st.rerun()


#_____________________________________________

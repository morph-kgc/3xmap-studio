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
from streamlit_js_eval import streamlit_js_eval

# Config-----------------------------------
if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
    st.set_page_config(page_title="3Xmap Studio", layout="wide",
        page_icon="logo/fav_icon.png")
else:
    st.set_page_config(page_title="3Xmap Studio", layout="wide",
        page_icon="logo/fav_icon_inverse.png")

# Automatic detection of dark mode-------------------------
if "dark_mode_flag" not in st.session_state or st.session_state["dark_mode_flag"] is None:
    st.session_state["dark_mode_flag"] = streamlit_js_eval(js_expressions="window.matchMedia('(prefers-color-scheme: dark)').matches",
        key="dark_mode")

# Header-----------------------------------
dark_mode = False if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"] else True
header_html = utils.render_header(title="Global Configuration",
    description="System-wide configuration: load <b>mapping</b>, manage <b>namespaces</b>, and <b>save work</b>.",
    dark_mode=dark_mode)
st.markdown(header_html, unsafe_allow_html=True)

# Import style-----------------------------
style_container = st.empty()
if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
    style_container.markdown(utils.import_st_aesthetics(), unsafe_allow_html=True)
else:
    style_container.markdown(utils.import_st_aesthetics_dark_mode(), unsafe_allow_html=True)



# Initialise session state variables----------------------------------------
# TAB1
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
if "session_retrieved_ok_flag" not in st.session_state:
    st.session_state["session_retrieved_ok_flag"] = False
if "g_mapping_source_cache" not in st.session_state:
    st.session_state["g_mapping_source_cache"] = ["",""]
if "original_g_size_cache" not in st.session_state:
    st.session_state["original_g_size_cache"] = 0
if "cached_mapping_retrieved_ok_flag" not in st.session_state:
    st.session_state["cached_mapping_retrieved_ok_flag"] = False
if "g_label_changed_ok_flag" not in st.session_state:
    st.session_state["g_label_changed_ok_flag"] = False

# TAB2
if "ns_dict" not in st.session_state:
    st.session_state["ns_dict"] = {}
if "ns_bound_ok_flag" not in st.session_state:
    st.session_state["ns_bound_ok_flag"] = False
if "structural_ns_changed_ok_flag" not in st.session_state:
    st.session_state["structural_ns_changed_ok_flag"] = False
if "ns_unbound_ok_flag" not in st.session_state:
    st.session_state["ns_unbound_ok_flag"] = False
if "last_added_ns_list" not in st.session_state:
    st.session_state["last_added_ns_list"] = []

# TAB3
if "progress_saved_ok_flag" not in st.session_state:
    st.session_state["progress_saved_ok_flag"] = False
if "mapping_downloaded_ok_flag" not in st.session_state:
    st.session_state["mapping_downloaded_ok_flag"] = False
if "session_saved_ok_flag" not in st.session_state:
    st.session_state["session_saved_ok_flag"] = False

# OTHER PAGES
if "db_connections_dict" not in st.session_state:
    st.session_state["db_connections_dict"] = {}
if "db_connection_status_dict" not in st.session_state:
    st.session_state["db_connection_status_dict"] = {}
if "sql_queries_dict" not in st.session_state:
    st.session_state["sql_queries_dict"] = {}
if "ds_files_dict" not in st.session_state:
    st.session_state["ds_files_dict"] = {}
if "g_ontology_components_dict" not in st.session_state:
    st.session_state["g_ontology_components_dict"] = {}
if "g_ontology" not in st.session_state:
    st.session_state["g_ontology"] = Graph()


# Namespaces-----------------------------------
RML, RR, QL = utils.get_required_ns().values()

if "structural_ns" not in st.session_state and st.session_state["g_label"]:
    st.session_state["structural_ns"] = utils.get_default_structural_ns()
    prefix, ns = utils.get_default_structural_ns()   # bind the default ns for the structural components
    st.session_state["g_mapping"].bind(prefix, ns)

# Define on_click functions-------------------------------------------------
#TAB1
def create_new_g_mapping():
    # create mapping
    st.session_state["g_label"] = st.session_state["g_label_temp_new"]   # consolidate g_label
    st.session_state["g_mapping"] = Graph()   # create a new empty mapping
    # bind default namespaces
    for prefix, namespace in utils.get_default_ns_dict().items():
        utils.bind_namespace(prefix, namespace)
    # bind ontology namespaces
    ontology_ns_dict = utils.get_ontology_ns_dict()
    for prefix, namespace in ontology_ns_dict.items():
        utils.bind_namespace(prefix, namespace)
    # store information_____________
    st.session_state["g_mapping_source_cache"] = ["scratch", ""]   #cache info on the mapping source
    st.session_state["new_g_mapping_created_ok_flag"] = True   #flag for success mesagge
    utils.empty_last_added_lists()
    # reset fields__________________
    st.session_state["key_g_label_temp_new"] = ""

def load_existing_g_mapping():
    # load mapping
    st.session_state["g_label"] = st.session_state["g_label_temp_existing"]   # consolidate g_label
    st.session_state["original_g_size_cache"] = utils.get_number_of_tm(st.session_state["candidate_g_mapping"])
    st.session_state["g_mapping"] = st.session_state["candidate_g_mapping"]   # consolidate the loaded mapping
    # bind default namespaces
    for prefix, namespace in utils.get_default_ns_dict().items():
        utils.bind_namespace(prefix, namespace)
    # bind ontology namespaces
    ontology_ns_dict = utils.get_ontology_ns_dict()
    for prefix, namespace in ontology_ns_dict.items():
        utils.bind_namespace(prefix, namespace)
    # store information________________________
    st.session_state["g_mapping_source_cache"] = ["file", selected_load_file.name]
    st.session_state["existing_g_mapping_loaded_ok_flag"] = True
    utils.empty_last_added_lists()
    # reset fields___________________________
    st.session_state["key_mapping_uploader"] = str(uuid.uuid4())
    st.session_state["key_g_label_temp_existing"] = ""

def retrieve_session():
    # get information from pkl file
    full_path = os.path.join(folder_name, selected_pkl_file_w_extension)
    # retrieve session___________________________
    with open(full_path, "rb") as f:     # load mapping
        project_state_list = pickle.load(f)
    utils.retrieve_project_state(project_state_list)
    # build the complete ontology from its components
    st.session_state["g_ontology"] = Graph()
    for g_ontology in st.session_state["g_ontology_components_dict"].values():
        st.session_state["g_ontology"] += g_ontology
    #store information___________________________
    utils.empty_last_added_lists()
    st.session_state["selected_pkl_file_wo_extension"] = selected_pkl_file_wo_extension
    # reset fields___________________________
    st.session_state["session_retrieved_ok_flag"] = True
    st.session_state["key_selected_pkl_file_wo_extension"] = "Select a session"

def retrieve_cached_mapping():
    # get information from pkl file_______________________
    st.session_state["g_label"] = cached_mapping_name    # g label
    with open(pkl_cache_file_path, "rb") as f:     # load mapping
        project_state_list = pickle.load(f)
    utils.retrieve_project_state(project_state_list)
    # build the complete ontology from its components___________
    st.session_state["g_ontology"] = Graph()
    for g_ontology in st.session_state["g_ontology_components_dict"].values():
        st.session_state["g_ontology"] += g_ontology
    #store information___________________________
    utils.empty_last_added_lists()
    st.session_state["cached_mapping_retrieved_ok_flag"] = True
    # reset fields___________________________
    st.session_state["key_retrieve_cached_mapping_checkbox"] = False

def change_g_label():
    # change g label_____________________________________
    st.session_state["g_label"] = g_label_candidate
    #store information___________________________
    st.session_state["g_label_changed_ok_flag"] = True
    # reset fields___________________________
    st.session_state["key_change_mapping_label_checkbox"] = False

# TAB2
def bind_custom_namespace():
    # bind and store information___________________________
    utils.bind_namespace(prefix_input, iri_input)
    st.session_state["ns_bound_ok_flag"] = True   #for success message
    # reset fields_____________________________
    st.session_state["key_iri_input"] = ""
    st.session_state["key_prefix_input"] = ""
    st.session_state["key_add_ns_radio"] = "✏️ Custom"

def bind_predefined_namespaces():
    if "Select all" in st.session_state["predefined_ns_to_bind_list"]:
        st.session_state["predefined_ns_to_bind_list"] = predefined_ns_list_not_duplicated
    # bind and store information___________________________
    for prefix in st.session_state["predefined_ns_to_bind_list"]:
        namespace = predefined_ns_dict[prefix]
        utils.bind_namespace(prefix, namespace)
    st.session_state["ns_bound_ok_flag"] = True    #for success message
    # reset fields_____________________________
    st.session_state["key_predefined_ns_to_bind_multiselect"] = []
    st.session_state["key_add_ns_radio"] = "📋 Predefined"

# def bind_all_predefined_namespaces():
#     # bind and store information___________________________
#     for requested_prefix in predefined_ns_dict:
#         namespace = predefined_ns_dict[requested_prefix]
#         utils.bind_namespace(prefix, namespace)
#     st.session_state["ns_bound_ok_flag"] = True   #for success message
#     # reset fields_____________________________
#     st.session_state["key_add_ns_radio"] = "📋 Predefined"

def bind_ontology_namespaces():
    # bind and store information___________________________
    for prefix in ontology_ns_to_bind_list:
        namespace = ontology_ns_dict[prefix]
        utils.bind_namespace(prefix, namespace)
    st.session_state["ns_bound_ok_flag"] = True   # for success message
    # reset fields_____________________________
    st.session_state["key_ontology_ns_to_bind_multiselect"] = []
    st.session_state["key_add_ns_radio"] = "🧩 Ontology"
    st.session_state["key_ontology_filter_for_ns"] = "Select ontology"

def change_structural_ns():
    # unbind original namespace________________________
    if unbind_previous_base_ns_checkbox:
        prefix = st.session_state["structural_ns"][0]
        utils.unbind_namespaces([prefix])
    # bind new namespace and store________________________
    st.session_state["structural_ns"] = [structural_ns_prefix_candidate, Namespace(structural_ns_iri_candidate)]
    utils.bind_namespace(structural_ns_prefix_candidate, structural_ns_iri_candidate)
    #store information________________________
    st.session_state["structural_ns_changed_ok_flag"] = True
    # reset fields_____________________________
    st.session_state["key_structural_ns_prefix_candidate"] = ""
    st.session_state["key_structural_ns_iri_candidate"] = ""
    st.session_state["key_add_ns_radio"] = "🏛️ Base"

def unbind_namespaces():
    # unbind the namespaces and store information_________________
    utils.unbind_namespaces(ns_to_unbind_list)
    st.session_state["ns_unbound_ok_flag"] = True
    # reset fields_____________________________
    st.session_state["key_unbind_multiselect"] = []

def unbind_all_namespaces():
    # unbind and store information___________________________
    utils.unbind_namespaces(mapping_ns_dict_wo_structural_ns)
    st.session_state["ns_unbound_ok_flag"] = True
    # reset fields_____________________________
    st.session_state["key_unbind_multiselect"] = []


#TAB3
def save_progress():
    # name of temporary file_____________
    pkl_cache_filename = "__" + st.session_state["g_label"] + "_cache__.pkl"
    # remove all cache pkl files in cwd_____________
    existing_pkl_file_list = [f for f in os.listdir() if f.endswith("_cache__.pkl")]
    for file in existing_pkl_file_list:
        filepath = os.path.join(os.getcwd(), file)
        if os.path.isfile(file):
            os.remove(file)
    #save progress___________________________
    project_state_list = utils.save_project_state()
    with open(pkl_cache_filename, "wb") as f:
        pickle.dump(project_state_list, f)
    #store information___________________________
    st.session_state["progress_saved_ok_flag"] = True
    #reset fields__________________________________
    st.session_state["key_save_progress_checkbox"] = False

def save_session():
    # create folder if needed
    os.makedirs(folder_name, exist_ok=True)
    full_path = os.path.join(folder_name, pkl_filename_w_extension)
    # save session___________________________
    project_state_list = utils.save_project_state()
    with open(full_path, "wb") as f:
        pickle.dump(project_state_list, f)
    # store information___________________________
    st.session_state["session_saved_ok_flag"] = True
    st.session_state["pkl_filename"] = pkl_filename + '.pkl'
    # reset fields_____________________
    st.session_state["key_pkl_filename"] = ""

# TAB 5
def activate_dark_mode():
    st.session_state["dark_mode_flag"] = True

def deactivate_dark_mode():
    st.session_state["dark_mode_flag"] = False

#____________________________________________________________
# PANELS OF THE PAGE (tabs)

tab1, tab2, tab3, tab4 = st.tabs(["Select Mapping",
    "Configure Namespaces", "Save Mapping", "Set Style"])

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
            st.markdown(f"""<div class="success-message-flag">
                ✅ The mapping <b style="color:#F63366;">{st.session_state["g_label"]}</b> has been created!
            </div>""", unsafe_allow_html=True)
        st.session_state["new_g_mapping_created_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    with col1a:
        st.session_state["g_label_temp_new"] = st.text_input("⌨️ Enter mapping label:*", # just a candidate until confirmed
        key="key_g_label_temp_new")

    # A mapping has not been loaded yet__________
    if not st.session_state["g_label"]:   #a mapping has not been loaded yet

        if st.session_state["g_label_temp_new"]:  #after a new label has been given
            with col1a:
                st.button("Create", on_click=create_new_g_mapping, key="key_create_new_g_mapping_button_1")


    # A mapping is currently loaded__________
    else:  #a mapping is currently loaded (ask if overwrite)
        with col1:
            col1a, col1b = st.columns([2,1])
        if st.session_state["g_label_temp_new"]:   #after a label and file have been given
            with col1:
                st.markdown(f"""<div class="warning-message">
                        ⚠️ If you continue:<br>
                        <small><div style="margin-left:1.5em;">
                        🗑️ Mapping <b>{st.session_state["g_label"]}</b> will be overwritten.<br>
                        🆕 Mapping <b>{st.session_state["g_label_temp_new"]}</b> will be created.<br>
                        </div>
                        You can export the current mapping or save the session in
                        the <b>Save Mapping </b> pannel.</small>
                    </div>""", unsafe_allow_html=True)

            with col1a:
                overwrite_g_mapping_checkbox = st.checkbox(
                    f"""🔒 I am sure I want to overwrite mapping {st.session_state["g_label"]}""",
                    key="key_overwrite_g_mapping_checkbox_new")

                if overwrite_g_mapping_checkbox:
                    with col1a:
                        st.button(f"""Overwrite and create""", on_click=create_new_g_mapping, key="key_create_new_g_mapping_button_2")

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
            st.markdown(f"""<div class="success-message-flag">
                ✅ The mapping <b style="color:#F63366;">{st.session_state["g_label"]}</b> has been loaded!
            </div>""", unsafe_allow_html=True)
        st.session_state["existing_g_mapping_loaded_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    with col1a:
        selected_load_file = st.file_uploader(f"""🖱️
        Upload mapping file:*""", type=mapping_format_list, key=st.session_state["key_mapping_uploader"])

    with col1b:
        if selected_load_file:
            st.session_state["g_label_temp_existing"] = st.text_input("⌨️ Enter mapping label:*",   #just candidate until confirmed
                key="key_g_label_temp_existing", value=os.path.splitext(selected_load_file.name)[0])

    if selected_load_file:
        st.session_state["candidate_g_mapping"] = utils.load_mapping_from_file(
            selected_load_file)   #we load the mapping as a candidate (until confirmed)


    # A mapping has not been loaded yet__________
    if not st.session_state["g_label"]:   # a mapping has not been loaded yet
        with col1:
            col1a, col1b = st.columns([2,1])

        if st.session_state["g_label_temp_existing"] and selected_load_file:  # after a label and file have been given
            with col1:
                col1a, col1b = st.columns([1,2])
            with col1a:
                st.button("Load", on_click=load_existing_g_mapping, key="key_load_existing_g_mapping_button_2")


    # A mapping is currently loaded__________
    else:  #a mapping is currently loaded (ask if overwrite or save)
        with col1:
            col1a, col1b = st.columns([2,1])
        if st.session_state["g_label_temp_existing"] and selected_load_file:   #after a label and file have been given
            with col1:
                st.markdown(f"""<div class="warning-message">
                        ⚠️ If you continue:<br>
                        <small><div style="margin-left:1.5em;">
                        🗑️ Mapping <b>{st.session_state["g_label"]}</b> will be overwritten.<br>
                        🆕 Mapping <b>{st.session_state["g_label_temp_existing"]}</b> will be created.<br>
                        </div>
                        <small>You can export the current mapping or save the session in
                        the <b>Save Mapping </b> pannel.
                    </div>""", unsafe_allow_html=True)

            with col1a:
                overwrite_g_mapping_checkbox = st.checkbox(
                    f"""🔒 I am sure I want to overwrite mapping {st.session_state["g_label"]}""",
                    key="key_overwrite_g_mapping_checkbox_existing")

                if overwrite_g_mapping_checkbox:
                    st.button(f"""Overwrite and create""", on_click=load_existing_g_mapping, key="key_load_existing_g_mapping_button_2")

    # OPTION: Retrieve session--------------------------------------
    folder_name = "saved_sessions"
    if os.path.isdir(folder_name):   # create if it does not exist
        folder_path = os.path.join(os.getcwd(), folder_name)
        pkl_files_list = [f for f in os.listdir(folder_path) if f.endswith(".pkl")]
    else:
        pkl_files_list = []

    if pkl_files_list:
        with col1:
            st.write("___________________________")
            st.markdown("""<div class="purple-heading">
                    🗃️ Retrieve Saved Session
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["session_retrieved_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The session <b>{st.session_state["selected_pkl_file_wo_extension"]}</b> has been retrieved!
                </div>""", unsafe_allow_html=True)
            st.session_state["session_retrieved_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()

        with col1:
            col1a, col1b =st.columns([2,1])
        with col1a:
            pkl_files_dict = {f.removesuffix(".pkl"): f for f in pkl_files_list}
            list_to_choose = list(pkl_files_dict.keys())
            list_to_choose.insert(0, "Select a session")
            selected_pkl_file_wo_extension = st.selectbox("🖱️ Select a session:*", list_to_choose,
                key="key_selected_pkl_file_wo_extension")
            selected_pkl_file_w_extension = pkl_files_dict[selected_pkl_file_wo_extension] if selected_pkl_file_wo_extension != "Select a session" else ""

        if selected_pkl_file_w_extension:

            if st.session_state["g_label"]:
                with col1a:
                    overwrite_g_mapping_checkbox_retrieve = st.checkbox(
                        f"""🔒 I am sure I want to overwrite mapping {st.session_state["g_label"]}""",
                        key="key_overwrite_g_mapping_checkbox_retrieve")

                if overwrite_g_mapping_checkbox_retrieve:
                    with col1a:
                        st.button("Retrieve", key="key_retrieve_session_button_1", on_click=retrieve_session)

                with col1:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ If you continue:<br>
                            <small><div style="margin-left:1.5em;">
                            🗑️ Mapping <b>{st.session_state["g_label"]}</b> will be overwritten.<br>
                            🆕 Session <b>{selected_pkl_file_wo_extension}</b> will be retrieved.<br>
                            </div>
                            <small>You can export the current mapping or save the session in
                            the <b>Save Mapping </b> pannel.
                        </div>""", unsafe_allow_html=True)

            else:
                st.button("Retrieve", key="key_retrieve_session_button_2", on_click=retrieve_session)

    if st.session_state["cached_mapping_retrieved_ok_flag"]:
        with col3:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ Mapping <b style="color:#F63366;">{st.session_state["g_label"]}</b> has been retrieved from cache!
            </div>""", unsafe_allow_html=True)
        st.session_state["cached_mapping_retrieved_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    if st.session_state["g_label_changed_ok_flag"]:
        with col3:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ Mapping was renamed to <b style="color:#F63366;">{st.session_state["g_label"]}</b>!
            </div>""", unsafe_allow_html=True)
        st.session_state["g_label_changed_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    # g mapping INFORMATION BOX--------------------------------------------
    with col3:
        if st.session_state["g_label"]:
            if st.session_state["g_mapping_source_cache"][0] == "file":
                st.markdown(f"""<div class="blue-status-message">
                        <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                        style="vertical-align:middle; margin-right:8px; height:20px;">
                        You are working with mapping
                        <b>{st.session_state["g_label"]}</b>.
                        <ul style="font-size:0.85rem; margin:6px 0 0 15px; padding-left:10px;">
                            <li>Mapping was loaded from file <b>{st.session_state["g_mapping_source_cache"][1]}</b></li>
                            <li>When loaded, mapping had <b>{st.session_state["original_g_size_cache"]} TriplesMaps</b></li>
                            <li>Now mapping has <b>{utils.get_number_of_tm(st.session_state["g_mapping"])} TriplesMaps<b/></li>
                        </ul></div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="blue-status-message">
                        <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                        style="vertical-align:middle; margin-right:8px; height:20px;">
                        You are working with mapping
                        <b>{st.session_state["g_label"]}</b>.
                        <ul style="font-size:0.85rem; margin:6px 0 0 15px; padding-left:10px;">
                            <li>Mapping was created <b>from scratch</b></li>
                            <li>Mapping has <b>{utils.get_number_of_tm(st.session_state["g_mapping"])} TriplesMaps<b/></li>
                        </ul></div>""", unsafe_allow_html=True)


        else:
            st.markdown("""<div class="gray-status-message">
                ✖️ <b>No mapping</b> has been loaded yet.
            </div>
            """, unsafe_allow_html=True)

    # option to retrieve mapping from cache-----------------------------------
    if not st.session_state["g_label"]:
        pkl_cache_filename = next((f for f in os.listdir() if f.endswith("_cache__.pkl")), None)  # fallback if no match is found

        if pkl_cache_filename:
            pkl_cache_file_path = os.path.join(os.getcwd(), pkl_cache_filename)
            cached_mapping_name = pkl_cache_filename.split("_cache__.pkl")[0]
            cached_mapping_name = cached_mapping_name.split("__")[1]
            with col3:
                st.write("")
                retrieve_cached_mapping_checkbox = st.checkbox(
                    "🗃️ Retrieve cached mapping",
                    key="key_retrieve_cached_mapping_checkbox")
                if retrieve_cached_mapping_checkbox:
                    st.markdown(f"""<div class="info-message-blue">
                            ℹ️ Mapping <b style="color:#F63366;">
                            {cached_mapping_name}</b> will be loaded, together
                            with any loaded ontologies and data sources.
                        </span></div>""", unsafe_allow_html=True)
                    st.write("")
                    st.button("Load", key="key_retrieve_cached_mapping_button", on_click=retrieve_cached_mapping)

    # option to change the mapping label-----------------------------------
    if st.session_state["g_label"]:

        with col3:
            st.write("")
            change_g_label_checkbox = st.checkbox(
                "🏷️ Rename mapping",
                key="key_change_mapping_label_checkbox")
            if change_g_label_checkbox:
                g_label_candidate = st.text_input("⌨️ Enter new mapping label:*")

                if g_label_candidate:
                    st.button("Change", key="key_change_g_label_button", on_click=change_g_label)
                    st.markdown(f"""<div class="info-message-gray">
                            ℹ️ Mapping label will be changed to <b style="color:#F63366;">
                            {g_label_candidate}</b> (currently <b>{st.session_state["g_label"]}</b>).
                        </span></div>""", unsafe_allow_html=True)


#_______________________________________________________

#________________________________________________
#ADD NAMESPACE
# Here we bind the namespaces
with tab2:
    st.write("")
    st.write("")

    if not st.session_state["g_label"]:
        col1, col2 = st.columns([2,1.5])
        with col1:
            utils.get_missing_g_mapping_error_message()

    else:   #only allow to continue if mapping is loaded

        col1,col2 = st.columns([2,1.5])

        # Display last added namespaces in dataframe (also option to show all ns)
        mapping_ns_dict = utils.get_mapping_ns_dict()
        used_mapping_ns_dict = utils.get_used_mapping_ns_dict()

        with col2:
            col2a, col2b = st.columns([0.5, 2])

        with col2b:
            st.write("")
            st.write("")
            last_added_ns_df = pd.DataFrame({
                "Prefix": st.session_state["last_added_ns_list"],
                "Namespace": [mapping_ns_dict.get(prefix, "") for prefix in st.session_state["last_added_ns_list"]]})
            last_last_added_ns_df = last_added_ns_df.head(utils.get_max_length_for_display()[1])

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
            used_mapping_ns_df = pd.DataFrame(list(used_mapping_ns_dict.items()), columns=["Prefix", "Namespace"]).iloc[::-1]

            #Option to show bound namespaces
            with st.expander("🔎 Show all namespaces"):
                st.write("")
                st.dataframe(mapping_ns_df, hide_index=True)

            #Option to show used bound namespaces
            with st.expander("🔎 Show used namespaces"):
                st.write("")
                st.dataframe(used_mapping_ns_df, hide_index=True)



        # PURPLE HEADING - ADD A NEW NAMESPACE
        with col1:
            st.markdown("""<div class="purple-heading">
                    🆕 Add New Namespace
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["ns_bound_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>Namespace/s</b> have been bound!
                </div>""", unsafe_allow_html=True)
            st.write("")
            st.write("")
            st.session_state["ns_bound_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()


        if st.session_state["structural_ns_changed_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>base namespace</b> has been changed!
                </div>""", unsafe_allow_html=True)
            st.session_state["structural_ns_changed_ok_flag"]  = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()


        if st.session_state["g_ontology_components_dict"]:
            ontology_ns_dict = utils.get_ontology_ns_dict()
            mapping_ns_dict = utils.get_mapping_ns_dict()
            ontology_ns_list = [key for key in ontology_ns_dict if key not in mapping_ns_dict]
            add_ns_options = ["✏️ Custom", "🧩 Ontology", "📋 Predefined", "🏛️ Base"]
        else:
            add_ns_options = ["✏️ Custom", "📋 Predefined", "🏛️ Base"]

        with col1:
            add_ns_selected_option = st.radio("🖱️ Select an option:*", add_ns_options, key="key_add_ns_radio",
                label_visibility="collapsed", horizontal=True)

        predefined_ns_dict = utils.get_predefined_ns_dict()
        default_ns_dict = utils.get_default_ns_dict()
        default_structural_ns = utils.get_default_structural_ns()
        ontology_ns_dict = utils.get_ontology_ns_dict()
        mapping_ns_dict = utils.get_mapping_ns_dict()

        if add_ns_selected_option == "✏️ Custom":
            with col1:
                col1a, col1b = st.columns([1,2])

            with col1a:           # prefix and iri input
                prefix_input = st.text_input("⌨️ Enter prefix*: ", key = "key_prefix_input")
            with col1b:
                iri_input = st.text_input("⌨️ Enter an IRI for the new namespace:*", key="key_iri_input")
            st.session_state["new_ns_prefix"] = prefix_input if prefix_input else ""
            st.session_state["new_ns_iri"] = iri_input if iri_input else ""

            with col1a:
                if prefix_input:
                    valid_prefix_input = False
                    if prefix_input in mapping_ns_dict:
                        bound_prefix = "Namespace not bound"
                        for pr, ns in mapping_ns_dict.items():
                            if ns == iri_input:
                                bound_prefix = pr
                                break
                        if bound_prefix != prefix_input:
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ <b>Prefix is already in use.</b>
                                <small>The chosen prefix will be auto-renamed with a numeric suffix.</small>
                            </div>""", unsafe_allow_html=True)
                            valid_prefix_input = True
                    else:
                        valid_prefix_input = True

            with col1b:
                if iri_input:
                    valid_iri_input = False
                    if not utils.is_valid_iri(iri_input):
                        st.markdown(f"""<div class="error-message">
                            ❌ <b> Invalid IRI. </b>
                            <small>Please make sure it starts with a valid scheme (e.g., http, https), includes no illegal characters
                            and ends with a delimiter (/, # or :).</small>
                        </div>""", unsafe_allow_html=True)
                    elif iri_input in mapping_ns_dict.values():
                        for pr, ns in mapping_ns_dict.items():
                            if ns == iri_input:
                                bound_prefix = pr
                                break
                        if prefix_input == bound_prefix:
                            st.markdown(f"""<div class="error-message">
                                ❌ <b> Namespace is already bound to prefix {bound_prefix}.</b>
                            </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ <b> Namespace is already bound to prefix {bound_prefix}. </b>
                                <small>If you continue, that prefix will be overwritten <b>({bound_prefix} → {prefix_input})</b>.</small>
                            </div>""", unsafe_allow_html=True)
                            valid_iri_input = True
                    else:
                        valid_iri_input = True


            if iri_input and prefix_input:
                if valid_iri_input and valid_prefix_input:
                    with col1a:
                        st.button("Bind", key="key_bind_custom_ns_button", on_click=bind_custom_namespace)

        elif add_ns_selected_option == "🧩 Ontology":

            there_are_ontology_ns_unbound_flag = False
            ontology_ns_dict = utils.get_ontology_ns_dict()
            for pr, ns in ontology_ns_dict.items():
                if not ns in mapping_ns_dict.values():
                    there_are_ontology_ns_unbound_flag = True
                    continue

            if not there_are_ontology_ns_unbound_flag:
                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    st.markdown(f"""<div class="info-message-gray">
                        🔒 All <b>ontology namespaces</b> are already bound.
                    </div>""", unsafe_allow_html=True)
                    st.write("")
            else:
                default_ns = list(utils.get_default_ns_dict())

                g_ont_components_w_unbound_ns = []
                for ont_label, ont in st.session_state["g_ontology_components_dict"].items():
                    for pr, ns in utils.get_ontology_component_ns_dict(ont).items():
                        if not str(ns) in mapping_ns_dict.values():
                            g_ont_components_w_unbound_ns.append(utils.get_ontology_tag(ont_label))
                            break

                if len(st.session_state["g_ontology_components_dict"]) == 1:   # no ontolgoy filter
                    with col1:
                        col1a, col1b = st.columns([2,1])

                    ontology_filter_for_ns = "Select ontology"

                    with col1a:
                        ontology_ns_list_not_duplicated = [k for k, v in ontology_ns_dict.items() if v not in mapping_ns_dict.values()]
                        list_to_choose = ontology_ns_list_not_duplicated.copy()
                        if len(list_to_choose) > 1:
                            list_to_choose.insert(0, "Select all")
                        ontology_ns_to_bind_list = st.multiselect("🖱️ Select ontology namespaces:*", list_to_choose,
                            key="key_ontology_ns_to_bind_multiselect")

                else:             # ontology filter available
                    with col1:
                        col1a, col1b = st.columns([1,2])
                    with col1a:
                        list_to_choose = [utils.get_ontology_tag(ont_label)
                            for ont_label in reversed(st.session_state["g_ontology_components_dict"])]
                        list_to_choose.insert(0, "Select ontology")
                        ontology_filter_for_ns = st.selectbox("➖ Filter by ontology (optional):", list_to_choose,
                            key="key_ontology_filter_for_ns")

                    if ontology_filter_for_ns == "Select ontology":
                        with col1b:
                            ontology_ns_list_not_duplicated = [k for k, v in ontology_ns_dict.items() if v not in mapping_ns_dict.values()]
                            list_to_choose = ontology_ns_list_not_duplicated.copy()
                            if len(list_to_choose) > 1:
                                list_to_choose.insert(0, "Select all")
                            ontology_ns_to_bind_list = st.multiselect("🖱️ Select ontology namespaces:*", list_to_choose,
                                key="key_ontology_ns_to_bind_multiselect")

                    else:
                        if ontology_filter_for_ns not in g_ont_components_w_unbound_ns:
                            with col1b:
                                st.write("")
                                st.markdown(f"""<div class="info-message-gray">
                                    🔒 All <b>namespaces</b> of the <b style="color:#F63366;">{ontology_filter_for_ns}</b>
                                    ontology are already bound.
                                </div>""", unsafe_allow_html=True)
                                st.write("")
                            ontology_ns_to_bind_list = []
                        else:
                            for ont_label in st.session_state["g_ontology_components_dict"]:
                                if utils.get_ontology_tag(ont_label) == ontology_filter_for_ns:
                                    ont = st.session_state["g_ontology_components_dict"][ont_label]
                            ontology_component_ns_dict = utils.get_ontology_component_ns_dict(ont)
                            ontology_ns_list_not_duplicated = [k for k, v in ontology_component_ns_dict.items() if v not in mapping_ns_dict.values()]
                            list_to_choose = ontology_ns_list_not_duplicated.copy()
                            if len(list_to_choose) > 1:
                                list_to_choose.insert(0, "Select all")
                            with col1b:
                                ontology_ns_to_bind_list = st.multiselect("🖱️ Select ontology namespaces:*", list_to_choose,
                                    key="key_ontology_ns_to_bind_multiselect")

                if ontology_ns_to_bind_list:
                    already_used_prefix_list = []
                    for pr in ontology_ns_to_bind_list:
                        if pr in mapping_ns_dict:
                            already_used_prefix_list.append(pr)

                    if "Select all" not in ontology_ns_to_bind_list:   # "Select all" not selected
                        with col1:
                            st.button("Bind", key="key_bind_ontology_ns_button", on_click=bind_ontology_namespaces)
                    else:
                        ontology_ns_to_bind_list = ontology_ns_list_not_duplicated

                        with col1:
                            bind_all_ontology_ns_checkbox = st.checkbox(
                            "🔒 I am sure I want to bind all the namespaces in the ontology/ies",
                            key="key_bind_all_ontology_ns_checkbox")
                            if bind_all_ontology_ns_checkbox:
                                st.button("Bind", key="key_bind_ontology_ns_button", on_click=bind_ontology_namespaces)

                    if ontology_filter_for_ns != "Select ontology":
                        ontology_ns_dict = utils.get_ontology_component_ns_dict(ont)

                    inner_html = ""
                    max_length = utils.get_max_length_for_display()[4]
                    for prefix in ontology_ns_to_bind_list:
                        inner_html += f"""<div style="margin-bottom:6px;">
                            <b>🔗 {prefix}</b> → {ontology_ns_dict[prefix]}
                        </div>"""

                    if len(ontology_ns_to_bind_list) > max_length:
                        inner_html += f"""<div style="margin-bottom:6px;">
                            🔗 ... <b>(+{len(ontology_ns_to_bind_list[max_length:])})</b>
                        </div>"""

                    with col1:
                        col1a, col1b = st.columns([2,1])
                    with col1a:
                        st.markdown(f"""<div class="info-message-gray">
                                <small>{inner_html}</small>
                            </div>""", unsafe_allow_html=True)

                    with col1b:
                        if len(already_used_prefix_list) == 1:
                            st.markdown(f"""<div class="warning-message">
                                        <small>⚠️ <b>Prefix {utils.format_list_for_markdown(already_used_prefix_list)} is already in use</b>
                                        and will be auto-renamed with a numeric suffix.</small>
                                </div>""", unsafe_allow_html=True)

                        elif already_used_prefix_list:
                            st.markdown(f"""<div class="warning-message">
                                        <small>⚠️ <b>Prefixes {utils.format_list_for_markdown(already_used_prefix_list)} are already in use</b>
                                        and will be auto-renamed with a numeric suffix.</small>
                                </div>""", unsafe_allow_html=True)


        elif add_ns_selected_option == "📋 Predefined":
            with col1:
                col1a, col1b = st.columns([2,1])

            there_are_predefined_ns_unbound_flag = False
            for pr, ns in predefined_ns_dict.items():
                if not ns in mapping_ns_dict.values():
                    there_are_predefined_ns_unbound_flag = True
                    continue

            if not there_are_predefined_ns_unbound_flag:
                with col1a:
                    st.markdown(f"""<div class="info-message-gray">
                        🔒 All <b>predefined namespaces<b> are already bound.
                    </div>""", unsafe_allow_html=True)
                    st.write("")
            else:

                with col1a:
                    predefined_ns_list_not_duplicated = [k for k, v in predefined_ns_dict.items() if v not in mapping_ns_dict.values()]
                    list_to_choose = predefined_ns_list_not_duplicated.copy()
                    if len(list_to_choose) > 1:
                        list_to_choose.insert(0, "Select all")
                    predefined_ns_to_bind_list = st.multiselect("🖱️ Select predefined namespaces:*", list_to_choose,
                        key="key_predefined_ns_to_bind_multiselect")

                already_used_prefix_list = []
                for pr in predefined_ns_to_bind_list:
                    if pr in mapping_ns_dict:
                        already_used_prefix_list.append(pr)

                # Information messages
                if predefined_ns_to_bind_list and "Select all" not in predefined_ns_to_bind_list:
                    # create a single info message
                    inner_html = ""
                    max_length = utils.get_max_length_for_display()[4]
                    for prefix in predefined_ns_to_bind_list[:max_length]:
                        inner_html += f"""<div style="margin-bottom:6px;">
                            <b>🔗 {prefix}</b> → {predefined_ns_dict[prefix]}
                        </div>"""

                    if len(predefined_ns_to_bind_list) > max_length:   # many sm to remove
                        inner_html += f"""<div style="margin-bottom:6px;">
                            🔗 ... <b>(+{len(predefined_ns_to_bind_list[max_length:])})</b>
                        </div>"""

                elif predefined_ns_to_bind_list:
                    # create a single info message
                    inner_html = ""
                    max_length = utils.get_max_length_for_display()[4]
                    for prefix in list(predefined_ns_list_not_duplicated)[:max_length]:
                        inner_html += f"""<div style="margin-bottom:6px;">
                            <b>🔗 {prefix}</b> → {predefined_ns_dict[prefix]}
                        </div>"""

                    if len(predefined_ns_list_not_duplicated) > max_length:   # many sm to remove
                        inner_html += f"""<div style="margin-bottom:6px;">
                            🔗 ... <b>(+{len(list(predefined_ns_list_not_duplicated)[max_length:])})</b>
                        </div>"""


                if predefined_ns_to_bind_list:
                    st.session_state["predefined_ns_to_bind_list"] = predefined_ns_to_bind_list
                    if "Select all" not in predefined_ns_to_bind_list:   # "Select all" not selected
                        with col1a:
                            st.button("Bind", key="key_bind_predefined_ns_button", on_click=bind_predefined_namespaces)
                    else:
                        with col1a:
                            bind_all_predefined_ns_button_checkbox = st.checkbox(
                            "🔒 I want to bind all predefined namespaces",
                            key="key_bind_all_predefined_ns_button_checkbox")
                            if bind_all_predefined_ns_button_checkbox:
                                st.button("Bind", key="key_bind_all_predefined_ns_button", on_click=bind_predefined_namespaces)

                    with col1:
                        col1a, col1b = st.columns([2,1])
                    with col1a:
                        st.markdown(f"""<div class="info-message-gray">
                                <small>{inner_html}</small>
                            </div>""", unsafe_allow_html=True)

                    with col1b:
                        if len(already_used_prefix_list) == 1:
                            st.markdown(f"""<div class="warning-message">
                                        <small>⚠️ <b>Prefix {utils.format_list_for_markdown(already_used_prefix_list)} is already in use</b>
                                        and will be auto-renamed with a numeric suffix.</small>
                                </div>""", unsafe_allow_html=True)

                        elif already_used_prefix_list:
                            st.markdown(f"""<div class="warning-message">
                                        <small>⚠️ <b>Prefixes {utils.format_list_for_markdown(already_used_prefix_list)} are already in use</b>
                                        and will be auto-renamed with a numeric suffix.</small>
                                </div>""", unsafe_allow_html=True)



        if add_ns_selected_option == "🏛️ Base":

            with col1:
                st.markdown(f"""<div class="gray-preview-message">
                        🔒 Base IRI:
                        <span style="font-size:0.92em;"><b>
                        🔗 {st.session_state["structural_ns"][0]}</b> →
                        <b style="color:#F63366;">{st.session_state["structural_ns"][1]}
                        </span></b><br>
                        <small>To change it, enter another option below.</small>
                    </div>""", unsafe_allow_html=True)
                st.write("")
            with col1:
                col1a, col1b = st.columns([1,2])
            with col1a:
                structural_ns_prefix_candidate = st.text_input("⌨️ Enter prefix:", key="key_structural_ns_prefix_candidate")
            with col1b:
                structural_ns_iri_candidate = st.text_input("⌨️ Enter base IRI:", key="key_structural_ns_iri_candidate")

            with col1a:
                if structural_ns_prefix_candidate:
                    valid_prefix_input = False
                    if structural_ns_prefix_candidate in mapping_ns_dict:
                        bound_prefix = "Namespace not bound"
                        for pr, ns in mapping_ns_dict.items():
                            if ns == structural_ns_iri_candidate:
                                bound_prefix = pr
                                break
                        if bound_prefix != structural_ns_prefix_candidate:
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ <b>Prefix is already in use.</b>
                                <small>The chosen prefix will be auto-renamed with a numeric suffix.</small>
                            </div>""", unsafe_allow_html=True)
                            valid_prefix_input = True
                    else:
                        valid_prefix_input = True

            with col1b:

                if structural_ns_iri_candidate:
                    valid_iri_input = False
                    if not utils.is_valid_iri(structural_ns_iri_candidate):
                        st.markdown(f"""<div class="error-message">
                            ❌ <b> Invalid IRI. </b>
                            <small>Please make sure it starts with a valid scheme (e.g., http, https), includes no illegal characters
                            and ends with a delimiter (/, # or :).</small>
                        </div>""", unsafe_allow_html=True)
                    elif structural_ns_iri_candidate in mapping_ns_dict.values():
                        for pr, ns in mapping_ns_dict.items():
                            if ns == structural_ns_iri_candidate:
                                bound_prefix = pr
                                break
                        if structural_ns_prefix_candidate == bound_prefix:
                            st.markdown(f"""<div class="error-message">
                                ❌ <b> Namespace is already bound to prefix {bound_prefix}.</b>
                            </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ <b> Namespace is already bound to prefix {bound_prefix}. </b>
                                <small>If you continue, that prefix will be overwritten <b>({bound_prefix} → {structural_ns_prefix_candidate})</b>.</small>
                            </div>""", unsafe_allow_html=True)
                            valid_iri_input = True
                    else:
                        valid_iri_input = True






                if structural_ns_iri_candidate and structural_ns_prefix_candidate:
                    if valid_iri_input and valid_prefix_input:
                        with col1:
                            unbind_previous_base_ns_checkbox = st.checkbox(f"🗑️ Unbind {st.session_state["structural_ns"][0]} namespace",
                                key="key_unbind_previous_base_ns_checkbox", value=True)
                            st.button("Confirm", key="key_change_structural_ns_button", on_click=change_structural_ns)

                if not structural_ns_iri_candidate and not structural_ns_prefix_candidate:
                    if st.session_state["structural_ns"] != utils.get_default_structural_ns():
                        with col1:
                            default_structural_ns = utils.get_default_structural_ns()
                            structural_ns_prefix_candidate = default_structural_ns[0]
                            structural_ns_iri_candidate = default_structural_ns[1]
                            unbind_previous_base_ns_checkbox = False
                            st.button("Set to default", key="key_structural_ns_set_to_default_button", on_click=change_structural_ns)




        # unbind ns success message - show here if "Unbind" purple heading is not going to be shown
        mapping_ns_dict = utils.get_mapping_ns_dict()

        if not mapping_ns_dict or mapping_ns_dict == {st.session_state["structural_ns"][0]: st.session_state["structural_ns"][1]}:
            if st.session_state["ns_unbound_ok_flag"]:
                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    st.markdown(f"""<div class="success-message-flag">
                        ✅ The <b>Namespace/s</b> have been unbound!
                    </div>""", unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.session_state["ns_unbound_ok_flag"] = False
                time.sleep(st.session_state["success_display_time"])
                st.rerun()

        # PURPLE HEADING - UNBIND NS (if there are bound ns)
        if mapping_ns_dict and mapping_ns_dict != {st.session_state["structural_ns"][0]: st.session_state["structural_ns"][1]}:
            with col1:
                st.write("______")
                st.markdown("""<div class="purple-heading">
                        🗑️ Unbind Existing Namespace
                    </div>""", unsafe_allow_html=True)
                st.markdown("")

            if st.session_state["ns_unbound_ok_flag"]:  # show message here if "Unbind" purple heading is going to be shown
                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    st.markdown(f"""<div class="success-message-flag">
                        ✅ The <b>Namespace/s</b> have been unbound!
                    </div>""", unsafe_allow_html=True)
                st.write("")
                st.session_state["ns_unbound_ok_flag"] = False
                time.sleep(st.session_state["success_display_time"])
                st.rerun()

            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                mapping_ns_dict = utils.get_mapping_ns_dict()
                list_to_choose = sorted(mapping_ns_dict.keys())
                if st.session_state["structural_ns"][0] in list_to_choose:
                    list_to_choose.remove(st.session_state["structural_ns"][0])
                if len(list_to_choose) > 1:
                    list_to_choose.insert(0, "Select all")
                ns_to_unbind_list = st.multiselect("🖱️ Select namespaces to unbind:*", list_to_choose, key="key_unbind_multiselect")


            if ns_to_unbind_list and "Select all" not in ns_to_unbind_list:

                # create a single info message
                inner_html = ""
                max_length = utils.get_max_length_for_display()[4]
                formatted_ns_to_unbind = utils.format_list_for_markdown(ns_to_unbind_list)
                for prefix in ns_to_unbind_list[:max_length]:
                    inner_html += f"""<div style="margin-bottom:6px;">
                        <b>🔗 {prefix}</b> → {mapping_ns_dict[prefix]}
                    </div>"""

                if len(ns_to_unbind_list) > max_length:   # many sm to remove
                    inner_html += f"""<div style="margin-bottom:6px;">
                        🔗 ... <b>(+{len(ns_to_unbind_list[:max_length])})</b>
                    </div>"""

                with col1a:
                    unbind_ns_button_checkbox = st.checkbox(
                    "🔒 I am sure want to unbind the selected namespace/s",
                    key="key_unbind_all_ns_button_checkbox")
                    if unbind_ns_button_checkbox:
                        st.button(f"Unbind", key="key_unbind_ns_button", on_click=unbind_namespaces)

                    if len(ns_to_unbind_list) > 0:
                        with col1a:
                            st.markdown(f"""<div class="info-message-gray">
                                    <small>{inner_html}</small>
                                </div>""", unsafe_allow_html=True)


            elif ns_to_unbind_list:    # unbind all namespaces

                # create a single info message
                inner_html = ""
                max_length = utils.get_max_length_for_display()[4]
                mapping_ns_dict_wo_structural_ns = {k: v for k, v in mapping_ns_dict.items() if k != st.session_state["structural_ns"][0]}

                for prefix in list(mapping_ns_dict_wo_structural_ns)[:max_length]:
                    if prefix != "Select all":
                        inner_html += f"""<div style="margin-bottom:6px;">
                            🔗 <b>{prefix}</b> → {mapping_ns_dict_wo_structural_ns[prefix]}
                        </div>"""

                if len(mapping_ns_dict_wo_structural_ns) > max_length:   # many sm to remove
                    inner_html += f"""<div style="margin-bottom:2px;">
                        🔗 ... <b>(+{len(list(mapping_ns_dict_wo_structural_ns)[:max_length])})</b>
                    </div>"""

                with col1b:
                    st.write("")
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ You are deleting <b>all namespaces</b>.
                        <small>Make sure you want to go ahead.</small>
                    </div>""", unsafe_allow_html=True)

                with col1a:
                    unbind_all_ns_button_checkbox = st.checkbox(
                    "🔒 I am sure I want to unbind all namespaces",
                    key="key_unbind_all_ns_button_checkbox")
                    if unbind_all_ns_button_checkbox:
                        st.button("Unbind", key="key_unbind_all_ns_button", on_click=unbind_all_namespaces)

                    st.markdown(f"""<div class="info-message-gray">
                            <small>{inner_html}</small>
                        </div>""", unsafe_allow_html=True)


#_____________________________________________




#________________________________________________
# SAVE MAPPING OPTION
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
        # with col2b:
        #     utils.get_corner_status_message()

        with col2b:
            st.write("")
            save_progress_checkbox = st.checkbox(
                "💾 Save progress",
                key="key_save_progress_checkbox")
            if save_progress_checkbox:
                st.button("Save", key="key_save_progress_button", on_click=save_progress)
                st.markdown(f"""<div class="info-message-blue">
                        ℹ️ Current project state will be temporarily saved (mapping <b style="color:#F63366;">
                        {st.session_state["g_label"]}</b>,
                        loaded ontologies and data sources).
                        <small>To retrieve cached work go to the <b>Select Mapping</b> panel.</small>
                    </span></div>""", unsafe_allow_html=True)
                existing_pkl_file_list = [f for f in os.listdir() if f.endswith("_cache__.pkl")]
                if existing_pkl_file_list:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ Any previously cached mapping will be deleted.
                        </div>""", unsafe_allow_html=True)


        if st.session_state["progress_saved_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ Current state of mapping <b style="color:#F63366;">{st.session_state["g_label"]}</b> has been cached!
                </div>""", unsafe_allow_html=True)
            st.session_state["progress_saved_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()


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
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The mapping <b style="color:#F63366;">{st.session_state["g_label"]}</b> has been exported!
                </div>""", unsafe_allow_html=True)
            st.session_state["key_export_filename_selectbox"] = ""
            st.session_state["mapping_downloaded_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()

        with col1:
            col1a, col1b, col1c = st.columns([0.8,1.7,1])

        export_extension_dict = utils.get_g_mapping_file_formats_dict()
        export_format_list = list(export_extension_dict)

        with col1a:
            export_format = st.selectbox("🖱️ Select format:*", export_format_list, key="key_export_format_selectbox")
        export_extension = export_extension_dict[export_format]

        with col1b:
            export_filename = st.text_input("⌨️ Enter filename (without extension):*", key="key_export_filename_selectbox")

        with col1c:
            if export_filename:
                export_filename_valid_flag = utils.is_valid_filename(export_filename)

        export_filename_complete = export_filename + export_extension if export_filename else ""

        if export_filename_complete and export_filename_valid_flag:
            with col1c:
                st.markdown(f"""<div class="info-message-blue">
                        ℹ️ Current state of mapping <b>
                        {st.session_state["g_label"]}</b> will exported
                        to file <b style="color:#F63366;">{export_filename_complete}</b>.
                    </span></div>""", unsafe_allow_html=True)

            serialised_data = st.session_state["g_mapping"].serialize(format=export_format)
            with col1a:
                st.session_state["mapping_downloaded_ok_flag"] = st.download_button(label="Export", data=serialised_data,
                    file_name=export_filename_complete, mime="text/plain")

            # THIS IS TO DELETE EVERYTHING AFTER SAVING
            # if st.session_state["mapping_downloaded_ok_flag"]:    # delete cache file if any and rerun
            #     for file in os.listdir():
            #         if file.endswith("_cache__.pkl") and os.path.isfile(file):
            #             os.remove(file)
            #     for key in list(st.session_state.keys()):   # clean session state
            #         del st.session_state[key]
            #     st.rerun()   # to get to success message

        if st.session_state["g_label"] and export_filename:
            check_g_mapping = utils.check_g_mapping(st.session_state["g_mapping"])
            if check_g_mapping:
                max_length = utils.get_max_length_for_display()[5]
                inner_html = "⚠️" + check_g_mapping
                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    st.markdown(f"""<div class="warning-message">
                            {inner_html}
                        </div>""", unsafe_allow_html=True)


        with col1:
            st.write("________")
            st.markdown("""<div class="purple-heading">
                    💾 Save session
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["session_saved_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The session has been saved to file <b style="color:#F63366;">{st.session_state["pkl_filename"]}</b>!
                </div>""", unsafe_allow_html=True)
            st.session_state["session_saved_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()

        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            pkl_filename = st.text_input("⌨️ Enter filename (without extension):*", key="key_pkl_filename")

        if pkl_filename:
            # if "." in pkl_filename:
            #     with col1b:
            #         st.markdown(f"""<div class="warning-message">
            #                 ⚠️ The filename <b style="color:#cc9a06;">{pkl_filename}</b>
            #                 seems to include an extension.
            #             </div>""", unsafe_allow_html=True)
            with col1b:
                valid_pkl_filename_flag = utils.is_valid_filename(pkl_filename)


        folder_name = "saved_sessions"
        pkl_filename_w_extension = pkl_filename + '.pkl'
        folder_path = os.path.join(os.getcwd(), folder_name)
        file_path = os.path.join(folder_path, pkl_filename_w_extension)

        if pkl_filename and os.path.isfile(file_path):
            with col1b:
                st.markdown(f"""<div class="warning-message">
                        ⚠️ <b>A session was already saved with this filename</b>. <small>Please, pick
                        a different filename unless you want to overwrite it.</small>
                    </div>""", unsafe_allow_html=True)
            with col1a:
                overwrite_pkl_checkbox = st.checkbox(
                    f"""🔒 I am sure I want to overwrite""",
                    key="key_overwrite_pkl_checkbox")
            if overwrite_pkl_checkbox:
                with col1a:
                    st.button("Save", key="key_save_session_button", on_click=save_session)
        elif pkl_filename and valid_pkl_filename_flag:
            with col1b:
                st.markdown(f"""<div class="info-message-blue">
                        ℹ️ Current <b>session state</b> will be exported
                        to file <b style="color:#F63366;">{pkl_filename + ".pkl"}</b>.
                        <small> This includes the mapping, ontologies, namespaces and data sources.</small>
                    </span></div>""", unsafe_allow_html=True)
            with col1a:
                st.button("Save", key="key_save_session_button", on_click=save_session)


#_____________________________________________

#________________________________________________
# SET STYLE OPTION
with tab4:

    st.write("")
    st.write("")

    col1,col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])

    with col1:
        st.markdown("""<div class="purple-heading">
                🎨 Style Configuration
            </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([2,1])

    with col1a:
        if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
            st.markdown(f"""<div class="gray-preview-message">
                    🔒 <b>Dark mode OFF</b>.
                    <small>Click button to activate.</small>
                </div>""", unsafe_allow_html=True)
            st.write("")
            st.button("Activate Dark Mode", on_click=activate_dark_mode, key="key_activate_dark_mode_button")
        else:
            st.markdown(f"""<div class="gray-preview-message">
                    🔒 <b>Dark mode ON</b>.
                    <small>Click button to deactivate.</small>
                </div>""", unsafe_allow_html=True)
            st.write("")
            st.button("Dectivate Dark Mode", on_click=deactivate_dark_mode, key="key_deactivate_dark_mode_button")

#_____________________________________________

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

# Config------------------------------------------------------------------------
if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
    st.set_page_config(page_title="3Xmap Studio", layout="wide",
        page_icon="logo/fav_icon.png")
else:
    st.set_page_config(page_title="3Xmap Studio", layout="wide",
        page_icon="logo/fav_icon_inverse.png")

# Initialise page---------------------------------------------------------------
utils.init_page()
RML, QL = utils.get_required_ns_dict().values()

# Define on_click functions-----------------------------------------------------
#TAB1
def create_new_g_mapping():
    # optional reset (clear everything)_____________________
    if overwrite_g_mapping_and_session_checkbox:
        utils.full_reset()
    # create mapping__________________________________
    st.session_state["g_label"] = st.session_state["g_label_temp_new"]   # consolidate g_label
    st.session_state["g_mapping"] = Graph()   # create a new empty mapping
    # bind default namespaces__________________________
    for prefix, namespace in utils.get_default_ns_dict().items():
        utils.bind_namespace(prefix, namespace)
    # bind required namespaces___________________________
    for prefix, namespace in utils.get_required_ns_dict().items():
        utils.bind_namespace(prefix, namespace)
    # bind base namespaces_______________________________
    prefix, ns = utils.get_default_base_ns()
    st.session_state["g_mapping"].bind(prefix, ns)
    # bind ontology namespaces______________________________
    ontology_ns_dict = utils.get_g_ns_dict(st.session_state["g_ontology"])
    for prefix, namespace in ontology_ns_dict.items():
        utils.bind_namespace(prefix, namespace)
    # store information________________________________
    st.session_state["g_mapping_source_cache"] = ["scratch", ""]   #cache info on the mapping source
    st.session_state["original_g_mapping_ns_dict"] = {}
    st.session_state["new_g_mapping_created_ok_flag"] = True   #flag for success mesagge
    utils.empty_last_added_lists()
    # reset fields__________________
    st.session_state["key_g_label_temp_new"] = ""

def import_existing_g_mapping():
    # optional reset (clear everything)_____________________
    if overwrite_g_mapping_and_session_checkbox:
        utils.full_reset()
    # import mapping_____________________________________
    st.session_state["g_label"] = st.session_state["g_label_temp_existing"]   # consolidate g_label
    st.session_state["original_g_size_cache"] = utils.get_number_of_tm(st.session_state["candidate_g_mapping"])
    st.session_state["original_g_mapping_ns_dict"] = utils.get_g_ns_dict(st.session_state["candidate_g_mapping"])
    st.session_state["g_mapping"] = st.session_state["candidate_g_mapping"]   # consolidate the loaded mapping
    # set base namespace___________________________________
    st.session_state["base_ns"] = utils.get_g_mapping_base_ns()
    utils.change_g_mapping_base_ns(st.session_state["base_ns"][0], st.session_state["base_ns"][1])  # ensure all nodes have same base ns
    # bind default namespaces____________________________
    for prefix, namespace in utils.get_default_ns_dict().items():
        utils.bind_namespace(prefix, namespace)
    # bind required namespaces______________________________
    for prefix, namespace in utils.get_required_ns_dict().items():
        utils.bind_namespace(prefix, namespace)
    # bind mapping namespaces_________________________________
    for prefix, namespace in st.session_state["g_mapping"].namespaces():
        utils.bind_namespace(prefix, namespace)
    # bind ontology namespaces_____________________________
    ontology_ns_dict = utils.get_g_ns_dict(st.session_state["g_ontology"])
    for prefix, namespace in ontology_ns_dict.items():
        utils.bind_namespace(prefix, namespace)
    # store information________________________
    if import_mapping_selected_option == "🌐 URL":
        st.session_state["g_mapping_source_cache"] = ["URL", selected_mapping_input]
    elif import_mapping_selected_option == "📁 File":
        st.session_state["g_mapping_source_cache"] = ["file", selected_mapping_input.name]
    st.session_state["existing_g_mapping_loaded_ok_flag"] = True
    utils.empty_last_added_lists()
    # reset fields___________________________
    st.session_state["key_mapping_link"] = ""
    st.session_state["key_import_mapping_selected_option"] = "🌐 URL"
    st.session_state["key_mapping_uploader"] = str(uuid.uuid4())
    st.session_state["key_g_label_temp_existing"] = ""

def retrieve_session():
    # get information from pkl file___________________________
    full_path = os.path.join(folder_name, selected_pkl_file_w_extension)
    # retrieve session___________________________
    with open(full_path, "rb") as f:     # load mapping
        project_state_list = pickle.load(f)
    utils.retrieve_project_state(project_state_list)
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

def full_reset():
    # full reset___________________________
    utils.full_reset()
    #store information___________________________
    st.session_state["everything_reseted_ok_flag"] = True
    # reset fields___________________________
    st.session_state["key_full_reset_checkbox"] = False

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
    # bind and store information___________________________
    for prefix in st.session_state["predefined_ns_to_bind_list"]:
        namespace = predefined_ns_dict[prefix]
        utils.bind_namespace(prefix, namespace)
    st.session_state["ns_bound_ok_flag"] = True    #for success message
    # reset fields_____________________________
    st.session_state["key_predefined_ns_to_bind_multiselect"] = []
    st.session_state["key_add_ns_radio"] = "📋 Predefined"

def bind_original_mapping_namespaces():
    # bind and store information___________________________
    for prefix in original_mapping_ns_to_bind_list:
        namespace = original_mapping_ns_dict[prefix]
        utils.bind_namespace(prefix, namespace)
    st.session_state["ns_bound_ok_flag"] = True   # for success message
    # reset fields_____________________________
    st.session_state["key_original_mapping_ns_to_bind_multiselect"] = []
    st.session_state["key_add_ns_radio"] = "🗺️ Mapping"

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

def change_base_ns():
    # bind new namespace and store________________________
    st.session_state["base_ns"] = [base_ns_prefix_candidate, Namespace(base_ns_iri_candidate)]
    utils.bind_namespace(base_ns_prefix_candidate, base_ns_iri_candidate)
    # change base namespace in g mapping___________________
    utils.change_g_mapping_base_ns(st.session_state["base_ns"][0], st.session_state["base_ns"][1])
    #store information________________________
    st.session_state["base_ns_changed_ok_flag"] = True
    # reset fields_____________________________
    st.session_state["key_base_ns_prefix_candidate"] = "Select prefix"
    st.session_state["key_add_ns_radio"] = "🏛️ Base"

def unbind_namespaces():
    # unbind the namespaces and store information_________________
    utils.unbind_namespaces(ns_to_unbind_list)
    st.session_state["ns_unbound_ok_flag"] = True
    # reset fields_____________________________
    st.session_state["key_unbind_multiselect"] = []

def unbind_all_namespaces():
    # unbind and store information___________________________
    utils.unbind_namespaces(mapping_ns_dict_available_to_unbind)
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
    # create folder if needed_________________________
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

def delete_sessions():
    # remove files___________________________________
    for file in sessions_to_remove_list:
        file_path = os.path.join(folder_path, file + ".pkl")
        if os.path.isfile(file_path):
            os.remove(file_path)
    # remove folder if empty___________________
    if not os.listdir(folder_path):
        os.rmdir(folder_path)
    # store information_________________________________
    st.session_state["session_removed_ok_flag"] = True
    # reset fields_______________________________
    st.session_state["key_save_session_options"] = "💾 Save session"

# TAB5
def activate_dark_mode():
    st.session_state["dark_mode_flag"] = True

def deactivate_dark_mode():
    st.session_state["dark_mode_flag"] = False

#_______________________________________________________________________________
# PANELS OF THE PAGE (tabs)
tab1, tab2, tab3, tab4 = st.tabs(["Select Mapping",
    "Configure Namespaces", "Save Mapping", "Set Style"])

#_______________________________________________________________________________
# PANEL: SELECT MAPPING
with tab1:
    st.write("")
    st.write("")

    # PURPLE HEADING: CREATE NEW MAPPING----------------------------------------
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
        time.sleep(utils.get_success_message_time())
        st.rerun()

    with col1a:
        st.session_state["g_label_temp_new"] = st.text_input("🏷️ Enter mapping label:*", # just a candidate until confirmed
        key="key_g_label_temp_new")
        valid_mapping_label = utils.is_valid_label_hard(st.session_state["g_label_temp_new"])

    # A mapping has not been loaded yet
    if not st.session_state["g_label"]:

        if valid_mapping_label:

            if st.session_state["db_connections_dict"] or st.session_state["ds_files_dict"] or st.session_state["g_ontology_components_dict"]:
                with col1:
                    overwrite_g_mapping_and_session_checkbox = st.checkbox(
                        f"""🔄 Start fresh: remove previously loaded ontologies and data sources""",
                        value=True, key="key_overwrite_g_mapping_and_session_checkbox_new")
            else:
                overwrite_g_mapping_and_session_checkbox = False

            with col1:
                st.button("Create", on_click=create_new_g_mapping, key="key_create_new_g_mapping_button_1")


    # A mapping is currently loaded
    else:
        if valid_mapping_label:

            with col1b:
                st.markdown(f"""<div class="warning-message">
                        ⚠️ Mapping <b>{st.session_state["g_label"]}</b> will be overwritten.
                        <small>You can export it or save the session in
                        the <b>Save Mapping </b> panel.</small>
                    </div>""", unsafe_allow_html=True)

            if st.session_state["db_connections_dict"] or st.session_state["ds_files_dict"] or st.session_state["g_ontology_components_dict"]:
                with col1a:
                    overwrite_g_mapping_and_session_checkbox = st.checkbox(
                        f"""🔄 Start fresh: remove previously loaded ontologies and data sources""",
                        value=True, key="key_overwrite_g_mapping_and_session_checkbox_new")
            else:
                overwrite_g_mapping_and_session_checkbox = False

            with col1a:
                overwrite_g_mapping_checkbox = st.checkbox(
                    f"""🔒 I am sure I want to overwrite mapping {st.session_state["g_label"]}""",
                    key="key_overwrite_g_mapping_checkbox_new")

            if overwrite_g_mapping_checkbox:
                with col1a:
                    st.button(f"""Create""", on_click=create_new_g_mapping, key="key_create_new_g_mapping_button_2")

    with col1:
        st.write("______")


    # PURPLE HEADING- IMPORT EXISTING MAPPING-----------------------------------
    with col1:
        st.markdown("""<div class="purple-heading">
                📁 Import Existing Mapping
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
        time.sleep(utils.get_success_message_time())
        st.rerun()

    with col1b:
        import_mapping_selected_option = st.radio("🖱️ Select an option:*", ["🌐 URL", "📁 File"],
            label_visibility="hidden", horizontal=True, key="key_import_mapping_selected_option")

    if import_mapping_selected_option == "🌐 URL":
        with col1a:
            selected_mapping_input = st.text_input(f"""⌨️ Enter link to mapping:*""", key="key_mapping_link")

        if selected_mapping_input:
            try:
                suggested_mapping_label = split_uri(selected_mapping_input)[1]
                suggested_mapping_label = utils.format_suggested_mapping_label(suggested_mapping_label)
            except:
                suggested_mapping_label = ""

            with col1:
                col1a, col1b = st.columns([2,1])

            with col1a:
                st.session_state["g_label_temp_existing"] = st.text_input("🏷️ Enter mapping label:*",   # just candidate until confirmed
                    key="key_g_label_temp_existing", value=suggested_mapping_label)

            with col1a:
                valid_mapping_label = utils.is_valid_label_hard(st.session_state["g_label_temp_existing"])

            with col1b:
                st.write("")
                st.session_state["candidate_g_mapping"] = utils.load_mapping_from_link(
                    selected_mapping_input)   # we load the mapping as a candidate (until confirmed)

    elif import_mapping_selected_option == "📁 File":

        with col1a:
            selected_mapping_input = st.file_uploader(f"""🖱️
            Upload mapping file:*""", type=mapping_format_list, key=st.session_state["key_mapping_uploader"])

        with col1b:
            if selected_mapping_input:

                suggested_mapping_label = os.path.splitext(selected_mapping_input.name)[0]
                suggested_mapping_label = utils.format_suggested_mapping_label(suggested_mapping_label)

                st.session_state["g_label_temp_existing"] = st.text_input("🏷️ Enter mapping label:*",   # just candidate until confirmed
                    key="key_g_label_temp_existing", value=suggested_mapping_label)
                valid_mapping_label = utils.is_valid_label_hard(st.session_state["g_label_temp_existing"])

                st.session_state["candidate_g_mapping"] = utils.load_mapping_from_file(
                    selected_mapping_input)   # we load the mapping as a candidate (until confirmed)

    # A mapping has not been loaded yet
    if st.session_state["candidate_g_mapping"] and not st.session_state["g_label"]:

        if valid_mapping_label and selected_mapping_input:
            if st.session_state["db_connections_dict"] or st.session_state["ds_files_dict"] or st.session_state["g_ontology_components_dict"]:
                with col1:
                    overwrite_g_mapping_and_session_checkbox = st.checkbox(
                        f"""🔄 Start fresh: remove previously loaded ontologies and data sources""",
                        value=True, key="key_overwrite_g_mapping_and_session_checkbox_existing")
            else:
                overwrite_g_mapping_and_session_checkbox = False
            with col1:
                st.button("Import", on_click=import_existing_g_mapping, key="key_import_existing_g_mapping_button_2")


    # A mapping is currently loaded
    elif st.session_state["candidate_g_mapping"] and st.session_state["g_label"]:
        if valid_mapping_label and selected_mapping_input:
            with col1b:
                st.markdown(f"""<div class="warning-message">
                        ⚠️ Mapping <b>{st.session_state["g_label"]}</b> will be overwritten.
                        <small>You can export it or save the session in
                        the <b>Save Mapping </b> panel.</small>
                    </div>""", unsafe_allow_html=True)

            if st.session_state["db_connections_dict"] or st.session_state["ds_files_dict"] or st.session_state["g_ontology_components_dict"]:
                with col1a:
                    overwrite_g_mapping_and_session_checkbox = st.checkbox(
                        f"""🔄 Start fresh: remove previously loaded ontologies and data sources""",
                        value=True, key="key_overwrite_g_mapping_and_session_checkbox_existing")
            else:
                overwrite_g_mapping_and_session_checkbox = False

            with col1a:
                overwrite_g_mapping_checkbox = st.checkbox(
                    f"""🔒 I am sure I want to overwrite mapping {st.session_state["g_label"]}""",
                    key="key_overwrite_g_mapping_checkbox_existing")

            if overwrite_g_mapping_checkbox:
                with col1a:
                    st.button(f"""Import""", on_click=import_existing_g_mapping, key="key_import_existing_g_mapping_button_2")

    # PURPLE HEADING - RETRIEVE SAVED SESSION-----------------------------------
    # Only shows if there exist saved sessions
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
            time.sleep(utils.get_success_message_time())
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

                with col1b:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ Mapping <b>{st.session_state["g_label"]}</b> will be overwritten.
                            <small>You can export it or save the session in
                            the <b>Save Mapping </b> panel.
                        </div>""", unsafe_allow_html=True)

            else:
                st.button("Retrieve", key="key_retrieve_session_button_2", on_click=retrieve_session)

    # SUCCESS MESSAGES----------------------------------------------------------
    # for retrieve cached mapping, change label and full reset

    if st.session_state["cached_mapping_retrieved_ok_flag"]:
        with col3:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ Mapping <b style="color:#F63366;">{st.session_state["g_label"]}</b> has been retrieved from cache!
            </div>""", unsafe_allow_html=True)
        st.session_state["cached_mapping_retrieved_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    if st.session_state["g_label_changed_ok_flag"]:
        with col3:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ Mapping was renamed to <b style="color:#F63366;">{st.session_state["g_label"]}</b>!
            </div>""", unsafe_allow_html=True)
        st.session_state["g_label_changed_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    if st.session_state["everything_reseted_ok_flag"]:
        with col3:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ <b>Clean slate:</b> Everything has been <b style="color:#F63366;">reset</b>!
            </div>""", unsafe_allow_html=True)
        st.session_state["everything_reseted_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    # RIGHT COLUMN: MAPPING INFORMATION BOX-------------------------------------
    with col3:
        if st.session_state["g_label"]:

            if st.session_state["g_mapping_source_cache"][0] == "URL":
                max_length = utils.get_max_length_for_display()[8]
                URL_for_display = st.session_state["g_mapping_source_cache"][1]
                if len(URL_for_display) > max_length:
                    URL_for_display = "..." + URL_for_display[-max_length:]
                st.markdown(f"""<div class="gray-preview-message">
                        <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                        style="vertical-align:middle; margin-right:8px; height:20px;">
                        You are working with mapping
                        <b style="color:#F63366;">{st.session_state["g_label"]}</b>.
                        <ul style="font-size:0.85rem; margin:6px 0 0 15px; padding-left:10px;">
                            <li>Mapping was loaded from URL <b>{URL_for_display}</b></li>
                            <li>When loaded, mapping had <b>{st.session_state["original_g_size_cache"]} TriplesMaps</b></li>
                            <li>Now mapping has <b>{utils.get_number_of_tm(st.session_state["g_mapping"])} TriplesMaps<b/></li>
                        </ul></div>""", unsafe_allow_html=True)

            elif st.session_state["g_mapping_source_cache"][0] == "file":
                st.markdown(f"""<div class="gray-preview-message">
                        <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                        style="vertical-align:middle; margin-right:8px; height:20px;">
                        You are working with mapping
                        <b style="color:#F63366;">{st.session_state["g_label"]}</b>.
                        <ul style="font-size:0.85rem; margin:6px 0 0 15px; padding-left:10px;">
                            <li>Mapping was loaded from file <b>{st.session_state["g_mapping_source_cache"][1]}</b></li>
                            <li>When loaded, mapping had <b>{st.session_state["original_g_size_cache"]} TriplesMaps</b></li>
                            <li>Now mapping has <b>{utils.get_number_of_tm(st.session_state["g_mapping"])} TriplesMaps<b/></li>
                        </ul></div>""", unsafe_allow_html=True)

            else:
                st.markdown(f"""<div class="gray-preview-message">
                        <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                        style="vertical-align:middle; margin-right:8px; height:20px;">
                        You are working with mapping
                        <b style="color:#F63366;">{st.session_state["g_label"]}</b>.
                        <ul style="font-size:0.85rem; margin:6px 0 0 15px; padding-left:10px;">
                            <li>Mapping was created <b>from scratch</b></li>
                            <li>Mapping has <b>{utils.get_number_of_tm(st.session_state["g_mapping"])} TriplesMaps<b/></li>
                        </ul></div>""", unsafe_allow_html=True)


        else:
            st.markdown("""<div class="gray-preview-message">
                🚫 <b>No mapping</b> has been loaded yet.
            </div>
            """, unsafe_allow_html=True)

    # RIGHT COLUMN OPTION: Retrieve cached mapping------------------------------
    # Only shows if not working with a mapping
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
                    st.button("Retrieve", key="key_retrieve_cached_mapping_button", on_click=retrieve_cached_mapping)
                    st.markdown(f"""<div class="info-message-blue">
                            ℹ️ Mapping <b style="color:#F63366;">
                            {cached_mapping_name}</b> will be loaded, together
                            with any imported ontologies and data sources.
                        </span></div>""", unsafe_allow_html=True)


    # RIGHT COLUMN OPTION: Change the mapping label-----------------------------
    # Only shows if working with a mapping
    if st.session_state["g_label"]:

        with col3:
            st.write("")
            change_g_label_checkbox = st.checkbox(
                "🏷️ Rename mapping",
                key="key_change_mapping_label_checkbox")
            if change_g_label_checkbox:
                g_label_candidate = st.text_input("⌨️ Enter new mapping label:*")
                valid_candidate_valid_label = utils.is_valid_label_hard(g_label_candidate)

                if valid_candidate_valid_label:
                    st.button("Change", key="key_change_g_label_button", on_click=change_g_label)
                    st.markdown(f"""<div class="info-message-blue">
                            ℹ️ Mapping label will be changed to <b style="color:#F63366;">
                            {g_label_candidate}</b> (currently <b>{st.session_state["g_label"]}</b>).
                        </span></div>""", unsafe_allow_html=True)

    # RIGHT COLUMN OPTION: Full reset-------------------------------------------
    # Only shows if there is a mapping, ontology or data source
    if (st.session_state["g_label"] or st.session_state["db_connections_dict"]
        or st.session_state["ds_files_dict"] or st.session_state["g_ontology_components_dict"]):

        with col3:
            full_reset_checkbox = st.checkbox(
                "🔄 Full reset", key="key_full_reset_checkbox")
            if full_reset_checkbox:
                st.markdown(f"""<div class="warning-message">
                        ⚠️ All progress <b>will be lost</b>
                        <small>(mapping, ontologies, namespaces and/or data sources).
                        You can export the mapping or save the session in the <b>Save Mapping</b> panel.</small>
                    </span></div>""", unsafe_allow_html=True)

                second_full_reset_checkbox = st.checkbox(
                    "🔒 I am sure I want to reset everything", key="key_second_full_reset_checkbox")

                if second_full_reset_checkbox:
                    st.button("Reset", key="key_full_reset_button", on_click=full_reset)


#_______________________________________________________________________________
# PANEL: CONFIGURE NAMESPACES
# Available only if mapping is loaded
with tab2:
    st.write("")
    st.write("")

    if not st.session_state["g_label"]:
        col1, col2 = st.columns([2,1.5])
        with col1:
            utils.get_missing_g_mapping_error_message()

    else:   # only allow to continue if mapping is loaded

        col1,col2 = st.columns([2,1.5])

        # RIGHT COLUMN: ADDED NS INFO-------------------------------------------
        mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
        used_mapping_ns_dict = utils.get_used_g_ns_dict(st.session_state["g_mapping"])

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

            # Option to show used bound namespaces
            with st.expander("🔎 Show used namespaces"):
                st.write("")
                st.dataframe(used_mapping_ns_df, hide_index=True)

            # Option to show bound namespaces
            with st.expander("🔎 Show all namespaces"):
                st.write("")
                st.dataframe(mapping_ns_df, hide_index=True)


        # PURPLE HEADING: ADD NEW NAMESPACE-------------------------------------
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
            time.sleep(utils.get_success_message_time())
            st.rerun()


        if st.session_state["base_ns_changed_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>base namespace</b> has been changed!
                </div>""", unsafe_allow_html=True)
            st.session_state["base_ns_changed_ok_flag"]  = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        predefined_ns_dict = utils.get_predefined_ns_dict()
        default_ns_dict = utils.get_default_ns_dict()
        default_base_ns = utils.get_default_base_ns()
        ontology_ns_dict = utils.get_g_ns_dict(st.session_state["g_ontology"])
        mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
        ontology_ns_list = [key for key in ontology_ns_dict if key not in mapping_ns_dict]
        add_ns_options = ["✏️ Custom", "🏛️ Base"]
        if predefined_ns_dict:
            add_ns_options.insert(1, "📋 Predefined")
        if st.session_state["g_ontology_components_dict"]:
            add_ns_options.insert(1, "🧩 Ontology")
        if st.session_state["original_g_mapping_ns_dict"]:
            add_ns_options.insert(1, "🗺️ Mapping")

        with col1:
            add_ns_selected_option = st.radio("🖱️ Select an option:*", add_ns_options, key="key_add_ns_radio",
                label_visibility="collapsed", horizontal=True)

        # CUSTOM NAMESPACE
        if add_ns_selected_option == "✏️ Custom":
            with col1:
                col1a, col1b = st.columns([1,2])

            with col1a:
                prefix_input = st.text_input("⌨️ Enter prefix:* ", key = "key_prefix_input")

            with col1b:
                iri_input = st.text_input("⌨️ Enter an IRI for the new namespace:*", key="key_iri_input")
            st.session_state["new_ns_prefix"] = prefix_input if prefix_input else ""
            st.session_state["new_ns_iri"] = iri_input if iri_input else ""

            with col1a:
                if prefix_input:
                    valid_prefix_input = utils.is_valid_prefix(prefix_input)
                    if valid_prefix_input:
                        if prefix_input in mapping_ns_dict:
                            bound_prefix = ""
                            for pr, ns in mapping_ns_dict.items():
                                if ns == URIRef(iri_input):
                                    bound_prefix = pr
                                    break
                            if bound_prefix != prefix_input:
                                st.markdown(f"""<div class="warning-message">
                                    ⚠️ Prefix <b>{prefix_input}</b> is already in use.
                                    <small>The chosen prefix will be auto-renamed with a numeric suffix.</small>
                                </div>""", unsafe_allow_html=True)

            with col1b:
                if iri_input:
                    valid_iri_input = True
                    if not utils.is_valid_iri(iri_input):
                        st.markdown(f"""<div class="error-message">
                            ❌ <b> Invalid IRI. </b>
                            <small>Please make sure it starts with a valid scheme (e.g., http, https), includes no illegal characters
                            and ends with a delimiter (/, # or :).</small>
                        </div>""", unsafe_allow_html=True)
                        valid_iri_input = False
                    elif URIRef(iri_input) in mapping_ns_dict.values():
                        for pr, ns in mapping_ns_dict.items():
                            if ns == URIRef(iri_input):
                                bound_prefix = pr
                                break
                        if prefix_input == bound_prefix:
                            st.markdown(f"""<div class="error-message">
                                ❌ Namespace <b>{iri_input}</b> is already bound to prefix <b>{bound_prefix}</b>.
                                <small> Please pick a different namespace and/or prefix.</small>
                            </div>""", unsafe_allow_html=True)
                            valid_iri_input = False
                        elif prefix_input:
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ Namespace is already bound to prefix <b>{bound_prefix}</b>.
                                <small>If you continue, that prefix will be overwritten <b>({bound_prefix} → {prefix_input})</b>.</small>
                            </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ Namespace is already bound to prefix <b>{bound_prefix}</b>.
                            </div>""", unsafe_allow_html=True)

            if iri_input and prefix_input:
                if valid_iri_input and valid_prefix_input:
                    with col1a:
                        st.button("Bind", key="key_bind_custom_ns_button", on_click=bind_custom_namespace)

        # ORIGINAL MAPPING NAMESPACE
        elif add_ns_selected_option == "🗺️ Mapping":

            original_mapping_ns_dict = st.session_state["original_g_mapping_ns_dict"]
            there_are_original_mapping_ns_unbound_flag = utils.are_there_unbound_ns(original_mapping_ns_dict)

            with col1:
                col1a, col1b = st.columns([2,1])
            if not there_are_original_mapping_ns_unbound_flag:
                with col1a:
                    st.markdown(f"""<div class="info-message-gray">
                        🔒 All <b>original mapping namespaces</b> are already bound.
                    </div>""", unsafe_allow_html=True)
                    st.write("")

            else:
                with col1a:
                    original_mapping_ns_list_not_duplicated = [k for k, v in original_mapping_ns_dict.items() if v not in mapping_ns_dict.values()]
                    list_to_choose = sorted(original_mapping_ns_list_not_duplicated.copy())
                    if len(list_to_choose) > 1:
                        list_to_choose.insert(0, "Select all")
                    original_mapping_ns_to_bind_list = st.multiselect("🖱️ Select ontology namespaces:*", list_to_choose,
                        key="key_ontology_ns_to_bind_multiselect")

                if original_mapping_ns_to_bind_list:
                    already_used_prefix_list = []
                    for pr in original_mapping_ns_to_bind_list:
                        if pr in mapping_ns_dict:
                            already_used_prefix_list.append(pr)

                    if "Select all" not in original_mapping_ns_to_bind_list:   # "Select all" not selected
                        with col1:
                            st.button("Bind", key="key_bind_original_mapping_ns_button", on_click=bind_original_mapping_namespaces)
                    else:
                        original_mapping_ns_to_bind_list = original_mapping_ns_list_not_duplicated
                        with col1:
                            bind_all_original_mapping_ns_checkbox = st.checkbox(
                            "🔒 I am sure I want to bind all the namespaces in the original mapping",
                            key="key_bind_all_original_mapping_ns_checkbox")
                            if bind_all_original_mapping_ns_checkbox:
                                st.button("Bind", key="key_bind_original_mapping_ns_button", on_click=bind_original_mapping_namespaces)


                    with col1:
                        col1a, col1b = st.columns([2,1])
                    with col1a:
                        utils.get_ns_previsualisation_message(original_mapping_ns_to_bind_list, original_mapping_ns_dict)

                    with col1b:
                        utils.get_ns_warning_message(original_mapping_ns_to_bind_list)

        # ONTOLOGY NAMESPACE
        elif add_ns_selected_option == "🧩 Ontology":

            there_are_ontology_ns_unbound_flag = utils.are_there_unbound_ns(ontology_ns_dict)

            if not there_are_ontology_ns_unbound_flag:
                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    st.markdown(f"""<div class="info-message-gray">
                        🔒 All <b>ontology namespaces</b> are already bound.
                    </div>""", unsafe_allow_html=True)
                    st.write("")
            else:

                g_ont_components_w_unbound_ns = []
                for ont_label, ont in st.session_state["g_ontology_components_dict"].items():
                    ontology_component_ns_dict = utils.get_g_ns_dict(ont)
                    if utils.are_there_unbound_ns(ontology_component_ns_dict):
                        g_ont_components_w_unbound_ns.append(st.session_state["g_ontology_components_tag_dict"][ont_label])

                if len(st.session_state["g_ontology_components_dict"]) == 1:   # no ontolgoy filter
                    with col1:
                        col1a, col1b = st.columns([2,1])

                    ontology_filter_for_ns = "Select ontology"

                    with col1a:
                        ontology_ns_list_not_duplicated = [k for k, v in ontology_ns_dict.items() if v not in mapping_ns_dict.values()]
                        list_to_choose = sorted(ontology_ns_list_not_duplicated.copy())
                        if len(list_to_choose) > 1:
                            list_to_choose.insert(0, "Select all")
                        ontology_ns_to_bind_list = st.multiselect("🖱️ Select ontology namespaces:*", list_to_choose,
                            key="key_ontology_ns_to_bind_multiselect")

                else:             # ontology filter available
                    with col1:
                        col1a, col1b = st.columns([1,2])
                    with col1a:
                        list_to_choose = sorted(st.session_state["g_ontology_components_tag_dict"].values())
                        list_to_choose.insert(0, "Select ontology")
                        ontology_filter_for_ns = st.selectbox("⚙️ Filter by ontology (optional):", list_to_choose,
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
                            for ont_label, ont_tag in st.session_state["g_ontology_components_tag_dict"].items():
                                if ont_tag == ontology_filter_for_ns:
                                    ont = st.session_state["g_ontology_components_dict"][ont_label]
                            ontology_component_ns_dict = utils.get_g_ns_dict(ont)
                            ontology_ns_list_not_duplicated = [k for k, v in ontology_component_ns_dict.items() if v not in mapping_ns_dict.values()]
                            list_to_choose = ontology_ns_list_not_duplicated.copy()
                            if len(list_to_choose) > 1:
                                list_to_choose.insert(0, "Select all")
                            with col1b:
                                ontology_ns_to_bind_list = st.multiselect("🖱️ Select ontology namespaces:*", list_to_choose,
                                    key="key_ontology_ns_to_bind_multiselect")

                if ontology_ns_to_bind_list:

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
                        ontology_ns_dict = utils.get_g_ns_dict(ont)

                    with col1:
                        col1a, col1b = st.columns([2,1])
                    with col1a:
                        utils.get_ns_previsualisation_message(ontology_ns_to_bind_list, ontology_ns_dict)

                    with col1b:
                        utils.get_ns_warning_message(ontology_ns_to_bind_list)

        # PREDEFINED NAMESPACE
        elif add_ns_selected_option == "📋 Predefined":
            with col1:
                col1a, col1b = st.columns([2,1])

            there_are_predefined_ns_unbound_flag = utils.are_there_unbound_ns(predefined_ns_dict)

            if not there_are_predefined_ns_unbound_flag:
                with col1a:
                    st.markdown(f"""<div class="info-message-gray">
                        🔒 All <b>predefined namespaces<b> are already bound.
                    </div>""", unsafe_allow_html=True)
                    st.write("")
            else:
                with col1b:
                    st.write("")
                    st.markdown(f"""<div class="info-message-blue">
                        ℹ️ This option offers quick binding of <b>common namespaces</b>.
                    </div>""", unsafe_allow_html=True)

                with col1a:
                    predefined_ns_list_not_duplicated = [k for k, v in predefined_ns_dict.items() if v not in mapping_ns_dict.values()]
                    list_to_choose = sorted(predefined_ns_list_not_duplicated.copy())
                    if len(list_to_choose) > 1:
                        list_to_choose.insert(0, "Select all")
                    predefined_ns_to_bind_list = st.multiselect("🖱️ Select predefined namespaces:*", list_to_choose,
                        key="key_predefined_ns_to_bind_multiselect")

                already_used_prefix_list = []
                for pr in predefined_ns_to_bind_list:
                    if pr in mapping_ns_dict:
                        already_used_prefix_list.append(pr)

                # Information messages
                if "Select all" in predefined_ns_to_bind_list:
                    predefined_ns_to_bind_list = predefined_ns_list_not_duplicated

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
                            utils.get_ns_previsualisation_message(predefined_ns_to_bind_list, predefined_ns_dict)

                    with col1b:
                        utils. get_ns_warning_message(predefined_ns_to_bind_list)


        # CONFIGURE BASE NAMESPACE
        if add_ns_selected_option == "🏛️ Base":

            with col1:
                st.markdown(f"""<div class="gray-preview-message">
                        🏛️ Base IRI:
                        <span style="font-size:0.92em;"><b>
                        🔗 {st.session_state["base_ns"][0]}</b> →
                        <b style="color:#F63366;">{st.session_state["base_ns"][1]}
                        </span></b><br>
                        <small>To change it, select another option below
                        (go to <b>✏️ Custom</b> option to add more).</small>
                    </div>""", unsafe_allow_html=True)
                st.write("")
            with col1:
                col1a, col1b = st.columns([1,2])

            with col1a:
                mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
                list_to_choose = sorted(mapping_ns_dict.keys())
                list_to_choose.insert(0, "Select prefix")
                if st.session_state["base_ns"][0] in list_to_choose:
                    list_to_choose.remove(st.session_state["base_ns"][0])
                base_ns_prefix_candidate = st.selectbox("🖱️ Select new base namespace:",
                    list_to_choose, key="key_base_ns_prefix_candidate")

            with col1:
                if base_ns_prefix_candidate != "Select prefix":
                    base_ns_iri_candidate = mapping_ns_dict[base_ns_prefix_candidate]
                    st.button("Confirm", key="key_change_base_ns_button", on_click=change_base_ns)

                if base_ns_prefix_candidate == "Select prefix":
                    if st.session_state["base_ns"] != utils.get_default_base_ns():
                        with col1:
                            default_base_ns = utils.get_default_base_ns()
                            base_ns_prefix_candidate = default_base_ns[0]
                            base_ns_iri_candidate = default_base_ns[1]
                            st.button("Set to default", key="key_base_ns_set_to_default_button", on_click=change_base_ns)


        # UNBIND NS SUCCESS MESSAGE---------------------------------------------
        # Only shows here if no "Unbind Namespace" purple heading
        mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
        default_ns_dict = utils.get_default_ns_dict()
        required_ns_dict = utils.get_required_ns_dict()
        list_to_choose = [k for k in mapping_ns_dict if (k not in default_ns_dict and k not in required_ns_dict)]
        if st.session_state["base_ns"][0] in list_to_choose:
            list_to_choose.remove(st.session_state["base_ns"][0])

        if not list_to_choose:
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
                time.sleep(utils.get_success_message_time())
                st.rerun()

        # PURPLE HEADING: UNBIND NAMESPACE--------------------------------------
        # Only shows if there are bound namespaces
        if list_to_choose:
            with col1:
                st.write("______")
                st.markdown("""<div class="purple-heading">
                        🗑️ Unbind Existing Namespace
                    </div>""", unsafe_allow_html=True)
                st.markdown("")

            if st.session_state["ns_unbound_ok_flag"]:
                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    st.markdown(f"""<div class="success-message-flag">
                        ✅ The <b>Namespace/s</b> have been unbound!
                    </div>""", unsafe_allow_html=True)
                st.write("")
                st.session_state["ns_unbound_ok_flag"] = False
                time.sleep(utils.get_success_message_time())
                st.rerun()

            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
                default_ns_dict = utils.get_default_ns_dict()
                required_ns_dict = utils.get_required_ns_dict()
                list_to_choose = [k for k in mapping_ns_dict if (k not in default_ns_dict and k not in required_ns_dict)]
                list_to_choose = sorted(list_to_choose)
                if st.session_state["base_ns"][0] in list_to_choose:
                    list_to_choose.remove(st.session_state["base_ns"][0])
                if len(list_to_choose) > 1:
                    list_to_choose.insert(0, "Select all")
                ns_to_unbind_list = st.multiselect("🖱️ Select namespaces to unbind:*", list_to_choose, key="key_unbind_multiselect")


            if ns_to_unbind_list and "Select all" not in ns_to_unbind_list:

                with col1a:
                    unbind_ns_button_checkbox = st.checkbox(
                    "🔒 I am sure want to unbind the selected namespace/s",
                    key="key_unbind_all_ns_button_checkbox")
                    if unbind_ns_button_checkbox:
                        st.button(f"Unbind", key="key_unbind_ns_button", on_click=unbind_namespaces)

            elif ns_to_unbind_list:

                mapping_ns_dict_available_to_unbind = {k: v for k, v in mapping_ns_dict.items() if
                    (k not in default_ns_dict and k not in required_ns_dict) and k != st.session_state["base_ns"][0]}
                ns_to_unbind_list = list(mapping_ns_dict_available_to_unbind)

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
                        st.button("Unbind", key="key_unbind_all_ns_button", on_click=unbind_namespaces)

            if ns_to_unbind_list:
                with col1a:
                    utils.get_ns_previsualisation_message(ns_to_unbind_list, mapping_ns_dict)

#_______________________________________________________________________________
# PANEL: SAVE MAPPING
# Available only if mapping is loaded
with tab3:
    st.write("")
    st.write("")

    if not st.session_state["g_label"]:
        col1, col2 = st.columns([2,1.5])
        with col1:
            utils.get_missing_g_mapping_error_message()

    else:
        col1,col2 = st.columns([2,1.5])

        with col2:
            col2a,col2b = st.columns([1,2])

        # RIGHT COLUMN OPTION: SAVE PROGRESS------------------------------------
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
                            ⚠️ Any <b>previously cached information</b> will be deleted.
                        </div>""", unsafe_allow_html=True)


        if st.session_state["progress_saved_ok_flag"]:
            with col2b:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ Current state of mapping <b style="color:#F63366;">{st.session_state["g_label"]}</b> has been cached!
                </div>""", unsafe_allow_html=True)
            st.session_state["progress_saved_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()


        # PURPLE HEADING: EXPORT MAPPING----------------------------------------
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
            time.sleep(utils.get_success_message_time())
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

            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                reset_after_exporting_mapping_checkbox = st.checkbox("🔄 Start fresh: Reset session after exporting mapping",
                    key="key_reset_after_exporting_mapping_checkbox")

            serialised_data = st.session_state["g_mapping"].serialize(format=export_format)
            with col1a:
                st.session_state["mapping_downloaded_ok_flag"] = st.download_button(label="Export", data=serialised_data,
                    file_name=export_filename_complete, mime="text/plain")

        if st.session_state["mapping_downloaded_ok_flag"]:
            st.rerun()

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

        # PURPLE HEADING: SAVE SESSION------------------------------------------
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
            time.sleep(utils.get_success_message_time())
            st.rerun()

        if st.session_state["session_removed_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>session/s</b> have been deleted!
                </div>""", unsafe_allow_html=True)
            st.session_state["session_removed_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        with col1:
            col1a, col1b = st.columns([2,1])

        folder_name = "saved_sessions"
        folder_path = os.path.join(os.getcwd(), folder_name)
        if os.path.isdir(folder_path):
            file_list = [os.path.splitext(f)[0] for f in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, f)) and f.endswith(".pkl")]
        else:
            file_list = []

        if file_list:
            with col1b:
                save_session_selected_option = st.radio("🖱️ Select an option:*", ["💾 Save session", "🗑️ Delete sessions"],
                    label_visibility="hidden", key="key_save_session_options")
        else:
            save_session_selected_option = "💾 Save session"

        if save_session_selected_option == "💾 Save session":

            with col1a:
                pkl_filename = st.text_input("⌨️ Enter filename (without extension):*", key="key_pkl_filename")
            if pkl_filename:
                with col1b:
                    valid_pkl_filename_flag = utils.is_valid_filename(pkl_filename)

            pkl_filename_w_extension = pkl_filename + '.pkl'
            file_path = os.path.join(folder_path, pkl_filename_w_extension)

            if pkl_filename and os.path.isfile(file_path):
                with col1b:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ A session was already saved with <b>this filename</b>. <small>Pick
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

        elif save_session_selected_option == "🗑️ Delete sessions":

            with col1a:
                list_to_choose = sorted(file_list)
                if len(list_to_choose) > 1:
                    list_to_choose.insert(0, "Select all")
                sessions_to_remove_list = st.multiselect("🖱️ Select sessions to delete:*", list_to_choose,
                    key="key_sessions_to_remove_list")

                if sessions_to_remove_list:

                    if "Select all" in sessions_to_remove_list:
                        sessions_to_remove_list = file_list
                        delete_sessions_checkbox = st.checkbox("🔒 I am sure I want to delete all saved sessions",
                            key="key_delete_sessions_checkbox")
                    else:
                        delete_sessions_checkbox = st.checkbox("🔒 I am sure I want to delete the selected session/s",
                            key="key_delete_sessions_checkbox")

                    if delete_sessions_checkbox:
                        st.button("Delete", key="delete_sessions_button", on_click=delete_sessions)


#_______________________________________________________________________________
# PANEL: SET STYLE
with tab4:

    st.write("")
    st.write("")

    col1,col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])

    # PURPLE HEADING: STYLE CONFIGURATION---------------------------------------
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

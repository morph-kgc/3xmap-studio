import streamlit as st
import os #for file navigation
import rdflib
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle
from rdflib.namespace import split_uri
import re
import configparser
import io
import time
import uuid   # to handle uploader keys
import requests
from morph_kgc import materialize
from sqlalchemy import create_engine
from streamlit.runtime.uploaded_file_manager import UploadedFile
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

# Temporal folder to store intermediate files-----------------------------------
temp_folder_path = "materialisation_files_temp"

#define on_click functions--------------------------------------------
# TAB1
def autoconfig():
    # reset config dict
    st.session_state["mkgc_config"] = configparser.ConfigParser()
    # list to manage data source labels
    base_label = "DataSource"
    used_data_source_labels_list = []
    # autoconfig SQL data sources_____________________________________
    for ds in st.session_state["db_connections_dict"]:
        i = 1
        while f"{base_label}{i}" in used_data_source_labels_list:
            i += 1
        mkgc_ds_label = f"{base_label}{i}"
        used_data_source_labels_list.append(mkgc_ds_label)
        db_url = utils.get_db_url_str(ds)
        mkgc_mappings_str = str(os.path.join(temp_folder_path, st.session_state["g_label"] + ".ttl"))
        st.session_state["mkgc_config"][mkgc_ds_label] = {"db_url": db_url,
            "mappings": mkgc_mappings_str}
    # autoconfig TABULAR data sources___________________________________
    for ds_label in st.session_state["ds_files_dict"]:
        i = 1
        while f"{base_label}{i}" in used_data_source_labels_list:
            i += 1
        mkgc_ds_label = f"{base_label}{i}"
        used_data_source_labels_list.append(mkgc_ds_label)
        mkgc_tab_ds_file_path = os.path.join(temp_folder_path, ds_label)
        mkgc_mappings_str = str(os.path.join(temp_folder_path, st.session_state["g_label"] + ".ttl"))
        st.session_state["mkgc_config"][mkgc_ds_label] = {"file_path": mkgc_tab_ds_file_path,
            "mappings": mkgc_mappings_str}
    # store information_________________________
    st.session_state["autoconfig_active_flag"] = True
    st.session_state["autoconfig_generated_ok_flag"] = True

def reset_config_file_tab1():
    # reset variables__________________________
    st.session_state["mkgc_config"] = configparser.ConfigParser()
    st.session_state["mkgc_g_mappings_dict"] = {}
    st.session_state["materialised_g_mapping_file"] = None
    st.session_state["materialised_g_mapping"] = Graph()
    st.session_state["autoconfig_active_flag"] = False
    # store information_________________________
    st.session_state["config_file_reset_ok_flag_tab1"] = True

def reset_config_file_tab2():
    # reset variables__________________________
    st.session_state["mkgc_config"] = configparser.ConfigParser()
    st.session_state["mkgc_g_mappings_dict"] = {}
    st.session_state["materialised_g_mapping_file"] = None
    st.session_state["materialised_g_mapping"] = Graph()
    st.session_state["autoconfig_active_flag"] = False
    # store information_________________________
    st.session_state["config_file_reset_ok_flag_tab2"] = True

# TAB2
def enable_manual_config():
    # reset config dict
    st.session_state["mkgc_config"] = configparser.ConfigParser()
    # store information________________________
    st.session_state["autoconfig_active_flag"] = False
    st.session_state["manual_config_enabled_ok_flag"] = True

def save_sql_ds_for_mkgc():
    # add to config dict___________________
    st.session_state["mkgc_config"][mkgc_ds_label] = {"db_url": db_url,
        "mappings": mkgc_mappings_str_for_sql}
    # store information________________________
    st.session_state["ds_for_mkgcgc_saved_ok_flag"] = True
    # reset fields__________________________
    st.session_state["key_mkgc_ds_label"] = ""

def save_tab_ds_for_mkgc():
    # add to config dict___________________
    st.session_state["mkgc_config"][mkgc_ds_label] = {"file_path": mkgc_tab_ds_file_path,
        "mappings": mkgc_mappings_str_for_tab}
    # store information________________________
    st.session_state["ds_for_mkgcgc_saved_ok_flag"] = True
    # reset fields__________________________
    st.session_state["key_mkgc_ds_label"] = ""

def remove_ds_for_mkgc():
    # remove from config dict___________________
    for ds in ds_for_mkgcgc_to_remove_list:
        del st.session_state["mkgc_config"][ds]
    # store information________________________
    st.session_state["ds_for_mkgcgc_removed_ok_flag"] = True
    # reset fields__________________________
    if st.session_state["db_connections_dict"]:
        st.session_state["key_mkgc_ds_type"] = "📊 SQL Database"
    else:
        st.session_state["key_mkgc_ds_type"] = "🛢️ Tabular data"

def save_options_for_mkgc():
    #create section_______________
    if not st.session_state["mkgc_config"].has_section("CONFIGURATION"):
        st.session_state["mkgc_config"].add_section("CONFIGURATION")
    # add to config dict___________________
    if output_file:
        st.session_state["mkgc_config"]["CONFIGURATION"]["output_file"] = output_file
    else:
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "output_file"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "output_file")
    if output_format != "Select option":
        st.session_state["mkgc_config"]["CONFIGURATION"]["output_format"] = output_format
    else:
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "output_format"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "output_format")
    if log_level != "Select option":
        st.session_state["mkgc_config"]["CONFIGURATION"]["log_level"] = log_level
    else:
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "log_level"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "log_level")
    if mapping_partitioning != "Select option":
        st.session_state["mkgc_config"]["CONFIGURATION"]["mapping_partitioning"] = mapping_partitioning
    else:
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "mapping_partitioning"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "mapping_partitioning")
    if na_values:
        st.session_state["mkgc_config"]["CONFIGURATION"]["na_values"] = na_values
    else:
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "na_values"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "na_values")
    if only_printable_chars != "Select option":
        st.session_state["mkgc_config"]["CONFIGURATION"]["only_printable_chars"] = only_printable_chars
    else:
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "only_printable_chars"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "only_printable_chars")
    if literal_escaping_chars:
        st.session_state["mkgc_config"]["CONFIGURATION"]["literal_escaping_chars"] = literal_escaping_chars
    else:
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "literal_escaping_chars"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "literal_escaping_chars")
    if infer_sql_datatypes != "Select option":
        st.session_state["mkgc_config"]["CONFIGURATION"]["infer_sql_datatypes"] = infer_sql_datatypes
    else:
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "infer_sql_datatypes"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "infer_sql_datatypes")
    if number_of_processes:
        st.session_state["mkgc_config"]["CONFIGURATION"]["number_of_processes"] = number_of_processes
    else:
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "number_of_processes"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "number_of_processes")
    if output_kafka_server:
        st.session_state["mkgc_config"]["CONFIGURATION"]["output_kafka_server"] = output_kafka_server
    else:
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "output_kafka_server"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "output_kafka_server")
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "output_kafka_topic"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "output_kafka_topic")
    if output_kafka_server:
        if output_kafka_topic:
            st.session_state["mkgc_config"]["CONFIGURATION"]["output_kafka_topic"] = output_kafka_topic
        else:
            if st.session_state["mkgc_config"].has_option("CONFIGURATION", "output_kafka_topic"):
                st.session_state["mkgc_config"].remove_option("CONFIGURATION", "output_kafka_topic")
    # store information________________________
    st.session_state["configuration_for_mkgcgc_saved_ok_flag"] = True
    # reset fields__________________________
    st.session_state["key_configure_options_for_mkgc"] = "🔒 Keep options"

def remove_options_for_mkgc():
    # remove from config dict___________________
    del st.session_state["mkgc_config"]["CONFIGURATION"]
    # store information________________________
    st.session_state["configuration_for_mkgcgc_removed_ok_flag"] = True
    # reset fields__________________________
    st.session_state["key_configure_options_for_mkgc"] = "🚫 No options"

def save_mapping_for_mkgc():
    # store information________________________
    st.session_state["mkgc_g_mappings_dict"][additional_mapping_label] = uploaded_mapping
    st.session_state["additional_mapping_added_ok_flag"] = True
    # reset fields_______________________________
    st.session_state["key_additional_mapping_label"] = ""
    st.session_state["key_mapping_uploader"] = str(uuid.uuid4())

def save_mapping_for_mkgcgc_from_url():
    # store information________________________
    st.session_state["mkgc_g_mappings_dict"][additional_mapping_label] = mapping_url
    st.session_state["additional_mapping_added_ok_flag"] = True
    # reset fields_______________________________
    st.session_state["key_additional_mapping_label"] = ""

def remove_additional_mapping_for_mkgc():
    # remove________________________
    for mapping in mappings_to_remove_list:
        del st.session_state["mkgc_g_mappings_dict"][mapping]
    # store information________________________
    st.session_state["additional_mapping_removed_ok_flag"] = True
    # reset fields_______________________________
    st.session_state["key_mappings_to_remove_list"] = []

# TAB3
def materialise_graph():
    # empty folder if it exists or create if it does not______________
    if os.path.exists(temp_folder_path):
        for filename in os.listdir(temp_folder_path):
            file_path = os.path.join(temp_folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # delete file or link
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # delete subfolder
            except Exception as e:
                st.write(f"⚠️ Failed to delete {file_path}: {e}")
    else:
        os.makedirs(temp_folder_path)  # Create folder if it doesn't exist

    # download g_mapping if used___________________________________________
    if st.session_state["g_label"] in mkgc_used_mapping_list:
        # Download g_mapping to file
        mapping_content = st.session_state["g_mapping"]
        mapping_content_str = mapping_content.serialize(format="turtle")
        filename = st.session_state["g_label"] + ".ttl"

        file_path = os.path.join(temp_folder_path, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(mapping_content_str)

    # download additional mappings to file if used (only for files, not URL mappings)________________
    for g_label in mkgc_used_mapping_list:
        if g_label != st.session_state["g_label"]:
            g_mapping_file = st.session_state["mkgc_g_mappings_dict"][g_label]
            if isinstance(g_mapping_file, UploadedFile):
                ext = os.path.splitext(g_mapping_file.name)[1]
                filename = g_label + ext
                file_path = os.path.join(temp_folder_path, filename)
                with open(file_path, "wb") as f:
                    f.write(g_mapping_file.getvalue())  # write file content as bytes

    # download used tabular data sources___________________________________
    for ds_filename in mkgc_used_tab_ds_list:
        ds_file = st.session_state["ds_files_dict"][ds_filename]

        if hasattr(ds_file, "getvalue"):  # large files (elephant upload) - BytesIO or similar
            file_bytes = ds_file.getvalue()
        elif hasattr(ds_file, "read"):  # uploaded file object
            ds_file.seek(0)
            file_bytes = ds_file.read()

        file_path = os.path.join(temp_folder_path, ds_filename)  # write to temp folder
        with open(file_path, "wb") as f:
            f.write(file_bytes)



    # write config to a file____________________________________________________
    config_path = os.path.join(os.getcwd(), "materialising_mapping_temp", "mkgc_config.ini")
    with open(config_path, "w", encoding="utf-8") as f:
        st.session_state["mkgc_config"].write(f)

    # run Morph-KGC with the config file path to materialise_______________________
    try:
        st.session_state["materialised_g_mapping"] = materialize(config_path)
        st.session_state["materialised_g_mapping_file"] = io.BytesIO()
        st.session_state["materialised_g_mapping"].serialize(destination=st.session_state["materialised_g_mapping_file"], format="turtle")  # or "xml", "nt", "json-ld"
        st.session_state["materialised_g_mapping_file"].seek(0)  # rewind to the beginning
        # delete temporal folder___________________________________________________
        for filename in os.listdir(temp_folder_path):       # delete all files inside the folder
            file_path = os.path.join(temp_folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        os.rmdir(temp_folder_path)      # remove the empty folder

        # store information________________________________________________________
        st.session_state["graph_materialised_ok_flag"] = True

    except Exception as e:
        st.session_state["graph_materialised_ok_flag"] = ["error", e]
        # delete temporal folder___________________________________________________
        for filename in os.listdir(temp_folder_path):       # delete all files inside the folder
            file_path = os.path.join(temp_folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        os.rmdir(temp_folder_path)      # remove the empty folder
#____________________________________________________________
# PANELS OF THE PAGE (tabs)

tab1, tab2, tab3 = st.tabs(["AutoConfig", "Manual Config", "Materialise"])

#________________________________________________
# AUTOMATIC CONFIGURATION
with tab1:

    col1, col2 = st.columns([2,1.5])

    with col1:
        col1a, col1b = st.columns([2,1])

    with col2:
        col2a, col2b = st.columns([0.5, 2])

    # Show config content
    with col2b:
        config_string = io.StringIO()
        st.session_state["mkgc_config"].write(config_string)
        if config_string.getvalue() != "":
            st.markdown(f"```ini\n{config_string.getvalue()}\n```")
            st.markdown(f"""<div class="info-message-gray">
                ⏳ When ready, go to the <b>Materialise</b> pannel.
            </div>""", unsafe_allow_html=True)

            st.write("")
            reset_config_file_checkbox = st.checkbox("🔄 Reset Config file",
                key="key_reset_config_file_tab_1_checkbox")

            if reset_config_file_checkbox:
                st.button("Reset", key="key_reset_config_file_tab1_button", on_click=reset_config_file_tab1)
                st.markdown(f"""<div class="warning-message">
                    ⚠️ If you continue, the <b>Config file will be cleared</b>
                    and any configuration will be lost.
                    <small>Make sure you want to go ahead.</small>
                </div>""", unsafe_allow_html=True)

    if st.session_state["config_file_reset_ok_flag_tab1"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>Config file</b> has been reset!
            </div>""", unsafe_allow_html=True)
        st.session_state["config_file_reset_ok_flag_tab1"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()


    # PURPLE HEADING - AUTOMATIC CONFIGURATION
    with col1:
        st.markdown("""<div class="purple-heading">
                🤖 Automatic Configuration
            </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([2,1])

    if st.session_state["autoconfig_generated_ok_flag"]:
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>Config file</b> has been auto-generated!
            </div>""", unsafe_allow_html=True)
        st.session_state["autoconfig_generated_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()


    if not st.session_state["db_connections_dict"] and not st.session_state["ds_files_dict"]:
        with col1a:
            st.markdown(f"""<div class="error-message">
                ❌ There are <b>no data sources</b> available.
                <small>You can add them in the <b>📊 SQL Databases</b>
                and the <b>🛢️ Tabular data</b> pages.</small>
            </div>""", unsafe_allow_html=True)

    else:
        if st.session_state["autoconfig_active_flag"]:
            with col1a:
                st.button("Update auto-config", key="key_update_autoconfig_button", on_click=autoconfig)

        else:

            if config_string.getvalue() != "":
                with col1b:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ A manual <b>Config file</b> is already being created.
                        <small>If you continue, it will be <b>overwritten</b> with an auto-generated version.</small>
                    </div>""", unsafe_allow_html=True)
                with col1a:
                    autoconfig_checkbox = st.checkbox(
                    "🔒 I am sure I want to overwrite the current Config file",
                    key="key_autooconfig_checkbox")
                    if autoconfig_checkbox:
                        st.button("AutoConfig", key="key_autoconfig_button", on_click=autoconfig)
            else:
                with col1a:
                    st.button("AutoConfig", key="key_autoconfig_button", on_click=autoconfig)


#________________________________________________
# MANUAL CONFIGURATION
with tab2:

    col1, col2 = st.columns([2,1.5])

    with col1:
        col1a, col1b = st.columns([2,1])

    with col2:
        col2a, col2b = st.columns([0.5, 2])

    # Show config content
    with col2b:
        config_string = io.StringIO()
        st.session_state["mkgc_config"].write(config_string)
        if config_string.getvalue() != "":
            st.markdown(f"```ini\n{config_string.getvalue()}\n```")
            st.markdown(f"""<div class="info-message-gray">
                ⏳ When ready, go to the <b>Materialise</b> pannel.
            </div>""", unsafe_allow_html=True)

            st.write("")
            reset_config_file_checkbox = st.checkbox("🔄 Reset Config file",
                key="key_reset_config_file_tab_2_checkbox")

            if reset_config_file_checkbox:
                st.button("Reset", key="key_reset_config_file_tab2_button", on_click=reset_config_file_tab2)
                st.markdown(f"""<div class="warning-message">
                    ⚠️ If you continue, the <b>Config file will be cleared</b>
                    and any configuration will be lost.
                    <small>Make sure you want to go ahead.</small>
                </div>""", unsafe_allow_html=True)


    if st.session_state["manual_config_enabled_ok_flag"]:
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ <b>Manual configuration</b> has been enabled!
            </div>""", unsafe_allow_html=True)
        st.session_state["manual_config_enabled_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    if st.session_state["config_file_reset_ok_flag_tab2"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>Config file</b> has been reset!
            </div>""", unsafe_allow_html=True)
        st.session_state["config_file_reset_ok_flag_tab2"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    # PURPLE HEADING - ENABLE MANUAL CONFIG
    if st.session_state["autoconfig_active_flag"]:
        with col1:
            st.markdown("""<div class="purple-heading">
                    ✏️ Manual Configuration
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a, col1b = st.columns(2)
        with col1b:
            st.markdown(f"""<div class="info-message-blue">
                ✏️ <b>Enable</b> to start manual editition of the <b>Config file</b> <small>(from scratch)</small>.
            </div>""", unsafe_allow_html=True)
        with col1a:
            st.button("Enable", key="key_enable_manual_config_button", on_click=enable_manual_config)


    else:

        # PURPLE HEADING - ADD DATA SOURCE
        with col1:
            st.markdown("""<div class="purple-heading">
                    📊 Configure Data Source
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a, col1b = st.columns([1.5,1])

        if st.session_state["ds_for_mkgcgc_saved_ok_flag"]:
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>data source</b> has been saved!
                </div>""", unsafe_allow_html=True)
            st.session_state["ds_for_mkgcgc_saved_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        if st.session_state["ds_for_mkgcgc_removed_ok_flag"]:
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>data source</b> has been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["ds_for_mkgcgc_removed_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()


        if not st.session_state["db_connections_dict"] and not st.session_state["ds_files_dict"]:
            with col1a:
                st.markdown(f"""<div class="error-message">
                    ❌ There are <b>no data sources</b> available.
                    <small>You can add them in the <b>📊 SQL Databases</b>
                    and the <b>🛢️ Tabular data</b> pages.</small>
                </div>""", unsafe_allow_html=True)
            mkgc_ds_type = ""

        else:
            if not st.session_state["ds_files_dict"]:
                list_to_choose = ["📊 SQL Database"]
            elif not st.session_state["db_connections_dict"]:
                list_to_choose = ["🛢️ Tabular data"]
            else:
                list_to_choose = ["📊 SQL Database", "🛢️ Tabular data"]
            if list(st.session_state["mkgc_config"].keys()) != ["DEFAULT"] and list(st.session_state["mkgc_config"].keys()) != ["DEFAULT", "CONFIGURATION"]:
                list_to_choose.append("🗑️ Remove")
            with col1b:
                st.write("")
                mkgc_ds_type = st.radio("🖱️ Select an option:*", list_to_choose,
                    label_visibility="collapsed", key="key_mkgc_ds_type")

            if mkgc_ds_type != "🗑️ Remove":

                with col1a:
                    mkgc_ds_label = st.text_input("⌨️ Enter data source label:*", key="key_mkgc_ds_label")

                if mkgc_ds_label:
                    excluded_characters = r"[ \t\n\r<>\"{}|\\^`\[\]%']"
                    if mkgc_ds_label in st.session_state["mkgc_config"]:
                        with col1a:
                            st.markdown(f"""<div class="error-message">
                                ❌ Label is <b>already in use</b>.
                                <small> You must either delete the already existing data source or pick a different label.</small>
                            </div>""", unsafe_allow_html=True)
                    elif re.search(excluded_characters, mkgc_ds_label):
                        with col1a:
                            st.markdown(f"""<div class="error-message">
                                ❌ <b>Forbidden character</b> in data source label.
                                <small> Please, pick a valid label.</small>
                            </div>""", unsafe_allow_html=True)
                    elif mkgc_ds_label.lower() == "CONFIGURATION":
                        with col1a:
                            st.markdown(f"""<div class="error-message">
                                ❌ <b>"CONFIGURATION" label</b> is not allowed.
                                <small> You must pick a different label.</small>
                            </div>""", unsafe_allow_html=True)

                    else:

                        if mkgc_ds_type == "📊 SQL Database":

                            with col1:
                                col1a, col1b = st.columns(2)
                            with col1a:
                                list_to_choose = list(reversed(st.session_state["db_connections_dict"]))
                                list_to_choose.insert(0, "Select data source")
                                mkgc_sql_ds = st.selectbox("🖱️ Select data source:*", list_to_choose,
                                    key="key_mkgc_sql_ds")

                                if mkgc_sql_ds != "Select data source":
                                    db_url = utils.get_db_url_str(mkgc_sql_ds)
                                    db_user = st.session_state["db_connections_dict"][mkgc_sql_ds][4]
                                    db_password = st.session_state["db_connections_dict"][mkgc_sql_ds][5]
                                    db_type = st.session_state["db_connections_dict"][mkgc_sql_ds][0]

                            with col1b:
                                mkgc_g_mapping_dict_complete = st.session_state["mkgc_g_mappings_dict"].copy()
                                if st.session_state["g_label"]:
                                    mkgc_g_mapping_dict_complete[st.session_state["g_label"]] = st.session_state["g_mapping"]

                                list_to_choose = list(reversed(list(mkgc_g_mapping_dict_complete)))
                                if len(list_to_choose) > 1:
                                    list_to_choose.insert(0, "Select all")

                                if st.session_state["g_label"]:
                                    mkgc_mappings_list_for_sql = st.multiselect("🖱️ Select mappings:*", list_to_choose,
                                        default=[st.session_state["g_label"]], key="key_mkgc_mappings")
                                else:
                                    mkgc_mappings_list_for_sql = st.multiselect("🖱️ Select mappings:*", list_to_choose,
                                        key="key_mkgc_mappings")

                                if not mkgc_g_mapping_dict_complete:
                                    with col1:
                                        st.markdown(f"""<div class="error-message">
                                            ❌ <b> No mappings available. </b>
                                            <small>You can <b>build a mapping</b> using this application
                                            and/or load additional mappings in the <b>Additional Mappings</b> section
                                            of this pannel.</small>
                                        </div>""", unsafe_allow_html=True)

                            if "Select all" in mkgc_mappings_list_for_sql:
                                mkgc_mappings_list_for_sql = list(reversed(list(mkgc_g_mapping_dict_complete)))

                            mkgc_mappings_paths_list_for_sql = []
                            for mapping_label in mkgc_mappings_list_for_sql:
                                if mapping_label == st.session_state["g_label"]:
                                    mkgc_mappings_paths_list_for_sql.append(os.path.join(temp_folder_path, mapping_label + ".ttl"))
                                elif isinstance(st.session_state["mkgc_g_mappings_dict"][mapping_label], UploadedFile):
                                    mkgc_mappings_paths_list_for_sql.append(os.path.join(temp_folder_path, mapping_label + ".ttl"))
                                else:
                                    mkgc_mappings_paths_list_for_sql.append(st.session_state["mkgc_g_mappings_dict"][mapping_label])
                            mkgc_mappings_str_for_sql = ",".join(mkgc_mappings_paths_list_for_sql)   # join into a comma-separated string for the config

                            # with col1:
                            #     col1a, col1b = st.columns(2)
                            # with col1a:
                            #     schema = st.text_input("⌨️ Enter schema (optional):")
                            # with col1b:
                            #     driver_class = st.text_input("⌨️ Enter driver class (optional):")

                            if mkgc_sql_ds != "Select data source" and mkgc_mappings_list_for_sql:
                                with col1a:
                                    st.button("Save", key="save_sql_ds_for_mkgcgc_button", on_click=save_sql_ds_for_mkgc)

                        if mkgc_ds_type == "🛢️ Tabular data":

                            with col1:
                                col1a, col1b = st.columns(2)
                            with col1a:
                                list_to_choose = list(reversed(st.session_state["ds_files_dict"]))
                                list_to_choose.insert(0, "Select data source")
                                mkgc_tab_ds_file = st.selectbox("🖱️ Select data source:*", list_to_choose,
                                    key="key_mkgc_tab_ds_file")

                                if mkgc_tab_ds_file != "Select data source":
                                    mkgc_tab_ds_file_path = os.path.join(temp_folder_path, mkgc_tab_ds_file)

                            with col1b:
                                mkgc_g_mapping_dict_complete = st.session_state["mkgc_g_mappings_dict"].copy()
                                if st.session_state["g_label"]:
                                    mkgc_g_mapping_dict_complete[st.session_state["g_label"]] = st.session_state["g_mapping"]

                                list_to_choose = list(reversed(list(mkgc_g_mapping_dict_complete)))
                                if len(list_to_choose) > 1:
                                    list_to_choose.insert(0, "Select all")

                                if st.session_state["g_label"]:
                                    mkgc_mappings_list_for_tab = st.multiselect("🖱️ Select mappings:*", list_to_choose,
                                        default=[st.session_state["g_label"]], key="key_mkgc_mappings")
                                else:
                                    mkgc_mappings_list_for_tab = st.multiselect("🖱️ Select mappings:*", list_to_choose,
                                        key="key_mkgc_mappings")

                                if not mkgc_g_mapping_dict_complete:
                                    with col1:
                                        st.markdown(f"""<div class="error-message">
                                            ❌ <b> No mappings available. </b>
                                            <small>You can <b>build a mapping</b> using this application
                                            and/or load additional mappings in the <b>Additional Mappings</b> section
                                            of this pannel.</small>
                                        </div>""", unsafe_allow_html=True)

                            mkgc_mappings_paths_list_for_tab = []
                            for mapping_label in mkgc_mappings_list_for_tab:
                                if mapping_label == st.session_state["g_label"]:
                                    mkgc_mappings_paths_list_for_tab.append(os.path.join(temp_folder_path, mapping_label + ".ttl"))
                                elif isinstance(st.session_state["mkgc_g_mappings_dict"][mapping_label], UploadedFile):
                                    mkgc_mappings_paths_list_for_tab.append(os.path.join(temp_folder_path, mapping_label + ".ttl"))
                                else:
                                    mkgc_mappings_paths_list_for_tab.append(st.session_state["mkgc_g_mappings_dict"][mapping_label])
                            mkgc_mappings_str_for_tab = ",".join(mkgc_mappings_paths_list_for_tab)   # join into a comma-separated string for the config

                            if mkgc_tab_ds_file != "Select data source" and mkgc_mappings_list_for_tab:
                                with col1a:
                                    st.button("Save", key="save_tab_ds_for_mkgcgc_button", on_click=save_tab_ds_for_mkgc)

                if list(st.session_state["mkgc_config"].keys()) == ["DEFAULT"] or list(st.session_state["mkgc_config"].keys()) == ["DEFAULT", "CONFIGURATION"]:
                    if st.session_state["ds_for_mkgcgc_removed_ok_flag"]:
                        with col1a:
                            st.write("")
                            st.markdown(f"""<div class="success-message-flag">
                                ✅ The <b>data source/s</b> have been removed!
                            </div>""", unsafe_allow_html=True)
                        st.session_state["ds_for_mkgcgc_removed_ok_flag"] = False
                        time.sleep(utils.get_success_message_time())
                        st.rerun()

            if mkgc_ds_type == "🗑️ Remove":

                with col1a:
                    list_to_choose = list(reversed(list(st.session_state["mkgc_config"])))
                    list_to_choose.remove("DEFAULT")
                    if "CONFIGURATION" in list_to_choose:
                        list_to_choose.remove("CONFIGURATION")
                    if len(list_to_choose) > 1:
                        list_to_choose.insert(0, "Select all")

                    ds_for_mkgcgc_to_remove_list = st.multiselect("🖱️ Select data sources:*", list_to_choose,
                        key="key_ds_for_mkgcgc_to_remove_list")

                    if "Select all" in ds_for_mkgcgc_to_remove_list:
                        ds_for_mkgcgc_to_remove_list = list(reversed(list(st.session_state["mkgc_config"])))
                        ds_for_mkgcgc_to_remove_list.remove("DEFAULT")
                        if "CONFIGURATION" in ds_for_mkgcgc_to_remove_list:
                            ds_for_mkgcgc_to_remove_list.remove("CONFIGURATION")
                        with col1b:
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ You are deleting <b>all Data Sources</b>.
                                <small>Make sure you want to go ahead.</small>
                            </div>""", unsafe_allow_html=True)
                        with col1a:
                            remove_all_ds_checkbox = st.checkbox(
                            "🔒 I am sure I want to remove all Data Sources",
                            key="key_remove_all_ds_checkbox")
                            if remove_all_ds_checkbox:
                                st.button("Remove", key="remove_ds_for_mkgcgc_button", on_click=remove_ds_for_mkgc)

                    elif ds_for_mkgcgc_to_remove_list:
                        with col1a:
                            remove_ds_checkbox = st.checkbox(
                            "🔒 I am sure I want to remove the selected Data Source/s",
                            key="key_remove_ds_checkbox")
                            if remove_ds_checkbox:
                                st.button("Remove", key="remove_ds_for_mkgcgc_button", on_click=remove_ds_for_mkgc)



        # PURPLE HEADING - ADD OPTIONS
        with col1:
            st.write("_______")
            st.markdown("""<div class="purple-heading">
                    ⚙️ Configure Options
                </div>""", unsafe_allow_html=True)

        with col1:
            col1a, col1b = st.columns(2)

        if st.session_state["configuration_for_mkgcgc_saved_ok_flag"]:
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>configuration</b> has been saved!
                </div>""", unsafe_allow_html=True)
            st.session_state["configuration_for_mkgcgc_saved_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        if st.session_state["configuration_for_mkgcgc_removed_ok_flag"]:
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>configuration</b> has been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["configuration_for_mkgcgc_removed_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()


        with col1:
            if st.session_state["mkgc_config"].has_section("CONFIGURATION"):
                configure_options_for_mkgc = st.radio("🖱️ Select an option:*",
                    ["🔒 Keep options", "✏️ Modify options", "🗑️ Remove options"],
                    horizontal=True, label_visibility="collapsed",
                    key="key_configure_options_for_mkgc")
            else:
                configure_options_for_mkgc = st.radio("🖱️ Select an option:*",
                    ["🚫 No options", "✏️ Add options"],
                    horizontal=True, label_visibility="collapsed",
                    key="key_configure_options_for_mkgc")

        if configure_options_for_mkgc in ["✏️ Modify options", "✏️ Add options"]:

            options_for_mkgcgc_ok_flag = True

            with col1:
                col1a, col1b = st.columns(2)

            with col1a:
                default_output_file = st.session_state["mkgc_config"].get("CONFIGURATION", "output_filename", fallback="")
                default_output_filename = os.path.basename(default_output_file)
                output_filename = st.text_input("⌨️ Enter output filename (optional):", value=default_output_filename,
                    key="key_output_filename")

                if output_filename:
                    excluded_characters = r"[\\/:*?\"<>| ]"
                    windows_reserved_names = ["CON", "PRN", "AUX", "NUL",
                        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
                        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]
                    if re.search(excluded_characters, output_filename):
                        st.markdown(f"""<div class="error-message">
                            ❌ <b>Forbidden character</b> in filename.
                            <small> Please, pick a valid filename.</small>
                        </div>""", unsafe_allow_html=True)
                        options_for_mkgcgc_ok_flag = False
                    elif output_filename.endswith("."):
                        st.markdown(f"""<div class="error-message">
                            ❌ <b>Trailing "."</b> in filename.
                            <small> Please, remove it.</small>
                        </div>""", unsafe_allow_html=True)
                        options_for_mkgcgc_ok_flag = False
                    else:
                        for item in windows_reserved_names:
                            if item == os.path.splitext(output_filename)[0].upper():
                                st.markdown(f"""<div class="error-message">
                                    ❌ <b>Reserved filename.</b><br>
                                    <small>Please, pick a different filename.</small>
                                </div>""", unsafe_allow_html=True)
                                options_for_mkgcgc_ok_flag = False
                                break  # Stop checking after first match
                        if options_for_mkgcgc_ok_flag:
                            if not os.path.splitext(output_filename)[1]:
                                st.markdown(f"""<div class="warning-message">
                                    ⚠️ <b>No extension</b> in filename.
                                    <small> Using an extension is recommended. Make sure it matches the file format (if given).</small>
                                </div>""", unsafe_allow_html=True)

                output_file = os.path.join(temp_folder_path, output_filename) if output_filename else ""

            with col1b:
                default_output_format = st.session_state["mkgc_config"].get("CONFIGURATION", "output_format", fallback="Select option")
                list_to_choose = ["N-TRIPLES", "N-QUADS"]
                list_to_choose.insert(0, "Select option")
                output_format = st.selectbox("🖱️ Select format (optional):", list_to_choose,
                    index=list_to_choose.index(default_output_format), key="key_output_format")

            with col1:
                col1a, col1b = st.columns(2)
            with col1a:
                default_log_level = st.session_state["mkgc_config"].get("CONFIGURATION", "log_level", fallback="Select option")
                list_to_choose = ["INFO", "DEBUG","WARNING", "ERROR", "CRITICAL", "NOTSET"]
                list_to_choose.insert(0, "Select option")
                log_level = st.selectbox("🖱️ Select log level (optional):", list_to_choose,
                    index=list_to_choose.index(default_log_level), key="key_log_level")

            with col1b:
                default_mapping_partitioning = st.session_state["mkgc_config"].get("CONFIGURATION", "mapping_partitioning", fallback="Select option")
                list_to_choose = ["MAXIMAL", "PARTIAL-AGGREGATIONS", "off"]
                list_to_choose.insert(0, "Select option")
                mapping_partitioning = st.selectbox("🖱️ Select mapping partitioning (optional):", list_to_choose,
                    index=list_to_choose.index(default_mapping_partitioning), key="key_mapping_partitioning")

            with col1:
                col1a, col1b = st.columns(2)
            with col1a:
                default_na_values = st.session_state["mkgc_config"].get("CONFIGURATION", "na_values", fallback="")
                default_na_values_list = default_na_values.split(",") if default_na_values else []
                list_to_choose = ["null", "NULL", "nan", "NaN", "NA", "N/A", "#N/A", "missing", '""',
                    "-", ".", "none", "None", "undefined", "#VALUE!", "#REF!", "#DIV/0!"]
                na_values_list = st.multiselect("🖱️ Select na values (optional)", list_to_choose,
                    default=default_na_values_list, key="key_na_values")
                na_values = ",".join(na_values_list)

            with col1b:
                default_only_printable_chars = st.session_state["mkgc_config"].get("CONFIGURATION", "only_printable_chars", fallback="Select option")
                list_to_choose = ["Select option", "Yes", "No"]
                only_printable_chars = st.selectbox("🖱️ Only printable charts (optional):", list_to_choose,
                    index=list_to_choose.index(default_only_printable_chars), key="key_only_printable_chars")

            with col1:
                col1a, col1b = st.columns(2)
            with col1a:
                default_literal_escaping_chars = st.session_state["mkgc_config"].get("CONFIGURATION", "literal_escaping_chars", fallback="")
                default_literal_escaping_chars_list = list(default_literal_escaping_chars) if default_literal_escaping_chars else []
                list_to_choose = ["Select all", "!", "#", "$", "&", "'", "(", ")", "*", "+", ",", "/", ":", ";", "=", "?", "@", "[", "]"]
                literal_escaping_chars_list = st.multiselect("🖱️ Select safe percent encodings (optional)", list_to_choose,
                    default=default_literal_escaping_chars_list, key="key_literal_escaping_chars")
                if "Select all" in literal_escaping_chars_list:
                    literal_escaping_chars_list = ["!", "#", "$", "&", "'", "(", ")", "*", "+", ",", "/", ":", ";", "=", "?", "@", "[", "]"]
                literal_escaping_chars = "".join(literal_escaping_chars_list)

            with col1b:
                default_infer_sql_datatypes = st.session_state["mkgc_config"].get("CONFIGURATION", "infer_sql_datatypes ", fallback="Select option")
                list_to_choose = ["Select option", "Yes", "No"]
                list_to_choose = ["Select option", "Yes", "No"]
                infer_sql_datatypes = st.selectbox("🖱️ Infer sql datatypes (optional):", list_to_choose,
                    index=list_to_choose.index(default_infer_sql_datatypes), key="key_infer_sql_datatypes")

            with col1:
                col1a, col1b = st.columns(2)

            with col1a:
                default_number_of_processes = st.session_state["mkgc_config"].get("CONFIGURATION", "number_of_processes", fallback="")
                number_of_processes = st.text_input("⌨️ Enter number of processes (optional):",
                    value = default_number_of_processes, key="key_number_of_processes")
                if number_of_processes:
                    try:
                        number_of_processes_check = int(number_of_processes)
                        if number_of_processes_check < 0:
                            st.markdown(f"""<div class="error-message">
                                ❌ Input must be a <b>positive integer</b>.
                            </div>""", unsafe_allow_html=True)
                            number_of_processes = ""
                    except:
                        st.markdown(f"""<div class="error-message">
                            ❌ Input must be an <b>integer</b>.
                        </div>""", unsafe_allow_html=True)
                        number_of_processes = ""

            with col1b:
                default_output_kafka_server = st.session_state["mkgc_config"].get("CONFIGURATION", "output_kafka_server", fallback="")
                output_kafka_server = st.text_input("⌨️ Output Kafka server (optional):",
                    value=default_output_kafka_server, key="key_default_output_kafka_server")

            with col1:
                col1a, col1b = st.columns(2)

            if output_kafka_server:
                with col1b:
                    default_output_kafka_topic = st.session_state["mkgc_config"].get("CONFIGURATION", "output_kafka_topic", fallback="")
                    output_kafka_topic = st.text_input("⌨️ Output Kafka topic (optional):",
                        value=default_output_kafka_topic, key="key_optput_kafka_topic")
                    if not output_kafka_topic:
                        st.markdown(f"""<div class="error-message">
                            ❌ An <b>output Kafka topic</b> must be selected if
                            a <b>output Kafka server</b> is entered.
                        </div>""", unsafe_allow_html=True)
                        options_for_mkgcgc_ok_flag = False
                    else:
                        kafka_topic_forbidden_chars = " /\\:;\"'<>[]{}|^`~?*&%#@=+,\t\n\r"
                        pattern = "[" + re.escape(kafka_topic_forbidden_chars) + "]"
                        if re.search(pattern, output_kafka_topic):
                            st.markdown(f"""<div class="error-message">
                                ❌ <b>Forbidden character</b> in output Kafka topic.
                                <small> Please, pick a valid topic.</small>
                            </div>""", unsafe_allow_html=True)
                            options_for_mkgcgc_ok_flag = False

            if output_kafka_server and output_kafka_topic:
                with col1b:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ <b>No validation provided</b>.
                        <small> Please check connectivity and provide a valid topic.</small>
                    </div>""", unsafe_allow_html=True)

            if options_for_mkgcgc_ok_flag:
                with col1a:
                    st.button("Save", key="key_save_options_for_mkgcgc_button", on_click=save_options_for_mkgc)

        if configure_options_for_mkgc == "🗑️ Remove options":
            with col1:
                remove_options_for_mkgcgc_checkbox = st.checkbox(
                ":gray-badge[⚠️ I am sure I want to remove the Options]",
                key="key_remove_options_for_mkgcgc_checkbox")
                if remove_options_for_mkgcgc_checkbox:
                    st.button("Remove", on_click=remove_options_for_mkgc)


        # PURPLE HEADING - ADDITIONAL MAPPINGS
        with col1:
            st.write("_______")
            st.markdown("""<div class="purple-heading">
                    ➕ Additional Mappings
                </div>""", unsafe_allow_html=True)

        with col1:
            st.write("")
            col1a, col1b = st.columns([1.5,1])

        if st.session_state["additional_mapping_added_ok_flag"]:
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>additional mapping</b> has been included!
                </div>""", unsafe_allow_html=True)
            st.session_state["additional_mapping_added_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        if st.session_state["additional_mapping_removed_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>additional mapping/s</b> have been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["additional_mapping_removed_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        # List of all used mappings (only allow to remvoe mapping if not used)
        mkgc_used_mapping_list = []
        mkgc_not_used_mapping_list = []
        for section in st.session_state["mkgc_config"].sections():
            if section != "CONFIGURATION" and section != "DEFAULT":
                mapping_path_list_string = st.session_state["mkgc_config"].get(section, "mappings", fallback="")
                if mapping_path_list_string:
                    for mapping_path in mapping_path_list_string.split(","):
                        mapping_path = mapping_path.strip()
                        g_label = next((key for key, value in st.session_state["mkgc_g_mappings_dict"].items()
                            if value == mapping_path), os.path.splitext(os.path.basename(mapping_path))[0])
                        if g_label not in mkgc_used_mapping_list:   # only save if not duplicated
                            mkgc_used_mapping_list.append(g_label)
        for g_label in st.session_state["mkgc_g_mappings_dict"]:
            if g_label not in mkgc_used_mapping_list:
                mkgc_not_used_mapping_list.append(g_label)


        with col1b:
            list_to_choose = ["📁 File", "🌐 URL"]

            if mkgc_not_used_mapping_list:
                list_to_choose.append("🗑️ Remove")
            additional_mapping_source_option = st.radio("🖱️ Add mapping from:*", list_to_choose,
                horizontal=True, key="key_additional_mapping_source_option")

        if additional_mapping_source_option == "📁 File":
            with col1a:
                additional_mapping_label = st.text_input("⌨️ Enter mapping label:*", key="key_additional_mapping_label")

            if additional_mapping_label in st.session_state["mkgc_g_mappings_dict"] or additional_mapping_label == st.session_state["g_label"]:
                if additional_mapping_label:
                    with col1a:
                        st.markdown(f"""<div class="error-message">
                            ❌ Label <b>{additional_mapping_label}</b> is already in use.
                            <small>Please, pick a different label.</small>
                        </div>""", unsafe_allow_html=True)

            elif additional_mapping_label:

                with col1a:
                    uploaded_mapping = st.file_uploader(f"""🖱️ Upload mapping file:*""",
                        key=st.session_state["key_mapping_uploader"])

                    if uploaded_mapping:

                        uploaded_mapping_ok_flag = True
                        extension = os.path.splitext(uploaded_mapping.name)[1]
                        allowed_mapping_extensions = [".ttl", ".rml.ttl", ".r2rml.ttl", ".fnml.ttl",
                            ".rml-star.ttl", ".yaml", ".yml"]
                        if extension not in allowed_mapping_extensions:
                            with col1b:
                                st.write("")
                                st.markdown(f"""<div class="error-message">
                                    ❌ <b> File type is not valid. </b>
                                    <small>The allowed extensions are ".ttl", ".rml.ttl", ".r2rml.ttl", ".fnml.ttl",
                                        ".rml-star.ttl", ".yaml" and ".yml".</small>
                                </div>""", unsafe_allow_html=True)
                                uploaded_mapping_ok_flag = False

                        else:
                            try:
                                g = utils.load_mapping_from_file(uploaded_mapping)

                                # Check for key RML predicates
                                rml_predicates = [rdflib.URIRef("http://semweb.mmlab.be/ns/rml#logicalSource"),
                                    rdflib.URIRef("http://www.w3.org/ns/r2rml#subjectMap"),
                                    rdflib.URIRef("http://www.w3.org/ns/r2rml#predicateObjectMap")]

                                found_predicates = any(p in [pred for _, pred, _ in g] for p in rml_predicates)
                                check_g_mapping = utils.check_g_mapping(g)

                                if not found_predicates:
                                    with col1b:
                                        st.write("")
                                        st.write("")
                                        st.markdown(f"""<div class="error-message">
                                                ❌ File loaded, but <b>no RML structure found</b>.
                                                <small>Please, check your mapping content.</small>
                                            </div>""", unsafe_allow_html=True)
                                        uploaded_mapping_ok_flag = False

                                elif check_g_mapping:
                                    with col1b:
                                        st.write("")
                                        st.write("")
                                        st.markdown(f"""<div class="error-message">
                                                {check_g_mapping}
                                            </div>""", unsafe_allow_html=True)
                                        uploaded_mapping_ok_flag = False

                                else:
                                    with col1b:
                                        st.write("")
                                        st.write("")
                                        st.markdown(f"""<div class="success-message">
                                                ✔️ <b>Valid RML mapping<b> detected.
                                            </div>""", unsafe_allow_html=True)

                            except Exception as e:
                                with col1b:
                                    st.write("")
                                    st.write("")
                                    st.markdown(f"""<div class="error-message">
                                        ❌ <b> Failed to parse mapping file. </b>
                                        <small>Complete error: {e}</small>
                                    </div>""", unsafe_allow_html=True)
                                    uploaded_mapping_ok_flag = False

                        if uploaded_mapping_ok_flag:
                            with col1a:
                                st.button("Save", key="key_save_mapping_for_mkgcgc_button",
                                    on_click=save_mapping_for_mkgc)

        elif additional_mapping_source_option == "🌐 URL":

            with col1a:
                additional_mapping_label = st.text_input("⌨️ Enter mapping label:*", key="key_additional_mapping_label")

            if additional_mapping_label in st.session_state["mkgc_g_mappings_dict"] or additional_mapping_label == st.session_state["g_label"]:
                if additional_mapping_label:
                    with col1a:
                        st.markdown(f"""<div class="error-message">
                            ❌ Label <b>{additional_mapping_label}</b> is already in use.
                            <small>Please, pick a different label.</small>
                        </div>""", unsafe_allow_html=True)

            elif additional_mapping_label:
                with col1a:
                    mapping_url = st.text_input("⌨️ Enter mapping URL:*", key="key_mapping_url")

                if mapping_url:

                    with col1:
                        mapping_url_ok_flag = utils.is_valid_url_mapping(mapping_url, True)

                    if mapping_url_ok_flag:
                        with col1b:
                            st.write("")
                            st.markdown(f"""<div class="success-message">
                                    ✔️ <b>Valid RML mapping<b> detected.
                                </div>""", unsafe_allow_html=True)

                        with col1a:
                            st.button("Save", key="key_save_mapping_for_mkgcgc_from_url_button",
                                on_click=save_mapping_for_mkgcgc_from_url)

        if additional_mapping_source_option == "🗑️ Remove":

            list_to_choose =  list(reversed(mkgc_not_used_mapping_list))
            if len(list_to_choose) > 1:
                list_to_choose.insert(0, "Select all")
            with col1a:
                mappings_to_remove_list = st.multiselect("🖱️ Select mappings to remove:*",list_to_choose,
                    key="key_mappings_to_remove_list")

            if len(mkgc_not_used_mapping_list) < len(st.session_state["mkgc_g_mappings_dict"]):
                with col1b:
                    st.markdown(f"""<div class="info-message-gray">
                            Only <b>unused mappings</b> can be removed. <small>To remove other mappings,
                            delete the Data Sources that use them.</small>
                        </div>""", unsafe_allow_html=True)

            if "Select all" in mappings_to_remove_list:
                mappings_to_remove_list = list(st.session_state["mkgc_g_mappings_dict"].keys())
                with col1b:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ If you continue, <b>all mappings ({len(mappings_to_remove_list)})</b>
                            will be removed. <small>Make sure you want to go ahead.</small>
                        </div>""", unsafe_allow_html=True)

                with col1a:
                    delete_all_mappings_checkbox = st.checkbox(
                    "🔒 I am sure I want to delete all mappings",
                    key="key_delete_all_mappings_checkbox")
                    if delete_all_mappings_checkbox:
                        st.button("Remove", key="key_remove_additional_mapping_for_mkgcgc_button", on_click=remove_additional_mapping_for_mkgc)

            elif mappings_to_remove_list:
                with col1a:
                    delete_mappings_checkbox = st.checkbox(
                    "🔒 I am sure I want to delete the selected mapping/s",
                    key="key_delete_mappings_checkbox")
                    if delete_mappings_checkbox:
                        st.button("Remove", key="key_remove_additional_mapping_for_mkgcgc_button", on_click=remove_additional_mapping_for_mkgc)



#________________________________________________
# MATERIALISE
with tab3:

    col1, col2 = st.columns([2,1.5])

    with col1:
        col1a, col1b = st.columns([2,1])

    with col2:
        col2a, col2b = st.columns([0.5, 2])

    # Show config content
    config_string = io.StringIO()
    st.session_state["mkgc_config"].write(config_string)
    if config_string.getvalue() != "":
        with col2b:
            st.markdown(f"```ini\n{config_string.getvalue()}\n```")

    # PURPLE HEADING - MATERIALISE
    with col1:
        st.markdown("""<div class="purple-heading">
                🔮 Materialise
            </div>""", unsafe_allow_html=True)

    with col1:
        col1a, col1b = st.columns([2.5,1])

    if isinstance(st.session_state["graph_materialised_ok_flag"], list):
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="error-message">
                ❌ <b>Error during materialisation.</b>
                <small><b>Full error: {st.session_state["graph_materialised_ok_flag"][1]}</b></small>
            </div>""", unsafe_allow_html=True)
        st.session_state["graph_materialised_ok_flag"] = False
        time.sleep(utils.get_success_message_time()+5)
        st.rerun()

    if st.session_state["graph_materialised_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ <b>Graph</b> has been materialised!
            </div>""", unsafe_allow_html=True)
        st.session_state["graph_materialised_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    if config_string.getvalue() == "":
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.markdown(f"""<div class="error-message">
                ❌ <b>Config file is empty</b>.<small> You can auto-generate it
                in the <b>AutoConfig</b> pannel, or go to the
                <b>Manual Config</b> pannel for manual edition.</small>
            </div>""", unsafe_allow_html=True)

    else:

        # List of all used mappings
        mkgc_used_mapping_list = []
        for section in st.session_state["mkgc_config"].sections():
            if section != "CONFIGURATION" and section != "DEFAULT":
                mapping_path_list_string = st.session_state["mkgc_config"].get(section, "mappings", fallback="")
                if mapping_path_list_string:
                    for mapping_path in mapping_path_list_string.split(","):
                        mapping_path = mapping_path.strip()
                        g_label = next((key for key, value in st.session_state["mkgc_g_mappings_dict"].items()
                            if value == mapping_path), os.path.splitext(os.path.basename(mapping_path))[0])
                        if g_label not in mkgc_used_mapping_list:   # only save if not duplicated
                            mkgc_used_mapping_list.append(g_label)

        # List of all used sql databases
        mkgc_used_db_conn_list = []
        for section in st.session_state["mkgc_config"].sections():
            if section != "CONFIGURATION" and section != "DEFAULT":
                used_db_url = st.session_state["mkgc_config"].get(section, "db_url", fallback="")
                if used_db_url and used_db_url not in mkgc_used_db_conn_list:
                    mkgc_used_db_conn_list.append(used_db_url)

        # List of all used tabular data sources
        mkgc_used_tab_ds_list = []
        for section in st.session_state["mkgc_config"].sections():
            if section != "CONFIGURATION" and section != "DEFAULT":
                file_path = st.session_state["mkgc_config"].get(section, "file_path", fallback="")
                if file_path:
                    filename = os.path.basename(file_path)
                    if filename not in mkgc_used_tab_ds_list:
                        mkgc_used_tab_ds_list.append(filename)


        everything_ok_flag = True
        inner_html_success = ""
        inner_html_error = ""

        # Check g_mapping if used (additional mappings checked before adding)
        if st.session_state["g_label"] in mkgc_used_mapping_list:
            g_mapping_ok_flag = True
            if st.session_state["g_label"]:
                check_g_mapping = utils.check_g_mapping(st.session_state["g_mapping"])
                if check_g_mapping:
                    inner_html_error += "❌" + check_g_mapping
                    everything_ok_flag = False
                    g_mapping_ok_flag = False
                else:
                    inner_html_success += f"""✔️ Mapping <b>{st.session_state["g_label"]}</b>
                        complete.<br>"""

        # Message on additional mappings if used
        # Check links to additional mappings
        mkgc_not_working_url_mappings_list = []
        for section in st.session_state["mkgc_config"].sections():
            if section != "CONFIGURATION" and section != "DEFAULT":
                mapping_path_list_string = st.session_state["mkgc_config"].get(section, "mappings", fallback="")
                if mapping_path_list_string:
                    for mapping_path in mapping_path_list_string.split(","):
                        if mapping_path in st.session_state["mkgc_g_mappings_dict"].values(): # these are the URL additional mappings
                            if not utils.is_valid_url_mapping(mapping_path, False):
                                mkgc_not_working_url_mappings_list.append(mapping_path)


        mkgc_used_additional_mapping_list = mkgc_used_mapping_list.copy()
        if st.session_state["g_label"] in mkgc_used_additional_mapping_list:
            mkgc_used_additional_mapping_list.remove(st.session_state["g_label"])
        if mkgc_used_additional_mapping_list and not mkgc_not_working_url_mappings_list:
            inner_html_success += f"""✔️ <b>Additional mappings</b> are valid:<br>
                <div style="margin-left: 20px"><b><small>
                {utils.format_list_for_markdown(mkgc_used_additional_mapping_list)}</small><br></div>"""
        elif mkgc_used_additional_mapping_list:
            inner_html_error += f"""❌ URL to <b>additional mapping/s</b> not working:<br>
                <div style="margin-left: 20px"><b><small>
                {utils.format_list_for_markdown(mkgc_not_working_url_mappings_list)}</small><br></div>"""

        # Check connections to db if used
        not_working_db_conn_list = []
        for connection_string in mkgc_used_db_conn_list:
            timeout = 3
            try:
                engine = create_engine(connection_string, connect_args={"connect_timeout": timeout})
                conn = engine.connect()
            except Exception as e:
                not_working_db_conn_list.append(connection_string)
        if not not_working_db_conn_list and mkgc_used_db_conn_list:
            formatted_list = "<br>".join(mkgc_used_db_conn_list)
            inner_html_success += f"""✔️ All <b>connections to databases</b> are working:<br>
                <div style="margin-left: 20px"><small><b>{formatted_list}</b></small><br></div>"""
        elif not_working_db_conn_list:
            everything_ok_flag = False
            if len(not_working_db_conn_list) == 1:
                inner_html_error += f"""❌ A connection to database is not working:<br>
                    <div style="margin-left: 20px"><small><b>{utils.format_list_for_markdown(not_working_db_conn_list)}
                    </b></small><br></div>"""
            else:
                inner_html_error += f"""❌ Several connections to databases are not working:<br>
                    <div style="margin-left: 20px"><small><b>
                    {utils.format_list_for_markdown(not_working_db_conn_list)}</b></small><br></div>"""

        # Check all tabular sources are loaded
        not_loaded_ds_list = []
        for ds_filename in mkgc_used_tab_ds_list:
            if not ds_filename in st.session_state["ds_files_dict"]:
                not_loaded_ds_list.append(ds_filename)

        if not not_loaded_ds_list and mkgc_used_tab_ds_list:
            inner_html_success += f"""✔️ All <b>tabular data sources</b> are loaded:<br>
                <div style="margin-left: 20px"><small>
                <b>{utils.format_list_for_markdown(mkgc_used_tab_ds_list)}</b></small><br></div>"""
        elif mkgc_used_tab_ds_list:
            everything_ok_flag = False
            with col1a:
                if len(not_loaded_ds_list) == 1:
                    inner_html_error += f"""❌ A <b>tabular data source</b> is not loaded:
                        <div style="margin-left: 20px"><b><small>
                        {utils.format_list_for_markdown(not_loaded_ds_list)}</b></small><br></div>"""
                else:
                    inner_html_error += f"""❌ Several <b>tabular data sources</b> are not loaded:
                        <div style="margin-left: 20px"><small><b>
                        {utils.format_list_for_markdown(not_loaded_ds_list)}</b></small>
                        <br></div>"""

        # show check message
        with col1a:
            if inner_html_success:
                st.markdown(f"""<div class="success-message">
                        {inner_html_success}
                    </div>""", unsafe_allow_html=True)
            if inner_html_error:
                st.markdown(f"""<div class="error-message">
                        {inner_html_error}
                    </div>""", unsafe_allow_html=True)

        if everything_ok_flag:

            with col1a:
                st.write("")
                st.button("Materialise", key="key_materialise_graph_button", on_click=materialise_graph)

        else:
            with col1b:
                if st.session_state["g_label"] and not g_mapping_ok_flag:
                    st.markdown(f"""<div class="info-message-blue">
                            <small>ℹ️ You can fix mapping <b>{st.session_state["g_label"]}</b>
                            in the <b>Build Mapping</b> page.</small>
                        </div>""", unsafe_allow_html=True)
                if not_working_db_conn_list:
                    st.markdown(f"""<div class="info-message-blue">
                            <small>ℹ️ You can check the <b>connections to databases</b> in the
                            <b>Manage Logical Sources</b> page.</small>
                        </div>""", unsafe_allow_html=True)
                if not_loaded_ds_list:
                    st.markdown(f"""<div class="info-message-blue">
                            <small>ℹ️ You can load the <b>tabular data sources</b> in the
                            <b>Manage Logical Sources</b> page.</small>
                        </div>""", unsafe_allow_html=True)

        if st.session_state["materialised_g_mapping"]:

            with col1b:
                st.markdown(f"""<div class="info-message-blue">
                        ℹ️ Graph materialised with <b>{len(st.session_state["materialised_g_mapping"])} triples</b>.
                    </div>""", unsafe_allow_html=True)

            with col1:
                st.write("")
                st.markdown("""<div class="gray-heading">
                        📥 Download graph
                    </div>""", unsafe_allow_html=True)
                st.write("")

            with col1:
                col1a, col1b = st.columns([1,2])

            download_extension_dict = utils.get_g_mapping_file_formats_dict()
            download_format_list = list(download_extension_dict)

            with col1a:
                download_format = st.selectbox("🖱️ Select format:*", download_format_list, key="key_download_format_selectbox")
            download_extension = download_extension_dict[download_format]

            with col1b:
                download_filename = st.text_input("⌨️ Enter filename (without extension):*", key="key_download_filename_selectbox")

            if "." in download_filename:
                with col1b:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ The filename <b style="color:#cc9a06;">{download_filename}</b>
                            seems to include an extension.
                        </div>""", unsafe_allow_html=True)

            with col1:
                col1a, col1b = st.columns([1.5,1])

            if download_filename:
                download_filename_complete = download_filename + download_extension if download_filename else ""
                if download_format == "turtle":
                    mime_option = "text/turtle"
                elif download_format == "ntriples":
                    mime_option = "application/n-triples"
                elif download_format == "trig":
                    mime_option = "application/trig"
                elif download_format == "jsonld":
                    mime_option = "application/ld+json"

                with col1a:
                    st.write("")
                    st.download_button(label="Download",
                        data=st.session_state["materialised_g_mapping_file"],
                        file_name=download_filename_complete,
                        mime=mime_option)

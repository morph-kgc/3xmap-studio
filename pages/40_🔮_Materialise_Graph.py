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

# Header
st.markdown("""<div style="display:flex; align-items:center; background-color:#f0f0f0; padding:12px 18px;
    border-radius:8px; margin-bottom:16px;">
    <span style="font-size:1.7rem; margin-right:18px;">🔮</span><div>
        <h3 style="margin:0; font-size:1.75rem;">
            <span style="color:#511D66; font-weight:bold; margin-right:12px;">◽◽◽◽◽</span>
            Materialise Graph
            <span style="color:#511D66; font-weight:bold; margin-left:12px;">◽◽◽◽◽</span>
        </h3>
        <p style="margin:0; font-size:0.95rem; color:#555;">
            Use <b>Morph-KGC</b> to materialise a graph from <b>mappings</b> and <b>data sources</b>.
        </p>
    </div></div>""", unsafe_allow_html=True)

#____________________________________________
#PRELIMINARY

# Import style
utils.import_st_aesthetics()
st.write("")

# Namespaces
RML, RR, QL = utils.get_required_ns().values()

# Temporal folder to put everything
temp_folder_path = os.path.join(os.getcwd(), "materialising_mapping_temp")

# Initialise session state variables
# OTHER PAGES
if "g_label" not in st.session_state:
    st.session_state["g_label"] = ""
if "g_mapping" not in st.session_state:
    st.session_state["g_mapping"] = Graph()
if "db_connections_dict" not in st.session_state:
    st.session_state["db_connections_dict"] = {}
if "ds_files_dict" not in st.session_state:
    st.session_state["ds_files_dict"] = {}

# TAB1
if "mk_config" not in st.session_state:
    st.session_state["mk_config"] = configparser.ConfigParser()
if "mk_g_mappings_dict" not in st.session_state:
    st.session_state["mk_g_mappings_dict"] = {}
if "ds_for_mk_saved_ok_flag" not in st.session_state:
    st.session_state["ds_for_mk_saved_ok_flag"] = False
if "ds_for_mk_removed_ok_flag" not in st.session_state:
    st.session_state["ds_for_mk_removed_ok_flag"] = False
if "configuration_for_mk_saved_ok_flag" not in st.session_state:
    st.session_state["configuration_for_mk_saved_ok_flag"] = False
if "configuration_for_mk_removed_ok_flag" not in st.session_state:
    st.session_state["configuration_for_mk_removed_ok_flag"] = False

# TAB2
if "additional_mapping_added_ok_flag" not in st.session_state:
    st.session_state["additional_mapping_added_ok_flag"] = False
if "key_mapping_uploader" not in st.session_state:
    st.session_state["key_mapping_uploader"] = str(uuid.uuid4())
if "additional_mapping_for_mk_saved_ok_flag" not in st.session_state:
    st.session_state["additional_mapping_for_mk_saved_ok_flag"] = False
if "additional_mapping_removed_ok_flag" not in st.session_state:
    st.session_state["additional_mapping_removed_ok_flag"] = False
if "additional_mapping_added_from_URL_ok_flag" not in st.session_state:
    st.session_state["additional_mapping_added_from_URL_ok_flag"] = False


#define on_click functions
# TAB1
def save_sql_ds_for_mk():
    # add to config dict___________________
    st.session_state["mk_config"][mk_ds_label] = {"db_url": db_url,
        "mappings": mk_mappings_str_for_sql}
    # store information________________________
    st.session_state["ds_for_mk_saved_ok_flag"] = True
    # reset fields__________________________
    st.session_state["key_mk_ds_label"] = ""

def save_tab_ds_for_mk():
    # add to config dict___________________
    st.session_state["mk_config"][mk_ds_label] = {"file_path": mk_tab_ds_file_path,
        "mappings": mk_mappings_str_for_tab}
    # store information________________________
    st.session_state["ds_for_mk_saved_ok_flag"] = True
    # reset fields__________________________
    st.session_state["key_mk_ds_label"] = ""

def remove_ds_for_mk():
    # remove from config dict___________________
    for ds in ds_for_mk_to_remove_list:
        del st.session_state["mk_config"][ds]
    # store information________________________
    st.session_state["ds_for_mk_removed_ok_flag"] = True
    # reset fields__________________________
    st.session_state["key_ds_for_mk_to_remove_list"] = []

def save_options_for_mk():
    #create section_______________
    if not st.session_state["mk_config"].has_section("CONFIGURATION"):
        st.session_state["mk_config"].add_section("CONFIGURATION")
    # add to config dict___________________
    if output_file:
        st.session_state["mk_config"]["CONFIGURATION"]["output_file"] = output_file
    else:
        if st.session_state["mk_config"].has_option("CONFIGURATION", "output_file"):
            st.session_state["mk_config"].remove_option("CONFIGURATION", "output_file")
    if output_format != "Select option":
        st.session_state["mk_config"]["CONFIGURATION"]["output_format"] = output_format
    else:
        if st.session_state["mk_config"].has_option("CONFIGURATION", "output_format"):
            st.session_state["mk_config"].remove_option("CONFIGURATION", "output_format")
    if log_level != "Select option":
        st.session_state["mk_config"]["CONFIGURATION"]["log_level"] = log_level
    else:
        if st.session_state["mk_config"].has_option("CONFIGURATION", "log_level"):
            st.session_state["mk_config"].remove_option("CONFIGURATION", "log_level")
    if mapping_partitioning != "Select option":
        st.session_state["mk_config"]["CONFIGURATION"]["mapping_partitioning"] = mapping_partitioning
    else:
        if st.session_state["mk_config"].has_option("CONFIGURATION", "mapping_partitioning"):
            st.session_state["mk_config"].remove_option("CONFIGURATION", "mapping_partitioning")
    if na_values:
        st.session_state["mk_config"]["CONFIGURATION"]["na_values"] = na_values
    else:
        if st.session_state["mk_config"].has_option("CONFIGURATION", "na_values"):
            st.session_state["mk_config"].remove_option("CONFIGURATION", "na_values")
    if only_printable_chars != "Select option":
        st.session_state["mk_config"]["CONFIGURATION"]["only_printable_chars"] = only_printable_chars
    else:
        if st.session_state["mk_config"].has_option("CONFIGURATION", "only_printable_chars"):
            st.session_state["mk_config"].remove_option("CONFIGURATION", "only_printable_chars")
    if literal_escaping_chars:
        st.session_state["mk_config"]["CONFIGURATION"]["literal_escaping_chars"] = literal_escaping_chars
    else:
        if st.session_state["mk_config"].has_option("CONFIGURATION", "literal_escaping_chars"):
            st.session_state["mk_config"].remove_option("CONFIGURATION", "literal_escaping_chars")
    if infer_sql_datatypes != "Select option":
        st.session_state["mk_config"]["CONFIGURATION"]["infer_sql_datatypes"] = infer_sql_datatypes
    else:
        if st.session_state["mk_config"].has_option("CONFIGURATION", "infer_sql_datatypes"):
            st.session_state["mk_config"].remove_option("CONFIGURATION", "infer_sql_datatypes")
    if number_of_processes:
        st.session_state["mk_config"]["CONFIGURATION"]["number_of_processes"] = number_of_processes
    else:
        if st.session_state["mk_config"].has_option("CONFIGURATION", "number_of_processes"):
            st.session_state["mk_config"].remove_option("CONFIGURATION", "number_of_processes")
    if output_kafka_server:
        st.session_state["mk_config"]["CONFIGURATION"]["output_kafka_server"] = output_kafka_server
    else:
        if st.session_state["mk_config"].has_option("CONFIGURATION", "output_kafka_server"):
            st.session_state["mk_config"].remove_option("CONFIGURATION", "output_kafka_server")
        if st.session_state["mk_config"].has_option("CONFIGURATION", "output_kafka_topic"):
            st.session_state["mk_config"].remove_option("CONFIGURATION", "output_kafka_topic")
    if output_kafka_server:
        if output_kafka_topic:
            st.session_state["mk_config"]["CONFIGURATION"]["output_kafka_topic"] = output_kafka_topic
        else:
            if st.session_state["mk_config"].has_option("CONFIGURATION", "output_kafka_topic"):
                st.session_state["mk_config"].remove_option("CONFIGURATION", "output_kafka_topic")
    # store information________________________
    st.session_state["configuration_for_mk_saved_ok_flag"] = True
    # reset fields__________________________
    st.session_state["key_configure_options_for_mk"] = "🔒 Keep options"

def remove_options_for_mk():
    # remove from config dict___________________
    del st.session_state["mk_config"]["CONFIGURATION"]
    # store information________________________
    st.session_state["configuration_for_mk_removed_ok_flag"] = True
    # reset fields__________________________
    st.session_state["key_configure_options_for_mk"] = "🚫 No options"

# TAB2
def save_mapping_for_mk():
    # store information________________________
    st.session_state["mk_g_mappings_dict"][uploaded_mapping_label] = uploaded_mapping
    st.session_state["additional_mapping_added_ok_flag"] = True
    # reset fields_______________________________
    st.session_state["key_uploaded_mapping_label"] = ""
    st.session_state["key_mapping_uploader"] = str(uuid.uuid4())

def save_mapping_for_mk_from_url():
    # store information________________________
    st.session_state["mk_g_mappings_dict"][url_mapping_label] = url_mapping
    st.session_state["additional_mapping_added_from_URL_ok_flag"] = True
    # reset fields_______________________________
    st.session_state["key_mapping_label_url"] = ""

def remove_additional_mapping_for_mk():
    # remove________________________
    for mapping in mappings_to_remove_list:
        del st.session_state["mk_g_mappings_dict"][mapping]
    # store information________________________
    st.session_state["additional_mapping_removed_ok_flag"] = True
    # reset fields_______________________________
    st.session_state["key_mappings_to_remove_list"] = []



#____________________________________________________________
# PANELS OF THE PAGE (tabs)

tab1, tab2, tab3 = st.tabs(["Materialise", "Additional Mappings", "Check and Go"])


#________________________________________________
# MATERIALISE
with tab1:

    col1, col2 = st.columns([2,1.5])

    with col1:
        col1a, col1b = st.columns([2,1])

    with col2:
        col2a, col2b = st.columns([0.5, 2])

    # Show config content
    with col2b:
        config_string = io.StringIO()
        st.session_state["mk_config"].write(config_string)
        if config_string.getvalue() != "":
            st.markdown(f"```ini\n{config_string.getvalue()}\n```")

    # PURPLE HEADING - ADD DATA SOURCE
    with col1:
        st.markdown("""<div class="purple-heading">
                📊 Configure Data Source
            </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([2,1])

    if st.session_state["ds_for_mk_saved_ok_flag"]:
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>data source</b> has been saved!
            </div>""", unsafe_allow_html=True)
        st.session_state["ds_for_mk_saved_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()


    with col1a:
        mk_ds_label = st.text_input("⌨️ Enter data source label:*", key="key_mk_ds_label")

    if mk_ds_label:
        excluded_characters = r"[ \t\n\r<>\"{}|\\^`\[\]%']"
        if mk_ds_label in st.session_state["mk_config"]:
            with col1a:
                st.markdown(f"""<div class="error-message">
                    ❌ Label is <b>already in use</b>.
                    <small> You must either delete the already existing data source or pick a different label.</small>
                </div>""", unsafe_allow_html=True)
        elif re.search(excluded_characters, mk_ds_label):
            with col1a:
                st.markdown(f"""<div class="error-message">
                    ❌ <b>Forbidden character</b> in data source label.
                    <small> Please, pick a valid label.</small>
                </div>""", unsafe_allow_html=True)
        elif mk_ds_label.lower() == "CONFIGURATION":
            with col1a:
                st.markdown(f"""<div class="error-message">
                    ❌ <b>"CONFIGURATION" label</b> is not allowed.
                    <small> You must pick a different label.</small>
                </div>""", unsafe_allow_html=True)

        else:

            if not st.session_state["db_connections_dict"] and not st.session_state["ds_files_dict"]:
                with col1a:
                    st.markdown(f"""<div class="error-message">
                        ❌ <b> There are no data sources available.
                        <small>You can add them in the <b>📊 Manage Logical Sources</b> page.</small>
                    </div>""", unsafe_allow_html=True)
                mk_ds_type = ""
            elif not st.session_state["ds_files_dict"]:
                mk_ds_type = "📊 SQL Database"
            elif not st.session_state["db_connections_dict"]:
                mk_ds_type = "🛢️ Tabular data"
            else:
                with col1b:
                    st.write("")
                    mk_ds_type = st.radio("🖱️ Select an option:*", ["📊 SQL Database", "🛢️ Tabular data"],
                        label_visibility="collapsed", key="key_mk_ds_type")

            if mk_ds_type == "📊 SQL Database":

                with col1:
                    col1a, col1b = st.columns(2)
                with col1a:
                    list_to_choose = list(reversed(st.session_state["db_connections_dict"]))
                    list_to_choose.insert(0, "Select data source")
                    mk_sql_ds = st.selectbox("🖱️ Select data source:*", list_to_choose,
                        key="key_mk_sql_ds")

                    if mk_sql_ds != "Select data source":
                        db_url = utils.get_db_url_str(mk_sql_ds)
                        db_user = st.session_state["db_connections_dict"][mk_sql_ds][4]
                        db_password = st.session_state["db_connections_dict"][mk_sql_ds][5]
                        db_type = st.session_state["db_connections_dict"][mk_sql_ds][0]

                with col1b:
                    mk_g_mapping_dict_complete = st.session_state["mk_g_mappings_dict"].copy()
                    if st.session_state["g_label"]:
                        mk_g_mapping_dict_complete[st.session_state["g_label"]] = st.session_state["g_mapping"]

                    list_to_choose = list(reversed(list(mk_g_mapping_dict_complete)))
                    if len(list_to_choose) > 1:
                        list_to_choose.insert(0, "Select all")

                    if st.session_state["g_label"]:
                        mk_mappings_list_for_sql = st.multiselect("🖱️ Select mappings:*", list_to_choose,
                            default=[st.session_state["g_label"]], key="key_mk_mappings")
                    else:
                        mk_mappings_list_for_sql = st.multiselect("🖱️ Select mappings:*", list_to_choose,
                            key="key_mk_mappings")

                    if not mk_g_mapping_dict_complete:
                        with col1:
                            st.markdown(f"""<div class="error-message">
                                ❌ <b> No mappings available. </b>
                                <small>You can build a mapping using <b>RDFolio</b>
                                and/or load additional mappings in the <b>Additional Mappings</b> pannel.</small>
                            </div>""", unsafe_allow_html=True)

                if "Select all" in mk_mappings_list_for_sql:
                    mk_mappings_list_for_sql = list(reversed(list(mk_g_mapping_dict_complete)))

                mk_mappings_paths_list_for_sql = [os.path.join(temp_folder_path, mapping + ".ttl")
                    for mapping in mk_mappings_list_for_sql]
                mk_mappings_str_for_sql = ", ".join(mk_mappings_paths_list_for_sql)   # join into a comma-separated string for the config

                # with col1:
                #     col1a, col1b = st.columns(2)
                # with col1a:
                #     schema = st.text_input("⌨️ Enter schema (optional):")
                # with col1b:
                #     driver_class = st.text_input("⌨️ Enter driver class (optional):")

                if mk_sql_ds != "Select data source" and mk_mappings_list_for_sql:
                    with col1a:
                        st.button("Save", key="save_sql_ds_for_mk_button", on_click=save_sql_ds_for_mk)

            if mk_ds_type == "🛢️ Tabular data":

                with col1:
                    col1a, col1b = st.columns(2)
                with col1a:
                    list_to_choose = list(reversed(st.session_state["ds_files_dict"]))
                    list_to_choose.insert(0, "Select data source")
                    mk_tab_ds_file = st.selectbox("🖱️ Select data source:*", list_to_choose,
                        key="key_mk_tab_ds_file")

                    if mk_tab_ds_file != "Select data source":
                        mk_tab_ds_file_path = os.path.join(temp_folder_path, mk_tab_ds_file)

                with col1b:
                    mk_g_mapping_dict_complete = st.session_state["mk_g_mappings_dict"].copy()
                    if st.session_state["g_label"]:
                        mk_g_mapping_dict_complete[st.session_state["g_label"]] = st.session_state["g_mapping"]

                    list_to_choose = list(reversed(list(mk_g_mapping_dict_complete)))
                    if len(list_to_choose) > 1:
                        list_to_choose.insert(0, "Select all")

                    if st.session_state["g_label"]:
                        mk_mappings_list_for_tab = st.multiselect("🖱️ Select mappings:*", list_to_choose,
                            default=[st.session_state["g_label"]], key="key_mk_mappings")
                    else:
                        mk_mappings_list_for_tab = st.multiselect("🖱️ Select mappings:*", list_to_choose,
                            key="key_mk_mappings")

                    if not mk_g_mapping_dict_complete:
                        with col1:
                            st.markdown(f"""<div class="error-message">
                                ❌ <b> No mappings available. </b>
                                <small>You can build a mapping using <b>RDFolio</b>
                                and/or load additional mappings in the <b>Additional Mappings</b> pannel.</small>
                            </div>""", unsafe_allow_html=True)

                mk_mappings_paths_list_for_tab = [os.path.join(temp_folder_path, mapping + ".ttl")
                    for mapping in mk_mappings_list_for_tab]
                mk_mappings_str_for_tab = ", ".join(mk_mappings_paths_list_for_tab)   # join into a comma-separated string for the config

                if mk_tab_ds_file != "Select data source" and mk_mappings_list_for_tab:
                    with col1a:
                        st.button("Save", key="save_tab_ds_for_mk_button", on_click=save_tab_ds_for_mk)

    if list(st.session_state["mk_config"].keys()) == ["DEFAULT"] or list(st.session_state["mk_config"].keys()) == ["DEFAULT", "CONFIGURATION"]:
        if st.session_state["ds_for_mk_removed_ok_flag"]:
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>data source/s</b> have been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["ds_for_mk_removed_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()


    # PURPLE HEADING - REMOVE DATA SOURCE
    if list(st.session_state["mk_config"].keys()) != ["DEFAULT"] and list(st.session_state["mk_config"].keys()) != ["DEFAULT", "CONFIGURATION"]:
        with col1:
            st.write("______")
            st.markdown("""<div class="purple-heading">
                    🗑️ Remove Data Source
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a, col1b = st.columns([2,1])

        if st.session_state["ds_for_mk_removed_ok_flag"]:
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>data source</b> has been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["ds_for_mk_removed_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()

        with col1a:
            list_to_choose = list(reversed(list(st.session_state["mk_config"])))
            list_to_choose.remove("DEFAULT")
            if "CONFIGURATION" in list_to_choose:
                list_to_choose.remove("CONFIGURATION")
            if len(list_to_choose) > 1:
                list_to_choose.insert(0, "Select all")

            ds_for_mk_to_remove_list = st.multiselect("🖱️ Select data sources:*", list_to_choose,
                key="key_ds_for_mk_to_remove_list")

            if "Select all" in ds_for_mk_to_remove_list:
                ds_for_mk_to_remove_list = list(reversed(list(st.session_state["mk_config"])))
                ds_for_mk_to_remove_list.remove("DEFAULT")
                if "CONFIGURATION" in ds_for_mk_to_remove_list:
                    ds_for_mk_to_remove_list.remove("CONFIGURATION")

            if ds_for_mk_to_remove_list:
                with col1a:
                    st.button("Remove", key="remove_ds_for_mk_button", on_click=remove_ds_for_mk)



    # PURPLE HEADING - ADD OPTIONS
    with col1:
        st.write("_______")
        st.markdown("""<div class="purple-heading">
                ⚙️ Configure Options
            </div>""", unsafe_allow_html=True)

    with col1:
        col1a, col1b = st.columns(2)

    if st.session_state["configuration_for_mk_saved_ok_flag"]:
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>configuration</b> has been saved!
            </div>""", unsafe_allow_html=True)
        st.session_state["configuration_for_mk_saved_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    if st.session_state["configuration_for_mk_removed_ok_flag"]:
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>configuration</b> has been removed!
            </div>""", unsafe_allow_html=True)
        st.session_state["configuration_for_mk_removed_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()


    with col1:
        if st.session_state["mk_config"].has_section("CONFIGURATION"):
            configure_options_for_mk = st.radio("🖱️ Select an option:*",
                ["🔒 Keep options", "✏️ Modify options", "🗑️ Remove options"],
                horizontal=True, label_visibility="collapsed",
                key="key_configure_options_for_mk")
        else:
            configure_options_for_mk = st.radio("🖱️ Select an option:*",
                ["🚫 No options", "✏️ Add options"],
                horizontal=True, label_visibility="collapsed",
                key="key_configure_options_for_mk")

    if configure_options_for_mk in ["✏️ Modify options", "✏️ Add options"]:

        options_for_mk_ok_flag = True

        with col1:
            col1a, col1b = st.columns(2)

        with col1a:
            default_output_file = st.session_state["mk_config"].get("CONFIGURATION", "output_filename", fallback="")
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
                    options_for_mk_ok_flag = False
                elif output_filename.endswith("."):
                    st.markdown(f"""<div class="error-message">
                        ❌ <b>Trailing "."</b> in filename.
                        <small> Please, remove it.</small>
                    </div>""", unsafe_allow_html=True)
                    options_for_mk_ok_flag = False
                else:
                    for item in windows_reserved_names:
                        if item == os.path.splitext(output_filename)[0].upper():
                            st.markdown(f"""<div class="error-message">
                                ❌ <b>Reserved filename.</b><br>
                                <small>Please, pick a different filename.</small>
                            </div>""", unsafe_allow_html=True)
                            options_for_mk_ok_flag = False
                            break  # Stop checking after first match
                    if options_for_mk_ok_flag:
                        if not os.path.splitext(output_filename)[1]:
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ <b>No extension</b> in filename.
                                <small> Using an extension is recommended. Make sure it matched the file format (if given).</small>
                            </div>""", unsafe_allow_html=True)

            output_file = os.path.join(temp_folder_path, output_filename) if output_filename else ""

        with col1b:
            default_output_format = st.session_state["mk_config"].get("CONFIGURATION", "output_format", fallback="Select option")
            list_to_choose = ["N-TRIPLES", "N-QUADS"]
            list_to_choose.insert(0, "Select option")
            output_format = st.selectbox("🖱️ Select format (optional):", list_to_choose,
                index=list_to_choose.index(default_output_format), key="key_output_format")

        with col1:
            col1a, col1b = st.columns(2)
        with col1a:
            default_log_level = st.session_state["mk_config"].get("CONFIGURATION", "log_level", fallback="Select option")
            list_to_choose = ["INFO", "DEBUG","WARNING", "ERROR", "CRITICAL", "NOTSET"]
            list_to_choose.insert(0, "Select option")
            log_level = st.selectbox("🖱️ Select log level (optional):", list_to_choose,
                index=list_to_choose.index(default_log_level), key="key_log_level")

        with col1b:
            default_mapping_partitioning = st.session_state["mk_config"].get("CONFIGURATION", "mapping_partitioning", fallback="Select option")
            list_to_choose = ["MAXIMAL", "PARTIAL-AGGREGATIONS", "off"]
            list_to_choose.insert(0, "Select option")
            mapping_partitioning = st.selectbox("🖱️ Select mapping partitioning (optional):", list_to_choose,
                index=list_to_choose.index(default_mapping_partitioning), key="key_mapping_partitioning")

        with col1:
            col1a, col1b = st.columns(2)
        with col1a:
            default_na_values = st.session_state["mk_config"].get("CONFIGURATION", "na_values", fallback="")
            default_na_values_list = default_na_values.split(",") if default_na_values else []
            list_to_choose = ["null", "NULL", "nan", "NaN", "NA", "N/A", "#N/A", "missing", '""',
                "-", ".", "none", "None", "undefined", "#VALUE!", "#REF!", "#DIV/0!"]
            na_values_list = st.multiselect("🖱️ Select na values (optional)", list_to_choose,
                default=default_na_values_list, key="key_na_values")
            na_values = ",".join(na_values_list)

        with col1b:
            default_only_printable_chars = st.session_state["mk_config"].get("CONFIGURATION", "only_printable_chars", fallback="Select option")
            list_to_choose = ["Select option", "Yes", "No"]
            only_printable_chars = st.selectbox("🖱️ Only printable charts (optional):", list_to_choose,
                index=list_to_choose.index(default_only_printable_chars), key="key_only_printable_chars")

        with col1:
            col1a, col1b = st.columns(2)
        with col1a:
            default_literal_escaping_chars = st.session_state["mk_config"].get("CONFIGURATION", "literal_escaping_chars", fallback="")
            default_literal_escaping_chars_list = list(default_literal_escaping_chars) if default_literal_escaping_chars else []
            list_to_choose = ["Select all", "!", "#", "$", "&", "'", "(", ")", "*", "+", ",", "/", ":", ";", "=", "?", "@", "[", "]"]
            literal_escaping_chars_list = st.multiselect("🖱️ Select safe percent encodings (optional)", list_to_choose,
                default=default_literal_escaping_chars_list, key="key_literal_escaping_chars")
            if "Select all" in literal_escaping_chars_list:
                literal_escaping_chars_list = ["!", "#", "$", "&", "'", "(", ")", "*", "+", ",", "/", ":", ";", "=", "?", "@", "[", "]"]
            literal_escaping_chars = "".join(literal_escaping_chars_list)

        with col1b:
            default_infer_sql_datatypes = st.session_state["mk_config"].get("CONFIGURATION", "infer_sql_datatypes ", fallback="Select option")
            list_to_choose = ["Select option", "Yes", "No"]
            list_to_choose = ["Select option", "Yes", "No"]
            infer_sql_datatypes = st.selectbox("🖱️ Infer sql datatypes (optional):", list_to_choose,
                index=list_to_choose.index(default_infer_sql_datatypes), key="key_infer_sql_datatypes")

        with col1:
            col1a, col1b = st.columns(2)

        with col1a:
            default_number_of_processes = st.session_state["mk_config"].get("CONFIGURATION", "number_of_processes", fallback="")
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
            default_output_kafka_server = st.session_state["mk_config"].get("CONFIGURATION", "output_kafka_server", fallback="")
            output_kafka_server = st.text_input("⌨️ Output Kafka server (optional):",
                value=default_output_kafka_server, key="key_default_output_kafka_server")

        with col1:
            col1a, col1b = st.columns(2)

        if output_kafka_server:
            with col1b:
                default_output_kafka_topic = st.session_state["mk_config"].get("CONFIGURATION", "output_kafka_topic", fallback="")
                output_kafka_topic = st.text_input("⌨️ Output Kafka topic (optional):",
                    value=default_output_kafka_topic, key="key_optput_kafka_topic")
                if not output_kafka_topic:
                    st.markdown(f"""<div class="error-message">
                        ❌ An <b>output Kafka topic</b> must be selected if
                        a <b>output Kafka server</b> is entered.
                    </div>""", unsafe_allow_html=True)
                    options_for_mk_ok_flag = False
                else:
                    kafka_topic_forbidden_chars = " /\\:;\"'<>[]{}|^`~?*&%#@=+,\t\n\r"
                    pattern = "[" + re.escape(kafka_topic_forbidden_chars) + "]"
                    if re.search(pattern, output_kafka_topic):
                        st.markdown(f"""<div class="error-message">
                            ❌ <b>Forbidden character</b> in output Kafka topic.
                            <small> Please, pick a valid topic.</small>
                        </div>""", unsafe_allow_html=True)
                        options_for_mk_ok_flag = False

        if output_kafka_server and output_kafka_topic:
            with col1b:
                st.markdown(f"""<div class="warning-message">
                    ⚠️ <b>No validation provided</b>.
                    <small> Please check connectivity and provide a valid topic.</small>
                </div>""", unsafe_allow_html=True)

        if options_for_mk_ok_flag:
            st.button("Save", key="key_save_options_for_mk_button", on_click=save_options_for_mk)

    if configure_options_for_mk == "🗑️ Remove options":
        with col1:
            remove_options_for_mk_checkbox = st.checkbox(
            ":gray-badge[⚠️ I am sure I want to remove the Options]",
            key="key_remove_options_for_mk_checkbox")
            if remove_options_for_mk_checkbox:
                st.button("Remove", on_click=remove_options_for_mk)

#________________________________________________
# ADDITIONAL MAPPINGS
with tab2:

    col1, col2 = st.columns([2,1.5])

    with col1:
        col1a, col1b = st.columns([2,1])

    with col2:
        col2a, col2b = st.columns([0.5, 2])

    with col2b:
        st.write("")
        st.write("")

        rows = [{"Mapping": label} for label in reversed(list(st.session_state["mk_g_mappings_dict"].keys()))]
        mk_g_mappings_df = pd.DataFrame(rows)
        mk_g_mappings_df = mk_g_mappings_df.head(utils.get_max_length_for_display()[1])

        max_length = utils.get_max_length_for_display()[1]   # max number of connections to show directly
        if st.session_state["mk_g_mappings_dict"]:
            if len(st.session_state["mk_g_mappings_dict"]) < max_length:
                st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                        🔎 additional mappings
                    </div>""", unsafe_allow_html=True)
                st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                        🔎 last added mappings
                    </div>""", unsafe_allow_html=True)
                st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        (complete list below)
                    </div>""", unsafe_allow_html=True)
            st.dataframe(mk_g_mappings_df, hide_index=True)


        #Option to show all connections (if too many)
        if st.session_state["db_connections_dict"] and len(st.session_state["db_connections_dict"]) > max_length:
            with st.expander("🔎 Show all mappings"):
                st.write("")
                st.dataframe(mk_g_mappings_df, hide_index=True)

    #PURPLE HEADING - UPLOAD FILE
    with col1:
        st.write("")
        st.markdown("""<div class="purple-heading">
                📁 Upload Mapping from File
            </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([2,1])

    if st.session_state["additional_mapping_added_ok_flag"]:
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>mapping</b> has been added!
            </div>""", unsafe_allow_html=True)
        st.session_state["additional_mapping_added_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    with col1a:
        uploaded_mapping_label = st.text_input("⌨️ Enter mapping label:*", key="key_uploaded_mapping_label")

    if uploaded_mapping_label in st.session_state["mk_g_mappings_dict"] or uploaded_mapping_label == st.session_state["g_label"]:
        if uploaded_mapping_label:
            with col1a:
                st.markdown(f"""<div class="error-message">
                    ❌ Label <b>{uploaded_mapping_label}</b> is already in use.
                    <small>Please, pick a different label.</small>
                </div>""", unsafe_allow_html=True)

    elif uploaded_mapping_label:

        with col1:
            col1a, col1b = st.columns([2,1])

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
                        st.write("")
                        st.button("Save", key="key_save_mapping_for_mk_button",
                            on_click=save_mapping_for_mk)


    #PURPLE HEADING - ADD MAPPING FROM URL
    with col1:
        st.write("______")
        st.markdown("""<div class="purple-heading">
                🌐 Add Mapping from URL
            </div>""", unsafe_allow_html=True)
        st.write("")


    with col1:
        col1a, col1b = st.columns([1,2])

    if st.session_state["additional_mapping_added_from_URL_ok_flag"]:
        with col1:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>mapping</b> has been added!
            </div>""", unsafe_allow_html=True)
        st.session_state["additional_mapping_added_from_URL_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    with col1a:
        url_mapping_label = st.text_input("⌨️ Enter mapping label:*", key="key_mapping_label_url")

        #https://raw.githubusercontent.com/arcangelo7/rml-mapping/main/rules.rml.ttl

    if url_mapping_label in st.session_state["mk_g_mappings_dict"] or url_mapping_label == st.session_state["g_label"]:
        if url_mapping_label:
            with col1a:
                st.markdown(f"""<div class="error-message">
                    ❌ Label <b>{url_mapping_label}</b> is already in use.
                    <small>Please, pick a different label.</small>
                </div>""", unsafe_allow_html=True)

    elif url_mapping_label:

        with col1b:
            mapping_url = st.text_input("⌨️ Enter mapping URL:*", key="key_mapping_url")

        if mapping_url:

            mapping_url_ok_flag = True

            try:
                # Fetch content
                response = requests.get(mapping_url)
                response.raise_for_status()
                url_mapping = response.text

                # Check extension
                if mapping_url.endswith((".ttl", ".rml.ttl", ".r2rml.ttl", ".fnml.ttl", ".rml-star.ttl")):
                    # Step 3a: Parse as RDF
                    g = rdflib.Graph()
                    g.parse(data=url_mapping, format="turtle")

                    # Look for RML/R2RML predicates
                    rml_predicates = [
                        rdflib.URIRef("http://semweb.mmlab.be/ns/rml#logicalSource"),
                        rdflib.URIRef("http://www.w3.org/ns/r2rml#subjectMap"),
                        rdflib.URIRef("http://www.w3.org/ns/r2rml#predicateObjectMap")]

                    found = any(p in [pred for _, pred, _ in g] for p in rml_predicates)

                    if not found:
                        with col1:
                            st.markdown(f"""<div class="error-message">
                                    ❌ Link working, but <b>no RML structure found</b>.
                                    <small>Please, check your mapping content.</small>
                                </div>""", unsafe_allow_html=True)
                            mapping_url_ok_flag = False

                elif url.endswith((".yaml", ".yml")):
                    # Parse as YAML
                    data = yaml.safe_load(url_mapping)

                    # Step 4b: Check for YARRRML structure
                    if not "mappings" in data and isinstance(data["mappings"], dict):
                        with col1:
                            st.markdown(f"""<div class="error-message">
                                    ❌ Link working, but <b>no YARRRML structure found</b>.
                                    <small>Please, check your mapping content.</small>
                                </div>""", unsafe_allow_html=True)
                            mapping_url_ok_flag = False

                else:
                    with col1:
                        st.markdown(f"""<div class="error-message">
                            ❌ <b>Extension is not valid</b>.
                        </div>""", unsafe_allow_html=True)
                        mapping_url_ok_flag = False

            except Exception as e:
                with col1:
                    st.markdown(f"""<div class="error-message">
                        ❌ <b>Validation failed.</b><br>
                        <small> Complete error: {e}</small>
                    </div>""", unsafe_allow_html=True)
                mapping_url_ok_flag = False

            if mapping_url_ok_flag:
                with col1:
                    st.markdown(f"""<div class="success-message">
                            ✔️ <b>Valid RML mapping<b> detected.
                        </div>""", unsafe_allow_html=True)

                with col1:
                    st.write("")
                    st.button("Save", key="key_save_mapping_for_mk_from_url_button",
                        on_click=save_mapping_for_mk_from_url)

    if not st.session_state["ds_files_dict"] and st.session_state["additional_mapping_removed_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>data source file/s</b> have been removed!
            </div>""", unsafe_allow_html=True)
        st.session_state["additional_mapping_removed_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    #PURPLE HEADING - REMOVE FILE
    if st.session_state["ds_files_dict"]:
        with col1:
            st.write("_______")
            st.markdown("""<div class="purple-heading">
                    🗑️ Remove Mapping
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["additional_mapping_removed_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>mapping/s</b> have been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["additional_mapping_removed_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()

        with col1:
            col1a, col1b = st.columns([2,1])

        list_to_choose =  list(reversed(list(st.session_state["mk_g_mappings_dict"].keys())))
        if len(list_to_choose) > 1:
            list_to_choose.insert(0, "Select all")
        with col1a:
            mappings_to_remove_list = st.multiselect("🖱️ Select mappings:*",list_to_choose,
                key="key_mappings_to_remove_list")

        if "Select all" in mappings_to_remove_list:
            mappings_to_remove_list = list(st.session_state["mk_g_mappings_dict"].keys())
            with col1a:
                if len(mappings_to_remove_list) == 1:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ If you continue, the mapping <b style="color:#F63366;">
                            {utils.format_list_for_markdown(mappings_to_remove_list)}</b>
                            will be removed.
                        </div>""", unsafe_allow_html=True)
                elif len(mappings_to_remove_list) < utils.get_max_length_for_display()[5]:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ If you continue, the mappings <b style="color:#F63366;">
                            {utils.format_list_for_markdown(mappings_to_remove_list)}</b>
                            will be removed.
                        </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ If you continue, <b style="color:#F63366;">all mappings</b>
                            will be removed.
                        </div>""", unsafe_allow_html=True)
                st.write("")

                delete_all_mappings_checkbox = st.checkbox(
                ":gray-badge[⚠️ I am sure I want to delete all mappings]",
                key="key_delete_sm_class_checkbox")
                if delete_all_mappings_checkbox:
                    st.button("Remove", key="key_remove_additional_mapping_for_mk_button", on_click=remove_additional_mapping_for_mk)

        elif mappings_to_remove_list:
            with col1a:
                if len(mappings_to_remove_list) == 1:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ If you continue, the mapping <b style="color:#F63366;">
                            {utils.format_list_for_markdown(mappings_to_remove_list)}</b>
                            will be removed.
                        </div>""", unsafe_allow_html=True)
                elif len(mappings_to_remove_list) < utils.get_max_length_for_display()[5]:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ If you continue, the mappings <b style="color:#F63366;">
                            {utils.format_list_for_markdown(mappings_to_remove_list)}</b>
                            will be removed.
                        </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ If you continue, the <b style="color:#F63366;">selected files</b>
                            will be removed.
                        </div>""", unsafe_allow_html=True)
                st.write("")

                delete_mappings_checkbox = st.checkbox(
                ":gray-badge[⚠️ I am sure I want to delete the selected mapping/s]",
                key="key_delete_sm_class_checkbox")
                if delete_mappings_checkbox:
                    st.button("Remove", key="key_remove_additional_mapping_for_mk_button", on_click=remove_additional_mapping_for_mk)




#________________________________________________
# CHECK AND GO
with tab3:

    col1, col2 = st.columns([2,1.5])

    with col1:
        col1a, col1b = st.columns([2,1])

    with col2:
        col2a, col2b = st.columns([0.5, 2])

    # Show config content
    config_string = io.StringIO()
    st.session_state["mk_config"].write(config_string)
    if config_string.getvalue() != "":
        with col2b:
            st.markdown(f"```ini\n{config_string.getvalue()}\n```")

    # PURPLE HEADING - CHECK AND GO
    with col1:
        st.markdown("""<div class="purple-heading">
                ⚙️ Check and go
            </div>""", unsafe_allow_html=True)

        with col1:
            col1a, col1b = st.columns([2,1])

        if config_string.getvalue() == "":
            with col1a:
                st.markdown(f"""<div class="error-message">
                    ❌ <b>Config file is empty</b>.<small> You can enter data in the <b>Materialise pannel</b>.</small>
                </div>""", unsafe_allow_html=True)

        else:



            # List of all used mappings
            mk_used_mapping_list = []
            for section in st.session_state["mk_config"].sections():
                if section != "CONFIGURATION" and section != "DEFAULT":
                    mapping_path_list_string = st.session_state["mk_config"].get(section, "mappings", fallback="")
                    if mapping_path_list_string:
                        for mapping_path in mapping_path_list_string.split(","):
                            clean_path = mapping_path.strip()
                            g_label = os.path.splitext(os.path.basename(clean_path))[0]
                            if g_label not in mk_used_mapping_list:
                                mk_used_mapping_list.append(g_label)

            # List of all used sql databases
            mk_used_db_conn_list = []
            for section in st.session_state["mk_config"].sections():
                if section != "CONFIGURATION" and section != "DEFAULT":
                    used_db_url = st.session_state["mk_config"].get(section, "db_url", fallback="")
                    if used_db_url and used_db_url not in mk_used_db_conn_list:
                        mk_used_db_conn_list.append(used_db_url)

            # List of all used tabular data sources
            mk_used_tab_ds_list = []
            for section in st.session_state["mk_config"].sections():
                if section != "CONFIGURATION" and section != "DEFAULT":
                    file_path = st.session_state["mk_config"].get(section, "file_path", fallback="")
                    if file_path:
                        filename = os.path.basename(file_path)
                        if filename not in mk_used_tab_ds_list:
                            mk_used_tab_ds_list.append(filename)


            everything_ok_flag = True

            # Check g_mapping if used (additional mappings checked before adding)
            if st.session_state["g_label"] in mk_used_mapping_list:
                g_mapping_ok_flag = True
                if st.session_state["g_label"]:
                    inner_html = utils.check_g_mapping(st.session_state["g_mapping"])
                    if inner_html:
                        full_html = f"""<div class="error-message">
                                ❌ {inner_html}
                            </div>"""
                        everything_ok_flag = False
                    else:
                        full_html = f"""<div class="success-message">
                                ✔️ Mapping <b>{st.session_state["g_label"]}</b> complete.
                            </div>"""
                    with col1a:
                        st.markdown(full_html, unsafe_allow_html=True)

            # Message on additional mappings if used
            mk_used_additional_mapping_list = mk_used_mapping_list.copy()
            if st.session_state["g_label"] in mk_used_additional_mapping_list:
                mk_used_additional_mapping_list.remove(st.session_state["g_label"])
            if mk_used_additional_mapping_list:
                additional_mappings_list_for_display = utils.format_list_for_markdown(mk_used_additional_mapping_list)
                with col1a:
                    st.markdown(f"""<div class="success-message">
                            ✔️ Additional mappings ok:
                            <b><small>{additional_mappings_list_for_display}</small>
                        </div>""", unsafe_allow_html=True)

            # Check connections to db if used
            not_working_db_conn_list = []
            for connection_string in mk_used_db_conn_list:
                timeout = 3
                try:
                    engine = create_engine(connection_string, connect_args={"connect_timeout": timeout})
                    conn = engine.connect()
                except Exception as e:
                    not_working_db_conn_list.append(connection_string)
            if not not_working_db_conn_list:
                with col1a:
                    formatted_list = "<br>".join(mk_used_db_conn_list)
                    st.markdown(f"""<div class="success-message">
                        ✔️ All <b>connections to databases</b> are working:<br>
                        <small><b>{formatted_list}</b></small>
                    </div>""", unsafe_allow_html=True)
            else:
                everything_ok_flag = False
                with col1a:
                    if len(not_loaded_ds_list) == 1:
                        st.markdown(f"""<div class="error-message">
                                ❌ The connection to database <b>{utils.format_list_for_markdown(not_working_db_conn_list)}</b>
                                is not working.
                                <small>Please, check it in the <b>Manage Logical Sources</b> page.</small>
                            </div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""<div class="error-message">
                                ❌ The tabular data sources <b>{utils.format_list_for_markdown(not_working_db_conn_list)}</b>
                                are not working.
                                <small>Please, check them in the <b>Manage Logical Sources</b> page.</small>
                            </div>""", unsafe_allow_html=True)

            # Check all tabular sources are loaded
            not_loaded_ds_list = []
            for ds_filename in mk_used_tab_ds_list:
                if not ds_filename in st.session_state["ds_files_dict"]:
                    not_loaded_ds_list.append(ds_filename)

            if not not_loaded_ds_list:
                with col1a:
                    st.markdown(f"""<div class="success-message">
                            ✔️ All tabular data sources loaded:
                            <small><b>{utils.format_list_for_markdown(mk_used_tab_ds_list)}</b></small>
                        </div>""", unsafe_allow_html=True)
            else:
                everything_ok_flag = False
                with col1a:
                    if len(not_loaded_ds_list) == 1:
                        st.markdown(f"""<div class="error-message">
                                ❌ The tabular data source <b>{utils.format_list_for_markdown(not_loaded_ds_list)}</b>
                                is not loaded.
                                <small>Please, load it in the <b>Manage Logical Sources</b> page.</small>
                            </div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""<div class="error-message">
                                ❌ The tabular data sources <b>{utils.format_list_for_markdown(not_loaded_ds_list)}</b>
                                are not loaded.
                                <small>Please, load them in the <b>Manage Logical Sources</b> page.</small>
                            </div>""", unsafe_allow_html=True)


            if everything_ok_flag:

                with col1a:
                    st.write("")
                    st.button("Materialise")

                # Empty folder if it exists or create if it does not
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

                # Download g_mapping if used
                if st.session_state["g_label"] in mk_used_mapping_list:
                    # Download g_mapping to file
                    mapping_content = st.session_state["g_mapping"]
                    mapping_content_str = mapping_content.serialize(format="turtle")
                    filename = st.session_state["g_label"] + ".ttl"

                    file_path = os.path.join(temp_folder_path, filename)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(mapping_content_str)

                # Download additional mappings to file if used
                for g_label in mk_used_mapping_list:
                    if g_label != st.session_state["g_label"]:
                        g_mapping_file = st.session_state["mk_g_mappings_dict"][g_label]
                        ext = os.path.splitext(g_mapping_file.name)[1]
                        filename = g_label + ext
                        file_path = os.path.join(temp_folder_path, filename)
                        with open(file_path, "wb") as f:
                            f.write(g_mapping_file.getvalue())  # write file content as bytes

                # Download used tabular data sources
                for ds_filename in mk_used_tab_ds_list:
                    ds_file = st.session_state["ds_files_dict"][ds_filename]
                    filename = ds_file.name
                    file_path = os.path.join(temp_folder_path, filename)
                    with open(file_path, "wb") as f:
                        f.write(ds_file.getvalue())  # write file content as bytes



                #MATERIALISATION
                # Write config to a file
                config_path = os.path.join(os.getcwd(), "materialising_mapping_temp", "mk_config.ini")
                with open(config_path, "w", encoding="utf-8") as f:
                    st.session_state["mk_config"].write(f)
                # Run Morph-KGC with the config file path to materialise
                g = materialize(config_path)
                with col1a:
                    st.markdown(f"""<div class="success-message-flag">
                            ✅ Graph materialised with {len(g)} triples.
                        </div>""", unsafe_allow_html=True)


# output_dir	Directory where output files will be saved	./output/
# udfs	Path to Python file with user-defined functions	./functions/my_udfs.py
# logging_file	Path to save logs (default is stdout)	./logs/morph.log

# log_level	Logging verbosity level	INFO, DEBUG, ERROR
# mapping_partitioning	Strategy for partitioning mappings	MAXIMAL, PARTIAL-AGGREGATIONS
# na_values	Comma-separated values treated as NULL	null,NULL,nan     HERE
# only_printable_chars	Whether to filter out non-printable characters	yes, no
# literal_escaping_chars	Characters to preserve in percent encoding	/:
# infer_sql_datatypes	Whether to infer SQL datatypes	yes, no
# number_of_processes	Number of parallel processes to use	4

# output_kafka_server	Kafka server address (if using Kafka output)	localhost:9092
# output_kafka_topic	Kafka topic name (if using Kafka output)	rdf-triples

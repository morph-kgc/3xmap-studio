import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle
from rdflib.namespace import split_uri
import re
import configparser
import io

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

#TAB1
if "mk_config" not in st.session_state:
    st.session_state["mk_config"] = configparser.ConfigParser()
if "mk_db_connections_dict" not in st.session_state:
    st.session_state["mk_db_connections_dict"] = {}
if "mk_ds_files_dict" not in st.session_state:
    st.session_state["mk_ds_files_dict"] = {}
if "mk_g_mapping_dict" not in st.session_state:
    if st.session_state["g_label"]:
        st.session_state["mk_g_mapping_dict"] = {st.session_state["g_label"]: os.path.join(temp_folder_path, st.session_state["g_label"] + ".ttl")}
    else:
        st.session_state["mk_g_mapping_dict"] = {}
if "ds_for_mk_saved_ok_flag" not in st.session_state:
    st.session_state["ds_for_mk_saved_ok_flag"] = False
if "ds_for_mk_removed_ok_flag" not in st.session_state:
    st.session_state["ds_for_mk_removed_ok_flag"] = False

#define on_click functions
# TAB1
def save_sql_ds_for_mk():
    # add to config dict___________________
    st.session_state["mk_config"][mk_ds_label] = {"db_url": db_url, "db_user": db_user,
        "db_password": db_password, "db_type": db_type,
        "mappings": mk_mappings_str_for_sql}
    if schema:
        st.session_state["mk_config"][mk_ds_label]["schema"] = schema
    if driver_class:
        st.session_state["mk_config"][mk_ds_label]["driver_class"] = driver_class
    # store information________________________
    st.session_state["ds_for_mk_saved_ok_flag"] = True
    # reset values__________________________
    st.session_state["key_mk_ds_label"] = ""

def save_tab_ds_for_mk():
    # add to config dict___________________
    st.session_state["mk_config"][mk_ds_label] = {"file_path": file_path,
        "mappings": mk_mappings_str_for_tab}
    # store information________________________
    st.session_state["ds_for_mk_saved_ok_flag"] = True
    # reset values__________________________
    st.session_state["key_mk_ds_label"] = ""

def remove_ds_for_mk():
    # remove from config dict___________________
    for ds in ds_for_mk_to_remove_list:
        del st.session_state["mk_config"][ds]
    # store information________________________
    st.session_state["ds_for_mk_removed_ok_flag"] = True
    # reset values__________________________
    st.session_state["key_ds_for_mk_to_remove_list"] = []

def save_options_for_mk():
    #create section_______________
    if not st.session_state["mk_config"].has_section("Options"):
        st.session_state["mk_config"].add_section("Options")
    # add to config dict___________________
    if output_file:
        st.session_state["mk_config"]["Options"]["output_file"] = output_file
    else:
        if st.session_state["mk_config"].has_option("Options", "output_file"):
            st.session_state["mk_config"].remove_option("Options", "output_file")
    if output_format != "Select option":
        st.session_state["mk_config"]["Options"]["output_format"] = output_format
    else:
        if st.session_state["mk_config"].has_option("Options", "output_format"):
            st.session_state["mk_config"].remove_option("Options", "output_format")
    if log_level != "Select option":
        st.session_state["mk_config"]["Options"]["log_level"] = log_level
    else:
        if st.session_state["mk_config"].has_option("Options", "log_level"):
            st.session_state["mk_config"].remove_option("Options", "log_level")
    if mapping_partitioning != "Select option":
        st.session_state["mk_config"]["Options"]["mapping_partitioning"] = mapping_partitioning
    else:
        if st.session_state["mk_config"].has_option("Options", "mapping_partitioning"):
            st.session_state["mk_config"].remove_option("Options", "mapping_partitioning")
    if na_values:
        st.session_state["mk_config"]["Options"]["na_values"] = na_values
    else:
        if st.session_state["mk_config"].has_option("Options", "na_values"):
            st.session_state["mk_config"].remove_option("Options", "na_values")
    if only_printable_chars != "Select option":
        st.session_state["mk_config"]["Options"]["only_printable_chars"] = only_printable_chars
    else:
        if st.session_state["mk_config"].has_option("Options", "only_printable_chars"):
            st.session_state["mk_config"].remove_option("Options", "only_printable_chars")
    if safe_percent_encoding:
        st.session_state["mk_config"]["Options"]["safe_percent_encoding"] = safe_percent_encoding
    else:
        if st.session_state["mk_config"].has_option("Options", "safe_percent_encoding"):
            st.session_state["mk_config"].remove_option("Options", "safe_percent_encoding")
    if infer_sql_datatypes != "Select option":
        st.session_state["mk_config"]["Options"]["infer_sql_datatypes"] = infer_sql_datatypes
    else:
        if st.session_state["mk_config"].has_option("Options", "infer_sql_datatypes"):
            st.session_state["mk_config"].remove_option("Options", "infer_sql_datatypes")
    if number_of_processes:
        st.session_state["mk_config"]["Options"]["number_of_processes"] = number_of_processes
    else:
        if st.session_state["mk_config"].has_option("Options", "number_of_processes"):
            st.session_state["mk_config"].remove_option("Options", "number_of_processes")
    if output_kafka_server:
        st.session_state["mk_config"]["Options"]["output_kafka_server"] = output_kafka_server
    else:
        if st.session_state["mk_config"].has_option("Options", "output_kafka_server"):
            st.session_state["mk_config"].remove_option("Options", "output_kafka_server")
        if st.session_state["mk_config"].has_option("Options", "output_kafka_topic"):
            st.session_state["mk_config"].remove_option("Options", "output_kafka_topic")
    if output_kafka_server:
        if output_kafka_topic:
            st.session_state["mk_config"]["Options"]["output_kafka_topic"] = output_kafka_topic
        else:
            if st.session_state["mk_config"].has_option("Options", "output_kafka_topic"):
                st.session_state["mk_config"].remove_option("Options", "output_kafka_topic")
    # store information________________________
    st.session_state["options_for_mk_saved_ok_flag"] = True
    # reset values__________________________
    st.session_state["key_configure_options_for_mk_toggle"] = "🔒 Keep options"

def remove_options_for_mk():
    # remove from config dict___________________
    del st.session_state["mk_config"]["Options"]
    # store information________________________
    st.session_state["options_for_mk_removed_ok_flag"] = True
    # reset values__________________________
    st.session_state["key_configure_options_for_mk_toggle"] = "🚫 No options"



#____________________________________________________________
# PANELS OF THE PAGE (tabs)

tab1, tab2, tab3, tab4 = st.tabs(["Materialise", "Additional SQL Data Sources", "Additional Tabular Data Sources", "Additional Mappings"])


#________________________________________________
# MANAGE SQL DATA SOURCES
with tab1:

    col1, col2 = st.columns([2,1.5])

    with col1:
        col1a, col1b = st.columns([2,1])

    with col2:
        col2a, col2b = st.columns([0.5, 2])

    # Show config content
    with col2b:
        config_string = io.StringIO()
        if config_string:
            st.session_state["mk_config"].write(config_string)
            st.markdown(f"```ini\n{config_string.getvalue()}\n```")

    # PURPLE HEADING - ADD DATA SOURCE
    with col1:
        st.markdown("""<div class="purple-heading">
                📊 Configure Data Source
            </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([2,1])

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
        elif mk_ds_label.lower() == "options":
            with col1a:
                st.markdown(f"""<div class="error-message">
                    ❌ <b>"Options" label</b> is not allowed.
                    <small> You must pick a different label.</small>
                </div>""", unsafe_allow_html=True)
        elif mk_ds_label in st.session_state["mk_db_connections_dict"]:
            with col1a:
                st.markdown(f"""<div class="error-message">
                    ❌ Label <b>{mk_ds_label}</b> is already in use.
                    <small> You must pick a different label.</small>
                </div>""", unsafe_allow_html=True)

        else:

            with col1b:
                st.write("")
                mk_ds_type = st.radio("🖱️ Select an option:*", ["📊 SQL Database", "🛢️ Tabular data"],
                    label_visibility="collapsed", key="key_mk_ds_type")

            if mk_ds_type == "📊 SQL Database":

                with col1:
                    col1a, col1b = st.columns(2)
                with col1a:
                    db_connections_dict_complete = st.session_state["mk_db_connections_dict"] | st.session_state["db_connections_dict"]
                    list_to_choose = list(reversed(db_connections_dict_complete))
                    list_to_choose.insert(0, "Select data source")
                    mk_sql_ds = st.selectbox("🖱️ Select data source:*", list_to_choose,
                        key="key_mk_sql_ds")

                    if mk_sql_ds != "Select data source":
                        db_url = utils.get_jdbc_str(mk_sql_ds)
                        db_user = st.session_state["db_connections_dict"][mk_sql_ds][4]
                        db_password = st.session_state["db_connections_dict"][mk_sql_ds][5]
                        db_type = st.session_state["db_connections_dict"][mk_sql_ds][0]

                with col1b:
                    list_to_choose = list(reversed(list(st.session_state["mk_g_mapping_dict"])))
                    list_to_choose.insert(0, "Select all")
                    if st.session_state["g_label"]:
                        mk_mappings_list_for_sql = st.multiselect("🖱️ Select mappings:*", list_to_choose,
                            default=[st.session_state["g_label"]], key="key_mk_mappings_for_sql")
                    else:
                        mk_mappings_list_for_sql = st.multiselect("🖱️ Select mappings:*", list_to_choose,
                            key="key_mk_mappings_for_sql")

                mk_mappings_paths_list_for_sql = [st.session_state["mk_g_mapping_dict"][mapping]
                for mapping in mk_mappings_list_for_sql]
                mk_mappings_str_for_sql = ", ".join(mk_mappings_paths_list_for_sql)   # join into a comma-separated string for the config

                with col1a:
                    schema = st.text_input("⌨️ Enter schema (optional):")
                with col1b:
                    driver_class = st.text_input("⌨️ Enter driver class (optional):")

                if mk_sql_ds != "Select data source" and mk_mappings_list_for_sql:
                    with col1a:
                        st.button("Save", key="save_sql_ds_for_mk_button", on_click=save_sql_ds_for_mk)

            if mk_ds_type == "🛢️ Tabular data":

                with col1:
                    col1a, col1b = st.columns(2)
                with col1a:
                    ds_files_dict_complete = st.session_state["mk_ds_files_dict"] | st.session_state["ds_files_dict"]
                    list_to_choose = list(reversed(ds_files_dict_complete))
                    list_to_choose.insert(0, "Select data source")
                    mk_tab_ds_file = st.selectbox("🖱️ Select data source:*", list_to_choose,
                        key="key_mk_tab_ds_file")

                    if mk_tab_ds_file != "Select data source":
                        file_path = os.path.join(temp_folder_path, mk_tab_ds_file)

                with col1b:
                    list_to_choose = list(reversed(list(st.session_state["mk_g_mapping_dict"])))
                    list_to_choose.insert(0, "Select all")
                    if st.session_state["g_label"]:
                        mk_mappings_list_for_tab = st.multiselect("🖱️ Select mappings:*", list_to_choose,
                            default=[st.session_state["g_label"]], key="key_mk_mappings")
                    else:
                        mk_mappings_list_for_tab = st.multiselect("🖱️ Select mappings:*", list_to_choose,
                            key="key_mk_mappings")

                mk_mappings_paths_list_for_tab = [st.session_state["mk_g_mapping_dict"][mapping]
                for mapping in mk_mappings_list_for_tab]
                mk_mappings_str_for_tab = ", ".join(mk_mappings_paths_list_for_tab)   # join into a comma-separated string for the config

                if mk_tab_ds_file != "Select data source" and mk_mappings_list_for_tab:
                    with col1a:
                        st.button("Save", key="save_tab_ds_for_mk_button", on_click=save_tab_ds_for_mk)

    # PURPLE HEADING - REMOVE DATA SOURCE
    if list(st.session_state["mk_config"].keys()) != ["DEFAULT"]:
        with col1:
            st.write("______")
            st.markdown("""<div class="purple-heading">
                    🗑️ Remove Data Source
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a, col1b = st.columns([2,1])

        with col1a:
            list_to_choose = list(reversed(list(st.session_state["mk_config"])))
            list_to_choose.remove("DEFAULT")
            list_to_choose.insert(0, "Select all")

            ds_for_mk_to_remove_list = st.multiselect("🖱️ Select data sources:*", list_to_choose,
                key="key_ds_for_mk_to_remove_list")

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
    with col1:
        if st.session_state["mk_config"].has_section("Options"):
            configure_options_for_mk = st.radio("🖱️ Select an option:*",
                ["🔒 Keep options", "✏️ Modify options", "🗑️ Remove options"],
                horizontal=True, label_visibility="collapsed",
                key="key_configure_options_for_mk_toggle")
        else:
            configure_options_for_mk = st.radio("🖱️ Select an option:*",
                ["🚫 No options", "✏️ Add options"],
                horizontal=True, label_visibility="collapsed",
                key="key_configure_options_for_mk_toggle")

    if configure_options_for_mk in ["✏️ Modify options", "✏️ Add options"]:
        with col1:
            col1a, col1b = st.columns(2)

        with col1a:
            default_output_file = st.session_state["mk_config"].get("Options", "output_filename", fallback="")
            default_output_filename = os.path.basename(default_output_file)
            output_filename = st.text_input("⌨️ Enter output filename (optional):", value=default_output_filename,
                key="key_output_filename")
            output_file = os.path.join(temp_folder_path, output_filename) if output_filename else ""

        with col1b:
            default_output_format = st.session_state["mk_config"].get("Options", "output_format", fallback="Select option")
            list_to_choose = list(utils.get_g_mapping_file_formats_dict())
            list_to_choose.insert(0, "Select option")
            output_format = st.selectbox("🖱️ Select format (optional):", list_to_choose,
                index=list_to_choose.index(default_output_format), key="key_output_format")

        with col1:
            col1a, col1b = st.columns(2)
        with col1a:
            default_log_level = st.session_state["mk_config"].get("Options", "log_level", fallback="Select option")
            list_to_choose = ["ERROR", "WARNING", "INFO", "DEBUG"]
            list_to_choose.insert(0, "Select option")
            log_level = st.selectbox("🖱️ Select log level (optional):", list_to_choose,
                index=list_to_choose.index(default_log_level), key="key_log_level")

        with col1b:
            default_mapping_partitioning = st.session_state["mk_config"].get("Options", "mapping_partitioning", fallback="Select option")
            list_to_choose = ["MAXIMAL", "PARTIAL-AGGREGATIONS", "NONE"]
            list_to_choose.insert(0, "Select option")
            mapping_partitioning = st.selectbox("🖱️ Select mapping partitioning (optional):", list_to_choose,
                index=list_to_choose.index(default_mapping_partitioning), key="key_mapping_partitioning")

        with col1:
            col1a, col1b = st.columns(2)
        with col1a:
            default_na_values = st.session_state["mk_config"].get("Options", "na_values", fallback="")
            default_na_values_list = default_na_values.split(",") if default_na_values else []
            list_to_choose = ["null", "NULL", "nan", "NaN", "NA", "N/A", "#N/A", "missing", '""',
                "-", ".", "none", "None", "undefined", "#VALUE!", "#REF!", "#DIV/0!"]
            na_values_list = st.multiselect("🖱️ Select na values (optional)", list_to_choose,
                default=default_na_values_list, key="key_na_values")
            na_values = ",".join(na_values_list)

        with col1b:
            default_only_printable_chars = st.session_state["mk_config"].get("Options", "only_printable_chars", fallback="Select option")
            list_to_choose = ["Select option", "Yes", "No"]
            only_printable_chars = st.selectbox("🖱️ Only printable charts (optional):", list_to_choose,
                index=list_to_choose.index(default_only_printable_chars), key="key_only_printable_chars")

        with col1:
            col1a, col1b = st.columns(2)
        with col1a:
            default_safe_percent_encoding = st.session_state["mk_config"].get("Options", "safe_percent_encoding", fallback="")
            safe_percent_encoding = st.text_input("⌨️ Enter safe percent encodings (optional):",
                value=default_safe_percent_encoding, key="key_default_safe_percent_encoding")

        with col1b:
            default_infer_sql_datatypes = st.session_state["mk_config"].get("Options", "infer_sql_datatypes ", fallback="Select option")
            list_to_choose = ["Select option", "Yes", "No"]
            list_to_choose = ["Select option", "Yes", "No"]
            infer_sql_datatypes = st.selectbox("🖱️ Infer sql datatypes (optional):", list_to_choose,
                index=list_to_choose.index(default_infer_sql_datatypes), key="key_infer_sql_datatypes")

        with col1:
            col1a, col1b = st.columns(2)

        with col1a:
            default_number_of_processes = st.session_state["mk_config"].get("Options", "number_of_processes", fallback="")
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

        with col1:
            col1a, col1b = st.columns(2)
        with col1a:
            default_output_kafka_server = st.session_state["mk_config"].get("Options", "output_kafka_server", fallback="")
            output_kafka_server = st.text_input("⌨️ Output Kafka server (optional):",
                value=default_output_kafka_server, key="key_default_output_kafka_server")

        options_for_mk_ok_flag = True
        if output_kafka_server:
            with col1b:
                default_output_kafka_topic = st.session_state["mk_config"].get("Options", "output_kafka_topic", fallback="")
                output_kafka_topic = st.text_input("⌨️ Output Kafka topic (optional):",
                    value=default_output_kafka_topic, key="key_optput_kafka_topic")
                if not output_kafka_topic:
                    st.markdown(f"""<div class="error-message">
                        ❌ An <b>output Kafka topic</b> must be selected if
                        a <b>output Kafka server</b> is entered.
                    </div>""", unsafe_allow_html=True)
                    options_for_mk_ok_flag = False

        if options_for_mk_ok_flag:
            st.button("Save", key="key_save_options_for_mk_button", on_click=save_options_for_mk)

    if configure_options_for_mk == "🗑️ Remove options":
        with col1:
            remove_options_for_mk_checkbox = st.checkbox(
            ":gray-badge[⚠️ I am sure I want to remove the Options]",
            key="key_remove_options_for_mk_checkbox")
            if remove_options_for_mk_checkbox:
                st.button("Remove", on_click=remove_options_for_mk)


# output_dir	Directory where output files will be saved	./output/
# udfs	Path to Python file with user-defined functions	./functions/my_udfs.py
# logging_file	Path to save logs (default is stdout)	./logs/morph.log

# log_level	Logging verbosity level	INFO, DEBUG, ERROR
# mapping_partitioning	Strategy for partitioning mappings	MAXIMAL, PARTIAL-AGGREGATIONS
# na_values	Comma-separated values treated as NULL	null,NULL,nan     HERE
# only_printable_chars	Whether to filter out non-printable characters	yes, no
# safe_percent_encoding	Characters to preserve in percent encoding	/:
# infer_sql_datatypes	Whether to infer SQL datatypes	yes, no
# number_of_processes	Number of parallel processes to use	4

# output_kafka_server	Kafka server address (if using Kafka output)	localhost:9092
# output_kafka_topic	Kafka topic name (if using Kafka output)	rdf-triples

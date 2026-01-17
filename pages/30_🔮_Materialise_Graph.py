import configparser
import io
from morph_kgc import materialize
import os #for file navigation
from rdflib import Graph
import re
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
import time
import utils
import uuid

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
temp_folder_path = utils.get_folder_name(temp_materialisation_files=True)

# Define on_click functions--------------------------------------------
# TAB1
def reset_config_file():
    # reset variables__________________________
    st.session_state["mkgc_config"] = configparser.ConfigParser()
    st.session_state["mkgc_g_mappings_dict"] = {}
    st.session_state["materialised_g_mapping_file"] = None
    st.session_state["materialised_g_mapping"] = Graph()
    st.session_state["autoconfig_active_flag"] = False
    # store information_________________________
    st.session_state["config_file_reset_ok"] = True

def autoconfig():
    # reset config dict and additional mappings___________________
    st.session_state["mkgc_g_mappings_dict"] = {}
    st.session_state["mkgc_config"] = configparser.ConfigParser()
    # list to manage data source labels_______________
    base_label = "DataSource"
    used_data_source_labels_list = []
    # autoconfig SQL data sources_________________
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
    # autoconfig file data sources____________________
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

def enable_manual_config():
    # reset config dict
    st.session_state["mkgc_config"] = configparser.ConfigParser()
    # store information________________________
    st.session_state["autoconfig_active_flag"] = False
    st.session_state["manual_config_enabled_ok_flag"] = True

def materialise_graph():
    # Get info________________________________________
    mkgc_used_mapping_list = utils.get_all_mappings_used_for_materialisation()
    mkgc_used_tab_ds_list = utils.get_all_tab_ds_used_for_materialisation()

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

    # download used data files___________________________________
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
    config_path = os.path.join(os.getcwd(), temp_folder_path, "mkgc_config.ini")
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
        st.session_state["graph_materialised_ok_flag"] = "error"
        st.session_state["error_during_materialisation_flag"] = [True, e]
        st.session_state["materialised_g_mapping"] = True
        # delete temporal folder____________________________________
        for filename in os.listdir(temp_folder_path):       # delete all files inside the folder
            file_path = os.path.join(temp_folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        os.rmdir(temp_folder_path)      # remove the empty folder

def back_to_materialisation():
    # store information________________________
    st.session_state["materialised_g_mapping"] = False
    st.session_state["error_during_materialisation_flag"] = False

def save_sql_ds_for_mkgc():
    # add to config dict___________________
    st.session_state["mkgc_config"][mkgc_ds_label] = {"db_url": db_url,
        "mappings": mkgc_mappings_str}
    # store information________________________
    st.session_state["ds_for_mkgcgc_saved_ok_flag"] = True
    # reset fields__________________________
    st.session_state["key_mkgc_ds_label"] = ""

def save_tab_ds_for_mkgc():
    # add to config dict___________________
    st.session_state["mkgc_config"][mkgc_ds_label] = {"file_path": mkgc_tab_ds_file_path,
        "mappings": mkgc_mappings_str}
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
        st.session_state["key_mkgc_ds_type"] = "📊 Database"
    else:
        st.session_state["key_mkgc_ds_type"] = "🛢️ Data file"

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
    if output_format != "Default":
        st.session_state["mkgc_config"]["CONFIGURATION"]["output_format"] = output_format
    else:
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "output_format"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "output_format")
    if log_level != "Default":
        st.session_state["mkgc_config"]["CONFIGURATION"]["log_level"] = log_level
    else:
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "log_level"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "log_level")
    if mapping_partitioning != "Default":
        st.session_state["mkgc_config"]["CONFIGURATION"]["mapping_partitioning"] = mapping_partitioning
    else:
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "mapping_partitioning"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "mapping_partitioning")
    if na_values:
        st.session_state["mkgc_config"]["CONFIGURATION"]["na_values"] = na_values
    else:
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "na_values"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "na_values")
    if only_printable_chars != "Default":
        st.session_state["mkgc_config"]["CONFIGURATION"]["only_printable_chars"] = only_printable_chars
    else:
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "only_printable_chars"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "only_printable_chars")
    if literal_escaping_chars:
        st.session_state["mkgc_config"]["CONFIGURATION"]["literal_escaping_chars"] = literal_escaping_chars
    else:
        if st.session_state["mkgc_config"].has_option("CONFIGURATION", "literal_escaping_chars"):
            st.session_state["mkgc_config"].remove_option("CONFIGURATION", "literal_escaping_chars")
    if infer_sql_datatypes != "Default":
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

def save_mapping_for_mkgc_from_file():
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
    st.session_state["key_additional_mapping_source_option"] = "📁 File"

def remove_additional_mapping_for_mkgc():
    # remove________________________
    for mapping in mappings_to_remove_list:
        del st.session_state["mkgc_g_mappings_dict"][mapping]
    # store information________________________
    st.session_state["additional_mapping_removed_ok_flag"] = True
    # reset fields_______________________________
    st.session_state["key_additional_mapping_source_option"] = "📁 File"

# TAB2
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
tab1, tab2 = st.tabs(["Materialise", "Check issues"])

#_______________________________________________________________________________
# PANEL: MATERIALISE
with tab1:
    col1, col2, col2a, col2b = utils.get_panel_layout()

    # RIGHT COLUMN SUCCESS MESSAGES---------------------------------------------
    if st.session_state["autoconfig_generated_ok_flag"]:
        with col2b:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>Config file</b> has been auto-generated!
            </div>""", unsafe_allow_html=True)
        st.session_state["autoconfig_generated_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    if st.session_state["manual_config_enabled_ok_flag"]:
        with col2b:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ <b>Manual configuration</b> has been enabled!
            </div>""", unsafe_allow_html=True)
        st.session_state["manual_config_enabled_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    if st.session_state["config_file_reset_ok"]:
        with col2b:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>Config file</b> has been reset!
            </div>""", unsafe_allow_html=True)
        st.session_state["config_file_reset_ok"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()


    with col2b:
        utils.get_corner_status_message(mapping_info=True)

    # ERROR MESSAGE: NO DATA SOURCES AVAILABLE----------------------------------
    if not st.session_state["db_connections_dict"] and not st.session_state["ds_files_dict"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.markdown(f"""<div class="error-message">
                ❌ There are <b>no data sources</b> available.
                <small>You can add them in the <b>📊 SQL Databases</b>
                and the <b>🛢️ Data Files</b> pages.</small>
            </div>""", unsafe_allow_html=True)
        st.stop()

    # AUTOGENERATE THE CONFIG FILE (if auto mode active)------------------------
    if st.session_state["autoconfig_active_flag"]:
        utils.get_autoconfig_file()

    # RIGHT COLUMN: CONFIG FILE CONTENT-----------------------------------------
    with col2b:
        config_string = io.StringIO()
        st.session_state["mkgc_config"].write(config_string)
        if config_string.getvalue() != "":
            if st.session_state["autoconfig_active_flag"]:
                st.markdown(f"```ini\n{config_string.getvalue()}# Autogenerated\n```")
            else:
                st.markdown(f"```ini\n{config_string.getvalue()}\n```")
        else:
            st.markdown(f"```ini\n# Config file empty\n```")

    # RIGHT COLUMN: OPTIONS TO CHANGE TO AUTO/MANUAL AND RESET------------------
    with col2b:
        # MANUAL CONFIG ACTIVE
        if not st.session_state["autoconfig_active_flag"] and not st.session_state["materialised_g_mapping"]:
            with col2b:
                config_string = io.StringIO()
                st.session_state["mkgc_config"].write(config_string)
                if config_string.getvalue() != "":
                    reset_config_file_checkbox = st.checkbox("🔄 Reset Config file",
                        key="key_reset_config_file_checkbox")
                    if reset_config_file_checkbox:
                        st.markdown(f"""<div class="warning-message">
                            ⚠️ If you continue, the <b>Config file</b> will be cleared
                            and any configuration will be lost.
                            <small>Make sure you want to go ahead.</small>
                        </div>""", unsafe_allow_html=True)
                        st.button("Reset", key="key_reset_config_file_button", on_click=reset_config_file)

                back_to_autoconfig_checkbox = st.checkbox("🤖 Back to Autoconfig",
                    key="key_back_to_autoconfig_checkbox")
                if back_to_autoconfig_checkbox:
                    if config_string.getvalue() != "":
                        st.markdown(f"""<div class="warning-message">
                            ⚠️ A manual <b>Config file</b> already exists.
                            <small>If you continue, it will be <b>overwritten</b> with an auto-generated version.</small>
                        </div>""", unsafe_allow_html=True)
                        autoconfig_checkbox = st.checkbox(
                        "🔒 I am sure I want to overwrite the current Config file",
                        key="key_autooconfig_checkbox")
                        if autoconfig_checkbox:
                            st.button("AutoConfig", key="key_autoconfig_button", on_click=autoconfig)
                    else:
                        st.button("AutoConfig", key="key_autoconfig_button", on_click=autoconfig)

        # AUTOCONFIG ACTIVE
        elif st.session_state["autoconfig_active_flag"] and not st.session_state["materialised_g_mapping"]:
            enable_manual_configuration_checkbox = st.checkbox("✏️ Enable manual configuration",
                key="key_enable_manual_configuration_checkbox")
            if enable_manual_configuration_checkbox:
                st.button("Enable", key="key_enable_manual_config_button", on_click=enable_manual_config)

    # Check if there is at least one data source in Config file (used later)
    at_least_one_ds_in_config_file_flag = False
    for section in st.session_state["mkgc_config"].sections():
        if section != "CONFIGURATION" and section != "DEFAULT":
            at_least_one_ds_in_config_file_flag = True
            break

    # SUCCESS MESSAGES----------------------------------------------------------
    if st.session_state["graph_materialised_ok_flag"] == "error":
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="error-message">
                ❌ <b>Error during materialisation.</b>
            </div>""", unsafe_allow_html=True)
        st.session_state["graph_materialised_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
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

    # PURPLE HEADING: MATERIALISE-----------------------------------------------
    # If mapping not materialised yet and at least one ds in Config file
    if not st.session_state["materialised_g_mapping"]:
        if at_least_one_ds_in_config_file_flag:
            with col1:
                st.markdown("""<div class="purple-heading">
                        🔮 Materialise
                    </div>""", unsafe_allow_html=True)
                st.write("")

            with col1:
                col1a, col1b = st.columns([2,1])

            with col1a:
                if st.session_state["autoconfig_active_flag"]:
                    st.markdown(f"""<div class="gray-preview-message">
                        🤖 The <b>Config file</b> has been <b>automatically generated</b>.
                        <small> <b>Manual configuration</b> may be enabled.</small>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="gray-preview-message">
                        ✏️ The <b>Config file</b> has been <b>manually built</b>.<br>
                    </div>""", unsafe_allow_html=True)

                st.write("")
                st.button("Materialise", key="key_materialise_graph_button", on_click=materialise_graph)

            everything_ok_flag = utils.check_issues_for_materialisation()[0]
            if not everything_ok_flag:
                with col1b:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ <b>Potential error sources</b> detected for materialisation.
                        <small>Go to the 🕵️<b>Check Issues</b> pannel for more information.</small>
                    </div>""", unsafe_allow_html=True)

            if not st.session_state["autoconfig_active_flag"] and at_least_one_ds_in_config_file_flag:
                with col1:
                    st.write("_______")

    # PURPLE HEADING: EXPORT GRAPH----------------------------------------------
    # If graph materialised ok (no errors)
    elif not st.session_state["error_during_materialisation_flag"]:
        with col1:
            st.markdown("""<div class="purple-heading">
                    📤 Export graph
                </div>""", unsafe_allow_html=True)
            st.write("")
        with col1:
            col1a, col1b = st.columns([1,2])
        with col1a:
            download_extension_dict = utils.get_supported_formats(mapping=True, fun=True)
            download_format_list = list(download_extension_dict)
            download_format = st.selectbox("🖱️ Select format:*", download_format_list, key="key_download_format_selectbox")
        with col1b:
            download_extension = download_extension_dict[download_format]
            download_filename = st.text_input("⌨️ Enter filename (without extension):", key="key_download_filename_selectbox",
                value="materialised_graph")

            if "." in download_filename:
                st.markdown(f"""<div class="warning-message">
                        ⚠️ The filename <b style="color:#cc9a06;">{download_filename}</b>
                        seems to include an extension.
                    </div>""", unsafe_allow_html=True)

        with col1:
            col1a, col1b = st.columns([2,1])
        if download_filename:
            download_filename_complete = download_filename + download_extension if download_filename else ""
            if download_format == "🐢 Turtle":
                data = st.session_state["materialised_g_mapping_file"]
                mime_option = "text/turtle"
            else:
                g = Graph()
                g.parse(data=st.session_state["materialised_g_mapping_file"].getvalue().decode("utf-8"), format="turtle")
                if download_format == "3️⃣ N-Triples":
                    data = g.serialize(format="nt")
                    mime_option = "application/n-triples"
                elif download_format == "trig":
                    data = g.serialize(format="json-ld")
                    mime_option = "application/trig"
                elif download_format == "jsonld":
                    data = g.serialize(format="trig")
                mime_option = "application/ld+json"

            with col1a:
                st.write("")
                st.download_button(label="Export",
                    data=data,
                    file_name=download_filename_complete,
                    mime=mime_option)

            with col1a:
                back_to_materialisation_checkbox = st.checkbox("🔄 Back to materialisation", key="key_back_to_materialisation_checkbox")
                if back_to_materialisation_checkbox:
                    st.button("Back", key="key_back_to_materialisation_button", on_click=back_to_materialisation)

            with col1b:
                st.markdown(f"""<div class="info-message-blue">
                        ℹ️ Graph materialised with <b>{len(st.session_state["materialised_g_mapping"])} triples</b>.
                    </div>""", unsafe_allow_html=True)

    # PURPLE HEADING: MATERIALISATION ERROR-------------------------------------
    # If error raised during materialisation
    elif st.session_state["error_during_materialisation_flag"]:

        with col1:
            st.markdown("""<div class="purple-heading">
                    🛑 Materialisation Error
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            st.markdown(f"""<div class="error-message">
                    ❌ <b> Error during materialisation. </b>
                    <small><i><b>Full error:</b> {st.session_state["error_during_materialisation_flag"][1]}.</i></small>
                </div>""", unsafe_allow_html=True)
            st.write("")
            back_to_materialisation_checkbox = st.checkbox("🔄 Back to materialisation",
                key="key_back_to_materialisation_checkbox")
            if back_to_materialisation_checkbox:
                st.button("Back", key="key_back_to_materialisation_button", on_click=back_to_materialisation)


    # MANUAL MODE ACTIVE (SHOW SECTIONS TO BUILD THE CONFIG FILE)
    if not st.session_state["autoconfig_active_flag"] and not st.session_state["materialised_g_mapping"]:
        # PURPLE HEADING: CONFIGURE DATA SOURCE---------------------------------
        with col1:
            st.markdown("""<div class="purple-heading">
                    📊 Configure Data Source
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["ds_for_mkgcgc_saved_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>data source</b> has been saved!
                </div>""", unsafe_allow_html=True)
            st.session_state["ds_for_mkgcgc_saved_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        if st.session_state["ds_for_mkgcgc_removed_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>data source(s)</b> have been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["ds_for_mkgcgc_removed_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        with col1:
            col1a, col1b = st.columns([1.5,1])

        if not st.session_state["ds_files_dict"]:
            list_to_choose = ["📊 Database"]
        elif not st.session_state["db_connections_dict"]:
            list_to_choose = ["🛢️ Data file"]
        else:
            list_to_choose = ["📊 Database", "🛢️ Data file"]
        if list(st.session_state["mkgc_config"].keys()) != ["DEFAULT"] and list(st.session_state["mkgc_config"].keys()) != ["DEFAULT", "CONFIGURATION"]:
            list_to_choose.append("🗑️ Remove")    # if only "default" or "configuration" sections
        with col1b:
            if len(list_to_choose) == 1:
                st.write("")
                st.write("")
            if len(list_to_choose) == 2:
                st.write("")
            mkgc_ds_type = st.radio("🖱️ Select an option:*", list_to_choose,
                label_visibility="collapsed", key="key_mkgc_ds_type")

        # ADD DATA SOURCE (SQL OR FILE)
        if mkgc_ds_type != "🗑️ Remove":
            with col1a:
                mkgc_ds_label = st.text_input("⌨️ Enter data source label:*", key="key_mkgc_ds_label")

            if mkgc_ds_label:
                if mkgc_ds_label.lower() in (item.lower() for item in st.session_state["mkgc_config"]):
                    with col1a:
                        st.markdown(f"""<div class="error-message">
                            ❌ Label is <b>already in use</b>.
                            <small> You must pick a different label.</small>
                        </div>""", unsafe_allow_html=True)
                elif not utils.is_valid_label(mkgc_ds_label, hard=True, display=False):
                    with col1a:
                        utils.is_valid_label(mkgc_ds_label, hard=True)
                elif mkgc_ds_label.lower() == "configuration":
                    with col1a:
                        st.markdown(f"""<div class="error-message">
                            ❌ <b><i>CONFIGURATION</i></b> is not allowed as a label.
                            <small> You must pick a different label.</small>
                        </div>""", unsafe_allow_html=True)

                else:  # valid label

                    with col1:
                        col1a, col1b = st.columns(2)

                    # Select data source
                    if mkgc_ds_type == "📊 Database":

                        with col1a:
                            list_to_choose = sorted(st.session_state["db_connections_dict"])
                            list_to_choose.insert(0, "Select data source")
                            mkgc_sql_ds = st.selectbox("🖱️ Select data source:*", list_to_choose,
                                key="key_mkgc_sql_ds")

                            if mkgc_sql_ds != "Select data source":
                                db_url = utils.get_db_url_str(mkgc_sql_ds)
                                db_user = st.session_state["db_connections_dict"][mkgc_sql_ds][4]
                                db_password = st.session_state["db_connections_dict"][mkgc_sql_ds][5]
                                db_type = st.session_state["db_connections_dict"][mkgc_sql_ds][0]

                    if mkgc_ds_type == "🛢️ Data file":
                        with col1a:
                            list_to_choose = sorted(st.session_state["ds_files_dict"])
                            list_to_choose.insert(0, "Select data source")
                            mkgc_tab_ds_file = st.selectbox("🖱️ Select data source:*", list_to_choose,
                                key="key_mkgc_tab_ds_file")

                            if mkgc_tab_ds_file != "Select data source":
                                mkgc_tab_ds_file_path = os.path.join(temp_folder_path, mkgc_tab_ds_file)

                    # Select mappings (g_mapping default if exists)
                    with col1b:
                        mkgc_g_mapping_dict_complete = st.session_state["mkgc_g_mappings_dict"].copy()
                        if st.session_state["g_label"]:
                            mkgc_g_mapping_dict_complete[st.session_state["g_label"]] = st.session_state["g_mapping"]
                        list_to_choose = sorted(st.session_state["mkgc_g_mappings_dict"].keys())
                        if st.session_state["g_label"]:
                            list_to_choose.insert(0, st.session_state["g_label"])
                        if len(list_to_choose) > 1:
                            list_to_choose.insert(0, "Select all")
                        if st.session_state["g_label"]:
                            mkgc_mappings_list = st.multiselect("🖱️ Select mappings:*", list_to_choose,
                                default=[st.session_state["g_label"]], key="key_mkgc_mappings")
                        else:
                            mkgc_mappings_list = st.multiselect("🖱️ Select mappings:*", list_to_choose,
                                key="key_mkgc_mappings")

                        if not mkgc_g_mapping_dict_complete:
                            with col1:
                                st.markdown(f"""<div class="error-message">
                                    ❌ <b> No mappings available.</b>
                                    <small>You can <b>🏗️ Build a Mapping</b> using this application
                                    and/or include <b><small>➕</small> Additional Mappings</b> below.</small>
                                </div>""", unsafe_allow_html=True)

                    if "Select all" in mkgc_mappings_list:
                        mkgc_mappings_list = sorted(st.session_state["mkgc_g_mappings_dict"].keys())
                        if st.session_state["g_label"]:
                            mkgc_mappings_list.insert(0, st.session_state["g_label"])

                    # Get mapping paths in temp folder
                    mkgc_mappings_paths_list = []
                    for mapping_label in mkgc_mappings_list:
                        if mapping_label == st.session_state["g_label"]:
                            mkgc_mappings_paths_list.append(os.path.join(temp_folder_path, mapping_label + ".ttl"))
                        elif isinstance(st.session_state["mkgc_g_mappings_dict"][mapping_label], UploadedFile):
                            mkgc_mappings_paths_list.append(os.path.join(temp_folder_path, mapping_label + ".ttl"))
                        else:
                            mkgc_mappings_paths_list.append(st.session_state["mkgc_g_mappings_dict"][mapping_label])
                    mkgc_mappings_str = ",".join(mkgc_mappings_paths_list)   # join into a comma-separated string for the config

                    # Save data source
                    if mkgc_ds_type == "📊 Database":
                        if mkgc_sql_ds != "Select data source" and mkgc_mappings_list:
                            with col1a:
                                st.button("Save", key="save_sql_ds_for_mkgcgc_button", on_click=save_sql_ds_for_mkgc)

                    elif mkgc_ds_type == "🛢️ Data file":
                        if mkgc_tab_ds_file != "Select data source" and mkgc_mappings_list:
                            with col1a:
                                st.button("Save", key="save_tab_ds_for_mkgcgc_button", on_click=save_tab_ds_for_mkgc)

        # REMOVE DATA SOURCE (SQL OR FILE)
        if mkgc_ds_type == "🗑️ Remove":
            st.write("HI")
            with col1a:
                list_to_choose = sorted(st.session_state["mkgc_config"])
                list_to_choose.remove("DEFAULT")
                if "CONFIGURATION" in list_to_choose:
                    list_to_choose.remove("CONFIGURATION")
                if len(list_to_choose) > 1:
                    list_to_choose.insert(0, "Select all")
                ds_for_mkgcgc_to_remove_list = st.multiselect("🖱️ Select data sources:*", list_to_choose,
                    key="key_ds_for_mkgcgc_to_remove_list")

                if "Select all" in ds_for_mkgcgc_to_remove_list:
                    ds_for_mkgcgc_to_remove_list = sorted(st.session_state["mkgc_config"])
                    ds_for_mkgcgc_to_remove_list.remove("DEFAULT")
                    if "CONFIGURATION" in ds_for_mkgcgc_to_remove_list:
                        ds_for_mkgcgc_to_remove_list.remove("CONFIGURATION")
                    with col1b:
                        st.markdown(f"""<div class="warning-message">
                            ⚠️ You are deleting <b>all data sources</b>.
                            <small>Make sure you want to go ahead.</small>
                        </div>""", unsafe_allow_html=True)
                    with col1a:
                        remove_all_ds_checkbox = st.checkbox(
                        "🔒 I am sure I want to remove all data sources",
                        key="key_remove_all_ds_checkbox")
                        if remove_all_ds_checkbox:
                            st.button("Remove", key="remove_ds_for_mkgcgc_button", on_click=remove_ds_for_mkgc)

                elif ds_for_mkgcgc_to_remove_list:
                    with col1a:
                        remove_ds_checkbox = st.checkbox(
                        "🔒 I am sure I want to remove the selected data source(s)",
                        key="key_remove_ds_checkbox")
                        if remove_ds_checkbox:
                            st.button("Remove", key="remove_ds_for_mkgcgc_button", on_click=remove_ds_for_mkgc)


        # PURPLE HEADING: CONFIGURE OPTIONS-------------------------------------
        with col1:
            st.write("_______")
            st.markdown("""<div class="purple-heading">
                    ⚙️ Configure Options
                </div>""", unsafe_allow_html=True)

        if st.session_state["configuration_for_mkgcgc_saved_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>configuration</b> has been saved!
                </div>""", unsafe_allow_html=True)
            st.session_state["configuration_for_mkgcgc_saved_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        if st.session_state["configuration_for_mkgcgc_removed_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
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

            # Filename
            with col1a:
                default_output_file = st.session_state["mkgc_config"].get("CONFIGURATION", "output_file", fallback="")
                default_output_filename = os.path.basename(default_output_file)
                output_filename = st.text_input("⌨️ Enter output filename: ᵒᵖᵗ", value=default_output_filename,
                    key="key_output_filename")

                if output_filename:
                    excluded_characters = r"[\\/:*?\"<>|]"
                    windows_reserved_names = ["CON", "PRN", "AUX", "NUL",
                        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
                        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]
                    options_for_mkgcgc_ok_flag = utils.is_valid_filename(output_filename, extension=True)
                    if options_for_mkgcgc_ok_flag and not os.path.splitext(output_filename)[1]:
                        st.markdown(f"""<div class="warning-message">
                            ⚠️ <b>No extension</b> in filename.
                            <small> Using an extension is recommended (matching the file format if given).</small>
                        </div>""", unsafe_allow_html=True)
                output_file = os.path.join(temp_folder_path, output_filename) if output_filename else ""

            # Output format
            with col1b:
                default_output_format = st.session_state["mkgc_config"].get("CONFIGURATION", "output_format", fallback="Default")
                list_to_choose = ["Default", "N-TRIPLES", "N-QUADS"]
                output_format = st.selectbox("🖱️ Select format: ᵒᵖᵗ", list_to_choose,
                    index=list_to_choose.index(default_output_format), key="key_output_format")

            with col1:
                col1a, col1b = st.columns(2)

            # Log level
            with col1a:
                default_log_level = st.session_state["mkgc_config"].get("CONFIGURATION", "log_level", fallback="Default")
                list_to_choose = ["INFO", "DEBUG","WARNING", "ERROR", "CRITICAL", "NOTSET"]
                list_to_choose.insert(0, "Default")
                log_level = st.selectbox("🖱️ Select logging level: ᵒᵖᵗ", list_to_choose,
                    index=list_to_choose.index(default_log_level), key="key_log_level")

            # Mapping partitioning
            with col1b:
                default_mapping_partitioning = st.session_state["mkgc_config"].get("CONFIGURATION", "mapping_partitioning", fallback="Default")
                list_to_choose = ["MAXIMAL", "PARTIAL-AGGREGATIONS", "off"]
                list_to_choose.insert(0, "Default")
                mapping_partitioning = st.selectbox("🖱️ Select mapping partitioning: ᵒᵖᵗ", list_to_choose,
                    index=list_to_choose.index(default_mapping_partitioning), key="key_mapping_partitioning")

            with col1:
                col1a, col1b = st.columns(2)

            # NA values
            with col1a:
                default_na_values = st.session_state["mkgc_config"].get("CONFIGURATION", "na_values", fallback="")
                default_na_values_list = default_na_values.split(",") if default_na_values else []
                list_to_choose = ["null", "NULL", "nan", "NaN", "NA", "N/A", "#N/A", "missing", '""',
                    "-", ".", "none", "None", "undefined", "#VALUE!", "#REF!", "#DIV/0!"]
                na_values_list = st.multiselect("🖱️ Select NA values: ᵒᵖᵗ", list_to_choose,
                    default=default_na_values_list, key="key_na_values")
                na_values = ",".join(na_values_list)

            # Only printable chars option
            with col1b:
                default_only_printable_chars = st.session_state["mkgc_config"].get("CONFIGURATION", "only_printable_chars", fallback="Default")
                list_to_choose = ["Default", "Yes", "No"]
                only_printable_chars = st.selectbox("🖱️ Only printable charts: ᵒᵖᵗ", list_to_choose,
                    index=list_to_choose.index(default_only_printable_chars), key="key_only_printable_chars")

            with col1:
                col1a, col1b = st.columns(2)

            # Safe percent encodings
            with col1a:
                default_literal_escaping_chars = st.session_state["mkgc_config"].get("CONFIGURATION", "literal_escaping_chars", fallback="")
                default_literal_escaping_chars_list = list(default_literal_escaping_chars) if default_literal_escaping_chars else []
                list_to_choose = ["Select all", "!", "#", "$", "&", "'", "(", ")", "*", "+", ",", "/", ":", ";", "=", "?", "@", "[", "]"]
                literal_escaping_chars_list = st.multiselect("🖱️ Select safe percent encodings: ᵒᵖᵗ", list_to_choose,
                    default=default_literal_escaping_chars_list, key="key_literal_escaping_chars")
                if "Select all" in literal_escaping_chars_list:
                    literal_escaping_chars_list = ["!", "#", "$", "&", "'", "(", ")", "*", "+", ",", "/", ":", ";", "=", "?", "@", "[", "]"]
                literal_escaping_chars = "".join(literal_escaping_chars_list)

            # Infer datatypes option
            with col1b:
                default_infer_sql_datatypes = st.session_state["mkgc_config"].get("CONFIGURATION", "infer_sql_datatypes ", fallback="Default")
                list_to_choose = ["Default", "Yes", "No"]
                list_to_choose = ["Default", "Yes", "No"]
                infer_sql_datatypes = st.selectbox("🖱️ Infer sql datatypes: ᵒᵖᵗ", list_to_choose,
                    index=list_to_choose.index(default_infer_sql_datatypes), key="key_infer_sql_datatypes")

            with col1:
                col1a, col1b = st.columns(2)

            # Number of processes
            with col1a:
                default_number_of_processes = st.session_state["mkgc_config"].get("CONFIGURATION", "number_of_processes", fallback="")
                number_of_processes = st.text_input("⌨️ Enter number of processes: ᵒᵖᵗ",
                    value = default_number_of_processes, key="key_number_of_processes")
                if number_of_processes:
                    if not number_of_processes.isdigit():
                        st.markdown(f"""<div class="error-message">
                            ❌ <b>Invalid input</b>. <small>Only <b>positive integers</b> allowed.</small>
                        </div>""", unsafe_allow_html=True)
                        options_for_mkgcgc_ok_flag = False

            # Output Kafka server
            with col1b:
                default_output_kafka_server = st.session_state["mkgc_config"].get("CONFIGURATION", "output_kafka_server", fallback="")
                output_kafka_server = st.text_input("⌨️ Output Kafka server: ᵒᵖᵗ",
                    value=default_output_kafka_server, key="key_default_output_kafka_server")
                output_kafka_server_ok_flag = True
                pattern = r"^[a-zA-Z0-9.-]+:\d+$"
                if output_kafka_server and not re.match(pattern, output_kafka_server.strip()):
                    st.markdown(f"""<div class="error-message">
                        ❌ <b>Invalid Kafka server</b>.
                        <small> Must be in the form <b><i>host:port</i></b>.</small>
                    </div>""", unsafe_allow_html=True)
                    options_for_mkgcgc_ok_flag = False
                    output_kafka_server_ok_flag = False
                    output_kafka_server = ""


            with col1:
                col1a, col1b = st.columns(2)

            # Output Kafka topic
            if output_kafka_server:
                with col1b:
                    default_output_kafka_topic = st.session_state["mkgc_config"].get("CONFIGURATION", "output_kafka_topic", fallback="")
                    output_kafka_topic = st.text_input("⌨️ Output Kafka topic: ᵒᵖᵗ",
                        value=default_output_kafka_topic, key="key_optput_kafka_topic")
                    if not output_kafka_topic:
                        st.markdown(f"""<div class="error-message">
                            ❌ An <b>output Kafka topic</b> must be selected <small>if
                            an <b>output Kafka server</b> is entered.</small>
                        </div>""", unsafe_allow_html=True)
                        options_for_mkgcgc_ok_flag = False
                    elif re.search(r"\s", output_kafka_topic):
                        st.markdown(f"""<div class="error-message">
                            ❌ <b>Invalid Kafka topic</b>.
                            <small> Make sure it does not contain any <b>spaces</b>.</small>
                        </div>""", unsafe_allow_html=True)
                        options_for_mkgcgc_ok_flag = False
                    else:
                        kafka_topic_forbidden_chars = " /\\:;\"'<>[]{}|^`~?*&%#@=+,\t\n\r"
                        pattern = "[" + re.escape(kafka_topic_forbidden_chars) + "]"
                        if re.search(pattern, output_kafka_topic):
                            st.markdown(f"""<div class="error-message">
                                ❌ <b>Forbidden character</b> in output Kafka topic.
                                <small> Please pick a valid topic.</small>
                            </div>""", unsafe_allow_html=True)
                            options_for_mkgcgc_ok_flag = False

            if output_kafka_server and output_kafka_topic:
                with col1b:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ <b>No validation provided</b>.
                        <small> Please verify the Kafka server connection and ensure a valid topic name.</small>
                    </div>""", unsafe_allow_html=True)

            # Save
            if options_for_mkgcgc_ok_flag:
                with col1a:
                    st.button("Save", key="key_save_options_for_mkgcgc_button", on_click=save_options_for_mkgc)

        if configure_options_for_mkgc == "🗑️ Remove options":
            with col1:
                st.button("Remove", on_click=remove_options_for_mkgc)


        # PURPLE HEADING: ADDITIONAL MAPPINGS-----------------------------------
        with col1:
            st.write("_______")
            st.markdown("""<div class="purple-heading">
                    ➕ Additional Mappings
                </div>""", unsafe_allow_html=True)

        if st.session_state["additional_mapping_added_ok_flag"]:
            with col1:
                col1a, colb = st.columns([2,1])
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
                    ✅ The <b>additional mapping(s)</b> have been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["additional_mapping_removed_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        with col1:
            col1a, col1b = st.columns([1.5,1])

        # List of all used mappings (only allow to remove mapping if not used)
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


        if additional_mapping_source_option in ["📁 File", "🌐 URL"]:
            with col1a:
                additional_mapping_label = st.text_input("⌨️ Enter mapping label:*", key="key_additional_mapping_label")

                if additional_mapping_label:
                    if (additional_mapping_label.lower() in
                        (key.lower() for key in st.session_state["mkgc_g_mappings_dict"])
                        or additional_mapping_label.lower() == st.session_state["g_label"].lower()):
                        st.markdown(f"""<div class="error-message">
                            ❌ Label <b>{additional_mapping_label}</b> is already in use.
                            <small>Please pick a different label.</small>
                        </div>""", unsafe_allow_html=True)
                        additional_mapping_label = ""
                    elif not utils.is_valid_label(additional_mapping_label):
                        additional_mapping_label = ""

            with col1:
                col1a, col1b = st.columns([2,1])

        if additional_mapping_source_option == "📁 File" and additional_mapping_label:
            with col1a:
                mapping_format_list = sorted(utils.get_supported_formats(mapping=True).values())
                uploaded_mapping = st.file_uploader(f"""🖱️ Upload mapping file:*""",
                    type=mapping_format_list, key=st.session_state["key_mapping_uploader"])

            if uploaded_mapping:
                with col1b:
                    st.write("")
                    st.write("")
                    uploaded_mapping_ok_flag = utils.load_mapping_from_file(uploaded_mapping)
                with col1a:
                    if uploaded_mapping_ok_flag:
                        st.button("Save", key="key_save_mapping_for_mkgcgc_from_file_button",
                            on_click=save_mapping_for_mkgc_from_file)

        elif additional_mapping_source_option == "🌐 URL" and additional_mapping_label:
            with col1a:
                mapping_url = st.text_input("⌨️ Enter mapping URL:*", key="key_mapping_url")

            if mapping_url:
                with col1a:
                    mapping_url_ok_flag = utils.load_mapping_from_link(mapping_url)
                if mapping_url_ok_flag:
                    with col1a:
                        st.button("Save", key="key_save_mapping_for_mkgcgc_from_url_button",
                            on_click=save_mapping_for_mkgcgc_from_url)

        if additional_mapping_source_option == "🗑️ Remove":

            list_to_choose =  sorted(mkgc_not_used_mapping_list)
            if len(list_to_choose) > 1:
                list_to_choose.insert(0, "Select all")
            with col1a:
                mappings_to_remove_list = st.multiselect("🖱️ Select mappings to remove:*", list_to_choose,
                    key="key_mappings_to_remove_list")

            if len(mkgc_not_used_mapping_list) < len(st.session_state["mkgc_g_mappings_dict"]):
                with col1b:
                    st.markdown(f"""<div class="info-message-gray">
                            💤 Only <b>unused mappings</b> are allowed to be removed.
                        </div>""", unsafe_allow_html=True)

            if "Select all" in mappings_to_remove_list:
                mappings_to_remove_list = list(st.session_state["mkgc_g_mappings_dict"].keys())
                with col1b:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ If you continue, <b>all unused mappings ({len(mkgc_not_used_mapping_list)})</b>
                            will be removed. <small>Make sure you want to go ahead.</small>
                        </div>""", unsafe_allow_html=True)

                with col1a:
                    delete_all_mappings_checkbox = st.checkbox(
                    "🔒 I am sure I want to delete all mappings",
                    key="key_delete_all_mappings_checkbox")
                    if delete_all_mappings_checkbox:
                        st.button("Remove", key="key_remove_additional_mapping_for_mkgcgc_button",
                            on_click=remove_additional_mapping_for_mkgc)

            elif mappings_to_remove_list:
                with col1a:
                    delete_mappings_checkbox = st.checkbox(
                    "🔒 I am sure I want to delete the selected mapping(s)",
                    key="key_delete_mappings_checkbox")
                    if delete_mappings_checkbox:
                        st.button("Remove", key="key_remove_additional_mapping_for_mkgcgc_button",
                            on_click=remove_additional_mapping_for_mkgc)


#_______________________________________________________________________________
# PANEL: CHECK ISSUES
with tab2:
    col1, col2, col2a, col2b = utils.get_panel_layout()
    with col2b:
        utils.get_corner_status_message(mapping_info=True)

    # ERROR MESSAGE: NO DATA SOURCES AVAILABLE----------------------------------
    if not st.session_state["db_connections_dict"] and not st.session_state["ds_files_dict"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.markdown(f"""<div class="error-message">
                ❌ There are <b>no data sources</b> available.
                <small>You can add them in the <b>📊 SQL Databases</b>
                and the <b>🛢️ Data Files</b> pages.</small>
            </div>""", unsafe_allow_html=True)
        st.stop()

    # RIGHT COLUMN: CONFIG FILE CONTENT-----------------------------------------
    with col2b:
        config_string = io.StringIO()
        st.session_state["mkgc_config"].write(config_string)
        if config_string.getvalue() != "":
            if st.session_state["autoconfig_active_flag"]:
                st.markdown(f"```ini\n{config_string.getvalue()}# Autogenerated\n```")
            else:
                st.markdown(f"```ini\n{config_string.getvalue()}\n```")
        else:
            st.markdown(f"```ini\n# Config file empty\n```")

    # PURPLE HEADING: CHECK ISSUES----------------------------------------------
    with col1:
        st.markdown("""<div class="purple-heading">
                🕵️ Check issues
            </div>""", unsafe_allow_html=True)

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

    # CONFIG FILE EMPTY
    if config_string.getvalue() == "":
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.markdown(f"""<div class="error-message">
                ❌ <b>Config file is empty</b>.<small> You can auto-generate it
                or manually build it in the <b>Materialise</b> panel.</small>
            </div>""", unsafe_allow_html=True)

    # WARNING/SUCCESS MESSAGES
    else:
        everything_ok_flag, inner_html_success, inner_html_error, info_table_html = utils.check_issues_for_materialisation()
        with col1:
            messages = []
            if inner_html_error:
                messages.append(f"""⚠️ <b>Potential materialisation error sources:</b><br>
                <div style='margin-left: 1.3em;'><small>{inner_html_error}</small></div>""")
            if inner_html_success:
                messages.append(f"""✔️ <b>Good prospects:</b><br>
                <div style='margin-left: 1.3em;'><small>{inner_html_success}</small></div>""")

            separator = "<hr style='border:0; border-top:1px solid #999; margin:10px 0;'>"
            final_message = separator.join(messages)
            if final_message:
                st.write("")
                st.markdown(f"""<div class="gray-preview-message" style="font-size:13px; line-height:1.5;">
                        {final_message}
                    </div>""", unsafe_allow_html=True)
                st.write("")

        # SHOW INFO TABLE
        with col1:
            st.markdown(f"""<div class="gray-preview-message" style="font-size:13px; line-height:1.2;">
                {info_table_html}
                </div>
            """, unsafe_allow_html=True)

        # CLEAN MAPPING
        (g_mapping_complete_flag, heading_html, inner_html, tm_wo_sm_list, tm_wo_pom_list,
            pom_wo_om_list, pom_wo_predicate_list) = utils.check_g_mapping(st.session_state["g_mapping"])

        if not g_mapping_complete_flag:
            tm_to_clean_list = list(set(tm_wo_sm_list).union(tm_wo_pom_list))
            pom_to_clean_list = list(set(pom_wo_om_list).union(pom_wo_predicate_list))

            with col1:
                col1a, col1b = st.columns([3,1])

            with col1a:
                st.write("")
                st.markdown(f"""<div class="gray-preview-message" style="font-size:13px; line-height:1.3;">
                        {heading_html + inner_html}
                    </div>""", unsafe_allow_html=True)
                st.write("")

            with col1:
                clean_g_mapping_checkbox = st.checkbox(
                f"""🧹 Clean mapping {st.session_state["g_label"]}""",
                key="key_clean_g_mapping_checkbox")

                if clean_g_mapping_checkbox:
                    st.button("Clean", key="key_clean_g_mapping_button", on_click=clean_g_mapping)

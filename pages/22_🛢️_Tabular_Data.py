import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace
import utils
import time
import pandas as pd
import psycopg
import pymysql    # another option mysql-connector-python
import oracledb
import pyodbc
import uuid   # to handle uploader keys
import io
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

#define on_click functions--------------------------------------------
# TAB1
def save_ds_file():
    # save file
    st.session_state["ds_files_dict"][ds_file.name] = ds_file
    # store information_________________
    st.session_state["ds_file_saved_ok_flag"] = True
    # reset fields_______________________
    st.session_state["key_ds_uploader"] = str(uuid.uuid4())

def save_large_ds_file():
    # save file________________________________
    st.session_state["ds_files_dict"][ds_large_filename] = ds_file
    # store information_________________
    st.session_state["ds_file_saved_ok_flag"] = True
    # reset fields_______________________
    st.session_state["key_large_file_checkbox"] = False

def remove_file():
    # delete files________________
    for file in ds_files_to_remove_list:
        del st.session_state["ds_files_dict"][file]
    # store information________________
    st.session_state["ds_file_removed_ok_flag"] = True  # for success message
    # reset fields_____________________
    st.session_state["key_ds_files_to_remove_list"] = []



# START PAGE_____________________________________________________________________

#____________________________________________________________
# PANELS OF THE PAGE (tabs)

tab1, tab2 = st.tabs(["Load File", "Display Data"])


#________________________________________________
# MANAGE TABULAR DATA SOURCES
with tab1:

    col1, col2 = st.columns([2,1.5])

    with col1:
        col1a, col1b = st.columns([2,1])

    with col2:
        col2a, col2b = st.columns([0.5, 2])

    with col2b:
        st.write("")
        st.write("")


    rows = []
    ds_files = list(st.session_state["ds_files_dict"].items())
    ds_files.reverse()

    for filename, file_obj in ds_files:
        base_name = filename.split(".")[0]
        file_format = filename.split(".")[-1]

        if hasattr(file_obj, "size"):
            # Streamlit UploadedFile
            file_size_kb = file_obj.size / 1024
        elif hasattr(file_obj, "fileno"):
            # File object from open(path, "rb")
            file_size_kb = os.fstat(file_obj.fileno()).st_size / 1024
        else:
            file_size_kb = None  # Unknown format

        if not file_size_kb:
            file_size = None
        elif file_size_kb < 1:
            file_size = f"""{int(file_size_kb*1024)} bytes"""
        elif file_size_kb < 1024:
            file_size = f"""{int(file_size_kb)} kB"""
        else:
            file_size = f"""{int(file_size_kb/1024)} MB"""

        row = {"Filename": base_name, "Format": file_format,
            "Size": file_size if file_size_kb is not None else "N/A"}
        rows.append(row)

        db_connections_df = pd.DataFrame(rows)
        last_added_db_connections_df = db_connections_df.head(utils.get_max_length_for_display()[1])

    with col2b:
        max_length = utils.get_max_length_for_display()[1]   # max number of connections to show directly
        if st.session_state["ds_files_dict"]:
            if len(st.session_state["ds_files_dict"]) < max_length:
                st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                        🔎 uploaded files
                    </div>""", unsafe_allow_html=True)
                st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                        🔎 last uploaded files
                    </div>""", unsafe_allow_html=True)
                st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        (complete list below)
                    </div>""", unsafe_allow_html=True)
            st.dataframe(last_added_db_connections_df, hide_index=True)

        #Option to show all connections (if too many)
        if st.session_state["ds_files_dict"] and len(st.session_state["ds_files_dict"]) > max_length:
            with st.expander("🔎 Show all files"):
                st.write("")
                st.dataframe(db_connections_df, hide_index=True)


    #PURPLE HEADING - UPLOAD FILE
    with col1:
        st.write("")
        st.markdown("""<div class="purple-heading">
                📁 Upload File <small>(or Update)</small>
            </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([2,1])

    if st.session_state["ds_file_saved_ok_flag"]:
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>data source file</b> has been saved!
            </div>""", unsafe_allow_html=True)
        st.session_state["ds_file_saved_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    ds_allowed_formats = utils.get_ds_allowed_tab_formats()            #data source for the TriplesMap
    with col1a:
        ds_file = st.file_uploader(f"""🖱️ Upload data source file:*""",
            type=ds_allowed_formats, key=st.session_state["key_ds_uploader"])

        if ds_file:
            try:
                columns_df = utils.read_tab_file_unsaved(ds_file)

                if ds_file.name in st.session_state["ds_files_dict"]:
                    st.write("")
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ File <b>{ds_file.name}</b> is already loaded.<br>
                        <small>If you continue its content will be updated.</small>
                    </div>""", unsafe_allow_html=True)
                    st.write("")
                    update_file_checkbox = st.checkbox(
                    "🔒 I am sure I want to update the file",
                    key="key_update_file_checkbox")
                    if update_file_checkbox:
                        st.button("Save", key="key_save_ds_file_button", on_click=save_ds_file)

                else:
                    st.button("Save", key="key_save_ds_file_button", on_click=save_ds_file)

            except Exception as e:    # empty file
                with col1a:
                    st.markdown(f"""<div class="error-message">
                        ❌ The file <b>{ds_file.name}</b> appears to be empty or corrupted. Please load a valid file. {e}
                    </div>""", unsafe_allow_html=True)
                    st.write("")


    if not ds_file:
        with col1b:
            st.write("")
            st.write("")
            large_file_checkbox = st.checkbox(
                "🐘 My file is larger than 200 MB",
                key="key_large_file_checkbox")

        if large_file_checkbox:

            folder_name = utils.get_ds_folder_name()
            folder_path = os.path.join(os.getcwd(), folder_name)

            with col1:
                col1a, col1b = st.columns([2,1])

            if not os.path.isdir(folder_path):
                with col1b:
                    st.write("")
                    st.markdown(f"""<div class="error-message">
                            ❌ Folder <b>{folder_name}</b> does not exist. <small>Please,
                            create it within the main folder and <b>add your file</b> to it</small>.
                        </div>""", unsafe_allow_html=True)

            else:
                tab_files = [f for f in os.listdir(folder_path)
                    if os.path.isfile(os.path.join(folder_path, f)) and any(f.endswith(ext)
                    for ext in ds_allowed_formats)]


                if not tab_files:
                    with col1b:
                        st.write("")
                        st.markdown(f"""<div class="error-message">
                                ❌ The folder <b>{folder_name}</b> is empty. <small>Please,
                                <b>add your file</b> to it</small>.
                            </div>""", unsafe_allow_html=True)

                else:
                    with col1b:
                        st.write("")
                        st.markdown(f"""<div class="info-message-blue">
                                ℹ️ <b>Add your file</b> to the <b style="color:#F63366;">
                                {folder_name}</b> folder to select it
                                from the list below <small><b>(do not use uploader)</b></small>.
                            </span></div>""", unsafe_allow_html=True)
                    list_to_choose = tab_files
                    list_to_choose.insert(0, "Select file")
                    with col1a:
                        ds_large_filename = st.selectbox("🖱️ Select file*:", tab_files)

                    if ds_large_filename != "Select file":

                        ds_file_path = os.path.join(folder_path, ds_large_filename)
                        ds_file = open(ds_file_path, "rb")
                        try:
                            columns_df = utils.read_tab_file_unsaved(ds_file)

                            if ds_large_filename in st.session_state["ds_files_dict"]:
                                with col1a:
                                    st.markdown(f"""<div class="warning-message">
                                        ⚠️ File <b>{ds_large_filename}</b> is already loaded.
                                        <small>If you continue, its content <b>will be updated</b>.</small>
                                    </div>""", unsafe_allow_html=True)
                                    update_large_file_checkbox = st.checkbox(
                                    "🔒 I am sure I want to update the file",
                                    key="key_update_large_file_checkbox")
                                    if update_large_file_checkbox:
                                        st.button("Save", key="key_save_large_ds_file_button", on_click=save_large_ds_file)
                            else:
                                with col1a:
                                    st.button("Save", key="key_save_large_ds_file_button",
                                    on_click=save_large_ds_file)

                        except:    # empty file
                            with col1a:
                                st.markdown(f"""<div class="error-message">
                                    ❌ The file <b>{ds_large_filename}</b> appears to be empty or corrupted. Please select a valid file.
                                </div>""", unsafe_allow_html=True)
                                st.write("")


    if not st.session_state["ds_files_dict"] and st.session_state["ds_file_removed_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>data source file/s</b> have been removed!
            </div>""", unsafe_allow_html=True)
        st.session_state["ds_file_removed_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    #PURPLE HEADING - REMOVE FILE
    if st.session_state["ds_files_dict"]:
        with col1:
            st.write("_______")
            st.markdown("""<div class="purple-heading">
                    🗑️ Remove Files
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["ds_file_removed_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>data source file/s</b> have been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["ds_file_removed_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        with col1:
            col1a, col1b = st.columns([2,1])

        list_to_choose =  list(reversed(list(st.session_state["ds_files_dict"].keys())))
        if len(list_to_choose) > 1:
            list_to_choose.insert(0, "Select all")
        with col1a:
            ds_files_to_remove_list = st.multiselect("🖱️ Select files:*",list_to_choose,
                key="key_ds_files_to_remove_list")

        if "Select all" in ds_files_to_remove_list:
            ds_files_to_remove_list = list(st.session_state["ds_files_dict"].keys())
            with col1b:
                st.write("")
                st.markdown(f"""<div class="warning-message">
                        ⚠️ You are removing <b>all files ({len(ds_files_to_remove_list)})</b>.
                        <small>Make sure you want to go ahead.</small>
                    </div>""", unsafe_allow_html=True)
            with col1a:
                delete_all_files_checkbox= st.checkbox(
                "🔒 I am sure I want to remove all files",
                key="key_delete_all_files_checkbox")
                if delete_all_files_checkbox:
                    st.button("Remove", key="key_remove_file_button", on_click=remove_file)

        elif ds_files_to_remove_list:
            with col1a:
                delete_files_checkbox= st.checkbox(
                "🔒 I am sure I want to remove the selected file/s",
                key="key_delete_files_checkbox")
                if delete_files_checkbox:
                    st.button("Remove", key="key_remove_file_button", on_click=remove_file)



#________________________________________________
# DISPLAY DATA
with tab2:

    col1, col2 = st.columns([2,1.5])

    with col1:
        col1a, col1b = st.columns([2,1])

    if not st.session_state["db_connections_dict"] and not st.session_state["ds_files_dict"]:
            with col1:
                st.markdown(f"""<div class="error-message">
                    ❌ <b>No Tabular Logical Sources have been added.</b> <small>You can add them in the
                    <b>Load File</b> pannel.</small>
                </div>""", unsafe_allow_html=True)

    else:

        col1, col2 = st.columns([2,1.5])

        with col2:
            col2a, col2b = st.columns([0.5, 2])

        with col2b:
            st.write("")
            st.write("")


        rows = []
        ds_files = list(st.session_state["ds_files_dict"].items())
        ds_files.reverse()

        for filename, file_obj in ds_files:
            base_name = filename.split(".")[0]
            file_format = filename.split(".")[-1]

            if hasattr(file_obj, "size"):
                # Streamlit UploadedFile
                file_size_kb = file_obj.size / 1024
            elif hasattr(file_obj, "fileno"):
                # File object from open(path, "rb")
                file_size_kb = os.fstat(file_obj.fileno()).st_size / 1024
            else:
                file_size_kb = None  # Unknown format

            if not file_size_kb:
                file_size = None
            elif file_size_kb < 1:
                file_size = f"""{int(file_size_kb*1024)} bytes"""
            elif file_size_kb < 1024:
                file_size = f"""{int(file_size_kb)} kB"""
            else:
                file_size = f"""{int(file_size_kb/1024)} MB"""

            row = {"Filename": base_name, "Format": file_format,
                "Size": file_size if file_size_kb is not None else "N/A"}
            rows.append(row)

            db_connections_df = pd.DataFrame(rows)
            last_added_db_connections_df = db_connections_df.head(utils.get_max_length_for_display()[1])

        with col2b:
            max_length = utils.get_max_length_for_display()[1]   # max number of connections to show directly
            if st.session_state["ds_files_dict"]:
                if len(st.session_state["ds_files_dict"]) < max_length:
                    st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                            🔎 uploaded files
                        </div>""", unsafe_allow_html=True)
                    st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                            🔎 last uploaded files
                        </div>""", unsafe_allow_html=True)
                    st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                            (complete list below)
                        </div>""", unsafe_allow_html=True)
                st.dataframe(last_added_db_connections_df, hide_index=True)

            #Option to show all connections (if too many)
            if st.session_state["ds_files_dict"] and len(st.session_state["ds_files_dict"]) > max_length:
                with st.expander("🔎 Show all files"):
                    st.write("")
                    st.dataframe(db_connections_df, hide_index=True)

            #PURPLE HEADING - VIEW TABLE
            with col1:
                st.write("")
                st.markdown("""<div class="purple-heading">
                        🔎 Display Table
                    </div>""", unsafe_allow_html=True)
                st.write("")

            with col1:
                col1a, col1b = st.columns(2)

            with col1a:
                list_to_choose = list(reversed(list(st.session_state["ds_files_dict"].keys())))
                list_to_choose.insert(0, "Select file")
                tab_filename_for_display = st.selectbox("🖱️ Select file:*", list_to_choose,
                    key="key_tab_filename_for_display")

            if tab_filename_for_display != "Select file":

                tab_file_for_display = st.session_state["ds_files_dict"][tab_filename_for_display]

                df = utils.read_tab_file(tab_filename_for_display)
                tab_file_for_display.seek(0)

                with col1b:
                    column_list = df.columns.tolist()
                    tab_column_filter_list = st.multiselect(f"""🖱️ Select columns (optional, max {utils.get_max_length_for_display()[3]}):""",
                        column_list, key="key_tab_column_filter")

                if not tab_column_filter_list:
                    with col1:
                        max_rows = utils.get_max_length_for_display()[2]
                        max_cols = utils.get_max_length_for_display()[3]

                        limited_df = df.iloc[:, :max_cols]   # limit number of columns

                        # Slice rows if needed
                        if len(df) > max_rows and df.shape[1] > max_cols:
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ Showing the <b>first {max_rows} rows</b> (out of {len(df)})
                                and the <b>first {max_cols} columns</b> (out of {df.shape[1]}).
                            </div>""", unsafe_allow_html=True)
                            st.write("")
                        elif len(df) > max_rows:
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ Showing the <b>first {max_rows} rows</b> (out of {len(df)}).
                            </div>""", unsafe_allow_html=True)
                            st.write("")
                        elif df.shape[1] > max_cols:
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ Showing the <b>first {max_cols} columns</b> (out of {df.shape[1]}).
                            </div>""", unsafe_allow_html=True)
                            st.write("")
                        st.dataframe(limited_df.head(max_rows), hide_index=True)

                else:
                    if len(tab_column_filter_list) > utils.get_max_length_for_display()[3]:
                        with col1:
                            st.markdown(f"""<div class="error-message">
                                ❌ <b> Too many columns</b> selected. Please, respect the limit
                                of {utils.get_max_length_for_display()[3]}.
                            </div>""", unsafe_allow_html=True)
                    else:
                        with col1:
                            st.dataframe(df[tab_column_filter_list], hide_index=True)

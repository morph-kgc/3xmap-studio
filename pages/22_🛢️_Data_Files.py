import io
import json
import jsonpath_ng
import os
import pandas as pd
import streamlit as st
import time
import utils
import uuid
import xml.etree.ElementTree as ET

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

def remove_files():
    # delete files________________
    for file in ds_files_to_remove_list:
        del st.session_state["ds_files_dict"][file]
    # store information________________
    st.session_state["ds_file_removed_ok_flag"] = True  # for success message
    # reset fields_____________________
    st.session_state["key_ds_files_to_remove_list"] = []

# TAB3
def save_path():
    # store information________________
    st.session_state["path_saved_ok_flag"] = True  # for success message
    st.session_state["saved_paths_dict"][st.session_state["path_label"]] = [selected_filename_for_path, path_to_save]
    # reset fields_____________________
    st.session_state["key_selected_filename_for_path"] = "Select file"

def remove_paths():
    # delete paths________________
    for path_label in paths_to_drop_list:
        del st.session_state["saved_paths_dict"][path_label]
    # store information____________________
    st.session_state["path_removed_ok_flag"] = True
    st.session_state["key_manage_view_option"] = "🧭 Path results"


#_______________________________________________________________________________
# PANELS OF THE PAGE (tabs)
tab1, tab2, tab3 = st.tabs(["Manage Files", "Display Data", "Manage Paths"])

#_______________________________________________________________________________
# PANEL: MANAGE FILES
with tab1:
    col1, col2, col2a, col2b = utils.get_panel_layout()

    with col2b:
        utils.display_right_column_df("file_ds", "uploaded files")

    # PURPLE HEADING: UPLOAD FILE-----------------------------------------------
    with col1:
        st.markdown("""<div class="purple-heading">
                📁 Upload File
            </div>""", unsafe_allow_html=True)
        st.write("")

    if st.session_state["ds_file_saved_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>data source file</b> has been saved!
            </div>""", unsafe_allow_html=True)
        st.session_state["ds_file_saved_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    with col1:
        col1a, col1b = st.columns([2,1])
    with col1a:
        ds_allowed_formats = utils.get_supported_formats(data_files=True)            #data source for the TriplesMap
        ds_file = st.file_uploader(f"""🖱️ Upload data source file:*""",
            type=sorted(ds_allowed_formats), key=st.session_state["key_ds_uploader"])

    if ds_file:
        try:
            utils.read_data_file(ds_file, unsaved=True)

            if ds_file.name in st.session_state["ds_files_dict"]:
                with col1b:
                    st.write("")
                    st.write("")
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ File <b>{ds_file.name}</b> is already loaded.
                        <small>If you continue its content will be updated.</small>
                    </div>""", unsafe_allow_html=True)
                with col1a:
                    update_file_checkbox = st.checkbox(
                    "🔒 I am sure I want to update the file",
                    key="key_update_file_checkbox")
                    if update_file_checkbox:
                        st.button("Save", key="key_save_ds_file_button", on_click=save_ds_file)

            else:
                with col1a:
                    st.button("Save", key="key_save_ds_file_button", on_click=save_ds_file)

        except Exception as e:    # empty file
            with col1b:
                st.write("")
                st.write("")
                st.markdown(f"""<div class="error-message">
                    ❌ The file <b>{ds_file.name}</b> appears to be <b>empty or corrupted</b>.
                    <small><i><b>Full error:</b> {e}</i></small>
                </div>""", unsafe_allow_html=True)
                st.write("")

    elif not ds_file:
        with col1b:
            st.write("")
            st.write("")
            large_file_checkbox = st.checkbox(
                "🐘 My file is larger than 200 MB",
                key="key_large_file_checkbox")

        if large_file_checkbox:

            folder_name = utils.get_folder_name(data_sources=True)
            folder_path = os.path.join(os.getcwd(), folder_name)

            if not os.path.isdir(folder_path):
                with col1b:
                    st.markdown(f"""<div class="info-message-blue">
                            📁 Create folder <b style="color:#F63366;">
                            {folder_name}</b> <small>and <b>add your file</b> to it</small>.
                        </span></div>""", unsafe_allow_html=True)

            else:
                tab_files = [f for f in os.listdir(folder_path)
                    if os.path.isfile(os.path.join(folder_path, f)) and any(f.endswith(ext)
                    for ext in ds_allowed_formats)]


                if not tab_files:
                    with col1b:
                        st.markdown(f"""<div class="info-message-blue">
                                📄 <b>Add your file</b> to the <b style="color:#F63366;">
                                {folder_name}</b> folder <small>(folder is now empty)</small>.
                            </span></div>""", unsafe_allow_html=True)

                else:
                    with col1b:
                        st.markdown(f"""<div class="info-message-blue">
                                📄 <b>Add your file</b> to the <b style="color:#F63366;">
                                {folder_name}</b> folder <small>and select it
                                from the list below <b>(do not use uploader)</b></small>.
                            </span></div>""", unsafe_allow_html=True)
                    list_to_choose = tab_files
                    list_to_choose.insert(0, "Select file")
                    with col1a:
                        ds_large_filename = st.selectbox("🖱️ Select file*:", tab_files)

                    if ds_large_filename != "Select file":

                        ds_file_path = os.path.join(folder_path, ds_large_filename)
                        ds_file = open(ds_file_path, "rb")
                        try:
                            utils.read_data_file(ds_file, unsaved=True)

                            if ds_large_filename in st.session_state["ds_files_dict"]:
                                with col1b:
                                    st.markdown(f"""<div class="warning-message">
                                        ⚠️ File <b>{ds_large_filename}</b> is already loaded.
                                        <small>If you continue, its content <b>will be updated</b>.</small>
                                    </div>""", unsafe_allow_html=True)
                                with col1a:
                                    update_large_file_checkbox = st.checkbox(
                                    "🔒 I am sure I want to update the file",
                                    key="key_update_large_file_checkbox")
                                    if update_large_file_checkbox:
                                        st.button("Save", key="key_save_large_ds_file_button", on_click=save_large_ds_file)
                            else:
                                with col1a:
                                    st.button("Save", key="key_save_large_ds_file_button",
                                    on_click=save_large_ds_file)

                        except Exception as e:    # empty file
                            with col1b:
                                st.markdown(f"""<div class="error-message">
                                    ❌ The file <b>{ds_large_filename}</b> appears to be <b>empty or corrupted</b>.
                                    <small><i><b>Full error:</b> {e}</i>.</small>
                                </div>""", unsafe_allow_html=True)


    # SUCCESS MESSAGE: FILE REMOVED---------------------------------------------
    # Shows here if no Remove Files purple heading
    if not st.session_state["ds_files_dict"] and st.session_state["ds_file_removed_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>data source file(s)</b> have been removed!
            </div>""", unsafe_allow_html=True)
        st.session_state["ds_file_removed_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    #PURPLE HEADING - REMOVE FILE-----------------------------------------------
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
                    ✅ The <b>data source file(s)</b> have been removed!
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
                    st.button("Remove", key="key_remove_files_button", on_click=remove_files)

        elif ds_files_to_remove_list:
            with col1a:
                delete_files_checkbox= st.checkbox(
                "🔒 I am sure I want to remove the selected file(s)",
                key="key_delete_files_checkbox")
                if delete_files_checkbox:
                    st.button("Remove", key="key_remove_files_button", on_click=remove_files)


#_______________________________________________________________________________
# PANEL: DISPLAY DATA
with tab2:
    col1, col2, col2a, col2b = utils.get_panel_layout()

    if not st.session_state["ds_files_dict"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.markdown(f"""<div class="error-message">
                ❌ <b>No Data Files have been added.</b> <small>You can load them in the
                <b>Manage Files</b> panel.</small>
            </div>""", unsafe_allow_html=True)

    else:
        with col2b:
            utils.display_right_column_df("file_ds", "uploaded files")

        #PURPLE HEADING: DISPLAY TABLE------------------------------------------
        with col1:
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
            file_format = utils.get_file_format(tab_filename_for_display)

            # TABULAR DATA FILES
            if file_format not in utils.get_supported_formats(hierarchical_files=True):

                df = utils.read_data_file(tab_filename_for_display)
                tab_file_for_display.seek(0)

                with col1b:
                    column_list = df.columns.tolist()
                    tab_column_filter_list = st.multiselect(f"""📡 Filter by columns
                        (optional, max {utils.get_max_length_for_display()[3]}):""",
                        column_list, key="key_tab_column_filter")

                if not tab_column_filter_list:
                    with col1:
                        utils.display_limited_df(df, "")

                else:
                    if len(tab_column_filter_list) > utils.get_max_length_for_display()[3]:
                        with col1:
                            st.markdown(f"""<div class="error-message">
                                ❌ <b> Too many columns</b> selected. <small>Please respect the <b>limit
                                of {utils.get_max_length_for_display()[3]}</b>.</small>
                            </div>""", unsafe_allow_html=True)
                    else:
                        with col1:
                            utils.display_limited_df(df[tab_column_filter_list], "")

            # HIERARCHICAL DATA FILES
            else:

                # Ask user for path expression
                with col1b:
                    path_expr = st.text_area("🧭 Enter path:",
                        height=150, key="key_hierarchical_path_expr")

                df = pd.DataFrame()

                if path_expr.strip():
                    with col1:
                        utils.display_path_dataframe(tab_filename_for_display, path_expr)

                else: # No path expression given
                    if file_format == "json":
                        raw_bytes = tab_file_for_display.getvalue()
                        data = json.loads(raw_bytes.decode("utf-8"))
                        if utils.is_flat_file(data, file_format):
                            df = pd.DataFrame(data if isinstance(data, list) else [data])
                            with col1:
                                utils.display_limited_df(df, "")

                    elif file_format == "xml":
                        raw_bytes = tab_file_for_display.getvalue()
                        tree = ET.parse(io.BytesIO(raw_bytes))
                        root = tree.getroot()
                        if utils.is_flat_file(root, file_format):
                            df = pd.read_xml(io.BytesIO(raw_bytes), parser="etree")
                            with col1:
                                utils.display_limited_df(df, "")

#_______________________________________________________________________________
# PANEL: MANAGE PATHS
with tab3:
    col1, col2, col2a, col2b = utils.get_panel_layout()

    # Get loaded hierarchical files if any
    hierarchical_data_file_dict = {}
    for filename, file in st.session_state["ds_files_dict"].items():
        file_format = utils.get_file_format(filename)
        if file_format in utils.get_supported_formats(hierarchical_files=True):
            hierarchical_data_file_dict[filename] = file

    if not hierarchical_data_file_dict:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            utils.get_missing_element_error_message(hierarchical_files=True)

    else:
        with col2b:
            utils.display_right_column_df("saved_paths", "saved paths", complete=False)

            #Option to show all views (if too many)
            if st.session_state["saved_paths_dict"] and len(st.session_state["saved_paths_dict"]) > utils.get_max_length_for_display()[1]:
                paths_df = utils.display_right_column_df("saved_paths", "saved paths",  display=False)
                with col2:
                    col2a, col2b = st.columns([0.5,2])
                with col2b:
                        st.write("")
                        with st.expander("🔎 Show all saved paths"):
                            st.dataframe(views_df, hide_index=True)

        # PURPLE HEADER: CREATE PATH--------------------------------------------
        with col1:
            st.markdown("""<div class="purple-heading">
                    🖼️ Create Path
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["path_saved_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>path</b> has been saved!
                </div>""", unsafe_allow_html=True)
            st.session_state["path_saved_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        with col1:
            col1a, col1b = st.columns(2)

        with col1a:
            list_to_choose = sorted(hierarchical_data_file_dict.keys())
            list_to_choose.insert(0, "Select file")
            selected_filename_for_path = st.selectbox("🖱️ Select file:*", list_to_choose,
                key="key_selected_filename_for_path")

        if selected_filename_for_path != "Select file":

            selected_file_for_path = hierarchical_data_file_dict[selected_filename_for_path]
            file_format = utils.get_file_format(selected_filename_for_path)

            with col1b:
                path_label = st.text_input("🏷️ Enter path label (opt):",
                    key="key_path_label")
            with col1b:
                path_label_ok_flag = utils.is_valid_label(path_label)
            if path_label and path_label in st.session_state["saved_paths_dict"]:
                with col1b:
                    st.markdown(f"""<div class="error-message">
                        ❌ The label <b>{path_label}</b> is <b>already in use</b>.
                        <small>You must pick a different label.</small>
                    </div>""", unsafe_allow_html=True)
                    path_label_ok_flag = False

            with col1:
                path_to_save = st.text_area("⌨️ Enter path:*",
                    height=150, key="key_path_to_save")

            if not path_label:
                with col1b:
                    if path_to_save in st.session_state["saved_paths_dict"]:
                        st.markdown(f"""<div class="error-message">
                            ❌ <b>Path already used as a label</b></b>.
                            <small> A label must be added in this case.</small>
                        </div>""", unsafe_allow_html=True)
                        path_label_ok_flag = False
                    elif len(path_to_save) > utils.get_max_length_for_display()[10]:
                        st.markdown(f"""<div class="warning-message">
                            ⚠️ <b>Path is quite long</b> <small>({len(path_to_save)} characters)</b>.
                            Labelling it is recommended.</small>
                        </div>""", unsafe_allow_html=True)
                    path_label = path_to_save
                    path_label_ok_flag = True

            df = pd.DataFrame()

            if path_to_save.strip():
                with col1:
                    path_ok_flag = utils.display_path_dataframe(selected_filename_for_path, path_to_save, display=False)

            if path_to_save.strip() and path_label_ok_flag and path_ok_flag:
                with col1:
                    st.session_state["path_label"] = path_label
                    st.button("Save", key="key_save_path_button",
                        on_click=save_path)

            if path_to_save.strip():
                with col1:
                    utils.display_path_dataframe(selected_filename_for_path, path_to_save)

    # SUCCESS MESSAGE: PATH REMOVED---------------------------------------------
    # Shows here if no Manage Saved Paths purple heading
    if not st.session_state["saved_paths_dict"] and st.session_state["path_removed_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>path(s)</b> have been removed!
            </div>""", unsafe_allow_html=True)
        st.session_state["path_removed_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()


    # PURPLE HEADING: MANAGE PATHS----------------------------------------------
    # Shows only if there are paths to be managed
    if st.session_state["saved_paths_dict"]:
        with col1:
            st.write("________")
            st.markdown("""<div class="purple-heading">
                    ⚙️ Manage Saved Paths
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["path_removed_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>path(s)</b> have been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["path_removed_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        with col1:
            col1a, col1b, col1c = st.columns([0.8,1,1])

        files_w_paths_set = set()
        for path_label in st.session_state["saved_paths_dict"]:
            files_w_paths_set.add(st.session_state["saved_paths_dict"][path_label][0])
        files_w_paths_list = list(files_w_paths_set)

        with col1a:
            list_to_choose = ["🧭 Path results", "🔎 Inspect", "🗑️ Remove"]
            manage_path_option = st.radio("🖱️ Select an option:*", list_to_choose,
                label_visibility="collapsed", key="key_manage_path_option")

        with col1b:
            list_to_choose = files_w_paths_list
            list_to_choose.insert(0, "No filter")
            file_to_manage_path_filter = st.selectbox("📡 Filter by file (opt):", list_to_choose,
                key="key_file_to_manage_path_filter")

            if file_to_manage_path_filter == "No filter":
                paths_to_manage_list = list(st.session_state["saved_paths_dict"])

            else:
                paths_to_manage_list = []
                for path_label in st.session_state["saved_paths_dict"]:
                    if st.session_state["saved_paths_dict"][path_label][0] == file_to_manage_path_filter:
                        paths_to_manage_list.append(path_label)

        if manage_path_option == "🧭 Path results":

            with col1c:
                list_to_choose = paths_to_manage_list
                list_to_choose.insert(0, "Select path")
                path_to_inspect_label = st.selectbox("🖱️ Select path:*", list_to_choose,
                    key="key_path_to_inspect_label")

            #HEREIGO
            if path_to_inspect_label != "Select path":
                filename_to_inspect_path = st.session_state["saved_paths_dict"][path_to_inspect_label][0]
                path_to_inspect = st.session_state["saved_paths_dict"][path_to_inspect_label][1]
                with col1:
                    utils.display_path_dataframe(filename_to_inspect_path, path_to_inspect)

        if manage_path_option == "🔎 Inspect":
            with col1c:
                list_to_choose = paths_to_manage_list.copy()
                if len(list_to_choose) > 1:
                    list_to_choose.insert(0, "Select all")
                paths_to_inspect_list = st.multiselect("🖱️ Select paths:*", list_to_choose,
                    key="key_paths_to_inspect_list")

            if "Select all" in paths_to_inspect_list:
                paths_to_inspect_list = paths_to_manage_list

            if paths_to_inspect_list:

                rows = []
                for label in paths_to_inspect_list:
                    filename = st.session_state["saved_paths_dict"][label][0]
                    path_expression = st.session_state["saved_paths_dict"][label][1]

                    rows.append({"Label": label, "Data file": filename,
                            "Path": path_expression})

                df = pd.DataFrame(rows)

                with col1:
                    st.markdown(f"""<div class="info-message-blue">
                            🔎 <b> Paths ({len(rows)}):</b>
                        </div></div>""", unsafe_allow_html=True)
                    st.dataframe(df , hide_index=True)

        if manage_path_option == "🗑️ Remove":

            with col1c:
                list_to_choose = paths_to_manage_list
                if len(list_to_choose) > 1:
                    list_to_choose.insert(0, "Select all")
                paths_to_drop_list = st.multiselect("🖱️ Select paths:*", list_to_choose,
                    key="key_paths_to_drop_list")

            if paths_to_drop_list:

                with col1:
                    col1a, col1b = st.columns([2.5,1])

                if "Select all" in paths_to_drop_list:
                    with col1b:
                        st.markdown(f"""<div class="warning-message">
                            ⚠️ You are deleting <b>all paths ({len(st.session_state["saved_paths_dict"])})</b>.
                            <small>Make sure you want to go ahead.</small>
                        </div>""", unsafe_allow_html=True)
                    with col1a:
                        remove_paths_checkbox = st.checkbox(
                        "🔒 I am sure I want to remove all paths",
                        key="key_remove_paths_checkbox")
                        paths_to_drop_list = list(st.session_state["saved_paths_dict"].keys())
                else:
                    with col1a:
                        remove_paths_checkbox = st.checkbox(
                        "🔒 I am sure I want to remove the selected paths",
                        key="key_remove_paths_checkbox")

                if remove_paths_checkbox:
                    with col1a:
                        st.button("Remove", key="key_remove_paths_button", on_click=remove_paths)

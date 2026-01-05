import os
import streamlit as st
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

#_______________________________________________________________________________
# PANELS OF THE PAGE (tabs)
tab1, tab2 = st.tabs(["Manage Files", "Display Data"])

#_______________________________________________________________________________
# PANEL: MANAGE FILES
with tab1:
    col1, col2, col2a, col2b = utils.get_panel_layout()

    with col2b:
        utils.display_right_column_df("tabular_ds", "uploaded files")

    # PURPLE HEADING: UPLOAD FILE-----------------------------------------------
    with col1:
        st.markdown("""<div class="purple-heading">
                📁 Upload File <small>(or Update)</small>
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
        ds_allowed_formats = utils.get_supported_formats(tab_data=True)            #data source for the TriplesMap
        ds_file = st.file_uploader(f"""🖱️ Upload data source file:*""",
            type=ds_allowed_formats, key=st.session_state["key_ds_uploader"])

    if ds_file:
        try:
            columns_df = utils.read_tab_file(ds_file, unsaved=True)

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
                    <small><i><b>Full error:</b> {e}.</i></small>
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
                            columns_df = utils.read_tab_file(ds_file, unsaved=True)

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
                ❌ <b>No Tabular Logical Sources have been added.</b> <small>You can add them in the
                <b>Manage Files</b> panel.</small>
            </div>""", unsafe_allow_html=True)

    else:
        with col2b:
            utils.display_right_column_df("tabular_ds", "uploaded files")

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

            df = utils.read_tab_file(tab_filename_for_display)
            tab_file_for_display.seek(0)

            with col1b:
                column_list = df.columns.tolist()
                tab_column_filter_list = st.multiselect(f"""📡 Filter by columns
                    (optional, max {utils.get_max_length_for_display()[3]}):""",
                    column_list, key="key_tab_column_filter")

            if not tab_column_filter_list:
                with col1:
                    max_rows = utils.get_max_length_for_display()[2]
                    max_cols = utils.get_max_length_for_display()[3]

                    limited_df = df.iloc[:, :max_cols]   # limit number of columns

                    # Slice rows if needed
                    if len(df) > max_rows and df.shape[1] > max_cols:
                        st.markdown(f"""<div class="warning-message">
                            ⚠️ Showing the <b>first {max_rows} rows</b> <small>(out of {len(df)})</small>
                            and the <b>first {max_cols} columns</b> <small>(out of {df.shape[1]})</small>.
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                    elif len(df) > max_rows:
                        st.markdown(f"""<div class="warning-message">
                            ⚠️ Showing the <b>first {max_rows} rows</b> <small>(out of {len(df)})</small>.
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                    elif df.shape[1] > max_cols:
                        st.markdown(f"""<div class="warning-message">
                            ⚠️ Showing the <b>first {max_cols} columns</b> <small>(out of {df.shape[1]})</small>.
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                    st.dataframe(limited_df.head(max_rows), hide_index=True)

            else:
                if len(tab_column_filter_list) > utils.get_max_length_for_display()[3]:
                    with col1:
                        st.markdown(f"""<div class="error-message">
                            ❌ <b> Too many columns</b> selected. <small>Please respect the <b>limit
                            of {utils.get_max_length_for_display()[3]}</b>.</small>
                        </div>""", unsafe_allow_html=True)
                else:
                    with col1:
                        st.dataframe(df[tab_column_filter_list], hide_index=True)

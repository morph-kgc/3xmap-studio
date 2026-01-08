import json
import pandas as pd
from pymongo import MongoClient
import streamlit as st
from sqlalchemy import text
import time
import utils
import uuid

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
# TAB1
def update_db_connections():
    # update conenction status dict_________________________-
    for connection_label in st.session_state["db_connections_dict"]:
        utils.update_db_connection_status_dict(connection_label)
    # store information____________________________
    st.session_state["db_connection_status_updated_ok_flag"] = True
    # reset fields
    st.session_state["key_db_engine"] = "Select engine"
    st.session_state["key_connection_for_table_display"] = "Select data source"

def save_connection():
    # store information________________
    st.session_state["db_connection_saved_ok_flag"] = True  # for success message
    st.session_state["db_connections_dict"][conn_label] = [db_engine,
        host, port, database, user, password]    # to store connections
    st.session_state["db_connection_status_dict"][conn_label] = ["🔌", ""]
    # reset fields_____________________
    st.session_state["key_db_engine"] = "Select engine"
    st.session_state["key_conn_label"] = ""

def remove_connection():
    # delete connections________________
    for connection_label in connection_labels_to_remove_list:
        del st.session_state["db_connections_dict"][connection_label]
    # delete views________________
    views_to_delete_list = []
    for view_label in st.session_state["saved_views_dict"]:
        if st.session_state["saved_views_dict"][view_label][0] in connection_labels_to_remove_list:
            views_to_delete_list.append(view_label)
    for view_label in views_to_delete_list:
        del st.session_state["saved_views_dict"][view_label]
    # store information________________
    st.session_state["db_connection_removed_ok_flag"] = True  # for success message
    # reset fields_____________________
    st.session_state["key_connection_labels_to_remove_list"] = []
    st.session_state["key_manage_connection_option"] = "🔎 Inspect"

# TAB2
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

# TAB3
def save_mongo_view():
    # save view as collection
    db.command({"create": mongo_view_label, "viewOn": selected_db_table, "pipeline": pipeline})
    # store information________________
    st.session_state["view_saved_ok_flag"] = True  # for success message
    st.session_state["saved_views_dict"][mongo_view_label] = [connection_for_view, f"""{mongo_view_label} ({selected_db_table})"""]
    # reset fields_____________________
    st.session_state["key_connection_for_view"] = "Select a connection"

def save_sql_view():
    # store information________________
    st.session_state["view_saved_ok_flag"] = True  # for success message
    st.session_state["saved_views_dict"][sql_view_label] = [connection_for_view, sql_query]
    # reset fields_____________________
    st.session_state["key_connection_for_view"] = "Select a connection"

def remove_views():
    # delete views________________
    for view_label in views_to_drop_list:
        utils.remove_view_from_db(view_label)    # from database (if Mongo)
        del st.session_state["saved_views_dict"][view_label]    # from dict
    # store information____________________
    st.session_state["view_removed_ok_flag"] = True
    st.session_state["key_manage_view_option"] = "🖼️ View results"


#_______________________________________________________________________________
# PANELS OF THE PAGE (tabs)
tab1, tab2, tab3 = st.tabs(["Manage Connections", "Inspect Data", "Manage Views"])

#_______________________________________________________________________________
# PANEL: MANAGE CONNECTIONS
with tab1:

    col1, col2, col2a, col2b = utils.get_panel_layout()

    # RIGHT COLUMN: CONNECTION INFORMATION--------------------------------------
    if st.session_state["db_connection_status_updated_ok_flag"]:
        with col2b:
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>database connection status information</b> has been updated!
            </div>""", unsafe_allow_html=True)
        st.session_state["db_connection_status_updated_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    if st.session_state["db_connections_dict"]:

        with col2b:
            utils.display_right_column_df("db_connections", "database connections", complete=False)

        with col2:
            col2a, col2b, col2c = st.columns([0.5,0.8,1.2])
        with col2c:
            highlight_color = "#fff7db" if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"] else "#7a6228"
            st.markdown(f"""<div style='text-align: right; font-size: 11px; margin-top: -15px;'>
                <span style='background-color: {highlight_color}; padding: 2px 6px; border-radius: 4px;'>🕹️ must be manually updated</span>
            </div>""", unsafe_allow_html=True)

        with col2b:
            st.button("Update", key="key_update_db_connections_button", on_click=update_db_connections)

        with col2:
            col2a, col2b = st.columns([1,0.8])
        with col2b:
            st.markdown("""<div class="info-message-gray">
            🐢 This pannel can be <b>slow</b> <small>if there are failed connections</small>.
                </div>""", unsafe_allow_html=True)

        # Option to show all connections (if too many)
        db_connections_df = utils.display_right_column_df("db_connections", "database connections",  display=False)
        if st.session_state["db_connections_dict"] and len(st.session_state["db_connections_dict"]) > utils.get_max_length_for_display()[1]:
            with col2:
                col2a, col2b = st.columns([0.5,2])
            with col2b:
                st.write("")
                with st.expander("🔎 Show all connections"):
                    st.dataframe(db_connections_df, hide_index=True)

    # PURPLE HEADING: ADD CONNECTION TO DATABASE--------------------------------
    with col1:
        st.markdown("""<div class="purple-heading">
                🔌 Add Connection to Database
            </div>""", unsafe_allow_html=True)
        st.write("")

    if st.session_state["db_connection_saved_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>connection to the database</b> has been saved!
            </div>""", unsafe_allow_html=True)
        st.session_state["db_connection_saved_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    with col1:
        col1a, col1b = st.columns([2,1])

    with col1a:
        list_to_choose = utils.get_supported_formats(databases=True)
        list_to_choose.insert(0, "Select engine")
        db_engine = st.selectbox("🖱️ Select a database engine:*", list_to_choose, key="key_db_engine")

    with col1b:
        conn_label = st.text_input("🏷️ Enter label:*", key="key_conn_label")

    with col1:
        valid_conn_label = utils.is_valid_label(conn_label)
        if valid_conn_label and conn_label in st.session_state["db_connections_dict"]:
            st.markdown(f"""<div class="error-message">
                ❌ Label <b>{conn_label}</b> is already in use.
                <small>You must pick a <b>different label</b> for this connection.</small>
                    </div>""", unsafe_allow_html=True)
            valid_conn_label = False

    if db_engine != "Select engine":
        default_ports_dict = utils.get_default_ports()
        default_port = default_ports_dict[db_engine] if db_engine in default_ports_dict else ""

        with col1:
            col1a, col1b, col1c = st.columns(3)

        with col1a:
            host = st.text_input("⌨️ Enter host:*", value="localhost")
            user = st.text_input("⌨️ Enter user:*")
        with col1b:
            port = st.text_input("⌨️ Enter port:*", value=default_port)
            password = st.text_input("⌨️ Enter password:*", type="password")
        with col1c:
            if db_engine == "Oracle":
                database = st.text_input("⌨️ Enter service name:*")
            elif db_engine == "MongoDB":
                database = st.text_input("⌨️ Enter database name:*", value="admin")
            else:
                database = st.text_input("⌨️ Enter database name:*")

        if (valid_conn_label and host and port and database and user and password):
            with col1:
                connection_ok_flag = utils.try_connection_to_db(db_engine, host, port, database, user, password)
                if connection_ok_flag:
                    url_str = url_str = utils.get_db_url_str_from_input(db_engine, host, port, database, user, password)

                    with col1:
                        col1a, col1b = st.columns([2,1])

                    duplicated_conn_flag = False
                    for conn in st.session_state["db_connections_dict"]:
                        if utils.get_db_url_str(conn) == url_str:
                            duplicated_conn_flag = conn

                    if duplicated_conn_flag:
                        with col1a:
                            st.markdown(f"""<div class="error-message">
                                    ❌ The connection <b>already exists</b>
                                    <small>(with label <b>{duplicated_conn_flag}</b>).</small>
                                </div>""", unsafe_allow_html=True)
                    else:
                        with col1:
                            col1a, col1b = st.columns([4,1])
                        with col1a:
                            st.button("Save", key="key_save_connection_button", on_click=save_connection)
                            st.markdown(f"""<div class="success-message">
                                    ✔️ Valid connection to database.<br>
                                    <small style="margin-left: 1em;">🔌 <b>{conn_label}</b> → <b style="color:#F63366;">{url_str}</b></small>
                                </div>""", unsafe_allow_html=True)


    # SUCCESS MESSAGE: CONNECTION TO DATABASE REMOVED
    # Shows here in case there is no "Manage Connections" purple heading
    if not st.session_state["db_connections_dict"] and st.session_state["db_connection_removed_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>connection to the database(s)</b> have been removed!
            </div>""", unsafe_allow_html=True)
        st.session_state["db_connection_removed_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    # PURPLE HEADING: MANAGE CONNECTIONS----------------------------------------
    # Shows only if there are connections to be managed
    if st.session_state["db_connections_dict"]:
        with col1:
            st.write("_______")
            st.markdown("""<div class="purple-heading">
                    ⚙️ Manage Connections
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["db_connection_removed_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>connection(s) to the database</b> have been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["db_connection_removed_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        with col1:
            col1a, col1b = st.columns([2,1])

        with col1b:
            st.write("")
            list_to_choose = ["🔎 Inspect", "🗑️ Remove"]
            manage_connection_option = st.radio("🖱️ Select an option:*", list_to_choose,
                label_visibility="collapsed", key="key_manage_connection_option")

        if manage_connection_option == "🔎 Inspect":

            with col1a:
                list_to_choose = sorted(st.session_state["db_connections_dict"].keys())
                list_to_choose.insert(0, "Select all")
                connection_label_to_check_list = st.multiselect("🖱️ Select connections:*", list_to_choose,
                    key="key_connection_label_to_check_list")

                if "Select all" in connection_label_to_check_list:
                    connection_label_to_check_list = sorted(st.session_state["db_connections_dict"].keys())

                if connection_label_to_check_list:
                    rows = []
                    failed_conn_list = []
                    for conn_label in connection_label_to_check_list:

                        utils.update_db_connection_status_dict(conn_label)

                        engine = st.session_state["db_connections_dict"][conn_label][0]
                        host = st.session_state["db_connections_dict"][conn_label][1]
                        port= st.session_state["db_connections_dict"][conn_label][2]
                        database = st.session_state["db_connections_dict"][conn_label][3]
                        user = st.session_state["db_connections_dict"][conn_label][4]
                        password = st.session_state["db_connections_dict"][conn_label][5]
                        status = st.session_state["db_connection_status_dict"][conn_label][0]

                        if status == "🚫":
                            failed_conn_list.append(conn_label)

                        rows.append({"Label": conn_label, "Engine": engine,
                            "Host": host, "Port": port, "Database": database,
                            "User": user, "Status": status})

                    df = pd.DataFrame(rows)

                    with col1:
                        st.dataframe(df, use_container_width=True, hide_index=True)

                    inner_html = ""
                    for conn_label in failed_conn_list:
                        inner_html += f"""<div>
                        🚫 <b>{conn_label}:</b>
                        <small>{str(st.session_state["db_connection_status_dict"][conn_label][1])}</small><br></div>"""

                    if inner_html:
                        with col1:
                            st.markdown(f"""<div class="error-message">
                                {inner_html}
                            </div>""", unsafe_allow_html=True)
                            st.write("")

        elif manage_connection_option == "🗑️ Remove":

            with col1a:
                list_to_choose = list(reversed(list(st.session_state["db_connections_dict"].keys())))
                list_to_choose.insert(0, "Select all failed connections")
                if len(list_to_choose) > 2:
                    list_to_choose.insert(0, "Select all")
                connection_labels_to_remove_list = st.multiselect("🖱️ Select connections:*", list_to_choose,
                    key="key_connection_labels_to_remove_list")

            not_working_connections_list = []
            for connection_label in st.session_state["db_connections_dict"]:
                if "Select all failed connections" in connection_labels_to_remove_list:
                    utils.update_db_connection_status_dict(connection_label)
                if st.session_state["db_connection_status_dict"][connection_label][0] == "🚫":
                    not_working_connections_list.append(connection_label)

            if "Select all" in connection_labels_to_remove_list:
                connection_labels_to_remove_list = list(st.session_state["db_connections_dict"].keys())

                with col1b:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ You are removing <b>all connections</b> to databases.
                        <small>Make sure you want to go ahead.</small>
                    </div>""", unsafe_allow_html=True)

                with col1a:
                    delete_all_connections_checkbox = st.checkbox(
                    "🔒 I am sure I want to remove all connections",
                    key="key_delete_all_connections_checkbox")
                    if delete_all_connections_checkbox:
                        st.button("Remove", key="key_remove_connection_button", on_click=remove_connection)

            elif connection_labels_to_remove_list:

                if  "Select all failed connections" in connection_labels_to_remove_list:

                    connection_labels_to_remove_list.remove("Select all failed connections")
                    connection_labels_to_remove_list = list(set(connection_labels_to_remove_list + not_working_connections_list))


                    if not not_working_connections_list:
                        with col1b:
                            st.markdown(f"""<div class="success-message">
                                    ✔️ <b>No failed connections</b> to remove.
                                    <small>All connections are working. </small>
                                </div>""", unsafe_allow_html=True)

                with col1a:
                    if connection_labels_to_remove_list:
                        delete_all_cross_connections_checkbox= st.checkbox(
                        "🔒 I am sure I want to remove the selected connections",
                        key="key_delete_all_cross_connections_checkbox")
                        if delete_all_cross_connections_checkbox:
                            st.button("Remove", key="key_remove_connection_button", on_click=remove_connection)


            with col1:
                inner_html = ""
                max_length = utils.get_max_length_for_display()[4]

                for conn in connection_labels_to_remove_list[:max_length]:
                    url_str = utils.get_db_url_str(conn)
                    if conn not in not_working_connections_list:
                        inner_html += f"""<div style="margin-bottom:4px;">
                            <small><b>🔌 {conn}</b> → {url_str}</small>
                        </div>"""
                    else:
                        inner_html += f"""<div style="margin-bottom:4px;">
                            <small><b>🚫 {conn}</b> → {url_str}</small>
                        </div>"""

                if len(connection_labels_to_remove_list) > max_length:
                    inner_html += f"""<div style="margin-bottom:4px;">
                        <small>🔌 ... <b>(+{len(connection_labels_to_remove_list[:max_length])})</b></small>
                    </div>"""

                if len(connection_labels_to_remove_list) > 0:
                    st.markdown(f"""<div class="info-message-gray">
                            {inner_html}
                        </div>""", unsafe_allow_html=True)


#_______________________________________________________________________________
# PANEL: INSPECT DATA
with tab2:

    col1, col2, col2a, col2b = utils.get_panel_layout()

    if not st.session_state["db_connections_dict"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            utils.get_missing_element_error_message(databases=True)

    else:

        # RIGHT COLUMN: CONNECTION INFORMATION----------------------------------
        if st.session_state["db_connections_dict"]:

            with col2b:
                utils.display_right_column_df("db_connections", "database connections", complete=False)

            with col2:
                col2a, col2b, col2c = st.columns([0.5,0.8,1.2])
            with col2c:
                if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
                    highlight_color = "#fff7db"
                else:
                    highlight_color = "#7a6228"
                st.markdown(f"""<div style='text-align: right; font-size: 11px; margin-top: -15px;'>
                    <span style='background-color: {highlight_color}; padding: 2px 6px; border-radius: 4px;'>🕹️ must be manually updated</span>
                </div>""", unsafe_allow_html=True)

            with col2b:
                st.button("Update", key="key_update_db_connections_button_2", on_click=update_db_connections)

            with col2:
                col2a, col2b = st.columns([1,0.8])
            with col2b:
                st.markdown("""<div class="info-message-gray">
                🐢 This pannel can be <b>slow</b> <small>if there are failed connections</small>.
                    </div>""", unsafe_allow_html=True)

            # Option to show all connections (if too many)
            if st.session_state["db_connections_dict"] and len(st.session_state["db_connections_dict"]) > utils.get_max_length_for_display()[1]:
                with col2:
                    col2a, col2b = st.columns([0.5,2])
                with col2b:
                    st.write("")
                    with st.expander("🔎 Show all connections"):
                        st.dataframe(db_connections_df, hide_index=True)


        #PURPLE HEADING: DISPLAY TABLE------------------------------------------
        with col1:
            st.markdown("""<div class="purple-heading">
                    📅 Display Table
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a, col1b = st.columns([2,1])

        with col1a:
            list_to_choose = sorted(st.session_state["db_connections_dict"].keys())
            list_to_choose.insert(0, "Select data source")
            connection_for_table_display = st.selectbox("🖱️ Select data source:*", list_to_choose,
                key="key_connection_for_table_display")

            # this avoids persistence in the table selectbox when changing the connection
            if "last_connection_for_table_display" not in st.session_state:
                st.session_state["last_connection_for_table_display"] = None
            if connection_for_table_display != st.session_state["last_connection_for_table_display"]:
                st.session_state["key_selected_db_table"] = "Select table"
                st.session_state["last_connection_for_table_display"] = connection_for_table_display

        if connection_for_table_display != "Select data source":

            connection_ok_flag = utils.update_db_connection_status_dict(connection_for_table_display)

            if not connection_ok_flag:
                with col1b:
                    st.markdown(f"""<div class="error-message">
                        ❌ <b> Connection not working. </b>
                        <small>Please check it in the <b>Manage Connections</b> panel.</small>
                    </div>""", unsafe_allow_html=True)

            else:
                conn = utils.make_connection_to_db(connection_for_table_display)
                result = utils.get_tables_from_db(connection_for_table_display)
                db_tables = [row[0] for row in result]

                with col1b:
                    list_to_choose = sorted(db_tables).copy()
                    list_to_choose.insert(0, "Select table")
                    selected_db_table = st.selectbox("🖱️ Select table:*", list_to_choose,
                        key="key_selected_db_table")
                    if len(db_tables) == 0:
                        st.markdown(f"""<div class="error-message">
                                ❌ <b>No tables</b> in database.
                            </div>""", unsafe_allow_html=True)

                if selected_db_table != "Select table":

                    df = utils.get_df_from_db(connection_for_table_display, selected_db_table)

                    with col1a:
                        column_list = df.columns.tolist()
                        sql_column_filter_list = st.multiselect(f"""🖱️ Select columns (optional, max {utils.get_max_length_for_display()[3]}):""",
                            column_list, key="key_sql_column_filter")

                    with col1:
                        if not sql_column_filter_list:
                            utils.display_limited_df(df, "Table")

                        else:
                            if len(sql_column_filter_list) > utils.get_max_length_for_display()[3]:
                                with col1a:
                                    st.markdown(f"""<div class="error-message">
                                        ❌ <b> Too many columns</b> selected. Please, respect the limit
                                        of {utils.get_max_length_for_display()[3]}.
                                    </div>""", unsafe_allow_html=True)
                            else:
                                utils.display_limited_df(df, "Table", display=False)
                                if not df.empty:
                                    st.dataframe(df[sql_column_filter_list], hide_index=True)


#_______________________________________________________________________________
# PANEL: MANAGE VIEWS
with tab3:
    col1, col2, col2a, col2b = utils.get_panel_layout()

    if not st.session_state["db_connections_dict"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            utils.get_missing_element_error_message(databases=True)

    else:
        with col2b:
            utils.display_right_column_df("saved_views", "saved views", complete=False)

            with col2:
                col2a, col2b = st.columns([1,0.8])
            with col2b:
                st.markdown("""<div class="info-message-gray">
                🐢 This pannel can be <b>slow</b> <small>if there are failed connections</small>.
                    </div>""", unsafe_allow_html=True)

            #Option to show all views (if too many)
            if st.session_state["saved_views_dict"] and len(st.session_state["saved_views_dict"]) > utils.get_max_length_for_display()[1]:
                with col2:
                    col2a, col2b = st.columns([0.5,2])
                with col2b:
                        st.write("")
                        with st.expander("🔎 Show all saved views"):
                            st.dataframe(views_df, hide_index=True)

        # PURPLE HEADER: CREATE VIEW--------------------------------------------
        with col1:
            st.markdown("""<div class="purple-heading">
                    🖼️ Create View
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["view_saved_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>view</b> has been saved!
                </div>""", unsafe_allow_html=True)
            st.session_state["view_saved_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        with col1:
            col1a, col1b = st.columns(2)

        with col1a:
            list_to_choose = list(reversed(list(st.session_state["db_connections_dict"].keys())))
            list_to_choose.insert(0, "Select a connection")
            connection_for_view = st.selectbox("🖱️ Select a connection:*", list_to_choose,
                key="key_connection_for_view")

        if connection_for_view != "Select a connection":

            with col1a:
                conn, connection_ok_flag = utils.check_connection_to_db(connection_for_view)
            engine = st.session_state["db_connections_dict"][connection_for_view][0]

            # MONGODB DATABASE
            if engine == "MongoDB" and connection_ok_flag:

                with col2b:
                    st.markdown(f"""<div class="info-message-blue">
                        🖼️ <b>MongoDB views</b> are created in the database
                        <small>as read‑only collections (but can be also managed from this page)</small>.
                    </div>""", unsafe_allow_html=True)

                database = st.session_state["db_connections_dict"][connection_for_view][3]
                db = conn[database]

                with col1b:
                    mongo_view_label = st.text_input("🏷️ Enter label for the view:*",
                        key="key_mongo_view_label")
                    if mongo_view_label in db.list_collection_names():
                        st.markdown(f"""<div class="error-message">
                            ❌ The label <b>{mongo_view_label}</b> is already in use.
                            <small>You must pick a different label.</small>
                        </div>""", unsafe_allow_html=True)
                        valid_mongo_view_label_flag = False
                    elif len(database) + 1 + len(mongo_view_label) > 120:
                        st.markdown(f"""<div class="error-message">
                            ❌ <b>Label must be shorter.</b>
                            <small>Database + label must be less than 120 characters.</small>
                        </div>""", unsafe_allow_html=True)
                        valid_mongo_view_label_flag = False
                    else:
                        valid_mongo_view_label_flag = utils.is_valid_label(mongo_view_label, hard=True) # hard mode enough to ensure all requriements but length


                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    result = utils.get_tables_from_db(connection_for_view)
                    db_tables = [row[0] for row in result]
                    db_tables = sorted(db_tables)
                    list_to_choose = db_tables.copy()
                    list_to_choose.insert(0, "Select table")
                    selected_db_table = st.selectbox("🖱️ Select table:*", list_to_choose,
                        key="key_selected_db_table_for_view")
                with col1b:
                    if len(db_tables) == 0:
                        st.write("")
                        st.markdown(f"""<div class="error-message">
                                ❌ <b>No tables</b> in database.
                            </div>""", unsafe_allow_html=True)

                with col1:
                    pipeline_str = st.text_area("⌨️ Enter pipeline:*",
                        height=150, key="key_pipeline")

                if pipeline_str:
                    try:
                        pipeline = json.loads(pipeline_str)      # Parse the text into a Python list/dict
                        pipeline_ok_flag = True
                        preview = list(db[selected_db_table].aggregate(pipeline))
                        df = pd.DataFrame(preview)

                    except json.JSONDecodeError as e:
                        pipeline_ok_flag = False
                        with col1:
                            st.markdown(f"""<div class="error-message">
                                ❌ <b>Invalid pipeline input.</b><small> Please enter a valid pipeline in JSON format.
                                <i><b>Full error:</b> {e}.</i></small>
                            </div>""", unsafe_allow_html=True)

                if pipeline_str and pipeline_ok_flag and valid_mongo_view_label_flag and selected_db_table != "Select table":
                    with col1:
                        st.button("Save", key="key_save_mongo_view_button",
                            on_click=save_mongo_view)

                if selected_db_table != "Select table" and pipeline_str and pipeline_ok_flag:
                    with col1:
                        utils.display_limited_df(df, "View previsualisation")

            # SQL DATABASE CONNECTIONS
            elif engine != "MongoDB" and connection_ok_flag:
                with col1b:
                    sql_view_label = st.text_input("🏷️ Enter label for the view (to save it):*",
                        key="key_sql_view_label")
                with col1b:
                    valid_sql_view_label_flag = utils.is_valid_label(sql_view_label)
                if sql_view_label and sql_view_label in st.session_state["saved_views_dict"]:
                    with col1b:
                        st.markdown(f"""<div class="error-message">
                            ❌ The label <b>{sql_view_label}</b> is already in use.
                            <small>You must pick a different label.</small>
                        </div>""", unsafe_allow_html=True)
                        valid_sql_view_label_flag = False

                with col1:
                    sql_query = st.text_area("⌨️ Enter SQL query:*",
                        height=150, key="key_sql_query")

                if sql_query:
                    df, sql_query_ok_flag, error = utils.run_query(connection_for_view, sql_query)

                    if not sql_query_ok_flag:
                        with col1:
                            st.markdown(f"""<div class="error-message">
                                ❌ <b>Invalid query</b>.<small> Please check your input.
                                <i><b> Full error:</b> {error}</i></small>
                            </div>""", unsafe_allow_html=True)

                if sql_query and sql_query_ok_flag and valid_sql_view_label_flag:
                    with col1:
                        st.button("Save", key="key_save_sql_view_button",
                            on_click=save_sql_view)

                if sql_query and sql_query_ok_flag:

                    with col1:
                        utils.display_limited_df(df, "View previsualisation")

    # SUCCESS MESSAGE: VIEW REMOVED---------------------------------------------
    # Shows here if no Manage Saved Views purple heading
    if not st.session_state["saved_views_dict"] and st.session_state["view_removed_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>view(s)</b> have been removed!
            </div>""", unsafe_allow_html=True)
        st.session_state["view_removed_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()


    # PURPLE HEADING: MANAGE SAVED----------------------------------------------
    # Shows only if there are connections to databases
    if st.session_state["saved_views_dict"]:
        with col1:
            st.write("________")
            st.markdown("""<div class="purple-heading">
                    ⚙️ Manage Saved Views
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["view_removed_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>view</b> has been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["view_removed_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        with col1:
            col1a, col1b, col1c = st.columns([0.8,1,1])

        connections_w_views_set = set()
        for view_label in st.session_state["saved_views_dict"]:
            connections_w_views_set.add(st.session_state["saved_views_dict"][view_label][0])
        connections_w_views_list = list(connections_w_views_set)

        with col1a:
            list_to_choose = ["🖼️ View results", "🔎 Inspect", "🗑️ Remove"]
            manage_view_option = st.radio("🖱️ Select an option:*", list_to_choose,
                label_visibility="collapsed", key="key_manage_view_option")

        with col1b:
            list_to_choose = connections_w_views_list
            list_to_choose.insert(0, "No filter")
            connection_to_manage_view_filter = st.selectbox("📡 Filter by connection (opt):", list_to_choose,
                key="key_connection_to_manage_view_filter")

            if connection_to_manage_view_filter == "No filter":
                views_to_manage_list = list(st.session_state["saved_views_dict"])

            else:
                views_to_manage_list = []
                for view_label in st.session_state["saved_views_dict"]:
                    if st.session_state["saved_views_dict"][view_label][0] == connection_to_manage_view_filter:
                        views_to_manage_list.append(view_label)

        if manage_view_option == "🖼️ View results":

            with col1c:
                list_to_choose = views_to_manage_list
                list_to_choose.insert(0, "Select view")
                view_to_inspect = st.selectbox("🖱️ Select view:*", views_to_manage_list,
                    key="key_view_to_inspect")

            if view_to_inspect != "Select view":
                with col1:
                    utils.display_db_view_results(view_to_inspect)

        if manage_view_option == "🔎 Inspect":
            with col1c:
                list_to_choose = views_to_manage_list.copy()
                if len(list_to_choose) > 1:
                    list_to_choose.insert(0, "Select all")
                views_to_inspect_list = st.multiselect("🖱️ Select views:*", list_to_choose,
                    key="key_views_to_inspect_list")

            if "Select all" in views_to_inspect_list:
                views_to_inspect_list = views_to_manage_list

            if views_to_inspect_list:

                rows = []
                for label in views_to_inspect_list:
                    connection = st.session_state["saved_views_dict"][label][0]
                    database =  st.session_state["db_connections_dict"][connection][3]

                    query_or_collection = st.session_state["saved_views_dict"][label][1]
                    query_or_collection = query_or_collection

                    rows.append({"Label": label, "Source": connection,
                            "Database": database, "Query/collection": query_or_collection})

                views_df = pd.DataFrame(rows)

                with col1:
                    st.markdown(f"""<div class="info-message-blue">
                            🔎 <b> Views ({len(rows)}):</b>
                        </div></div>""", unsafe_allow_html=True)
                    st.dataframe(views_df , hide_index=True)

        if manage_view_option == "🗑️ Remove":

            with col1c:
                list_to_choose = views_to_manage_list
                if len(list_to_choose) > 1:
                    list_to_choose.insert(0, "Select all")
                views_to_drop_list = st.multiselect("🖱️ Select views:*", list_to_choose,
                    key="key_views_to_drop_list")

            if views_to_drop_list:

                with col1:
                    col1a, col1b = st.columns([2.5,1])

                if "Select all" in views_to_drop_list:
                    with col1b:
                        st.markdown(f"""<div class="warning-message">
                            ⚠️ You are deleting <b>all views ({len(st.session_state["saved_views_dict"])})</b>.
                            <small>Make sure you want to go ahead.</small>
                        </div>""", unsafe_allow_html=True)
                    with col1a:
                        remove_views_checkbox = st.checkbox(
                        "🔒 I am sure I want to remove all views",
                        key="key_remove_views_checkbox")
                        views_to_drop_list = list(st.session_state["saved_views_dict"].keys())
                else:
                    with col1a:
                        remove_views_checkbox = st.checkbox(
                        "🔒 I am sure I want to remove the selected views",
                        key="key_remove_views_checkbox")

                if remove_views_checkbox:
                    with col1a:
                        st.button("Remove", key="key_remove_views_button", on_click=remove_views)

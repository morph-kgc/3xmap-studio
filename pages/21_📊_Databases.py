import pandas as pd
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
    #store information____________________________
    st.session_state["db_connection_status_updated_ok_flag"] = True

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
    # delete queries________________
    queries_to_delete_list = []
    for query in st.session_state["sql_queries_dict"]:
        if st.session_state["sql_queries_dict"][query][0] in connection_labels_to_remove_list:
            queries_to_delete_list.append(query)
    for query in queries_to_delete_list:
        del st.session_state["sql_queries_dict"][query]
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
def save_view():
    # store information________________
    st.session_state["sql_query_saved_ok_flag"] = True  # for success message
    st.session_state["sql_queries_dict"][sql_query_label] = [connection_for_query, sql_query]
    # reset fields_____________________
    st.session_state["key_sql_query"] = ""
    st.session_state["key_sql_query_label"] = ""

def remove_views():
    # delete queries________________
    for query in queries_to_drop_list:
        del st.session_state["sql_queries_dict"][query]
    # store information____________________
    st.session_state["sql_query_removed_ok_flag"] = True
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
        rows = [{"Label": label, "Engine": st.session_state["db_connections_dict"][label][0],
                "Database": st.session_state["db_connections_dict"][label][3],
                "Status": st.session_state["db_connection_status_dict"][label][0]}
                for label in reversed(list(st.session_state["db_connections_dict"].keys()))]
        db_connections_df = pd.DataFrame(rows)
        last_added_db_connections_df = db_connections_df.head(utils.get_max_length_for_display()[1])

        with col2b:
            max_length = utils.get_max_length_for_display()[1]
            if len(st.session_state["db_connections_dict"]) < max_length:
                st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                        🔎 database connections
                    </div>""", unsafe_allow_html=True)
                st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                        🔎 last added database connections
                    </div>""", unsafe_allow_html=True)
                st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        (complete list below)
                    </div>""", unsafe_allow_html=True)
            st.dataframe(last_added_db_connections_df, hide_index=True)

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
            st.write("")
            st.markdown("""<div class="info-message-gray">
            🐢 This pannel can be <b>slow</b> <small>if there are failed connections</small>.
                </div>""", unsafe_allow_html=True)

        # Option to show all connections (if too many)
        if st.session_state["db_connections_dict"] and len(st.session_state["db_connections_dict"]) > max_length:
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
                        with col1a:
                            st.button("Save", key="key_save_connection_button", on_click=save_connection)
                            st.markdown(f"""<div class="success-message">
                                    ✔️ Valid connection to database.<br>
                                    <small style="margin-left: 1em;">🔌 <b>{conn_label}</b> → <b style="color:#F63366;">{url_str}</b>.</small>
                                </div>""", unsafe_allow_html=True)


    # SUCCESS MESSAGE: CONNECTION TO DATABASE REMOVED
    # Shows here in case there is no "Manage Connections" purple heading
    if not st.session_state["db_connections_dict"] and st.session_state["db_connection_removed_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>connection to the database/s</b> have been removed!
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
                    ✅ The <b>connection/s to the database</b> have been removed!
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
                    for conn in connection_label_to_check_list:

                        utils.update_db_connection_status_dict(conn)

                        engine = st.session_state["db_connections_dict"][conn][0]
                        host = st.session_state["db_connections_dict"][conn][1]
                        port= st.session_state["db_connections_dict"][conn][2]
                        database = st.session_state["db_connections_dict"][conn][3]
                        user = st.session_state["db_connections_dict"][conn][4]
                        password = st.session_state["db_connections_dict"][conn][5]
                        status = st.session_state["db_connection_status_dict"][conn][0]

                        if status == "🚫":
                            failed_conn_list.append(conn)

                        rows.append({"Label": conn, "Engine": engine,
                            "Host": host, "Port": port, "Database": database,
                            "User": user, "Status": status})

                    df = pd.DataFrame(rows)

                    with col1:
                        st.dataframe(df, use_container_width=True, hide_index=True)

                    inner_html = ""
                    for conn in failed_conn_list:
                        inner_html += f"""<div>
                        🚫 <b>{conn}:</b>
                        <small>{str(st.session_state["db_connection_status_dict"][conn][1])}</small><br></div>"""

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

    # RFBOOKMARK
#_______________________________________________________________________________
# PANEL: INSPECT DATA
with tab2:

    col1, col2, col2a, col2b = utils.get_panel_layout()

    if not st.session_state["db_connections_dict"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.markdown(f"""<div class="error-message">
                    ❌ <b>No connections to databases have been configured.</b> <small>You can add them in the
                    <b>Manage Connections</b> panel.</small>
                </div>""", unsafe_allow_html=True)

    else:

        # RIGHT COLUMN: CONNECTION INFORMATION----------------------------------
        with col2b:
            rows = [{"Label": label, "Engine": st.session_state["db_connections_dict"][label][0],
                    "Database": st.session_state["db_connections_dict"][label][3],
                    "Status": st.session_state["db_connection_status_dict"][label][0]}
                    for label in reversed(list(st.session_state["db_connections_dict"].keys()))]
            db_connections_df = pd.DataFrame(rows)
            last_added_db_connections_df = db_connections_df.head(utils.get_max_length_for_display()[1])

            max_length = utils.get_max_length_for_display()[1]   # max number of connections to show directly
            if st.session_state["db_connections_dict"]:
                if len(st.session_state["db_connections_dict"]) < max_length:
                    st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                            🔎 database connections
                        </div>""", unsafe_allow_html=True)
                    st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                            🔎 last added database connections
                        </div>""", unsafe_allow_html=True)
                    st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                            (complete list below)
                        </div>""", unsafe_allow_html=True)
                    st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        </div>""", unsafe_allow_html=True)

                st.dataframe(last_added_db_connections_df, hide_index=True)

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
                    st.write("")
                    st.markdown("""<div class="info-message-gray">
                    🐢 This pannel can be <b>slow</b> <small>if there are failed connections</small>.
                        </div>""", unsafe_allow_html=True)

            # Option to show all connections (if too many)
            with col2b:
                st.write("")
                if st.session_state["db_connections_dict"] and len(st.session_state["db_connections_dict"]) > max_length:
                    with st.expander("🔎 Show all connections"):
                        st.write("")
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
                db_tables = [row[0] for row in result.fetchall()]

                with col1b:
                    list_to_choose = db_tables
                    list_to_choose.insert(0, "Select table")
                    selected_db_table = st.selectbox("🖱️ Select table:*", list_to_choose,
                        key="key_selected_db_table")

                # RFBOOKMARK
                if selected_db_table != "Select table":

                    result = conn.execute(text(f"SELECT * FROM {selected_db_table}"))
                    rows = result.fetchall()
                    columns = result.keys()
                    df = pd.DataFrame(rows, columns=columns)

                    table_len = f"{len(df)} rows" if len(df) != 1 else f"{len(df)} row"
                    inner_html = f"""📅 <b style="color:#F63366;"> Table ({table_len}):</b>
                            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"""

                    with col1a:
                        column_list = df.columns.tolist()
                        sql_column_filter_list = st.multiselect(f"""🖱️ Select columns (optional, max {utils.get_max_length_for_display()[3]}):""",
                            column_list, key="key_sql_column_filter")

                    if not sql_column_filter_list:

                        with col1:
                            max_rows = utils.get_max_length_for_display()[2]
                            max_cols = utils.get_max_length_for_display()[3]
                            limited_df = df.iloc[:, :max_cols]   # limit number of columns

                            # Slice rows if needed
                            if len(df) > max_rows and df.shape[1] > max_cols:
                                inner_html += f"""<small>Showing the <b>first {max_rows} rows</b> (out of {len(df)})
                                    and the <b>first {max_cols} columns</b> (out of {df.shape[1]}).</small>"""
                            elif len(df) > max_rows:
                                inner_html += f"""<small>Showing the <b>first {max_rows} rows</b> (out of {len(df)}).</small>"""
                            elif df.shape[1] > max_cols:
                                inner_html += f"""<small>Showing the <b>first {max_cols} columns</b> (out of {df.shape[1]}).</small>"""

                            st.markdown(f"""<div class="info-message-blue">
                                    {inner_html}
                                </div>""", unsafe_allow_html=True)
                            st.dataframe(limited_df.head(max_rows), hide_index=True)

                    else:
                        if len(sql_column_filter_list) > utils.get_max_length_for_display()[3]:
                            with col1:
                                st.markdown(f"""<div class="error-message">
                                    ❌ <b> Too many columns</b> selected. Please, respect the limit
                                    of {utils.get_max_length_for_display()[3]}.
                                </div>""", unsafe_allow_html=True)
                        else:
                            with col1:
                                table_len = f"{len(df)} rows" if len(df) != 1 else f"{len(df)} row"
                                st.markdown(f"""<div class="info-message-blue">
                                        {inner_html}
                                    </div>""", unsafe_allow_html=True)
                                st.dataframe(df[sql_column_filter_list], hide_index=True)


#_______________________________________________________________________________
# PANEL: MANAGE VIEWS
with tab3:

    col1, col2 = st.columns([2,1.5])

    with col1:
        col1a, col1b = st.columns([2,1])

    if not st.session_state["db_connections_dict"]:
            with col1:
                st.markdown(f"""<div class="error-message">
                    ❌ <b>No SQL data sources have been added.</b> <small>You can add them in the
                    <b>Connect to Database</b> pannel.</small>
                </div>""", unsafe_allow_html=True)

    else:

        col1, col2 = st.columns([2,1.5])

        with col2:
            col2a, col2b = st.columns([0.5, 2])

        with col2b:
            st.write("")
            st.write("")

            rows = []
            for label in reversed(list(st.session_state["sql_queries_dict"].keys())):
                connection = st.session_state["sql_queries_dict"][label][0]
                database =  st.session_state["db_connections_dict"][connection][3]

                sql_query = st.session_state["sql_queries_dict"][label][1]
                max_length = utils.get_max_length_for_display()[10]
                sql_query = sql_query[:max_length] + "..." if len(sql_query) > max_length else sql_query

                rows.append({"Label": label, "Source": connection,
                        "Database": database, "Query": sql_query})

            sql_queries_df = pd.DataFrame(rows)
            last_sql_queries_df = sql_queries_df.head(utils.get_max_length_for_display()[1])

            max_length = utils.get_max_length_for_display()[1]   # max number of connections to show directly
            if st.session_state["sql_queries_dict"]:
                if len(st.session_state["sql_queries_dict"]) < max_length:
                    st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                            🔎 saved views
                        </div>""", unsafe_allow_html=True)
                    st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                            🔎 last saved views
                        </div>""", unsafe_allow_html=True)
                    st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                            (complete list below)
                        </div>""", unsafe_allow_html=True)
                st.dataframe(last_sql_queries_df, hide_index=True)
                st.write("")

            #Option to show all views (if too many)
            if st.session_state["sql_queries_dict"] and len(st.session_state["sql_queries_dict"]) > max_length:
                with st.expander("🔎 Show all saved views"):
                    st.write("")
                    st.dataframe(sql_queries_df, hide_index=True)

            with col2:
                col2a, col2b = st.columns([0.5,2])
            with col2b:
                st.markdown("""<div class="info-message-gray">
                🐢 This pannel can be <b>slow</b> <small>if there are failed connections</small>.
                    </div>""", unsafe_allow_html=True)

        # PURPLE HEADER: QUERY DATA---------------------------------------------
        with col1:
            st.markdown("""<div class="purple-heading">
                    🖼️ Create View
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["sql_query_saved_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>view</b> has been saved!
                </div>""", unsafe_allow_html=True)
            st.session_state["sql_query_saved_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        with col1:
            col1a, col1b = st.columns(2)


        with col1a:
            list_to_choose = list(reversed(list(st.session_state["db_connections_dict"].keys())))
            list_to_choose.insert(0, "Select a connection")
            connection_for_query = st.selectbox("🖱️ Select a connection:*", list_to_choose,
                key="key_connection_for_query")

        if connection_for_query != "Select a connection":

            with col1b:
                sql_query_label = st.text_input("🏷️ Enter label for the view (to save it):*",
                    key="key_sql_query_label")
                valid_sql_query_label = utils.is_valid_label(sql_query_label)
                if sql_query_label and sql_query_label not in st.session_state["sql_queries_dict"]:
                    sql_query_label_ok_flag = True
                elif sql_query_label:
                    sql_query_label_ok_flag = False
                    with col1b:
                        st.markdown(f"""<div class="error-message">
                            ❌ The label <b>{sql_query_label}</b> is already in use.
                            You must pick a different label.
                        </div>""", unsafe_allow_html=True)
                    st.write("")
                else:
                    sql_query_label_ok_flag = False

            try:
                conn = utils.make_connection_to_db(connection_for_query)
                connection_ok_flag = True

            except:
                with col1a:
                    st.markdown(f"""<div class="error-message">
                        ❌ The connection <b>{connection_for_query}</b> is not working.
                        <small>Please check it in the <b>Manage Connections</b> pannel.</small>
                    </div>""", unsafe_allow_html=True)
                    st.write("")
                connection_ok_flag = False

            if connection_ok_flag:

                cur = conn.cursor()   # create a cursor

                with col1:
                    sql_query = st.text_area("⌨️ Enter SQL query:*",
                        height=150, key="key_sql_query")

                if sql_query:

                    try:
                        cur.execute(sql_query)
                        sql_query_ok_flag = True

                    except Exception as e:
                        with col1:
                            st.markdown(f"""<div class="error-message">
                                ❌ <b>Invalid SQL syntax</b>. Please check your query.<br>
                                <small><b> Full error:</b> {e}</small>
                            </div>""", unsafe_allow_html=True)
                            st.write("")
                        sql_query_ok_flag = False

                if sql_query and sql_query_ok_flag and valid_sql_query_label:
                    with col1:
                        st.button("Save", key="key_save_view_button",
                            on_click=save_view)

                if sql_query and sql_query_ok_flag:
                    rows = cur.fetchall()
                    engine = st.session_state["db_connections_dict"][connection_for_query][0]
                    if engine == "SQL Server":
                        rows = [tuple(row) for row in rows]   # rows are of type <class 'pyodbc.Row'> -> convert to tuple
                    columns = [desc[0] for desc in cur.description]
                    df = pd.DataFrame(rows, columns=columns)


                    with col1:
                        st.markdown(f"""<div class="info-message-blue">
                                🖼️ <b style="color:#F63366;"> View previsualisation</b><br>
                            </div></div>""", unsafe_allow_html=True)
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

    # SUCCESS MESSAGE: VIEW REMOVED---------------------------------------------
    # Shows here if no Manage saved views purple header
    if not st.session_state["sql_queries_dict"] and st.session_state["sql_query_removed_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>view/s</b> have been removed!
            </div>""", unsafe_allow_html=True)
        st.session_state["sql_query_removed_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()


    # PURPLE HEADER: MANAGE SAVED VIEWS----------------------------------------
    # Shows only if there are connections
    if st.session_state["sql_queries_dict"]:
        with col1:
            st.write("________")
            st.markdown("""<div class="purple-heading">
                    ⚙️ Manage Saved Views
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["sql_query_removed_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>view</b> has been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["sql_query_removed_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        with col1:
            col1a, col1b, col1c = st.columns([0.8,1,1])

        connections_w_queries_set = set()
        for query in st.session_state["sql_queries_dict"]:
            connections_w_queries_set.add(st.session_state["sql_queries_dict"][query][0])
        connections_w_queries_list = list(connections_w_queries_set)

        with col1a:
            list_to_choose = ["🖼️ View results", "🔎 Inspect", "🗑️ Remove"]
            manage_view_option = st.radio("🖱️ Select an option:*", list_to_choose,
                label_visibility="collapsed", key="key_manage_view_option")

        with col1b:
            list_to_choose = connections_w_queries_list
            list_to_choose.insert(0, "No filter")
            connection_to_manage_query_filter = st.selectbox("⚙️ Filter by connection (opt):", list_to_choose,
                key="key_connection_to_manage_query_filter")

            if connection_to_manage_query_filter == "No filter":

                sql_queries_to_manage_list = list(st.session_state["sql_queries_dict"])
                for query in st.session_state["sql_queries_dict"]:
                    if st.session_state["sql_queries_dict"][query][0] == connection_to_manage_query_filter:
                        sql_queries_to_manage_list.append(query)

                connection_ok_flag = True

            else:

                sql_queries_to_manage_list = []
                for query in st.session_state["sql_queries_dict"]:
                    if st.session_state["sql_queries_dict"][query][0] == connection_to_manage_query_filter:
                        sql_queries_to_manage_list.append(query)

        if manage_view_option == "🖼️ View results":

            with col1c:
                list_to_choose = sql_queries_to_manage_list
                list_to_choose.insert(0, "Select view")
                sql_query_to_inspect = st.selectbox("🖱️ Select view:*", sql_queries_to_manage_list,
                    key="key_sql_query_to_inspect")

            if sql_query_to_inspect != "Select view":

                with col1:
                    connection_ok_flag = utils.display_db_view_results(sql_query_to_inspect)
                    if not connection_ok_flag:
                        st.markdown(f"""<div class="error-message">
                            ❌ The connection <b>{st.session_state["sql_queries_dict"][query][0]}</b> is not working.
                            <small>Please check it in the <b>Manage Connections</b> pannel.</small>
                        </div>""", unsafe_allow_html=True)


        if manage_view_option == "🔎 Inspect":

            with col1c:
                list_to_choose = sql_queries_to_manage_list.copy()
                if len(list_to_choose) > 1:
                    list_to_choose.insert(0, "Select all")
                queries_to_inspect_list = st.multiselect("🖱️ Select views:*", list_to_choose,
                    key="key_queries_to_inspect_list")

            if "Select all" in queries_to_inspect_list:
                queries_to_inspect_list = sql_queries_to_manage_list


            if queries_to_inspect_list:

                rows = []
                for label in queries_to_inspect_list:
                    connection = st.session_state["sql_queries_dict"][label][0]
                    database =  st.session_state["db_connections_dict"][connection][3]

                    sql_query = st.session_state["sql_queries_dict"][label][1]
                    max_length = utils.get_max_length_for_display()[10]
                    sql_query = sql_query[:max_length] + "..." if len(sql_query) > max_length else sql_query

                    rows.append({"Label": label, "Source": connection,
                            "Database": database, "Complete query": sql_query})

                sql_queries_df = pd.DataFrame(rows)

                with col1:
                    st.markdown(f"""<div class="info-message-blue">
                            🔎 <b> Views ({len(rows)}):</b>
                        </div></div>""", unsafe_allow_html=True)
                    st.dataframe(sql_queries_df , hide_index=True)


        if manage_view_option == "🗑️ Remove":

            with col1c:
                list_to_choose = sql_queries_to_manage_list
                if len(list_to_choose) > 1:
                    list_to_choose.insert(0, "Select all")
                queries_to_drop_list = st.multiselect("🖱️ Select views:*", list_to_choose,
                    key="key_queries_to_drop_list")

            if queries_to_drop_list:

                with col1:
                    col1a, col1b = st.columns([2.5,1])

                if "Select all" in queries_to_drop_list:
                    with col1b:
                        st.markdown(f"""<div class="warning-message">
                            ⚠️ You are deleting <b>all views ({len(st.session_state["sql_queries_dict"])})</b>.
                            <small>Make sure you want to go ahead.</small>
                        </div>""", unsafe_allow_html=True)
                    with col1a:
                        remove_views_checkbox = st.checkbox(
                        "🔒 I am sure I want to remove all views",
                        key="key_remove_views_checkbox")
                        queries_to_drop_list = list(st.session_state["sql_queries_dict"].keys())
                else:
                    with col1a:
                        remove_views_checkbox = st.checkbox(
                        "🔒 I am sure I want to remove the selected views",
                        key="key_remove_views_checkbox")

                if remove_views_checkbox:
                    with col1a:
                        st.button("Remove", key="key_remove_views_button", on_click=remove_views)

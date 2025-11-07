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
import io
from streamlit_js_eval import streamlit_js_eval

# Config-----------------------------------
if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
    st.set_page_config(page_title="3Xmap Studio", layout="wide",
        page_icon="logo/fav_icon.png")
else:
    st.set_page_config(page_title="3Xmap Studio", layout="wide",
        page_icon="logo/fav_icon_inverse.png")

# Automatic detection of dark mode-------------------------
if "dark_mode_flag" not in st.session_state or st.session_state["dark_mode_flag"] is None:
    st.session_state["dark_mode_flag"] = streamlit_js_eval(js_expressions="window.matchMedia('(prefers-color-scheme: dark)').matches",
        key="dark_mode")

# Header-----------------------------------
# dark_mode = False if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"] else True
# header_html = utils.render_header(title="SQL Databases",
#     description="""Manage the connections to <b>relational data sources</b>, consult the data
#                     and <b>save views</b>.""",
#     dark_mode=dark_mode)
# st.markdown(header_html, unsafe_allow_html=True)

# Sidebar logo-----------------------------------
dark_mode = False if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"] else True
utils.render_sidebar_logo(dark_mode=dark_mode)

# Import style----------------------------------------------
style_container = st.empty()
if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
    style_container.markdown(utils.import_st_aesthetics(), unsafe_allow_html=True)
else:
    style_container.markdown(utils.import_st_aesthetics_dark_mode(), unsafe_allow_html=True)


# Initialise session state variables------------------------------------
utils.initialise_session_state_variables()

#define on_click functions-----------------------------------------
# TAB1
def update_db_connections():
    for connection_label in st.session_state["db_connections_dict"]:
        try:
            conn = utils.make_connection_to_db(connection_label)
            if conn:
                conn.close() # optional: close immediately or keep open for queries
            st.session_state["db_connection_status_dict"][connection_label] = ["✔️", ""]

        except Exception as e:
            st.session_state["db_connection_status_dict"][connection_label] = ["❌", e]

def save_connection():
    # store information________________
    st.session_state["db_connection_saved_ok_flag"] = True  # for success message
    st.session_state["db_connections_dict"][conn_label] = [db_engine,
        host, port, database, user, password]    # to store connections
    st.session_state["db_connection_status_dict"][conn_label] = ["✔️", ""]
    # reset fields_____________________
    st.session_state["key_db_engine"] = "Select an engine"
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


# START PAGE_____________________________________________________________________

#____________________________________________________________
# PANELS OF THE PAGE (tabs)

tab1, tab2, tab3 = st.tabs(["Connect to Database", "Display Data", "Create View"])


#________________________________________________
# MANAGE SQL DATA SOURCES
with tab1:

    col1, col2 = st.columns([2,1.5])

    with col1:
        col1a, col1b = st.columns([2,1])

    with col2:
        col2a, col2b = st.columns([0.5, 2])

    with col2b:
        st.write("")
        st.write("")

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
            st.dataframe(last_added_db_connections_df, hide_index=True)

            st.button("Update", key="key_update_db_connections_button", on_click=update_db_connections)

        #Option to show all connections (if too many)
        if st.session_state["db_connections_dict"] and len(st.session_state["db_connections_dict"]) > max_length:
            with st.expander("🔎 Show all connections"):
                st.write("")
                st.dataframe(db_connections_df, hide_index=True)

    # PURPLE HEADING - ADD NEW CONNECTION
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
    db_engine_list = ["Select an engine", "PostgreSQL", "MySQL", "SQL Server", "MariaDB", "Oracle"]
    with col1a:
        db_engine = st.selectbox("🖱️ Select a database engine:*", db_engine_list, key="key_db_engine")
    with col1b:
        conn_label = st.text_input("⌨️ Enter label:*", key="key_conn_label")
        valid_conn_label = utils.is_valid_label(conn_label)
        if valid_conn_label and conn_label in st.session_state["db_connections_dict"]:
            with col1a:
                st.markdown(f"""<div class="error-message">
                    ❌ Label <b>{conn_label}</b> is already in use.<br>
                    You must choose a different label for this connection.
                        </div>""", unsafe_allow_html=True)
                valid_conn_label = False
                st.write("")

    if db_engine != "Select an engine":
        default_ports_dict = utils.get_default_ports()
        default_port = default_ports_dict[db_engine] if db_engine in default_ports_dict else ""
        default_users_dict = utils.get_default_users()
        default_user = default_users_dict[db_engine] if db_engine in default_users_dict else ""
        with col1:
            col1a, col1b, col1c = st.columns(3)
        with col1a:
            host = st.text_input("⌨️ Enter host:*", value="localhost")
            user = st.text_input("⌨️ Enter user:*", value=default_user)
        with col1b:
            port = st.text_input("⌨️ Enter port:*", value=default_port)
            password = st.text_input("⌨️ Enter password:*", type="password")
        with col1c:
            if not db_engine == "Oracle":
                database = st.text_input("⌨️ Enter database name:*")
            else:
                database = st.text_input("⌨️ Enter service name:*")

        if (valid_conn_label and host and port and database and user and password):
            with col1:
                connection_ok_flag = utils.try_connection(db_engine, host, port, database, user, password)
                if connection_ok_flag:
                    if db_engine == "Oracle":
                        jdbc_str = f"jdbc:oracle:thin:@{host}:{port}:{database}"
                    elif db_engine == "SQL Server":
                        jdbc_str = f"jdbc:sqlserver://{host}:{port};databaseName={database}"
                    elif db_engine == "PostgreSQL":
                        jdbc_str = f"jdbc:postgresql://{host}:{port}/{database}"
                    elif db_engine == "MySQL":
                        jdbc_str = f"jdbc:mysql://{host}:{port}/{database}"
                    elif db_engine =="MariaDB":
                        jdbc_str = f"jdbc:mariadb://{host}:{port}/{database}"

                    with col1:
                        col1a, col1b = st.columns([2,1])
                    with col1a:
                        st.button("Save", key="key_save_connection_button", on_click=save_connection)
                        st.markdown(f"""<div class="success-message">
                                ✔️ Valid connection to database.<br>
                                <small>🔌 <b>{conn_label}</b> → <b style="color:#F63366;">{jdbc_str}</b>.</small>
                            </div>""", unsafe_allow_html=True)




    if not st.session_state["db_connections_dict"] and st.session_state["db_connection_removed_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>connection to the database</b> has been removed!
            </div>""", unsafe_allow_html=True)
        st.session_state["db_connection_removed_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()



    # PURPLE HEADING - REMOVE CONNECTION
    if st.session_state["db_connections_dict"]:
        with col1:
            st.write("_______")
            st.markdown("""<div class="purple-heading">
                    🗑️ Remove Connections
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
        with col1a:
            list_to_choose = list(reversed(list(st.session_state["db_connections_dict"].keys())))
            list_to_choose.insert(0, "Select all ❌")
            if len(list_to_choose) > 2:
                list_to_choose.insert(0, "Select all")
            connection_labels_to_remove_list = st.multiselect("🖱️ Select connections:*", list_to_choose,
                key="key_connection_labels_to_remove_list")

        if "Select all" in connection_labels_to_remove_list:
            connection_labels_to_remove_list = list(st.session_state["db_connections_dict"].keys())

            # create a single info message
            inner_html = ""
            max_length = utils.get_max_length_for_display()[4]

            for conn in connection_labels_to_remove_list[:max_length]:
                jdbc_str = utils.get_jdbc_str(conn)
                inner_html += f"""<div style="margin-bottom:4px;">
                    <small><b>🔌 {conn}</b> → {jdbc_str}</small>
                </div>"""
            # wrap it all in a single info box
            full_html = f"""<div class="info-message-gray">
                {inner_html}</div>"""

            if len(connection_labels_to_remove_list) > max_length:   # many sm to remove
                inner_html += f"""<div style="margin-bottom:4px;">
                    <small>🔌 ... <b>(+{len(connection_labels_to_remove_list[:max_length])})</b></small>
                </div>"""

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
                if len(connection_labels_to_remove_list) > 0:
                    st.markdown(f"""<div class="info-message-gray">
                            {inner_html}
                        </div>""", unsafe_allow_html=True)


        elif "Select all ❌" in connection_labels_to_remove_list:

            not_working_connections_list = []

            for connection_label in st.session_state["db_connections_dict"]:
                utils.update_db_connection_status_dict(connection_label)
                if st.session_state["db_connection_status_dict"][connection_label][0] == "❌":
                    not_working_connections_list.append(connection_label)

            connection_labels_to_remove_list.remove("Select all ❌")
            connection_labels_to_remove_list = list(set(connection_labels_to_remove_list + not_working_connections_list))

            # create a single info message
            inner_html = ""
            max_length = utils.get_max_length_for_display()[4]

            for conn in connection_labels_to_remove_list[:max_length]:
                jdbc_str = utils.get_jdbc_str(conn)
                inner_html += f"""<div style="margin-bottom:4px;">
                    <small><b>🔌 {conn}</b> → {jdbc_str}</small>
                </div>"""

            if len(connection_labels_to_remove_list) > max_length:   # many sm to remove
                inner_html += f"""<div style="margin-bottom:4px;">
                    <small>🔌 ... <b>(+{len(connection_labels_to_remove_list[:max_length])})</b></small>
                </div>"""

            if not_working_connections_list:
                inner_html += f"""<div style="margin-bottom:4px;">
                    <small>Complete list of ❌ connections:
                    <b>{utils.format_list_for_markdown(not_working_connections_list)}</b></small>
                </div>"""
            else:
                inner_html += f"""<div style="margin-bottom:4px;">
                    <small>✔️ All <b>connections</b> are working. <small>No ❌ connections to remove.</small>
                </div>"""

            with col1a:
                if connection_labels_to_remove_list:
                    st.write("")
                    delete_all_cross_connections_checkbox= st.checkbox(
                    "🔒 I am sure I want to remove the selected connections",
                    key="key_delete_all_cross_connections_checkbox")
                    if delete_all_cross_connections_checkbox:
                        st.button("Remove", key="key_remove_connection_button", on_click=remove_connection)
                    st.markdown(f"""<div class="info-message-gray">
                            {inner_html}
                        </div>""", unsafe_allow_html=True)

        elif connection_labels_to_remove_list:
            # create a single info message
            inner_html = ""
            max_length = utils.get_max_length_for_display()[4]

            for conn in connection_labels_to_remove_list[:max_length]:
                jdbc_str = utils.get_jdbc_str(conn)
                inner_html += f"""<div style="margin-bottom:4px;">
                    <small><b>🔌 {conn}</b> → {jdbc_str}</small>
                </div>"""

            if len(connection_labels_to_remove_list) > max_length:   # many sm to remove
                inner_html += f"""<div style="margin-bottom:4px;">
                    <small>🔌 ... <b>(+{len(connection_labels_to_remove_list[:max_length])})</b></small>
                </div>"""

            with col1a:
                delete_connections_checkbox= st.checkbox(
                "🔒 I am sure I want to remove the selected connections",
                key="key_delete_connections_checkbox")
                if delete_connections_checkbox:
                    st.button("Remove", key="key_remove_connection_button", on_click=remove_connection)
                st.markdown(f"""<div class="info-message-gray">
                        {inner_html}
                    </div>""", unsafe_allow_html=True)

    # PURPLE HEADING - CONSULT CONNECTION
    if st.session_state["db_connections_dict"]:
        with col1:
            st.write("______")
            st.markdown("""<div class="purple-heading">
                    ℹ️ Connection Information
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:

            list_to_choose = list(reversed(list(st.session_state["db_connections_dict"].keys())))
            list_to_choose.insert(0, "Select connection")
            connection_label_to_check = st.selectbox("🖱️ Select connection:*", list_to_choose,
                key="key_connection_label_to_check")

            if connection_label_to_check != "Select connection":

                utils.update_db_connection_status_dict(connection_label_to_check)

                engine = st.session_state["db_connections_dict"][connection_label_to_check][0]
                host = st.session_state["db_connections_dict"][connection_label_to_check][1]
                port= st.session_state["db_connections_dict"][connection_label_to_check][2]
                database = st.session_state["db_connections_dict"][connection_label_to_check][3]
                user = st.session_state["db_connections_dict"][connection_label_to_check][4]
                password = st.session_state["db_connections_dict"][connection_label_to_check][5]

                status = st.session_state["db_connection_status_dict"][connection_label_to_check][0]

                df = pd.DataFrame([{"Label": connection_label_to_check, "Engine": engine,
                    "Host": host, "Port": port, "Database": database,
                    "User": user, "Status": status}])

                with col1:
                    st.dataframe(df, use_container_width=True, hide_index=True)

                if status == "❌":
                    with col1:
                        st.markdown(f"""<div class="error-message">
                            ❌ <b>Connection error:</b>
                            {str(st.session_state["db_connection_status_dict"][connection_label_to_check][1])}
                        </div>""", unsafe_allow_html=True)
                        st.write("")


#________________________________________________
# DISPLAY DATA
with tab2:

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
                st.dataframe(last_added_db_connections_df, hide_index=True)

                st.button("Update", key="key_update_db_connections_button_2", on_click=update_db_connections)

            #Option to show all connections (if too many)
            if st.session_state["db_connections_dict"] and len(st.session_state["db_connections_dict"]) > max_length:
                with st.expander("🔎 Show all connections"):
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
            col1a, col1b = st.columns([2,1])


        with col1a:
            list_to_choose = list(reversed(list(st.session_state["db_connections_dict"].keys())))
            list_to_choose.insert(0, "Select a SQL data source")
            connection_for_table_display = st.selectbox("🖱️ Select a SQL data source:*", list_to_choose,
                key="key_connection_for_table_display")

            # this avoids persistence in the choose a table selectbox when changing the connection
            if "last_connection_for_table_display" not in st.session_state:
                st.session_state["last_connection_for_table_display"] = None
            if connection_for_table_display != st.session_state["last_connection_for_table_display"]:
                st.session_state["key_selected_db_table"] = "Select a table"
                st.session_state["last_connection_for_table_display"] = connection_for_table_display

        if connection_for_table_display != "Select a SQL data source":

            try:
                conn = utils.make_connection_to_db(connection_for_table_display)
                connection_ok_flag = True

            except:
                with col1a:
                    st.markdown(f"""<div class="error-message">
                        ❌ The connection <b>{connection_label}</b> is not working.
                        Please remove it and save it again in the <b>Manage Connections</b> pannel.
                    </div>""", unsafe_allow_html=True)
                    st.write("")
                connection_ok_flag = False

            if connection_ok_flag:

                cur = conn.cursor()   # create a cursor
                engine = st.session_state["db_connections_dict"][connection_for_table_display][0]
                database = st.session_state["db_connections_dict"][connection_for_table_display][3]

                utils.get_tables_from_db(engine, cur, database)

                db_tables = [row[0] for row in cur.fetchall()]

                with col1b:
                    list_to_choose = db_tables
                    list_to_choose.insert(0, "Select a table")
                    selected_db_table = st.selectbox("🖱️ Choose a table:*", list_to_choose,
                        key="key_selected_db_table")

                if selected_db_table != "Select a table":

                    cur.execute(f"SELECT * FROM {selected_db_table}")
                    rows = cur.fetchall()
                    if engine == "SQL Server":
                        rows = [tuple(row) for row in rows]   # rows are of type <class 'pyodbc.Row'> -> convert to tuple
                    columns = [desc[0] for desc in cur.description]

                    df = pd.DataFrame(rows, columns=columns)

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
                        if len(sql_column_filter_list) > utils.get_max_length_for_display()[3]:
                            with col1:
                                st.markdown(f"""<div class="error-message">
                                    ❌ <b> Too many columns</b> selected. Please, respect the limit
                                    of {utils.get_max_length_for_display()[3]}.
                                </div>""", unsafe_allow_html=True)
                        else:
                            with col1:
                                st.dataframe(df[sql_column_filter_list], hide_index=True)

                    cur.close()
                    conn.close()



#________________________________________________
# VIEWS
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

            check_sql_query_dict = {}
            for sql_query_label in st.session_state["sql_queries_dict"]:
                sql_query = st.session_state["sql_queries_dict"][sql_query_label][1]
                connection_label = st.session_state["sql_queries_dict"][sql_query_label][0]

                try:
                    conn = utils.make_connection_to_db(connection_label)
                    cur = conn.cursor()
                    cur.execute(sql_query)
                    conn.close() # optional: close immediately or keep open for queries
                    check_sql_query_dict[sql_query_label] = "✔️"

                except:
                    check_sql_query_dict[sql_query_label] = "❌"

            rows = []
            for label in reversed(list(st.session_state["sql_queries_dict"].keys())):
                connection = st.session_state["sql_queries_dict"][label][0]
                database =  st.session_state["db_connections_dict"][connection][3]
                sql_query_ok_flag = check_sql_query_dict[sql_query_label]
                if len(st.session_state["sql_queries_dict"][label][1]) > 20:
                    sql_query = st.session_state["sql_queries_dict"][label][1][:20] + "..."
                else:
                    sql_query = st.session_state["sql_queries_dict"][label][1]
                rows.append({"Label": label, "Source": connection,
                        "Database": database, "Query": sql_query,
                        "Query OK": sql_query_ok_flag})

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

            #Option to show all connections (if too many)
            if st.session_state["sql_queries_dict"] and len(st.session_state["sql_queries_dict"]) > max_length:
                with st.expander("🔎 Show all saved views"):
                    st.write("")
                    st.dataframe(sql_queries_df, hide_index=True)

    #PURPLE HEADING - QUERY DATA
    if st.session_state["db_connections_dict"]:
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
                sql_query_label = st.text_input("⌨️ Enter label for the view (to save it):*",
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
                        ❌ The connection <b>{connection_label}</b> is not working.
                        Please remove it and save it again in the <b>Manage Connections</b> pannel.
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

                if sql_query and sql_query_ok_flag:

                    if sql_query_label_ok_flag:
                        with col1:
                            st.button("Save", key="key_save_view_button",
                                on_click=save_view)


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


    #PURPLE HEADING - REMOVE VIEW
    if st.session_state["sql_queries_dict"]:
        with col1:
            st.write("_________")
            st.markdown("""<div class="purple-heading">
                    🗑️Remove View
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
            col1a, col1b = st.columns(2)

        with col1a:
            list_to_choose = list(reversed(st.session_state["sql_queries_dict"]))
            if len(list_to_choose) > 1:
                list_to_choose.insert(0, "Select all")
            queries_to_drop_list = st.multiselect("🖱️ Select views:*", list_to_choose,
                key="key_queries_to_drop_list")

        if queries_to_drop_list:
            with col1a:
                if "Select all" in queries_to_drop_list:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ You are deleting <b>all views ({len(st.session_state["sql_queries_dict"])})</b>.
                        <small>Make sure you want to go ahead.</small>
                    </div>""", unsafe_allow_html=True)
                    st.write("")
                    remove_views_checkbox = st.checkbox(
                    "🔒 I am sure I want to remove all views",
                    key="key_remove_views_checkbox")
                    queries_to_drop_list = list(st.session_state["sql_queries_dict"].keys())
                else:
                    remove_views_checkbox = st.checkbox(
                    "🔒 I am sure I want to remove the selected views",
                    key="key_remove_views_checkbox")

            if remove_views_checkbox:
                with col1a:
                    st.button("Remove", key="key_remove_views_button", on_click=remove_views)


    #PURPLE HEADING - CONSULT SAVED VIEWS
    if st.session_state["sql_queries_dict"]:
        with col1:
            st.write("________")
            st.markdown("""<div class="purple-heading">
                    🔍 Consult Saved Views
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a, col1b = st.columns(2)

        connections_w_queries_set = set()
        for query in st.session_state["sql_queries_dict"]:
            connections_w_queries_set.add(st.session_state["sql_queries_dict"][query][0])
        connections_w_queries_list = list(connections_w_queries_set)


        with col1a:
            list_to_choose = connections_w_queries_list
            list_to_choose.insert(0, "Select a connection")
            connection_to_consult_query = st.selectbox("🖱️ Select a connection:*", list_to_choose,
                key="key_connection_to_consult_query")

        if connection_to_consult_query != "Select a connection":

            sql_queries_to_consult_list = []
            for query in st.session_state["sql_queries_dict"]:
                if st.session_state["sql_queries_dict"][query][0] == connection_to_consult_query:
                    sql_queries_to_consult_list.append(query)

            try:
                conn = utils.make_connection_to_db(connection_to_consult_query)
                connection_ok_flag = True

            except:
                with col1a:
                    st.markdown(f"""<div class="error-message">
                        ❌ The connection <b>{connection_label}</b> is not working.
                        Please check it in the <b>Manage Connections</b> pannel.
                    </div>""", unsafe_allow_html=True)
                    st.write("")
                connection_ok_flag = False

            if connection_ok_flag:

                with col1b:
                    list_to_choose = sql_queries_to_consult_list
                    list_to_choose.insert(0, "Select query")
                    sql_query_to_consult = st.selectbox("🖱️ Select query:*", sql_queries_to_consult_list,
                        key="key_sql_query_to_consult")


                if sql_query_to_consult != "Select query":

                    with col1:

                        st.markdown(f"""<div class="info-message-blue">
                                🖼️ <b style="color:#F63366;"> View</b>
                                <small>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(<b>Query:</b>
                                {st.session_state["sql_queries_dict"][sql_query_to_consult][1]})</small>
                            </div></div>""", unsafe_allow_html=True)

                    cur = conn.cursor()   # create a cursor

                    try:
                        cur.execute(st.session_state["sql_queries_dict"][sql_query_to_consult][1])
                        sql_query_ok_flag = True

                    except Exception as e:
                        with col1:
                            st.write("")
                            st.markdown(f"""<div class="error-message">
                                ❌ <b>Invalid SQL syntax</b>. Please check your query.<br>
                                <small><b> Full error:</b> {e}</small>
                            </div>""", unsafe_allow_html=True)
                            st.write("")
                        sql_query_ok_flag = False


                    rows = cur.fetchall()
                    engine = st.session_state["db_connections_dict"][connection_to_consult_query][0]
                    if engine == "SQL Server":
                        rows = [tuple(row) for row in rows]   # rows are of type <class 'pyodbc.Row'> -> convert to tuple
                    columns = [desc[0] for desc in cur.description]
                    df = pd.DataFrame(rows, columns=columns)


                    with col1:
                        st.write("")
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

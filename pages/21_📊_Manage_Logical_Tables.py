import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace
import utils
import time
import pandas as pd

import psycopg

# Header
st.markdown("""
<div style="display:flex; align-items:center; background-color:#f0f0f0; padding:12px 18px;
            border-radius:8px; margin-bottom:16px;">
    <span style="font-size:1.7rem; margin-right:18px;">📊</span>
    <div>
        <h3 style="margin:0; font-size:1.75rem;">
            <span style="color:#511D66; font-weight:bold; margin-right:12px;">◽◽◽◽◽</span>
            Manage Logical Tables
            <span style="color:#511D66; font-weight:bold; margin-left:12px;">◽◽◽◽◽</span>
        </h3>
        <p style="margin:0; font-size:0.95rem; color:#555;">
            Manage your logical tables: <b>PostgreSQL, xxx, xxx, etc.</b>
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

#____________________________________________
#PRELIMINARY

# Import style
utils.import_st_aesthetics()
st.write("")

# Initialise session state variables
#TAB1
if "db_connections_dict" not in st.session_state:
    st.session_state["db_connections_dict"] = {}
if "db_connection_saved_ok_flag" not in st.session_state:
    st.session_state["db_connection_saved_ok_flag"] = False
if "db_connection_removed_ok_flag" not in st.session_state:
    st.session_state["db_connection_removed_ok_flag"] = False

#TAB2
if "sql_queries_dict" not in st.session_state:
    st.session_state["sql_queries_dict"] = {}
if "sql_query_saved_ok_flag" not in st.session_state:
    st.session_state["sql_query_saved_ok_flag"] = False


#define on_click functions
# TAB1
def save_postgress_connection():
    # store information________________
    st.session_state["db_connection_saved_ok_flag"] = True  # for success message
    st.session_state["db_connections_dict"][label] = ["postgres",
        postgres_host, postgres_port, postgres_database, postgres_user, postgres_password]    # to store connections
    # reset fields_____________________
    st.session_state["key_db_connection_type"] = "Select an engine"
    st.session_state["key_connection_label"] = ""

def remove_connection():
    # delete connections________________
    for connection_label in connection_labels_to_remove_list:
        del st.session_state["db_connections_dict"][connection_label]
    # store information________________
    st.session_state["db_connection_removed_ok_flag"] = True  # for success message
    # reset fields_____________________
    st.session_state["key_connection_labels_to_remove_list"] = []

# TAB2
def save_sql_query():
    # store information________________
    st.session_state["sql_query_saved_ok_flag"] = True  # for success message
    st.session_state["sql_queries_dict"][sql_query_label] = [connection_for_query, sql_query]
    # reset fields_____________________
    st.session_state["key_sql_query"] = ""
    st.session_state["key_sql_query_label"] = ""


# START PAGE_____________________________________________________________________


col1, col2 = st.columns([2,1.5])
if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
    with col1:
        st.markdown(f"""
        <div style="background-color:#f8d7da; padding:1em;
                    border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
            ❗ You need to create or load a mapping. Please go to the
            <b style="color:#a94442;">Global Configuration page</b>.
        </div>
        """, unsafe_allow_html=True)
        st.stop()


#____________________________________________________________
# PANELS OF THE PAGE (tabs)

tab1, tab2, tab3 = st.tabs(["Manage Connections", "Query Data", "Save Logical Table"])


#________________________________________________
#MANAGE CONECTIONS
with tab1:

    col1, col2 = st.columns([2,1.5])

    #PURPLE HEADING - ADD NEW CONECTION
    with col1:
        st.markdown("""<div class="purple-heading">
                🔌 Add New Connection
            </div>""", unsafe_allow_html=True)
        st.write("")

    if st.session_state["db_connection_saved_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="custom-success">
                ✅ The <b>connection to the database</b> has been saved!
            </div>""", unsafe_allow_html=True)
        st.session_state["db_connection_saved_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    with col1:
        col1a, col1b = st.columns([2,1])

    # Display last added namespaces in dataframe (also option to show all ns)
    tm_dict = utils.get_tm_dict()

    with col2:
        col2a, col2b = st.columns([0.5, 2])

    with col2b:
        st.write("")
        st.write("")

        check_connection_dict = {}
        for connection_label in st.session_state["db_connections_dict"]:
            try:
                conn = utils.make_connection_to_db(connection_label)
                conn.close() # optional: close immediately or keep open for queries
                check_connection_dict[connection_label] = "✔️"

            except:
                check_connection_dict[connection_label] = "❌"

        rows = [{"Label": label, "Engine": st.session_state["db_connections_dict"][label][0],
                "Database": st.session_state["db_connections_dict"][label][3],
                "Connection OK": check_connection_dict[label]}
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
            st.write("")

        #Option to show all connections (if too many)
        if st.session_state["db_connections_dict"] and len(st.session_state["db_connections_dict"]) > max_length:
            with st.expander("🔎 Show all connections"):
                st.write("")
                st.dataframe(db_connections_df, hide_index=True)


    db_connection_type_list = ["Select an engine", "PostgreSQL"]
    with col1a:
        db_connection_type = st.selectbox("🖱️ Select a database engine:*", db_connection_type_list, key="key_db_connection_type")
    with col1b:
        label = st.text_input("⌨️ Enter label:*", key="key_connection_label")
        if label in st.session_state["db_connections_dict"]:
            with col1a:
                st.markdown(f"""<div class="custom-error-small">
                    ❌ Label <b>{label}</b> is already in use.<br>
                    You must choose a different label for this connection.
                        </div>""", unsafe_allow_html=True)
                st.write("")

    if db_connection_type == "PostgreSQL":
        with col1:
            col1a, col1b, col1c = st.columns(3)
        with col1a:
            postgres_host = st.text_input("⌨️ Enter host:*", value="localhost")
        with col1b:
            postgres_port = st.text_input("⌨️ Enter port:*", value="5432")
        with col1c:
            postgres_database = st.text_input("⌨️ Enter database name:*")
        with col1a:
            postgres_user = st.text_input("⌨️ Enter user:*", value="postgres")
        with col1b:
            postgres_password = st.text_input("⌨️ Enter password:*", type="password")

        with col1:
            col1a, col1b = st.columns([2,1])

        if (label and postgres_host and postgres_port and postgres_database
            and postgres_user and postgres_password and label not in st.session_state["db_connections_dict"]):
            with col1a:
                try:
                    conn = psycopg.connect(host=postgres_host, port=postgres_port,
                        dbname=postgres_database, user=postgres_user,
                        password=postgres_password)
                    st.button("Save", key="key_save_postgress_connection_button", on_click=save_postgress_connection)
                    conn.close() # optional: close immediately or keep open for queries

                except psycopg.OperationalError as e:
                    st.markdown(f"""<div class="custom-error-small">
                        ❌ <b>Connection failed.</b><br>
                        <small><b>Full error</b>: {e.args[0]} </small>
                    </div>""", unsafe_allow_html=True)
                    st.write("")

                except Exception as e:
                    st.markdown(f"""<div class="custom-error-small">
                        ❌ <b>Unexpected error.</b><br>
                        <small><b>Full error</b>: {str(e)} </small>
                    </div>""", unsafe_allow_html=True)
                    st.write("")

    if not st.session_state["db_connections_dict"] and st.session_state["db_connection_removed_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="custom-success">
                ✅ The <b>connection to the database</b> has been removed!
            </div>""", unsafe_allow_html=True)
        st.session_state["db_connection_removed_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()


    #PURPLE HEADING - REMOVE CONNECTION
    if st.session_state["db_connections_dict"]:
        with col1:
            st.write("_______")
            st.markdown("""<div class="purple-heading">
                    🗑️ Remove Connection
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["db_connection_removed_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="custom-success">
                    ✅ The <b>connection/s to the database</b> have been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["db_connection_removed_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()

        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            list_to_choose = list(reversed(list(st.session_state["db_connections_dict"].keys())))
            if len(list_to_choose) > 1:
                list_to_choose.insert(0, "Select all")
            connection_labels_to_remove_list = st.multiselect("🖱️ Select connections:*", list_to_choose,
                key="key_connection_labels_to_remove_list")

        if "Select all" in connection_labels_to_remove_list:
            connection_labels_to_remove_list = list(st.session_state["db_connections_dict"].keys())

        if connection_labels_to_remove_list != "Select a connection":
            with col1a:
                st.button("Remove", key="key_remove_connection_button", on_click=remove_connection)


#________________________________________________
# QUERY DATA
with tab2:

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
            rows.append({"Label": label, "Connection": connection,
                    "Database": database, "Query": sql_query,
                    "Query OK": sql_query_ok_flag})

        sql_queries_df = pd.DataFrame(rows)
        last_sql_queries_df = sql_queries_df.head(utils.get_max_length_for_display()[1])

        max_length = utils.get_max_length_for_display()[1]   # max number of connections to show directly
        if st.session_state["sql_queries_dict"]:
            if len(st.session_state["sql_queries_dict"]) < max_length:
                st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                        🔎 saved SQL queries
                    </div>""", unsafe_allow_html=True)
                st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                        🔎 last saved SQL queries
                    </div>""", unsafe_allow_html=True)
                st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        (complete list below)
                    </div>""", unsafe_allow_html=True)
            st.dataframe(last_sql_queries_df, hide_index=True)
            st.write("")

        #Option to show all connections (if too many)
        if st.session_state["sql_queries_dict"] and len(st.session_state["sql_queries_dict"]) > max_length:
            with st.expander("🔎 Show all saved SQL queries"):
                st.write("")
                st.dataframe(sql_queries_df, hide_index=True)

    #PURPLE HEADING - ADD NEW TRIPLESMAP
    with col1:
        st.markdown("""<div class="purple-heading">
                🔎 View Table
            </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns(2)

    with col1a:
        list_to_choose = list(reversed(list(st.session_state["db_connections_dict"].keys())))
        list_to_choose.insert(0, "Select a connection")
        connection_for_table_display = st.selectbox("🖱️ Select a connection:*", list_to_choose,
            key="key_connection_for_table_display")

    if connection_for_table_display != "Select a connection":

        try:
            conn = utils.make_connection_to_db(connection_for_table_display)
            connection_ok_flag = True

        except:
            with col1a:
                st.markdown(f"""<div class="custom-error-small">
                    ❌ The connection <b>{connection_label}</b> is not working.
                    Please remove it and save it again in the <b>Manage Connections</b> pannel.
                </div>""", unsafe_allow_html=True)
                st.write("")
            connection_ok_flag = False

        if connection_ok_flag:

            cur = conn.cursor()   # create a cursor

            cur.execute("""SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE';""")
            db_tables = [row[0] for row in cur.fetchall()]

            with col1b:
                list_to_choose = db_tables
                list_to_choose.insert(0, "Select a table")
                selected_db_table = st.selectbox("🖱️ Choose a table:*", list_to_choose,
                    key="key_selected_db_table")

            if selected_db_table != "Select a table":

                cur.execute(f"SELECT * FROM {selected_db_table};")
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

                df = pd.DataFrame(rows, columns=columns)

                with col1:
                    max_rows = utils.get_max_length_for_display()[2]
                    max_cols = utils.get_max_length_for_display()[3]

                    limited_df = df.iloc[:, :max_cols]   # limit number of columns

                    # Slice rows if needed
                    if len(df) > max_rows and df.shape[1] > max_cols:
                        st.markdown(f"""<div class="custom-warning-small">
                            ⚠️ Showing the <b>first {max_rows} rows</b> (out of {len(df)})
                            and the <b>first {max_cols} columns</b> (out of {df.shape[1]}).
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                    elif len(df) > max_rows:
                        st.markdown(f"""<div class="custom-warning-small">
                            ⚠️ Showing the <b>first {max_rows} rows</b> (out of {len(df)}).
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                    elif df.shape[1] > max_cols:
                        st.markdown(f"""<div class="custom-warning-small">
                            ⚠️ Showing the <b>first {max_cols} columns</b> (out of {df.shape[1]}).
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                    st.dataframe(limited_df.head(max_rows), hide_index=True)

                cur.close()
                conn.close()


    #PURPLE HEADING - QUERY DATA
    with col1:
        st.write("________")
        st.markdown("""<div class="purple-heading">
                ❔ Query Data
            </div>""", unsafe_allow_html=True)
        st.write("")

    if st.session_state["sql_query_saved_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="custom-success">
                ✅ The <b>SQL query</b> has been saved!
            </div>""", unsafe_allow_html=True)
        st.session_state["sql_query_saved_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
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
            sql_query_label = st.text_input("⌨️ Enter query label (to save):",
                key="key_sql_query_label")
            if sql_query_label and sql_query_label not in st.session_state["sql_queries_dict"]:
                sql_query_label_ok_flag = True
            elif sql_query_label:
                sql_query_label_ok_flag = False
                with col1b:
                    st.markdown(f"""<div class="custom-error-small">
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
                st.markdown(f"""<div class="custom-error-small">
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
                    with col1b:
                        st.markdown(f"""<div class="custom-error-small">
                            ❌ <b>Invalid SQL syntax</b>. Please check your query.<br>
                            <small><b> Full error:</b> {e}</small>
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                    sql_query_ok_flag = False

            if sql_query and sql_query_ok_flag:

                if sql_query_label_ok_flag:
                    with col1:
                        st.button("Save", key="key_save_sql_query_button",
                            on_click=save_sql_query)

                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                df = pd.DataFrame(rows, columns=columns)


                with col1:
                    max_rows = utils.get_max_length_for_display()[2]
                    max_cols = utils.get_max_length_for_display()[3]

                    limited_df = df.iloc[:, :max_cols]   # limit number of columns

                    # Slice rows if needed
                    if len(df) > max_rows and df.shape[1] > max_cols:
                        st.markdown(f"""<div class="custom-warning-small">
                            ⚠️ Showing the <b>first {max_rows} rows</b> (out of {len(df)})
                            and the <b>first {max_cols} columns</b> (out of {df.shape[1]}).
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                    elif len(df) > max_rows:
                        st.markdown(f"""<div class="custom-warning-small">
                            ⚠️ Showing the <b>first {max_rows} rows</b> (out of {len(df)}).
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                    elif df.shape[1] > max_cols:
                        st.markdown(f"""<div class="custom-warning-small">
                            ⚠️ Showing the <b>first {max_cols} columns</b> (out of {df.shape[1]}).
                        </div>""", unsafe_allow_html=True)
                        st.write("")
                    st.dataframe(limited_df.head(max_rows), hide_index=True)





with tab3:
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown(f"""
        <div style="background-color:#f8d7da; padding:1em;
                    border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
            ❌ This panel is not ready yet.
        </div>
        """, unsafe_allow_html=True)
        st.stop()

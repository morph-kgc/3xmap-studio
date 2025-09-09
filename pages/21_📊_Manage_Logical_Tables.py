import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace
import utils
import time
import pandas as pd

import psycopg2

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
    # delete connection________________
    del st.session_state["db_connections_dict"][connection_label_to_remove]
    # store information________________
    st.session_state["db_connection_removed_ok_flag"] = True  # for success message
    # reset fields_____________________
    st.session_state["key_connection_label_to_remove"] = "Select a connection"


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

    #PURPLE HEADING - ADD NEW TRIPLESMAP
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
        rows = [{"Label": label, "Engine": st.session_state["db_connections_dict"][label][0],
                "Database": st.session_state["db_connections_dict"][label][3]}
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
        if st.session_state["db_connections_dict"] and len(st.session_state["db_connections_dict"]) >= max_length:
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
                    conn = psycopg2.connect(host=postgres_host, port=postgres_port,
                        database=postgres_database, user=postgres_user,
                        password=postgres_password)
                    st.button("Save", key="key_save_postgress_connection_button", on_click=save_postgress_connection)
                    conn.close() # optional: close immediately or keep open for queries

                except psycopg2.OperationalError as e:
                    st.error(f"❌ Connection failed: {e.pgerror or str(e)}")

                except Exception as e:
                    st.error(f"⚠️ Unexpected error: {str(e)}")


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


    #PURPLE HEADING - ADD NEW TRIPLESMAP
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
                    ✅ The <b>connection to the database</b> has been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["db_connection_removed_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()

        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            list_to_choose = list(reversed(list(st.session_state["db_connections_dict"].keys())))
            list_to_choose.insert(0, "Select a connection")
            connection_label_to_remove = st.selectbox("🖱️ Select a connection:*", list_to_choose,
                key="key_connection_label_to_remove")

            if connection_label_to_remove != "Select a connection":
                st.button("Remove", key="key_remove_connection_button", on_click=remove_connection)


        # # Create a cursor
        # cur = conn.cursor()
        #
        # # Run a query
        # cur.execute("SELECT * FROM tb_categories;")
        # rows = cur.fetchall()
        #
        # # Print results
        # for row in rows:
        #     st.write(row)
        #
        # # Clean up
        # cur.close()
        # conn.close()

with tab2:
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown(f"""
        <div style="background-color:#f8d7da; padding:1em;
                    border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
            ❌ This panel is not ready yet.
        </div>
        """, unsafe_allow_html=True)
        st.stop()

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

import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle
from rdflib.namespace import split_uri
from rdflib.namespace import RDF, RDFS, DC, DCTERMS, OWL, XSD
from streamlit_js_eval import streamlit_js_eval
import io
import time   # for success messages

import rdflib, networkx as nx, matplotlib.pyplot as plt
from pyvis.network import Network
import streamlit.components.v1 as components
import networkx as nx

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

# START PAGE_____________________________________________________________________

#____________________________________________________________
# PANELS OF THE PAGE (tabs)
tab1, tab2, tab3, tab4 = st.tabs(["Network", "Predefined Searches", "SPARQL", "Preview"])

# ERROR MESSAGE IF NO MAPPING LOADED--------------------------------------------
col1, col2 = st.columns([2,1])
if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
    with col1:
        utils.get_missing_g_mapping_error_message_different_page()
        st.stop()

#________________________________________________
# NETWORK VISUALISATION
with tab1:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
    with col2b:
        utils.get_corner_status_message_mapping()

    #PURPLE HEADING - PREVIEW
    with col1:
        st.markdown("""<div class="purple-heading">
                🕸️ Network Visualisation
            </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([2,1])

    color_dict = utils.get_colors_for_network_dict()
    s_node_color = color_dict["s_node_color"]
    o_node_color = color_dict["o_node_color"]
    p_edge_color = color_dict["p_edge_color"]
    p_edge_label_color = color_dict["p_edge_label_color"]
    background_color = color_dict["background_color"]
    legend_font_color = color_dict["legend_font_color"]

    list_to_choose_tm = []
    for sm in st.session_state["g_mapping"].objects(predicate=RML.subjectMap):
        for rule in utils.get_rules_for_sm(sm):
            list_to_choose_tm.append(rule[3])
            break

    with col1a:
        list_to_choose = sorted(list_to_choose_tm.copy())
        list_to_choose.insert(0, "Select all")
        tm_for_network_list = st.multiselect("🖱️ Select TriplesMaps:*", list_to_choose,
            default=["Select all"], key="key_tm_for_network_list")
        if "Select all" in tm_for_network_list:
            tm_for_network_list = list_to_choose_tm

        if list_to_choose == ["Select all"]:
            with col1b:
                st.markdown(f"""<div class="error-message">
                    ❌ Mapping <b>{st.session_state["g_label"]}</b> contains no TriplesMaps.
                    <small>You can add them in the <b>🏗️Build Mapping</b> page.</small>
                </div>""", unsafe_allow_html=True)

    sm_for_network_list = []
    for sm in st.session_state["g_mapping"].objects(predicate=RML.subjectMap):
        for rule in utils.get_rules_for_sm(sm):
            if rule[3] in tm_for_network_list:
                sm_for_network_list.append(sm)
                break

    G = nx.DiGraph()
    legend_dict = {}
    for sm in sm_for_network_list:
        for rule in utils.get_rules_for_sm(sm):
            s, p, o, tm = rule

            s_id, legend_dict = utils.get_unique_node_label(s, "s", legend_dict)
            p_label, legend_dict = utils.get_unique_node_label(p, "p", legend_dict)
            o_id, legend_dict = utils.get_unique_node_label(o, "o", legend_dict)

            # Add nodes and edge
            G.add_node(s_id, label=s_id, color=s_node_color, shape="ellipse")
            if o_id not in G:
                G.add_node(o_id, label=o_id, color=o_node_color, shape="ellipse")  # conditional so that if node is also sm it will have s_node_color
            G.add_edge(s_id, o_id, label=p_label, color=p_edge_color, font={"color": p_edge_label_color})


    # Create Pyvis network
    G_net = Network(height="600px", width="100%", directed=True)
    G_net.from_nx(G)

    # Optional: improve layout and styling
    G_net.repulsion(node_distance=200, central_gravity=0.3, spring_length=200, spring_strength=0.05)
    G_net.set_options("""{
        "nodes": {"shape": "ellipse", "borderWidth": 0,
            "font": {"size": 14, "face": "arial", "align": "center",
              "color": "#ffffff"},
            "color": {"background": "#87cefa", "border": "#87cefa"}},
         "edges": {"width": 3, "arrows":
            {"to": {"enabled": true, "scaleFactor": 0.5}},
            "color": {"color": "#1e1e1e"},
            "font": {"size": 10, "align": "middle", "color": "#1e1e1e"},
            "smooth": false},
          "physics": {"enabled": true},
          "interaction": {"hover": true},
          "layout": {"improvedLayout": true}
        }""")

    # Render only if needed
    if sm_for_network_list:
        # Generate HTML string
        html = G_net.generate_html()

        # Inject background color
        html = html.replace('<div id="mynetwork"',
            f'<div id="mynetwork" style="background-color: {background_color};"')

        # Display in Streamlit
        with col1:
            components.html(html, height=600)

        # Create and display legend
        for letter in ["s", "p", "o"]:
            legend_flag = False
            legend_html = "<div style='font-family: sans-serif; font-size: 14px;'>"
            if letter == "s":
                legend_html += "<p>🔑 Subject legend</p>"
                object_color = s_node_color
            elif letter == "p":
                legend_html += "<p>🔑 Predicate legend</p>"
                object_color = p_edge_color
            elif letter == "o":
                legend_html += "<p>🔑 Object legend</p>"
                object_color = o_node_color

            for key, value in legend_dict.items():
                if key.startswith(letter):
                    legend_html += ("<div style='display: flex; align-items: flex-start; margin-bottom: 4px;'>"
                        f"<div style='min-width: 60px; font-weight: bold;'><code>{str(key)}</code></div>"
                        f"<div style='flex: 1; max-width: 100%; word-break: break-word; white-space: normal; font-size: 12px;'>{str(value)}</div>"
                        "</div>")
                    legend_flag = True

            legend_html += "</div>"

            with col2:
                if legend_flag:
                    st.markdown(f"""<div style='border-left: 4px solid {object_color}; padding: 0.4em 0.6em;
                        color: {legend_font_color}; font-size: 0.85em; font-family: "Source Sans Pro", sans-serif;
                        margin: 0.5em 0; background-color: {background_color}; border-radius: 4px; box-sizing: border-box;
                        word-wrap: break-word;'>
                            {legend_html}
                        </div>""", unsafe_allow_html=True)

#________________________________________________
# PREDEFINED SEARCHES
with tab2:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
    with col2b:
        utils.get_corner_status_message_mapping()

    #PURPLE HEADING - ADD NEW TRIPLESMAP
    with col1:
        st.markdown("""<div class="purple-heading">
                📌 Predefined Searches
            </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([1,2])

    predefined_searches_list = ["Select search", "Rules", "TriplesMaps", "Subject Maps", "Predicate-Object Maps",
        "Used Classes", "Used Properties", "Incomplete Nodes", "Orphaned Nodes", "All Triples"]

    with col1a:
        selected_predefined_search = st.selectbox("🔍 Select search:*", predefined_searches_list,
            key="key_selected_predefined_search")

    if selected_predefined_search == "Rules":
        with col1b:
            tm_dict = utils.get_tm_dict()
            list_to_choose = list(reversed(list(tm_dict)))
            if len(list_to_choose) > 1:
                selected_tm_for_display_list = st.multiselect("⚙️ Filter by TriplesMaps (opt):", list_to_choose,
                    placeholder="No filter", key="key_selected_tm_for_display_list_1")
            else:
                selected_tm_for_display_list = []

        with col1:
            col1a, col1b, col1c, col1d = st.columns(4)

        with col1a:
            limit = st.text_input("⌨️ Enter limit (opt):", key="key_limit")
        with col1b:
            offset = st.text_input("⌨️ Enter offset (opt):", key="key_offset")
        with col1c:
            list_to_choose = ["No order", "Ascending", "Descending"]
            order_clause = st.selectbox("🖱️ Select order (opt):", list_to_choose,
                key="key_order_clause")
        with col1d:
            st.write("")
            visualisation_option = st.radio("", ["👁️ Visual", "📅 Table"], label_visibility="collapsed",
                key="key_visualisation_option")

            query = """PREFIX rml: <http://w3id.org/rml/>

                SELECT DISTINCT ?tm ?sm ?pom ?om ?subject_value ?predicate ?object_value WHERE {
                  ?tm rml:subjectMap ?sm .
                  ?tm rml:predicateObjectMap ?pom .
                  ?pom rml:predicate ?predicate .
                  ?pom rml:objectMap ?om .

                  OPTIONAL { ?sm rml:template ?subject_value . }
                  OPTIONAL { ?sm rml:constant ?subject_value . }
                  OPTIONAL { ?sm rml:reference ?subject_value . }

                  OPTIONAL { ?om rml:template ?object_value . }
                  OPTIONAL { ?om rml:constant ?object_value . }
                  OPTIONAL { ?om rml:reference ?object_value . }
                }"""

            if order_clause == "Ascending":
                query += f"ORDER BY ASC(?tm) "
            elif order_clause == "Descending":
                query += f"ORDER BY DESC(?tm) "

            if limit:
                query += f"LIMIT {limit} "

            if offset:
                query += f"OFFSET {offset}"

            results = st.session_state["g_mapping"].query(query)

            df_data = []

            for row in results:
                tm = row.tm if hasattr(row, "tm") and row.tm else ""
                sm = row.sm if hasattr(row, "sm") and row.sm else ""
                pom = row.pom if hasattr(row, "pom") and row.pom else ""
                om = row.om if hasattr(row, "om") and row.om else ""

                subject = row.subject_value if hasattr(row, "subject_value") and row.subject_value else ""
                predicate = row.predicate if hasattr(row, "predicate") and row.predicate else ""
                object_ = row.object_value if hasattr(row, "object_value") and row.object_value else ""

                # Optional: apply label formatting
                tm_label = utils.get_node_label(tm)

                selected_tm_for_display_list = list(tm_dict) if not selected_tm_for_display_list else selected_tm_for_display_list
                if tm_label in selected_tm_for_display_list:
                    row_dict = {
                        "Subject": utils.format_iri_to_prefix_label(subject),
                        "Predicate": utils.format_iri_to_prefix_label(predicate),
                        "Object": utils.format_iri_to_prefix_label(object_),
                        "TriplesMap": utils.format_iri_to_prefix_label(tm),
                        "Subject Map": utils.format_iri_to_prefix_label(sm),
                        "Predicate-Object Map": utils.format_iri_to_prefix_label(pom),
                        "Object Map": utils.format_iri_to_prefix_label(om)}
                    df_data.append(row_dict)

            # Create DataFrame
            df = pd.DataFrame(df_data)

            # Drop empty columns
            df = df.loc[:, df.apply(lambda col: col.replace('', pd.NA).notna().any())]

            # Display
            with col1:
                if visualisation_option == "👁️ Visual":
                    inner_html = ""
                    for row in df.itertuples(index=False):
                        s = row.Subject
                        p = row.Predicate
                        o = row.Object
                        small_header, new_inner_html = utils.preview_rule_list(s, p, o)
                        inner_html += new_inner_html

                    st.markdown(f"""<div class="info-message-blue">
                        <b>RESULTS ({len(df)}):</b>
                    </div>""", unsafe_allow_html=True)
                    st.markdown(f"""<div class="gray-preview-message" style="margin-top:0px; padding-top:4px;">
                            {small_header}{inner_html}
                        </div>""", unsafe_allow_html=True)

                elif visualisation_option == "📅 Table":
                    st.markdown(f"""<div class="info-message-blue">
                        <b>RESULTS ({len(df)}):</b>
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ No results.
                    </div>""", unsafe_allow_html=True)

            # for row in results:

    if selected_predefined_search == "TriplesMaps":

        with col1b:
            tm_dict = utils.get_tm_dict()
            list_to_choose = list(reversed(list(tm_dict)))
            if len(list_to_choose) > 1:
                selected_tm_for_display_list = st.multiselect("️⚙️ Filter by TriplesMaps (optional):", list_to_choose,
                    placeholder="No filter", key="key_selected_tm_for_display_list_1")
            else:
                selected_tm_for_display_list = []

        with col1:
            col1a, col1b, col1c = st.columns(3)

        with col1a:
            limit = st.text_input("⌨️ Enter limit (optional):", key="key_limit")
        with col1b:
            offset = st.text_input("⌨️ Enter offset (optional):", key="key_offset")
        with col1c:
            list_to_choose = ["No order", "Ascending", "Descending"]
            order_clause = st.selectbox("🖱️ Select order (optional):", list_to_choose,
                key="key_order_clause")

            query = """PREFIX rml: <http://w3id.org/rml/>
                SELECT ?tm ?logicalSource ?source ?referenceFormulation ?iterator ?tableName ?sqlQuery WHERE {
                  ?tm rml:logicalSource ?logicalSource .
                  OPTIONAL { ?logicalSource rml:source ?source }
                  OPTIONAL { ?logicalSource rml:referenceFormulation ?referenceFormulation }
                  OPTIONAL { ?logicalSource rml:iterator ?iterator }
                  OPTIONAL { ?logicalSource rml:tableName ?tableName }
                  OPTIONAL { ?logicalSource rml:query ?sqlQuery }
                }"""

            if order_clause == "Ascending":
                query += f"ORDER BY ASC(?tm) "
            elif order_clause == "Descending":
                query += f"ORDER BY DESC(?tm) "

            if limit:
                query += f"LIMIT {limit} "

            if offset:
                query += f"OFFSET {offset}"

            results = st.session_state["g_mapping"].query(query)

            df_data = []

            for row in results:
                tm = row.tm if hasattr(row, "tm") and row.tm else ""
                logical_table = row.logicalTable if hasattr(row, "logicalTable") and row.logicalTable else ""
                table_name = row.tableName if hasattr(row, "tableName") and row.tableName else ""
                sql_query = row.sqlQuery if hasattr(row, "sqlQuery") and row.sqlQuery else ""
                logical_source = row.logicalSource if hasattr(row, "logicalSource") and row.logicalSource else ""
                source = row.source if hasattr(row, "source") and row.source else ""
                reference_formulation = str(row.referenceFormulation) if hasattr(row, "referenceFormulation") and row.referenceFormulation else ""

                tm_label = utils.get_node_label(tm)

                selected_tm_for_display_list = list(tm_dict) if not selected_tm_for_display_list else selected_tm_for_display_list
                if tm_label in selected_tm_for_display_list:
                    row_dict = {"TriplesMap": utils.format_iri_to_prefix_label(tm),
                        "View": sql_query,
                        "Table": table_name,
                        "Source": source,
                        "Reference Formulation": utils.format_iri_to_prefix_label(reference_formulation),
                        "Logical Source": logical_source}
                    df_data.append(row_dict)

            # Create DataFrame
            df = pd.DataFrame(df_data)

            # Drop empty columns
            df = df.loc[:, df.apply(lambda col: col.replace('', pd.NA).notna().any())]

            # Display
            with col1:
                if not df.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>RESULTS ({len(df)}):</b>
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ No results.
                    </div>""", unsafe_allow_html=True)

    if selected_predefined_search == "Subject Maps":

        with col1b:
            tm_dict = utils.get_tm_dict()
            list_to_choose = list(reversed(list(tm_dict)))
            if len(list_to_choose) > 1:
                selected_tm_for_display_list = st.multiselect("⚙️ Filter by TriplesMaps (optional):", list_to_choose,
                    placeholder="No filter", key="key_selected_tm_for_display_list_2")
            else:
                selected_tm_for_display_list = []

        with col1:
            col1a, col1b, col1c = st.columns(3)

        with col1a:
            limit = st.text_input("⌨️ Enter limit (optional):", key="key_limit")
        with col1b:
            offset = st.text_input("⌨️ Enter offset (optional):", key="key_offset")
        with col1c:
            list_to_choose = ["No order", "Ascending", "Descending"]
            order_clause = st.selectbox("🖱️ Select order (optional):", list_to_choose,
                key="key_order_clause")

        query = f"""PREFIX rml: <http://w3id.org/rml/>
            SELECT ?tm ?subjectMap ?template ?constant ?reference ?column ?termType ?graph (GROUP_CONCAT(?class; separator=", ") AS ?classes) WHERE {{
              ?tm rml:subjectMap ?subjectMap .
              OPTIONAL {{ ?subjectMap rml:template ?template }}
              OPTIONAL {{ ?subjectMap rml:constant ?constant }}
              OPTIONAL {{ ?subjectMap rml:reference ?reference }}
              OPTIONAL {{ ?subjectMap rml:class ?class }}
              OPTIONAL {{ ?subjectMap rml:termType ?termType }}
              OPTIONAL {{ ?subjectMap rml:graph ?graph }}
            }}
            GROUP BY ?tm ?subjectMap ?template ?reference ?column ?termType ?graph
        """

        if order_clause == "Ascending":
            query += f"ORDER BY ASC(?subjectMap) "
        elif order_clause == "Descending":
            query += f"ORDER BY DESC(?subjectMap) "

        if limit:
            query += f"LIMIT {limit} "

        if offset:
            query += f"OFFSET {offset}"

        results = st.session_state["g_mapping"].query(query)

        df_data = []

        for row in results:
            tm = row.tm if row.tm else ""
            subject_map = row.subjectMap if row.subjectMap else ""
            template = str(row.template) if row.template else ""
            constant = str(row.constant) if row.constant else ""
            reference = str(row.reference) if row.reference else ""
            if template:
                sm_rule_type = "Template"
                sm_rule = template
            elif constant:
                sm_rule_type = "Constant"
                sm_rule = constant
            elif reference:
                sm_rule_type = "Reference"
                sm_rule = reference
            else:
                sm_rule_type = ""
                sm_rule = ""
            raw_classes = str(row["classes"]) if row["classes"] else ""
            class_list = [utils.format_iri_to_prefix_label(c) for c in raw_classes.split(",") if c.strip()]
            class_list_to_string = ", ".join(class_list)
            term_type = str(row.termType) if row.termType else ""
            graph = str(row.graph) if row.graph else ""

            tm_label = utils.get_node_label(tm)
            sm_label = utils.get_node_label(subject_map)

            selected_tm_for_display_list = list(tm_dict) if not selected_tm_for_display_list else selected_tm_for_display_list
            if tm_label in selected_tm_for_display_list:
                row_dict = {"Rule": utils.format_iri_to_prefix_label(sm_rule),
                    "Type": sm_rule_type,
                    "Class": class_list_to_string,
                    "Term Type": utils.format_iri_to_prefix_label(term_type),
                    "TriplesMap": utils.format_iri_to_prefix_label(tm),
                    "Graph": utils.format_iri_to_prefix_label(graph),
                    "Subject Map": utils.format_iri_to_prefix_label(subject_map)}
                df_data.append(row_dict)

        df = pd.DataFrame(df_data)
        # Drop columns that are entirely empty (all values are NaN or empty strings)
        df = df.loc[:, df.apply(lambda col: col.replace('', pd.NA).notna().any())]


        with col1:
            st.write("")

            if not df.empty:
                st.markdown(f"""<div class="info-message-blue">
                    <b>RESULTS ({len(df)}):</b>
                </div>""", unsafe_allow_html=True)
                st.dataframe(df, hide_index=True)
            else:
                st.markdown("""<div class="warning-message">⚠️ No results.</div>""", unsafe_allow_html=True)

    if selected_predefined_search == "Predicate-Object Maps":

        with col1b:
            tm_dict = utils.get_tm_dict()
            list_to_choose = list(reversed(list(tm_dict)))
            list_to_choose.insert(0, "Select TriplesMap")
            tm_label_for_search = st.selectbox("🖱️ Select TriplesMap:*", list_to_choose,
                key="key_tm_label_for_search")

        if tm_label_for_search != "Select TriplesMap":
            tm_iri_for_search = tm_dict[tm_label_for_search]

            list_to_choose = []
            for pom in st.session_state["g_mapping"].objects(tm_iri_for_search, RML.predicateObjectMap):
                list_to_choose.append(pom)
            if len(list_to_choose) > 1:
                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    selected_pom_for_display_list = st.multiselect("⚙️ Filter by Predicate-Object Maps (optional):", list_to_choose,
                        placeholder="No filter", key="key_selected_pom_for_display_list")
            else:
                selected_pom_for_display_list = []

            with col1:
                col1a, col1b, col1c = st.columns(3)

            with col1a:
                limit = st.text_input("⌨️ Enter limit (optional):", key="key_limit")
            with col1b:
                offset = st.text_input("⌨️ Enter offset (optional):", key="key_offset")
            with col1c:
                list_to_choose = ["No order", "Ascending", "Descending"]
                order_clause = st.selectbox("🖱️ Select order (optional):", list_to_choose,
                    key="key_order_clause")

            query = f"""PREFIX rml: <http://w3id.org/rml/>
                SELECT ?pom ?predicate ?objectMap ?template ?constant ?reference ?termType ?datatype ?language ?graphMap WHERE {{
                  <{tm_iri_for_search}> rml:predicateObjectMap ?pom .
                  OPTIONAL {{ ?pom rml:predicate ?predicate }}
                  OPTIONAL {{ ?pom rml:objectMap ?objectMap }}
                  OPTIONAL {{ ?objectMap rml:template ?template }}
                  OPTIONAL {{ ?objectMap rml:constant ?constant }}
                  OPTIONAL {{ ?objectMap rml:reference ?reference }}
                  OPTIONAL {{ ?objectMap rml:termType ?termType }}
                  OPTIONAL {{ ?objectMap rml:datatype ?datatype }}
                  OPTIONAL {{ ?objectMap rml:language ?language }}
                  OPTIONAL {{ ?objectMap rml:graphMap ?graphMap }}
                }}
            """


            if order_clause == "Ascending":
                query += f"ORDER BY ASC(?pom) "
            elif order_clause == "Descending":
                query += f"ORDER BY DESC(?pom) "

            if limit:
                query += f"LIMIT {limit} "

            if offset:
                query += f"OFFSET {offset}"

            results = st.session_state["g_mapping"].query(query)

            df_data = []
            for row in results:
                pom = row.pom if row.pom else ""
                predicate = str(row.predicate) if row.predicate else ""
                object_map = row.objectMap if row.objectMap else ""
                template = str(row.template) if row.template else ""
                constant = str(row.constant) if row.constant else ""
                reference = str(row.reference) if row.reference else ""
                if template:
                    pom_rule_type = "Template"
                    pom_rule = template
                elif constant:
                    pom_rule_type = "Constant"
                    pom_rule = constant
                elif reference:
                    pom_rule_type = "Reference"
                    pom_rule = reference
                else:
                    pom_rule_type = ""
                    pom_rule = ""
                term_type = str(row.termType) if row.termType else ""
                datatype = str(row.datatype) if row.datatype else ""
                language = str(row.language) if row.language else ""
                graph_map = str(row.graphMap) if row.graphMap else ""

                pom_label = utils.get_node_label(pom)
                om_label = utils.get_node_label(object_map)

                all_pom_list = list(utils.get_pom_dict())
                selected_pom_for_display_list = all_pom_list if not selected_pom_for_display_list else selected_pom_for_display_list
                if pom in selected_pom_for_display_list:
                    row_dict = {"Predicate": utils.format_iri_to_prefix_label(predicate),
                        "Rule": utils.format_iri_to_prefix_label(pom_rule),
                        "Type": pom_rule_type,
                        "TermType": utils.format_iri_to_prefix_label(term_type),
                        "Datatype": utils.format_iri_to_prefix_label(datatype),
                        "Language": utils.format_iri_to_prefix_label(language),
                        "Graph Map": utils.format_iri_to_prefix_label(graph_map),
                        "Predicate-Object Map": utils.format_iri_to_prefix_label(pom),
                        "Object Map": utils.format_iri_to_prefix_label(object_map)}

                    df_data.append(row_dict)
            df = pd.DataFrame(df_data)
            # Drop columns that are entirely empty (all values are NaN or empty strings)
            df = df.loc[:, df.apply(lambda col: col.replace('', pd.NA).notna().any())]

            with col1:
                if not df.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>RESULTS ({len(df)}):</b>
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ No results.
                    </div>""", unsafe_allow_html=True)

    if selected_predefined_search == "Used Classes":

        with col1b:
            classes_set = set()
            for sm, rdf_class in st.session_state["g_mapping"].subject_objects(predicate=RML["class"]):
                rdf_class_label = utils.get_node_label(rdf_class)
                classes_set.add(rdf_class_label)

            list_to_choose_classes = sorted(list(classes_set))
            if len(list_to_choose_classes) > 1:
                selected_classes_for_display_list = st.multiselect("⚙️ Filter by Class (optional):", list_to_choose_classes,
                    placeholder="No filter", key="key_selected_classes_for_display_list")
            else:
                selected_classes_for_display_list = []

        with col1:
            col1a, col1b, col1c = st.columns(3)

        with col1a:
            limit = st.text_input("⌨️ Enter limit (optional):", key="key_limit")
        with col1b:
            offset = st.text_input("⌨️ Enter offset (optional):", key="key_offset")
        with col1c:
            list_to_choose = ["No order", "Ascending", "Descending"]
            order_clause = st.selectbox("🖱️ Select order (optional):", list_to_choose,
                key="key_order_clause")

        query = """PREFIX rml: <http://w3id.org/rml/>
            SELECT DISTINCT ?tm ?sm ?class WHERE {
              ?tm rml:subjectMap ?sm .
              ?sm rml:class ?class .
            }"""

        if order_clause == "Ascending":
            query += f"ORDER BY ASC(?class) "
        elif order_clause == "Descending":
            query += f"ORDER BY DESC(?class) "

        if limit:
            query += f"LIMIT {limit} "

        if offset:
            query += f"OFFSET {offset}"

        results = st.session_state["g_mapping"].query(query)

        df_data = []

        for row in results:
            tm = row.tm if hasattr(row, "tm") and row.tm else ""
            sm = row.sm if hasattr(row, "sm") and row.sm else ""
            rdf_class = row.get("class") if row.get("class") else ""
            class_label = utils.get_node_label(rdf_class)

            selected_classes_for_display_list = list_to_choose_classes if not selected_classes_for_display_list else selected_classes_for_display_list
            if class_label in selected_classes_for_display_list:
                df_data.append({"Class": utils.format_iri_to_prefix_label(rdf_class),
                    "TriplesMap": utils.format_iri_to_prefix_label(tm),
                    "Subject Map": utils.format_iri_to_prefix_label(sm)})

        df = pd.DataFrame(df_data)
        # Drop columns that are entirely empty (all values are NaN or empty strings)
        df = df.loc[:, df.apply(lambda col: col.replace('', pd.NA).notna().any())]

        with col1:
            if not df.empty:
                st.markdown(f"""<div class="info-message-blue">
                    <b>RESULTS ({len(df)}):</b>
                </div>""", unsafe_allow_html=True)
                st.dataframe(df, hide_index=True)
            else:
                st.markdown(f"""<div class="warning-message">
                    ⚠️ No results.
                </div>""", unsafe_allow_html=True)

    if selected_predefined_search == "Used Properties":

        with col1b:
            properties_set = set()
            for pom, predicate in st.session_state["g_mapping"].subject_objects(predicate=RML["predicate"]):
                predicate_label = utils.get_node_label(predicate)
                properties_set.add(predicate_label)

            list_to_choose_properties = sorted(list(properties_set))
            if len(list_to_choose_properties) > 1:
                selected_properties_for_display_list = st.multiselect("⚙️ Filter by Property (optional):", list_to_choose_properties,
                    placeholder="No filter", key="key_selected_properties_for_display_list")
            else:
                selected_properties_for_display_list = []

        with col1:
            col1a, col1b, col1c = st.columns(3)

        with col1a:
            limit = st.text_input("⌨️ Enter limit (optional):", key="key_limit")
        with col1b:
            offset = st.text_input("⌨️ Enter offset (optional):", key="key_offset")
        with col1c:
            list_to_choose = ["No order", "Ascending", "Descending"]
            order_clause = st.selectbox("🖱️ Select order (optional):", list_to_choose,
                key="key_order_clause")

        query = """PREFIX rml: <http://w3id.org/rml/>
        SELECT DISTINCT ?tm ?pom ?predicate WHERE {
          ?tm rml:predicateObjectMap ?pom .
          ?pom rml:predicate ?predicate .
        }"""

        if order_clause == "Ascending":
            query += f"ORDER BY ASC(?predicate) "
        elif order_clause == "Descending":
            query += f"ORDER BY DESC(?predicate) "

        if limit:
            query += f"LIMIT {limit} "

        if offset:
            query += f"OFFSET {offset}"

        results = st.session_state["g_mapping"].query(query)

        df_data = []

        for row in results:
            tm = row.tm if hasattr(row, "tm") and row.tm else ""
            pom = row.pom if hasattr(row, "pom") and row.pom else ""
            predicate = row.get("predicate") if row.get("predicate") else ""
            predicate_label = utils.get_node_label(predicate)

            selected_properties_for_display_list = list_to_choose_properties if not selected_properties_for_display_list else selected_properties_for_display_list
            if predicate_label in selected_properties_for_display_list:
                df_data.append({
                    "Property": utils.format_iri_to_prefix_label(predicate),
                    "TriplesMap": utils.format_iri_to_prefix_label(tm),
                    "Predicate-Object Map": utils.format_iri_to_prefix_label(pom)
                })

        df = pd.DataFrame(df_data)
        df = df.loc[:, df.apply(lambda col: col.replace('', pd.NA).notna().any())]

        with col1:
            if not df.empty:
                st.markdown(f"""<div class="info-message-blue">
                    <b>RESULTS ({len(df)}):</b>
                </div>""", unsafe_allow_html=True)
                st.dataframe(df, hide_index=True)
            else:
                st.markdown(f"""<div class="warning-message">
                    ⚠️ No results.
                </div>""", unsafe_allow_html=True)

    if selected_predefined_search == "Incomplete Nodes":

        with col1b:
            list_to_choose = ["Select node type", "TriplesMaps",
                "Predicate-Object Maps"]
            selected_incomplete_node_type = st.selectbox("🖱️ Select node type:*", list_to_choose,
                key="key_selected_incomplete_node_type")

        with col1:
            col1a, col1b, col1c = st.columns(3)

        with col1a:
            limit = st.text_input("⌨️ Enter limit (optional):", key="key_limit")
        with col1b:
            offset = st.text_input("⌨️ Enter offset (optional):", key="key_offset")
        with col1c:
            list_to_choose = ["No order", "Ascending", "Descending"]
            order_clause = st.selectbox("🖱️ Select order (optional):", list_to_choose,
                key="key_order_clause")

        if selected_incomplete_node_type == "TriplesMaps":
            query = """PREFIX rml: <http://w3id.org/rml/>
             SELECT DISTINCT ?tm WHERE {
              {?tm rml:logicalSource ?ls .
                FILTER NOT EXISTS { ?tm rml:subjectMap ?sm . }
              }
              UNION
              {?tm rml:logicalSource ?ls .
                FILTER NOT EXISTS { ?tm rml:predicateObjectMap ?pom . }
              }}"""

            if order_clause == "Ascending":
                query += f"ORDER BY ASC(?tm) "
            elif order_clause == "Descending":
                query += f"ORDER BY DESC(?tm) "

            if limit:
                query += f"LIMIT {limit} "

            if offset:
                query += f"OFFSET {offset}"

            results = st.session_state["g_mapping"].query(query)

            df_data = []

            for row in results:
                tm = row.get("tm")
                tm_label = utils.format_iri_to_prefix_label(tm) if tm else "(missing)"

                has_sm = bool(list(st.session_state["g_mapping"].objects(subject=tm, predicate=RML["subjectMap"])))
                has_pom = bool(list(st.session_state["g_mapping"].objects(subject=tm, predicate=RML["predicateObjectMap"])))

                df_data.append({"TriplesMap": tm_label,
                    "Has Subject Map": "❌" if not has_sm else "✔️",
                    "Has Predicate-Object Map": "❌" if not has_pom else "✔️"})

            df = pd.DataFrame(df_data)
            # Drop columns that are entirely empty (all values are NaN or empty strings)
            df = df.loc[:, df.apply(lambda col: col.replace('', pd.NA).notna().any())]


            with col1:
                if not df.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>RESULTS ({len(df)}):</b><br>
                        <small>TriplesMaps missing either a Subject Map or Predicate-Object Map.</small>
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ No results.
                    </div>""", unsafe_allow_html=True)

        if selected_incomplete_node_type == "Predicate-Object Maps":
            query = """PREFIX rml: <http://w3id.org/rml/>
             SELECT DISTINCT ?pom WHERE {
              ?pom a rml:PredicateObjectMap .
              FILTER NOT EXISTS {
                ?pom rml:objectMap ?om .}}"""

            if order_clause == "Ascending":
                query += f"ORDER BY ASC(?pom) "
            elif order_clause == "Descending":
                query += f"ORDER BY DESC(?pom) "

            if limit:
                query += f"LIMIT {limit} "

            if offset:
                query += f"OFFSET {offset}"

            results = st.session_state["g_mapping"].query(query)

            df_data = []

            for row in results:
                pom = row.get("pom")
                pom_label = utils.get_node_label(pom) if pom else "(missing)"

                # Check if objectMap is present
                has_om = bool(list(st.session_state["g_mapping"].objects(subject=pom, predicate=RML["objectMap"])))

                # Get predicate if defined
                predicate = st.session_state["g_mapping"].value(subject=pom, predicate=RML["predicate"])
                predicate_label = utils.get_node_label(predicate) if predicate else ""

                df_data.append({"Predicate-Object Map": pom_label,
                    "Predicate": predicate_label,
                    "Has Object Map": "❌" if not has_om else "✔️",
                    "Predicate-Object Map (complete)": str(pom) if pom else ""})

            df = pd.DataFrame(df_data)
            # Drop columns that are entirely empty (all values are NaN or empty strings)
            df = df.loc[:, df.apply(lambda col: col.replace('', pd.NA).notna().any())]

            with col1:
                if not df.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>RESULTS ({len(df)}):</b><br>
                        <small>Predicate-Object Maps missing an Object Map.</small>
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ No results.
                    </div>""", unsafe_allow_html=True)

    if selected_predefined_search == "Orphaned Nodes":

        with col1b:
            list_to_choose = ["Select node type", "Subject Maps", "Predicate-Object Maps", "Object Maps"]
            selected_orphaned_node_type = st.selectbox("🖱️ Select node type:*", list_to_choose,
                key="key_selected_orphaned_node_type")

        with col1:
            col1a, col1b, col1c = st.columns(3)

        with col1a:
            limit = st.text_input("⌨️ Enter limit (optional):", key="key_limit")
        with col1b:
            offset = st.text_input("⌨️ Enter offset (optional):", key="key_offset")
        with col1c:
            list_to_choose = ["No order", "Ascending", "Descending"]
            order_clause = st.selectbox("🖱️ Select order (optional):", list_to_choose,
                key="key_order_clause")

        if selected_orphaned_node_type == "Subject Maps":
            query = """PREFIX rml: <http://w3id.org/rml/>
             SELECT DISTINCT ?sm WHERE {{
              {{?sm rml:template ?template .
              }} UNION {{?sm rml:class ?class .
              }} UNION {{?sm rml:constant ?constant .
              }} UNION {{?sm rml:column ?column .
              }} UNION {{?sm rml:termType ?termType .
              }} UNION {{?sm rml:graphMap ?graphMap .
              }} UNION {{?sm rml:reference ?reference .}}

              FILTER NOT EXISTS {{?tm rml:subjectMap ?sm .}}
              FILTER NOT EXISTS {{?pom rml:predicateObjectMap ?sm .}}
              FILTER NOT EXISTS {{?om rml:objectMap ?sm .}}
            }}"""

            if order_clause == "Ascending":
                query += f"ORDER BY ASC(?sm) "
            elif order_clause == "Descending":
                query += f"ORDER BY DESC(?sm) "

            if limit:
                query += f"LIMIT {limit} "

            if offset:
                query += f"OFFSET {offset}"

            results = st.session_state["g_mapping"].query(query)

            df_data = []

            for row in results:
                sm = row.get("sm") if row.get("sm") else ""

                # Extract known properties from the graph
                g = st.session_state["g_mapping"]
                RR = Namespace("http://www.w3.org/ns/r2rml#")
                RML = Namespace("http://w3id.org/rml/")

                template = g.value(subject=sm, predicate=RML["template"])
                constant = g.value(subject=sm, predicate=RML["constant"])
                reference = g.value(subject=sm, predicate=RML["reference"])
                if template:
                    sm_rule_type = "Template"
                    sm_rule = template
                elif constant:
                    sm_rule_type = "Constant"
                    sm_rule = constant
                elif reference:
                    sm_rule_type = "Reference"
                    sm_rule = reference
                else:
                    sm_rule_type = ""
                    sm_rule = ""
                rdf_class = g.value(subject=sm, predicate=RML["class"])
                term_type = g.value(subject=sm, predicate=RML["termType"])
                graph_map = g.value(subject=sm, predicate=RML["graphMap"])

                row_dict = {"Subject Map": utils.format_iri_to_prefix_label(sm),
                    "Rule": str(sm_rule),
                    "Type": str(sm_rule_type),
                    "Class": utils.format_iri_to_prefix_label(rdf_class),
                    "Term Type": utils.format_iri_to_prefix_label(term_type),
                    "Graph Map": utils.format_iri_to_prefix_label(graph_map)}

                df_data.append(row_dict)

            df = pd.DataFrame(df_data)
            df = df.loc[:, df.apply(lambda col: col.replace('', pd.NA).notna().any())]


            with col1:
                if not df.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>RESULTS ({len(df)}):</b>
                        <small>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Possible Subject Maps not used by any TriplesMap]</small>
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ No results.
                    </div>""", unsafe_allow_html=True)

        if selected_orphaned_node_type == "Predicate-Object Maps":

            query = """PREFIX rml: <http://w3id.org/rml/>
             SELECT DISTINCT ?pom WHERE {
              {
                ?pom rml:predicate ?p .
              } UNION {
                ?pom rml:objectMap ?o .
              }
              FILTER NOT EXISTS {
                ?tm rml:predicateObjectMap ?pom .
              }}"""

            if order_clause == "Ascending":
                query += f"ORDER BY ASC(?pom) "
            elif order_clause == "Descending":
                query += f"ORDER BY DESC(?pom) "

            if limit:
                query += f"LIMIT {limit} "

            if offset:
                query += f"OFFSET {offset}"

            results = st.session_state["g_mapping"].query(query)

            df_data = []

            for row in results:
                pom = row.get("pom") if row.get("pom") else ""
                predicate = st.session_state["g_mapping"].value(subject=pom, predicate=RML["predicate"])

                row_dict = {"Predicate-Object Map": utils.format_iri_to_prefix_label(pom),
                    "Predicate": utils.format_iri_to_prefix_label(predicate)}

                df_data.append(row_dict)

            df = pd.DataFrame(df_data)
            df = df.loc[:, df.apply(lambda col: col.replace('', pd.NA).notna().any())]

            with col1:
                if not df.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>RESULTS ({len(df)}):</b>
                        <small>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Possible Predicate-Object Maps not used by any TriplesMap]
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ No results.
                    </div>""", unsafe_allow_html=True)

        if selected_orphaned_node_type == "Object Maps":

            query = """PREFIX rml: <http://w3id.org/rml/>
              SELECT DISTINCT ?om WHERE {{
              {{?om rml:constant ?c .
              }} UNION {{?om rml:column ?col .
              }} UNION {{?om rml:template ?tpl .
              }} UNION {{?om rml:termType ?tt .
              }} UNION {{?om rml:datatype ?dt .
              }} UNION {{?om rml:language ?lang .
              }} UNION {{?om rml:parentTriplesMap ?ptm .
              }} UNION {{?om rml:joinCondition ?jc .
              }} UNION {{?om rml:reference ?ref .}}

              FILTER NOT EXISTS {{?pom rml:objectMap ?om .}}
              FILTER NOT EXISTS {{?tm rml:subjectMap ?om .}}
            }}
            """

            if order_clause == "Ascending":
                query += f"ORDER BY ASC(?om) "
            elif order_clause == "Descending":
                query += f"ORDER BY DESC(?om) "

            if limit:
                query += f"LIMIT {limit} "

            if offset:
                query += f"OFFSET {offset}"

            results = st.session_state["g_mapping"].query(query)

            df_data = []

            for row in results:
                om = row.get("om") if row.get("om") else ""

                g = st.session_state["g_mapping"]

                template = g.value(subject=sm, predicate=RML["template"])
                constant = g.value(subject=sm, predicate=RML["constant"])
                reference = g.value(subject=sm, predicate=RML["reference"])
                if template:
                    om_rule_type = "Template"
                    om_rule = template
                elif constant:
                    om_rule_type = "Constant"
                    om_rule = constant
                elif reference:
                    om_rule_type = "Reference"
                    om_rule = reference
                else:
                    om_rule_type = ""
                    om_rule = ""
                term_type = g.value(subject=om, predicate=RML["termType"])
                datatype = g.value(subject=om, predicate=RML["datatype"])
                language = g.value(subject=om, predicate=RML["language"])
                parent_tm = g.value(subject=om, predicate=RML["parentTriplesMap"])
                join_condition = g.value(subject=om, predicate=RML["joinCondition"])

                row_dict = {"Object Map": utils.format_iri_to_prefix_label(om),
                        "Rule": utils.format_iri_to_prefix_label(om_rule),
                        "Type": str(om_rule_type),
                        "Term Type": utils.format_iri_to_prefix_label(term_type),
                        "Datatype": utils.format_iri_to_prefix_label(datatype),
                        "Language": utils.format_iri_to_prefix_label(language),
                        "Parent TriplesMap": utils.format_iri_to_prefix_label(parent_tm),
                        "Join Condition": utils.format_iri_to_prefix_label(join_condition)}

                df_data.append(row_dict)

            df = pd.DataFrame(df_data)
            df = df.loc[:, df.apply(lambda col: col.replace('', pd.NA).notna().any())]

            with col1:
                if not df.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>RESULTS ({len(df)}):</b>
                        <small>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Possible Object Maps not used by any Predicate-Object Map]
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ No results.
                    </div>""", unsafe_allow_html=True)

    if selected_predefined_search == "All Triples":

        with col1:
            col1a, col1b, col1c = st.columns(3)

        with col1a:
            limit = st.text_input("⌨️ Enter limit (optional):", key="key_limit")
        with col1b:
            offset = st.text_input("⌨️ Enter offset (optional):", key="key_offset")
        with col1c:
            list_to_choose = ["No order", "Ascending", "Descending"]
            order_clause = st.selectbox("🖱️ Select order (optional):", list_to_choose,
                key="key_order_clause")

            query = """SELECT ?s ?p ?o WHERE {
                ?s ?p ?o .}"""

            if order_clause == "Ascending":
                query += f"ORDER BY ASC(?s) "
            elif order_clause == "Descending":
                query += f"ORDER BY DESC(?s) "

            if limit:
                query += f"LIMIT {limit} "

            if offset:
                query += f"OFFSET {offset}"

            results = st.session_state["g_mapping"].query(query)

            df_data = []

            for row in results:
                s = row.s if hasattr(row, "s") and row.s else ""
                p = row.p if hasattr(row, "p") and row.p else ""
                o = row.o if hasattr(row, "o") and row.o else ""

                s_label = utils.get_node_label(s)
                p_label = utils.get_node_label(p)
                o_label = utils.get_node_label(o)

                df_data.append({"Subject": utils.format_iri_to_prefix_label(s),
                    "Predicate": utils.format_iri_to_prefix_label(p),
                    "Object": utils.format_iri_to_prefix_label(o)})

            df = pd.DataFrame(df_data)
            df = df.loc[:, df.apply(lambda col: col.replace('', pd.NA).notna().any())]

            with col1:
                if not df.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>RESULTS ({len(df)} triples):</b>
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ No results.
                    </div>""", unsafe_allow_html=True)



#________________________________________________
# SPARQL
with tab3:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
    with col2b:
        utils.get_corner_status_message_mapping()

    #PURPLE HEADING - ADD NEW TRIPLESMAP
    with col1:
        st.markdown("""<div class="purple-heading">
                ❔ SPARQL
            </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([2,1])


    with col1a:
        query = st.text_area("⌨️ Enter SPARQL query:*")

    if query:
        try:
            results = st.session_state["g_mapping"].query(query)
            # Create and display the DataFrame (build rows dynamically)
            rows = []
            columns = set()

            for row in results:
                row_dict = {}
                for var in row.labels:
                    value = row[var]
                    row_dict[str(var)] = str(value) if value else ""
                    columns.add(str(var))
                rows.append(row_dict)



            df = pd.DataFrame(rows, columns=sorted(columns))
            if not df.empty:
                with col1:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>RESULTS ({len(df)}):</b>
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
            else:
                with col1a:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ <b>No results.</b>
                    </div>""", unsafe_allow_html=True)

        except Exception as e:
            with col1a:
                st.markdown(f"""<div class="error-message">
                    ❌ <b> Failed to parse query. </b>
                    <small><b>Complete error:</b> {e}Y</small>
                </div>""", unsafe_allow_html=True)


#________________________________________________
# PREVIEW
with tab4:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
    with col2b:
        utils.get_corner_status_message_mapping()

    #PURPLE HEADING - PREVIEW
    with col1:
        st.markdown("""<div class="purple-heading">
                🔍 Preview
            </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([2,1])

        if st.session_state["mapping_downloaded_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The mapping <b style="color:#F63366;">{st.session_state["g_label"]}</b> has been downloaded!
                </div>""", unsafe_allow_html=True)
            st.session_state["mapping_downloaded_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()


    list_to_choose = list(utils.get_g_mapping_file_formats_dict())
    list_to_choose.remove("jsonld")

    with col1a:
        if not "key_export_format_selectbox" in st.session_state:
            st.session_state["key_export_format_selectbox"] = "🐢 turtle"  # this ensures the ntriples wont keep selected after download
        format_options_dict = {"🐢 turtle": "turtle", "3️⃣ ntriples": "ntriples"}
        preview_format_display = st.radio("🖱️ Select format:*", format_options_dict,
            horizontal=True, label_visibility="collapsed", key="key_export_format_selectbox")
        preview_format = format_options_dict[preview_format_display]

    if preview_format != "Select format":
        serialised_data = st.session_state["g_mapping"].serialize(format=preview_format)
        max_length = utils.get_max_length_for_display()[9]
        if len(serialised_data) > max_length:
            with col1:
                st.markdown(f"""<div class="info-message-blue">
                    🐘 <b>Your mapping is quite large</b> ({utils.format_number_for_display(len(st.session_state["g_mapping"]))} triples).
                    <small>Showing only the first {utils.format_number_for_display(max_length)} characters
                    (out of {utils.format_number_for_display(len(serialised_data))}) to avoid performance issues.</small>
                </div>""", unsafe_allow_html=True)
        st.code(serialised_data[:max_length])

        with col1b:
            allowed_format_dict = utils.get_g_mapping_file_formats_dict()
            extension = allowed_format_dict[preview_format]
            download_filename = st.session_state["g_label"] + extension
            st.session_state["mapping_downloaded_ok_flag"] = st.download_button(label="Download", data=serialised_data,
                file_name=download_filename, mime="text/plain")

        if st.session_state["mapping_downloaded_ok_flag"]:
            st.rerun()

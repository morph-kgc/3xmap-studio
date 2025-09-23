import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle
from rdflib.namespace import split_uri
from rdflib.namespace import RDF, RDFS, DC, DCTERMS, OWL, XSD

st.set_page_config(layout="wide")

# Header
if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
    st.markdown("""
    <div style="display:flex; align-items:center; background-color:#f0f0f0; padding:12px 18px;
                border-radius:8px; margin-bottom:16px;">
        <span style="font-size:1.7rem; margin-right:18px;">🔎</span>
        <div>
            <h3 style="margin:0; font-size:1.75rem;">
                <span style="color:#511D66; font-weight:bold; margin-right:12px;">◽◽◽◽◽</span>
                Display Mapping
                <span style="color:#511D66; font-weight:bold; margin-left:12px;">◽◽◽◽◽</span>
            </h3>
            <p style="margin:0; font-size:0.95rem; color:#555;">
                <b>Explore</b> your mapping and <b>query</b> it using <b>SPARQL</b>.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="display:flex; align-items:center; background-color:#1e1e1e; padding:12px 18px;
                border-radius:8px; margin-bottom:16px; border-left:4px solid #999999;">
        <span style="font-size:1.7rem; margin-right:18px; color:#dddddd;">🔎</span>
        <div>
            <h3 style="margin:0; font-size:1.75rem; color:#dddddd;">
                <span style="color:#bbbbbb; font-weight:bold; margin-right:12px;">◽◽◽◽◽</span>
                Display Mapping
                <span style="color:#bbbbbb; font-weight:bold; margin-left:12px;">◽◽◽◽◽</span>
            </h3>
            <p style="margin:0; font-size:0.95rem; color:#cccccc;">
                <b>Explore</b> your mapping and <b>query</b> it using <b>SPARQL</b>.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


#____________________________________________
#PRELIMINARY

# Import style
if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
    utils.import_st_aesthetics()
else:
    utils.import_st_aesthetics_dark_mode()
st.write("")


# Namespaces
RML, RR, QL = utils.get_required_ns().values()

# START PAGE_____________________________________________________________________


col1, col2 = st.columns([2,1.5])
if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
    with col1:
        st.markdown(f"""<div class="error-message">
            ❗ You need to create or load a mapping. Please go to the
            <b style="color:#a94442;">Global Configuration page</b>.
        </div>
        """, unsafe_allow_html=True)
        st.stop()


#____________________________________________________________
# PANELS OF THE PAGE (tabs)

tab1, tab2 = st.tabs(["Predefined Searches", "SPARQL"])

#________________________________________________
# PREDEFINED SEARCHES
with tab1:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
    with col2b:
        utils.get_corner_status_message()

    #PURPLE HEADING - ADD NEW TRIPLESMAP
    with col1:
        st.markdown("""<div class="purple-heading">
                📌 Predefined Searches
            </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([2,1])

    predefined_searches_list = ["Select search", "TriplesMaps", "Subject Maps", "Predicate-Object Maps",
        "Used Classes", "Incomplete Nodes", "Orphaned Nodes", "All Triples"]

    with col1a:
        selected_predefined_search = st.selectbox("🖱️ Select search:*", predefined_searches_list,
            key="key_selected_predefined_search")

    if selected_predefined_search == "TriplesMaps":

        with col1b:
            tm_dict = utils.get_tm_dict()
            list_to_choose = list(reversed(list(tm_dict)))
            if len(list_to_choose) > 1:
                selected_tm_for_display_list = st.multiselect("🖱️ Filter TriplesMaps (optional):", list_to_choose,
                    key="key_selected_tm_for_display_list_1")
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
            order_clause = st.selectbox("⌨️ Enter order (optional):", list_to_choose,
                key="key_order_clause")

            query = """
            SELECT ?tm ?logicalTable ?tableName ?sqlQuery ?logicalSource ?source ?referenceFormulation ?iterator WHERE {
              {
                ?tm a <http://www.w3.org/ns/r2rml#TriplesMap> ;
                    <http://www.w3.org/ns/r2rml#logicalTable> ?logicalTable .
                OPTIONAL { ?logicalTable <http://www.w3.org/ns/r2rml#tableName> ?tableName }
                OPTIONAL { ?logicalTable <http://www.w3.org/ns/r2rml#sqlQuery> ?sqlQuery }
              }
              UNION
              {
                ?tm a <http://www.w3.org/ns/r2rml#TriplesMap> ;
                    <http://semweb.mmlab.be/ns/rml#logicalSource> ?logicalSource .
                OPTIONAL { ?logicalSource <http://semweb.mmlab.be/ns/rml#source> ?source }
                OPTIONAL { ?logicalSource <http://semweb.mmlab.be/ns/rml#referenceFormulation> ?referenceFormulation }
              }
            }
            """

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
                tm = row.tm if row.tm else ""
                logical_table = row.logicalTable if hasattr(row, "logicalTable") and row.logicalTable else ""
                logical_source = row.logicalSource if hasattr(row, "logicalSource") and row.logicalSource else ""
                table_name = str(row.tableName) if hasattr(row, "tableName") and row.tableName else ""
                sql_query = str(row.sqlQuery) if hasattr(row, "sqlQuery") and row.sqlQuery else ""
                source = str(row.source) if hasattr(row, "source") and row.source else ""
                reference_formulation = str(row.referenceFormulation) if hasattr(row, "referenceFormulation") and row.referenceFormulation else ""

                tm_label = utils.get_node_label(tm)
                ls_label = utils.get_node_label(logical_source)
                lt_label = utils.get_node_label(logical_table)

                selected_tm_for_display_list = list(tm_dict) if not selected_tm_for_display_list else selected_tm_for_display_list
                if tm_label in selected_tm_for_display_list:
                    df_data.append({"TriplesMap": tm_label, "Logical Source": ls_label,
                        "Logical Table": lt_label, "Source": source,
                        "Table Name": table_name, "SQL Query": sql_query,
                         "Reference Formulation": reference_formulation,
                        "TriplesMap (complete)": tm, "Logical Source (complete)": logical_source,
                        "Logical Table (complete)": logical_table})

            df = pd.DataFrame(df_data)

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
                selected_tm_for_display_list = st.multiselect("🖱️ Filter TriplesMaps (optional):", list_to_choose,
                    key="key_selected_tm_for_display_list_2")
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
            order_clause = st.selectbox("⌨️ Enter order (optional):", list_to_choose,
                key="key_order_clause")

        query = f"""SELECT ?tm ?subjectMap ?template ?class ?termType ?graph WHERE {{
              ?tm a <http://www.w3.org/ns/r2rml#TriplesMap> ;
                  <http://www.w3.org/ns/r2rml#subjectMap> ?subjectMap .
              OPTIONAL {{ ?subjectMap <http://www.w3.org/ns/r2rml#template> ?template }}
              OPTIONAL {{ ?subjectMap <http://www.w3.org/ns/r2rml#class> ?class }}
              OPTIONAL {{ ?subjectMap <http://www.w3.org/ns/r2rml#termType> ?termType }}
              OPTIONAL {{ ?subjectMap <http://www.w3.org/ns/r2rml#graph> ?graph }}
            }}
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
            class_ = str(row["class"]) if row["class"] else ""
            term_type = str(row.termType) if row.termType else ""
            term_type = split_uri(term_type)[1] if term_type else ""
            graph = str(row.graph) if row.graph else ""

            tm_label = utils.get_node_label(tm)
            sm_label = utils.get_node_label(subject_map)

            selected_tm_for_display_list = list(tm_dict) if not selected_tm_for_display_list else selected_tm_for_display_list
            if tm_label in selected_tm_for_display_list:
                df_data.append({"SubjectMap": sm_label, "TriplesMap": tm_label,
                    "Template": template, "Class": class_, "TermType": term_type,
                    "Graph": graph, "SubjectMap (complete)": subject_map})

        with col1:
            st.write("")
            df = pd.DataFrame(df_data)

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

            with col1a:
                list_to_choose = []
                for pom in st.session_state["g_mapping"].objects(tm_iri_for_search, RR.predicateObjectMap):
                    list_to_choose.append(pom)
                if len(list_to_choose) > 1:
                    selected_pom_for_display_list = st.multiselect("🖱️ Filter Predicate-Object Maps (optional):", list_to_choose,
                        key="key_selected_pom_for_display_list")
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
                order_clause = st.selectbox("⌨️ Enter order (optional):", list_to_choose,
                    key="key_order_clause")

            query = f"""
            SELECT ?pom ?predicate ?objectMap ?template ?constant ?column ?termType ?datatype ?language WHERE {{
              <{tm_iri_for_search}> a <http://www.w3.org/ns/r2rml#TriplesMap> ;
                                     <http://www.w3.org/ns/r2rml#predicateObjectMap> ?pom .
              OPTIONAL {{ ?pom <http://www.w3.org/ns/r2rml#predicate> ?predicate }}
              OPTIONAL {{ ?pom <http://www.w3.org/ns/r2rml#objectMap> ?objectMap }}
              OPTIONAL {{ ?objectMap <http://www.w3.org/ns/r2rml#template> ?template }}
              OPTIONAL {{ ?objectMap <http://www.w3.org/ns/r2rml#constant> ?constant }}
              OPTIONAL {{ ?objectMap <http://www.w3.org/ns/r2rml#reference> ?column }}
              OPTIONAL {{ ?objectMap <http://www.w3.org/ns/r2rml#termType> ?termType }}
              OPTIONAL {{ ?objectMap <http://www.w3.org/ns/r2rml#datatype> ?datatype }}
              OPTIONAL {{ ?objectMap <http://www.w3.org/ns/r2rml#language> ?language }}
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
                column = str(row.column) if row.column else ""
                term_type = str(row.termType) if row.termType else ""
                term_type = split_uri(term_type)[1] if term_type else ""
                datatype = str(row.datatype) if row.datatype else ""
                language = str(row.language) if row.language else ""

                pom_label = utils.get_node_label(pom)
                om_label = utils.get_node_label(object_map)

                all_pom_list = list(utils.get_pom_dict())
                selected_pom_for_display_list = all_pom_list if not selected_pom_for_display_list else selected_pom_for_display_list
                if pom in selected_pom_for_display_list:
                    df_data.append({"Predicate-Object Map": pom_label,
                        "Predicate": predicate, "Object Map": om_label,
                        "Template": template, "Constant": constant, "Reference": column,
                        "TermType": term_type, "Datatype": datatype, "Language": language,
                        "Predicate ObjectMap (complete)": pom, "Object Map (complete)": object_map})

            df = pd.DataFrame(df_data)
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
            for sm, rdf_class in st.session_state["g_mapping"].subject_objects(predicate=RR["class"]):
                rdf_class_label = utils.get_node_label(rdf_class)
                classes_set.add(rdf_class_label)

            list_to_choose_classes = list(classes_set)
            if len(list_to_choose_classes) > 1:
                selected_classes_for_display_list = st.multiselect("🖱️ Filter Classes (optional):", list_to_choose_classes,
                    key="key_selected_classes_for_display_list")
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
            order_clause = st.selectbox("⌨️ Enter order (optional):", list_to_choose,
                key="key_order_clause")

        query = """SELECT DISTINCT ?tm ?sm ?class WHERE {
              ?tm a <http://www.w3.org/ns/r2rml#TriplesMap> ;
                  <http://www.w3.org/ns/r2rml#subjectMap> ?sm .
              ?sm <http://www.w3.org/ns/r2rml#class> ?class .
            }"""

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
            tm = row.tm if hasattr(row, "tm") and row.tm else ""
            sm = row.sm if hasattr(row, "sm") and row.sm else ""
            rdf_class = row.get("class") if row.get("class") else ""
            class_label = utils.get_node_label(rdf_class)

            tm_label = utils.get_node_label(tm)
            sm_label = utils.get_node_label(sm)

            selected_classes_for_display_list = list_to_choose_classes if not selected_classes_for_display_list else selected_classes_for_display_list
            if class_label in selected_classes_for_display_list:
                df_data.append({"Subject Map": sm_label,"TriplesMap": tm_label,
                    "Class": class_label,
                    "Class (complete)": rdf_class
                })

        df = pd.DataFrame(df_data)

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
            order_clause = st.selectbox("⌨️ Enter order (optional):", list_to_choose,
                key="key_order_clause")

        if selected_incomplete_node_type == "TriplesMaps":
            query = """SELECT DISTINCT ?tm WHERE {
              {?tm <http://semweb.mmlab.be/ns/rml#logicalSource> ?ls .
                FILTER NOT EXISTS { ?tm <http://www.w3.org/ns/r2rml#subjectMap> ?sm . }
              }
              UNION
              {?tm <http://semweb.mmlab.be/ns/rml#logicalSource> ?ls .
                FILTER NOT EXISTS { ?tm <http://www.w3.org/ns/r2rml#predicateObjectMap> ?pom . }
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
                tm_label = utils.get_node_label(tm) if tm else "(missing)"

                has_sm = bool(list(st.session_state["g_mapping"].objects(subject=tm, predicate=RR["subjectMap"])))
                has_pom = bool(list(st.session_state["g_mapping"].objects(subject=tm, predicate=RR["predicateObjectMap"])))

                df_data.append({"TriplesMap": tm_label,
                    "Has Subject Map": "❌" if not has_sm else "✔️",
                    "Has Predicate ObjectMap": "❌" if not has_pom else "✔️",
                    "TriplesMap (complete)": str(tm) if tm else ""})

            df = pd.DataFrame(df_data)

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
            query = """SELECT DISTINCT ?pom WHERE {
              ?pom a <http://www.w3.org/ns/r2rml#PredicateObjectMap> .
              FILTER NOT EXISTS {
                ?pom <http://www.w3.org/ns/r2rml#objectMap> ?om .}}"""

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
                has_om = bool(list(st.session_state["g_mapping"].objects(subject=pom, predicate=RR["objectMap"])))

                # Get predicate if defined
                predicate = st.session_state["g_mapping"].value(subject=pom, predicate=RR["predicate"])
                predicate_label = utils.get_node_label(predicate) if predicate else ""

                df_data.append({"Predicate-Object Map": pom_label,
                    "Predicate": predicate_label,
                    "Has Object Map": "❌" if not has_om else "✔️",
                    "Predicate-Object Map (complete)": str(pom) if pom else ""})

            df = pd.DataFrame(df_data)

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
            order_clause = st.selectbox("⌨️ Enter order (optional):", list_to_choose,
                key="key_order_clause")

        if selected_orphaned_node_type == "Subject Maps":
            query = """SELECT DISTINCT ?sm WHERE {
              {
                ?sm <http://www.w3.org/ns/r2rml#template> ?template .
              } UNION {
                ?sm <http://www.w3.org/ns/r2rml#class> ?class .
              } UNION {
                ?sm <http://www.w3.org/ns/r2rml#constant> ?constant .
              } UNION {
                ?sm <http://www.w3.org/ns/r2rml#column> ?column .
              } UNION {
                ?sm <http://www.w3.org/ns/r2rml#termType> ?termType .
              } UNION {
                ?sm <http://www.w3.org/ns/r2rml#graphMap> ?graphMap .
              } UNION {
                ?sm <http://semweb.mmlab.be/ns/rml#reference> ?reference .
              }
              FILTER NOT EXISTS {
                ?tm <http://www.w3.org/ns/r2rml#subjectMap> ?sm .
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
                sm_label = utils.get_node_label(sm)

                # Extract known properties from the graph
                g = st.session_state["g_mapping"]
                RR = Namespace("http://www.w3.org/ns/r2rml#")
                RML = Namespace("http://semweb.mmlab.be/ns/rml#")

                template = g.value(subject=sm, predicate=RR["template"])
                rdf_class = g.value(subject=sm, predicate=RR["class"])
                constant = g.value(subject=sm, predicate=RR["constant"])
                column = g.value(subject=sm, predicate=RR["column"])
                term_type = g.value(subject=sm, predicate=RR["termType"])
                graph_map = g.value(subject=sm, predicate=RR["graphMap"])
                reference = g.value(subject=sm, predicate=RML["reference"])

                df_data.append({
                    "Subject Map": sm_label,
                    "Class": utils.get_node_label(rdf_class) if rdf_class else "",
                    "Template": str(template) if template else "",
                    "Constant": str(constant) if constant else "",
                    "Column": str(column) if column else "",
                    "Term Type": str(term_type) if term_type else "",
                    "Graph Map": str(graph_map) if graph_map else "",
                    "Reference": str(reference) if reference else "",
                    "Subject Map (complete)": sm,})

            df = pd.DataFrame(df_data)

            with col1:
                if not df.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>RESULTS ({len(df)}):</b><br>
                        <small>Possible Subject Maps not used by any TriplesMap.</small>
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ No results.
                    </div>""", unsafe_allow_html=True)

        if selected_orphaned_node_type == "Predicate-Object Maps":
            query = """SELECT DISTINCT ?pom WHERE {
              {
                ?pom <http://www.w3.org/ns/r2rml#predicate> ?p .
              } UNION {
                ?pom <http://www.w3.org/ns/r2rml#objectMap> ?o .
              }
              FILTER NOT EXISTS {
                ?tm <http://www.w3.org/ns/r2rml#predicateObjectMap> ?pom .
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
                pom_label = utils.get_node_label(pom)
                predicate = st.session_state["g_mapping"].value(subject=pom, predicate=RR["predicate"])

                df_data.append({
                    "Predicate-Object Map": pom_label,
                    "Predicate": predicate,
                    "Predicate-Object Map (complete)": pom,})

            df = pd.DataFrame(df_data)

            with col1:
                if not df.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>RESULTS ({len(df)}):</b><br>
                        <small>Possible Predicate-Object Maps not used by any TriplesMap.
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ No results.
                    </div>""", unsafe_allow_html=True)

        if selected_orphaned_node_type == "Object Maps":
            query = """SELECT DISTINCT ?om WHERE {
              {
                ?om <http://www.w3.org/ns/r2rml#constant> ?c .
              } UNION {
                ?om <http://www.w3.org/ns/r2rml#column> ?col .
              } UNION {
                ?om <http://www.w3.org/ns/r2rml#template> ?tpl .
              } UNION {
                ?om <http://www.w3.org/ns/r2rml#termType> ?tt .
              } UNION {
                ?om <http://www.w3.org/ns/r2rml#datatype> ?dt .
              } UNION {
                ?om <http://www.w3.org/ns/r2rml#language> ?lang .
              } UNION {
                ?om <http://www.w3.org/ns/r2rml#parentTriplesMap> ?ptm .
              } UNION {
                ?om <http://www.w3.org/ns/r2rml#joinCondition> ?jc .
              } UNION {
                ?om <http://semweb.mmlab.be/ns/rml#reference> ?ref .
              }
              FILTER NOT EXISTS {
                ?pom <http://www.w3.org/ns/r2rml#objectMap> ?om .
              }
            }"""

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
                om_label = utils.get_node_label(om)

                g = st.session_state["g_mapping"]
                constant = g.value(subject=om, predicate=RR["constant"])
                column = g.value(subject=om, predicate=RR["column"])
                template = g.value(subject=om, predicate=RR["template"])
                term_type = g.value(subject=om, predicate=RR["termType"])
                datatype = g.value(subject=om, predicate=RR["datatype"])
                language = g.value(subject=om, predicate=RR["language"])
                parent_tm = g.value(subject=om, predicate=RR["parentTriplesMap"])
                join_condition = g.value(subject=om, predicate=RR["joinCondition"])
                reference = g.value(subject=om, predicate=RML["reference"])

                df_data.append({"Object Map": om_label,
                        "Constant": str(constant) if constant else "",
                        "Column": str(column) if column else "",
                        "Template": str(template) if template else "",
                        "Term Type": str(term_type) if term_type else "",
                        "Datatype": str(datatype) if datatype else "",
                        "Language": str(language) if language else "",
                        "Parent TriplesMap": str(parent_tm) if parent_tm else "",
                        "Join Condition": str(join_condition) if join_condition else "",
                        "Reference": str(reference) if reference else "",
                        "Object Map (complete)": str(om) if om else ""})

            df = pd.DataFrame(df_data)

            with col1:
                if not df.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>RESULTS ({len(df)}):</b><br>
                        <small>Possible Object Maps not used by any Predicate-Object Map.
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
            order_clause = st.selectbox("⌨️ Enter order (optional):", list_to_choose,
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

                df_data.append({"Subject": s_label, "Predicate": p_label,
                    "Object": o_label, "Subject (complete)": str(s),
                    "Predicate (complete)": str(p), "Object (complete)": str(o)})

            df = pd.DataFrame(df_data)

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
with tab2:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
    with col2b:
        utils.get_corner_status_message()

    #PURPLE HEADING - ADD NEW TRIPLESMAP
    with col1:
        st.markdown("""<div class="purple-heading">
                ❔ SPARQL
            </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([2,1])


    with col1a:
        query = st.text_area("⌨️ Enter query:*")

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

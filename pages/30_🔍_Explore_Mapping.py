import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle
from rdflib.namespace import split_uri
from rdflib.namespace import RDF, RDFS, DC, DCTERMS, OWL, XSD

# Header
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


#____________________________________________
#PRELIMINARY

# Import style
utils.import_st_aesthetics()
st.write("")

# Namespaces
RML, RR, QL = utils.get_required_ns().values()

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

tab1, tab2 = st.tabs(["Predefined Searched", "SPARQL"])

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

    predefined_searches_list = ["Select search", "TriplesMaps and Logical Sources", "Subject Maps", "Predicate-Object Maps",
        "Used Classes", "Incomplete Nodes", "Orphaned Nodes"]

    with col1a:
        selected_predefined_search = st.selectbox("🖱️ Select search:*", predefined_searches_list,
            key="key_selected_predefined_search")

    if selected_predefined_search == "TriplesMaps and Logical Sources":

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
                df_data.append({"TriplesMap": tm_label,
                    "SubjectMap": sm_label,
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
                        key="key_selected_tm_for_display_list_1")
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
                    key="key_selected_tm_for_display_list_1")
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
            rdf_class = row.get("class") if row.get("class") else ""
            class_label = utils.get_node_label(rdf_class)

            tm_label = utils.get_node_label(tm)
            sm_label = utils.get_node_label(sm)

            selected_classes_for_display_list = list_to_choose_classes if not selected_classes_for_display_list else selected_classes_for_display_list
            if class_label in selected_classes_for_display_list:
                df_data.append({"TriplesMap": tm_label, "Subject Map": sm_label,
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






#
# 7. Detect orphaned SubjectMaps or ObjectMaps
# SELECT ?map WHERE {
#   ?map <http://www.w3.org/ns/r2rml#template> ?template .
#   FILTER NOT EXISTS { ?tm <http://www.w3.org/ns/r2rml#subjectMap> ?map }
# }

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

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

    predefined_searches_list = ["Select search", "All TriplesMaps", "Subject Map details", "Predicate-Object Maps",
        "Predicate-Object Map details", "All Logical Tables", "Used Classes", "Incomplete Nodes", "Orphaned Nodes"]

    with col1a:
        selected_predefined_search = st.selectbox("🖱️ Select search:*", predefined_searches_list,
            key="key_selected_predefined_search")

    if selected_predefined_search == "All TriplesMaps":

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

        query = f"""SELECT ?tm WHERE {{
            ?tm a <http://www.w3.org/ns/r2rml#TriplesMap>}}"""

        if order_clause == "Ascending":
            query += f"ORDER BY ASC(?tm) "
        elif order_clause == "Descending":
            query += f"ORDER BY DESC(?tm) "

        if limit:
            query += f"LIMIT {limit} "

        if offset:
            query += f"OFFSET {offset}"

        results = st.session_state["g_mapping"].query(query)


        # Create and display the DataFrame
        df_data = []
        for row in results:
            uri = row.tm
            label = split_uri(uri)[1] if isinstance(uri, URIRef) else str(uri)  # or use uri.split("#")[-1] if URIs use hash
            df_data.append({"TriplesMap Label": label, "TriplesMap IRI": uri})

        with col1:
            df = pd.DataFrame(df_data)
            if not df.empty:
                st.markdown(f"""<div class="info-message-blue">
                    <b>RESULTS ({len(df)}):</b>
                </div>""", unsafe_allow_html=True)
                st.dataframe(df, hide_index=True)
            else:
                st.markdown(f"""<div class="warning-message">
                    ⚠️ No results.
                </div>""", unsafe_allow_html=True)

    if selected_predefined_search == "Subject Map details":

        with col1b:
            tm_dict = utils.get_tm_dict()
            list_to_choose = list(tm_dict)
            list_to_choose.insert(0, "Select TriplesMap")
            tm_label_for_search = st.selectbox("🖱️ Select TriplesMap:*", list_to_choose,
                key="key_tm_label_for_search")

        if tm_label_for_search != "Select TriplesMap":
            tm_iri_for_search = tm_dict[tm_label_for_search]

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

            query = f"""SELECT ?subjectMap ?template ?class ?termType ?graph WHERE {{
              <{tm_iri_for_search}> <http://www.w3.org/ns/r2rml#subjectMap> ?subjectMap .
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

            # Create and display the DataFrames
            df_data_1 = []
            df_data_2 = []

            for row in results:
                subject_map = row.subjectMap if row.subjectMap else ""
                template = str(row.template) if row.template else ""
                class_ = str(row["class"]) if row["class"] else ""
                term_type = str(row.termType) if row.termType else ""
                term_type = split_uri(term_type)[1] if term_type else ""
                graph = str(row.graph) if row.graph else ""

                label = split_uri(subject_map)[1] if isinstance(subject_map, URIRef) else str(subject_map)

                df_data_1.append({"SubjectMap Label": label, "SubjectMap IRI": subject_map,
                    "Template": template})

                df_data_2.append({"SubjectMap Label": label,
                    "Class": class_, "TermType": term_type, "Graph": graph})

            with col1:
                st.write("")

                df1 = pd.DataFrame(df_data_1)
                df2 = pd.DataFrame(df_data_2)

                if not df1.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>RESULTS:</b>
                    </div>""", unsafe_allow_html=True)
                    st.markdown("""<div style="background-color:#f0f0f0; padding:4px; border-radius:5px; font-size:14px;">
                            ℹ️ <b>SubjectMap Info</b>
                            </div>""", unsafe_allow_html=True)
                    st.dataframe(df1, hide_index=True)

                if not df2.empty:
                    st.markdown("""<div style="background-color:#f0f0f0; padding:4px; border-radius:5px; font-size:14px;">
                            ℹ️ <b>Additional Properties</b>
                        </div>""", unsafe_allow_html=True)
                    st.dataframe(df2, hide_index=True)

                if df1.empty and df2.empty:
                    st.markdown("""<div class="warning-message">⚠️ No results.</div>""", unsafe_allow_html=True)

    if selected_predefined_search == "Predicate-Object Maps":

        with col1b:
            tm_dict = utils.get_tm_dict()
            list_to_choose = list(tm_dict)
            list_to_choose.insert(0, "Select TriplesMap")
            tm_label_for_search = st.selectbox("🖱️ Select TriplesMap:*", list_to_choose,
                key="key_tm_label_for_search")


        if tm_label_for_search != "Select TriplesMap":
            tm_iri_for_search = tm_dict[tm_label_for_search]

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

            query = f"""SELECT ?pom ?predicate ?objectMap WHERE {{
              <{tm_iri_for_search}> <http://www.w3.org/ns/r2rml#predicateObjectMap> ?pom .
              OPTIONAL {{ ?pom <http://www.w3.org/ns/r2rml#predicate> ?predicate }}
              OPTIONAL {{ ?pom <http://www.w3.org/ns/r2rml#objectMap> ?objectMap }}
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
                pom = row.pom if row.pom else ""
                predicate = str(row.predicate) if row.predicate else ""
                object_map = str(row.objectMap) if row.objectMap else ""

                if isinstance(pom, URIRef):
                    label = split_uri(pom)[1]
                elif isinstance(pom, BNode):
                    label = "_:" + str(pom)[:7] + "..."
                else:
                    label = str(pom)

                df_data.append({"PredicateObjectMap Label": label,
                    "PredicateObjectMap IRI": pom, "Predicate": predicate,
                    "ObjectMap": object_map})

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

    if selected_predefined_search == "Predicate-Object Map details":

        with col1b:
            tm_dict = utils.get_tm_dict()
            list_to_choose = list(tm_dict)
            list_to_choose.insert(0, "Select TriplesMap")
            tm_label_for_search = st.selectbox("🖱️ Select TriplesMap:*", list_to_choose,
                key="key_tm_label_for_search")

        if tm_label_for_search != "Select TriplesMap":
            with col1a:
                tm_iri_for_search = tm_dict[tm_label_for_search]

                pom_list = list(st.session_state["g_mapping"].objects(subject=tm_iri_for_search, predicate=RR.predicateObjectMap))

                if pom_list:
                    list_to_choose = pom_list
                    list_to_choose.insert(0, "Select Predicate-Object Map")
                    pom_iri_for_search = st.selectbox("🖱️ Select Predicate-Object Map:*", list_to_choose,
                        key="key_pom_label_for_search")
                else:
                    st.markdown(f"""<div class="warning-message">
                            ⚠️ No Predicate-Object Maps for TriplesMap <b>{tm_label_for_search}</b>.
                        </div>""", unsafe_allow_html=True)
                    pom_iri_for_search = "Select Predicate-Object Map"

            if pom_iri_for_search != "Select Predicate-Object Map":
                tm_iri_for_search = tm_dict[tm_label_for_search]

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


                if isinstance(pom_iri_for_search, URIRef):

                    query = f"""
                    SELECT ?predicate ?predicateTemplate ?predicateConstant ?objectMap ?column ?template ?constant ?termType ?datatype ?language WHERE {{
                      <{pom_iri_for_search}> <http://www.w3.org/ns/r2rml#predicate> ?predicate .
                      OPTIONAL {{ <{pom_iri_for_search}> <http://www.w3.org/ns/r2rml#objectMap> ?objectMap }}
                      OPTIONAL {{ ?objectMap <http://www.w3.org/ns/r2rml#template> ?template }}
                      OPTIONAL {{ ?objectMap <http://www.w3.org/ns/r2rml#constant> ?constant }}
                      OPTIONAL {{ ?objectMap <http://www.w3.org/ns/r2rml#reference> ?column }}
                      OPTIONAL {{ ?objectMap <http://www.w3.org/ns/r2rml#termType> ?termType }}
                      OPTIONAL {{ ?objectMap <http://www.w3.org/ns/r2rml#datatype> ?datatype }}
                      OPTIONAL {{ ?objectMap <http://www.w3.org/ns/r2rml#language> ?language }}
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

                else:
                    query = """
                    SELECT ?predicate ?predicateTemplate ?predicateConstant ?objectMap ?column ?template ?constant ?termType ?datatype ?language WHERE {
                      ?pom <http://www.w3.org/ns/r2rml#predicate> ?predicate .
                      OPTIONAL { ?pom <http://www.w3.org/ns/r2rml#predicateTemplate> ?predicateTemplate }
                      OPTIONAL { ?pom <http://www.w3.org/ns/r2rml#predicateConstant> ?predicateConstant }
                      OPTIONAL { ?pom <http://www.w3.org/ns/r2rml#objectMap> ?objectMap }
                      OPTIONAL { ?objectMap <http://www.w3.org/ns/r2rml#template> ?template }
                      OPTIONAL { ?objectMap <http://www.w3.org/ns/r2rml#constant> ?constant }
                      OPTIONAL { ?objectMap <http://www.w3.org/ns/r2rml#reference> ?column }
                      OPTIONAL { ?objectMap <http://www.w3.org/ns/r2rml#termType> ?termType }
                      OPTIONAL { ?objectMap <http://www.w3.org/ns/r2rml#datatype> ?datatype }
                      OPTIONAL { ?objectMap <http://www.w3.org/ns/r2rml#language> ?language }
                    }
                    """

                    if order_clause == "Ascending":
                        query += f"ORDER BY ASC(?subjectMap) "
                    elif order_clause == "Descending":
                        query += f"ORDER BY DESC(?subjectMap) "

                    if limit:
                        query += f"LIMIT {limit} "

                    if offset:
                        query += f"OFFSET {offset}"

                    results = st.session_state["g_mapping"].query(query, initBindings={"pom": pom_iri_for_search})

                # Create and display the DataFrame
                df_data_1 = []
                df_data_2 = []

                for row in results:
                    predicate = str(row.predicate) if row.predicate else ""
                    object_map = str(row.objectMap) if row.objectMap else ""
                    template = str(row.template) if row.template else ""
                    constant = str(row.constant) if row.constant else ""
                    column = str(row.column) if row.column else ""
                    term_type = str(row.termType) if row.termType else ""
                    term_type = split_uri(term_type)[1] if term_type else ""
                    datatype = str(row.datatype) if row.datatype else ""
                    language = str(row.language) if row.language else ""


                    if isinstance(pom_iri_for_search, URIRef):
                        pom_label = split_uri(pom_iri_for_search)[1]
                    elif isinstance(pom_iri_for_search, BNode):
                        pom_label = "_:" + str(pom_iri_for_search)[:7] + "..."
                    else:
                        pom_label = str(pom_iri_for_search)

                    if isinstance(object_map, URIRef):
                        om_label = split_uri(object_map)[1]
                    elif isinstance(object_map, BNode):
                        om_label = "_:" + str(object_map)[:7] + "..."
                    else:
                        om_label = str(object_map)


                    df_data_1.append({"Predicate-Object Map label": pom_label,
                        "Predicate-Object Map": pom_iri_for_search, "Predicate": predicate})

                    df_data_2.append({"ObjectMap Label": om_label,
                        "ObjectMap IRI": object_map, "Template": template,
                        "Constant": constant, "Reference": column,
                        "TermType": term_type, "Datatype": datatype,
                        "Language": language})

                    with col1:
                        st.write("")
                        df1 = pd.DataFrame(df_data_1)
                        df2 = pd.DataFrame(df_data_2)

                        if not df1.empty:
                            st.markdown(f"""<div class="info-message-blue">
                                <b>RESULTS:</b>
                            </div>""", unsafe_allow_html=True)
                            st.markdown("""<div style="background-color:#f0f0f0; padding:4px; border-radius:5px; font-size:14px;">
                                    ℹ️ <b>Predicate-Object Map</b>
                                    </div>""", unsafe_allow_html=True)
                            st.dataframe(df1, hide_index=True)

                        if not df1.empty:
                            st.markdown("""<div style="background-color:#f0f0f0; padding:4px; border-radius:5px; font-size:14px;">
                                    ℹ️ <b>Object Map</b>
                                    </div>""", unsafe_allow_html=True)
                            st.dataframe(df1, hide_index=True)

                        if df1.empty and df2.empty:
                            st.markdown("""<div class="warning-message">⚠️ No results.</div>""", unsafe_allow_html=True)



# 5. List all logical tables and their sources
# SELECT ?tm ?logicalTable ?tableName ?sqlQuery WHERE {
#   ?tm a <http://www.w3.org/ns/r2rml#TriplesMap> ;
#       <http://www.w3.org/ns/r2rml#logicalTable> ?logicalTable .
#   OPTIONAL { ?logicalTable <http://www.w3.org/ns/r2rml#tableName> ?tableName }
#   OPTIONAL { ?logicalTable <http://www.w3.org/ns/r2rml#sqlQuery> ?sqlQuery }
# }
#
# 6. Find all classes used in SubjectMaps
# SELECT DISTINCT ?class WHERE {
#   ?tm a <http://www.w3.org/ns/r2rml#TriplesMap> ;
#       <http://www.w3.org/ns/r2rml#subjectMap> ?sm .
#   ?sm <http://www.w3.org/ns/r2rml#class> ?class .
# }
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

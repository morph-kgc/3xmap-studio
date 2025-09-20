import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle
from rdflib.namespace import split_uri


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
        "Object Map details", "All Logical Tables", "Used Classes", "Incomplete Nodes", "Orphaned Nodes"]

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

            query = f"""
            SELECT ?tm WHERE {{
                ?tm a <http://www.w3.org/ns/r2rml#TriplesMap>
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

        results = st.session_state["g_mapping"].query(query)

        # Build a list of rows for the DataFrame
        tm_data = []
        for row in results:
            uri = str(row.tm)
            label = uri.split("/")[-1] if "/" in uri else uri  # or use uri.split("#")[-1] if URIs use hash
            tm_data.append({"TriplesMap Label": label, "TriplesMap URI": uri})

        # Create and display the DataFrame
        with col1:
            df = pd.DataFrame(tm_data)
            if not df.empty:
                st.dataframe(df, hide_index=True)
            else:
                st.markdown(f"""<div class="warning-message">
                    ⚠️ No results.
                </div>""", unsafe_allow_html=True)











# 2. Show SubjectMap details for a TriplesMap
# SELECT ?subjectMap ?template ?class ?termType ?graph WHERE {
#   <TM_URI> <http://www.w3.org/ns/r2rml#subjectMap> ?subjectMap .
#   OPTIONAL { ?subjectMap <http://www.w3.org/ns/r2rml#template> ?template }
#   OPTIONAL { ?subjectMap <http://www.w3.org/ns/r2rml#class> ?class }
#   OPTIONAL { ?subjectMap <http://www.w3.org/ns/r2rml#termType> ?termType }
#   OPTIONAL { ?subjectMap <http://www.w3.org/ns/r2rml#graph> ?graph }
# }

# 3. Show Predicate-ObjectMaps for a TriplesMap
# SELECT ?pom ?predicate ?objectMap WHERE {
#   <TM_URI> <http://www.w3.org/ns/r2rml#predicateObjectMap> ?pom .
#   OPTIONAL { ?pom <http://www.w3.org/ns/r2rml#predicate> ?predicate }
#   OPTIONAL { ?pom <http://www.w3.org/ns/r2rml#objectMap> ?objectMap }
# }
#
# 4. Show ObjectMap details for a PredicateObjectMap
# SELECT ?objectMap ?column ?template ?constant ?termType ?datatype WHERE {
#   <POM_URI> <http://www.w3.org/ns/r2rml#objectMap> ?objectMap .
#   OPTIONAL { ?objectMap <http://www.w3.org/ns/r2rml#column> ?column }
#   OPTIONAL { ?objectMap <http://www.w3.org/ns/r2rml#template> ?template }
#   OPTIONAL { ?objectMap <http://www.w3.org/ns/r2rml#constant> ?constant }
#   OPTIONAL { ?objectMap <http://www.w3.org/ns/r2rml#termType> ?termType }
#   OPTIONAL { ?objectMap <http://www.w3.org/ns/r2rml#datatype> ?datatype }
# }
#
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

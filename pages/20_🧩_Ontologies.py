import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace, BNode
from rdflib.namespace import RDF, RDFS, DC, DCTERMS, OWL, XSD
from rdflib.namespace import split_uri
import streamlit as st
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
def load_ontology_from_link():
    # load ontology
    st.session_state["g_ontology"] = st.session_state["g_ontology_from_link_candidate"]  # consolidate ontology graph
    st.session_state["g_ontology_label"] = utils.get_ontology_human_readable_name(st.session_state["g_ontology"], source_link=st.session_state["key_ontology_link"])
    # bind ontology namespaces
    ontology_ns_dict = utils.get_g_ns_dict(st.session_state["g_ontology"])
    for prefix, namespace in ontology_ns_dict.items():
        utils.bind_namespace(prefix, namespace, overwrite=False)
    # store information___________________________
    st.session_state["g_ontology_loaded_ok_flag"] = True
    st.session_state["g_ontology_components_dict"][st.session_state["g_ontology_label"]] = st.session_state["g_ontology"]
    st.session_state["g_ontology_components_tag_dict"][st.session_state["g_ontology_label"]] = utils.get_unique_ontology_tag(st.session_state["g_ontology_label"])
    # reset fields___________________________
    st.session_state["key_ontology_link"] = ""
    st.session_state["ontology_link"] = ""

def load_ontology_from_file():
    # load ontology
    st.session_state["g_ontology"] = st.session_state["g_ontology_from_file_candidate"]  # consolidate ontology graph
    st.session_state["g_ontology_label"] = utils.get_ontology_human_readable_name(st.session_state["g_ontology"], source_file=st.session_state["ontology_file"])
    # bind ontology namespaces
    ontology_ns_dict = utils.get_g_ns_dict(st.session_state["g_ontology"])
    for prefix, namespace in ontology_ns_dict.items():
        utils.bind_namespace(prefix, namespace, overwrite=False)
    # store information___________________________
    st.session_state["g_ontology_loaded_ok_flag"] = True
    st.session_state["g_ontology_components_dict"][st.session_state["g_ontology_label"]]=st.session_state["g_ontology"]
    st.session_state["g_ontology_components_tag_dict"][st.session_state["g_ontology_label"]] = utils.get_unique_ontology_tag(st.session_state["g_ontology_label"])
    # reset fields___________________________
    st.session_state["key_ontology_uploader"] = str(uuid.uuid4())
    st.session_state["ontology_file"] = None
    st.session_state["key_import_ontology_selected_option"] = "🌐 URL"

def extend_ontology_from_link():
    # load ontology
    g_ontology_new_part = st.session_state["g_ontology_from_link_candidate"]
    g_ontology_new_part_label = utils.get_ontology_human_readable_name(g_ontology_new_part, source_link=st.session_state["key_ontology_link"])
    #store information___________________________
    st.session_state["g_ontology_loaded_ok_flag"] = True
    st.session_state["g_ontology_components_dict"][g_ontology_new_part_label] = g_ontology_new_part
    st.session_state["g_ontology_components_tag_dict"][g_ontology_new_part_label] = utils.get_unique_ontology_tag(g_ontology_new_part_label)
    # bind ontology namespaces
    ontology_ns_dict = utils.get_g_ns_dict(g_ontology_new_part)
    for prefix, namespace in ontology_ns_dict.items():
        utils.bind_namespace(prefix, namespace, overwrite=False)
    # merge ontologies components___________________
    st.session_state["g_ontology"] = Graph()
    for ont_label, ont in st.session_state["g_ontology_components_dict"].items():
        st.session_state["g_ontology"] += ont  # merge the graphs using RDFLib's += operator
        for prefix, namespace in utils.get_g_ns_dict(ont).items():
            st.session_state["g_ontology"].bind(prefix, namespace)
    # reset fields___________________________
    st.session_state["key_ontology_link"] = ""
    st.session_state["ontology_link"] = ""
    st.session_state["key_extend_ontology_selected_option"] = "🌐 URL"

def extend_ontology_from_file():
    # load ontology
    g_ontology_new_part = st.session_state["g_ontology_from_file_candidate"]
    g_ontology_new_part_label = utils.get_ontology_human_readable_name(g_ontology_new_part, source_file=st.session_state["ontology_file"])
    #store information___________________________
    st.session_state["g_ontology_loaded_ok_flag"] = True
    st.session_state["g_ontology_components_dict"][g_ontology_new_part_label] = g_ontology_new_part
    st.session_state["g_ontology_components_tag_dict"][g_ontology_new_part_label] = utils.get_unique_ontology_tag(g_ontology_new_part_label)
    # bind ontology namespaces
    ontology_ns_dict = utils.get_g_ns_dict(g_ontology_new_part)
    for prefix, namespace in ontology_ns_dict.items():
        utils.bind_namespace(prefix, namespace, overwrite=False)
    # merge ontologies components___________________
    st.session_state["g_ontology"] = Graph()
    for ont_label, ont in st.session_state["g_ontology_components_dict"].items():
        st.session_state["g_ontology"] += ont  # merge the graphs using RDFLib's += operator
        for prefix, namespace in utils.get_g_ns_dict(ont).items():
            st.session_state["g_ontology"].bind(prefix, namespace)
    # reset fields___________________________
    st.session_state["key_ontology_uploader"] = str(uuid.uuid4())
    st.session_state["ontology_file"] = None
    st.session_state["key_import_ontology_selected_option"] = "🌐 URL"

def reduce_ontology():
    #store information___________________________
    st.session_state["g_ontology_reduced_ok_flag"] = True
    # drop the given ontology components from the dictionary_______________________
    st.session_state["g_ontology_components_dict"] = {label: ont for label, ont in st.session_state["g_ontology_components_dict"].items() if label not in ontologies_to_drop_list}
    st.session_state["g_ontology_components_tag_dict"] = {label: ont for label, ont in st.session_state["g_ontology_components_tag_dict"].items() if label not in ontologies_to_drop_list}
    # merge remaining ontology components_______________________________
    st.session_state["g_ontology"] = Graph()
    for label, ont in st.session_state["g_ontology_components_dict"].items():
        st.session_state["g_ontology"] += ont
        for prefix, namespace in ont.namespaces():
            st.session_state["g_ontology"].bind(prefix, namespace)

#_______________________________________________________________________________
# PANELS OF THE PAGE (tabs)
tab1, tab2, tab3 = st.tabs(["Import Ontology", "Explore Ontology", "View Ontology"])

#_______________________________________________________________________________
# PANEL: IMPORT ONTOLOGY
with tab1:
    col1, col2, col2a, col2b = utils.get_panel_layout(narrow=True)

    # RIGHT COLUMN: ONTOLOGY INFO BOX-------------------------------------------
    with col2b:
        utils.get_corner_status_message(ontology_info=True)

    with col2:
        col2a,col2b = st.columns([2,1.5])
    with col2b:
        st.write("")
        st.markdown("""<div class="info-message-blue">
        🐢 Certain options in this panel can work a bit slow.
        <small> Some <b>patience</b> may be required.</small>
            </div>""", unsafe_allow_html=True)

    #PURPLE HEADING: ADD ONTOLOGY-----------------------------------------------
    with col1:
        st.markdown("""<div class="purple-heading">
                ➕ Add Ontology
            </div>""", unsafe_allow_html=True)
        st.write("")

    if st.session_state["g_ontology_loaded_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>ontology</b> has been imported!
            </div>""", unsafe_allow_html=True)
        st.session_state["g_ontology_loaded_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    with col1:
        col1a,col1b = st.columns([2,1])

    with col1b:
        import_ontology_selected_option = st.radio("🖱️ Import ontology from:*", ["🌐 URL", "📁 File"],
            label_visibility="hidden", horizontal=True, key="key_import_ontology_selected_option")

    if import_ontology_selected_option == "🌐 URL":

        with col1a:
            ontology_link = st.text_input("⌨️ Enter link to ontology:*", key="key_ontology_link")
            st.session_state["ontology_link"] = ontology_link if ontology_link else ""

        if ontology_link:

            g_candidate, fmt_candidate = utils.parse_ontology(st.session_state["ontology_link"])
            st.session_state["g_ontology_from_link_candidate"] = g_candidate
            st.session_state["g_ontology_from_link_candidate_fmt"] = fmt_candidate
            st.session_state["g_ontology_from_link_candidate_label"] = utils.get_ontology_human_readable_name(st.session_state["g_ontology_from_link_candidate"], source_link=st.session_state["ontology_link"])

            valid_ontology_flag, success_html, warning_html, error_html = utils.get_candidate_ontology_info_messages(st.session_state["g_ontology_from_link_candidate"], st.session_state["g_ontology_from_link_candidate_label"], st.session_state["g_ontology_from_link_candidate_fmt"])

            if valid_ontology_flag:

                with col1:
                    col1a, col1b, col1c = st.columns([1,3,3])

                if not st.session_state["g_ontology"]:   #no ontology imported yet
                    with col1a:
                        st.button("Add", key="key_load_ontology_from_link_button", on_click=load_ontology_from_link)

                else:  # an ontology is already imported
                    with col1a:
                        st.button("Add", key="key_extend_ontology_from_link_button", on_click=extend_ontology_from_link)

                if warning_html:
                    with col1b:
                        st.markdown(f"""<div class="warning-message">
                                {warning_html}
                            </div>""", unsafe_allow_html=True)

                with col1c:
                    st.markdown(f"""<div class="success-message">
                            {success_html}
                        </div>""", unsafe_allow_html=True)
            else:
                with col1a:
                    st.markdown(f"""<div class="error-message">
                            {error_html}
                        </div>""", unsafe_allow_html=True)


    elif import_ontology_selected_option == "📁 File":

        ontology_format_list = list(utils.get_supported_formats(ontology=True))

        with col1a:
            st.session_state["ontology_file"] = st.file_uploader(f"""🖱️
                Upload ontology file:*""", type=ontology_format_list, key=st.session_state["key_ontology_uploader"])

        if st.session_state["ontology_file"]:

            g_candidate, fmt_candidate = utils.parse_ontology(st.session_state["ontology_file"])
            st.session_state["g_ontology_from_file_candidate"] = g_candidate
            st.session_state["g_ontology_from_file_candidate_fmt"] = fmt_candidate
            st.session_state["g_ontology_from_file_candidate_label"] = utils.get_ontology_human_readable_name(st.session_state["g_ontology_from_file_candidate"], source_file=st.session_state["ontology_file"])
            valid_ontology_flag, success_html, warning_html, error_html = utils.get_candidate_ontology_info_messages(st.session_state["g_ontology_from_file_candidate"], st.session_state["g_ontology_from_file_candidate_label"], st.session_state["g_ontology_from_file_candidate_fmt"])

            if valid_ontology_flag:
                with col1b:
                    if warning_html:
                        st.markdown(f"""<div class="warning-message">
                                {warning_html}
                            </div>""", unsafe_allow_html=True)

                    st.markdown(f"""<div class="success-message">
                            {success_html}
                        </div>""", unsafe_allow_html=True)

                with col1a:
                    if not st.session_state["g_ontology"]:   #no ontology imported yet
                        st.button("Add", key="key_load_ontology_from_file_button", on_click=load_ontology_from_file)
                    else:   # an ontology is already imported
                        st.button("Add", key="key_extend_ontology_from_file_button", on_click=extend_ontology_from_file)

            else:
                with col1b:
                    st.markdown(f"""<div class="error-message">
                            {error_html}
                        </div>""", unsafe_allow_html=True)

    # SUCCESS MESSAGE: ONTOLOGY REMOVED-----------------------------------------
    # Shows here if there is no Remove ontology purple heading
    if not st.session_state["g_ontology"] and st.session_state["g_ontology_reduced_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>ontology/ies</b> have been removed!
            </div>""", unsafe_allow_html=True)
        st.session_state["g_ontology_reduced_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    # PURPLE HEADING: REMOVE ONTOLOGY-------------------------------------------
    # Shows only if there is at least one ontology
    if st.session_state["g_ontology"]:   #ontology loaded and more than 1 component
        with col1:
            st.write("________")
            st.markdown("""<div class="purple-heading">
                    🗑️ Remove Ontology
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["g_ontology_reduced_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>ontology/ies</b> have been removed!
                </div>""", unsafe_allow_html=True)
            st.session_state["g_ontology_reduced_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            list_to_choose = sorted(st.session_state["g_ontology_components_tag_dict"].values())
            if len(list_to_choose) > 1:
                list_to_choose.insert(0, "Select all")
            ontologies_to_drop_list_tags = st.multiselect("🖱️ Select ontologies to be dropped:*", list_to_choose,
                key="key_ontologies_to_drop_list")
            ontologies_to_drop_list = []
            for ont_label, ont_tag in st.session_state["g_ontology_components_tag_dict"].items():
                if ont_tag in ontologies_to_drop_list_tags:
                    ontologies_to_drop_list.append(ont_label)

        if ontologies_to_drop_list_tags:
            if "Select all" in ontologies_to_drop_list_tags:
                with col1b:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ You are deleting <b>all ontologies ({len(st.session_state["g_ontology_components_dict"])})</b>.
                        <small>Make sure you want to go ahead.</small>
                    </div>""", unsafe_allow_html=True)
                with col1a:
                    reduce_ontology_checkbox = st.checkbox(
                    f"""🔒 I am sure I want to drop all the ontologies""",
                    key="key_reduce_ontology_checkbox")
                ontologies_to_drop_list = list(st.session_state["g_ontology_components_dict"].keys())
            else:
                with col1a:
                    reduce_ontology_checkbox = st.checkbox(
                    f"""🔒 I am sure I want to drop the selected ontologies""",
                    key="key_reduce_ontology_checkbox")

            if reduce_ontology_checkbox:
                with col1a:
                    st.button("Drop", key="key_reduce_ontology_button", on_click=reduce_ontology)


#_______________________________________________________________________________
# PANEL: EXPLORE ONTOLOGY
with tab2:
    col1, col2, col2a, col2b = utils.get_panel_layout(narrow=True)

    # RIGHT COLUMN: ONTOLOGY INFO BOX-------------------------------------------
    with col2b:
        utils.get_corner_status_message(ontology_info=True)

    # PURPLE HEADING: EXPLORE ONTOLOGY------------------------------------------
    # Works only if there is at least one ontology
    if not st.session_state["g_ontology_components_dict"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            utils.get_missing_element_error_message(ontology=True)

    else:

        with col1:
            st.markdown("""<div class="purple-heading">
                    🔍 Explore Ontology
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a, col1b = st.columns([2.5, 1])

        ontology_searches_list = ["🏷️ Classes", "🔗 Properties", "✏️ Custom search"]

        with col1a:
            selected_ontology_search = st.radio("🖱️ Select search:*", ontology_searches_list,
                label_visibility="collapsed", horizontal=True, key="key_selected_ontology_search")

        if len(st.session_state["g_ontology_components_dict"]) > 1:
            with col1b:
                list_to_choose = sorted(st.session_state["g_ontology_components_tag_dict"].values())
                list_to_choose.insert(0, "All ontologies")
                ontology_component_for_search_tag = st.selectbox("🧩 Select ontology (opt):", list_to_choose,
                    key="key_ontology_component_for_search_tag")
            if ontology_component_for_search_tag == "All ontologies":
                ontology_for_search = st.session_state["g_ontology"]
            else:
                for ont, ont_tag in st.session_state["g_ontology_components_tag_dict"].items():
                    if ont_tag == ontology_component_for_search_tag:
                        ontology_for_search = st.session_state["g_ontology_components_dict"][ont]

        else:
            ontology_for_search = st.session_state["g_ontology"]

        max_length = utils.get_max_length_for_display()[9]
        if len(ontology_for_search) > max_length:
            with col2:
                col2a, col2b = st.columns([1,3])
            with col2b:
                st.write("")
                st.markdown(f"""<div class="info-message-blue">
                    🐘 <b>Your ontology is quite large</b> ({utils.format_number_for_display(len(ontology_for_search))} triples).
                    <small>Some <b>patience</b> may be required.</small>
                </div>""", unsafe_allow_html=True)

        # CLASSES
        if selected_ontology_search == "🏷️ Classes":

            with col1:
                col1a, col1b, col1c, col1d = st.columns(4)

            with col1a:
                limit = st.text_input("🎚️ Enter limit (opt):", key="key_limit")
                limit = "" if not limit.isdigit() else limit

            with col1b:
                offset = st.text_input("🎚️ Enter offset (opt):", key="key_offset")
                offset = "" if not offset.isdigit() else offset
            with col1c:
                list_to_choose = ["No order", "Ascending", "Descending"]
                order_clause = st.selectbox("🎚️ Select order (opt):", list_to_choose,
                    key="key_order_clause")

            no_filters_query = """PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl:  <http://www.w3.org/2002/07/owl#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                SELECT DISTINCT ?class ?label ?comment ?type WHERE {
                  VALUES ?type { owl:Class rdfs:Class }
                  ?class rdf:type ?type .
                  FILTER (isIRI(?class))
                  OPTIONAL { ?class rdfs:label ?label }
                  OPTIONAL { ?class rdfs:comment ?comment } }"""

            query = no_filters_query

            superclass_dict = {}
            for s, p, o in list(set(ontology_for_search.triples((None, RDFS.subClassOf, None)))):
                if not isinstance(o, BNode) and o not in superclass_dict.values():
                    superclass_dict[utils.format_iri_to_prefix_label(o)] = o

            list_to_choose = ["No filter", "Class type", "Annotation"]
            if superclass_dict:
                list_to_choose.insert(1, "Superclass")

            with col1d:
                class_filter_type = st.selectbox("📡 Add filter (opt):", list_to_choose,
                    key="key_class_filter_type")

            # Superclass filter
            if class_filter_type == "Superclass":

                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    superclass_list = sorted(superclass_dict.keys())
                    superclass_list.insert(0, "No superclass filter")
                    selected_superclass_filter = st.selectbox("📡 Filter by superclass (optional):", superclass_list,
                        key="key_selected_superclass_filter")   #superclass label

                if selected_superclass_filter != "No superclass filter":
                    selected_superclass_iri = superclass_dict[selected_superclass_filter]

                    query = f"""PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX owl:  <http://www.w3.org/2002/07/owl#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                    SELECT DISTINCT ?class ?label ?comment ?type WHERE {{
                      VALUES ?type {{ owl:Class rdfs:Class }}
                      ?class rdf:type ?type .
                      ?class rdfs:subClassOf <{selected_superclass_iri}> .
                      FILTER (isIRI(?class))
                      OPTIONAL {{ ?class rdfs:label ?label }}
                      OPTIONAL {{ ?class rdfs:comment ?comment }} }}"""

            # Class type filter
            if class_filter_type == "Class type":

                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    list_to_choose = ["No class type filter", "owl: Class", "rdfs: Class"]
                    selected_class_type = st.selectbox("📡 Filter by class type (optional):", list_to_choose,
                        key="key_selected_class_type")

                if selected_class_type != "No class type filter":

                    query = f"""PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX owl:  <http://www.w3.org/2002/07/owl#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                    SELECT DISTINCT ?class ?label ?comment ?type WHERE {{
                      ?class rdf:type ?type .
                      FILTER (isIRI(?class))

                      {"FILTER (?type = owl:Class)" if selected_class_type == "owl: Class" else
                        "FILTER (?type = rdfs:Class)" if selected_class_type == "rdfs: Class" else
                        "FILTER (?type = owl:Class || ?type = rdfs:Class)"}

                      OPTIONAL {{ ?class rdfs:label ?label }}
                      OPTIONAL {{ ?class rdfs:comment ?comment }} }}"""

            # Annotation filter
            if class_filter_type == "Annotation":

                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    annotation_options = ["No annotation filter", "Has comment", "Has label", "Has comment or label",
                        "Has comment and label"]
                    selected_annotation_filter = st.selectbox("📡 Filter by annotation presence (optional):", annotation_options,
                        key="key_selected_annotation_filter")

                if selected_annotation_filter != "No annotation filter":

                    base_query = """PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                        PREFIX owl:  <http://www.w3.org/2002/07/owl#>
                        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                        SELECT DISTINCT ?class ?label ?comment ?type WHERE {
                          VALUES ?type { owl:Class rdfs:Class }
                          ?class rdf:type ?type .
                          FILTER (isIRI(?class))
                          OPTIONAL { ?class rdfs:label ?label }
                          OPTIONAL { ?class rdfs:comment ?comment }"""

                    if selected_annotation_filter == "Has comment":
                        query = base_query + "FILTER EXISTS { ?class rdfs:comment ?comment } }"
                    elif selected_annotation_filter == "Has label":
                        query = base_query + "FILTER EXISTS { ?class rdfs:label ?label } }"
                    elif selected_annotation_filter == "Has comment or label":
                        query = base_query + """
                        FILTER (EXISTS { ?class rdfs:label ?label } ||
                          EXISTS { ?class rdfs:comment ?comment } ) }"""
                    elif selected_annotation_filter == "Has comment and label":
                        query = base_query + """
                        FILTER (EXISTS { ?class rdfs:label ?label } &&
                                EXISTS { ?class rdfs:comment ?comment }) }"""

            # Add limit, offset and order
            if order_clause == "Ascending":
                query += f"ORDER BY ASC(?class) "
            elif order_clause == "Descending":
                query += f"ORDER BY DESC(?class) "
            if limit:
                query += f"LIMIT {limit} "
            if offset:
                query += f"OFFSET {offset}"

            # Get the query results
            results = ontology_for_search.query(query)
            df_data = []

            for row in results:
                class_iri = getattr(row, "class", "")
                label = getattr(row, "label", "")
                comment = getattr(row, "comment", "")
                class_type = getattr(row, "type", "")  # Extract the class type

                if isinstance(class_iri, URIRef):  # filter out BNodes
                    df_data.append({
                        "Class": utils.format_iri_to_prefix_label(class_iri),
                        "Label": label, "Comment": comment,
                        "Class Type": ("owl: Class" if str(class_type) == "http://www.w3.org/2002/07/owl#Class" else
                            "rdfs: Class" if str(class_type) == "http://www.w3.org/2000/01/rdf-schema#Class" else
                            str(class_type)),
                         "Class IRI": class_iri })

            # Create dataframe and display
            df = pd.DataFrame(df_data)
            df = df.loc[:, df.apply(lambda col: col.replace('', pd.NA).notna().any())]   # drop empty columns

            with col1:
                if not df.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>Results ({len(df)}):</b>
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ No results.
                    </div>""", unsafe_allow_html=True)

        # PROPERTIES
        if selected_ontology_search == "🔗 Properties":
            with col1:
                col1a, col1b, col1c, col1d = st.columns(4)

            with col1a:
                limit = st.text_input("🎚️ Enter limit (opt):", key="key_limit_prop")
                limit = "" if not limit.isdigit() else limit
            with col1b:
                offset = st.text_input("🎚️ Enter offset (opt):", key="key_offset_prop")
                offset = "" if not offset.isdigit() else offset
            with col1c:
                list_to_choose = ["No order", "Ascending", "Descending"]
                order_clause = st.selectbox("🎚️ Select order (opt):", list_to_choose,
                    key="key_order_clause_prop")

            no_filters_query = """PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl:  <http://www.w3.org/2002/07/owl#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                SELECT DISTINCT ?property ?label ?comment (GROUP_CONCAT(STR(?type); separator=", ") AS ?types) WHERE {
                  ?property rdf:type ?type .
                  FILTER(?type IN (
                    rdf:Property,
                    owl:ObjectProperty,
                    owl:DatatypeProperty,
                    owl:AnnotationProperty
                  ))
                  FILTER (isIRI(?property))
                  OPTIONAL { ?property rdfs:label ?label }
                  OPTIONAL { ?property rdfs:comment ?comment }
                }
                GROUP BY ?property ?label ?comment"""

            query = no_filters_query

            superproperty_dict = {}
            for s, p, o in ontology_for_search.triples((None, RDFS.subPropertyOf, None)):
                if isinstance(o, URIRef) and o not in superproperty_dict.values():
                    superproperty_dict[utils.format_iri_to_prefix_label(o)] = o

            domain_dict = {}
            for s, p, o in ontology_for_search.triples((None, RDFS.domain, None)):
                if isinstance(o, URIRef) and o not in domain_dict.values():
                    domain_dict[utils.format_iri_to_prefix_label(o)] = o

            range_dict = {}
            for s, p, o in ontology_for_search.triples((None, RDFS.range, None)):
                if isinstance(o, URIRef) and o not in range_dict.values():
                    range_dict[utils.format_iri_to_prefix_label(o)] = o

            list_to_choose = ["No filter", "Property type", "Annotation"]
            if range_dict:
                list_to_choose.insert(1,"Range")
            if domain_dict:
                list_to_choose.insert(1,"Domain")
            if superproperty_dict:
                list_to_choose.insert(1,"Superproperty")

            with col1d:
                property_filter_type = st.selectbox("📡 Add filter (opt):", list_to_choose,
                    key="key_property_filter_type")

            # Superproperty filter
            if property_filter_type == "Superproperty":
                with col1:
                    col1a, col1b = st.columns([1.5,1])
                with col1a:
                    list_to_choose = sorted(list(superproperty_dict))
                    list_to_choose.insert(0, "No superproperty filter")
                    selected_superproperty_filter = st.selectbox("📡 Select superproperty filter:*", list_to_choose,
                        key="key_selected_superproperty_filter")


                if selected_superproperty_filter != "No superproperty filter":
                    selected_superproperty_iri = superproperty_dict[selected_superproperty_filter]

                    query = f"""PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                        PREFIX owl:  <http://www.w3.org/2002/07/owl#>
                        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                        SELECT DISTINCT ?property ?label ?comment (GROUP_CONCAT(STR(?type); separator=", ") AS ?types) WHERE {{
                          ?property rdf:type ?type .
                          FILTER(?type IN (
                            rdf:Property,
                            owl:ObjectProperty,
                            owl:DatatypeProperty,
                            owl:AnnotationProperty
                          ))
                          ?property rdfs:subPropertyOf <{selected_superproperty_iri}> .
                          FILTER (isIRI(?property))
                          OPTIONAL {{ ?property rdfs:label ?label }}
                          OPTIONAL {{ ?property rdfs:comment ?comment }}
                        }}
                        GROUP BY ?property ?label ?comment
                        """

            # Domain filter
            if property_filter_type == "Domain":
                with col1:
                    col1a, col1b = st.columns([1.5,1])
                with col1a:
                    list_to_choose = sorted(list(domain_dict))
                    list_to_choose.insert(0, "No domain filter")
                    selected_domain_filter = st.selectbox("📡 Select domain filter:*", list_to_choose,
                        key="key_selected_domain_filter")

                if selected_domain_filter != "No domain filter":
                    selected_domain_iri = domain_dict[selected_domain_filter]

                    query = f"""
                    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX owl:  <http://www.w3.org/2002/07/owl#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                    SELECT DISTINCT ?property ?label ?comment (GROUP_CONCAT(STR(?type); separator=", ") AS ?types) WHERE {{
                      ?property rdf:type ?type .
                      FILTER(?type IN (
                        rdf:Property,
                        owl:ObjectProperty,
                        owl:DatatypeProperty,
                        owl:AnnotationProperty
                      ))
                      ?property rdfs:domain <{selected_domain_iri}> .
                      FILTER (isIRI(?property))
                      OPTIONAL {{ ?property rdfs:label ?label }}
                      OPTIONAL {{ ?property rdfs:comment ?comment }}
                    }}
                    GROUP BY ?property ?label ?comment
                    """

            # Range filter
            if property_filter_type == "Range":
                with col1:
                    col1a, col1b = st.columns([1.5,1])
                with col1a:
                    list_to_choose = sorted(list(range_dict))
                    list_to_choose.insert(0, "No range filter")
                    selected_range_filter = st.selectbox("📡 Select range filter:*", list_to_choose,
                        key="key_selected_range_filter")

                if selected_range_filter != "No range filter":
                    selected_range_iri = range_dict[selected_range_filter]

                    query = f"""
                    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX owl:  <http://www.w3.org/2002/07/owl#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                    SELECT DISTINCT ?property ?label ?comment (GROUP_CONCAT(STR(?type); separator=", ") AS ?types) WHERE {{
                      ?property rdf:type ?type .
                      FILTER(?type IN (
                        rdf:Property,
                        owl:ObjectProperty,
                        owl:DatatypeProperty,
                        owl:AnnotationProperty
                      ))
                      ?property rdfs:range <{selected_range_iri}> .
                      FILTER (isIRI(?property))
                      OPTIONAL {{ ?property rdfs:label ?label }}
                      OPTIONAL {{ ?property rdfs:comment ?comment }}
                    }}
                    GROUP BY ?property ?label ?comment
                    """

            # Property type filter
            if property_filter_type == "Property type":
                with col1:
                    col1a, col1b = st.columns([1.5,1])
                with col1a:
                    property_type_dict = {"rdf: Property": "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property",
                        "owl: ObjectProperty": "http://www.w3.org/2002/07/owl#ObjectProperty",
                        "owl: DatatypeProperty": "http://www.w3.org/2002/07/owl#DatatypeProperty",
                        "owl: AnnotationProperty": "http://www.w3.org/2002/07/owl#AnnotationProperty"}
                    list_to_choose = list(property_type_dict)
                    list_to_choose.insert(0, "Select type")
                    selected_property_type = st.selectbox("📡 Select property type:", list_to_choose,
                        key="key_selected_property_type")

                if selected_property_type != "Select type":
                    selected_property_type_iri = property_type_dict[selected_property_type]

                    query = f"""PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX owl:  <http://www.w3.org/2002/07/owl#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                    SELECT DISTINCT ?property ?label ?comment (GROUP_CONCAT(STR(?type); separator=", ") AS ?types) WHERE {{
                      ?property rdf:type ?type .
                      FILTER(?type = <{selected_property_type_iri}>)
                      FILTER (isIRI(?property))
                      OPTIONAL {{ ?property rdfs:label ?label }}
                      OPTIONAL {{ ?property rdfs:comment ?comment }}
                    }}
                    GROUP BY ?property ?label ?comment
                    """

            # Annotation filter
            if property_filter_type == "Annotation":

                with col1:
                    col1a, col1b = st.columns([2, 1])
                with col1a:
                    annotation_options = ["No annotation filter", "Has comment", "Has label", "Has comment or label",
                        "Has comment and label"]
                    selected_annotation_filter = st.selectbox("📡 Filter by annotation presence (optional):", annotation_options,
                        key="key_selected_property_annotation_filter")

                if selected_annotation_filter != "No annotation filter":

                    base_query = """PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX owl:  <http://www.w3.org/2002/07/owl#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                    SELECT DISTINCT ?property ?label ?comment (GROUP_CONCAT(STR(?type); separator=", ") AS ?types) WHERE {
                      ?property rdf:type ?type .
                      FILTER(?type IN (
                        rdf:Property,
                        owl:ObjectProperty,
                        owl:DatatypeProperty,
                        owl:AnnotationProperty
                      ))
                      FILTER (isIRI(?property))
                      OPTIONAL { ?property rdfs:label ?label }
                      OPTIONAL { ?property rdfs:comment ?comment }
                    """

                    if selected_annotation_filter == "Has comment":
                        query = base_query + "FILTER EXISTS { ?property rdfs:comment ?comment } } GROUP BY ?property ?label ?comment"
                    elif selected_annotation_filter == "Has label":
                        query = base_query + "FILTER EXISTS { ?property rdfs:label ?label } } GROUP BY ?property ?label ?comment"
                    elif selected_annotation_filter == "Has comment or label":
                        query = base_query + """
                        FILTER (EXISTS { ?property rdfs:label ?label } ||
                                EXISTS { ?property rdfs:comment ?comment }) }
                        GROUP BY ?property ?label ?comment"""
                    elif selected_annotation_filter == "Has comment and label":
                        query = base_query + """
                        FILTER (EXISTS { ?property rdfs:label ?label } &&
                                EXISTS { ?property rdfs:comment ?comment }) }
                        GROUP BY ?property ?label ?comment"""

            # Add limit, offset and order
            if order_clause == "Ascending":
                query += " ORDER BY ASC(?property) "
            elif order_clause == "Descending":
                query += " ORDER BY DESC(?property) "
            if limit:
                query += f"LIMIT {limit} "
            if offset:
                query += f"OFFSET {offset}"

            # Get the query results
            results = ontology_for_search.query(query)
            df_data = []

            for row in results:
                prop_iri = getattr(row, "property", "")
                comment = getattr(row, "comment", "")
                label = getattr(row, "label", "")

                prop_types_iris_list = getattr(row, "types", "")
                prop_types_iris_list = [t.strip() for t in prop_types_iris_list.split(",") if t.strip()]
                prop_types_list = []
                if "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property" in prop_types_iris_list:
                    prop_types_list.append("rdf: Property")
                if "http://www.w3.org/2002/07/owl#ObjectProperty" in prop_types_iris_list:
                    prop_types_list.append("owl: ObjectProperty")
                if "http://www.w3.org/2002/07/owl#DatatypeProperty" in prop_types_iris_list:
                    prop_types_list.append("owl:DatatypeProperty")
                if "http://www.w3.org/2002/07/owl#AnnotationProperty" in prop_types_iris_list:
                    prop_types_list.append("owl: AnnotationProperty")
                prop_types = utils.format_list_for_display(prop_types_list)

                df_data.append({"Property": utils.format_iri_to_prefix_label(prop_iri),
                    "Label": label, "Comment": comment, "Property Type": prop_types,
                     "Property IRI": prop_iri  })

            # Create dataframe and display
            df = pd.DataFrame(df_data)
            df = df.loc[:, df.apply(lambda col: col.replace('', pd.NA).notna().any())]  # drop empty columns

            with col1:
                if not df.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>Results ({len(df)}):</b>
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ No results found.
                    </div>""", unsafe_allow_html=True)

        # CUSTOM SEARCH
        if selected_ontology_search == "✏️ Custom search":

            with col1a:
                query = st.text_area("⌨️ Enter SPARQL query:*")

            if query:
                try:
                    # Get query results
                    results = ontology_for_search.query(query)
                    rows = []
                    columns = set()

                    for row in results:
                        row_dict = {}
                        for var in row.labels:
                            value = row[var]
                            row_dict[str(var)] = str(value) if value else ""
                            columns.add(str(var))
                        rows.append(row_dict)

                    # Create and display the dataframe
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


#_______________________________________________________________________________
# PANEL: VIEW ONTOLOGY
with tab3:
    col1, col2, col2a, col2b = utils.get_panel_layout(narrow=True)

    # RIGHT COLUMN: ONTOLOGY INFO BOX-------------------------------------------
    with col2b:
        utils.get_corner_status_message(ontology_info=True)

    # PURPLE HEADING: VIEW ONTOLOGY---------------------------------------------
    if not st.session_state["g_ontology_components_dict"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            utils.get_missing_element_error_message(ontology=True)

    else:

        with col1:
            st.markdown("""<div class="purple-heading">
                    👨‍💻 View Ontology
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["ontology_downloaded_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.write("")
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>ontology</b> has been downloaded!
                </div>""", unsafe_allow_html=True)
            st.session_state["ontology_downloaded_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        with col1:
            col1a, col1b = st.columns([2,1.5])
        with col1a:
            if not "key_export_format_selectbox" in st.session_state:
                st.session_state["key_export_format_selectbox"] = "🐢 turtle"  # this ensures ntriples wont keep selected after download
            format_options_dict = {"🐢 turtle": "turtle", "3️⃣ ntriples": "ntriples"}
            preview_format_display = st.radio("🖱️ Select format:*", format_options_dict,
                label_visibility="collapsed", horizontal=True, key="key_export_format_selectbox")
            preview_format = format_options_dict[preview_format_display]

        if len(st.session_state["g_ontology_components_dict"]) > 1:
            with col1b:
                list_to_choose = sorted(st.session_state["g_ontology_components_tag_dict"].values())
                list_to_choose.insert(0, "All ontologies")
                if not "key_ontology_component_for_preview_tag" in st.session_state:
                    st.session_state["key_ontology_component_for_preview_tag"] = "All ontologies"  # this ensures the all ontologies selected after download
                ontology_component_for_preview_tag = st.selectbox("🧩 Select ontology (optional):", list_to_choose,
                    key="key_ontology_component_for_preview_tag")
            if ontology_component_for_preview_tag == "All ontologies":
                ontology_for_preview = st.session_state["g_ontology"]
            else:
                for ont, ont_tag in st.session_state["g_ontology_components_tag_dict"].items():
                    if ont_tag == ontology_component_for_preview_tag:
                        ontology_for_preview = st.session_state["g_ontology_components_dict"][ont]

        else:
            ontology_for_preview = st.session_state["g_ontology"]

        serialised_data = ontology_for_preview.serialize(format=preview_format)
        max_length = utils.get_max_length_for_display()[9]
        if len(serialised_data) > max_length:
            with col2:
                col2a, col2b = st.columns([0.5,2])
            with col2b:
                st.markdown(f"""<div class="info-message-blue">
                    🐘 <b>Your ontology is quite large</b> ({utils.format_number_for_display(len(ontology_for_preview))} triples).
                    <small>Showing only the first {utils.format_number_for_display(max_length)} characters
                    (out of {utils.format_number_for_display(len(serialised_data))}) to avoid performance issues.</small>
                </div>""", unsafe_allow_html=True)

        st.code(serialised_data[:max_length])

        allowed_format_dict = utils.get_supported_formats(mapping=True)
        extension = allowed_format_dict[preview_format]
        if len(st.session_state["g_ontology_components_dict"])> 1 and ontology_for_preview == st.session_state["g_ontology"]:
            download_filename = "merged_ontology" + extension
        elif len(st.session_state["g_ontology_components_dict"]) == 1:
            ont_tag = st.session_state["g_ontology_components_tag_dict"].get(ont_label, "UNKNOWN")  #HERE
            ont_tag = st.session_state["g_ontology_components_tag_dict"][ont_label]
            download_filename = ont_tag + extension
        else:
            download_filename = ontology_component_for_preview_tag + extension

        if len(st.session_state["g_ontology_components_dict"]) > 1:
            with col1a:
                st.session_state["ontology_downloaded_ok_flag"] = st.download_button(label="Download", data=serialised_data,
                    file_name=download_filename, mime="text/plain")
        else:
            with col1b:
                st.session_state["ontology_downloaded_ok_flag"] = st.download_button(label="Download", data=serialised_data,
                    file_name=download_filename, mime="text/plain")

        if st.session_state["ontology_downloaded_ok_flag"]:
            st.rerun()

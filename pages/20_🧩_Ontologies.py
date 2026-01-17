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
    # store information___________________________
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
    # store information___________________________
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
    # store information___________________________
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

# TAB4
def add_custom_term():
    # get info_____________________________________
    custom_term_type = st.session_state["custom_term_type"]
    term_iri = st.session_state["term_iri"]
    # store information___________________________
    if custom_term_type == "🏷️ Class":
        st.session_state["custom_terms_dict"][term_iri] =  "🏷️ Class"
    else:
        st.session_state["custom_terms_dict"][term_iri] =  "🔗 Property"
    st.session_state["custom_term_saved_ok_flag"] = True
    # reset fields____________________________________
    st.session_state["key_term_prefix"] = "Select namespace"
    st.session_state["key_term_input"] = ""
    st.session_state["key_custom_term_type"] = "🏷️ Class"

def remove_custom_terms():
    # get info__________________________________
    keys_to_delete = []
    for term_iri in st.session_state["custom_terms_dict"]:
        for term_label in terms_to_remove_list:
            if term_label == utils.get_node_label(term_iri):
                keys_to_delete.append(term_iri)
    # store information___________________________
    for key in keys_to_delete:
        del st.session_state["custom_terms_dict"][key]
    st.session_state["custom_terms_removed_ok_flag"] = True
    # reset fields____________________________________
    st.session_state["key_terms_to_remove_list"] = []
    st.session_state["filter_by_type"] = "🏷️ Class"


#_______________________________________________________________________________
# PANELS OF THE PAGE (tabs)
tab1, tab2, tab3, tab4 = st.tabs(["Import Ontology", "Explore Ontology", "View Ontology", "Custom Terms"])

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
        st.write("")
        import_ontology_selected_option = st.radio("🖱️ Import ontology from:*", ["🌐 URL", "📁 File"],
            label_visibility="collapsed", horizontal=True, key="key_import_ontology_selected_option")

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
            list_to_choose = ["🏷️ Classes", "🔗 Properties", "✏️ Custom search"]
            selected_ontology_search = st.radio("🖱️ Select search:*", list_to_choose,
                label_visibility="collapsed", horizontal=True, key="key_selected_ontology_search")

        if len(st.session_state["g_ontology_components_dict"]) > 1:
            with col1:
                col_ont, col_filter_a, col_filter_b = st.columns(3)
            with col_ont:
                list_to_choose = sorted(st.session_state["g_ontology_components_tag_dict"].values())
                list_to_choose.insert(0, "No filter")
                ontology_component_for_search_tag = st.selectbox("🧩 Filter by ontology:", list_to_choose,
                    key="key_ontology_component_for_search_tag")
            if ontology_component_for_search_tag == "No filter":
                ontology_for_search = st.session_state["g_ontology"]
            else:
                for ont, ont_tag in st.session_state["g_ontology_components_tag_dict"].items():
                    if ont_tag == ontology_component_for_search_tag:
                        ontology_for_search = st.session_state["g_ontology_components_dict"][ont]
        else:
            ontology_for_search = st.session_state["g_ontology"]
            with col1:
                col_filter_a, col_filter_b = st.columns(2)

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

            superclass_dict = {}
            for s, p, o in list(set(ontology_for_search.triples((None, RDFS.subClassOf, None)))):
                if not isinstance(o, BNode) and o not in superclass_dict.values():
                    superclass_dict[utils.get_node_label(o)] = o

            with col_filter_a:
                list_to_choose = ["No filter", "Class type", "Annotation"]
                if superclass_dict:
                    list_to_choose.insert(1, "Superclass")
                class_filter_type = st.selectbox("📡 Add filter:", list_to_choose,
                    key="key_class_filter_type")

            with col_filter_b:
                if class_filter_type == "Superclass":
                    superclass_list = sorted(superclass_dict.keys())
                    superclass_list.insert(0, "No filter")
                    selected_superclass_filter = st.selectbox("📡 Filter by superclass:", superclass_list,
                        key="key_selected_superclass_filter")   #superclass label

                if class_filter_type == "Class type":
                    list_to_choose = ["No filter", "owl: Class", "rdfs: Class"]
                    selected_class_type = st.selectbox("📡 Filter by class type:", list_to_choose,
                        key="key_selected_class_type")

                if class_filter_type == "Annotation":
                    annotation_options = ["No filter", "Has comment", "Has label", "Has comment or label",
                        "Has comment and label"]
                    selected_annotation_filter = st.selectbox("📡 Filter by annotation:", annotation_options,
                        key="key_selected_annotation_filter")

            with col1:
                col1a, col1b, col1c = st.columns(3)

            with col1a:
                limit = st.text_input("🎚️ Enter limit: ᵒᵖᵗ", key="key_limit", placeholder="🎚️ Limit ᵒᵖᵗ",
                    label_visibility="collapsed")
                limit = "" if not limit.isdigit() else limit

            with col1b:
                offset = st.text_input("🎚️ Enter offset: ᵒᵖᵗ", key="key_offset", placeholder="🎚️ Offset ᵒᵖᵗ",
                    label_visibility="collapsed")
                offset = "" if not offset.isdigit() else offset
            with col1c:
                list_to_choose = ["⮔ No order", "⮝ Ascending", "⮝ Descending"]
                order_clause = st.selectbox("🎚️ Select order: ᵒᵖᵗ", list_to_choose,
                    key="key_order_clause", label_visibility="collapsed")

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

            # Superclass filter
            if class_filter_type == "Superclass":

                if selected_superclass_filter != "No filter":
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

                if selected_class_type != "No filter":

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

                if selected_annotation_filter != "No filter":

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
            if order_clause == "⮝ Ascending":
                query += f"ORDER BY ASC(?class) "
            elif order_clause == "⮝ Descending":
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
                        "Class": utils.get_node_label(class_iri),
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

            superproperty_dict = {}
            for s, p, o in ontology_for_search.triples((None, RDFS.subPropertyOf, None)):
                if isinstance(o, URIRef) and o not in superproperty_dict.values():
                    superproperty_dict[utils.get_node_label(o)] = o

            domain_dict = {}
            for s, p, o in ontology_for_search.triples((None, RDFS.domain, None)):
                if isinstance(o, URIRef) and o not in domain_dict.values():
                    domain_dict[utils.get_node_label(o)] = o

            range_dict = {}
            for s, p, o in ontology_for_search.triples((None, RDFS.range, None)):
                if isinstance(o, URIRef) and o not in range_dict.values():
                    range_dict[utils.get_node_label(o)] = o

            with col_filter_a:
                list_to_choose = ["No filter", "Property type", "Annotation"]
                if range_dict:
                    list_to_choose.insert(1,"Range")
                if domain_dict:
                    list_to_choose.insert(1,"Domain")
                if superproperty_dict:
                    list_to_choose.insert(1,"Superproperty")
                property_filter_type = st.selectbox("📡 Add filter:", list_to_choose,
                    key="key_property_filter_type")

            with col_filter_b:
                if property_filter_type == "Superproperty":
                    list_to_choose = sorted(list(superproperty_dict))
                    list_to_choose.insert(0, "No filter")
                    selected_superproperty_filter = st.selectbox("📡 Filter by superproperty:", list_to_choose,
                        key="key_selected_superproperty_filter")

                if property_filter_type == "Domain":
                    list_to_choose = sorted(list(domain_dict))
                    list_to_choose.insert(0, "No filter")
                    selected_domain_filter = st.selectbox("📡 Filter by domain", list_to_choose,
                        key="key_selected_domain_filter")

                if property_filter_type == "Range":
                    list_to_choose = sorted(list(range_dict))
                    list_to_choose.insert(0, "No filter")
                    selected_range_filter = st.selectbox("📡 Filter by range:", list_to_choose,
                        key="key_selected_range_filter")

                if property_filter_type == "Property type":
                    property_type_dict = {"rdf: Property": "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property",
                        "owl: ObjectProperty": "http://www.w3.org/2002/07/owl#ObjectProperty",
                        "owl: DatatypeProperty": "http://www.w3.org/2002/07/owl#DatatypeProperty",
                        "owl: AnnotationProperty": "http://www.w3.org/2002/07/owl#AnnotationProperty"}
                    list_to_choose = list(property_type_dict)
                    list_to_choose.insert(0, "No filter")
                    selected_property_type = st.selectbox("📡 Filter by property type:", list_to_choose,
                        key="key_selected_property_type")

                if property_filter_type == "Annotation":
                    annotation_options = ["No filter", "Has comment", "Has label", "Has comment or label",
                        "Has comment and label"]
                    selected_annotation_filter = st.selectbox("📡 Filter by annotation:", annotation_options,
                        key="key_selected_property_annotation_filter")

            with col1:
                col1a, col1b, col1c = st.columns(3)

            with col1a:
                limit = st.text_input("🎚️ Enter limit: ᵒᵖᵗ", key="key_limit_prop", placeholder="🎚️ Limit ᵒᵖᵗ",
                    label_visibility="collapsed")
                limit = "" if not limit.isdigit() else limit
            with col1b:
                offset = st.text_input("🎚️ Enter offset: ᵒᵖᵗ", key="key_offset_prop", placeholder="🎚️ Offset ᵒᵖᵗ",
                    label_visibility="collapsed")
                offset = "" if not offset.isdigit() else offset
            with col1c:
                list_to_choose = ["⮔ No order", "⮝ Ascending", "⮝ Descending"]
                order_clause = st.selectbox("🎚️ Select order: ᵒᵖᵗ", list_to_choose,
                    key="key_order_clause_prop", label_visibility="collapsed")

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

            # Superproperty filter
            if property_filter_type == "Superproperty":

                if selected_superproperty_filter != "No filter":
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

                if selected_domain_filter != "No filter":
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

                if selected_range_filter != "No filter":
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

                if selected_property_type != "No filter":
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

                if selected_annotation_filter != "No filter":

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
            if order_clause == "⮝ Ascending":
                query += " ORDER BY ASC(?property) "
            elif order_clause == "⮝ Descending":
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

                df_data.append({"Property": utils.get_node_label(prop_iri),
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
                        ⚠️ No results.
                    </div>""", unsafe_allow_html=True)

        # CUSTOM SEARCH
        if selected_ontology_search == "✏️ Custom search":

            with col1:
                col1a, col1b = st.columns([2,1])

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
                                ⚠️ No results.
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
                list_to_choose.insert(0, "No filter")
                if not "key_ontology_component_for_preview_tag" in st.session_state:
                    st.session_state["key_ontology_component_for_preview_tag"] = "No filter"  # this ensures the all ontologies selected after download
                ontology_component_for_preview_tag = st.selectbox("🧩 Filter by ontology:", list_to_choose,
                    key="key_ontology_component_for_preview_tag")
            if ontology_component_for_preview_tag == "No filter":
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

#_______________________________________________________________________________
# PANEL: CUSTOM TERMS
with tab4:
    col1, col2, col2a, col2b = utils.get_panel_layout(narrow=True)

    with col2b:
        utils.display_right_column_df("custom_terms", "custom terms")

    # PURPLE HEADING: ADD CUSTOM TERMS------------------------------------------
    with col1:
        st.markdown("""<div class="purple-heading">
                ✏️ Add Custom Terms
            </div>""", unsafe_allow_html=True)
        st.write("")

    if st.session_state["custom_term_saved_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>term</b> has been saved!
            </div>""", unsafe_allow_html=True)
        st.session_state["custom_term_saved_ok_flag"] = False
        time.sleep(utils.get_success_message_time())
        st.rerun()

    with col1:
        col1a, col1b, col1c = st.columns(3)

    with col1a:
        mapping_ns_dict = utils.get_g_ns_dict(st.session_state["g_mapping"])
        prefix_list = list(mapping_ns_dict.keys())
        list_to_choose = sorted(mapping_ns_dict.keys())
        list_to_choose.insert(0,"Select namespace")
        term_prefix = st.selectbox("🖱️ Select namespace:", list_to_choose,
            key="key_term_prefix")

    with col1b:
        term_input = st.text_input("⌨️ Enter term:*", key="key_term_input")

    with col1c:
        list_to_choose = ["🏷️ Class", "🔗 Property"]
        st.write("")
        custom_term_type = st.radio("Select type*", list_to_choose, label_visibility="collapsed",
            key="key_custom_term_type")

    term_iri = ""
    if term_input and term_prefix != "Select namespace":
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            valid_input_flag = utils.is_valid_label(term_input, hard=True)
        NS = Namespace(mapping_ns_dict[term_prefix])
        term_iri = NS[term_input] if valid_input_flag else ""
    elif term_input and utils.is_valid_iri(term_input, delimiter_ending=False):
        term_iri = term_input
    elif term_input:
        term = "class" if custom_term_type == "🏷️ Class" else "property"
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.markdown(f"""<div class="error-message">
                ❌ <b> Invalid {term}. </b>
                <small>If no namespace is selected, the <b>{term}</b> must be a <b>valid IRI</b></small>
            </div>""", unsafe_allow_html=True)


    if term_iri and term_iri in st.session_state["custom_terms_dict"]:
        with col1:
            col1a, col1b = st.columns([2,1])

        with col1a:
            term = "class" if custom_term_type == "🏷️ Class" else "property"
            opposite_term = "property" if custom_term_type == "🏷️ Class" else "class"

            if st.session_state["custom_terms_dict"][term_iri] == custom_term_type:
                st.markdown(f"""<div class="error-message">
                    ❌ <b> Custom {term} already exists.</b>
                </div>""", unsafe_allow_html=True)

            else:
                st.markdown(f"""<div class="warning-message">
                    ⚠️ <b>This custom {term} already exists as a {opposite_term}.</b>
                    <small>If you continue, it will be overwritten.</small>
                </div>""", unsafe_allow_html=True)
                st.write("")
                st.session_state["custom_term_type"] = custom_term_type
                st.session_state["term_iri"] = term_iri
                st.button("Save", key="key_add_custom_term_button", on_click=add_custom_term)

    elif term_iri:
        with col1:
            col1a, col1b = st.columns([2,1])

        with col1a:
            st.session_state["custom_term_type"] = custom_term_type
            st.session_state["term_iri"] = term_iri
            st.button("Save", key="key_add_custom_term_button", on_click=add_custom_term)

    # SUCCESS MESSAGE: REMOVE CUSTOM TERM---------------------------------------
    # Only shows here when no "Remove Custom Term" purple heading
    if not st.session_state["custom_terms_dict"]:
        if st.session_state["custom_terms_removed_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>custom term(s)</b> have been removed!
                </div>""", unsafe_allow_html=True)
            st.write("")
            st.write("")
            st.session_state["custom_terms_removed_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()


    # PURPLE HEADING: REMOVE CUSTOM TERMS---------------------------------------
    # Only shows if there exist custom terms to be removed
    if st.session_state["custom_terms_dict"]:
        with col1:
            st.write("_____")
            st.markdown("""<div class="purple-heading">
                    🗑️ Remove Custom Terms
                </div>""", unsafe_allow_html=True)
            st.write("")

        if st.session_state["custom_terms_removed_ok_flag"]:
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                st.markdown(f"""<div class="success-message-flag">
                    ✅ The <b>custom term(s)</b> have been removed!
                </div>""", unsafe_allow_html=True)
            st.write("")
            st.write("")
            st.session_state["custom_terms_removed_ok_flag"] = False
            time.sleep(utils.get_success_message_time())
            st.rerun()

        with col1:
            col1a, col1b = st.columns([2,1])

        class_list = []
        property_list = []
        for term_iri in st.session_state["custom_terms_dict"]:
            if st.session_state["custom_terms_dict"][term_iri] == "🏷️ Class":
                class_list.append(utils.get_node_label(term_iri))
            else:
                property_list.append(utils.get_node_label(term_iri))

        with col1b:
            list_to_choose = []
            if class_list:
                list_to_choose.append("🏷️ Class")
            if property_list:
                list_to_choose.append("🔗 Property")
            st.write("")
            if len(list_to_choose) == 1:
                st.write("")
            filter_by_type = st.radio("📡 Filter by type:*", list_to_choose,
                label_visibility="collapsed", key="key_filter_by_type")

        with col1a:
            list_to_choose = []
            for term_iri in st.session_state["custom_terms_dict"]:
                if st.session_state["custom_terms_dict"][term_iri] == filter_by_type:
                    list_to_choose.append(utils.get_node_label(term_iri))
            list_to_choose = sorted(list_to_choose)
            if len(list_to_choose) > 1:
                list_to_choose.insert(0, "Select all")
            terms_to_remove_list = st.multiselect("🖱️ Select terms:*", list_to_choose,
                key="key_terms_to_remove_list")

            terms = "classes" if filter_by_type == "🏷️ Class" else "properties"
            if "Select all" in terms_to_remove_list:
                st.markdown(f"""<div class="warning-message">
                    ⚠️ You are deleting <b>all custom {terms}</b>.
                    <small>Make sure you want to go ahead.</small>
                </div>""", unsafe_allow_html=True)
                remove_custom_terms_checkbox = st.checkbox(
                f"🔒 I am sure I want to remove all {terms}",
                key="key_unbind_all_ns_button_checkbox")
                terms_to_remove_list = class_list if filter_by_type == "🏷️ Class" else property_list

            else:
                remove_custom_terms_checkbox = st.checkbox(
                f"🔒 I am sure I want to remove the selected {terms}",
                key="key_unbind_all_ns_button_checkbox")

            if terms_to_remove_list and remove_custom_terms_checkbox:
                st.button("Remove", key="key_remove_custom_terms_button",
                    on_click=remove_custom_terms)

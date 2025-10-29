import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle
from rdflib.namespace import split_uri
from rdflib.namespace import RDF, RDFS, DC, DCTERMS, OWL, XSD
from streamlit_js_eval import streamlit_js_eval
import plotly.express as px

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
dark_mode = False if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"] else True
header_html = utils.render_header(title="Ontology-Mapping Lens",
    description="""Get information on how your <b>mapping</b> and your <b>ontology</b> interact.""",
    dark_mode=dark_mode)
st.markdown(header_html, unsafe_allow_html=True)

# Import style--------------------------------------
style_container = st.empty()
if "dark_mode_flag" not in st.session_state or not st.session_state["dark_mode_flag"]:
    style_container.markdown(utils.import_st_aesthetics(), unsafe_allow_html=True)
else:
    style_container.markdown(utils.import_st_aesthetics_dark_mode(), unsafe_allow_html=True)

# Initialise session state variables----------------------------------------
# OTHER PAGES
if not "g_label" in st.session_state:
    st.session_state["g_label"] = ""
if not "g_mapping" in st.session_state:
    st.session_state["g_mapping"] = Graph()

# Namespaces------------------------------------------------------------
RML, RR, QL = utils.get_required_ns_dict().values()

# START PAGE_____________________________________________________________________


col1, col2 = st.columns([2,1.5])
if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
    with col1:
        st.write("")
        st.write("")
        utils.get_missing_g_mapping_error_message_different_page()
        st.stop()


#____________________________________________________________
# PANELS OF THE PAGE (tabs)

tab1, tab2, tab3 = st.tabs(["Ontology Coverage", "Mapping Density", "Domain/Range Validation"])

#________________________________________________
# ONTOLOGY COVERAGE
with tab1:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
    with col2b:
        utils.get_corner_status_message()

    if not st.session_state["g_ontology"]:
        with col1:
            st.markdown(f"""<div class="error-message">
                ❌ You need to import an ontology from the
                <b>Ontologies</b> page <small>(Import Ontology pannel).</small>
            </div>""", unsafe_allow_html=True)

    else:

        #PURPLE HEADING - ONTOLOGY COVERAGE
        with col1:
            st.markdown("""<div class="purple-heading">
                    📈 Ontology Coverage
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a, col1b, col1c = st.columns(3)


        with col1a:
            list_to_choose = ["🗺️ Mapping", "🏷️ Classes", "🔗 Properties"]
            type_for_lens = st.radio("🖱️ Select an option:*", list_to_choose,
                label_visibility="collapsed", key="key_type_for_lens")

        if type_for_lens == "🗺️ Mapping":
            with col1b:
                list_to_choose = ["📊 Stats"]
                selected_class_search = st.selectbox("🖱️ Select an option:*", list_to_choose,
                    key="key_class_search")

            with col1:
                col1a, col1b, col1c, col1d = st.columns([1,1,0.5,0.5])
            with col1a:
                utils.get_mapping_composition_by_class_donut_chart()
            with col1b:
                utils.get_mapping_composition_by_property_donut_chart()
            with col1d:
                utils.get_tm_number_metric()
                utils.get_rules_number_metric()



        if type_for_lens == "🏷️ Classes":

            with col1b:
                list_to_choose = ["📊 Stats", "📐Rules", "ℹ️ Information"]
                selected_class_search = st.selectbox("🖱️ Select an option:*", list_to_choose,
                    key="key_class_search")

            # Filter by ontology
            with col1c:
                list_to_choose = sorted(st.session_state["g_ontology_components_tag_dict"].values())
                if len(list_to_choose) > 1:
                    list_to_choose.insert(0, "No filter")
                ontology_filter_for_lens = st.selectbox("⚙️ Filter by ontology:",
                    list_to_choose, key="key_ontology_filter_for_lens")

            if ontology_filter_for_lens == "No filter":
                ontology_filter_for_lens = st.session_state["g_ontology"]
            else:
                for ont_label, ont_tag in st.session_state["g_ontology_components_tag_dict"].items():
                    if ont_tag == ontology_filter_for_lens:
                        ontology_filter_for_lens = st.session_state["g_ontology_components_dict"][ont_label]
                        break

            # Superclass filter
            superclass_dict = utils.get_ontology_superclass_dict(ontology_filter_for_lens)
            if superclass_dict:   # there exists at least one superclass (show superclass filter)
                classes_in_superclass_dict = {}
                with col1c:
                    superclass_list = sorted(superclass_dict.keys())
                    superclass_list.insert(0, "No filter")
                    superclass_filter_for_lens = st.selectbox("⚙️ Filter by superclass:", superclass_list,
                        key="key_superclass")   #superclass label
            else:
                superclass_filter_for_lens = "No filter"

            if superclass_filter_for_lens != "No filter":   # a superclass has been selected (filter)
                superclass_filter_for_lens = superclass_dict[superclass_filter_for_lens] #we get the superclass iri

            with col1:
                st.write("_____")

            if selected_class_search == "📊 Stats":

                with col1:
                    col1a, col1b, col1c, col1d = st.columns(4)
                with col1a:
                    utils.get_used_classes_metric(ontology_filter_for_lens, superclass_filter=superclass_filter_for_lens)
                with col1b:
                    utils.get_average_class_use_metric(ontology_filter_for_lens, superclass_filter=superclass_filter_for_lens)
                with col1c:
                    utils.get_class_mapping_density_metric(ontology_filter_for_lens)


                with col1:
                    col1a, col1b = st.columns(2)

                with col1a:
                    utils.get_used_classes_donut_chart(ontology_filter_for_lens)

                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1b:
                    ontology_used_classes_count_dict = utils.get_class_dictionaries_filtered_by_superclass(ontology_filter_for_lens, superclass_filter=superclass_filter_for_lens)[2]
                    all_classes = list(ontology_used_classes_count_dict.keys())
                    selected_classes = st.multiselect("🖱️ Select ontology classes to display (opt):", options=all_classes)
                with col1a:
                    utils.get_class_frequency_bar_plot(ontology_filter_for_lens, selected_classes)



            if selected_class_search == "📐Rules":

                with col1:
                    col1a, col1b = st.columns(2)

                # Class selection
                if superclass_dict:   # there exists at least one superclass (show superclass filter)
                    # classes_in_superclass_dict = {}
                    # with col1a:
                    #     superclass_list = sorted(superclass_dict.keys())
                    #     superclass_list.insert(0, "No filter")
                    #     superclass = st.selectbox("⚙️ Filter by superclass (opt):", superclass_list,
                    #         key="key_superclass")   #superclass label
                    if superclass != "No filter":   # a superclass has been selected (filter)
                    #     classes_in_superclass_dict[superclass] = superclass_dict[superclass]
                    #     superclass = superclass_dict[superclass] #we get the superclass iri
                    #     for s, p, o in list(set(st.session_state["g_ontology"].triples((None, RDFS.subClassOf, superclass)))):
                    #         classes_in_superclass_dict[split_uri(s)[1]] = s
                    #     class_list = sorted(classes_in_superclass_dict.keys())
                        list_to_choose = []
                        for class_label in class_list:
                            if class_label in ontology_used_classes_dict:
                                list_to_choose.append(class_label)
                        list_to_choose.insert(0, "Select a class")
                        with col1b:
                            subject_class = st.selectbox("🖱️ Select class:", list_to_choose,
                                key="key_subject_class")   #class label

                    else:  #no superclass selected (list all classes)
                        list_to_choose = sorted(ontology_used_classes_dict.keys())
                        list_to_choose.insert(0, "Select a class")
                        with col1b:
                            subject_class = st.selectbox("🖱️ Select class:*", list_to_choose,
                                key="key_subject_class")   #class label

                else:     #no superclasses exist (no superclass filter)
                    list_to_choose = sorted(ontology_used_classes_dict.keys())
                    list_to_choose.insert(0, "Select a class")
                    with col1a:
                        subject_class = st.selectbox("🖱️ Select class:*", list_to_choose,
                            key="key_subject_class")   #class label

                if subject_class != "Select a class":
                    subject_class_iri = ontology_classes_dict[subject_class] #we get the superclass iri
                    st.session_state["multiple_subject_class_list"] = [subject_class_iri]
                else:
                    subject_class_iri = ""


                if subject_class_iri:
                    # Get all subject maps with the selected class
                    rule_list_for_class = []
                    for s in st.session_state["g_mapping"].subjects(RR["class"], URIRef(subject_class_iri)):
                        sm_rule_list = utils.get_rules_for_sm(s)
                        for rule in sm_rule_list:
                            rule_list_for_class.append(rule)

                    df = pd.DataFrame(rule_list_for_class, columns=["Subject", "Predicate", "Object", "TriplesMap"])

                    # Display
                    with col1:
                        if not df.empty:
                            st.markdown(f"""<div class="info-message-blue">
                                <b>RULES ({len(df)}):</b>
                                &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp
                                <small>🏷️ Subject → 🔗 Predicate → 🎯 Object</b></small>
                            </div>""", unsafe_allow_html=True)
                            st.dataframe(df, hide_index=True)
                        else:
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ No results.
                            </div>""", unsafe_allow_html=True)

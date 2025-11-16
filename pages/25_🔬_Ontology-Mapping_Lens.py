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

# Initialise page---------------------------------------------------------------
utils.init_page()
RML, QL = utils.get_required_ns_dict().values()

# START PAGE_____________________________________________________________________

#____________________________________________________________
# PANELS OF THE PAGE (tabs)
tab1, tab2, tab3 = st.tabs(["Mapping", "Properties", "Classes"])

# ERROR IF NO MAPPING LOADED----------------------------------------------------
col1, col2 = st.columns([2,1])
if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
    with col1:
        utils.get_missing_g_mapping_error_message_different_page()
        st.stop()

#________________________________________________
# ONTOLOGY COVERAGE - MAPPING
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
            col1a, col1b, col1c, col1d = st.columns([1,1,0.5,0.5])
        with col1a:
            class_flag = utils.get_mapping_composition_by_class_donut_chart()
        with col1b:
            property_flag = utils.get_mapping_composition_by_property_donut_chart()
        with col1d:
            utils.get_tm_number_metric()
            utils.get_rules_number_metric()
        if class_flag or property_flag:
            with col2b:
                st.markdown(f"""<div class="info-message-gray">
                        🧮 Composition calculated with the <b>number of rules</b> which use the class or property.
                    </div>""", unsafe_allow_html=True)

#________________________________________________
# ONTOLOGY COVERAGE - PROPERTIES
with tab2:
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
                list_to_choose = ["📊 Stats", "ℹ️ Info table", "📐Rules"]
                selected_property_search = st.selectbox("🖱️ Select an option:*", list_to_choose,
                    key="key_property_search")

        # Filter by ontology
        with col1b:
            list_to_choose = sorted(st.session_state["g_ontology_components_tag_dict"].values())
            if len(list_to_choose) > 1:
                list_to_choose.insert(0, "No filter")
            ontology_filter_for_lens_tag = st.selectbox("⚙️ Filter by ontology:",
                list_to_choose, key="key_ontology_filter_for_lens_property")

        if ontology_filter_for_lens_tag == "No filter":
            ontology_filter_for_lens = st.session_state["g_ontology"]
        else:
            for ont_label, ont_tag in st.session_state["g_ontology_components_tag_dict"].items():
                if ont_tag == ontology_filter_for_lens_tag:
                    ontology_filter_for_lens = st.session_state["g_ontology_components_dict"][ont_label]
                    break

        # Superproperty filter
        superproperty_dict = utils.get_ontology_superproperty_dict(ontology_filter_for_lens)
        properties_in_superpropery_dict = {}
        with col1c:
            superproperty_list = sorted(superproperty_dict.keys())
            superproperty_list.insert(0, "No filter")
            superproperty_filter_for_lens_label = st.selectbox("⚙️ Filter by superproperty:", superproperty_list,
                key="key_superproperty")   #superproperty label

        if superproperty_filter_for_lens_label != "No filter":   # a superproperty has been selected (filter)
            superproperty_filter_for_lens = superproperty_dict[superproperty_filter_for_lens_label] #we get the superproperty iri
        else:
            superproperty_filter_for_lens = None

        if selected_property_search == "📊 Stats":

            with col2b:
                st.markdown(f"""<div class="info-message-gray">
                        🧮 A property is <b>used</b> if it appears in at least one rule (as a predicate).
                        <b>Property frequency</b> is the number of times a property is used in a rule.
                    </div>""", unsafe_allow_html=True)

            with col1:
                st.write("_____")
                col1a, col1b, col1c, col1d, col1e = st.columns([1,1,1,0.1,1])
            with col1a:
                utils.get_used_properties_metric(ontology_filter_for_lens, superproperty_filter=superproperty_filter_for_lens)
            with col1b:
                utils.get_average_property_frequency_metric(ontology_filter_for_lens, superproperty_filter=superproperty_filter_for_lens)
            with col1c:
                utils.get_average_property_frequency_metric(ontology_filter_for_lens, superproperty_filter=superproperty_filter_for_lens, type="all_properties")
            with col1e:
                inner_html = ""
                if ontology_filter_for_lens_tag != "No filter":
                    inner_html += f"""🧩 Ontology:<br><span style="padding-left:20px;">
                        <b style="color:#F63366;">{ontology_filter_for_lens_tag}</b></span><br>"""
                if superproperty_filter_for_lens_label != "No filter":
                    inner_html += f"""🏷️ Superproperty:<br><span style="padding-left:20px;">
                        <b style="color:#F63366;">{superproperty_filter_for_lens_label}</b></span><br>"""
                if inner_html:
                    st.write("")
                    st.markdown(f"""<div class="gray-preview-message">
                            {inner_html}
                        </div>""", unsafe_allow_html=True)


            with col1:
                col1a, col1b = st.columns([1,2])
            with col1a:
                utils.get_used_properties_donut_chart(ontology_filter_for_lens, superproperty_filter=superproperty_filter_for_lens)


            ontology_used_properties_count_dict = utils.get_property_dictionaries_filtered_by_superproperty(ontology_filter_for_lens, superproperty_filter=superproperty_filter_for_lens)[2]
            list_to_choose = list(ontology_used_properties_count_dict.keys())
            if list_to_choose:
                with col1b:
                    selected_properties = st.multiselect("🖱️ Select ontology properties to display (opt):", list_to_choose,
                        key="key_selected_properties")

                    utils.get_property_frequency_bar_plot(ontology_filter_for_lens, selected_properties, superproperty_filter=superproperty_filter_for_lens)

        if selected_property_search == "ℹ️ Info table":
            filtered_ontology_used_properties_count_dict = utils.get_property_dictionaries_filtered_by_superproperty(ontology_filter_for_lens,
                superproperty_filter=superproperty_filter_for_lens)[2]
            filtered_ontology_properties_dict =utils.get_property_dictionaries_filtered_by_superproperty(ontology_filter_for_lens,
                superproperty_filter=superproperty_filter_for_lens)[0]

            rows = []
            for label, iri in filtered_ontology_properties_dict.items():
                is_used = label in filtered_ontology_used_properties_count_dict
                count = filtered_ontology_used_properties_count_dict.get(label, 0)
                rows.append({
                    "property Label": label,
                    "Used": is_used,
                    "#Rules": count,
                    "property IRI": iri})

            df = pd.DataFrame(rows)
            df = df.sort_values(by="#Rules", ascending=False)
            with col1:
                st.markdown(f"""<div class="info-message-blue">
                    <b>🔗 PROPERTIES ({len(df)}):</b>
                </div>""", unsafe_allow_html=True)
                st.dataframe(df, hide_index=True)

            with col1:
                col1a, col1b = st.columns(2)


        if selected_property_search == "📐Rules":

            with col1:
                col1a, col1b = st.columns(2)

            # property selection
            filtered_ontology_used_properties_dict = utils.get_property_dictionaries_filtered_by_superproperty(ontology_filter_for_lens,
                superproperty_filter=superproperty_filter_for_lens)[0]
            list_to_choose = sorted(filtered_ontology_used_properties_dict)
            list_to_choose.insert(0, "Select a property")
            with col1a:
                selected_property = st.selectbox("🖱️ Select property:", list_to_choose,
                    key="key_selected_property")   #property label


            if selected_property != "Select a property":
                selected_property_iri = filtered_ontology_used_properties_dict[selected_property] #we get the superproperty iri
                # Get all predicates that use the selected property
                rule_list_for_property = []
                for sm in st.session_state["g_mapping"].objects(None, RML["subjectMap"]):
                    sm_rule_list = utils.get_rules_for_sm(sm)
                    for rule in sm_rule_list:
                        if rule[1] == utils.format_iri_to_prefix_label(selected_property_iri):
                            rule_list_for_property.append(rule)
                    # for s in st.session_state["g_mapping"].subjects(RML["property"], URIRef(selected_property_iri)):
                    #     sm_rule_list = utils.get_rules_for_sm(s)
                    #     for rule in sm_rule_list:
                    #         rule_list_for_property.append(rule)

                # Display
                with col1:
                    utils.display_rules(rule_list_for_property)

#________________________________________________
# ONTOLOGY COVERAGE - CLASSES
with tab3:
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
            list_to_choose = ["📊 Stats", "ℹ️ Info table", "📐Rules"]
            selected_class_search = st.selectbox("🖱️ Select an option:*", list_to_choose,
                key="key_class_search")

        # Filter by ontology
        with col1b:
            list_to_choose = sorted(st.session_state["g_ontology_components_tag_dict"].values())
            if len(list_to_choose) > 1:
                list_to_choose.insert(0, "No filter")
            ontology_filter_for_lens_tag = st.selectbox("⚙️ Filter by ontology:",
                list_to_choose, key="key_ontology_filter_for_lens_class")

        if ontology_filter_for_lens_tag == "No filter":
            ontology_filter_for_lens = st.session_state["g_ontology"]
        else:
            for ont_label, ont_tag in st.session_state["g_ontology_components_tag_dict"].items():
                if ont_tag == ontology_filter_for_lens_tag:
                    ontology_filter_for_lens = st.session_state["g_ontology_components_dict"][ont_label]
                    break

        # Superclass filter
        superclass_dict = utils.get_ontology_superclass_dict(ontology_filter_for_lens)
        classes_in_superclass_dict = {}
        with col1c:
            superclass_list = sorted(superclass_dict.keys())
            superclass_list.insert(0, "No filter")
            superclass_filter_for_lens_label = st.selectbox("⚙️ Filter by superclass:", superclass_list,
                key="key_superclass")   #superclass label

        if superclass_filter_for_lens_label != "No filter":   # a superclass has been selected (filter)
            superclass_filter_for_lens = superclass_dict[superclass_filter_for_lens_label] #we get the superclass iri
        else:
            superclass_filter_for_lens = None

        if selected_class_search == "📊 Stats":

            with col2b:
                st.markdown(f"""<div class="info-message-gray">
                        🧮 A class is <b>used</b> if it appears in at least one rule.
                        <b>Class frequency</b> is the number of times a class is used in a rule.
                    </div>""", unsafe_allow_html=True)

            with col1:
                st.write("_____")
                col1a, col1b, col1c, col1d, col1e = st.columns([1,1,1,0.1,1])
            with col1a:
                utils.get_used_classes_metric(ontology_filter_for_lens, superclass_filter=superclass_filter_for_lens)
            with col1b:
                utils.get_average_class_frequency_metric(ontology_filter_for_lens, superclass_filter=superclass_filter_for_lens)
            with col1c:
                utils.get_average_class_frequency_metric(ontology_filter_for_lens, superclass_filter=superclass_filter_for_lens, type="all_classes")
            with col1e:
                inner_html = ""
                if ontology_filter_for_lens_tag != "No filter":
                    inner_html += f"""🧩 Ontology:<br><span style="padding-left:20px;">
                        <b style="color:#F63366;">{ontology_filter_for_lens_tag}</b></span><br>"""
                if superclass_filter_for_lens_label != "No filter":
                    inner_html += f"""🏷️ Superclass:<br><span style="padding-left:20px;">
                        <b style="color:#F63366;">{superclass_filter_for_lens_label}</b></span><br>"""
                if inner_html:
                    st.write("")
                    st.markdown(f"""<div class="gray-preview-message">
                            {inner_html}
                        </div>""", unsafe_allow_html=True)


            with col1:
                col1a, col1b = st.columns([1,2])
            with col1a:
                utils.get_used_classes_donut_chart(ontology_filter_for_lens, superclass_filter=superclass_filter_for_lens)


            ontology_used_classes_count_by_rules_dict = utils.get_class_dictionaries_filtered_by_superclass(ontology_filter_for_lens, superclass_filter=superclass_filter_for_lens)[3]
            list_to_choose = list(ontology_used_classes_count_by_rules_dict.keys())
            if list_to_choose:
                with col1b:
                    selected_classes = st.multiselect("🖱️ Select ontology classes to display (opt):", list_to_choose,
                        key="key_selected_classes")

                    utils.get_class_frequency_bar_plot(ontology_filter_for_lens, selected_classes, superclass_filter=superclass_filter_for_lens)


        if selected_class_search == "ℹ️ Info table":

            filtered_ontology_used_classes_count_by_rules_dict = utils.get_class_dictionaries_filtered_by_superclass(ontology_filter_for_lens,
                superclass_filter=superclass_filter_for_lens)[3]
            filtered_ontology_classes_dict =utils.get_class_dictionaries_filtered_by_superclass(ontology_filter_for_lens,
                superclass_filter=superclass_filter_for_lens)[0]

            rows = []
            for label, iri in filtered_ontology_classes_dict.items():
                is_used = label in filtered_ontology_used_classes_count_by_rules_dict
                count = filtered_ontology_used_classes_count_by_rules_dict.get(label, 0)
                rows.append({
                    "Class Label": label,
                    "Used": is_used,
                    "#Rules": count,
                    "Class IRI": utils.format_iri_to_prefix_label(iri)})

            df = pd.DataFrame(rows)
            df = df.sort_values(by="#Rules", ascending=False)
            with col1:
                st.markdown(f"""<div class="info-message-blue">
                    <b>🏷️ CLASSES ({len(df)}):</b>
                </div>""", unsafe_allow_html=True)
                st.dataframe(df, hide_index=True)

            with col1:
                col1a, col1b = st.columns(2)


        if selected_class_search == "📐Rules":

            with col1:
                col1a, col1b = st.columns(2)

            # Class selection
            filtered_ontology_used_classes_dict = utils.get_class_dictionaries_filtered_by_superclass(ontology_filter_for_lens,
                superclass_filter=superclass_filter_for_lens)[0]
            list_to_choose = list(filtered_ontology_used_classes_dict)
            list_to_choose.insert(0, "Select a class")
            with col1a:
                subject_class = st.selectbox("🖱️ Select class:", list_to_choose,
                    key="key_subject_class")   #class label


            if subject_class != "Select a class":
                subject_class_iri = filtered_ontology_used_classes_dict[subject_class] #we get the superclass iri
                # Get all subject maps with the selected class
                rule_list_for_class = []
                for s in st.session_state["g_mapping"].subjects(RML["class"], URIRef(subject_class_iri)):
                    sm_rule_list = utils.get_rules_for_sm(s)
                    for rule in sm_rule_list:
                        rule_list_for_class.append(rule)

                # Display
                with col1:
                    utils.display_rules(rule_list_for_class)

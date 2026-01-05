from collections import defaultdict
import pandas as pd
from rdflib import URIRef
import streamlit as st
import utils

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

#____________________________________________________________
# PANELS OF THE PAGE (tabs)
tab1, tab2, tab3, tab4 = st.tabs(["Mapping Composition", "Class Usage", "Property Usage", "External Terms"])

# ERROR MESSAGE: NO MAPPING LOADED----------------------------------------------
col1, col2 = st.columns([2,1])
if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
    with col1:
        utils.get_missing_element_error_message(mapping=True, different_page=True)
        st.stop()

#_______________________________________________________________________________
# PANEL: ONTOLOGY COVERAGE
with tab1:
    col1, col2, col2a, col2b = utils.get_panel_layout(narrow=True)
    with col2b:
        utils.get_corner_status_message(mapping_info=True, ontology_info=True)

    if not st.session_state["g_ontology"]:
        with col1:
            utils.get_missing_element_error_message(ontology=True, different_page=True)

    else:
        #PURPLE HEADING: MAPPING COMPOSITION BY ONTOLOGY------------------------
        with col1:
            st.markdown("""<div class="purple-heading">
                    🍩 Mapping composition by ontology
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
                        <small>🧮 Composition calculated with the <b>number of rules</b> which use the class or property.</small>
                    </div>""", unsafe_allow_html=True)


#_______________________________________________________________________________
# PANEL: CLASS USAGE
with tab2:
    col1, col2, col2a, col2b = utils.get_panel_layout(narrow=True)
    with col2b:
        utils.get_corner_status_message(mapping_info=True, ontology_info=True)

    if not st.session_state["g_ontology"]:
        with col1:
            utils.get_missing_element_error_message(ontology=True, different_page=True)

    else:
        #PURPLE HEADING: CLASS USAGE-----------------------------------------
        with col1:
            st.markdown("""<div class="purple-heading">
                    🏷️ Class Usage
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a, col1b, col1c = st.columns(3)

        with col1a:
            list_to_choose = ["📊 Stats", "ℹ️ Info table", "📐Rules"]
            selected_class_search = st.radio("🖱️ Select an option:*", list_to_choose,
                label_visibility="collapsed", key="key_class_search")

        # Filter by ontology
        with col1b:
            list_to_choose = sorted(st.session_state["g_ontology_components_tag_dict"].values())
            if len(list_to_choose) > 1:
                list_to_choose.insert(0, "No filter")
            ontology_filter_for_lens_tag = st.selectbox("🧩 Filter by ontology (opt):",
                list_to_choose, key="key_ontology_filter_for_lens_class")

        if ontology_filter_for_lens_tag == "No filter":
            ontology_filter_for_lens = st.session_state["g_ontology"]
        else:
            for ont_label, ont_tag in st.session_state["g_ontology_components_tag_dict"].items():
                if ont_tag == ontology_filter_for_lens_tag:
                    ontology_filter_for_lens = st.session_state["g_ontology_components_dict"][ont_label]
                    break

        # Filter by superclass
        superclass_dict = utils.get_ontology_class_dict(ontology_filter_for_lens, superclass=True)
        classes_in_superclass_dict = {}
        with col1c:
            superclass_list = sorted(superclass_dict.keys())
            superclass_list.insert(0, "No filter")
            superclass_filter_for_lens_label = st.selectbox("📡 Filter by superclass (opt):", superclass_list,
                key="key_superclass")   #superclass label

        if superclass_filter_for_lens_label != "No filter":   # a superclass has been selected (filter)
            superclass_filter_for_lens = superclass_dict[superclass_filter_for_lens_label] # get the superclass iri
        else:
            superclass_filter_for_lens = None

        with col1:
            st.markdown("<hr style='margin-top:6px; margin-bottom:6 px; border:0; border-top:1px solid #ddd;'>",
                unsafe_allow_html=True)

        # STATS
        if selected_class_search == "📊 Stats":

            with col2b:
                st.markdown(f"""<div class="info-message-gray">
                        <small>🧮 A class is considered <b>used</b> if it appears in at least one rule.
                        <b>Class frequency</b> is the number of times a class is used in a rule.</small>
                    </div>""", unsafe_allow_html=True)

            with col1:
                col1a, col1b, col1c, col1d, col1e = st.columns([1,1,1,0.1,1])
            with col1a:
                utils.get_used_ontology_terms_metric(ontology_filter_for_lens, superfilter=superclass_filter_for_lens, class_=True)
            with col1b:
                utils.get_average_ontology_term_frequency_metric(ontology_filter_for_lens, superfilter=superclass_filter_for_lens)
            with col1c:
                utils.get_average_ontology_term_frequency_metric(ontology_filter_for_lens, superfilter=superclass_filter_for_lens, class_=True, type="all")
            with col1e:
                utils.get_filter_info_message_for_lens(ontology_filter_for_lens_tag, superclass_filter_for_lens_label)

            with col1:
                col1a, col1b = st.columns([1,2])
            with col1a:
                utils.get_used_ontology_terms_donut_chart(ontology_filter_for_lens, superfilter=superclass_filter_for_lens, class_=True)

            ontology_used_classes_count_by_rules_dict = utils.get_class_dictionaries_filtered_by_superclass(ontology_filter_for_lens, superclass_filter=superclass_filter_for_lens)[3]
            list_to_choose = list(ontology_used_classes_count_by_rules_dict.keys())
            if list_to_choose:
                with col1b:
                    selected_classes = st.multiselect("🖱️ Select ontology classes to display (opt):", list_to_choose,
                        key="key_selected_classes")

                    utils.get_ontology_term_frequency_bar_plot(ontology_filter_for_lens, selected_classes, superfilter=superclass_filter_for_lens, class_=True)

        # INFO TABLE
        if selected_class_search == "ℹ️ Info table":

            with col1:
                col1a, col1b = st.columns([2,1])

            with col1b:
                utils.get_filter_info_message_for_lens(ontology_filter_for_lens_tag, utils.get_node_label(superproperty_filter_for_lens))

            filtered_ontology_used_classes_count_by_rules_dict = utils.get_class_dictionaries_filtered_by_superclass(ontology_filter_for_lens,
                superclass_filter=superclass_filter_for_lens)[3]
            filtered_ontology_class_dict =utils.get_class_dictionaries_filtered_by_superclass(ontology_filter_for_lens,
                superclass_filter=superclass_filter_for_lens)[0]

            with col1a:
                list_to_choose = sorted(filtered_ontology_class_dict.keys())
                selected_classes_for_lens = st.multiselect("🖱️ Select ontology classes to display (optional):", list_to_choose,
                    key="key_selected_classes_for_lens")
                selected_classes_for_lens = sorted(filtered_ontology_class_dict.keys()) if not selected_classes_for_lens else selected_classes_for_lens

            rows = []
            for class_label in selected_classes_for_lens:
                is_used = class_label in filtered_ontology_used_classes_count_by_rules_dict
                count = filtered_ontology_used_classes_count_by_rules_dict.get(class_label, 0)
                ont_tag = "Other"
                for ont_label, g_ont in st.session_state["g_ontology_components_dict"].items():
                    class_dict = utils.get_ontology_class_dict(g_ont)
                    if class_label in class_dict:
                        ont_tag = st.session_state["g_ontology_components_tag_dict"][ont_label]
                        break
                rows.append({"Class": class_label, "Used": is_used,
                    "#Rules": count, "Ontology": ont_tag})


            df = pd.DataFrame(rows)
            df = df.sort_values(by="#Rules", ascending=False)
            with col1:
                if not df.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>🏷️ CLASSES ({len(df)}):</b>
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ No results.
                    </div>""", unsafe_allow_html=True)

        # RULES
        if selected_class_search == "📐Rules":

            with col1:
                col1a, col1b = st.columns([2,1])

            with col1b:
                utils.get_filter_info_message_for_lens(ontology_filter_for_lens_tag, utils.get_node_label(superproperty_filter_for_lens))

            # Class selection
            filtered_ontology_used_class_dict = utils.get_class_dictionaries_filtered_by_superclass(ontology_filter_for_lens,
                superclass_filter=superclass_filter_for_lens)[0]
            list_to_choose = list(filtered_ontology_used_class_dict)
            list_to_choose.insert(0, "Select class")
            with col1a:
                subject_class = st.selectbox("🖱️ Select class:", list_to_choose,
                    key="key_subject_class")   #class label

            if subject_class != "Select class":
                subject_class_iri = filtered_ontology_used_class_dict[subject_class] # get the class iri
                rule_list_for_class = []    # get all rules that use the selected class
                for s in st.session_state["g_mapping"].subjects(RML["class"], URIRef(subject_class_iri)):
                    sm_rule_list = utils.get_rules_for_sm(s)
                    for rule in sm_rule_list:
                        rule_list_for_class.append(rule)

                # Display
                with col1:
                    utils.display_rule_list(rule_list_for_class)

#_______________________________________________________________________________
# PANEL: PROPERTY USAGE
with tab3:
    col1, col2, col2a, col2b = utils.get_panel_layout(narrow=True)
    with col2b:
        utils.get_corner_status_message(mapping_info=True, ontology_info=True)

    if not st.session_state["g_ontology"]:
        with col1:
            utils.get_missing_element_error_message(ontology=True, different_page=True)

    else:

        #PURPLE HEADING: PROPERTY USAGE-----------------------------------------
        with col1:
            st.markdown("""<div class="purple-heading">
                    🔗 Property Usage
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a, col1b, col1c = st.columns(3)

            with col1a:
                list_to_choose = ["📊 Stats", "ℹ️ Info table", "📐Rules"]
                selected_property_search = st.radio("🖱️ Select an option:*", list_to_choose,
                    label_visibility="collapsed", key="key_property_search")

        # Filter by ontology
        with col1b:
            list_to_choose = sorted(st.session_state["g_ontology_components_tag_dict"].values())
            if len(list_to_choose) > 1:
                list_to_choose.insert(0, "No filter")
            ontology_filter_for_lens_tag = st.selectbox("🧩 Filter by ontology (opt):",
                list_to_choose, key="key_ontology_filter_for_lens_property")

        if ontology_filter_for_lens_tag == "No filter":
            ontology_filter_for_lens = st.session_state["g_ontology"]
        else:
            for ont_label, ont_tag in st.session_state["g_ontology_components_tag_dict"].items():
                if ont_tag == ontology_filter_for_lens_tag:
                    ontology_filter_for_lens = st.session_state["g_ontology_components_dict"][ont_label]
                    break

        # Filter by superproperty
        superproperty_dict = utils.get_ontology_property_dict(ontology_filter_for_lens, superproperty=True)
        with col1c:
            list_to_choose = sorted(superproperty_dict.keys())
            list_to_choose.insert(0, "No filter")
            superproperty_filter_for_lens_label = st.selectbox("📡 Filter by superproperty (opt):", list_to_choose,
                key="key_superproperty")   #superproperty label
        if superproperty_filter_for_lens_label != "No filter":   # a superproperty has been selected (filter)
            superproperty_filter_for_lens = superproperty_dict[superproperty_filter_for_lens_label] # get the superproperty iri
        else:
            superproperty_filter_for_lens = None

        with col1:
            st.markdown("<hr style='margin-top:6px; margin-bottom:6 px; border:0; border-top:1px solid #ddd;'>",
                unsafe_allow_html=True)

        # STATS
        if selected_property_search == "📊 Stats":

            with col2b:
                st.markdown(f"""<div class="info-message-gray">
                        <small>🧮 A property is considered <b>used</b> if it appears in at least one rule (as a predicate).
                        <b>Property frequency</b> is the number of times a property is used in a rule.</small>
                    </div>""", unsafe_allow_html=True)

            with col1:
                col1a, col1b, col1c, col1d, col1e = st.columns([1,1,1,0.1,1])
            with col1a:
                utils.get_used_ontology_terms_metric(ontology_filter_for_lens, superfilter=superproperty_filter_for_lens)
            with col1b:
                utils.get_average_ontology_term_frequency_metric(ontology_filter_for_lens, superfilter=superproperty_filter_for_lens)
            with col1c:
                utils.get_average_ontology_term_frequency_metric(ontology_filter_for_lens, superfilter=superproperty_filter_for_lens, type="all")
            with col1e:
                utils.get_filter_info_message_for_lens(ontology_filter_for_lens_tag, superproperty_filter_for_lens_label)

            with col1:
                col1a, col1b = st.columns([1,2])
            with col1a:
                utils.get_used_ontology_terms_donut_chart(ontology_filter_for_lens, superfilter=superproperty_filter_for_lens)

            ontology_used_properties_count_dict = utils.get_property_dictionaries_filtered_by_superproperty(ontology_filter_for_lens, superproperty_filter=superproperty_filter_for_lens)[2]
            list_to_choose = list(ontology_used_properties_count_dict.keys())
            if list_to_choose:
                with col1b:
                    selected_properties = st.multiselect("🖱️ Select ontology properties to display (optional):", list_to_choose,
                        key="key_selected_properties")
                    utils.get_ontology_term_frequency_bar_plot(ontology_filter_for_lens, selected_properties, superfilter=superproperty_filter_for_lens)

        # INFO TABLE
        if selected_property_search == "ℹ️ Info table":

            with col1:
                col1a, col1b = st.columns([2,1])

            with col1b:
                utils.get_filter_info_message_for_lens(ontology_filter_for_lens_tag, utils.get_node_label(superproperty_filter_for_lens))

            filtered_ontology_used_properties_count_dict = utils.get_property_dictionaries_filtered_by_superproperty(ontology_filter_for_lens,
                superproperty_filter=superproperty_filter_for_lens)[2]
            filtered_ontology_property_dict =utils.get_property_dictionaries_filtered_by_superproperty(ontology_filter_for_lens,
                superproperty_filter=superproperty_filter_for_lens)[0]
            with col1a:
                list_to_choose = sorted(filtered_ontology_property_dict.keys())
                selected_properties_for_lens = st.multiselect("🖱️ Select ontology properties to display (optional):", list_to_choose,
                    key="key_selected_properties_for_lens")
                selected_properties_for_lens = sorted(filtered_ontology_property_dict.keys()) if not selected_properties_for_lens else selected_properties_for_lens

            rows = []
            for prop_label in selected_properties_for_lens:
                is_used = prop_label in filtered_ontology_used_properties_count_dict   # boolean
                count = filtered_ontology_used_properties_count_dict.get(prop_label, 0)
                ont_tag = "Other"
                for ont_label, g_ont in st.session_state["g_ontology_components_dict"].items():
                    property_dict = utils.get_ontology_property_dict(g_ont)
                    if prop_label in property_dict:
                        ont_tag = st.session_state["g_ontology_components_tag_dict"][ont_label]
                        break
                rows.append({"Property": prop_label, "Used": is_used,
                    "#Rules": count, "Ontology": ont_tag})

            df = pd.DataFrame(rows)
            df = df.sort_values(by="#Rules", ascending=False)
            with col1:
                if not df.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>🔗 PROPERTIES ({len(df)}):</b>
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ No results.
                    </div>""", unsafe_allow_html=True)

        # RULES
        if selected_property_search == "📐Rules":

            with col1:
                col1a, col1b = st.columns([2,1])

            with col1b:
                utils.get_filter_info_message_for_lens(ontology_filter_for_lens_tag, utils.get_node_label(superproperty_filter_for_lens))

            # Property selection
            filtered_ontology_used_property_dict = utils.get_property_dictionaries_filtered_by_superproperty(ontology_filter_for_lens,
                superproperty_filter=superproperty_filter_for_lens)[0]
            list_to_choose = sorted(filtered_ontology_used_property_dict)
            list_to_choose.insert(0, "Select property")
            with col1a:
                selected_property = st.selectbox("🖱️ Select property:*", list_to_choose,
                    key="key_selected_property")   #property label

            if selected_property != "Select property":
                selected_property_iri = filtered_ontology_used_property_dict[selected_property] # get the superproperty iri

                rule_list_for_property = []   # get all rules that use the selected property as predicate
                for sm in st.session_state["g_mapping"].objects(None, RML["subjectMap"]):
                    sm_rule_list = utils.get_rules_for_sm(sm)
                    for rule in sm_rule_list:
                        if rule[1] == utils.get_node_label(selected_property_iri):
                            rule_list_for_property.append(rule)

                # Display
                with col1:
                    utils.display_rule_list(rule_list_for_property)

#_______________________________________________________________________________
# PANEL: EXTERNAL TERMS
with tab4:
    col1, col2, col2a, col2b = utils.get_panel_layout(narrow=True)
    with col2b:
        utils.get_corner_status_message(mapping_info=True, ontology_info=True)

    if not st.session_state["g_ontology"]:
        with col1:
            utils.get_missing_element_error_message(ontology=True, different_page=True)

    else:
        #PURPLE HEADING: EXTERNAL TERMS-----------------------------------------
        with col1:
            st.markdown("""<div class="purple-heading">
                    📤 External Terms
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a, col1b, col1c = st.columns(3)

        with col1a:
            list_to_choose = ["ℹ️ Info table", "📐Rules"]
            selected_external_term_search = st.radio("🖱️ Select an option:*", list_to_choose,
                label_visibility="collapsed", key="key_external_terms_search")

        with col1b:
            list_to_choose = ["No filter", "🏷️ Classes", "🔗 Properties"]
            external_terms_type = st.selectbox("📡 Filter by type (optional)", list_to_choose,
                key="key_external_terms_type")

        # Dictionaries for external classes
        external_classes_dict = {}
        for s, p, o in st.session_state["g_mapping"].triples((None, RML["class"], None)):
            if isinstance(o, URIRef) and not utils.identify_term_ontology(utils.get_node_label(o)):
                external_classes_dict[utils.get_node_label(o)] = o

        usage_count_dict_classes = {}
        for class_label, class_iri in external_classes_dict.items():
            for s, p, o in st.session_state["g_mapping"].triples((None, RML["class"], URIRef(class_iri))):
                sm_iri = s
                sm_iri_rule_list = utils.get_rules_for_sm(sm_iri)
                if sm_iri_rule_list:
                    usage_count_dict_classes[class_label] = len(sm_iri_rule_list)

        # Dictionaries for external properties
        external_properties_dict = {}
        for s, p, o in st.session_state["g_mapping"].triples((None, RML["predicate"], None)):
            if isinstance(o, URIRef) and not utils.identify_term_ontology(utils.get_node_label(o)):
                external_properties_dict[utils.get_node_label(o)] = o

        usage_count_dict_properties = defaultdict(int)
        for prop_label, prop_iri in external_properties_dict.items():
            for triple in st.session_state["g_mapping"].triples((None, RML["predicate"], URIRef(prop_iri))):
                usage_count_dict_properties[prop_label] += 1

        # Joined dictionaries
        usage_count_dict = usage_count_dict_classes | usage_count_dict_properties
        joined_dict = external_classes_dict | external_properties_dict

        # INFO TABLE
        if selected_external_term_search == "ℹ️ Info table":

            # Select external terms
            with col1c:
                if external_terms_type  == "🏷️ Classes":
                    list_to_choose = sorted(external_classes_dict)
                elif external_terms_type  == "🔗 Properties":
                    list_to_choose = sorted(external_properties_dict)
                elif external_terms_type  == "No filter":
                    list_to_choose = sorted(joined_dict)
                selected_external_terms = st.multiselect("🖱️ Select terms (opt):", list_to_choose,
                    key="key_selected_external_terms")

            if not selected_external_terms and external_terms_type == "🏷️ Classes":
                selected_external_terms = list(external_classes_dict)
            elif not selected_external_terms and external_terms_type == "🔗 Properties":
                selected_external_terms = list(external_properties_dict)
            elif not selected_external_terms and external_terms_type == "No filter":
                selected_external_terms = list(joined_dict)

            rows = []
            for term in selected_external_terms:
                count = usage_count_dict.get(term, 0)
                type = "🏷️ Class" if term in external_classes_dict else "🔗 Property"
                origin = "External"
                for custom_term in st.session_state["custom_terms_dict"]:
                    if utils.get_node_label(custom_term) == term:
                        origin = "Custom"
                rows.append({"Term": term, "Type": type, "#Rules": count, "Origin": origin})

            df = pd.DataFrame(rows)
            df = df.sort_values(by="#Rules", ascending=False)
            with col1:
                if not df.empty:
                    st.markdown(f"""<div class="info-message-blue">
                        <b>📤 EXTERNAL TERMS ({len(df)}):</b>
                    </div>""", unsafe_allow_html=True)
                    st.dataframe(df, hide_index=True)
                else:
                    st.markdown(f"""<div class="warning-message">
                        ⚠️ No results.
                    </div>""", unsafe_allow_html=True)

        # RULES
        if selected_external_term_search == "📐Rules":
            # Select external term
            with col1c:
                if external_terms_type  == "🏷️ Classes":
                    list_to_choose = sorted(external_classes_dict)
                elif external_terms_type  == "🔗 Properties":
                    list_to_choose = sorted(external_properties_dict)
                elif external_terms_type  == "No filter":
                    list_to_choose = sorted(external_classes_dict | external_properties_dict)
                selected_external_term = st.selectbox("🖱️ Select term:*", list_to_choose,
                    key="key_selected_external_terms")

            selected_external_term_iri = joined_dict[selected_external_term ] # get the term iri

            # Get all rules that use the selected term as a class
            rule_list_for_class = []    # get all rules that use the selected class
            for s in st.session_state["g_mapping"].subjects(RML["class"], URIRef(selected_external_term_iri)):
                sm_rule_list = utils.get_rules_for_sm(s)
                for rule in sm_rule_list:
                    rule_list_for_class.append(rule)

            # Get all rules that use the selected term as predicate
            rule_list_for_property = []
            for sm in st.session_state["g_mapping"].objects(None, RML["subjectMap"]):
                sm_rule_list = utils.get_rules_for_sm(sm)
                for rule in sm_rule_list:
                    if rule[1] == utils.get_node_label(selected_external_term_iri):
                        rule_list_for_property.append(rule)

            # Display
            with col1:
                if rule_list_for_class:
                    st.markdown(f"""<div class="info-message-gray">
                            🏷️ Term used as <b>class</b>:
                        </div>""", unsafe_allow_html=True)
                    utils.display_rule_list(rule_list_for_class)
                if rule_list_for_property:
                    st.markdown(f"""<div class="info-message-gray">
                            🔗 Term used as <b>property</b>:
                        </div>""", unsafe_allow_html=True)
                    utils.display_rule_list(rule_list_for_property)
                if not rule_list_for_class and not rule_list_for_property:
                    utils.display_rule_list(rule_list_for_class)   # No results (should not happen)

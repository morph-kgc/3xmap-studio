import streamlit as st
import os
import utils
import pandas as pd
import pickle
from rdflib import Graph, URIRef, Literal, Namespace, BNode
from rdflib.namespace import split_uri
from rdflib.namespace import RDF, RDFS, DC, DCTERMS, OWL, XSD
import time   # for success messages
import re
import uuid   # to handle uploader keys
import io
from io import IOBase
from streamlit_js_eval import streamlit_js_eval

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
header_html = utils.render_header(title="Ontologies",
    description="Import <b>ontologies</b> from link or file.",
    dark_mode=dark_mode)
st.markdown(header_html, unsafe_allow_html=True)

# Import style-----------------------------
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
if not "last_added_ns_list" in st.session_state:
    st.session_state["last_added_ns_list"] = []

# TAB1
if "g_ontology" not in st.session_state:
    st.session_state["g_ontology"] = Graph()
if "g_ontology_label" not in st.session_state:
    st.session_state["g_ontology_label"] = ""
if "g_ontology_loaded_ok_flag" not in st.session_state:
    st.session_state["g_ontology_loaded_ok_flag"] = False
if "ontology_link" not in st.session_state:
    st.session_state["ontology_link"] = ""
if "key_ontology_uploader" not in st.session_state:
    st.session_state["key_ontology_uploader"] = None
if "ontology_file" not in st.session_state:
    st.session_state["ontology_file"] = None
if "g_ontology_from_file_candidate" not in st.session_state:
    st.session_state["g_ontology_from_file_candidate"] = Graph()
if "g_ontology_from_link_candidate" not in st.session_state:
    st.session_state["g_ontology_from_link_candidate"] = Graph()
if "g_ontology_components_dict" not in st.session_state:
    st.session_state["g_ontology_components_dict"] = {}
if "g_ontology_reduced_ok_flag" not in st.session_state:
    st.session_state["g_ontology_reduced_ok_flag"] = False


# Namespaces-----------------------------------
QL, RML, RR = utils.get_required_ns_dict().values()


# Define on_click functions-------------------------------------------------

# TAB1
def load_ontology_from_link():  #HEREIGONS
    # load ontology
    st.session_state["g_ontology"] = st.session_state["g_ontology_from_link_candidate"]  # consolidate ontology graph
    st.session_state["g_ontology_label"] = utils.get_ontology_human_readable_name(st.session_state["g_ontology"], source_link=st.session_state["key_ontology_link"])
    # bind ontology namespaces
    ontology_ns_dict = utils.get_ontology_ns_dict()
    for prefix, namespace in ontology_ns_dict.items():
        utils.bind_namespace_wo_overwriting(prefix, namespace)
    # store information___________________________
    st.session_state["g_ontology_loaded_ok_flag"] = True
    st.session_state["g_ontology_components_dict"][st.session_state["g_ontology_label"]] = st.session_state["g_ontology"]
    # reset fields___________________________
    st.session_state["key_ontology_link"] = ""
    st.session_state["ontology_link"] = ""

def load_ontology_from_file():
    # load ontology
    st.session_state["g_ontology"] = st.session_state["g_ontology_from_file_candidate"]  # consolidate ontology graph
    st.session_state["g_ontology_label"] = utils.get_ontology_human_readable_name(st.session_state["g_ontology"], source_file=st.session_state["ontology_file"])
    # bind ontology namespaces
    ontology_ns_dict = utils.get_ontology_ns_dict()
    for prefix, namespace in ontology_ns_dict.items():
        utils.bind_namespace_wo_overwriting(prefix, namespace)
    # store information___________________________
    st.session_state["g_ontology_loaded_ok_flag"] = True
    st.session_state["g_ontology_components_dict"][st.session_state["g_ontology_label"]]=st.session_state["g_ontology"]
    # reset fields___________________________
    st.session_state["key_ontology_uploader"] = str(uuid.uuid4())
    st.session_state["ontology_file"] = None

def extend_ontology_from_link():
    # load ontology
    g_ontology_new_part = st.session_state["g_ontology_from_link_candidate"]
    g_ontology_new_part_label = utils.get_ontology_human_readable_name(g_ontology_new_part, source_link=st.session_state["key_ontology_link"])
    #store information___________________________
    st.session_state["g_ontology_loaded_ok_flag"] = True
    st.session_state["g_ontology_components_dict"][g_ontology_new_part_label] = g_ontology_new_part
    # bind ontology namespaces
    ontology_ns_dict = utils.get_ontology_component_ns_dict(g_ontology_new_part)
    for prefix, namespace in ontology_ns_dict.items():
        utils.bind_namespace_wo_overwriting(prefix, namespace)
    # merge ontologies components___________________
    st.session_state["g_ontology"] = Graph()
    for ont_label, ont in st.session_state["g_ontology_components_dict"].items():
        st.session_state["g_ontology"] += ont  # merge the graphs using RDFLib's += operator
        for prefix, namespace in utils.get_ontology_component_ns_dict(ont).items():
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
    # bind ontology namespaces
    ontology_ns_dict = utils.get_ontology_component_ns_dict(g_ontology_new_part)
    for prefix, namespace in ontology_ns_dict.items():
        utils.bind_namespace_wo_overwriting(prefix, namespace)
    # merge ontologies components___________________
    st.session_state["g_ontology"] = Graph()
    for ont_label, ont in st.session_state["g_ontology_components_dict"].items():
        st.session_state["g_ontology"] += ont  # merge the graphs using RDFLib's += operator
        for prefix, namespace in utils.get_ontology_component_ns_dict(ont).items():
            st.session_state["g_ontology"].bind(prefix, namespace)
    # reset fields___________________________
    st.session_state["key_ontology_uploader"] = str(uuid.uuid4())
    st.session_state["ontology_file"] = None
    st.session_state["key_extend_ontology_selected_option"] = "📁 File"

def reduce_ontology():
    #store information___________________________
    st.session_state["g_ontology_reduced_ok_flag"] = True
    # drop the given ontology components from the dictionary_______________________
    st.session_state["g_ontology_components_dict"] = {label: ont for label, ont in st.session_state["g_ontology_components_dict"].items() if label not in ontologies_to_drop_list}
    # merge remaining ontology components_______________________________
    st.session_state["g_ontology"] = Graph()
    for label, ont in st.session_state["g_ontology_components_dict"].items():
        st.session_state["g_ontology"] += ont
        for prefix, namespace in ont.namespaces():
            st.session_state["g_ontology"].bind(prefix, namespace)

#____________________________________________________________
# PANELS OF THE PAGE (tabs)

tab1, tab2, tab3 = st.tabs(["Import Ontology", "Explore Ontology", "View Ontology"])

#________________________________________________
# PANEL: "IMPORT ONTOLOGY"
with tab1:

    col1, col2 = st.columns([2,1.5])

    if st.session_state["g_ontology_loaded_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>ontology</b> has been imported!
            </div>""", unsafe_allow_html=True)
        st.session_state["g_ontology_loaded_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    if st.session_state["g_ontology_reduced_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="success-message-flag">
                ✅ The <b>ontology/ies</b> have been removed!
            </div>""", unsafe_allow_html=True)
        st.session_state["g_ontology_reduced_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()


    with col2:
        col2a,col2b = st.columns([1,2])
        with col2b:
            st.write("")
            st.write("")
            utils.get_corner_status_message_ontology()

    with col2:
        col2a,col2b = st.columns([2,1.5])
    with col2b:
        st.write("")
        st.markdown("""<div class="info-message-blue">
        🐢 Certain options in this panel can be a bit slow. <small> Some patience may be required.</small>
            </div>""", unsafe_allow_html=True)

    #LOAD ONTOLOGY FROM URL___________________________________
    if not st.session_state["g_ontology"]:   #no ontology is loaded yet
        with col1:
            st.write("")
            st.write("")
            st.markdown("""<div class="purple-heading">
                    ➕ Add New Ontology
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a,col1b = st.columns([2,1])

        with col1b:
            import_ontology_selected_option = st.radio("🖱️ Import ontology from:*", ["🌐 URL", "📁 File"],
                horizontal=True, key="key_import_ontology_selected_option")

        if import_ontology_selected_option == "🌐 URL":

            with col1a:
                ontology_link = st.text_input("⌨️ Enter link to ontology:*", key="key_ontology_link")
            st.session_state["ontology_link"] = ontology_link if ontology_link else ""

            if ontology_link:

                #http://purl.org/ontology/bibo/
                #http://xmlns.com/foaf/0.1/

                g_candidate, fmt_candidate = utils.parse_ontology(st.session_state["ontology_link"])
                st.session_state["g_ontology_from_link_candidate"] = g_candidate
                st.session_state["g_ontology_from_link_candidate_fmt"] = fmt_candidate
                st.session_state["g_ontology_from_link_candidate_label"] = utils.get_ontology_human_readable_name(st.session_state["g_ontology_from_link_candidate"], source_link=st.session_state["ontology_link"])

                if not utils.is_valid_ontology(g_candidate):
                    with col1a:
                        st.markdown(f"""<div class="error-message">
                            ❌ URL <b>does not</b> link to a valid ontology.
                        </div>""", unsafe_allow_html=True)
                        st.write("")

                else:
                    with col1:
                        col1a, col1b = st.columns(2)

                    with col1b:
                        st.markdown(f"""<div class="success-message">
                                ✔️ <b>Valid ontology:</b> <b style="color:#F63366;">
                                {st.session_state["g_ontology_from_link_candidate_label"]}</b>
                                <small>(parsed successfully with format
                                <b>{st.session_state["g_ontology_from_link_candidate_fmt"]}</b>).</small>
                            </div>""", unsafe_allow_html=True)

                    ontology_ns_dict = utils.get_ontology_component_ns_dict(st.session_state["g_ontology_from_link_candidate"])
                    mapping_ns_dict = utils.get_mapping_ns_dict()
                    already_used_prefix_list = []
                    already_bound_ns_list = []
                    for pr, ns in ontology_ns_dict.items():
                        if ns in mapping_ns_dict.values() and (pr not in mapping_ns_dict or mapping_ns_dict[pr] != ns):
                            already_bound_ns_list.append(ns)
                        elif pr in mapping_ns_dict and str(ns) != mapping_ns_dict[pr]:
                            already_used_prefix_list.append(pr)

                    if already_used_prefix_list and already_bound_ns_list:
                        with col1a:
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ <small><b>Some prefixes ({len(already_used_prefix_list)}) are already in use</b>
                                (or reserved) and will be auto-renamed.
                                <b>Some namespaces ({len(already_bound_ns_list)}) are already bound</b>
                                (or reserved) to other prefixes and will be ignored.</small>
                            </div>""", unsafe_allow_html=True)
                    elif already_used_prefix_list:
                        with col1a:
                            st.markdown(f"""<div class="warning-message">
                                ⚠️ <b>Some prefixes ({len(already_used_prefix_list)}) are already in use</b>
                                <small>(or reserved) and will be auto-renamed with a numeric suffix.</small><br>
                            </div>""", unsafe_allow_html=True)
                    elif already_bound_ns_list:
                        with col1a:
                            st.markdown(f"""<div class="warning-message">
                                <b>Some namespaces ({len(already_bound_ns_list)}) are already bound</b>
                                <small>to other prefixes (or reserved) and will be ignored.</small>
                            </div>""", unsafe_allow_html=True)




                    with col1a:
                        st.button("Add", key="key_load_ontology_from_link_button", on_click=load_ontology_from_link)

        elif import_ontology_selected_option == "📁 File":

            ontology_extension_dict = utils.get_g_ontology_file_formats_dict()   #ontology allowed formats
            ontology_format_list = list(ontology_extension_dict)

            with col1a:
                st.session_state["ontology_file"] = st.file_uploader(f"""🖱️
                    Upload ontology file:*""", type=ontology_format_list, key=st.session_state["key_ontology_uploader"])

            if st.session_state["ontology_file"]:

                g_candidate, fmt_candidate = utils.parse_ontology(st.session_state["ontology_file"])
                st.session_state["g_ontology_from_file_candidate"] = g_candidate
                st.session_state["g_ontology_from_file_candidate_fmt"] = fmt_candidate
                st.session_state["g_ontology_from_file_candidate_label"] = utils.get_ontology_human_readable_name(st.session_state["g_ontology_from_file_candidate"], source_file=st.session_state["ontology_file"])


                if not utils.is_valid_ontology(g_candidate):
                    with col1b:
                        st.markdown(f"""<div class="error-message">
                            ❌ File <b>does not</b> contain a valid ontology.
                        </div>""", unsafe_allow_html=True)
                        st.write("")

                else:
                    with col1b:
                        st.markdown(f"""<div class="success-message">
                                ✔️ <b>Valid ontology:</b> <b style="color:#F63366;">
                                {st.session_state["g_ontology_from_file_candidate_label"]}</b>
                                <small>(parsed successfully with format
                                <b>{st.session_state["g_ontology_from_file_candidate_fmt"]}</b>).</small>
                            </div>""", unsafe_allow_html=True)

                    with col1a:
                        st.button("Add", key="key_load_ontology_from_file_button", on_click=load_ontology_from_file)


    #EXTEND ONTOLOGY___________________________________
    if st.session_state["g_ontology"]:   #ontology loaded
        with col1:
            st.write("")
            st.write("")
            st.markdown("""<div class="purple-heading">
                    ➕ Add New Ontology
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a,col1b = st.columns([2,1])
        with col1b:
            extend_ontology_selected_option = st.radio("🖱️ Import ontology from:*", ["🌐 URL", "📁 File"], horizontal=True, key="key_extend_ontology_selected_option")

        if extend_ontology_selected_option == "🌐 URL":
            with col1a:
                ontology_link = st.text_input("⌨️ Enter link to ontology:*", key="key_ontology_link")
            st.session_state["ontology_link"] = ontology_link if ontology_link else ""

            if ontology_link:

                g_candidate, fmt_candidate = utils.parse_ontology(st.session_state["ontology_link"])
                st.session_state["g_ontology_from_link_candidate"] = g_candidate
                st.session_state["g_ontology_from_link_candidate_fmt"] = fmt_candidate
                st.session_state["g_ontology_from_link_candidate_label"] = utils.get_ontology_human_readable_name(st.session_state["g_ontology_from_link_candidate"], source_link=st.session_state["ontology_link"])

                if not utils.is_valid_ontology(g_candidate):
                    with col1a:
                        st.markdown(f"""<div class="error-message">
                            ❌ URL <b>does not</b> link to a valid ontology.
                        </div>""", unsafe_allow_html=True)

                elif st.session_state["g_ontology_from_link_candidate_label"] in st.session_state["g_ontology_components_dict"]:
                    with col1a:
                        st.markdown(f"""<div class="error-message">
                                ❌ The ontology <b>
                                {st.session_state["g_ontology_from_link_candidate_label"]}</b>
                                has been already imported.
                            </div>""", unsafe_allow_html=True)

                else:
                    with col1:
                        col1a, col1b, col1c = st.columns([1,1.8,1.8])
                    with col1a:
                        st.button("Add", key="key_extend_ontology_from_link_button", on_click=extend_ontology_from_link)
                    with col1c:
                        st.markdown(f"""<div class="success-message">
                                ✔️ <b>Valid ontology:</b> <b style="color:#F63366;">
                                {st.session_state["g_ontology_from_link_candidate_label"]}</b>
                                <small>(parsed successfully with format
                                <b>{st.session_state["g_ontology_from_link_candidate_fmt"]}</b>).</small>
                            </div>""", unsafe_allow_html=True)

                    if utils.check_ontology_overlap(st.session_state["g_ontology_from_link_candidate"], st.session_state["g_ontology"]):
                        with col1b:
                            st.markdown(f"""<div class="warning-message">
                                    ⚠️ <b>Ontologies overlap</b>. <small>Check them
                                    externally to make sure they are aligned and compatible.</small>
                                </div>""", unsafe_allow_html=True)



        if extend_ontology_selected_option == "📁 File":

            ontology_extension_dict = utils.get_g_ontology_file_formats_dict()   #ontology allowed formats
            ontology_format_list = list(ontology_extension_dict)

            with col1a:
                st.session_state["ontology_file"] = st.file_uploader(f"""🖱️
                    Upload ontology file:*""", type=ontology_format_list, key=st.session_state["key_ontology_uploader"])

            if st.session_state["ontology_file"]:

                g_candidate, fmt_candidate = utils.parse_ontology(st.session_state["ontology_file"])
                st.session_state["g_ontology_from_file_candidate"] = g_candidate
                st.session_state["g_ontology_from_file_candidate_fmt"] = fmt_candidate
                st.session_state["g_ontology_from_file_candidate_label"] = utils.get_ontology_human_readable_name(st.session_state["g_ontology_from_file_candidate"], source_file=st.session_state["ontology_file"])

                if not utils.is_valid_ontology(g_candidate):
                    with col1b:
                        st.markdown(f"""<div class="error-message">
                            ❌ File <b>does not</b> contain a valid ontology.
                        </div>""", unsafe_allow_html=True)

                elif st.session_state["g_ontology_from_file_candidate_label"] in st.session_state["g_ontology_components_dict"]:
                    with col1b:
                        st.markdown(f"""<div class="error-message">
                                ❌ The ontology <b>
                                {st.session_state["g_ontology_from_file_candidate_label"]}</b>
                                has been already imported.
                            </div>""", unsafe_allow_html=True)

                else:
                    with col1a:
                        st.button("Add", key="key_extend_ontology_from_file_button", on_click=extend_ontology_from_file)
                    with col1b:
                        st.markdown(f"""<div class="success-message">
                                ✔️ <b>Valid ontology:</b> <b style="color:#F63366;">
                                {st.session_state["g_ontology_from_file_candidate_label"]}</b><br>
                                <small>(parsed successfully with format
                                <b>{st.session_state["g_ontology_from_file_candidate_fmt"]}</b>).</small>
                            </div>""", unsafe_allow_html=True)

                    if utils.check_ontology_overlap(st.session_state["g_ontology_from_file_candidate"], st.session_state["g_ontology"]):
                        with col1b:
                            st.markdown(f"""<div class="warning-message">
                                    ⚠️ <b>Ontologies overlap</b>. <small>Check them
                                    externally to make sure they are aligned and compatible.</small>
                                </div>""", unsafe_allow_html=True)
                            st.write("")

        with col1:
            st.write("________")

    #DISCARD ONTOLOGY___________________________________
    if st.session_state["g_ontology"]:   #ontology loaded and more than 1 component
        with col1:
            st.markdown("""<div class="purple-heading">
                    🗑️ Remove Ontology
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            list_to_choose = []
            for ont_label in st.session_state["g_ontology_components_dict"]:
                list_to_choose.insert(0, utils.get_ontology_tag(ont_label))
            # list_to_choose = list(reversed(list(st.session_state["g_ontology_components_dict"].keys())))
            if len(list_to_choose) > 1:
                list_to_choose.insert(0, "Select all")
            ontologies_to_drop_list_tags = st.multiselect("🖱️ Select ontologies to be dropped:*", list_to_choose,
                key="key_ontologies_to_drop_list")
            ontologies_to_drop_list = []
            for ont_label in st.session_state["g_ontology_components_dict"]:
                if utils.get_ontology_tag(ont_label) in ontologies_to_drop_list_tags:
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

#__________________________________________________
# EXPLORE ONTOLOGY
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
                🔍 Search Ontology
            </div>""", unsafe_allow_html=True)
        st.write("")

    with col1:
        col1a, col1b = st.columns([1.5, 1])

    ontology_searches_list = ["Select search", "Classes", "Properties", "Superclasses", "Custom search"]

    with col1a:
        selected_ontology_search = st.selectbox("🖱️ Select search:*", ontology_searches_list,
            key="key_selected_ontology_search")

    if len(st.session_state["g_ontology_components_dict"]) > 1:
        with col1b:
            list_to_choose = []
            for ont in st.session_state["g_ontology_components_dict"]:
                list_to_choose.append(utils.get_ontology_tag(ont))
            list_to_choose.insert(0, "All ontologies")
            ontology_component_for_search_tag = st.selectbox("🖱️ Select ontology (optional):", list_to_choose,
                key="key_ontology_component_for_search_tag")
        if ontology_component_for_search_tag == "All ontologies":
            ontology_for_search = st.session_state["g_ontology"]
        else:
            for ont in st.session_state["g_ontology_components_dict"]:
                if utils.get_ontology_tag(ont) == ontology_component_for_search_tag:
                    ontology_for_search = st.session_state["g_ontology_components_dict"][ont]

    else:
        ontology_for_search = st.session_state["g_ontology"]

    if selected_ontology_search == "Classes":
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

            query = """PREFIX rr: <http://www.w3.org/ns/r2rml#>
                PREFIX rml: <http://semweb.mmlab.be/ns/rml#>

                SELECT DISTINCT ?tm ?sm ?pom ?om ?subject_value ?predicate ?object_value WHERE {
                  ?tm rr:subjectMap ?sm .
                  ?tm rr:predicateObjectMap ?pom .
                  ?pom rr:predicate ?predicate .
                  ?pom rr:objectMap ?om .

                  OPTIONAL { ?sm rr:template ?subject_value . }
                  OPTIONAL { ?sm rr:constant ?subject_value . }
                  OPTIONAL { ?sm rml:reference ?subject_value . }

                  OPTIONAL { ?om rr:template ?object_value . }
                  OPTIONAL { ?om rr:constant ?object_value . }
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
                sm_label = utils.get_node_label(sm)
                pom_label = utils.get_node_label(pom)
                om_label = utils.get_node_label(om)
                subject_label = utils.get_node_label(subject)
                predicate_label = utils.get_node_label(predicate)
                object_label = utils.get_node_label(object_)

                selected_tm_for_display_list = list(tm_dict) if not selected_tm_for_display_list else selected_tm_for_display_list
                if tm_label in selected_tm_for_display_list:
                    row_dict = {
                        "Subject": subject_label,
                        "Predicate": predicate_label,
                        "Object": object_label,
                        "TriplesMap": tm_label,
                        "SubjectMap": sm_label,
                        "PredicateObjectMap": pom_label,
                        "ObjectMap": om_label
                    }
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

    if selected_ontology_search == "Custom search":
        with col1a:
            query = st.text_area("⌨️ Enter query:*")

        if query:
            try:
                results = ontology_for_search.query(query)
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
# VIEW ONTOLOGY
with tab3:
    st.write("")
    st.write("")

    col1, col2 = st.columns([2,1])

    with col2:
        col2a,col2b = st.columns([1,2])
    with col2b:
        utils.get_corner_status_message_ontology()

    #PURPLE HEADING - PREVIEW
    with col1:
        st.markdown("""<div class="purple-heading">
                🔍 View Ontologies
            </div>""", unsafe_allow_html=True)
        st.write("")

    if not st.session_state["g_ontology_components_dict"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.markdown(f"""<div class="error-message">
                ❌ You need to import at least one ontology in the <b>Import Ontology</b> pannel.
            </div>""", unsafe_allow_html=True)
    else:
        with col1:
            col1a, col1b = st.columns(2)
        with col1a:
            format_options_dict = {"🐢 turtle": "turtle", "3️⃣ ntriples": "nt",
                "📐 trig": "trig"}
            preview_format_display = st.radio("🖱️ Select format:*", format_options_dict,
                horizontal=True, key="key_export_format_selectbox")
            preview_format = format_options_dict[preview_format_display]
        if len(st.session_state["g_ontology_components_dict"]) > 1:
            with col1b:
                list_to_choose = []
                for ont in st.session_state["g_ontology_components_dict"]:
                    list_to_choose.append(utils.get_ontology_tag(ont))
                list_to_choose.insert(0, "All ontologies")
                ontology_component_for_preview_tag = st.selectbox("🖱️ Select ontology (optional):", list_to_choose,
                    key="key_ontology_component_for_preview_tag")
            if ontology_component_for_preview_tag == "All ontologies":
                ontology_for_preview = st.session_state["g_ontology"]
            else:
                for ont in st.session_state["g_ontology_components_dict"]:
                    if utils.get_ontology_tag(ont) == ontology_component_for_preview_tag:
                        ontology_for_preview = st.session_state["g_ontology_components_dict"][ont]

        else:
            ontology_for_preview = st.session_state["g_ontology"]

        serialised_data = ontology_for_preview.serialize(format=preview_format)
        max_length = 100000
        st.code(serialised_data[:max_length])

        if len(serialised_data) > max_length:
            with col2b:
                if len(serialised_data) < 10**6:
                    len_for_display = f"{int(len(serialised_data) / 1000)}k"
                elif len(serialised_data) < 10*10**6:
                    len_for_display = f"{round(len(serialised_data) / 10**6, 1)}M"
                else:
                    len_for_display = f"{round(int(serialised_data)/ 10**6)}M"
                st.markdown(f"""<div class="warning-message">
                    ⚠️ <b>Your ontology is quite large</b>.
                    <small>Showing only the first {int(max_length/1000)}k characters
                    (out of {len_for_display}) to avoid performance issues.</small>
                </div>""", unsafe_allow_html=True)
                st.write("")

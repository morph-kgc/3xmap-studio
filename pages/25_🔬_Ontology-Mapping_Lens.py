import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle
from rdflib.namespace import split_uri
from rdflib.namespace import RDF, RDFS, DC, DCTERMS, OWL, XSD
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

tab1, tab2, tab3 = st.tabs(["Ontology Usage", "Mapping Density", "Domain/Range Validation"])

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

    if not st.session_state["g_ontology"]:
        with col1:
            st.markdown(f"""<div class="error-message">
                ❌ You need to import an ontology from the
                <b>Ontologies</b> page <small>(Import Ontology pannel).</small>
            </div>""", unsafe_allow_html=True)

    else:

        #PURPLE HEADING - ADD NEW TRIPLESMAP
        with col1:
            st.markdown("""<div class="purple-heading">
                    📈 Ontology Usage
                </div>""", unsafe_allow_html=True)
            st.write("")

        with col1:
            col1a, col1b = st.columns(2)

        with col1a:
            list_to_choose = ["🏷️ Classes", "🔗 Properties"]
            type_for_lens = st.radio("🖱️ Select an option:*", list_to_choose,
                horizontal=True, key="key_type_for_lens")

        # Filter by ontology
        if len(st.session_state["g_ontology_components_dict"]) > 1:
            with col1b:
                list_to_choose = sorted(st.session_state["g_ontology_components_tag_dict"].values())
                list_to_choose.insert(0, "Select ontology")
                ontology_filter_for_lens = st.selectbox("🔻 Filter by ontology (optional):",
                    list_to_choose, key="key_ontology_filter_for_lens")

            if ontology_filter_for_lens == "Select ontology":
                ontology_filter_for_lens = st.session_state["g_ontology"]
            else:
                for ont_label, ont_tag in st.session_state["g_ontology_components_tag_dict"].items():
                    if ont_tag == ontology_filter_for_lens:
                        ontology_filter_for_lens = st.session_state["g_ontology_components_dict"][ont_label]
                        break

        else:
            ontology_filter_for_lens = st.session_state["g_ontology"]

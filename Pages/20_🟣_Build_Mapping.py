import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle
from rdflib.namespace import split_uri
from rdflib.namespace import OWL
from rdflib.namespace import RDF, RDFS, DC, DCTERMS
import time



#____________________________________________
#PRELIMINARY
#Aesthetics
utils.import_st_aesthetics()
st.write("")

# Namespaces
namespaces = utils.get_predefined_ns_dict()
RML = namespaces["rml"]
RR = namespaces["rr"]
QL = namespaces["ql"]
MAP = namespaces["map"]
CLASS = namespaces["class"]
LS = namespaces["logicalSource"]
BASE = Namespace(utils.get_rdfolio_base_iri())

#define on_click functions
def reset_input():    #function to reset input upon click
    st.session_state["overwrite_checkbox"] = False
    st.session_state["save_g_filename_flag"] = ""

def save_tmap_new_ls():   #function to save TriplesMap upon click
    if logical_source_label:
        logical_source_iri = LS[f"{logical_source_label}"]
    else:
        logical_source_iri = BNode()
    utils.add_logical_source(st.session_state["g_mapping"], tmap_label, selected_ds, logical_source_iri)
    utils.update_dictionaries()             #to update tmap_dict
    st.session_state["ds_list"] = "Select a data source"      #restart input variables
    st.session_state["tmap_label_input"] = ""
    st.session_state["save_tmap_success"] = True

def save_tmap_existing_ls():   #function to save TriplesMap upon click
    tmap_iri = MAP[f"{tmap_label}"]
    logical_source_iri =  LS[f"{selected_existing_logical_source}"]
    st.session_state["g_mapping"].add((tmap_iri, RML.logicalSource, logical_source_iri))    #bind to logical source
    st.session_state["ds_list"] = "Select a data source"      #restart input variables
    st.session_state["tmap_label_input"] = ""
    st.session_state["save_tmap_success"] = True

def delete_triplesmap():   #function to delete a TriplesMap
    st.session_state["deleted_triples"] = utils.remove_triplesmap(st.session_state["tm_to_remove"])
    st.session_state["tm_to_remove"] = "Select a TriplesMap"
    st.session_state["tmap_deleted_ok"] = True

def delete_labelled_subject_map():   #function to delete a Subject Map
    st.session_state["g_mapping"].remove((sm_to_remove, None, None))
    st.session_state["g_mapping"].remove((None, None, sm_to_remove))
    st.session_state["sm_to_remove"] = "Select a TriplesMap"
    st.session_state["smap_deleted_ok"] = True

def unassign_subject_map():
    st.session_state["g_mapping"].remove((tm_to_unassign_sm_iri, RR.subjectMap, None))
    st.session_state["tm_to_unassign_sm"] = "Select a TriplesMap"

def save_subject_existing():
    st.session_state["g_mapping"].add((tmap_iri_existing, RR.subjectMap, selected_existing_sm_iri))
    st.session_state["subject_saved_ok_existing"] = True
    st.session_state["smap_ordered_list"].insert(0, tmap_iri_existing)
    st.session_state["existing_sm_uncollapse"] = False
    st.session_state["new_sm_uncollapse"] = False


def save_subject_template():   #function to save subject (template option)
    utils.update_dictionaries()
    if not s_label:
        smap_iri = BNode()
    else:
        smap_iri = MAP[s_label]

    st.session_state["g_mapping"].add((tmap_iri, RR.subjectMap, smap_iri))
    st.session_state["g_mapping"].add((smap_iri, RR.template, Literal(f"http://example.org/resource/{{{st.session_state["subject_id_input"]}}}")))
    st.session_state["subject_id"] = "Select a column of the data source:"
    st.session_state["subject_id_input"] = ""
    st.session_state["subject_saved_ok_new"] = True
    st.session_state["subject_label"] = ""
    st.session_state["smap_ordered_list"].insert(0, tmap_iri)
    st.session_state["existing_sm_uncollapse"] = False
    st.session_state["new_sm_uncollapse"] = False


def save_subject_constant():   #function to save subject (template option)
    utils.update_dictionaries()
    if not s_label:
        smap_iri = BNode()
    else:
        smap_iri = MAP[s_label]

    st.session_state["g_mapping"].add((tmap_iri, RR.subjectMap, smap_iri))
    st.session_state["g_mapping"].add((smap_iri, RR.constant, Literal(f"http://example.org/resource/{st.session_state["subject_constant_input"]}")))
    st.session_state["subject_constant"] = ""
    st.session_state["subject_saved_ok_new"] = True
    st.session_state["subject_label"] = ""
    st.session_state["smap_ordered_list"].insert(0, tmap_iri)
    st.session_state["existing_sm_uncollapse"] = False
    st.session_state["new_sm_uncollapse"] = False


def save_subject_reference():   #function to save subject (template option)
    utils.update_dictionaries()
    if not s_label:
        smap_iri = BNode()
    else:
        smap_iri = MAP[s_label]

    st.session_state["g_mapping"].add((tmap_iri, RR.subjectMap, smap_iri))
    st.session_state["g_mapping"].add((smap_iri, RML.reference, Literal(st.session_state["subject_id_input"])))
    st.session_state["subject_id"] = "Select a column of the data source:"
    st.session_state["subject_id_input"] = ""
    st.session_state["subject_saved_ok_new"] = True
    st.session_state["subject_label"] = ""
    st.session_state["smap_ordered_list"].insert(0, tmap_iri)
    st.session_state["existing_sm_uncollapse"] = False
    st.session_state["new_sm_uncollapse"] = False

def save_simple_subject_class():
    st.session_state["g_mapping"].add((selected_subject_bnode, RR["class"], subject_class))

def save_union_class():
    st.session_state["g_mapping"].add((selected_subject_bnode, RR["class"], selected_union_class_BNode))
    st.session_state["selected_union_class_label"] = "Select a union class"

def save_external_subject_class():
    st.session_state["g_mapping"].add((selected_subject_bnode, RR["class"], subject_class))

def delete_subject_class():
    st.session_state["g_mapping"].remove((selected_subject_bnode, RR["class"], None))

def change_to_BNode():
    st.session_state["g_mapping"].remove((selected_subject_bnode, RR["termType"], RR.IRI))
    st.session_state["g_mapping"].add((selected_subject_bnode, RR["termType"], RR.BlankNode))

def change_to_IRI():
    st.session_state["g_mapping"].remove((selected_subject_bnode, RR["termType"], RR.BlankNode))
    st.session_state["g_mapping"].add((selected_subject_bnode, RR["termType"], RR.IRI))

def save_subject_graph():
    st.session_state["g_mapping"].add((selected_subject_bnode, RR["graph"], subject_graph))

def delete_subject_graph():
    st.session_state["g_mapping"].remove((selected_subject_bnode, RR["graph"], None))



#initialise session state variables
if "confirm_button" not in st.session_state:
    st.session_state["confirm_button"] = False
if "custom_ns_dict" not in st.session_state:
    st.session_state["custom_ns_dict"] = {}
if "save_tmap_success" not in st.session_state:
    st.session_state["save_tmap_success"] = False
if "tmap_label" not in st.session_state:
    st.session_state["tmap_label"] = ""
if "selected_ds" not in st.session_state:
    st.session_state["selected_ds"] = None
if "subject_id_input" not in st.session_state:
    st.session_state["subject_id_input"] = ""
if "subject_saved_ok_new" not in st.session_state:
    st.session_state["subject_saved_ok_new"] = False
if "subject_saved_ok_existing" not in st.session_state:
    st.session_state["subject_saved_ok_existing"] = False
if "tmap_ordered_list" not in st.session_state:
    st.session_state["tmap_ordered_list"] = []
if "smap_ordered_list" not in st.session_state:
    st.session_state["smap_ordered_list"] = []
if "deleted_triples" not in st.session_state:
    st.session_state["deleted_triples"] = []
if "tmap_deleted_ok" not in st.session_state:
    st.session_state["tmap_deleted_ok"] = False
if "smap_deleted_ok" not in st.session_state:
    st.session_state["smap_deleted_ok"] = False



col1,col2 = st.columns([2,1.5])
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




#g = Graph() #create empty graph to store triples (this is the mapping we are building)
ds_folder_path = utils.get_ds_folder_path()   #path to folder with data sources HERE DELETE

#___________________________________________

 #_____________________________________________
#SELECT OPTION -> Buttons for namespace, map, subject or predicate-object
col1, col2, col3, col4 = st.columns(4)

if "20_option_button" not in st.session_state:
    st.session_state["20_option_button"] = None

with col1:
    tmap_button = st.button("Add TriplesMap")
if tmap_button:
    st.session_state["20_option_button"] = "map"

with col2:
    s_button = st.button("Add Subject Map", key = "s_button")
if s_button:
    st.session_state["20_option_button"] = "s"

with col3:
    po_button = st.button("Add Predicate-Object Map", key = "po_button")
if po_button:
    st.session_state["20_option_button"] = "po"

with col4:
    save_progress_button = st.button("Save progress", key = "save_progress_button")
if save_progress_button:
    st.session_state["20_option_button"] = "save_progress"

st.write("_______________")
#_____________________________________________



#________________________________________________
#ADD TRIPLESMAP
if st.session_state["20_option_button"] == "map":

    col1,col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
        with col2b:
            st.markdown(f"""
                <div style="background-color:#e6e6fa; padding:1em; border-radius:5px;
                color:#2a0134; border:1px solid #511D66;">
                    <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                    style="vertical-align:middle; margin-right:8px; height:20px;">
                    You are currently working with mapping
                    <b style="color:#007bff;">{st.session_state["g_label"]}</b>.
                </div>
            """, unsafe_allow_html=True)
            st.write("")

            if st.session_state["ontology_label"]:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                            border-radius:5px; color:#155724; border:1px solid #444;">
                    🧩 The ontology
                    <b style="color:#007bff;">{st.session_state["ontology_label"]}</b>
                    is currently loaded.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="background-color:#f0f0f0; padding:10px; border-radius:5px; margin-bottom:8px; border:1px solid #ccc;">
                        <span style="font-size:0.95rem; color:#333;">
                            🚫 <b>No ontology</b> is loaded.<br>
                        </span>
                        <span style="font-size:0.82rem; color:#555;">
                            Working without an ontology could result in structural inconsistencies.
                        </span>
                    </div>
                """, unsafe_allow_html=True)




    #DISPLAY TRIPLESMAP INFO IN A DATAFRAME
    utils.update_dictionaries()
    with col2:    #display the last TriplesMaps in a dataframe
        col2a,col2b = st.columns([0.5,2])
        with col2b:
            st.write("")
            st.write("")
            # tmap_df = pd.DataFrame(list(st.session_state["data_source_dict"].items()), columns=["TriplesMap label", "Data source"]).iloc[::-1]
            tmap_df = utils.build_tmap_df()

            if not tmap_df.empty:
                tmap_df_filtered = tmap_df[tmap_df["TriplesMap Label"].isin(st.session_state["tmap_ordered_list"])].copy()
                tmap_df_filtered["sort_key"] = tmap_df_filtered["TriplesMap Label"].apply(lambda x: st.session_state["tmap_ordered_list"].index(x))
                tmap_df_ordered = tmap_df_filtered.sort_values("sort_key").drop(columns=["sort_key", "TriplesMap IRI"]).reset_index(drop=True)

                # ordered_rows = [(tm_label, st.session_state["data_source_dict"][tm_label]) for tm_label in st.session_state["tmap_ordered_list"]]
                # tmap_df_ordered = pd.DataFrame(ordered_rows, columns=["TriplesMap label", "Data source"])
                tmap_df_last = tmap_df_ordered.head(7)

                st.markdown("""
                    <div style='text-align: right; font-size: 14px; color: grey;'>
                        last added TriplesMaps
                    </div>
                """, unsafe_allow_html=True)
                st.markdown("""
                    <div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        (complete TriplesMap list in 🔎 Show TriplesMaps)
                    </div>
                """, unsafe_allow_html=True)
                st.dataframe(tmap_df_last, hide_index=True)
                st.write("")


    # st.write("HERE2")
    # st.write(utils.get_ontology_base_iri())
    #
    # st.write("HERE", st.session_state["tmap_dict"])
    # derived_triples_list = utils.get_tmap_derived_triples("AuthorsTriplesMap")
    # derived_triples_df = pd.DataFrame(derived_triples_list, columns=["s", "p", "o"])
    # st.dataframe(derived_triples_df)
    #
    # derived_triples_list = utils.get_tmap_exclusive_derived_triples("AuthorsTriplesMap")
    # derived_triples_df = pd.DataFrame(derived_triples_list, columns=["s", "p", "o"])
    # st.write("HERE")
    # st.dataframe(derived_triples_df)



    with col1:
        st.markdown("""
        <div style="background-color:#e6e6fa; border:1px solid #511D66;
                    border-radius:5px; padding:10px; margin-bottom:8px;">
            <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                🧱 Add New TriplesMap
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")

    with col1:
        col1a, col1b = st.columns([2,1])
    with col1a:
        tmap_label = st.text_input("Enter label for the new TriplesMap", key="tmap_label_input")    #user-friendly name for the TriplesMap



    labelled_logical_sources_list = []      #existing labelled logical sources
    for s, p, o in st.session_state["g_mapping"].triples((None, RML.logicalSource, None)):
        if isinstance(o, URIRef):
            labelled_logical_sources_list.append(split_uri(o)[1])

    if tmap_label:   #after a label has been given
        st.session_state["tmap_label"] = tmap_label
        if tmap_label in st.session_state["tmap_dict"]:   #if label is already in use
            with col1a:
                st.markdown(f"""
                <div style="background-color:#f8d7da; padding:1em;
                            border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                    ❌ TriplesMap label <b style="color:#a94442;">{tmap_label}</b> already in use: <br>
                    Please pick a different label.
                </div>
                """, unsafe_allow_html=True)
                st.write("")

        else:    #if label is valid

            with col1:
                st.markdown("""<div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
                    </div>""", unsafe_allow_html=True)
            with col1:
                col1a, col1b = st.columns([2,1])

            with col1b:
                existing_ls_uncollapse = st.toggle("", key="existing_ls_uncollapse")
            with col1a:
                st.markdown("""<span style="font-size:1.1em; font-weight:bold;">📑 Assign an existing Logical Source</span><br>
                        <small>Select an already created logical source from list</small>""",
                    unsafe_allow_html=True)
                st.write("")

                if existing_ls_uncollapse:

                    labelled_logical_sources_list.insert(0, "Select a logical source")

                    if len(labelled_logical_sources_list) == 1:
                        st.markdown(f"""
                            <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                <span style="font-size:0.95rem;">
                                ⚠️ This option is not available. No labelled logical sources exist in mapping {st.session_state["g_label"]} yet.
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        st.write("")

                    else:

                        selected_existing_logical_source = st.selectbox("Select an existing logical source:", labelled_logical_sources_list)
                        st.write("")

                        if selected_existing_logical_source != "Select a logical source":
                            save_tmap_button_existing_ls = st.button("Save TriplesMap", on_click=save_tmap_existing_ls)

            with col1:
                col1a,col1b = st.columns([2,1])
            with col1b:
                new_ls_uncollapse = st.toggle("", key = "new_ls_uncollapse")
            with col1a:
                st.markdown(
                    """
                    <div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
                        <span style="font-size:1.1em; font-weight:bold;">🆕 Assign a new Logical Source</span><br>
                        <small>Create logical source from scratch</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                    )
                st.write("")

            if new_ls_uncollapse:

                ds_allowed_formats = utils.get_ds_allowed_formats()            #data source for the TriplesMap
                ds_list = [f for f in os.listdir(ds_folder_path) if f.endswith(ds_allowed_formats)]
                ds_list.insert(0, "Select a data source") # Add a placeholder option
                with col1a:
                    selected_ds = st.selectbox("Choose a file:", ds_list, key="ds_list")
                    logical_source_label = st.text_input("Enter label for the logical source (optional):")
                    if logical_source_label in labelled_logical_sources_list:
                        with col1a:
                            st.markdown(f"""
                                <div style="background-color:#fff3cd; padding:1em;
                                border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                                    ⚠️ The logical source label <b style="color:#cc9a06;">{logical_source_label}</b>
                                    is already in use and will be ignored. Please, pick a different label.</div>
                            """, unsafe_allow_html=True)
                            st.write("")
                        logical_source_label = ""   #ignore logical source label if it already exists

                if selected_ds != "Select a data source":
                    st.session_state["selected_ds"] = selected_ds
                    with col1a:
                        save_tmap_button_new_ls = st.button("Save TriplesMap", on_click=save_tmap_new_ls)




        # if tmap_label in st.session_state["tmap_dict"]:
        #     with col1a:
        #         st.markdown(f"""
        #         <div style="background-color:#f8d7da; padding:1em;
        #                     border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
        #             ❌ TriplesMap label <b style="color:#a94442;">{tmap_label}</b> already in use: <br>
        #             Please pick a different label.
        #         </div>
        #         """, unsafe_allow_html=True)
        #         st.write("")
        # elif tmap_label and selected_ds != "Select a data source":
        #     with col1a:
        #         save_tmap_button = st.button("Save new TriplesMap", on_click=save_tmap)

    if st.session_state["save_tmap_success"]:
        with col1b:
            st.session_state["save_tmap_success"] = False
            st.write("")
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:1em;
            border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                ✅ You created the TriplesMap <b style="color:#0f5132;">{st.session_state["tmap_label"]}
                </b>, <br>
                associated to the data source <b style="color:#0f5132;"> {st.session_state["selected_ds"]}</b>.  </div>
            """, unsafe_allow_html=True)
            st.write("")
            st.session_state["tmap_ordered_list"].insert(0, st.session_state["tmap_label"])
            time.sleep(2)
            st.rerun()



    with col1:
        st.write("________")
        st.markdown("""
        <div style="background-color:#e6e6fa; border:1px solid #511D66;
                    border-radius:5px; padding:10px; margin-bottom:8px;">
            <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                🗑️ Remove Existing TriplesMap
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")

    with col1:
        col1a, col1b = st.columns([2,1])

    tm_to_remove_list = list(st.session_state["data_source_dict"].keys())
    tm_to_remove_list.insert(0, "Select a TriplesMap")

    if len(tm_to_remove_list) == 1:
        with col1a:
            st.markdown(f"""
            <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                    <span style="font-size:0.95rem;">
                    ⚠️ There are no TriplesMap to remove.
                    </span>
                </div>
                """, unsafe_allow_html=True)
    else:

        with col1a:
            tm_to_remove = st.selectbox("Select a TriplesMap", tm_to_remove_list, key="tm_to_remove")

        if tm_to_remove != "Select a TriplesMap":
            with col1a:
                delete_triplesmap_checkbox = st.checkbox(
                ":gray-badge[⚠️ I am completely sure I want to delete the TriplesMap]",
                key="delete_triplesmap_checkbox")
            if delete_triplesmap_checkbox:
                with col1:
                    col1a, col1b = st.columns([1,2])
                with col1a:
                    st.button("Delete", on_click=delete_triplesmap)


    with col1:
        col1a, col1b = st.columns([2,1])
    if st.session_state["tmap_deleted_ok"]:
        with col1b:
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:1em;
            border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                ✅ The <b style="color:#007bff;">Triplesmap
                </b> has been succesfully deleted!  </div>
            """, unsafe_allow_html=True)
            st.write("")
        with col1a:
            st.markdown(
                """
                <div style='background-color:#f0f0f0; padding:8px; border-radius:4px;'>
                    <b>Deleted triples:</b>
                </div>""", unsafe_allow_html=True)
            for s, p, o in st.session_state["deleted_triples"]:
                if isinstance(s, URIRef):
                    s = split_uri(s)[1]
                elif isinstance(s, BNode):
                    s = ("BNode: " + str(s)[:5] + "...")
                if isinstance(p, URIRef):
                    p = split_uri(p)[1]
                if isinstance(o, URIRef):
                    o = split_uri(o)[1]
                elif isinstance(o, BNode):
                    o = ("BNode: " + str(o)[:5] + "...")
                st.markdown(
                    f"""
                    <div style='background-color:#f0f0f0; padding:6px 10px; border-radius:5px;'>
                        <small>🔹 {s} → {p} → {o}</small>
                    </div>""", unsafe_allow_html=True)
        st.session_state["tmap_deleted_ok"] = False
        time.sleep(5)
        st.rerun()

    with col1a:
        if st.session_state["deleted_triples"] and st.toggle("🔎 Display last removed triples") and not st.session_state["tmap_deleted_ok"]:
            st.markdown(
                """
                <div style='background-color:#f0f0f0; padding:8px; border-radius:4px;'>
                    <b> Last deleted triples:</b>
                </div>""", unsafe_allow_html=True)
            for s, p, o in st.session_state["deleted_triples"]:
                if isinstance(s, URIRef):
                    s = split_uri(s)[1]
                elif isinstance(s, BNode):
                    s = ("BNode: " + str(s)[:5] + "...")
                if isinstance(p, URIRef):
                    p = split_uri(p)[1]
                if isinstance(o, URIRef):
                    o = split_uri(o)[1]
                elif isinstance(o, BNode):
                    o = ("BNode: " + str(o)[:5] + "...")
                st.markdown(
                    f"""
                    <div style='background-color:#f0f0f0; padding:6px 10px; border-radius:5px;'>
                        <small>🔹 {s} → {p} → {o}</small>
                    </div>""", unsafe_allow_html=True)


    with col1:
        st.write("_____")
        st.markdown("""
        <div style="background-color:#e6e6fa; border:1px solid #511D66;
                    border-radius:5px; padding:10px; margin-bottom:8px;">
            <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                🔎 Show TriplesMaps
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")

        with st.expander("ℹ️ Show all TriplesMaps"):
            st.write("")
            st.dataframe(tmap_df.drop(columns=["TriplesMap IRI"]))


#________________________________________________



#________________________________________________
#ADD SUBJECT MAP TO MAP
if st.session_state["20_option_button"] == "s":

    col1,col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
        with col2b:
            st.markdown(f"""
                <div style="background-color:#e6e6fa; padding:1em; border-radius:5px;
                color:#2a0134; border:1px solid #511D66;">
                    <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                    style="vertical-align:middle; margin-right:8px; height:20px;">
                    You are currently working with mapping
                    <b style="color:#007bff;">{st.session_state["g_label"]}</b>.
                </div>
            """, unsafe_allow_html=True)
            st.write("")

            if st.session_state["ontology_label"]:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                            border-radius:5px; color:#155724; border:1px solid #444;">
                    🧩 The ontology
                    <b style="color:#007bff;">{st.session_state["ontology_label"]}</b>
                    is currently loaded.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="background-color:#f0f0f0; padding:10px; border-radius:5px; margin-bottom:8px; border:1px solid #ccc;">
                        <span style="font-size:0.95rem; color:#333;">
                            🚫 <b>No ontology</b> is loaded.<br>
                        </span>
                        <span style="font-size:0.82rem; color:#555;">
                            Working without an ontology could result in structural inconsistencies.
                        </span>
                    </div>
                """, unsafe_allow_html=True)


    #DISPLAY TRIPLESMAP AND SUBJECT INFO IN A DATAFRAME__________________
    utils.update_dictionaries()
    subject_df = utils.build_subject_df()

    if not subject_df.empty:

        subject_df_filtered = subject_df[subject_df["TriplesMap IRI"].isin(st.session_state["smap_ordered_list"])].copy()
        subject_df_filtered["sort_key"] = subject_df_filtered["TriplesMap IRI"].apply(lambda x: st.session_state["smap_ordered_list"].index(x))
        subject_df_ordered = subject_df_filtered.sort_values("sort_key").drop(columns=["sort_key", "TriplesMap IRI", "Data Source"]).reset_index(drop=True)


        with col2:    #display the last Subject Maps in a dataframe
            col2a,col2b = st.columns([0.1,2])
            with col2b:
                st.write("")
                st.write("")
                subject_df_last = subject_df_ordered.head(7)
                st.markdown("""
                    <div style='text-align: right; font-size: 14px; color: grey;'>
                        last added Subject Maps
                    </div>
                """, unsafe_allow_html=True)
                st.markdown("""
                    <div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                        (complete Subject Map list in 🔎 Show Subject Maps)
                    </div>
                """, unsafe_allow_html=True)
                st.dataframe(subject_df_last, hide_index=True)
                st.write("")



#ADD NEW SUBJECT MAP_________________________________________________________
    with col1:
        st.markdown("""
        <div style="background-color:#e6e6fa; border:1px solid #511D66;
                    border-radius:5px; padding:10px; margin-bottom:8px;">
            <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                🧱 Add New Subject Map
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")

        col1a, col1b = st.columns([2,1])


    #SELECT THE TRIPLESMAP TO WHICH THE SUBJECT MAP WILL BE ADDED___________________________
    #only triplesmaps without subject can be selected
    tmap_list = list(st.session_state["tmap_dict"].values())
    tmap_without_subject_list = []          #list of all TriplesMap which do not have a subject yet
    for tmap_label, tmap_iri in st.session_state["tmap_dict"].items():
        if not next(st.session_state["g_mapping"].objects(tmap_iri, RR.subjectMap), None):   #if there is no subject for that TriplesMap
            tmap_without_subject_list.append(tmap_label)
    tmap_without_subject_list.insert(0, "Select a TriplesMap")


    if not st.session_state["tmap_dict"]:
        with col1a:
            st.markdown(f"""
                <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                ⚠️ No TriplesMaps in mapping {st.session_state["g_label"]}.<br>
                You can add new TriplesMaps in the <b style="color:#cc9a06;">Add TriplesMap option</b>.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            st.write("")

    elif len(tmap_without_subject_list) == 1:
        with col1a:
            st.markdown(
                f"""
                <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                🔒 <b>All existing TriplesMaps have already been assigned a subject map.</b><br>
                <ul style="margin-top:0.5em; margin-bottom:0; font-size:0.9em; list-style-type: disc; padding-left: 1.2em;">
                    <li>Note that only one subject can be assigned to each TriplesMap.</li>
                    <li>You can add new TriplesMaps in the <b style="color:#007bff;">Add TriplesMap option</b>.</li>
                </ul>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.write("")


    else:
        #IF THERE ARE TRIPLESMAPS AVAILABLE UNCOLLAPSE OPTIONS___________________________

        #first create dictionary of all the existing Subject Maps
        existing_subject_map_dict = {"Select a Subject Map": "Select a Subject Map"}
        for sm in st.session_state["g_mapping"].objects(predicate=RR.subjectMap):
            if isinstance(sm, URIRef):
                existing_subject_map_dict[split_uri(sm)[1]] = sm
        existing_subject_map_list = list(existing_subject_map_dict.keys())

        with col1a:
            tmap_label_input = st.selectbox("Select a TriplesMap", tmap_without_subject_list, key="s_tmap_label_input")

        tmap_label_input_existing = tmap_label_input
        tmap_label_input_new = tmap_label_input

        if tmap_label_input != "Select a TriplesMap":


            with col1:
                st.markdown("""<div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
                    </div>""", unsafe_allow_html=True)

            with col1:
                col1a, col1b = st.columns([2,1])
            with col1b:
                existing_sm_uncollapse = st.toggle("", key="existing_sm_uncollapse")
            with col1a:
                st.write("")
                st.markdown("""<span style="font-size:1.1em; font-weight:bold;">📑 Select existing Subject Map</span><br>
                        <small>Select an already created Subject Map from list</small>""",
                    unsafe_allow_html=True)

            if existing_sm_uncollapse:
                with col1a:
                    if len(existing_subject_map_dict) == 1:
                        st.markdown(f"""
                            <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                <span style="font-size:0.95rem;">
                                ⚠️ This option is not available. No labelled Subject Maps exist in mapping {st.session_state["g_label"]}.
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        tmap_label_input_existing = "Select a TriplesMap"
                    else:

                        if tmap_label_input_existing == "Select a TriplesMap":
                            pass
                            # with col1b:
                            #     st.write("")
                            #     st.write("")
                            #     st.markdown(f"""
                            #     <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                            #             <span style="font-size:0.95rem;">
                            #             ⚠️ You must select a TriplesMap to continue.
                            #             </span>
                            #         </div>
                            #         """, unsafe_allow_html=True)
                        else:
                            selected_existing_sm_label = st.selectbox("Choose an existing Subject Map", existing_subject_map_list)
                            selected_existing_sm_iri = existing_subject_map_dict[selected_existing_sm_label]
                            if selected_existing_sm_label != "Select a Subject Map":
                                tmap_iri_existing = st.session_state["tmap_dict"][tmap_label_input_existing]
                                save_existing_subject_map = st.button("Save", on_click=save_subject_existing)



            with col1a:
                st.markdown(
                    """
                    <div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
                    </div>
                    """,
                    unsafe_allow_html=True
                    )

            with col1:
                col1a, col1b = st.columns([2,1])
            with col1b:
                new_sm_uncollapse = st.toggle("", key="new_sm_uncollapse")
            with col1a:
                st.write("")
                st.markdown(
                    """
                        <span style="font-size:1.1em; font-weight:bold;">🆕 Create new Subject Map</span><br>
                        <small>Create Subject Map defining its subject generation rule</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                    )
                    #REUSE: ⚙️ Define the subject generation rule. Determine the logic for subject creation based on mapping type.

            if new_sm_uncollapse:

                #GET DATA SOURCE OF THE TRIPLESMAP____________________________
                if tmap_label_input_new == "Select a TriplesMap":
                    tmap_iri = None
                    tmap_logical_source_iri = None
                    s_generation_type = ""
                    # with col1b:
                    #     st.write("")
                    #     st.write("")
                    #     st.markdown(f"""
                    #     <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                    #             <span style="font-size:0.95rem;">
                    #             ⚠️ You must select a TriplesMap to continue.
                    #             </span>
                    #         </div>
                    #         """, unsafe_allow_html=True)

                else:   #TriplesMap selected
                    tmap_iri = st.session_state["tmap_dict"][tmap_label_input_new]
                    tmap_logical_source_iri = next(st.session_state["g_mapping"].objects(tmap_iri, RML.logicalSource), None)

                    #here we get the columns of the data source for the template option
                    data_source = next(st.session_state["g_mapping"].objects(tmap_logical_source_iri, RML.source), None)   #name of ds file
                    if data_source:
                        data_source_file = os.path.join(os.getcwd(), "data_sources", data_source)    #full path of ds file
                        columns_df = pd.read_csv(data_source_file)
                        column_list = columns_df.columns.tolist()
                    else:
                        column_list = []


                    with col1a:
                        s_label = st.text_input("Enter Subject Map label (optional)", key="subject_label")

                    if s_label in existing_subject_map_dict:
                        with col1a:
                            st.markdown(f"""
                                <div style="background-color:#fff3cd; padding:1em;
                                border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                                    ⚠️ The Subject Map label <b style="color:#cc9a06;">{s_label}</b>
                                    is already in use and will be ignored. Please, pick a different label.</div>
                            """, unsafe_allow_html=True)
                        s_label = ""   #ignore subject map label if it already exists


                    with col1:
                        col1a, col1b = st.columns([2,1])

                    with col1a:

                        s_generation_type_list = ["Template 📐", "Constant 🔒", "Reference 🔗"]

                        st.write("")
                        s_generation_type = st.radio(
                            label="Define the subject generation rule:",
                            options=s_generation_type_list,
                            horizontal=True,
                            )




                #TEMPLATE OPTION______________________________
                if s_generation_type == "Template 📐":

                    with col1b:
                        st.write("")
                        st.write("")
                        st.write("")
                        st.markdown(f"""
                            <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                <span style="font-size:0.95rem;">
                                    <b> 📐 Template use case </b>: <br>Dynamically construct the subject IRI using data values.
                                </span>
                            </div>
                            """, unsafe_allow_html=True)

                    #Select the column of the data source for the template
                    column_list.insert(0, "Select a column of the data source:")
                    with col1a:
                        subject_id = st.selectbox("Select the subject id", column_list, key="subject_id")

                    if subject_id != "Select a column of the data source:":
                        st.session_state["subject_id_input"] = subject_id

                    with col1a:
                        if tmap_label_input_new != "Select a TriplesMap" and subject_id != "Select a column of the data source:":
                            st.button("Save subject", on_click=save_subject_template)


                #CONSTANT OPTION______________________________
                if s_generation_type == "Constant 🔒":

                    with col1b:
                        st.write("")
                        st.write("")
                        st.write("")
                        st.markdown(f"""
                            <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                <span style="font-size:0.95rem;">
                                    <b> 🔒 Constant use case </b>: <br>Every subject is the same fixed IRI.
                                </span>
                            </div>
                            """, unsafe_allow_html=True)

                    with col1a:
                        subject_constant = st.text_input("Enter the subject constant", key="subject_constant")

                    if subject_constant != "Enter the subject constant":
                        st.session_state["subject_constant_input"] = subject_constant

                    with col1a:
                        if tmap_label_input_new != "Select a TriplesMap" and subject_constant != "Enter the subject constant":
                            st.button("Save subject", on_click=save_subject_constant)


                #REFERENCE OPTION______________________________
                if s_generation_type == "Reference 🔗":

                    with col1b:
                        st.write("")
                        st.write("")
                        st.write("")
                        st.markdown(f"""
                            <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                <span style="font-size:0.95rem;">
                                    <b> 🔗 Reference use case </b>: <br> Directly use the data value as the subject,
                                    especially for literals or when you want full control.
                                </span>
                            </div>
                            """, unsafe_allow_html=True)

                    #Select the column of the data source for the reference
                    column_list.insert(0, "Select a column of the data source:")
                    with col1a:
                        subject_id = st.selectbox("Select the subject id", column_list, key="subject_id")

                    if subject_id != "Select a column of the data source:":
                        st.session_state["subject_id_input"] = subject_id

                    with col1a:
                        if tmap_label_input_new != "Select a TriplesMap" and subject_id != "Select a column of the data source:":
                            st.button("Save subject", on_click=save_subject_reference)


        if st.session_state["subject_saved_ok_existing"]:
            with col1b:
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ The Subject Map has been assigned to the TriplesMap
                    <b style="color:#0f5132;">{split_uri(st.session_state["smap_ordered_list"][0])[1]}</b>.</div>
                """, unsafe_allow_html=True)
            st.session_state["subject_saved_ok_existing"] = False
            time.sleep(2)
            st.rerun()


    if st.session_state["subject_saved_ok_new"]:
        with col1:
            col1a, col1b = st.columns([1,2])
        with col1a:
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:1em;
            border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                ✅ The Subject Map has been assigned to the TriplesMap
                <b style="color:#0f5132;">{split_uri(st.session_state["smap_ordered_list"][0])[1]}</b>.</div>
            """, unsafe_allow_html=True)
        st.session_state["subject_saved_ok_new"] = False
        time.sleep(2)
        st.rerun()


    # st.write("This is for debugging purposes and will be deleted")
    # st.write("g_label: ", st.session_state["g_label"])
    #
    # st.write(f"Graph has {len(st.session_state["g_mapping"])} triples")
    # for s, p, o in list(st.session_state["g_mapping"])[:9]:  # show first 5 triples
    #     st.write(f"{s} -- {p} --> {o}")

#_________________________________________________________________


#_____________________________________________________________________
#ADD EXTRA TRIPLES TO SUBJECT MAP

    with col1:
        st.write("______________")
        st.markdown("""
        <div style="background-color:#e6e6fa; border:1px solid #511D66;
                    border-radius:5px; padding:10px; margin-bottom:8px;">
            <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                ➕ Subject Map Configuration
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")


    #SELECT THE TRIPLESMAP (this will give the subject if it exists)__________________________________
    #list of all triplesmaps
    tm_with_sm_list = ["Select a TriplesMap"]
    for tm_label, tm_iri in st.session_state["tmap_dict"].items():
        if any(st.session_state["g_mapping"].triples((tm_iri, RR.subjectMap, None))):
            tm_with_sm_list.append(tm_label)

    with col1:
        col1a, col1b = st.columns([2,1])

    if not st.session_state["tmap_dict"]:
        with col1a:
            st.markdown(f"""
                <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                ⚠️ No TriplesMaps in mapping {st.session_state["g_label"]}.<br>
                You can add new TriplesMaps in the <b style="color:#cc9a06;">Add TriplesMap option</b>.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            st.write("")

    elif len(tm_with_sm_list) == 1:
        with col1a:
            st.markdown(f"""
                <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                ⚠️ This option is not available because no TriplesMaps have already been assigned a Subject Map yet.
                Please do so in the <b style="color:#cc9a06;">🧱 Add New Subject Map</b> section of this pannel.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            st.write("")

    else:

        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            selected_tm_label = st.selectbox("Select a TriplesMap", tm_with_sm_list)   #select a triplesmap

        if selected_tm_label == "Select a TriplesMap":
            pass
            # with col1b:
            #     st.markdown(f"""
            #         <div style="background-color:#fff9db; border:1px dashed #511D66;
            #         padding:10px; border-radius:5px; margin-bottom:8px;">
            #             <span style="font-size:0.95rem;">
            #             ⚠️ You must select a TriplesMap to continue.
            #             </span>
            #         </div>
            #         """, unsafe_allow_html=True)
        else:

            selected_tm = st.session_state["tmap_dict"][selected_tm_label]        #selected tm iri
            selected_subject_bnode = st.session_state["g_mapping"].value(selected_tm, RR.subjectMap)     #subject of selected tm (BNode)
            selected_subject_id = st.session_state["subject_dict"][selected_tm_label][1]
            selected_subject_type = st.session_state["subject_dict"][selected_tm_label][2]


            with col1a:
                st.markdown(f"""
                    <div style="background-color:#edf7ef; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                         🔖 The Subject Map assigned to the TriplesMap <b>{selected_tm_label}</b>
                         is the {selected_subject_type} <b>{selected_subject_id}</b>.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                st.write("")


            #SUBJECT CLASS (ontology-based)
            with col1:
                st.markdown(
                    """
                    <div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1b:
                subject_class_uncollapse = st.toggle("", key="subject_class_uncollapse")
            with col1a:
                st.markdown(
                    """
                        <span style="font-size:1.1em; font-weight:bold;">🏷️ Subject class</span><br>
                        <small>Declares the ontology-based class of the generated subjects.</small>
                    """,
                    unsafe_allow_html=True
                )

            if subject_class_uncollapse:

                #Check whether the subject map already has a class
                subject_class = st.session_state["g_mapping"].value(selected_subject_bnode, RR["class"])

                with col1a:
                    if subject_class and selected_subject_bnode:   #subject class already exists
                        if isinstance(subject_class, URIRef):
                            st.markdown(
                                f"""
                                <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                                    🔒 Subject class:
                                    <b style="color:#007bff;">{split_uri(subject_class)[1]}</b><br>
                                    <small>Delete it to assign a different subject class.</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        elif isinstance(subject_class, BNode) and utils.is_union_class(subject_class):
                            st.markdown(
                                f"""
                                <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                                    🔒 Subject class:
                                    <b style="color:#007bff;">Union class {utils.get_union_class_label(subject_class)}</b><br>
                                    <small>Delete it to assign a different subject class.</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        elif isinstance(subject_class, BNode):
                            st.markdown(
                                f"""
                                <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                                    🔒 Subject class:
                                    <b style="color:#007bff;">BNode</b><br> ({subject_class})<br>
                                    <small>Delete it to assign a different subject class.</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        st.write("")
                        with col1a:
                            delete_subject_class_checkbox = st.checkbox(
                            ":gray-badge[⚠️ I am completely sure I want to delete the subject class]",
                            key="delete_subject_class")
                        if delete_subject_class_checkbox:
                            with col1:
                                col1a, col1b = st.columns([1,2])
                            with col1a:
                                st.button("Delete", on_click=delete_subject_class)


                    elif selected_subject_bnode:        #subject class does not exist
                        with col1a:
                            st.markdown(
                                f"""
                                <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                                    🔓 Subject class:
                                    <b style="color:#007bff;">not given</b><br>
                                    <small>Enter below.</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        st.write("")

                        #WE ORGANISE THE ONTOLOGY CLASSES IN DIFFERENT DICTIONARIES
                        #dictionary for simple classes
                        ontology_classes_dict = {"Select a class": ""}
                        class_triples = set()
                        class_triples |= set(st.session_state["g_ontology"].triples((None, RDF.type, OWL.Class)))   #collect owl:Class definitions
                        class_triples |= set(st.session_state["g_ontology"].triples((None, RDF.type, RDFS.Class)))    # collect rdfs:Class definitions
                        for s, p, o in class_triples:   #we add to dictionary removing the BNodes
                            if not isinstance(s, BNode):
                                ontology_classes_dict[split_uri(s)[1]] = s

                        #dictionary for superclasses
                        superclass_dict = {"Select a superclass": ""}
                        classes_in_superclass_dict = {"Select a class": ""}
                        for s, p, o in list(set(st.session_state["g_ontology"].triples((None, RDFS.subClassOf, None)))):
                            if not isinstance(o, BNode) and o not in superclass_dict.values():
                                superclass_dict[o.split("/")[-1].split("#")[-1]] = o


                        #ONLY SHOW OPTIONS IF THE ONTOLOGY HAS THEM
                        class_type_option_list = ["Class outside ontology"]
                        if len(ontology_classes_dict) != 1:   #if the ontology includes at least one class
                            class_type_option_list.insert(0, "Ontology class")


                        if class_type_option_list == ["Class outside ontology"]:   #no ontology or no classes in ontology
                            class_type = "Class outside ontology"
                        else:    #there is an ontology and it has classes
                            with col1a:
                                class_type = st.radio(
                                    label="Select an option:",
                                    options=class_type_option_list,
                                    horizontal=True,
                                    label_visibility="collapsed"
                                )


                        #ONTOLOGY CLASS
                        if class_type == "Ontology class":

                            if len(superclass_dict) != 1:   #there exists at least one superclass (show option to select a superclass)
                                with col1a:
                                    superclass = st.selectbox("Select a superclass to filter classes (optional)", list(superclass_dict.keys()))   #superclass label
                                classes_in_superclass_dict[superclass] = superclass_dict[superclass]
                            else:     #no superclasses exist (don't give option to select superclass)
                                superclass = "Select a superclass"

                            if superclass != "Select a superclass":   #a superclass has been selected
                                superclass = superclass_dict[superclass] #we get the superclass iri
                                for s, p, o in list(set(st.session_state["g_ontology"].triples((None, RDFS.subClassOf, superclass)))):
                                    classes_in_superclass_dict[split_uri(s)[1]] = s
                                with col1a:
                                    subject_class = st.selectbox("Select a class", list(classes_in_superclass_dict.keys()))   #class label
                                subject_class = classes_in_superclass_dict[subject_class] #we get the superclass iri
                            else:  #no superclass selected or no superclasses exist, give all classes as options
                                with col1a:
                                    subject_class = st.selectbox("Select a class", list(ontology_classes_dict.keys()), key="subject_class_from_all")   #class label
                                subject_class = ontology_classes_dict[subject_class] #we get the superclass iri


                            if subject_class != "":
                                with col1:
                                    col1a,col2a = st.columns([1,2])
                                with col1a:
                                    st.button("Save", key="save_subject_class", on_click=save_simple_subject_class)



                        #CLASS OUTSIDE ONTOLOGY
                        if class_type == "Class outside ontology":
                            with col1b:
                                st.markdown("<br><br>", unsafe_allow_html=True)
                            if st.session_state["g_ontology"] and len(class_type_option_list) == 1: #there is an ontology but it has no classes
                                with col1b:
                                    st.write("")
                                    st.markdown(f"""
                                        <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                            <span style="font-size:0.95rem;">
                                              🚧<b> Caution</b>: The ontology {st.session_state["ontology_label"]}
                                              does not define any classes. <b>Classes can only be added manually</b>.
                                              Using an ontology with predefined classes is recommended.
                                            </span>
                                        </div>
                                        """, unsafe_allow_html=True)
                            elif st.session_state["g_ontology"]:   #there exists an ontology and it has classes
                                with col1b:
                                    st.write("")
                                    st.markdown(f"""
                                        <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                            <span style="font-size:0.95rem;">
                                              🚧<b> Caution</b>: The option \"Class outside ontology\"
                                              <b>lacks ontology alignment</b> and could result in structural inconsistencies.
                                              We recommend an ontology-driven approach.
                                            </span>
                                        </div>
                                        """, unsafe_allow_html=True)
                            else:
                                with col1b:
                                    st.markdown(f"""
                                        <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                            <span style="font-size:0.95rem;">
                                              🚧<b> Caution</b>: You are working without an ontology. We recommend loading an ontology
                                               from the <b> Global Configuration</b> panel.
                                            </span>
                                        </div>
                                        """, unsafe_allow_html=True)

                            subject_class_prefix_list = list(st.session_state["ns_dict"].keys())
                            with col1a:
                                subject_class_prefix_list.insert(0,"Select a namespace")
                            with col1a:
                                subject_class_prefix = st.selectbox("Select a namespace", subject_class_prefix_list)
                            if len(subject_class_prefix_list) == 1:
                                with col1b:
                                    st.write("")
                                    st.markdown(f"""
                                        <div style="background-color:#f8d7da; border:1px dashed #a94442; padding:10px; border-radius:5px; margin-bottom:8px;">
                                            <span style="font-size:0.95rem;">
                                              ⚠️ No namespaces available. You can add namespaces in the
                                               <b>Global Configuration</b> page.
                                            </span>
                                        </div>
                                        """, unsafe_allow_html=True)
                            if subject_class_prefix != "Select a namespace":
                                NS = Namespace(st.session_state["ns_dict"][subject_class_prefix])
                            with col1a:
                                subject_class_input = st.text_input("Enter subject class")
                            if subject_class_input and subject_class_prefix != "Select a namespace":
                                subject_class = NS[subject_class_input]
                                with col1a:
                                    st.button("Save", on_click=save_external_subject_class)



            #TERM TYPE - IRI by default, but can be changed to BNode
            with col1a:
                st.write("")
                st.markdown(
                    """
                    <div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1b:
                term_type_uncollapse = st.toggle("", key="term_type_uncollapse")
            with col1a:
                st.markdown(
                    """
                        <span style="font-size:1.1em; font-weight:bold;">🆔 Term type</span><br>
                        <small>Indicates the target graph for the subject map triples. If not given, the default graph will be used.</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if term_type_uncollapse:
                if not st.session_state["g_mapping"].value(selected_subject_bnode, RR["termType"]):   #If termType not indicated yet, make it IRI (default)
                    st.session_state["g_mapping"].add((selected_subject_bnode, RR["termType"], RR.IRI))
                selected_subject_term_type = st.session_state["g_mapping"].value(selected_subject_bnode, RR["termType"])

                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    if selected_subject_bnode:
                        st.write("")
                        if split_uri(selected_subject_term_type)[1] == "IRI":
                            st.markdown(
                                f"""
                                <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                                    🔒 Subject term type:
                                    <b style="color:#007bff;">IRI</b><br>
                                    <small>Click button to change to BNode.</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            with col1:
                                col1a, col1b = st.columns([1,2])
                            with col1a:
                                st.write("")
                                st.button("Change to BNode", on_click=change_to_BNode)
                        else:
                            st.markdown(
                                f"""
                                <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                                    🔒 Subject term type:
                                    <b style="color:#007bff;">BNode</b><br>
                                    <small>Click button to change to IRI.</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            with col1:
                                col1a, col1b = st.columns([1,2])
                            with col1a:
                                st.write("")
                                st.button("Change to IRI", on_click=change_to_IRI)



            #GRAPH - If not given, default graph    HERE condider if rr:graphMap option (dynamic) is worth it
            with col1a:
                st.write("")
                st.markdown(
                    """
                    <div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1b:
                graph_map_uncollapse = st.toggle("", key="graph_map_uncollapse")
            with col1a:
                st.markdown(
                    """
                        <span style="font-size:1.1em; font-weight:bold;">🗺️️ Graph map</span><br>
                        <small>Indicates the target graph for the subject map triples. If not given, the default graph will be used.</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.write("")

            if graph_map_uncollapse:
                subject_graph = st.session_state["g_mapping"].value(selected_subject_bnode, RR["graph"])

                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    if subject_graph and selected_subject_bnode:    #subject graph already given
                        st.markdown(
                            f"""
                            <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                                🔒 Subject graph:
                                <b style="color:#007bff;">{split_uri(subject_graph)[1]}</b><br>
                                <small>Delete it to assign a different subject graph.</small>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        st.write("")

                        with col1a:
                            delete_subject_graph_checkbox = st.checkbox(
                            ":gray-badge[⚠️ I am completely sure I want to delete the subject graph]",
                            key="delete_subject_graph")
                        if delete_subject_graph_checkbox:
                            with col1:
                                col1a, col1b = st.columns([1,2])
                            with col1a:
                                st.button("Delete", on_click=delete_subject_graph)

                    elif selected_subject_bnode:       #subject graph not given
                        with col1a:
                            st.markdown(
                                f"""
                                <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                                    🔓 Subject graph:
                                    <b style="color:#007bff;">not given</b><br>
                                    <small>Enter below.</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        st.write("")
                        subject_graph_input = st.text_input("Enter subject graph", key="subject_graph_input")
                        subject_graph = BASE[subject_graph_input]
                        with col1:
                            col1a, col1b = st.columns([1,2])
                        with col1a:
                            if subject_graph_input:
                                st.button("Save", on_click=save_subject_graph)


    with col1:
        st.write("---")
        st.markdown("""
        <div style="background-color:#e6e6fa; border:1px solid #511D66;
                    border-radius:5px; padding:10px; margin-bottom:8px;">
            <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                🗑️ Remove existing Subject Map
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")

    with col1:
        col1a, col1b = st.columns([2,1])

    with col1:
        st.markdown("""<div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
            </div>""", unsafe_allow_html=True)

    with col1:
        col1a, col1b = st.columns([2,1])
    with col1b:
        delete_labelled_sm_uncollapse = st.toggle("", key="delete_labelled_sm_uncollapse")
    with col1a:
        st.write("")
        st.markdown("""<span style="font-size:1.1em; font-weight:bold;">🔖 Delete labelled Subject Map</span><br>
                <small>Select a labelled Subject Map and erase it completely</small>""",
            unsafe_allow_html=True)

    if delete_labelled_sm_uncollapse:
        with col1:
            col1a, col1b = st.columns([2,1])

        utils.update_dictionaries()
        sm_to_remove_list = ["Select a Subject Map"]
        for tm_label in st.session_state["subject_dict"]:
            if st.session_state["subject_dict"][tm_label][3] not in sm_to_remove_list and st.session_state["subject_dict"][tm_label][3] != "Unlabelled":
                sm_to_remove_list.append(st.session_state["subject_dict"][tm_label][3])

        if len(sm_to_remove_list) == 1:
            with col1a:
                st.markdown(f"""
                <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                        ⚠️ There are no labelled Subject Maps to remove.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
        else:

            with col1a:
                sm_to_remove_label = st.selectbox("Select a Subject Map", sm_to_remove_list, key="sm_to_remove")
                sm_to_remove = MAP[sm_to_remove_label]

            if sm_to_remove_label != "Select a Subject Map":
                assigned_tmap_list = []
                for tmap_label in st.session_state["subject_dict"]:
                    if sm_to_remove_label == st.session_state["subject_dict"][tmap_label][3]:
                        assigned_tmap_list.append(tmap_label)
                with col1a:
                    assigned_str = ", ".join(str(item) for item in assigned_tmap_list)
                    st.markdown(f"""
                        <div style="background-color:#fff3cd; padding:1em;
                        border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                            ⚠️ The Subject Map <b style="color:#cc9a06;">{sm_to_remove_label}</b>
                            is currently assigned to these TriplesMaps: <b style="color:#cc9a06;">{assigned_str}</b>.
                            </div>
                    """, unsafe_allow_html=True)
                    st.write("")
                    delete_labelled_subject_map_checkbox = st.checkbox(
                    ":gray-badge[⚠️ I am completely sure I want to delete the Subject Map]",
                    key="delete_labelled_subject_map_checkbox")
                if delete_labelled_subject_map_checkbox:
                    with col1:
                        col1a, col1b = st.columns([1,2])
                    with col1a:
                        st.button("Delete", on_click=delete_labelled_subject_map)

    with col1a:
        st.markdown("""<div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
            </div>""", unsafe_allow_html=True)
    with col1:
        col1a, col1b = st.columns([2,1])
    with col1b:
        delete_specific_sm_uncollapse = st.toggle("", key="delete_specific_sm_uncollapse")
    with col1a:
        st.write("")
        st.markdown("""<span style="font-size:1.1em; font-weight:bold;">
        🎯 Unassign Subject Map of a specific TriplesMap</span><br>
                <small>Select a TriplesMap and unassign its Subject Map</small>""",
            unsafe_allow_html=True)

    if delete_specific_sm_uncollapse:
        with col1:
            col1a, col1b = st.columns([2,1])

        tm_with_sm_list = ["Select a TriplesMap"]
        for tm_label, tm_iri in st.session_state["tmap_dict"].items():
            if any(st.session_state["g_mapping"].triples((tm_iri, RR.subjectMap, None))):
                tm_with_sm_list.append(tm_label)

        if len(tm_with_sm_list) == 1:
            with col1a:
                st.write("")
                st.markdown(f"""
                <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                        ⚠️ There are no TriplesMap with assigned Subject Maps.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

        else:

            with col1a:
                tm_to_unassign_sm = st.selectbox("Select a TriplesMap", tm_with_sm_list, key="tm_to_unassign_sm")

            if tm_to_unassign_sm != "Select a TriplesMap":
                tm_to_unassign_sm_iri = st.session_state["tmap_dict"][tm_to_unassign_sm]
                sm_to_unassign = st.session_state["g_mapping"].value(subject=tm_to_unassign_sm_iri, predicate=RR.subjectMap)

                st.write("HERE2", tm_to_unassign_sm_iri)
                with col1a:
                    if isinstance(sm_to_unassign, URIRef):
                        sm_to_unassign = split_uri(sm_to_unassign)[1]
                    elif isinstance(sm_to_unassign, BNode):
                        sm_to_unassign = "BNode: " + str(sm_to_unassign)[:5] + "..."
                    st.markdown(f"""
                        <div style="background-color:#fff3cd; padding:1em;
                        border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                            ⚠️ The TriplesMap <b style="color:#cc9a06;">{tm_to_unassign_sm}</b>
                            has been assigned the Subject Map <b style="color:#cc9a06;">{sm_to_unassign}</b>.
                            </div>
                    """, unsafe_allow_html=True)
                    st.write("")

                with col1a:
                    unassign_sm_checkbox = st.checkbox(
                    ":gray-badge[⚠️ I am completely sure I want to unassign the Subject Map]",
                    key=" unassign_sm_checkbox")
                if unassign_sm_checkbox:
                    with col1:
                        col1a, col1b = st.columns([1,2])
                    with col1a:
                        st.write("HERE3", st.session_state["g_mapping"].value(tm_to_unassign_sm_iri, RR.subjectMap))
                        st.button("Unassign", on_click=unassign_subject_map)



    with col1:
        col1a, col1b = st.columns([2,1])
    if st.session_state["smap_deleted_ok"]:
        with col1b:
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:1em;
            border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                ✅ The <b style="color:#007bff;">Subject Map
                </b> has been succesfully deleted!  </div>
            """, unsafe_allow_html=True)
            st.write("")
        st.session_state["smap_deleted_ok"] = False
        time.sleep(5)
        st.rerun()


    with col1:
        st.write("---")
        st.markdown("""
        <div style="background-color:#e6e6fa; border:1px solid #511D66;
                    border-radius:5px; padding:10px; margin-bottom:8px;">
            <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                🔎 Subject Map Snapshot
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")


    #SHOW COMPLETE INFORMATION ON THE SUBJECT MAPS___________________________________
    utils.update_dictionaries()
    subject_df_complete = utils.build_complete_subject_df()
    filtered_tmap_without_subject_list = [item for item in tmap_without_subject_list if item != "Select a TriplesMap"]
    tmap_without_subject_df = pd.DataFrame(filtered_tmap_without_subject_list, columns=['TriplesMap without Subject Map'])

    with col1:
        with st.expander("ℹ️ Show all Subject Maps"):
            st.write("")
            st.write("")
            if not subject_df.empty:
                st.dataframe(subject_df.drop(columns="TriplesMap IRI").copy(), hide_index=True)
            else:
                st.write("⚠️ No Subject Maps have been assigned yet!")

    with col1:
        with st.expander("ℹ️ Show all Subject Map entries"):
            st.write("")
            st.write("")
            if not subject_df_complete.empty:
                st.dataframe(subject_df_complete, hide_index=True)
            else:
                st.write("⚠️ No Subject Maps have been assigned yet!")

    with col1:
        with st.expander("ℹ️ Show all TriplesMap with no Subject Map"):
            st.write("")
            st.write("")
            if not tmap_without_subject_df.empty:
                st.dataframe(tmap_without_subject_df, hide_index=True)
            else:
                st.write("✔️ All TriplesMap have already been assigned Subject Maps!")

#________________________________________________

#________________________________________________
#ADD PREDICATE-OBJECT MAP TO MAP
if st.session_state["20_option_button"] == "po":

    st.markdown(f"""
    <div style="background-color:#f8d7da; padding:1em;
                border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
        ❌ This section is not ready yet.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

    col1,col2 = st.columns(2)

    po_options = ["Simple Object Map via reference (column-based)",
    "Constant-valued", "Template-based", "Language-tagged Literals",
    "Data Type Assignment", "Referencing Object Maps",
    "Referencing Object Map with Join Condition"
    ]

    with col2:
        po_type = st.radio("1️⃣ Choose the type of object map:", po_options)

        map_list = list(st.session_state["tmap_dict"].keys())
        map_list.insert(0, "Select a map")


        with col1:
            map_label = st.selectbox("Select a Triples map", map_list)

        if tmap_label != "Select a map":
            map_node = st.session_state["tmap_dict"][map_label]
            map_logical_source = next(st.session_state["g_mapping"].objects(map_node, RML.logicalSource), None)
            subject_map = st.session_state["g_mapping"].value(subject=map_node, predicate=RR.subjectMap)
        else:
            map_node = None
            map_logical_source = None
            subject_map = None

        if tmap_label != "Select a map":
            with col1:
                st.success(f"Subject map is {split_uri(subject_map)[1]}")

        po_map_label = BNode()


    st.write("___________________________")

    if po_type == "Simple Object Map via reference (column-based)":


        col1, col2 = st.columns([1,2])

        ns_list = list(st.session_state["ns_dict"].keys())
        if not ns_list:
            with col2:
                st.warning("No available namespaces, please add them in the Global Configuration page.")  #HERE this will never happen, rpedefined NS
        else:
            ns_list.insert(0,"Select a namespace")

            with col1:
                p_label_prefix = st.selectbox("Select a namespace for the predicate", ns_list)

            with col2:
                p_label = st.text_input("Enter predicate label")

            if p_label_prefix != "Select a namespace" and p_label:
                PNS = Namespace(st.session_state["ns_dict"][p_label_prefix])
                p_iri = PNS[p_label]


            with col1:
                om_label_prefix = st.selectbox("Select a namespace for the objectMap", ns_list)

            with col2:
                om_label = st.text_input("Enter objectMap name")

            if om_label_prefix != "Select a namespace" and om_label:
                OMNS = Namespace(st.session_state["ns_dict"][om_label_prefix])
                om_iri = OMNS[om_label]


            data_source = next(st.session_state["g_mapping"].objects(map_logical_source, RML.source), None)   #name of ds file
            if data_source:
                data_source = utils.get_ds_full_path(data_source)   #full path of ds file


            if data_source:
                columns_df = pd.read_csv(data_source)
                column_list = columns_df.columns.tolist()
                column_list.insert(0, "Select a data source")
            else:
                column_list = []

            reference = st.selectbox("Select the reference (column name from where to get the data)", column_list)



            st.write("___________________________")

            show_data_list = []

            if subject_map:
                s_prefix = st.session_state["g_mapping"].namespace_manager.compute_qname(subject_map)[0]
                subject_map_label = split_uri(subject_map)[1]
            else:
                s_prefix = ""
                subject_map_label = ""

            if tmap_label != "Select a map":
                map_iri = st.session_state["tmap_dict"][map_label]
                m_prefix =  st.session_state["g_mapping"].namespace_manager.compute_qname(map_iri)[0]
            else:
                m_prefix = ""
                map_label = ""

            if p_label_prefix == "Select a namespace":
                p_label_prefix = ""

            if om_label_prefix == "Select a namespace":
                om_label_prefix = ""

            if reference == "Select a data source":
                reference = ""


            show_data_list.append({
                "": "Namespace",
                "TriplesMap": m_prefix,
                "SubjectMap": s_prefix,
                "Predicate": p_label_prefix,
                "ObjectMap": om_label_prefix,
                "Reference": "---"
            })


            show_data_list.append({
                "": "Label",
                "TriplesMap": map_label,
                "SubjectMap": subject_map_label,
                "Predicate": p_label,
                "ObjectMap": om_label,
                "Reference": reference
            })


            show_data_df = pd.DataFrame(show_data_list)
            st.dataframe(show_data_df, use_container_width=True, hide_index=True)


        if subject_map and po_map_label and p_iri and om_iri and reference:
            po_button = st.button("Save predicate-object")
            if po_button:

                st.session_state["g_mapping"].add((subject_map, RR.predicateObjectMap, po_map_label))
                st.session_state["g_mapping"].add((po_map_label, RR.predicate, p_iri))
                st.session_state["g_mapping"].add((po_map_label, RR.objectMap, om_iri))
                st.session_state["g_mapping"].add((om_iri, RML.reference, Literal(reference)))

    else:
        st.error("OPTION NOT YET AVAILABLE")

#________________________________________________


#________________________________________________
#SAVE PROGRESS
if st.session_state["20_option_button"] == "save_progress":

    st.markdown(f"""
    <div style="background-color:#f8d7da; padding:1em;
                border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
        ❌ This section is not ready yet.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

    col1, col2 = st.columns(2)

    save_g_folder_path = utils.get_g_folder_path()
    existing_files_list = [f for f in os.listdir(save_g_folder_path) if f.endswith(".pkl")]
    with col1:
        save_g_filename = st.text_input(
        f"Enter the filename to save the mapping {st.session_state["g_label"]} (without extension):", key="save_g_filename_flag")
        if save_g_filename and (save_g_filename + ".pkl") in existing_files_list:
            st.warning(f"""The file {save_g_filename} is already in use. Are you sure you want to
            overwrite it?""")
            overwrite_checkbox = st.checkbox(f"""I am I want to overwrite it""", key="overwrite_checkbox")
        else:
            overwrite_checkbox = True


        if overwrite_checkbox:
            if save_g_filename:
                st.session_state["save_g_filename"] = save_g_filename + ".pkl"
            confirm_button = st.button("Save progress", on_click=reset_input)


            if confirm_button:

                save_g_full_path = utils.get_g_full_path(st.session_state["save_g_filename"])

                with open(save_g_full_path, "wb") as f:
                    pickle.dump(st.session_state["g_mapping"], f)


                st.success(f"""The mapping {st.session_state["candidate_label_flag"]}
                 has been saved to file {st.session_state["save_g_filename"]}.""")



#________________________________________________







    # #OPTION TO SHOW INFORMATION_________________________
    # with col2:    #display all the TriplesMaps in a dataframe
    #     col2a,col2b = st.columns(2)
    # with col2b:
    #     st.write("")
    #     st.write("")
    #
    #     with col2:
    #         col2a,col2b = st.columns([0.1,2])
    #     with col2b:
    #         with st.expander("ℹ️ Show panel information"):
    #             st.markdown(""" <br>
    #                     💬 <b>Working with subject maps:</b>
    #                     <ul style="font-size:0.85rem; margin-left:10px; padding-left:15px; list-style-type: disc;">
    #                         <li>
    #                             First, create a TriplesMap in the <b>Add TriplesMap</b> panel.
    #                         </li>
    #                         <li>
    #                             Then, go to panel <b> Add Subject Map </b> to set the Subject Map of the TriplesMap
    #                             (each TriplesMap can only be assigned one Subject Map).
    #                         </li>
    #                         <li>
    #                             Create the Subject Map in section <b>🧱 Add New Subject Map</b>.
    #                         </li>
    #                         <li>
    #                             You can add more details in the <b>➕ Subject Map Configuration</b> section (optional):
    #                             <ul style="list-style-type: none; margin: 0; padding-left: 0;">
    #                                 <li>🏷️ <b>Subject class</b>: Declares the subject’s class (ontology-based).
    #                                 Allows to select union or intersection classes if included in the ontology.</li>
    #                                 <li>🆔 <b>Term type</b>: Specifies whether the subject is an IRI or a blank node.</li>
    #                                 <li>🗺️️ <b>Graph map</b>: Designates the named graph for storing the generated triples.</li>
    #                             </ul>
    #                         </li>
    #                     </ul>
    #                 """, unsafe_allow_html=True)

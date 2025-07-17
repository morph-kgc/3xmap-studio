import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle
from rdflib.namespace import split_uri


#________________________________________________
#AESTHETICS

#button style
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #3498db;
        color: white;
        height: 3em;
        width: 100%;
        border-radius: 5px;
        border: none;
    }
    div.stButton > button:hover {
        background-color: #2e86c1;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

#Header
st.markdown("""
<div style="display:flex; align-items:center; background-color:#f0f0f0; padding:12px 18px;
            border-radius:8px; margin-bottom:16px;">
    <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
         style="width:32px; margin-right:12px;">
    <div>
        <h3 style="margin:0; font-size:1.75rem;">
            <span style="color:#511D66; font-weight:bold; margin-right:12px;">-----</span>
            Build Mapping
            <span style="color:#511D66; font-weight:bold; margin-left:12px;">-----</span>
        </h3>
        <p style="margin:0; font-size:0.95rem; color:#555;">
            Build your mapping by adding <b>Triple Maps</b>, <b>Subject Maps</b>, and <b>Predicate-Object Maps</b>.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)


st.write("")

#__________________________________________


#____________________________________________
#PRELIMINARY
# Namespaces
namespaces = utils.get_predefined_ns_dict()
RML = namespaces["rml"]
RR = namespaces["rr"]
QL = namespaces["ql"]
MAP = namespaces["map"]
SUBJ = namespaces["subj"]
EX = namespaces["ex"]
CLASS = namespaces["class"]
FOAF = namespaces["foaf"]


#define on_click functions
def reset_input():    #function to reset input upon click
    st.session_state["overwrite_checkbox"] = False
    st.session_state["save_g_filename_flag"] = ""

def save_tmap():   #function to save TriplesMap upon click
    utils.add_logical_source(st.session_state["g_mapping"], tmap_label, selected_ds)   #HERE I GO - update dic separately and remove from function add triples
    utils.update_dictionaries()             #to update tmap_dict
    st.session_state["ds_list"] = "Select a data source"      #restart input variables
    st.session_state["tmap_label_input"] = ""
    st.session_state["save_tmap_success"] = True

def save_subject_template():   #function to save subject (template option)
    namespaces = utils.get_predefined_ns_dict()
    RR = namespaces["rr"]
    SUBJ = namespaces["subj"]

    tmap_iri = st.session_state["tmap_dict"][tmap_label]
    smap_iri = BNode()
    utils.update_dictionaries()

    st.session_state["g_mapping"].add((tmap_iri, RR.subjectMap, smap_iri))
    st.session_state["g_mapping"].add((smap_iri, RR.template, Literal(f"http://example.org/resource/{{{st.session_state["subject_id_input"]}}}")))
    st.session_state["s_tmap_label_input"] = "Select a TriplesMap"
    st.session_state["subject_id"] = "Select a column of the data source:"
    st.session_state["subject_id_input"] = ""
    st.session_state["subject_saved_ok"] = True

def save_subject_constant():   #function to save subject (template option)
    namespaces = utils.get_predefined_ns_dict()
    RR = namespaces["rr"]
    SUBJ = namespaces["subj"]

    tmap_iri = st.session_state["tmap_dict"][tmap_label]
    smap_iri = BNode()
    utils.update_dictionaries()

    st.session_state["g_mapping"].add((tmap_iri, RR.subjectMap, smap_iri))
    st.session_state["g_mapping"].add((smap_iri, RR.constant, Literal(f"http://example.org/resource/{st.session_state["subject_constant_input"]}")))
    st.session_state["s_tmap_label_input"] = "Select a TriplesMap"
    st.session_state["subject_constant"] = "Enter the subject constant"
    st.session_state["subject_saved_ok"] = True


def save_subject_reference():   #function to save subject (template option)
    namespaces = utils.get_predefined_ns_dict()
    RR = namespaces["rr"]
    SUBJ = namespaces["subj"]
    RML = namespaces["rml"]

    tmap_iri = st.session_state["tmap_dict"][tmap_label]
    smap_iri = BNode()
    utils.update_dictionaries()

    st.session_state["g_mapping"].add((tmap_iri, RR.subjectMap, smap_iri))
    st.session_state["g_mapping"].add((smap_iri, RML.reference, Literal(st.session_state["subject_id_input"])))
    st.session_state["s_tmap_label_input"] = "Select a TriplesMap"
    st.session_state["subject_id"] = "Select a column of the data source:"
    st.session_state["subject_id_input"] = ""
    st.session_state["subject_saved_ok"] = True

def save_subject_class():
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
if "subject_saved_ok" not in st.session_state:
    st.session_state["subject_saved_ok"] = False





col1,col2 = st.columns(2)
if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
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
            if st.session_state["g_label"]:
                st.markdown(f"""
                <div style="background-color:#e6e6fa; padding:1em; border-radius:5px;
                color:#2a0134; border:1px solid #511D66;">
                    ☑️ You are currently working with mapping
                    <b style="color:#511D66;">{st.session_state["g_label"]}</b>.
                </div>
                """, unsafe_allow_html=True)


            else:
                st.markdown(f"""
                <div style="background-color:#e6e6fa; padding:1em; border-radius:5px;
                color:#2a0134; border:1px solid #511D66;">
                    ✖️ <b style="color:#511D66;">No mapping</b> has been loaded yet.
                </div>
                """, unsafe_allow_html=True)


    #DISPLAY TRIPLESMAP INFO IN A DATAFRAME
    utils.update_dictionaries()
    with col2:    #display all the TriplesMaps in a dataframe
        col2a,col2b = st.columns([0.5,2])
        with col2b:
            st.write("")
            st.write("")
            tmap_df = pd.DataFrame(list(st.session_state["data_source_dict"].items()), columns=["TriplesMap label", "Data source"])
            st.dataframe(tmap_df, hide_index=True)
            st.write("")

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
        if tmap_label:
            st.session_state["tmap_label"] = tmap_label

        ds_allowed_formats = utils.get_ds_allowed_formats()            #data source for the TriplesMap
        ds_list = [f for f in os.listdir(ds_folder_path) if f.endswith(ds_allowed_formats)]
        ds_list.insert(0, "Select a data source") # Add a placeholder option
        selected_ds = st.selectbox("Choose a file:", ds_list, key="ds_list")
        if selected_ds != "Select a data source":
            st.session_state["selected_ds"] = selected_ds

    if tmap_label in st.session_state["tmap_dict"]:
        with col1a:
            st.markdown(f"""
            <div style="background-color:#f8d7da; padding:1em;
                        border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                ❌ TriplesMap label <b style="color:#a94442;">{tmap_label}</b> already in use: <br>
                Please pick a different label.
            </div>
            """, unsafe_allow_html=True)
            st.write("")
    elif tmap_label and selected_ds != "Select a data source":
        with col1a:
            save_tmap_button = st.button("Save new TriplesMap", on_click=save_tmap)

    if st.session_state["save_tmap_success"]:
        with col1a:
            st.session_state["save_tmap_success"] = False
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:1em;
            border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                ✅ You created the TriplesMap <b style="color:#0f5132;">{st.session_state["tmap_label"]}
                </b>, <br>
                associated to the data source <b style="color:#0f5132;"> {st.session_state["selected_ds"]}</b>.  </div>
            """, unsafe_allow_html=True)


#________________________________________________



#________________________________________________
#ADD SUBJECT MAP TO MAP
if st.session_state["20_option_button"] == "s":

    col1,col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
        with col2b:
            if st.session_state["g_label"]:
                st.markdown(f"""
                <div style="background-color:#e6e6fa; padding:1em; border-radius:5px;
                color:#2a0134; border:1px solid #511D66;">
                    ☑️ You are currently working with mapping
                    <b style="color:#511D66;">{st.session_state["g_label"]}</b>.
                </div>
                """, unsafe_allow_html=True)


            else:
                st.markdown(f"""
                <div style="background-color:#e6e6fa; padding:1em; border-radius:5px;
                color:#2a0134; border:1px solid #511D66;">
                    ✖️ <b style="color:#511D66;">No mapping</b> has been loaded yet.
                </div>
                """, unsafe_allow_html=True)


    #DISPLAY TRIPLESMAP AND SUBJECT INFO IN A DATAFRAME__________________
    utils.update_dictionaries()
    subject_df = utils.build_subject_df()

    with col2:    #display all the TriplesMaps in a dataframe
        col2a,col2b = st.columns([0.1,2])
        with col2b:
            st.write("")
            st.write("")
            st.dataframe(subject_df, hide_index=True)
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
                <div style="background-color:#fff3cd; padding:1em;
                border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                    ⚠️ No TriplesMaps in mapping {st.session_state["g_label"]}.<br>
                    You can add new TriplesMaps in the <b style="color:#cc9a06;">Add TriplesMap option</b>.
                </div>
            """, unsafe_allow_html=True)
            st.write("")

    elif len(tmap_without_subject_list) == 1:
        with col1:
            st.markdown(f"""
                <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                    <span style="font-size:0.95rem;">
                ☑️ <b>All existing TriplesMaps have already been assigned a subject map.</b><br>
                <ul style="margin-top:0.5em; margin-bottom:0; font-size:0.9em; list-style-type: disc; padding-left: 1.2em;">
                    <li>Note that only one subject can be assigned to each TriplesMap.</li>
                    <li>You can add new TriplesMaps in the <b style="color:#007bff;">Add TriplesMap option</b>.</li>
                </ul>
                    </span>
                </div>
                """, unsafe_allow_html=True)
            st.write("")

    else:
        with col1a:
            tmap_label_input = st.selectbox("Select a TriplesMap", tmap_without_subject_list, key="s_tmap_label_input")

        #GET DATA SOURCE OF THE TRIPLESMAP____________________________
        if tmap_label_input != "Select a TriplesMap":
            tmap_iri = st.session_state["tmap_dict"][tmap_label_input]
            tmap_logical_source_iri = next(st.session_state["g_mapping"].objects(tmap_iri, RML.logicalSource), None)
        else:
            tmap_iri = None
            tmap_logical_source_iri = None

        data_source = next(st.session_state["g_mapping"].objects(tmap_logical_source_iri, RML.source), None)   #name of ds file
        if data_source:
            data_source_file = os.path.join(os.getcwd(), "data_sources", data_source)    #full path of ds file
            columns_df = pd.read_csv(data_source_file)
            column_list = columns_df.columns.tolist()
        else:
            column_list = []


        #INDICATE SUBJECT GENERATION RULE___________________________
        s_generation_type_list = ["Template 📐", "Constant 🔒", "Reference 🔗"]

        with col1:
            col1a, col1b = st.columns([2,1])

        with col1a:
            st.markdown("<b>--------- Define the subject generation rule ---------</b>", unsafe_allow_html=True)
            s_generation_type = st.radio(
                label="Select an option:",
                options=s_generation_type_list,
                horizontal=True,
                label_visibility="collapsed"
            )

        #TEMPLATE OPTION______________________________
        if s_generation_type == "Template 📐":

            with col1b:
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
                if tmap_label_input != "Select a TriplesMap" and subject_id != "Select a column of the data source:":
                    st.button("Save subject", on_click=save_subject_template)

            if st.session_state["subject_saved_ok"]:
                with col1a:
                    subject_info = st.session_state["subject_dict"].get(tmap_label, ["", ""])
                    st.markdown(f"""
                    <div style="background-color:#d4edda; padding:1em;
                    border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                        ✅ A subject has been assigned to the TriplesMap
                        <b style="color:#0f5132;">{tmap_label}</b>.<br>
                        The subject is a template using
                        <b style="color:#0f5132;"> {subject_info[1]} </b>
                        of the data source.</div>
                    """, unsafe_allow_html=True)
                st.session_state["subject_saved_ok"] = False


        #CONSTANT OPTION______________________________
        if s_generation_type == "Constant 🔒":

            with col1b:
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
                if tmap_label_input != "Select a TriplesMap" and subject_constant != "Enter the subject constant":
                    st.button("Save subject", on_click=save_subject_constant)

            if st.session_state["subject_saved_ok"]:
                with col1a:
                    st.markdown(f"""
                    <div style="background-color:#d4edda; padding:1em;
                    border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                        ✅ A subject has been assigned to the TriplesMap
                        <b style="color:#0f5132;">{tmap_label}</b>.<br>
                        The subject is a constant:
                        <b style="color:#0f5132;"> {st.session_state["subject_constant_input"]}. </b>
                        </div>
                    """, unsafe_allow_html=True)
                st.session_state["subject_saved_ok"] = False

        #REFERENCE OPTION______________________________
        if s_generation_type == "Reference 🔗":

            with col1b:
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
                if tmap_label_input != "Select a TriplesMap" and subject_id != "Select a column of the data source:":
                    st.button("Save subject", on_click=save_subject_reference)

            if st.session_state["subject_saved_ok"]:
                with col1a:
                    subject_info = st.session_state["subject_dict"].get(tmap_label, ["", ""])
                    st.markdown(f"""
                    <div style="background-color:#d4edda; padding:1em;
                    border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                        ✅ A subject has been assigned to the TriplesMap
                        <b style="color:#0f5132;">{tmap_label}</b>.<br>
                        The subject is a reference using
                        <b style="color:#0f5132;"> {subject_info[1]} </b>
                        of the data source.</div>
                    """, unsafe_allow_html=True)
                st.session_state["subject_saved_ok"] = False



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

        #➕ Add extra triples to Subject Map   (or settings) 🛠️

    #SELECT THE TRIPLESMAP TO WHICH THE SUBJECT MAP WILL BE ADDED___________________________
    #list of all triplesmaps
    tm_list = []
    for tm_label in st.session_state["tmap_dict"]:
        tm_list.append(tm_label)

    tm_list.insert(0, "Select a TriplesMap")

    with col1:
        col1a, col1b = st.columns([2,1])
    with col1a:
        selected_tm_label = st.selectbox("Select a TriplesMap", tm_list)   #select a triplesmap

    if selected_tm_label == "Select a TriplesMap":
        with col1b:
            st.markdown(f"""
                <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                    <span style="font-size:0.95rem;">
                    ❕ You must select a TriplesMap to continue.
                    </span>
                </div>
                """, unsafe_allow_html=True)
    else:

        selected_tm = st.session_state["tmap_dict"][selected_tm_label]        #selected tm iri
        selected_subject_bnode = st.session_state["g_mapping"].value(selected_tm, RR.subjectMap)     #subject of selected tm (BNode)
        selected_subject_id = st.session_state["subject_dict"][selected_tm_label][1]
        selected_subject_type = st.session_state["subject_dict"][selected_tm_label][2]

        if not selected_subject_bnode:
            with col1a:
                st.markdown(f"""
                    <div style="background-color:#fff3cd; padding:1em;
                    border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                        ⚠️ A subject has not been added yet to the TriplesMap
                        <b style="color:#cc9a06;"> {selected_tm_label}</b>.
                        Please add a subject for the TriplesMap in the
                        <b style="color:#cc9a06;">🧱 Add New Subject Map section</b>.
                    </div>
                """, unsafe_allow_html=True)
                st.write("")
            with col1b:
                st.markdown(f"""
                    <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                         🏷️ The TriplesMap <b>{selected_tm_label}</b>
                         has no subject.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            with col1b:
                st.markdown(f"""
                    <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                         🏷️ The subject of the TriplesMap <b>{selected_tm_label}</b>
                         is the {selected_subject_type} <b>{selected_subject_id}</b>.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                st.write("")

        #SUBJECT CLASS
        subject_class = st.session_state["g_mapping"].value(selected_subject_bnode, RR["class"])

        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            if subject_class and selected_subject_bnode:
                st.markdown(
                    f"""
                    <div style="background-color:#f0f0f0;padding:10px;border-radius:5px;">
                    Subject class: <b>{split_uri(subject_class)[1]}</b>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                with col1b:
                    st.button("Delete", on_click=delete_subject_class)


            elif selected_subject_bnode:
                subject_class_input = st.text_input("Enter subject class")
                subject_class = FOAF[subject_class_input]
                with col1b:
                    if subject_class_input:
                        st.write("")
                        st.button("Save", on_click=save_subject_class)



        #TERM TYPE - IRI by default, but can be changed to BNode
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
                        <div style="background-color:#f0f0f0;padding:10px;border-radius:5px;">
                        Subject term type: <b>IRI</b>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    with col1b:
                        st.write("")
                        st.button("Change to BNode", on_click=change_to_BNode)
                else:
                    st.markdown(
                        f"""
                        <div style="background-color:#f0f0f0;padding:10px;border-radius:5px;">
                        Subject term type: <b>BNode</b>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    with col1b:
                        st.write("")
                        st.button("Change to IRI", on_click=change_to_IRI)

        #GRAPH - If not given, default graph    HERE condider if rr:graphMap option (dynamic) is worth it
        subject_graph = st.session_state["g_mapping"].value(selected_subject_bnode, RR["graph"])

        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            if subject_graph and selected_subject_bnode:
                st.markdown(
                    f"""
                    <div style="background-color:#f0f0f0;padding:10px;border-radius:5px;">
                    Subject class: <b>{split_uri(subject_graph)[1]}</b>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                with col1b:
                    st.button("Delete", on_click=delete_subject_graph, key="delete_subject_graph")


            elif selected_subject_bnode:
                subject_graph_input = st.text_input("Enter subject graph", key="subject_graph_input")
                subject_graph = FOAF[subject_graph_input]
                with col1b:
                    if subject_graph_input:
                        st.write("")
                        st.button("Save", on_click=save_subject_graph)

        #OPTION TO DISPLAY CONFIGURATION INFORMATION
        with col1:
            st.write("")
            st.write("")
            col1a,col1b = st.columns(2)
        with col1a:
            st.markdown('<span id="custom-style-marker"></span>', unsafe_allow_html=True)
            show_info_button = st.button("ℹ️ Show configuration information")
            st.markdown("""
                <style>
                .element-container:has(#custom-style-marker) + div button {
                    background-color: #eee;
                    font-size: 0.75rem;
                    color: #444;
                }
                </style>
            """, unsafe_allow_html=True)

            if show_info_button:
                with col1:
                    st.markdown("""
                        <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        ℹ️ <b>Configuration options:</b>
                            <ul style="font-size:0.85rem; margin-left:15px; padding-left:10px;">
                                <li><b>Subject class</b>: Declares the RDF class of the generated subject.</li>
                                <li><b>Term type</b>: Specifies what kind of RDF node the subject should be (either an IRI or a blank node).</li>
                                <li><b>Graph map</b>: Indicates the named graph where the triples produced by the subject map will be stored.</li>
                            </ul>
                        </div>
                    """, unsafe_allow_html=True)
                with col1b:
                    st.markdown('<span id="custom-style-marker"></span>', unsafe_allow_html=True)
                    st.button("⬇️ Hide information")
                    st.markdown("""
                        <style>
                        .element-container:has(#custom-style-marker) + div button {
                            background-color: #eee;
                            font-size: 0.75rem;
                            color: #444;
                        }
                        </style>
                    """, unsafe_allow_html=True)

    with col1:
        st.write("---")
        st.markdown("""
        <div style="background-color:#e6e6fa; border:1px solid #511D66;
                    border-radius:5px; padding:10px; margin-bottom:8px;">
            <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                🔎 Show Subject Map Info
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")


    #SHOW COMPLETE INFORMATION ON THE SUBJECT MAPS___________________________________
    utils.update_dictionaries()
    subject_df = utils.build_complete_subject_df()

    with col1:
        col1a, col1b = st.columns(2)
    with col1a:
        show_subject_map_info_button = st.button("Show subject map information")
    if show_subject_map_info_button:
        with col1b:
            hide_subject_map_info_button = st.button("Hide information")
        st.write("")
        st.dataframe(subject_df, hide_index=True)
        st.write("")


#________________________________________________

#________________________________________________
#ADD PREDICATE-OBJECT MAP TO MAP


if st.session_state["20_option_button"] == "po":

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

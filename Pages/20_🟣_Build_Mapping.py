import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle
from rdflib.namespace import split_uri

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

def reset_input():    #function to reset input upon click
    st.session_state["overwrite_checkbox"] = False
    st.session_state["save_g_filename_flag"] = ""

if "confirm_button" not in st.session_state:
    st.session_state["confirm_button"] = False
if "custom_ns_dict" not in st.session_state:
    st.session_state["custom_ns_dict"] = {}


col1,col2 = st.columns(2)
if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
    with col1:
        st.error("❗ You need to select a mapping. Please go to Global Configuration.")
    st.stop()
if "map_dict" not in st.session_state:    #dictionary to store the maps
    st.session_state["map_dict"] = {}

#Here we load the mapping information to the mapping dictionary:
if st.session_state["g_label"]:
    triples_maps = list(st.session_state["g_mapping"].subjects(RML.logicalSource, None))
    # Print them
    for tm in triples_maps:
        triplesmap_label = tm.split("#")[-1]   #HERE CHANGE TO RDFLIB METHOD
        st.session_state["map_dict"][triplesmap_label] = tm




st.title("Build Mapping")

col1, col2, col3, col4, col5 = st.columns(5)
with col5:
    if st.session_state["g_label"]:
        st.markdown(
        f"""<span style="color:grey; font-size:16px;">
        <div style="line-height: 1.5;border: 1px solid blue; padding: 10px; border-radius: 5px;">
        You are currently working with the mapping
        <span style="color:blue; font-weight:bold;">{st.session_state["g_label"]}</span>.
        </div></span>
        """,
        unsafe_allow_html=True)
    else:
        st.markdown(
        f"""<span style="color:grey; font-size:16px;">
        <div style="line-height: 1.5;border: 1px solid blue; padding: 10px; border-radius: 5px;">
        <span style="color:blue; font-weight:bold;">No mapping</span> has been loaded yet.
        </div></span>
        """,
        unsafe_allow_html=True)

st.write("")



#g = Graph() #create empty graph to store triples (this is the mapping we are building)
ds_folder_path = utils.get_ds_folder_path()   #path to folder with data sources

#___________________________________________

 #_____________________________________________
#SELECT OPTION -> Buttons for namespace, map, subject or predicate-object


if "20_option_button" not in st.session_state:
    st.session_state["20_option_button"] = None

with col1:
    tmap_button = st.button("Add Triples Map")
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

    col1, col2, col3 = st.columns([2,0.1,2])
    with col1:
        st.write("Create new map")
        map_label = st.text_input("Enter a label for the new mapping")    #user-friendly name for the map

    with col2:
        st.markdown("<div style='height: 130px; border-left: 2px solid lightgray;'></div>", unsafe_allow_html=True)

    with col3:
        st.write("Remove existing map (if not in use)")
        remove_map_label = st.text_input("""Enter the label of the map
        you'd like to remove""")

    col1, col2, col3 = st.columns([2,0.1,2])

    with col1:
        ds_allowed_formats = (".csv",".json", ".xml")             #data source for the map
        ds_list = [f for f in os.listdir(ds_folder_path) if f.endswith(ds_allowed_formats)]
        ds_list.insert(0, "Select a data source") # Add a placeholder option
        selected_ds = st.selectbox("Choose a document:", ds_list, key="ds_list")

    with col2:
        st.markdown("<div style='height: 60px; border-left: 2px solid lightgray;'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2,0.1,2])

    with col1:
        save_tmap_button = st.button("Save new map")
    with col2:
     st.markdown("<div style='height: 80px; border-left: 2px solid lightgray;'></div>", unsafe_allow_html=True)
    with col3:
        remove_tmap_button = st.button("Remove map")

    with col1:
        if save_tmap_button:
            if not map_label:
                st.warning("⚠️ You must enter a map label")
            elif not selected_ds or selected_ds == "Select a data source":
                st.warning("⚠️ You must select a data source")
            elif map_label in st.session_state["map_dict"]:
                st.warning("⚠️ Map label already in use, please pick another label.")
            else:
                st.session_state["map_dict"] = utils.add_logical_source(st.session_state["g_mapping"], map_label, selected_ds, st.session_state["map_dict"])
                st.success(f"""You created the map {map_label},
                associated to the data source {selected_ds} 😎""")


    if remove_tmap_button:
        with col3:
            if not remove_map_label:
                st.warning("⚠️ You must enter a map label")
            elif remove_map_label not in st.session_state["map_dict"]:
                st.warning("⚠️ Map label does not exist")
            else:
                st.session_state["map_dict"] = utils.remove_map(st.session_state["g_mapping"], remove_map_label, st.session_state["map_dict"])
                st.success(f"{remove_map_label} has been deleted")


    st.write("_______________________")

    data_source_dict = {}
    for map_label, map_node in st.session_state["map_dict"].items():
        data_source = utils.get_data_source_file(st.session_state["g_mapping"], map_node)
        data_source_dict[map_label] = data_source

    #show the maps in a table, along with their data sources
    col1, col2 = st.columns([3,2])
    with col1:
        map_df = pd.DataFrame(list(data_source_dict.items()), columns=["Map label", "Data source"])
        st.dataframe(map_df, hide_index=True)
#________________________________________________


#________________________________________________
#ADD SUBJECT MAP TO MAP
if st.session_state["20_option_button"] == "s":

    if "s_map_dict" not in st.session_state:    #dictionary to store information on the subjects   {map: [subject, subject_type]}
        st.session_state["s_map_dict"] = {}

    map_list = list(st.session_state["map_dict"].keys())
    map_list.insert(0, "Select a map")

    map_label = st.selectbox("Select a map to add subject", map_list)

    if map_label != "Select a map":
        map_node = st.session_state["map_dict"][map_label]
        map_logical_source = next(st.session_state["g_mapping"].objects(map_node, RML.logicalSource), None)
    else:
        map_node = None
        map_logical_source = None

    subject_map_label = st.text_input("Enter label for the subject map")
    subject_class_label = st.text_input("Enter subject type")

    data_source = next(st.session_state["g_mapping"].objects(map_logical_source, RML.source), None)   #name of ds file
    if data_source:
        data_source = utils.get_ds_full_path(data_source)   #full path of ds file


    if data_source:
        columns_df = pd.read_csv(data_source)
        column_list = columns_df.columns.tolist()
    else:
        column_list = []

    subject_id = st.selectbox("Select the subject id", column_list)



    save_subject_button = st.button("Save subject")

    a_subject_map_already_exists = next(st.session_state["g_mapping"].objects(map_node, RR.subjectMap), None)

    if map_label and subject_map_label and save_subject_button:
        if a_subject_map_already_exists:
            st.warning(f"The map {map_label} already contains a subject map")
        else:
            utils.add_subject_map(st.session_state["g_mapping"], map_label, subject_map_label, subject_class_label, subject_id)

    st.write("_______________________")



    subject_map_dict = {}
    for map_label, map_node in st.session_state["map_dict"].items():
        data_source = utils.get_data_source_file(st.session_state["g_mapping"], map_node)
        subject_map = next(st.session_state["g_mapping"].objects(map_node, RR.subjectMap), None)
        subject_class = next(st.session_state["g_mapping"].objects(subject_map, RR["class"]), None)
        subject_id = next(st.session_state["g_mapping"].objects(subject_map, RR.template), None)
        if subject_map:
            subject_map = subject_map.rsplit("#",1)[-1]
            subject_class = subject_class.rsplit("#",1)[-1]
            subject_id = subject_id.rsplit("/",1)[-1]
        else:   #if no subject_map has been defined yet for the TriplesMap
            subject_class = None
            subject_id = None
        subject_map_dict[map_label] = [data_source, subject_map, subject_class, subject_id]


    map_df = pd.DataFrame.from_dict(
        subject_map_dict,
        orient="index",
        columns=["data_source_subject_map", "subject_map", "subject_class", "subject_id"]
    ).reset_index().rename(columns={"index": "map_label"})

    # map_df = pd.DataFrame(list(data_source_dict.items()), columns=["Map label", "Data source"])
    st.dataframe(map_df, hide_index=True)


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

        map_list = list(st.session_state["map_dict"].keys())
        map_list.insert(0, "Select a map")


        with col1:
            map_label = st.selectbox("Select a Triples map", map_list)

        if map_label != "Select a map":
            map_node = st.session_state["map_dict"][map_label]
            map_logical_source = next(st.session_state["g_mapping"].objects(map_node, RML.logicalSource), None)
            subject_map = st.session_state["g_mapping"].value(subject=map_node, predicate=RR.subjectMap)
        else:
            map_node = None
            map_logical_source = None
            subject_map = None

        if map_label != "Select a map":
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

            if map_label != "Select a map":
                map_iri = st.session_state["map_dict"][map_label]
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

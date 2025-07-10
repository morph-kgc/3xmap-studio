import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle

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


st.title("Global Configuration")
st.write("")

#initialise session state variables
if "10_option_button" not in st.session_state:
    st.session_state["10_option_button"] = None
if "g_button_option" not in st.session_state:
    st.session_state["g_button_option"] = ""
if "g_mapping" not in st.session_state:
    st.session_state["g_mapping"] = None
if "g_label" not in st.session_state:
    st.session_state["g_label"] = ""
if "candidate_g_label" not in st.session_state:
    st.session_state["candidate_g_label"] = ""
if "overwrite_checkbox" not in st.session_state:
    st.session_state["overwrite_checkbox"] = False
if "overwrite_selection" not in st.session_state:
    st.session_state["overwrite_selection"] = ""
if "save_g_filename" not in st.session_state:
    st.session_state["save_g_filename"] = ""
if "candidate_new_file" not in st.session_state:
    st.session_state["candidate_new_file"] = ""
if "candidate_load_file" not in st.session_state:
    st.session_state["candidate_load_file"] = ""
if "new_ns" not in st.session_state:
    st.session_state["new_ns"] = ""
if "new_prefix" not in st.session_state:
    st.session_state["new_prefix"] = ""
if "save_progress_success" not in st.session_state:
    st.session_state["save_progress_success"] = False
if "export_success" not in st.session_state:
    st.session_state["export_success"] = False
if "export_file" not in st.session_state:
    st.session_state["export_file"] = False
if "save_progress_filename_key" not in st.session_state:
    st.session_state["save_progress_filename_key"] = ""
if "load_success" not in st.session_state:
    st.session_state["load_success"] = ""
if "selected_load_pkl" not in st.session_state:
    st.session_state["selected_load_pkl"] = "Choose a file"


#initialise variables
candidate_g_label = ""
cancel_text = ""
save_text = ""
overwrite_text = ""
save_file_available = False
selected_pkl = ""     #file from where existing graph is loaded
overwrite_checkbox = False
load_file_ready = False


#directories
save_progress_folder = os.path.join(os.getcwd(), "saved_mappings")  #folder to save mappings (pkl)
export_folder = os.path.join(os.getcwd(), "exported_mappings")    #filder to export mappings (ttl and others)
utils.check_directories()


#define on_click functions
def reset_input():    #function to reset input upon click
    st.session_state["candidate_g_label_input"] = ""
    st.session_state["overwrite_checkbox"] = False
    st.session_state["load_file_selector"] = "Choose a file"

def bind_namespace():
    st.session_state["ns_dict"][st.session_state["new_prefix"]] = st.session_state["new_ns"]
    st.session_state["all_ns_dict"][st.session_state["new_prefix"]] = st.session_state["new_ns"]
    st.session_state["g_mapping"].bind(prefix_input, iri_input)  #here we bind the new namespace
    st.session_state["iri_input"] = ""
    st.session_state["prefix_input"] = ""

def save_progress():

    with open(save_progress_file, "wb") as f:
        pickle.dump(st.session_state["g_mapping"], f)

    st.session_state["save_progress_filename_key"] = ""
    st.session_state["save_progress_success"] = True

def export_mapping_to_file():
    st.session_state["g_mapping"].serialize(destination=export_file_path, format=export_format)
    st.session_state["export_file_input"] = ""
    st.session_state["export_success"] = True

def load_mapping():
    st.session_state["g_label"] = st.session_state["candidate_g_label"]
    with open(load_g_file_full_path, "rb") as f:
        st.session_state["g_mapping"] = pickle.load(f)   #we load the mapping
    st.session_state["load_success"] = True


#____________________________________________________________
#PAGE OPTIONS (buttons)

col1,col2,col3,col4 = st.columns(4)

#Option to select g_mapping
with col1:
    if st.button("Select mapping"):
        st.session_state["10_option_button"] = "g"

#Option to configure namespaces
with col2:
    if st.button("Configure namespaces"):
        st.session_state["10_option_button"] = "ns"

#Option to save progress
with col3:
    if st.button("Save progress"):
        st.session_state["10_option_button"] = "sp"

#Option to export mapping
with col4:
    if st.button("Export mapping"):
        st.session_state["10_option_button"] = "em"

st.write("_______________")
#____________________________________________________________


#________________________________________________
#SELECT MAPPING OPTION
if st.session_state["10_option_button"] == "g":

    #options to create new mapping or load an existing one
    col1,col2, col3 = st.columns([2,0.5, 1])
    with col1:
        col1a, col2a = st.columns(2)
        with col1a:
            new_g_button = st.button("Create new mapping")
        with col2a:
            existing_g_button = st.button("Load existing mapping")


    #BUTTONS TO SELECT OPTION - NEW OR EXISTING MAPPING_________________________
    if new_g_button:
        st.session_state["g_button_option"] = "Create new mapping"
    if existing_g_button:
        st.session_state["g_button_option"] = "Load existing mapping"


    #CREATE NEW MAPPING OPTION__________________________________________
    if st.session_state["g_button_option"] == "Create new mapping":

        with col1:
            candidate_g_label = st.text_input("Enter mapping label:", key="candidate_g_label_input")
            if candidate_g_label:
                st.session_state["candidate_g_label"] = candidate_g_label    #just candidate until confirmed

        #A MAPPING HAS NOT BEEN LOADED YET
        if st.session_state["g_mapping"] == None:   #a mapping has not been loaded yet
            if st.session_state["candidate_g_label"]:  #after a new label has been given (so st.session_state["candidate_g_label"] exists)
                with col1:
                    if st.button(f"Confirm {st.session_state["candidate_g_label"]}", on_click=reset_input):
                        st.session_state["g_label"] = st.session_state["candidate_g_label"]   #we consolidate g_label
                        st.session_state["g_mapping"] = Graph()   #we create a new empty mapping
                        st.markdown(f"""
                        <div style="background-color:#d4edda; padding:1em; border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                            ✅ The mapping <b style="color:#007bff;">{st.session_state["g_label"]}</b> has been created!
                        </div>
                        """, unsafe_allow_html=True)

        #A MAPPING IS CURRENTLY LOADED
        else:  #a mapping is currently loaded (ask if overwrite)
            if candidate_g_label:   #after a new label has been given
                st.session_state["candidate_g_label"] = candidate_g_label    #just candidate until confirmed

                with col1:
                    with st.form("overwrite_form"):
                        st.markdown(f"""
                            <div style="background-color:#fff3cd; padding:1em;
                            border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                                ⚠️ The mapping <b style="color:#cc9a06;">{st.session_state["g_label"]}</b> is already loaded! <br>
                                If you continue, it will be overwritten.</div>
                        """, unsafe_allow_html=True)

                        st.write("")

                        # Option labels
                        cancel_text = (f"""CANCEL loading mapping {st.session_state["candidate_g_label"]}   🛑""")
                        save_text = f"""SAVE mapping {st.session_state["g_label"]} first   💾"""
                        overwrite_text = f"""OVERWRITE mapping {st.session_state["g_label"]}  🗑️"""

                        overwrite_options = {
                            "opt_cancel": cancel_text,
                            "opt_save": save_text,
                            "opt_overwrite": overwrite_text
                        }


                        selection = st.radio(        # Widgets inside the form
                            "What would you like to do?",
                            list(overwrite_options.keys()),
                            format_func=lambda x: overwrite_options[x],
                            key="overwrite_selection_radio"
                        )

                        st.markdown("</div>", unsafe_allow_html=True)   # Closing the box

                        submitted = st.form_submit_button("Confirm")   # Submit button

                    if submitted:
                        st.session_state["overwrite_selection"] = st.session_state["overwrite_selection_radio"]

                    with col1:
                        if st.session_state["overwrite_selection"] == "opt_overwrite":
                            confirm_button = st.button(f"""I am sure I want to OVERWRITE
                            mapping {st.session_state["candidate_g_label"]}""", on_click=reset_input)
                        elif st.session_state["overwrite_selection"] == "opt_cancel":
                            confirm_button = st.button(f"""I am sure I want to CANCEL""", on_click=reset_input)
                        elif st.session_state["overwrite_selection"] == "opt_save": #for the save case we need to ask for the filename before confirming
                            save_g_filename = st.text_input(
                            f"Enter the filename to save the mapping {st.session_state["g_label"]} (without extension):")
                            existing_pkl_list = [f for f in os.listdir(save_progress_folder) if f.endswith(".pkl")]
                            if (save_g_filename + ".pkl") in existing_pkl_list:
                                st.markdown(f"""
                                    <div style="background-color:#fff3cd; padding:1em;
                                    border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                                        ⚠️ File <b style="color:#cc9a06;">{save_g_filename + ".pkl"}</b> already exists! <br>
                                        Please, choose a different filename.</div>
                                """, unsafe_allow_html=True)
                            else:
                                st.session_state["save_g_filename"] = save_g_filename
                                if save_g_filename:
                                    confirm_button = st.button(f"""I am sure I want to SAVE
                                     {st.session_state["g_label"]} to file {save_g_filename + ".ttl"}""",
                                      on_click=reset_input)

            if st.session_state["candidate_g_label"] and not candidate_g_label:   #this happens when i have confirmed and fields have been reset

                if st.session_state["overwrite_selection"] == "opt_overwrite":   #OVERWRITE OPTION
                    with col1:
                        st.markdown(f"""
                        <div style="background-color:#d4edda; padding:1em;
                        border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                            ✅ The mapping <b style="color:#007bff;">{st.session_state["candidate_g_label"]}
                            </b> has been created! <br> (and mapping
                            <b style="color:#007bff;"> {st.session_state["g_label"]} </b>
                            has been overwritten).  </div>
                        """, unsafe_allow_html=True)
                    st.session_state["g_label"] = st.session_state["candidate_g_label"]
                    st.session_state["g_mapping"] = Graph()
                    st.session_state["overwrite_selection"] = ""

                elif st.session_state["overwrite_selection"] == "opt_save":   #SAVE OPTION
                    save_current_mapping_file = save_progress_folder + "\\" + st.session_state["save_g_filename"] + ".pkl"
                    with open(save_current_mapping_file, "wb") as f:
                        pickle.dump(st.session_state["g_mapping"], f)
                    with col1:
                        st.markdown(f"""
                        <div style="background-color:#d4edda; padding:1em;
                        border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                            ✅ The mapping <b style="color:#007bff;">{st.session_state["candidate_g_label"]}
                            </b> has been created! <br> (and mapping
                            <b style="color:#007bff;"> {st.session_state["g_label"]} </b>
                            has been saved to file
                            <b style="color:#007bff;">{st.session_state["save_g_filename"]})</b>
                            .  </div>
                        """, unsafe_allow_html=True)
                    st.session_state["g_label"] = st.session_state["candidate_g_label"]
                    st.session_state["g_mapping"] = Graph()
                    st.session_state["overwrite_selection"] = ""

                elif st.session_state["overwrite_selection"] == "opt_cancel": #cancel option
                    with col1:
                        st.markdown(f"""
                            <div style="background-color:#fff3cd; padding:1em;
                            border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                                ⚠️ The mapping <b style="color:#cc9a06;">{st.session_state["candidate_g_label"]}</b>
                                has NOT been created! <br>
                                You are still working with mapping
                                <b style="color:#cc9a06;">{st.session_state["g_label"]}</b>. </div>
                        """, unsafe_allow_html=True)
                    st.session_state["overwrite_selection"] = ""


    #LOAD EXISTING MAPPING OPTION__________________________________________________________
    elif st.session_state["g_button_option"] == "Load existing mapping":
        save_g_full_path = utils.get_g_full_path(st.session_state["save_g_filename"])

        with col1:
            candidate_g_label = st.text_input("Enter mapping label:", key="candidate_g_label_input")
            if candidate_g_label:
                st.session_state["candidate_g_label"] = candidate_g_label    #just candidate until confirmed
            pkl_list = [f for f in os.listdir(save_progress_folder) if f.endswith(".pkl")]
            pkl_list.insert(0, "Choose a file") # Add a placeholder option
            with col1:
                selected_load_pkl = st.selectbox(f"""Select the file where the mapping
                {st.session_state["candidate_g_label"]} is saved:""", pkl_list, key="load_file_selector")
                if selected_load_pkl != "Choose a file":
                    st.session_state["selected_load_pkl"] = selected_load_pkl
            if st.session_state["selected_load_pkl"] != "Choose a file":
                load_g_file_full_path = save_progress_folder + "\\" + st.session_state["selected_load_pkl"]
                load_file_ready = True
                with open(load_g_file_full_path, "rb") as f:
                    st.session_state["candidate_g_mapping"] = pickle.load(f)   #we load the mapping as a candidate (ultil confirmed)


        #A MAPPING HAS NOT BEEN LOADED YET
        if st.session_state["g_mapping"] == None:   #a mapping has not been loaded yet
            if st.session_state["candidate_g_label"] and load_file_ready:  #after a new label has been given (so st.session_state["candidate_g_label"] exists)
                with col1:
                    if st.button(f"Confirm {st.session_state["candidate_g_label"]}", on_click=reset_input):
                        st.session_state["g_label"] = st.session_state["candidate_g_label"]   #we consolidate g_label
                        st.session_state["g_mapping"] = st.session_state["candidate_g_mapping"]
                        st.markdown(f"""
                        <div style="background-color:#d4edda; padding:1em; border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                            ✅ The mapping <b style="color:#007bff;">{st.session_state["g_label"]}</b> has been loaded
                            from file <b style="color:#007bff;">{st.session_state["selected_load_pkl"]}</b>!
                        </div>
                        """, unsafe_allow_html=True)


        #A MAPPING IS CURRENTLY LOADED
        else:  #a mapping is currently loaded (ask if overwrite)
            if candidate_g_label and selected_load_pkl != "Choose a file":   #after a new label has been given
                st.session_state["candidate_g_label"] = candidate_g_label    #just candidate until confirmed

                with col1:
                    with st.form("overwrite_form"):
                        st.markdown(f"""
                            <div style="background-color:#fff3cd; padding:1em;
                            border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                                ⚠️ The mapping <b style="color:#cc9a06;">{st.session_state["g_label"]}</b> is already loaded! <br>
                                If you continue, it will be overwritten.</div>
                        """, unsafe_allow_html=True)

                        st.write("")

                        # Option labels
                        cancel_text = (f"""CANCEL loading mapping {st.session_state["candidate_g_label"]}   🛑""")
                        save_text = f"""SAVE mapping {st.session_state["g_label"]} first   💾"""
                        overwrite_text = f"""OVERWRITE mapping {st.session_state["g_label"]}  🗑️"""

                        overwrite_options = {
                            "opt_cancel": cancel_text,
                            "opt_save": save_text,
                            "opt_overwrite": overwrite_text
                        }


                        selection = st.radio(        # Widgets inside the form
                            "What would you like to do?",
                            list(overwrite_options.keys()),
                            format_func=lambda x: overwrite_options[x],
                            key="overwrite_selection_radio"
                        )

                        st.markdown("</div>", unsafe_allow_html=True)   # Closing the box

                        submitted = st.form_submit_button("Confirm")   # Submit button

                    if submitted:
                        st.session_state["overwrite_selection"] = st.session_state["overwrite_selection_radio"]

                    with col1:
                        if st.session_state["overwrite_selection"] == "opt_overwrite":
                            confirm_button = st.button(f"""I am sure I want to OVERWRITE
                            mapping {st.session_state["candidate_g_label"]}""", on_click=reset_input)
                        elif st.session_state["overwrite_selection"] == "opt_cancel":
                            confirm_button = st.button(f"""I am sure I want to CANCEL""", on_click=reset_input)
                        elif st.session_state["overwrite_selection"] == "opt_save": #for the save case we need to ask for the filename before confirming
                            save_g_filename = st.text_input(
                            f"Enter the filename to save the mapping {st.session_state["g_label"]} (without extension):")
                            existing_pkl_list = [f for f in os.listdir(save_progress_folder) if f.endswith(".pkl")]
                            if (save_g_filename + ".pkl") in existing_pkl_list:
                                st.markdown(f"""
                                    <div style="background-color:#fff3cd; padding:1em;
                                    border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                                        ⚠️ File <b style="color:#cc9a06;">{save_g_filename + ".pkl"}</b> already exists! <br>
                                        Please, choose a different filename.</div>
                                """, unsafe_allow_html=True)
                            else:
                                st.session_state["save_g_filename"] = save_g_filename
                                if save_g_filename:
                                    confirm_button = st.button(f"""I am sure I want to SAVE
                                     {st.session_state["g_label"]} to file {save_g_filename + ".ttl"}""",
                                      on_click=reset_input)

            if st.session_state["candidate_g_label"] and not candidate_g_label:   #this happens when i have confirmed and fields have been reset

                if st.session_state["overwrite_selection"] == "opt_overwrite":   #OVERWRITE OPTION
                    with col1:
                        st.markdown(f"""
                        <div style="background-color:#d4edda; padding:1em;
                        border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                            ✅ The mapping <b style="color:#007bff;">{st.session_state["candidate_g_label"]}
                            </b> has been created! <br> (and mapping
                            <b style="color:#007bff;"> {st.session_state["g_label"]} </b>
                            has been overwritten).  </div>
                        """, unsafe_allow_html=True)
                    st.session_state["g_label"] = st.session_state["candidate_g_label"]
                    st.session_state["g_mapping"] = st.session_state["candidate_g_mapping"]
                    st.session_state["overwrite_selection"] = ""

                elif st.session_state["overwrite_selection"] == "opt_save":   #SAVE OPTION
                    save_current_mapping_file = save_progress_folder + "\\" + st.session_state["save_g_filename"] + ".pkl"
                    with open(save_current_mapping_file, "wb") as f:
                        pickle.dump(st.session_state["g_mapping"], f)
                    with col1:
                        st.markdown(f"""
                        <div style="background-color:#d4edda; padding:1em;
                        border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                            ✅ The mapping <b style="color:#007bff;">{st.session_state["candidate_g_label"]}
                            </b> has been created! <br> (and mapping
                            <b style="color:#007bff;"> {st.session_state["g_label"]} </b>
                            has been saved to file
                            <b style="color:#007bff;">{st.session_state["save_g_filename"]})</b>
                            .  </div>
                        """, unsafe_allow_html=True)
                    st.session_state["g_label"] = st.session_state["candidate_g_label"]
                    st.session_state["g_mapping"] = st.session_state["candidate_g_mapping"]
                    st.session_state["overwrite_selection"] = ""

                elif st.session_state["overwrite_selection"] == "opt_cancel": #cancel option
                    with col1:
                        st.markdown(f"""
                            <div style="background-color:#fff3cd; padding:1em;
                            border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                                ⚠️ The mapping <b style="color:#cc9a06;">{st.session_state["candidate_g_label"]}</b>
                                has NOT been created! <br>
                                You are still working with mapping
                                <b style="color:#cc9a06;">{st.session_state["g_label"]}</b>. </div>
                        """, unsafe_allow_html=True)
                    st.session_state["overwrite_selection"] = ""




    st.write("This is for debugging purposes and will be deleted")
    st.write("g_label: ", st.session_state["g_label"])

    st.write(f"Graph has {len(st.session_state["g_mapping"])} triples")
    for s, p, o in list(st.session_state["g_mapping"])[:5]:  # show first 5 triples
        st.write(f"{s} -- {p} --> {o}")

    with col3:
        if st.session_state["g_label"]:
            st.markdown(f"""
            <div style="background-color:#e6e6fa; padding:1em; border-radius:5px; color:#2a0134; border:1px solid #511D66;">
                ☑️ You are currently working with mapping
                <b style="color:#511D66;">{st.session_state["g_label"]}</b>.
            </div>
            """, unsafe_allow_html=True)


        else:
            st.markdown(f"""
            <div style="background-color:#e6e6fa; padding:1em; border-radius:5px; color:#2a0134; border:1px solid #511D66;">
                ✖️ <b style="color:#511D66;">No mapping</b> has been loaded yet.
            </div>
            """, unsafe_allow_html=True)



#_______________________________________________________

#________________________________________________
#ADD NAMESPACE
#Here we build a dictionary that will store the Namespaces
#it will contain predefined namespaces, along with the ones the user defines
#HERE I want to also give an option to show current namespaces

if st.session_state["10_option_button"] == "ns":   #ns button selected

    if st.session_state["g_mapping"] == None:
        st.error("❗ You need to create or load a mapping.")
        st.stop()

    if "ns_dict" not in st.session_state:
        st.session_state["ns_dict"] = utils.get_predefined_ns_dict()   #initial dictionary with predefined namespaces, custom ns will be added
    if "all_ns_dict" not in st.session_state:
        st.session_state["all_ns_dict"] = {}   #dictionary with all bound namespaces (includes the ones which are bound by default)

    for prefix, ns in st.session_state["ns_dict"].items():   #we bind the predefined ns
        st.session_state["g_mapping"].bind(prefix, ns)

    col1,col2 = st.columns([3,1])

    with col2:
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

    with col1:
        col1a, col1b = st.columns([2,1])


        with col1a:
            iri_input = st.text_input("Enter an IRI for the new namespace", key="iri_input")
            if iri_input:
                st.session_state["new_ns"] = iri_input

        with col1b:
            if iri_input:
                valid_iri_input = False
                if not utils.is_valid_iri(iri_input):
                    st.error("❌ Invalid IRI: Please check scheme and characters")
                elif iri_input in st.session_state["ns_dict"].values():
                    st.error("❌ IRI already in use")
                else:
                    st.success("✅ Valid IRI")
                    valid_iri_input = True

    with col1:
        col1a, col1b = st.columns([2,1])
        with col1a:
            prefix_input = st.text_input("Enter prefix: ", key = "prefix_input")
        if prefix_input:
            st.session_state["new_prefix"] = prefix_input

        with col1b:
            if prefix_input:
                valid_prefix_input = False
                if prefix_input in st.session_state["ns_dict"]:
                    st.error("❌ Prefix already in use")
                else:
                    st.success("✅ Valid prefix")
                    valid_prefix_input = True


    if iri_input and prefix_input:
        if valid_iri_input and valid_prefix_input:
            save_new_ns = st.button("Bind namespace", on_click=bind_namespace)



    ns_df = pd.DataFrame(list(st.session_state["ns_dict"].items()), columns=["Prefix", "Namespace"])
    st.dataframe(ns_df, hide_index=True)
    st.write("")


    col1,col2 = st.columns(2)
    with col1:
        show_all_ns = st.button("Show all bound namespaces (including predefined ns)")
    if show_all_ns:
        with col2:
            st.button("Hide")
        st.session_state["all_ns_dict"] = dict(st.session_state["g_mapping"].namespace_manager.namespaces())
        all_ns_df = pd.DataFrame(list(st.session_state["all_ns_dict"].items()), columns=["Prefix", "Namespace"])
        st.dataframe(all_ns_df, hide_index=True)

#_____________________________________________


#________________________________________________
#SAVE PROGRESS OPTION
#HERE - NOT WORKING
if st.session_state["10_option_button"] == "sp":

    if st.session_state["g_mapping"] == None:
        st.error("❗ You need to create or load a mapping.")
        st.stop()

    col1, col2 = st.columns(2)

    with col2:
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

        existing_save_progress_file_list = [f for f in os.listdir(save_progress_folder) if f.endswith(".pkl")]

    with col1:
        save_progress_filename = st.text_input(
        f"Enter the filename to save the mapping {st.session_state["g_label"]} (without extension):", key="save_progress_filename_key")
        if save_progress_filename and (save_progress_filename + ".pkl") in existing_save_progress_file_list:
            st.warning(f"""The file {save_progress_filename} is already in use. Are you sure you want to
            overwrite it?""")
            overwrite_checkbox = st.checkbox(f"""I am I want to overwrite it""", key="overwrite_checkbox")
        else:
            overwrite_checkbox = True

        save_progress_file = save_progress_folder + "\\" + save_progress_filename + ".pkl"

        if overwrite_checkbox:
            if save_progress_filename:
                st.session_state["save_progress_filename"] = save_progress_filename + ".pkl"
                confirm_button = st.button("Save progress", on_click=save_progress)

    if st.session_state["save_progress_success"]:
        with col1:
            st.success(f"The mapping {st.session_state["g_label"]} has been saved to {st.session_state["save_progress_filename"]}")
            st.session_state["save_progress_success"] = False

        #     st.success(f"""The mapping {st.session_state["candidate_g_label"]}
        #      has been saved to file {st.session_state["save_g_filename"]}.""")

#_____________________________________________

#________________________________________________
#EXPORT OPTION

if st.session_state["10_option_button"] == "em":

    if st.session_state["g_mapping"] == None:
        st.error("❗ You need to create or load a mapping.")
        st.stop()

    col1,col2 = st.columns([2,1])

    with col2:
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

    export_format_list = ["turtle", "longturtle", "n3", "ntriples", "nquads", "trigs",
                        "json-ld", "xml", "pretty-xml", "trix", "hext", "patch"
                        ]

    export_extension_dict = {"turtle": ".ttl", "longturtle": ".ttl", "n3": ".n3",
    "ntriples": ".nt", "nquads": "nq", "trig": ".trig", "json-ld": ".jsonld",
    "xml": ".xml", "pretty-xml": ".xml", "trix": ".trix", "hext": ".hext",
    "patch": ".patch"}

    valid_extensions = tuple(export_extension_dict.values())

    with col1:
        export_format = st.selectbox("Select format for export file", export_format_list, key="export_format")
    export_extension = export_extension_dict[export_format]

    with col1:
        export_file_input = st.text_input("Enter export filename (without extension)", key="export_file_input")
    export_file = export_file_input + export_extension

    if export_file_input:
        st.session_state["export_file"] = export_file
    export_file_path = "exported_mappings/" + export_file

    existing_export_file_list = [
        f for f in os.listdir(export_folder)
        if f.endswith(valid_extensions)
        ]

    with col1:
        if export_file_input and export_file in existing_export_file_list:
            st.warning(f"""The file {export_file} is already in use. Are you sure you want to
            overwrite it?""")
            overwrite_checkbox = st.checkbox(f"""I am sure I want to overwrite it""", key="overwrite_checkbox")
        else:
            overwrite_checkbox = True

    if export_file_input and overwrite_checkbox:
        with col1:
            st.button("Export mapping to file", on_click=export_mapping_to_file)

    if st.session_state["export_success"]:
        with col1:
            st.success(f"The mapping {st.session_state["g_label"]} has been saved to {st.session_state["export_file"]}")
            st.session_state["export_success"] = False



#_____________________________________________

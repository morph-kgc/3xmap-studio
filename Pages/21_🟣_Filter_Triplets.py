import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace
import utils

file_path = utils.get_file_path()    #get path to the selected graph
g = utils.get_selected_graph()     #get selected graph


st.title("Filter Triplets")

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown(f"""<div style="line-height: 1.5;"><span style="font-size:14px;">
    ▸ Here you can browse graph info. <br>
    ▸ Enter the field you want and leave the rest blank, I'll show you everything that matches. <br>
    ▸ The input will be taken from the textbox by default,
    or from the selectbox otherwise <br>
    ▸If no valid input is given it will be read as blank.<br>
    &nbsp
    </span></div>""", unsafe_allow_html=True)


with col2:
    utils.show_file_path_success()  #show warning indicating the graph file that has been selected

st.write("_________________________")

#___________________________________________
#DICTIONARIES AND LISTS

subject_uri_prefixname_dict = utils.get_uri_prefixname_dict("subject")
predicate_uri_prefixname_dict = utils.get_uri_prefixname_dict("predicate")
object_uri_prefixname_dict = utils.get_uri_prefixname_dict("object")

subject_name_uri_dict = utils.get_name_uri_dict("subject")
predicate_name_uri_dict = utils.get_name_uri_dict("predicate")
object_name_uri_dict = utils.get_name_uri_dict("object")

subject_prefixname_uri_dict = utils.get_prefixname_uri_dict("subject")
predicate_prefixname_uri_dict = utils.get_prefixname_uri_dict("predicate")
object_prefixname_uri_dict = utils.get_prefixname_uri_dict("object")

subject_uri_list = utils.get_uri_list("subject") #list to store all subject uris (in string form)
predicate_uri_list = utils.get_uri_list("predicate")
object_uri_list = utils.get_uri_list("object")

subject_duplicate_list = utils.get_duplicate_name_list("subject")
predicate_duplicate_list = utils.get_duplicate_name_list("predicate")
object_duplicate_list = utils.get_duplicate_name_list("object")

subject_name_list = utils.get_name_list("subject")
predicate_name_list = utils.get_name_list("predicate")
object_name_list = utils.get_name_list("object")

subject_Literal_list = utils.get_Literal_list("subject")
predicate_Literal_list = [] #predicates cannot be Literals
object_Literal_list = utils.get_Literal_list("object")

subject_prefixname_name_dict = utils.get_prefixname_name_dict("subject")     #{prefix:name : name}
predicate_prefixname_name_dict = utils.get_prefixname_name_dict("predicate")
object_dic_prefixname_name_dict = utils.get_prefixname_name_dict("object")
#___________________________________________



col1, col2, col3 = st.columns(3)

#_________________________________________________
#CHOOSING SUBJECT

with col1:
        custom_input = st.text_input("Enter a subject (or choose from list): ", key = "s_input")

#textbox input -> we check if custom_input is valid (can be a name, a prefix:name or an uri)
if (custom_input in subject_prefixname_uri_dict or
custom_input in subject_name_uri_dict or
custom_input in subject_uri_list or
custom_input in subject_Literal_list):
    custom_input_valid = True
else:
    custom_input_valid = False  #HERE need to empty box

with col1:
    #selectbox input
    options = ["All"] + list(utils.get_name_uri_dict_w_literals("subject").keys())
    selected_option = st.selectbox("or choose from list", options, index=None, label_visibility="collapsed")

if selected_option:  #index to monitor if input has been given in selectbox
    s_index_sb = "selectbox"
else:
    s_index_sb = ""

#__________________________________________________
#INPUT FROM TEXTBOX -> Check valid or invalid

s_index = ""

#input is a valid prefix:name or uri (UNIQUE)
if not custom_input:
    custom_input_valid = False
    s_index = "case_0"    #index to monitor if input has been given in textbox and case

#input is a valid prefix:name or uri (UNIQUE)
if (custom_input in subject_prefixname_uri_dict or
custom_input in subject_uri_list):
    custom_input_valid = True
    s_index = "case_1"    #index to monitor if input has been given in textbox and case

#input is a name, but it is not duplicated (UNIQUE)
if (custom_input in subject_name_list and not
custom_input in subject_duplicate_list
and not custom_input in subject_Literal_list):
    custom_input_valid = True
    s_index = "case_1"

#input is a literal which is not duplicated as a name
if (custom_input in subject_Literal_list and not
custom_input in subject_name_list):
    custom_input_valid = True
    s_index = "case_1"

#input is a name which is duplicated (but there is no Literal with this name)
if (custom_input in subject_duplicate_list and
custom_input not in subject_Literal_list):
    custom_input_valid = False
    s_index = "case_2"

#input is a Literal, but there is at least an uri with the same name
if (custom_input in subject_Literal_list and
custom_input in subject_name_list):
    custom_input_valid = True
    s_index = "case_3"

if (custom_input and custom_input not in subject_prefixname_uri_dict and
custom_input not in subject_uri_list and
custom_input not in subject_name_list and
custom_input not in subject_Literal_list):
    custom_input_valid = False
    s_index = "case_4"

if not custom_input:
    custom_input_valid = False
#________________________________________

#__________________________________________________
#SELECT INPUT EITHER FROM TEXTBOX OR SELECTBOX
#by default we read the input from textbox
#or from the selectbox if no valid input is given in the textbox
#if no input is given, "All" is selected
if custom_input_valid:
    subject_input = custom_input   #a valid textbox input was given
elif selected_option:
    subject_input = selected_option  #input from the selectbox
else:
    subject_input = "All"       #no valid input given

#_____________________________________________
#WE SHOW INFO ON INPUT (WHICH INPUT IS SELECTED AND WHY, CORRESPONDING URI, ETC)
#For this, we define a function

def show_input_info(node_type):

    if node_type == "subject":
        index_tb = s_index   #textbox index
        index_sb = s_index_sb    #selectbox index
    elif node_type == "predicate":
        index_tb = p_index
        index_sb = p_index_sb
    elif node_type == "object":
        index_tb = o_index
        index_sb = o_index_sb

    if index_tb == "case_0":    #no input given in textbox
        if not index_sb:
            st.markdown(
            """ <div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
            No input in TEXTBOX.<br>  </span></div>""",
            unsafe_allow_html=True)
            st.markdown(
            """ <div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
            No input in SELECTBOX.<br>  </span></div>""",
            unsafe_allow_html=True)
            st.markdown(
            """<div style="line-height: 0.8;"><span style="color:grey; font-size:14px;">
            <br> → NO INPUT GIVEN (blank)</span></div>""",
            unsafe_allow_html=True)
            st.write("")
        else:
            st.markdown(
            """ <div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
            No input in TEXTBOX.<br>   </span></div>""",
            unsafe_allow_html=True)
            st.markdown(
            """ <div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
            Valid input in SELECTBOX.<br>  </span></div>""",
            unsafe_allow_html=True)
            st.markdown(
            """<div style="line-height: 0.8;"><span style="color:green; font-size:14px;">
            <br> → SELECTING INPUT FROM SELECTBOX </span></div>""",
            unsafe_allow_html=True)
            st.write("")


    if index_tb == "case_1":  #valid input from textbox, no warnings
        st.markdown(
        """ <div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
        Input in TEXTBOX is valid.<br>   </span></div>""",
        unsafe_allow_html=True)
        if index_sb == "selectbox":
            st.markdown(
            """ <div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
            Ignoring input from SELECTBOX.<br>  </span></div>""",
            unsafe_allow_html=True)
        else:
            st.markdown(
            """ <div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
            No input in SELECTBOX.<br>  </span></div>""",
            unsafe_allow_html=True)
        st.markdown(
        """<div style="line-height: 0.8;"><span style="color:green; font-size:14px;">
        <br> → SELECTING INPUT FROM TEXTBOX </span></div>""",
        unsafe_allow_html=True)
        st.write("")

    if index_tb == "case_2":     #input from textbox not unique
        st.markdown(
        """ <div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
        Input in TEXTBOX is not unique → Ignoring (add prefix to use). </span></div>""",
        unsafe_allow_html=True)
        if index_sb == "selectbox":
            st.markdown(
            """ <div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
            Valid input in SELECTBOX.<br>   </span></div>""",
            unsafe_allow_html=True)
            st.markdown(
            """ <div style="line-height: 0.8;"><span style="color:green; font-size:14px;">
            <br> → SELECTING INPUT FROM SELECTBOX (textbox ignored) </span></div>""",
            unsafe_allow_html=True)
            st.write("")
        else:
            st.markdown(
            """ <div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
            No input in SELECTBOX.<br>  </span></div>""",
            unsafe_allow_html=True)
            st.markdown(
            """ <div style="line-height: 0.8;"><span style="color:grey; font-size:14px;">
            <br> → NO VALID INPUT GIVEN (blank)</span></div>""",
            unsafe_allow_html=True)
            st.write("")


    if index_tb == "case_3":    #valid input from textbox, warning input not unique, selecting Literal
        st.markdown(
        """ <div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
        Input in TEXTBOX is not unique → Selecting Literal.
        </span></div>""",
        unsafe_allow_html=True)
        if index_sb == "selectbox":
            st.markdown(
            """ <div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
            Ignoring input from SELECTBOX.<br>  </span></div>""",
            unsafe_allow_html=True)
        else:
            st.markdown(
            """ <div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
            No input in SELECTBOX.<br>  </span></div>""",
            unsafe_allow_html=True)
        st.markdown(
        """<div style="line-height: 0.8;"><span style="color:green; font-size:14px;">
        <br>→ SELECTING INPUT FROM TEXTBOX (Literal) </span></div>""",
        unsafe_allow_html=True)
        st.write("")


    if index_tb == "case_4":    #input from textbox not valid
        st.markdown(
        """ <div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
        Input in textbox is not valid. </span></div>""",
        unsafe_allow_html=True)
        if index_sb == "selectbox":
            st.markdown(
            """ <div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
            Valid input given in SELECTBOX.<br>  </span></div>""",
            unsafe_allow_html=True)
            st.markdown(
            """<span style="color:green; font-size:14px;">
            <br>→ SELECTING INPUT FROM SELECTBOX (textbox ignored) </span>""",
            unsafe_allow_html=True)
            st.write("")
        else:
            st.markdown(
            """ <div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
            No input in SELECTBOX.<br>  </span></div>""",
            unsafe_allow_html=True)
            st.markdown(
            """ <div style="line-height: 0.8;"><span style="color:orange; font-size:14px;">
            <br> → NO VALID INPUT GIVEN (blank)</span></div>""",
            unsafe_allow_html=True)
            st.write("")

with col1:
    show_input_info("subject")
#_________________________________________________



#_________________________________________________
#WE GET THE URI OF THE SELECTED SUBJECT (or Literal)
#If no valid input is given (All option) we get None
if subject_input == "All":
    selected_subject = None      #no valid input -> blank
elif subject_input in subject_Literal_list:
    selected_subject = Literal(subject_input)        #input in the shape Literal
elif subject_input in subject_name_uri_dict:
    selected_subject = subject_name_uri_dict[subject_input]  #input in the shape name
elif subject_input in subject_prefixname_uri_dict:
     selected_subject = subject_prefixname_uri_dict[subject_input] #input in the shape prefix:name
elif subject_input in subject_uri_list:
    selected_subject = subject_input        #input in the shape URIRef

#_______________________________________________


#_________________________________________________
#CHOOSING PREDICATE
with col2:
        custom_input = st.text_input("Enter a predicate (or choose from list): ", key = "p_input")

if (custom_input in predicate_prefixname_uri_dict or
custom_input in predicate_name_uri_dict or
custom_input in predicate_uri_list or
custom_input in predicate_Literal_list):
    custom_input_valid = True
else:
    custom_input_valid = False  #HERE need to empty box

#selectbox input
with col2:
    options = ["All"] + list(utils.get_name_uri_dict_w_literals("predicate").keys())
    selected_option = st.selectbox("or choose from list", options, index=None, label_visibility="collapsed")

if selected_option:  #index to monitor if input has been given in selectbox
    p_index_sb = "selectbox"
else:
    p_index_sb = ""

#__________________________________________________
#INPUT FROM TEXTBOX -> Check valid or invalid

p_index = ""

#input is a valid prefix:name or uri (UNIQUE)
if not custom_input:
    custom_input_valid = False
    p_index = "case_0"    #index to monitor if input has been given in textbox and case

#input is a valid prefix:name or uri (UNIQUE)
if (custom_input in predicate_prefixname_uri_dict or
custom_input in predicate_uri_list):
    custom_input_valid = True
    p_index = "case_1"    #index to monitor if input has been given in textbox and case

#input is a name, but it is not duplicated (UNIQUE)
if (custom_input in predicate_name_list and not
custom_input in predicate_duplicate_list
and not custom_input in predicate_Literal_list):
    custom_input_valid = True
    p_index = "case_1"

#input is a literal which is not duplicated as a name
if (custom_input in predicate_Literal_list and not
custom_input in predicate_name_list):
    custom_input_valid = True
    p_index = "case_1"

#input is a name which is duplicated (but there is no Literal with this name)
if (custom_input in predicate_duplicate_list and
custom_input not in predicate_Literal_list):
    custom_input_valid = False
    p_index = "case_2"

#input is a Literal, but there is at least an uri with the same name
if (custom_input in predicate_Literal_list and
custom_input in predicate_name_list):
    custom_input_valid = True
    p_index = "case_3"

if (custom_input and custom_input not in predicate_prefixname_uri_dict and
custom_input not in predicate_uri_list and
custom_input not in predicate_name_list and
custom_input not in predicate_Literal_list):
    custom_input_valid = False
    p_index = "case_4"

if not custom_input:
    custom_input_valid = False

#________________________________________

#__________________________________________________
#SELECT INPUT EITHER FROM TEXTBOX OR SELECTBOX
#by default we read the input from textbox
#or from the selectbox if no valid input is given in the textbox
#if no input is given, "All" is selected
if custom_input_valid:
    predicate_input = custom_input   #a valid textbox input was given
elif selected_option:
    predicate_input = selected_option  #input from the selectbox
else:
    predicate_input = "All"       #no valid input given

#_____________________________________________
#WE SHOW INFO ON INPUT (WHICH INPUT IS SELECTED AND WHY, CORRESPONDING URI, ETC)
#For this, we use already defined function

with col2:
    show_input_info("predicate")
#_________________________________________________



#_________________________________________________
#WE GET THE URI OF THE SELECTED predicate (or Literal)
#If no valid input is given (All option) we get None
if predicate_input == "All":
    selected_predicate = None
elif predicate_input in predicate_name_uri_dict:
    selected_predicate = predicate_name_uri_dict[predicate_input]  #input in the shape name
elif predicate_input in predicate_prefixname_uri_dict:
     selected_predicate = predicate_prefixname_uri_dict[predicate_input] #input in the shape prefix:name
elif predicate_input in predicate_uri_list:
    selected_predicate = predicate_input        #input in the shape URIRef
elif predicate_input in predicate_Literal_list:
    selected_predicate = predicate_input        #input in the shape Literal
else:
    selected_predicate = None
#_______________________________________________

#_________________________________________________
#CHOOSING OBJECT
with col3:
        custom_input = st.text_input("Enter an object (or choose from list): ", key = "o_input")

if (custom_input in object_prefixname_uri_dict or
custom_input in object_name_uri_dict or
custom_input in object_uri_list or
custom_input in object_Literal_list):
    custom_input_valid = True
else:
    custom_input_valid = False  #HERE need to empty box

#selectbox input
with col3:
    options = ["All"] + list(utils.get_name_uri_dict_w_literals("object").keys())
    selected_option = st.selectbox("or choose from list", options, index=None, label_visibility="collapsed")

if selected_option:  #index to monitor if input has been given in selectbox
    o_index_sb = "selectbox"
else:
    o_index_sb = ""

#__________________________________________________
#INPUT FROM TEXTBOX -> Check valid or invalid

o_index = ""

#input is a valid prefix:name or uri (UNIQUE)
if not custom_input:
    custom_input_valid = False
    o_index = "case_0"    #index to monitor if input has been given in textbox and case

#input is a valid prefix:name or uri (UNIQUE)
if (custom_input in object_prefixname_uri_dict or
custom_input in object_uri_list):
    custom_input_valid = True
    o_index = "case_1"    #index to monitor if input has been given in textbox and case

#input is a name, but it is not duplicated (UNIQUE)
if (custom_input in object_name_list and not
custom_input in object_duplicate_list
and not custom_input in object_Literal_list):
    custom_input_valid = True
    o_index = "case_1"

#input is a literal which is not duplicated as a name
if (custom_input in object_Literal_list and not
custom_input in object_name_list):
    custom_input_valid = True
    o_index = "case_1"

#input is a name which is duplicated (but there is no Literal with this name)
if (custom_input in object_duplicate_list and
custom_input not in object_Literal_list):
    custom_input_valid = False
    o_index = "case_2"

#input is a Literal, but there is at least an uri with the same name
if (custom_input in object_Literal_list and
custom_input in object_name_list):
    custom_input_valid = True
    o_index = "case_3"

if (custom_input and custom_input not in object_prefixname_uri_dict and
custom_input not in object_uri_list and
custom_input not in object_name_list and
custom_input not in object_Literal_list):
    custom_input_valid = False
    o_index = "case_4"

if not custom_input:
    custom_input_valid = False

#________________________________________

#__________________________________________________
#SELECT INPUT EITHER FROM TEXTBOX OR SELECTBOX
#by default we read the input from textbox
#or from the selectbox if no valid input is given in the textbox
#if no input is given, "All" is selected
if custom_input_valid:
    object_input = custom_input   #a valid textbox input was given
elif selected_option:
    object_input = selected_option  #input from the selectbox
else:
    object_input = "All"       #no valid input given

#_____________________________________________
#WE SHOW INFO ON INPUT (WHICH INPUT IS SELECTED AND WHY, CORRESPONDING URI, ETC)
#For this, we use already defined function

with col3:
    show_input_info("object")
#_________________________________________________



#_________________________________________________
#WE GET THE URI OF THE SELECTED object (or Literal)
#If no valid input is given (All option) we get None
if object_input == "All":
    selected_object = None
elif object_input in object_name_uri_dict:
    selected_object = object_name_uri_dict[object_input]  #input in the shape name
elif object_input in object_prefixname_uri_dict:
     selected_object = object_prefixname_uri_dict[object_input] #input in the shape prefix:name
elif object_input in object_uri_list:
    selected_object = object_input        #input in the shape URIRef
elif object_input in object_Literal_list:
    selected_object = object_input        #input in the shape Literal
else:
    selected_object = None
#_____________________________________________


#_____________________________________________
#SHOWING SELECTION
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
    f"""<div style="border: 1px solid green; padding: 10px; border-radius: 5px;">
    You selected: <span style="color:green;">{subject_input}</span></div>""",
    unsafe_allow_html=True)
    if (not "http:" in subject_input and not subject_input == "All"
    and not subject_input in subject_Literal_list):   #we show the uri if given input is not uri or All
        st.markdown(
        f"""<div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
        Corresponding to URI:  <span style="color:blue;">{selected_subject}</span></div>""",
        unsafe_allow_html=True)
    if subject_input in subject_Literal_list:
        st.markdown(
        f"""<div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
        Selected subject is a Literal</div>""",
        unsafe_allow_html=True)

with col2:
    st.markdown(
    f"""<div style="border: 1px solid green; padding: 10px; border-radius: 5px;">
    You selected: <span style="color:green;">{predicate_input}</span></div>""",
    unsafe_allow_html=True)
    if (not "http:" in predicate_input and not predicate_input == "All"
    and not predicate_input in predicate_Literal_list):   #we show the uri if given input is not uri or All
        st.markdown(
        f"""<div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
        Corresponding to URI:  <span style="color:blue;">{selected_predicate}</span></div>""",
        unsafe_allow_html=True)
    if predicate_input in predicate_Literal_list:
        st.markdown(
        f"""<div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
        Selected predicate is a Literal</div>""",
        unsafe_allow_html=True)


with col3:
    st.markdown(
    f"""<div style="border: 1px solid green; padding: 10px; border-radius: 5px;">
    You selected: <span style="color:green;">{object_input}</span></div>""",
    unsafe_allow_html=True)
    if (not "http:" in object_input and not object_input == "All"
    and not object_input in object_Literal_list):   #we show the uri if given input is not uri or All
        st.markdown(
        f"""<div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
        Corresponding to URI:  <span style="color:blue;">{selected_object}</span></div>""",
        unsafe_allow_html=True)
    if object_input in object_Literal_list:
        st.markdown(
        f"""<div style="line-height: 0.8;"><span style="color:grey; font-size:12px;">
        Selected object is a Literal</div>""",
        unsafe_allow_html=True)


st.write("")
st.write("")

# #____________________________________________________
# #FINDING ALL TRIPLETS THAT MATCH
col1, col2 = st.columns([2, 1])

with col2:
    display_select_list= ["Name", "Prefix:Name", "Full URI"]
    display_selection = st.radio("1️⃣ How do you want the info displayed?:", display_select_list)
    filter_button = st.button("Filter")



with col1:
    with st.container(border=True):

        if filter_button and display_selection == "Name":
            for s, p, o in g.triples((selected_subject, selected_predicate, selected_object)):
                if isinstance(s, URIRef):
                    subject_output = subject_uri_prefixname_dict[s]    #convert uri to prefix:name
                    subject_output = subject_prefixname_name_dict[subject_output]   #convert prefix:name to name
                else:
                    subject_output = s
                if isinstance(p, URIRef):
                    predicate_output = predicate_uri_prefixname_dict[p]
                    predicate_output = predicate_prefixname_name_dict[predicate_output]
                else:
                    predicate_output = p
                if isinstance(o, URIRef):
                        object_output = object_uri_prefixname_dict[o]
                        object_output = object_dic_prefixname_name_dict[object_output]
                else:
                    object_output = o
                st.write(f"🔹 {subject_output} → {predicate_output} → {object_output}")

        if filter_button and display_selection == "Prefix:Name":
            for s, p, o in g.triples((selected_subject, selected_predicate, selected_object)):
                if isinstance(s, URIRef):
                    subject_output = subject_uri_prefixname_dict[s]    #convert uri to prefix:name
                else:
                    subject_output = s
                if isinstance(p, URIRef):
                    predicate_output = predicate_uri_prefixname_dict[p]
                else:
                    predicate_output = p
                if isinstance(o, URIRef):
                        object_output = object_uri_prefixname_dict[o]
                else:
                    object_output = o
                st.write(f"🔹 {subject_output} → {predicate_output} → {object_output}")

        if filter_button and display_selection == "Full URI":
            for s, p, o in g.triples((selected_subject, selected_predicate, selected_object)):
                st.write(f"🔹 {s} → {p} → {o}")

#__________________________________________________

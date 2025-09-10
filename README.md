# RDFolio

Web app to visually build RML mappings - tool for transforming structured data into RDF triples

RDFolio is a simple tool to visually build RML mappings. It is an interactive web app built
with Streamlit for transforming structured data into RDF triples, using mainly the rdflib in Python.

To run it:

`pip install -r requirements.txt`

`python -m streamlit run RDFolio.py`

- You can start a new mapping from scratch.
- You can save progress, storing the mapping on a pkl file.
- When you are done, you can export the mapping to a ttl file
(other formats available).




MAIN VARIABLES:
st.session_state["g_mapping"]: stores the mapping
st.session_state["ns_dict"]: dictionary in the shape {prefix: namespace iri}
st.session_state["tmap_dict"]: dictionary in the shape {triplesmap label: triplesmap}
st.session_state["data_source_dict"]: dictionary in the shape {triplesmap label: data source}
st.session_state["subject_dict"]: dictionary in the shape {triplesmap label: [subject label, subject data source column]}

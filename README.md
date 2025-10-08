# 3Xmap Studio

3Xmap Studio is a visual editor for **[R2RML](https://www.w3.org/TR/r2rml/)** and **[RML](https://w3id.org/rml/core/spec)** mappings. It is built with [Streamlit](https://github.com/streamlit/streamlit) and uses [Morph-KGC](https://github.com/morph-kgc/morph-kgc/) to create the knowledge graph.

## Features :sparkles:

- Supports relational databases and CSV files (more formats to come).
- Guide mapping development through pre-loaded ontologies.
- Create [RML views](https://www.w3.org/TR/r2rml/#r2rml-views) over relational databases with SQL.
- Export the RML mapping and create the knowledge graph.
- Explore your mapping.
- Save the session for later.

## Getting Started :rocket:

You can run 3Xmap Studio by cloning this repository and executing:

```bash
pip install -r requirements.txt
python -m streamlit run 3xmap-studio.py
```

We recommend to use [virtual environments](https://docs.python.org/3/library/venv.html#) to install 3Xmap Studio.

## License :unlock:

3Xmap Studio is available under the **[Apache License 2.0](https://github.com/morph-kgc/3xmap-studio/blob/main/LICENSE)**.

## Author & Contact :mailbox_with_mail:

- **[Paloma Arenas-Guerrero](https://github.com/arenasg-paloma/)**
- **[Julián Arenas-Guerrero](https://github.com/arenas-guerrero-julian/) - [julian.arenas.guerrero@upm.es](mailto:julian.arenas.guerrero@upm.es)**

*[Universidad Politécnica de Madrid](https://www.upm.es/internacional)*.

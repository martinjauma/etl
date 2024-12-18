import streamlit as st
import os
import json
from modules.utils import (
    load_json,
    create_conditions_table,
    validate_json_against_table,
    remove_mismatched_objects
)

# Directorio de salida para guardar el JSON localmente
output_directory = './output'
os.makedirs(output_directory, exist_ok=True)

# Interfaz principal
st.title("JSON Validator and Editable Table")

# Subir archivo JSON
uploaded_file = st.file_uploader("Sube tu archivo JSON", type="json")
if uploaded_file is not None:
    try:
        # Cargar datos desde el JSON
        data = load_json(uploaded_file)

        # Extraer 'row_name' únicos y categorías (qualifiers)
        row_names = list(set(row["row_name"] for row in data["rows"]))
        qualifiers = list(
            set(qualifier["category"]
                for row in data["rows"]
                for clip in row["clips"]
                for qualifier in clip["qualifiers"]["qualifiers_array"])
        )

        # Crear tabla editable con 'row_name' y categorías
        conditions_table = create_conditions_table(row_names, qualifiers)

        # Mostrar la tabla editable
        st.subheader("Tabla editable")
        edited_table = st.data_editor(
            conditions_table, 
            use_container_width=True,
            key="editable_table"
        )

        # Validar el JSON contra la tabla
        if st.button("Validar JSON contra la tabla"):
            mismatches, duplicates = validate_json_against_table(data, edited_table)

            # Mostrar mismatches (no coincidencias)
            if mismatches:
                st.error("Las siguientes combinaciones no coinciden con la tabla:")
                for row_name, clip_index, qualifier in mismatches:
                    st.write(f"- Row Name: {row_name}, Clip #: {clip_index}, Qualifier: {qualifier}")
            else:
                st.success("¡Todas las combinaciones coinciden!")

            # Mostrar duplicados
            if duplicates:
                st.warning("Se encontraron qualifiers duplicados en los clips:")
                for row_name, clip_index, qualifier in duplicates:
                    st.write(f"- Row Name: {row_name}, Clip #: {clip_index}, Qualifier: {qualifier}")

            # Confirmación para generar un nuevo JSON sin los objetos no coincidentes
            if mismatches and st.button("Generar nuevo JSON sin objetos no coincidentes"):
                # Filtrar el JSON
                filtered_data = remove_mismatched_objects(data, mismatches)

                # Guardar el JSON localmente
                local_file_path = os.path.join(output_directory, "filtered_data.json")
                with open(local_file_path, "w") as f:
                    json.dump(filtered_data, f, indent=4)

                st.success(f"Nuevo JSON guardado localmente en: {os.path.abspath(local_file_path)}")

                # Previsualizar el nuevo JSON
                st.subheader("Previsualización del nuevo JSON:")
                st.json(filtered_data)

                # Botón para descargar el nuevo JSON desde Streamlit
                filtered_json = json.dumps(filtered_data, indent=4)
                st.download_button(
                    label="Descargar nuevo JSON",
                    data=filtered_json,
                    file_name="filtered_data.json",
                    mime="application/json"
                )

    except Exception as e:
        st.error(f"Error: {e}")

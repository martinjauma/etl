import streamlit as st
import json
import os
import pandas as pd
from modules.utils import load_json, load_csv_to_table, validate_data_against_json, create_conditions_table

# Configuración del directorio de salida
output_directory = './output'
os.makedirs(output_directory, exist_ok=True)

# Función para la primera página
def page_1():
    st.title("Página 1: Cargar JSON y Generar Tabla Editable")

    # Subir archivo JSON
    uploaded_file = st.file_uploader("Sube tu archivo JSON", type="json")
    if uploaded_file:
        try:
            # Cargar datos desde el JSON
            data = load_json(uploaded_file)

            # Validar si el JSON tiene la estructura esperada
            if "rows" not in data:
                st.error("El archivo JSON no contiene la clave esperada 'rows'.")
                return

            # Crear tabla editable
            row_names, qualifiers = create_conditions_table(data)
            st.subheader("Tabla editable generada desde el JSON")
            editable_table = st.data_editor(
                pd.DataFrame(row_names, columns=["row_name"]).join(
                    pd.DataFrame(columns=qualifiers).fillna(False)
                ),
                use_container_width=True,
                key="editable_table",
            )

            # Botón para guardar la tabla editada como JSON
            if st.button("Guardar Tabla como JSON"):
                output_path = os.path.join(output_directory, "tabla_editable.json")
                editable_table.to_json(output_path, orient="records", indent=4)
                st.success(f"Tabla guardada exitosamente en: {output_path}")

            # Validar coincidencias
            if st.button("Validar Coincidencias"):
                mismatches, duplicates = validate_data_against_json(data, editable_table, data_type="table")
                display_validation_results(mismatches, duplicates)

        except Exception as e:
            st.error(f"Error: {e}")


# Función para la segunda página
def page_2():
    st.title("Página 2: Validar Coincidencias entre JSON y CSV")

    # Subir archivo JSON
    json_file = st.file_uploader("Sube tu archivo JSON", type="json")
    csv_file = st.file_uploader("Sube tu archivo CSV", type="csv")

    if json_file and csv_file:
        try:
            json_data = load_json(json_file)
            csv_data = load_csv_to_table(csv_file)

            st.write("**Contenido del JSON**:")
            st.json(json_data)
            st.write("**Contenido del CSV**:")
            st.dataframe(csv_data)

            # Validar coincidencias
            if st.button("Validar Coincidencias"):
                mismatches, duplicates = validate_data_against_json(json_data, csv_data, data_type="csv")
                display_validation_results(mismatches, duplicates)

        except Exception as e:
            st.error(f"Error: {e}")


# Función para la tercera página
def page_3():
    st.title("Página 3: Validar JSON Generado contra JSON Original")

    json_file_path = os.path.join(output_directory, "tabla_editable.json")
    json_original_file = st.file_uploader("Sube tu JSON original para comparar", type="json")

    if os.path.exists(json_file_path) and json_original_file:
        try:
            with open(json_file_path, "r") as file:
                generated_data = json.load(file)

            original_data = load_json(json_original_file)

            st.write("**JSON Original**:")
            st.json(original_data)
            st.write("**JSON Generado**:")
            st.json(generated_data)

            if st.button("Validar Coincidencias"):
                mismatches, duplicates = validate_data_against_json(original_data, generated_data, data_type="json")
                display_validation_results(mismatches, duplicates)

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.error("Asegúrate de haber generado el JSON en Página 1 y haber subido el JSON original.")


# Función para mostrar resultados de validación
def display_validation_results(mismatches, duplicates):
    if mismatches:
        st.error("Las siguientes combinaciones no coinciden:")
        for mismatch in mismatches:
            st.write(f"- {mismatch}")
    else:
        st.success("¡Todas las combinaciones coinciden!")

    if duplicates:
        st.warning("Se encontraron qualifiers duplicados en el JSON:")
        for duplicate in duplicates:
            st.write(f"- {duplicate}")
    else:
        st.info("No se encontraron qualifiers duplicados.")


# Página de navegación
page = st.selectbox(
    "Selecciona una página",
    ["Página 1: Cargar JSON y Generar Tabla Editable",
     "Página 2: Subir JSON/CSV y Validar Coincidencias",
     "Página 3: Validar JSON Generado contra JSON Original"]
)

if page == "Página 1: Cargar JSON y Generar Tabla Editable":
    page_1()
elif page == "Página 2: Subir JSON/CSV y Validar Coincidencias":
    page_2()
elif page == "Página 3: Validar JSON Generado contra JSON Original":
    page_3()

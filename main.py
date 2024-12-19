#main.py

import streamlit as st
import json
import os
import pandas as pd
from modules.utils import (
    load_json,
    validate_data_against_json,
    load_csv_to_table
)

# Directorio de salida para guardar el JSON localmente
output_directory = './output'
os.makedirs(output_directory, exist_ok=True)

# Función para la primera página
def page_1():
    st.title("Página 1: Cargar JSON y Generar Tabla Editable")

    # Subir archivo JSON
    uploaded_file = st.file_uploader("Sube tu archivo JSON", type="json")
    if uploaded_file is not None:
        try:
            # Cargar datos desde el JSON
            data = load_json(uploaded_file)

            # Validar si el JSON tiene la estructura esperada
            if "rows" not in data:
                st.error("El archivo JSON no contiene la clave esperada 'rows'. Por favor, revisa la estructura del archivo.")
                return

            # Extraer 'row_name' únicos y categorías (qualifiers) del JSON
            row_names = list(set(row["row_name"] for row in data["rows"]))
            qualifiers = list(
                set(qualifier["category"]
                    for row in data["rows"]
                    for clip in row.get("clips", [])
                    for qualifier in clip.get("qualifiers", {}).get("qualifiers_array", []))
            )

            # Crear una tabla inicial con los 'row_name' y columnas de qualifiers
            initial_data = pd.DataFrame(
                data={qualifier: False for qualifier in qualifiers},  # Columnas con valores iniciales en False
                index=row_names  # Índices con los 'row_name'
            ).reset_index()

            initial_data.rename(columns={"index": "row_name"}, inplace=True)

            # Mostrar la tabla editable usando `st.dataframe`
            st.subheader("Tabla editable generada desde el JSON")
            edited_table = st.dataframe(initial_data)

            # Botón para guardar la tabla editada como JSON
            if st.button("Guardar Tabla como JSON"):
                try:
                    # Convertir la tabla editada a JSON
                    output_path = os.path.join(output_directory, "tabla_editable.json")
                    edited_table.to_json(output_path, orient="records", indent=4)

                    st.success(f"Tabla guardada exitosamente en: {output_path}")
                except Exception as e:
                    st.error(f"Error al guardar el archivo: {e}")

            if st.button("Validar Coincidencias"):
                mismatches, duplicates = validate_data_against_json(data, edited_table, data_type="table")

                # Mostrar resultados
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
        except Exception as e:
            st.error(f"Error al procesar el archivo JSON: {e}")

# Función para la segunda página
def page_2():
    st.title("Página 2: Validar Coincidencias entre JSON y CSV")

    # Subir archivo JSON
    json_file = st.file_uploader("Sube tu archivo JSON", type="json", key="json_upload")
    
    # Subir archivo CSV
    csv_file = st.file_uploader("Sube tu archivo CSV", type="csv", key="csv_upload")
    
    if json_file and csv_file:
        try:
            # Cargar el archivo JSON
            json_data = load_json(json_file)

            # Cargar el archivo CSV
            csv_data = load_csv_to_table(csv_file)

            st.subheader("Datos cargados correctamente")

            # Mostrar contenido de ambos archivos
            st.write("**Contenido del JSON**:")
            st.json(json_data)
            st.write("**Contenido del CSV**:")
            st.dataframe(csv_data)

            # Validar coincidencias entre JSON y CSV
            if st.button("Validar Coincidencias"):
                mismatches, duplicates = validate_data_against_json(json_data, csv_data, data_type="csv")

                # Mostrar resultados
                if mismatches:
                    st.error("Las siguientes combinaciones no coinciden:")
                    for mismatch in mismatches:
                        st.write(f"- {mismatch}")
                else:
                    st.success("¡Todas las combinaciones coinciden entre JSON y CSV!")

                if duplicates:
                    st.warning("Se encontraron qualifiers duplicados en el JSON:")
                    for duplicate in duplicates:
                        st.write(f"- {duplicate}")
                else:
                    st.info("No se encontraron qualifiers duplicados en el JSON.")
        except Exception as e:
            st.error(f"Error al procesar los archivos: {e}")

# Función para la tercera página
def page_3():
    st.title("Página 3: Validar JSON Generado contra el JSON Original")

    # Campo para seleccionar el archivo JSON generado
    json_file_path = os.path.join(output_directory, "tabla_editable.json")
    
    json_original_file = st.file_uploader("Sube tu JSON original para comparar", type="json", key="original_json")

    try:
        # Verificar si el archivo JSON generado existe
        if os.path.exists(json_file_path):
            # Cargar el JSON generado
            with open(json_file_path, "r") as file:
                generated_data = json.load(file)

            # Cargar el JSON original
            if json_original_file:
                original_data = load_json(json_original_file)

                # Mostrar contenido de ambos archivos
                st.subheader("JSON Original")
                st.json(original_data)
                st.subheader("JSON Generado")
                st.json(generated_data)

                if st.button("Validar Coincidencias"):
                    mismatches, duplicates = validate_data_against_json(original_data, generated_data, data_type="json")

                    # Mostrar resultados
                    if mismatches:
                        st.error("Las siguientes combinaciones no coinciden:")
                        for mismatch in mismatches:
                            st.write(f"- {mismatch}")
                    else:
                        st.success("¡Todas las combinaciones coinciden entre el JSON original y el generado!")

                    if duplicates:
                        st.warning("Se encontraron qualifiers duplicados en el JSON generado:")
                        for duplicate in duplicates:
                            st.write(f"- {duplicate}")
                    else:
                        st.info("No se encontraron qualifiers duplicados en el JSON generado.")
        else:
            st.error("El archivo JSON generado en la Página 1 no se encuentra. Por favor, genera el JSON en la Página 1 primero.")
    except Exception as e:
        st.error(f"Error al cargar los archivos JSON: {e}")

# Página de navegación
page = st.selectbox(
    "Selecciona una página",
    [
        "Página 1: Cargar JSON y Generar Tabla Editable",
        "Página 2: Subir JSON/CSV y Validar Coincidencias",
        "Página 3: Validar JSON Generado contra Original"
    ]
)

# Mostrar la página seleccionada
if page == "Página 1: Cargar JSON y Generar Tabla Editable":
    page_1()
elif page == "Página 2: Subir JSON/CSV y Validar Coincidencias":
    page_2()
elif page == "Página 3: Validar JSON Generado contra Original":
    page_3()

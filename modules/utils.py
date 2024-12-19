#utils.py
import pandas as pd
import json

def load_csv_to_table(csv_file):
    """Carga un archivo CSV y devuelve un DataFrame que se puede usar como una tabla."""
    try:
        # Leer el archivo CSV y convertirlo en un DataFrame
        df = pd.read_csv(csv_file)

        # Verificar si las columnas necesarias están en el CSV
        if "row_name" not in df.columns or any(q not in df.columns for q in df.columns if q != "row_name"):
            raise ValueError("El archivo CSV debe tener una columna 'row_name' y una columna por cada 'qualifier'.")

        return df
    except Exception as e:
        raise ValueError(f"Error cargando el archivo CSV: {e}")

def load_json(uploaded_file):
    """Carga el JSON desde un archivo subido con Streamlit."""
    try:
        # Leer el contenido del archivo como texto y cargar el JSON
        data = json.load(uploaded_file)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON: {e}")
    except Exception as e:
        raise ValueError(f"Error loading JSON: {e}")


def extract_row_names_and_qualifiers(data):
    """Extrae los 'row_name' únicos y las categorías (qualifiers) del JSON."""
    try:
        # Extraer row_names únicos
        row_names = list(set(item['row_name'] for item in data["rows"]))

        # Extraer qualifiers únicos
        unique_qualifiers = list(set(
            qualifier["category"]
            for row in data["rows"]
            for clip in row["clips"]
            for qualifier in clip["qualifiers"]["qualifiers_array"]
        ))

        return row_names, unique_qualifiers
    except KeyError as e:
        raise ValueError(f"Estructura JSON no válida, clave faltante: {e}")


def create_conditions_table(row_names, qualifiers):
    """
    Genera un DataFrame con 'row_name' como filas
    y los qualifiers como columnas con casillas de verificación (False por defecto).
    """
    try:
        # Crear DataFrame con Row Names y columnas de qualifiers
        df = pd.DataFrame({
            "row_name": row_names
        })
        
        # Añadir columnas para cada categoría de qualifier
        for qualifier in qualifiers:
            df[qualifier] = False  # Casillas de verificación desmarcadas por defecto

        return df
    except Exception as e:
        raise ValueError(f"Error creando la tabla de condiciones: {e}")

def validate_and_generate_json(data, edited_table):
    mismatches = []
    duplicates = []

    # Crear un set para identificar duplicados
    seen_qualifiers = set()

    # Iterar sobre las filas del JSON original
    for row in data["rows"]:
        row_name = row["row_name"]

        # Filtrar las filas correspondientes en la tabla editada
        table_row = edited_table[edited_table["row_name"] == row_name]

        if not table_row.empty:
            # Por cada clip en el JSON, verificar los qualifiers
            for clip_index, clip in enumerate(row["clips"]):
                for qualifier in clip["qualifiers"]["qualifiers_array"]:
                    category = qualifier["category"]

                    # Verificar si la categoría está marcada como True en la tabla editada
                    if category in table_row.columns and not table_row.iloc[0][category]:
                        mismatches.append((row_name, clip_index, category))

                    # Verificar duplicados
                    qualifier_id = (row_name, clip_index, category)
                    if qualifier_id in seen_qualifiers:
                        duplicates.append((row_name, clip_index, category))
                    else:
                        seen_qualifiers.add(qualifier_id)

    # Retornar los mismatches y duplicados
    return mismatches, duplicates



def remove_mismatched_objects(data, mismatches):
    """
    Elimina del JSON original los objetos (clips) que no coinciden con la tabla.
    :param data: El JSON original.
    :param mismatches: Lista de combinaciones que no coinciden.
    :return: Nuevo JSON con los objetos filtrados.
    """
    try:
        # Crear una copia del JSON original
        filtered_data = data.copy()

        # Convertir las no coincidencias en un conjunto para búsqueda rápida
        mismatched_set = set((row_name, clip_index, qualifier) for row_name, clip_index, qualifier in mismatches)

        # Iterar por los rows y clips para filtrar
        for row in filtered_data["rows"]:
            row_name = row["row_name"]
            row["clips"] = [
                clip for clip_index, clip in enumerate(row["clips"], start=1)
                if not any((row_name, clip_index, q["category"]) in mismatched_set for q in clip["qualifiers"]["qualifiers_array"])
            ]

        return filtered_data
    except Exception as e:
        raise ValueError(f"Error filtrando objetos no coincidentes: {e}")
    
    
def validate_data_against_json(json_data, data_to_validate, data_type="csv"):
    """
    Valida los datos de entrada (tabla, CSV o JSON) contra el archivo JSON original.

    :param json_data: El archivo JSON original (como diccionario).
    :param data_to_validate: Los datos a validar (pueden ser DataFrame o JSON).
    :param data_type: Tipo de los datos a validar: "csv", "json", "table".
    :return: (mismatches, duplicates): Listas de discrepancias y duplicados.
    """
    mismatches = []
    duplicates = []

    # Crear un DataFrame con la estructura del JSON
    json_rows = []
    for row in json_data["rows"]:
        row_name = row["row_name"]
        qualifiers = set(
            qualifier["category"]
            for clip in row["clips"]
            for qualifier in clip["qualifiers"]["qualifiers_array"]
        )
        json_rows.append({"row_name": row_name, **{q: True for q in qualifiers}})
    json_df = pd.DataFrame(json_rows)

    # Convertir datos a validar a DataFrame si es JSON
    if data_type == "json":
        data_to_validate = pd.DataFrame(data_to_validate)

    # Comparar filas entre JSON y datos a validar
    for _, row in data_to_validate.iterrows():
        row_name = row["row_name"]

        # Verificar si el row_name existe en el JSON
        if row_name not in json_df["row_name"].values:
            mismatches.append(f"Row Name '{row_name}' no está en el JSON.")
            continue

        # Verificar cada categoría (columna) en los datos a validar
        for col in data_to_validate.columns[1:]:
            if col not in json_df.columns:
                mismatches.append(f"Categoría '{col}' no está en el JSON.")
            else:
                json_value = json_df.loc[json_df["row_name"] == row_name, col].values[0]
                data_value = row[col]
                if pd.notna(data_value) and bool(data_value) != bool(json_value):
                    mismatches.append(f"Row Name: {row_name}, Columna: {col}, Valor JSON: {json_value}, Valor Datos: {data_value}")

    # Verificar duplicados en los clips dentro de cada row
    for row in json_data["rows"]:
        for clip_index, clip in enumerate(row["clips"]):
            seen_qualifiers = set()
            for qualifier in clip["qualifiers"]["qualifiers_array"]:
                qualifier_name = qualifier["category"]
                if qualifier_name in seen_qualifiers:
                    duplicates.append(f"Row Name: {row['row_name']}, Clip #: {clip_index + 1}, Qualifier duplicado: {qualifier_name}")
                else:
                    seen_qualifiers.add(qualifier_name)

    return mismatches, duplicates


import pandas as pd

def load_json(uploaded_file):
    """Carga el JSON desde un archivo subido con Streamlit."""
    import json
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
        row_names = list(set(item['row_name'] for item in data["rows"]))
        unique_qualifiers = list(set(
            qualifier["category"]
            for row in data["rows"]
            for clip in row["clips"]
            for qualifier in clip["qualifiers"]["qualifiers_array"]
        ))
        return row_names, unique_qualifiers
    except KeyError as e:
        raise ValueError(f"Invalid JSON structure, missing key: {e}")


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
        raise ValueError(f"Error creating conditions table: {e}")


def validate_json_against_table(data, table):
    """
    Valida las combinaciones del JSON contra la tabla editada por el usuario.
    Retorna una lista con:
      - Qualifiers no marcados como válidos.
      - Qualifiers duplicados en los clips.
    """
    try:
        mismatches = []
        duplicates = []
        
        for row in data["rows"]:
            row_name = row["row_name"]
            for clip_index, clip in enumerate(row["clips"], start=1):  # Enumerar los clips
                # Obtener todas las categorías en el clip actual
                categories = [qualifier["category"] for qualifier in clip["qualifiers"]["qualifiers_array"]]
                
                # Detectar duplicados
                for category in set(categories):
                    if categories.count(category) > 1:  # Más de una aparición
                        duplicates.append((row_name, clip_index, category))

                # Validar si las categorías están marcadas en la tabla
                for qualifier in clip["qualifiers"]["qualifiers_array"]:
                    category = qualifier["category"]
                    if not table.loc[(table["row_name"] == row_name), category].values[0]:
                        mismatches.append((row_name, clip_index, category))  # Agregar no coincidencias

        return mismatches, duplicates
    except Exception as e:
        raise ValueError(f"Error validating JSON against table: {e}")

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
        raise ValueError(f"Error filtering mismatched objects: {e}")


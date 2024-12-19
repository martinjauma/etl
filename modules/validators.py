#validators.py
import json

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


def get_row_names(data):
    """Obtiene los Row Names únicos del JSON."""
    if "rows" in data:
        return list(set(item['row_name'] for item in data['rows']))
    else:
        raise KeyError("The JSON structure is invalid. Key 'rows' not found.")

def filter_by_row_name(data, row_name):
    """Filtra los datos del JSON por Row Name."""
    if "rows" in data:
        return [item for item in data['rows'] if item['row_name'] == row_name]
    else:
        return []

def get_unique_qualifiers(data):
    """Obtiene todas las categorías de qualifiers únicos del JSON."""
    qualifiers = []
    for row in data.get("rows", []):
        for clip in row.get("clips", []):
            for qualifier in clip.get("qualifiers", {}).get("qualifiers_array", []):
                qualifiers.append(qualifier['category'])
    return list(set(qualifiers))

def validate_conditions(data, conditions):
    """
    Valida las condiciones entre un JSON y un DataFrame (CSV cargado).
    
    :param data: El JSON cargado.
    :param conditions: DataFrame con las condiciones del CSV.
    :return: Lista de errores con Row Name, número de clip y condiciones no cumplidas.
    """
    results = []
    for row_name, group in conditions.groupby("row_name"):
        filtered_data = filter_by_row_name(data, row_name)
        for item in filtered_data:
            for clip_index, clip in enumerate(item.get('clips', []), start=1):
                # Chequear las condiciones para este Row Name
                clip_categories = [q['category'] for q in clip.get('qualifiers', {}).get('qualifiers_array', [])]

                # Condiciones faltantes
                missing_conditions = [
                    condition for condition in group["required_category"] if condition not in clip_categories
                ]

                # Condiciones duplicadas
                duplicate_conditions = [
                    category for category in clip_categories if clip_categories.count(category) > 1
                ]

                if missing_conditions or duplicate_conditions:
                    results.append({
                        "row_name": row_name,
                        "clip_number": clip_index,
                        "missing": missing_conditions,
                        "duplicates": list(set(duplicate_conditions)),
                    })

    return results

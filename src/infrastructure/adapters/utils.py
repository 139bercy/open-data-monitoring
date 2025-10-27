def load_json_by_id(data, dataset_id) -> dict:
    """Charge un fichier JSON et crée un dictionnaire indexé par une clé"""
    return next((item for item in data if item["dataset_id"] == dataset_id), None)

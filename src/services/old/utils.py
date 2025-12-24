import hashlib

def get_job_id(company, title, location):
    """Génère un hash SHA-256 robuste."""
    # On normalise pour éviter que "Paris " et "Paris" créent deux IDs différents
    base_string = f"{str(company).lower().strip()}|{str(title).lower().strip()}|{str(location).lower().strip()}"
    return hashlib.sha256(base_string.encode('utf-8')).hexdigest()

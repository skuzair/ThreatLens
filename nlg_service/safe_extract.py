def safe_get(dictionary, key, default=None):
    if not isinstance(dictionary, dict):
        return default
    return dictionary.get(key, default)
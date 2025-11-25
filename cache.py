
import json
from typing import Any

GAME_CACHE_FILE = "game_cache.json"
LOGO_CACHE_FILE = "logo_cache.json"

def save_to_cache(data: Any, filename: str) -> None:
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def load_from_cache(filename: str) -> Any:
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    

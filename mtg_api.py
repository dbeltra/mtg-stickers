"""MTG API operations for fetching set information and symbols."""

import requests
import time
import logging
from typing import Optional, Dict, Any, List
from PIL import Image
from io import BytesIO


def fetch_set_info(set_code: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """Fetch set information from Scryfall API with retry logic."""
    url = f"https://api.scryfall.com/sets/{set_code}"
    
    for attempt in range(max_retries):
        try:
            logging.debug(f"Fetching set info for {set_code} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                set_data = response.json()
                return {
                    "code": set_code,
                    "name": set_data.get("name"),
                    "date": set_data.get("released_at"),
                }
            elif response.status_code == 404:
                logging.error(f"Set '{set_code}' not found")
                return None
            elif response.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt
                logging.warning(f"Rate limited, waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            else:
                logging.warning(f"HTTP {response.status_code} for {set_code}, attempt {attempt + 1}")
                
        except requests.exceptions.RequestException as e:
            logging.warning(f"Network error for {set_code}: {e}")
            
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt
            logging.debug(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
    
    logging.error(f"Failed to fetch set info for {set_code} after {max_retries} attempts")
    return None


def fetch_set_symbol(set_code: str, max_retries: int = 3) -> Optional[Image.Image]:
    """Fetch set symbol image from MTG Collection Builder with retry logic."""
    for attempt in range(max_retries):
        try:
            logging.debug(f"Fetching symbol for {set_code} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(
                url=f"https://mtgcollectionbuilder.com/images/symbols/sets/{set_code}.png",
                timeout=10
            )
            if response.status_code == 200:
                png_image = response.content
                return Image.open(BytesIO(png_image))
            elif response.status_code == 404:
                logging.debug(f"No symbol image available for {set_code}")
                return None
            else:
                logging.warning(f"HTTP {response.status_code} fetching symbol for {set_code}")
                
        except requests.exceptions.RequestException as e:
            logging.warning(f"Network error fetching symbol for {set_code}: {e}")
            
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt
            logging.debug(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
    
    logging.warning(f"Failed to fetch symbol for {set_code} after {max_retries} attempts")
    return None


def get_recent_sets(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent MTG sets from Scryfall API."""
    try:
        logging.debug("Fetching recent sets from Scryfall...")
        response = requests.get("https://api.scryfall.com/sets", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            sets = data.get("data", [])
            
            # Filter to only released sets and sort by release date
            released_sets = [s for s in sets if s.get("released_at")]
            released_sets.sort(key=lambda x: x.get("released_at", ""), reverse=True)
            
            return released_sets[:limit]
        else:
            logging.error(f"Failed to fetch recent sets: HTTP {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error fetching recent sets: {e}")
        return []

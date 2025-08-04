from typing import List, Dict, Set
import sqlite3
import re

# Regional brand mappings
BRAND_MAP = {
    "asia": ["Toyota", "Honda", "Hyundai", "Kia", "Nissan", "Mitsubishi", "Chery", "BYD", "Subaru", "Mazda", "Suzuki"],
    "europe": ["Volkswagen", "Renault", "Peugeot", "BMW", "Mercedes-Benz", "Audi", "Fiat", "Skoda", "Dacia", "Volvo", "Opel", "Citroen", "Seat"],
    "usa": ["Ford", "Chevrolet", "Tesla", "Dodge", "Jeep", "Chrysler"]
}

# Fuzzy brand mapping - maps user inputs to database brand names
FUZZY_BRAND_MAP = {
    # Mercedes variations
    "mercedes": "Mercedes - Benz",
    "mercedes benz": "Mercedes - Benz", 
    "mercedes-benz": "Mercedes - Benz",
    "mercedesbenz": "Mercedes - Benz",
    "benz": "Mercedes - Benz",
    "merc": "Mercedes - Benz",
    
    # BMW variations
    "bmw": "BMW",
    "beemer": "BMW",
    "bimmer": "BMW",
    
    # Volkswagen variations
    "volkswagen": "Volkswagen",
    "vw": "Volkswagen", 
    "volksvagen": "Volkswagen",
    "wolkswagen": "Volkswagen",
    
    # Audi variations
    "audi": "Audi",
    
    # Toyota variations
    "toyota": "Toyota",
    
    # Ford variations
    "ford": "Ford",
    
    # Honda variations
    "honda": "Honda",
    
    # Hyundai variations
    "hyundai": "Hyundai",
    "hyundaı": "Hyundai",  # Turkish character variation
    
    # Nissan variations
    "nissan": "Nissan",
    
    # Peugeot variations
    "peugeot": "Peugeot",
    "peugeot": "Peugeot",
    "peugot": "Peugeot",
    
    # Renault variations
    "renault": "Renault",
    "reno": "Renault",
    
    # Fiat variations
    "fiat": "Fiat",
    
    # Opel variations
    "opel": "Opel",
    
    # Tesla variations
    "tesla": "Tesla",
    
    # Kia variations
    "kia": "Kia",
    
    # Mazda variations
    "mazda": "Mazda",
    
    # Skoda variations
    "skoda": "Skoda",
    "škoda": "Skoda",
    
    # Seat variations
    "seat": "Seat",
    
    # Citroen variations
    "citroen": "Citroen",
    "citroën": "Citroen",
    
    # Chevrolet variations
    "chevrolet": "Chevrolet",
    "chevy": "Chevrolet",
    "chevrolet": "Chevrolet",
    
    # Mitsubishi variations
    "mitsubishi": "Mitsubishi",
    "mitsubıshı": "Mitsubishi",  # Turkish character variation
    
    # Suzuki variations
    "suzuki": "Suzuki",
    
    # Dacia variations
    "dacia": "Dacia",
    
    # Volvo variations
    "volvo": "Volvo",
    
    # Porsche variations
    "porsche": "Porsche",
    
    # Alfa Romeo variations
    "alfa romeo": "Alfa Romeo",
    "alfa": "Alfa Romeo",
    "alfaromeo": "Alfa Romeo",
    
    # Mini variations
    "mini": "Mini",
    
    # MG variations
    "mg": "MG",
    
    # Chery variations
    "chery": "Chery",
    
    # Geely variations
    "geely": "Geely",
    
    # Infiniti variations
    "infiniti": "Infiniti",
    
    # Lada variations
    "lada": "Lada",
    
    # Maserati variations
    "maserati": "Maserati",
    
    # Tata variations
    "tata": "Tata",
    
    # Tofaş variations
    "tofas": "Tofaş",
    "tofaş": "Tofaş",
    
    # Chrysler variations
    "chrysler": "Chrysler",
    
    # Daewoo variations
    "daewoo": "Daewoo",
}

def get_database_brands() -> Set[str]:
    """
    Get all unique brand names from the database.
    """
    try:
        # Use absolute path to database file
        import os
        db_path = os.path.join(os.path.dirname(__file__), 'araba_verileri.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT marka FROM araba_ilanlari ORDER BY marka')
        brands = {row[0] for row in cursor.fetchall()}
        conn.close()
        return brands
    except Exception as e:
        print(f"Error reading database brands: {e}")
        # Fallback to hardcoded list based on our database analysis
        return {
            "Alfa Romeo", "Audi", "BMW", "Chery", "Chevrolet", "Chrysler", "Citroen", 
            "Dacia", "Daewoo", "Fiat", "Ford", "Geely", "Honda", "Hyundai", "Infiniti", 
            "Kia", "Lada", "MG", "Maserati", "Mazda", "Mercedes - Benz", "Mini", 
            "Mitsubishi", "Nissan", "Opel", "Peugeot", "Porsche", "Renault", "Seat", 
            "Skoda", "Suzuki", "Tata", "Tesla", "Tofaş", "Toyota", "Volkswagen", "Volvo"
        }

def normalize_brand_name(user_brand: str) -> str:
    """
    Normalize user input brand name to match database brand names.
    
    Args:
        user_brand: The brand name as entered by the user
        
    Returns:
        The normalized brand name that matches the database, or the original if no match
    """
    if not user_brand:
        return user_brand
        
    # Convert to lowercase for comparison
    normalized_input = user_brand.lower().strip()
    
    # Remove common punctuation and normalize spaces
    normalized_input = re.sub(r'[^\w\s]', '', normalized_input)
    normalized_input = re.sub(r'\s+', ' ', normalized_input).strip()
    
    # Direct lookup in fuzzy map
    if normalized_input in FUZZY_BRAND_MAP:
        return FUZZY_BRAND_MAP[normalized_input]
    
    # Try partial matching for database brands
    db_brands = get_database_brands()
    
    # Exact match (case insensitive)
    for db_brand in db_brands:
        if normalized_input == db_brand.lower():
            return db_brand
            
    # Partial match - user input is contained in database brand
    for db_brand in db_brands:
        if normalized_input in db_brand.lower():
            return db_brand
            
    # Partial match - database brand is contained in user input  
    for db_brand in db_brands:
        if db_brand.lower() in normalized_input:
            return db_brand
    
    # No match found, return original
    return user_brand

def map_brands_list(user_brands: List[str]) -> List[str]:
    """
    Map a list of user-provided brand names to database brand names.
    
    Args:
        user_brands: List of brand names as entered by the user
        
    Returns:
        List of normalized brand names that match the database
    """
    if not user_brands:
        return []
        
    mapped_brands = []
    for brand in user_brands:
        mapped_brand = normalize_brand_name(brand)
        if mapped_brand:  # Only add non-empty results
            mapped_brands.append(mapped_brand)
            
    # Remove duplicates while preserving order
    seen = set()
    result = []
    for brand in mapped_brands:
        if brand not in seen:
            seen.add(brand)
            result.append(brand)
            
    return result

def map_region_to_brands(region: str) -> List[str]:
    """
    Maps a geographical region to a list of associated car brands.

    Args:
        region: The name of the region (e.g., "Asia", "Europe", "USA").
                The lookup is case-insensitive.

    Returns:
        A list of brand names associated with the region, or an empty list
        if the region is not found.
    """
    return BRAND_MAP.get(region.lower(), [])
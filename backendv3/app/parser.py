# app/parser.py

import os
import logging
from typing import List, Dict, Optional, Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# --- Constants for Heuristics and Normalization ---

# Mileage thresholds based on database analysis
LOW_MILEAGE_THRESHOLD_KM = 50000          # Very low mileage cars
MEDIUM_MILEAGE_THRESHOLD_KM = 100000      # Moderate mileage cars  
HIGH_MILEAGE_THRESHOLD_KM = 150000        # High mileage threshold
VERY_HIGH_MILEAGE_THRESHOLD_KM = 200000   # Very high mileage cars

# Age thresholds based on database analysis (current year: 2025)
VERY_YOUNG_CAR_THRESHOLD_YEARS = 2        # Almost new cars (2023+)
YOUNG_CAR_THRESHOLD_YEARS = 3             # Young cars (2022+)
MODERN_CAR_THRESHOLD_YEARS = 7            # Modern cars (2018+)
OLDER_CAR_THRESHOLD_YEARS = 10            # Older but decent cars (2015+)

# Vehicle segment classifications based on actual database body types
FAMILY_CAR_SEGMENTS = ["Sedan", "MPV", "Station wagon"]
CITY_CAR_SEGMENTS = ["Hatchback/5", "Hatchback/3", "Sedan"]
SPORTS_CAR_SEGMENTS = ["Coupe", "Roadster"] 
COMPACT_SEGMENTS = ["Hatchback/3", "Hatchback/5"]
LUXURY_SEGMENTS = ["Sedan", "Coupe", "Station wagon"]
PRACTICAL_SEGMENTS = ["MPV", "Station wagon", "Hatchback/5"]

# Additional useful classifications
ECONOMICAL_SEGMENTS = ["Hatchback/3", "Hatchback/5"]
SPACIOUS_SEGMENTS = ["Sedan", "MPV", "Station wagon"]
PERFORMANCE_SEGMENTS = ["Coupe", "Roadster"]

# --- Pydantic Models for Structured Output (Updated for new schema) ---

class Filters(BaseModel):
    fiyat_max: Optional[int] = Field(None, description="Maximum price in TL.")
    fiyat_min: Optional[int] = Field(None, description="Minimum price in TL.")
    age_max: Optional[int] = Field(None, description="Maximum age in years (to be converted to 'yil').")
    age_min: Optional[int] = Field(None, description="Minimum age in years (to be converted to 'yil').")
    km_max: Optional[int] = Field(None, description="Maximum mileage in km.")
    km_min: Optional[int] = Field(None, description="Minimum mileage in km.")
    yakit: Optional[List[str]] = Field(default_factory=list, description="Normalized fuel types: ['Benzin', 'Dizel', 'Hibrit', 'Elektrik'].")
    vites: Optional[str] = Field(None, description="Normalized transmission: 'Otomatik' or 'Manuel'.")
    marka: Optional[List[str]] = Field(default_factory=list, description="List of preferred brands.")
    kasa_tipi: Optional[List[str]] = Field(default_factory=list, description="List of preferred body types.")
    boya_durumu: Optional[str] = Field(None, description="Condition of paint, e.g., 'Yok' for none.")
    parca_durumu: Optional[str] = Field(None, description="Condition of replaced parts, e.g., 'Yok' for none.")

class Exclusions(BaseModel):
    exclude_brands: Optional[List[str]] = Field(default_factory=list, description="List of excluded brands.")
    exclude_fuel_types: Optional[List[str]] = Field(default_factory=list, description="List of excluded fuel types.")
    exclude_colors: Optional[List[str]] = Field(default_factory=list, description="List of excluded colors.")
    sports_car_excluded: bool = Field(False, description="True if user wants to exclude sports cars.")

class Inferred(BaseModel):
    assumptions: List[str] = Field(default_factory=list, description="A list of rationales for any assumptions made.")
    reset_filters: bool = Field(False, description="True if user wants to clear/reset previous filters for variety.")
    seek_diversity: bool = Field(False, description="True if user explicitly wants diverse/different options.")

class RawEntities(BaseModel):
    brands: List[str] = Field(default_factory=list, description="Brands mentioned.")
    models: List[str] = Field(default_factory=list, description="Models mentioned.")
    colors: List[str] = Field(default_factory=list, description="Colors mentioned.")
    segments: List[str] = Field(default_factory=list, description="Segments mentioned.")
    region: Optional[str] = Field(None, description="Geographical region mentioned (e.g., 'Asia', 'Europe', 'USA').")

class ParsedUserQuery(BaseModel):
    """Structured representation of a user's vehicle search query."""
    filters: Filters = Field(description="Normalized constraints for filtering.")
    exclusions: Exclusions = Field(description="Negative intents and exclusions.")
    inferred: Inferred = Field(description="Heuristics and assumptions applied.")
    raw_entities: RawEntities = Field(description="Raw entities detected in the query.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in the extraction (0.0 to 1.0).")


# --- LLM and Prompt Setup ---
LLM_MODEL = "gemini-2.5-flash-lite"

SYSTEM_PROMPT = """
You are an expert multilingual (Turkish/English) query parser for a used car marketplace.
Your task is to analyze the user's free-text query and convert it into a structured JSON object based on the provided Pydantic schema.
The database columns are: id, link, fiyat, marka, seri, model, yil, km, vites, yakit, kasa_tipi, renk, boya, parca.

**Follow these rules precisely:**

1.  **Normalization & Mapping:**
    -   **Price:** Parse numbers like "650 bin", "600.000 TL" into integers (e.g., 650000) and map to `fiyat_max` or `fiyat_min`.
    -   **Age:** A query like "under 3 years old" or "3 yaşından genç" should be parsed as `age_max: 3`. The system will convert this to a filter on the `yil` column.
    -   **Mileage:** Parse mileage and map to `km_max` or `km_min`. Note: Database stores km as strings like "69.000 km".
    -   **Brands:** Extract brand names as mentioned by user (e.g., "Mercedes", "BMW", "VW") and add to `marka` list. Don't worry about exact database naming - the system will normalize them. Common variations like "Mercedes" (for Mercedes-Benz), "VW" (for Volkswagen), "Benz" are acceptable.
    -   **Fuel Type:** Map synonyms (`benzinli/gasoline -> Benzin`, `dizel/diesel -> Dizel`, etc.) and assign to `yakit`.
    -   **Transmission:** Map `otomatik/automatic -> Otomatik`, `manuel/manual -> Manuel` and assign to `vites`.
    -   **Paint/Parts:** Map "boyasız" (no paint) to `boya_durumu: "Yok"`. Map "değişensiz" (no replaced parts) to `parca_durumu: "Yok"`.

2.  **Enhanced Heuristics & Inferences:** Apply these rules and document them in the `inferred.assumptions` list.
    
    **Mileage Heuristics:**
    -   "very low mileage" / "çok az kilometreli": Set `km_max` to {LOW_MILEAGE_THRESHOLD_KM}. Rationale: 'Inferred very low mileage threshold.'
    -   "low mileage" / "az kilometreli": Set `km_max` to {MEDIUM_MILEAGE_THRESHOLD_KM}. Rationale: 'Inferred low mileage threshold.'
    -   "moderate mileage" / "orta kilometreli": Set `km_max` to {HIGH_MILEAGE_THRESHOLD_KM}. Rationale: 'Inferred moderate mileage threshold.'
    
    **Age Heuristics:**
    -   "brand new" / "sıfır ayarında": Set `age_max` to {VERY_YOUNG_CAR_THRESHOLD_YEARS}. Rationale: 'Inferred brand new car threshold.'
    -   "young car" / "genç araba": Set `age_max` to {YOUNG_CAR_THRESHOLD_YEARS}. Rationale: 'Inferred young car threshold.'
    -   "modern car" / "modern araba": Set `age_max` to {MODERN_CAR_THRESHOLD_YEARS}. Rationale: 'Inferred modern car threshold.'
    
    **Segment Heuristics:**
    -   "family car" / "aile arabası": Add {FAMILY_CAR_SEGMENTS} to `filters.kasa_tipi`, set `exclusions.sports_car_excluded` to `True`. Rationale: 'Interpreted family car intent.'
    -   "city car" / "şehir arabası": Add {CITY_CAR_SEGMENTS} to `filters.kasa_tipi`. Rationale: 'Interpreted city car intent.'
    -   "compact car" / "kompakt araba": Add {COMPACT_SEGMENTS} to `filters.kasa_tipi`. Rationale: 'Interpreted compact car intent.'
    -   "economical car" / "ekonomik araba": Add {ECONOMICAL_SEGMENTS} to `filters.kasa_tipi`. Rationale: 'Interpreted economical car intent.'
    -   "spacious car" / "geniş araba": Add {SPACIOUS_SEGMENTS} to `filters.kasa_tipi`. Rationale: 'Interpreted spacious car intent.'
    -   "practical car" / "pratik araba": Add {PRACTICAL_SEGMENTS} to `filters.kasa_tipi`. Rationale: 'Interpreted practical car intent.'
    -   "luxury car" / "lüks araba": Add {LUXURY_SEGMENTS} to `filters.kasa_tipi`. Rationale: 'Interpreted luxury car intent.'
    -   "sports car" / "spor araba": Add {SPORTS_CAR_SEGMENTS} to `filters.kasa_tipi`. Rationale: 'Interpreted sports car intent.'

3.  **Negations & Exclusions:**
    -   "not a sports car" / "spor araba olmasın": Set `exclusions.sports_car_excluded` to `True`.
    -   "no diesel" / "dizel hariç": Add 'Dizel' to `exclusions.exclude_fuel_types`.
    -   "no manual" / "manuel hariç": Add 'Manuel' to `exclusions.exclude_fuel_types`.

4.  **Context Changes & Diversity:**
    -   "different cars" / "farklı arabalar": Set `inferred.seek_diversity` to `True` and `inferred.reset_filters` to `True`. Clear `filters.marka` to get variety. Rationale: 'User wants diverse car options.'
    -   "5 different cars" / "5 farklı araba": Set `inferred.seek_diversity` to `True` and `inferred.reset_filters` to `True`. Clear `filters.marka`. Rationale: 'User wants 5 diverse cars from different brands.'
    -   "something else" / "başka bir şey": Set `inferred.reset_filters` to `True`. Rationale: 'User wants to change search criteria.'
    -   "show me other options" / "başka seçenekler": Set `inferred.seek_diversity` to `True`. Rationale: 'User wants alternative options.'
    -   "variety" / "çeşitlilik": Set `inferred.seek_diversity` to `True`. Clear brand filters. Rationale: 'User explicitly wants variety.'

4.  **Confidence Score:** Provide a confidence score from 0.0 to 1.0 based on query ambiguity.

**Output Format:** Your entire output must be a single, valid JSON object that conforms to the `ParsedUserQuery` schema.
"""

def parse_user_query(query: str) -> Dict[str, Any]:
    """
    Parses a multilingual user query to extract structured vehicle search filters.
    """
    if not query or not query.strip():
        return ParsedUserQuery(
            filters=Filters(), exclusions=Exclusions(), inferred=Inferred(assumptions=["Empty query provided."]),
            raw_entities=RawEntities(), confidence=0.0
        ).model_dump()

    try:
        llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL, google_api_key=os.getenv("GEMINI_API_KEY"), temperature=0.0
        )
        structured_llm = llm.with_structured_output(ParsedUserQuery)

        formatted_prompt = SYSTEM_PROMPT.format(
            LOW_MILEAGE_THRESHOLD_KM=LOW_MILEAGE_THRESHOLD_KM,
            MEDIUM_MILEAGE_THRESHOLD_KM=MEDIUM_MILEAGE_THRESHOLD_KM,
            HIGH_MILEAGE_THRESHOLD_KM=HIGH_MILEAGE_THRESHOLD_KM,
            VERY_YOUNG_CAR_THRESHOLD_YEARS=VERY_YOUNG_CAR_THRESHOLD_YEARS,
            YOUNG_CAR_THRESHOLD_YEARS=YOUNG_CAR_THRESHOLD_YEARS,
            MODERN_CAR_THRESHOLD_YEARS=MODERN_CAR_THRESHOLD_YEARS,
            FAMILY_CAR_SEGMENTS=FAMILY_CAR_SEGMENTS,
            CITY_CAR_SEGMENTS=CITY_CAR_SEGMENTS,
            SPORTS_CAR_SEGMENTS=SPORTS_CAR_SEGMENTS,
            COMPACT_SEGMENTS=COMPACT_SEGMENTS,
            LUXURY_SEGMENTS=LUXURY_SEGMENTS,
            PRACTICAL_SEGMENTS=PRACTICAL_SEGMENTS,
            ECONOMICAL_SEGMENTS=ECONOMICAL_SEGMENTS,
            SPACIOUS_SEGMENTS=SPACIOUS_SEGMENTS,
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", formatted_prompt), ("human", "Please parse this user query: {user_query}")
        ])

        chain = prompt | structured_llm
        logger.info(f"Parsing user query: '{query}'")

        response: ParsedUserQuery = chain.invoke({"user_query": query})
        return response.model_dump()

    except Exception as e:
        logger.error(f"Failed to parse user query with LLM: {e}", exc_info=True)
        return ParsedUserQuery(
            filters=Filters(), exclusions=Exclusions(),
            inferred=Inferred(assumptions=[f"Parser failed due to an error: {e}"]),
            raw_entities=RawEntities(), confidence=0.1
        ).model_dump()
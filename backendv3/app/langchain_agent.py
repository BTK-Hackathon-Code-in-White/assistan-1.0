# app/langchain_agent.py

import os
import logging
import ast
import re
import signal
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from the correct path
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# --- Database and Agent Setup ---
# Use absolute path to database file to avoid path issues
DB_PATH = os.path.join(os.path.dirname(__file__), "araba_verileri.db")
DB_URL = f"sqlite:///{DB_PATH}"
LLM_MODEL = "gemini-2.5-flash"
CURRENT_YEAR = datetime.now().year

engine = create_engine(DB_URL)
db = SQLDatabase(engine=engine, sample_rows_in_table_info=0) # No need to sample rows
llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL, 
    temperature=0, 
    google_api_key=os.getenv("GEMINI_API_KEY"),
    timeout=30,  # 30 second timeout
    max_retries=2
)

SCHEMA_GUIDE = f"""
Database Schema Guide for the 'araba_ilanlari' table:
The table contains used car listings. All column names are lowercase.
- id: (INTEGER) Unique identifier for the listing.
- link: (TEXT) URL to the listing.
- fiyat: (REAL) The price in Turkish Lira (TL).
- marka: (TEXT) The brand of the car (e.g., 'Volkswagen', 'Ford').
- seri: (TEXT) The series of the model (e.g., 'Golf', 'Focus').
- model: (TEXT) The specific model/trim (e.g., '1.6 TDI Comfortline').
- yil: (INTEGER) The manufacturing year of the car (e.g., 2020).
- km: (REAL) The mileage in kilometers.
- vites: (TEXT) Transmission type. Canonical values are: 'Otomatik', 'Manuel'.
- yakit: (TEXT) Fuel type. Canonical values are: 'Benzin', 'Dizel', 'Hibrit', 'Elektrik'.
- kasa_tipi: (TEXT) Body type of the car (e.g., 'SUV', 'Sedan', 'Hatchback').
- renk: (TEXT) Color of the car.
- boya: (TEXT) Description of painted parts. "Yok" means no painted parts.
- parca: (TEXT) Description of replaced parts. "Yok" means no replaced parts.
"""

AGENT_PROMPT_PREFIX = f"""
You are a specialized SQL agent. Your purpose is to understand a user's request, formulate a SQL query, and then EXECUTE that query to get the results. The final output MUST be the raw query results in a list of tuples format, like [(),(),(),(),...].


The current year is {CURRENT_YEAR}. Adhere to these rules STRICTLY:
1.  **Read-Only**: Generate and execute `SELECT` statements ONLY.
2.  **Quoting**: Quote all column identifiers (e.g., `"fiyat"`, `"kasa_tipi"`).
3.  **Schema Grounding**: Use the provided schema guide. Do not invent columns.
4.  **Constraints**: Use the `constraints` dictionary to build precise `WHERE` clauses.
5.  **Filtering Logic**:
    - `fiyat_max` -> `"fiyat" <= value`. `km_max` -> `"km" <= value`.
    - **IMPORTANT**: If `age_max` is provided, calculate `min_year = {CURRENT_YEAR} - age_max`. The SQL filter must be `"yil" >= min_year`.
    - `marka` list -> `"marka" IN (...)`.
    - `boya_durumu: "Yok"` -> `"boya" = 'Yok'`.
    - `parca_durumu: "Yok"` -> `"parca" = 'Yok'`.
    - `sports_car_excluded: True` -> `"kasa_tipi" NOT IN ('Coupe', 'Cabrio', 'Roadster', 'Sport')`.
6.  **Diversity Handling**: If the task description mentions "diverse", "different brands", or "variety", prioritize showing cars from different brands by using `ORDER BY "marka", RANDOM()` or similar techniques to ensure brand diversity in results.
7.  **Result Limit**: You MUST add `LIMIT 5` to every query.
8.  **Single Statement**: Generate only one SQL statement. And it should start with "SELECT * ... "
9.  **Final Output**: After executing the query, you MUST return the results directly as a list of rows.
    DO NOT return the SQL query, explanations, or any other text.

{SCHEMA_GUIDE}
"""

# Tool and Agent setup
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
sql_agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    agent_type="openai-tools",
    verbose=False,  # Disable verbose logging for speed
    prefix=AGENT_PROMPT_PREFIX,
    agent_executor_kwargs={"handle_parsing_errors": True},
    max_execution_time=40  # 40 second timeout for agent execution
)

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Operation timed out")

def run_sql_query_from_text(task: str, constraints: dict) -> List[Dict[str, Any]]:
    """
    Executes a natural language query against the database using an LLM agent.
    """
    prompt = f"Task: {task}\n\nStructured Constraints to apply:\n{constraints}"
    logger.info("Invoking SQL agent.")

    try:
        # Set up timeout (only works on Unix-like systems)
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(40)  # 30 second timeout
        except AttributeError:
            # Windows doesn't support SIGALRM, skip timeout
            pass
        
        result = sql_agent_executor.invoke({"input": prompt})
        
        # Cancel timeout
        try:
            signal.alarm(0)
        except AttributeError:
            pass
            
        output = result.get("output", "[]")

        # 1. Adım: Ajan çıktısının bir SQL sorgusu olup olmadığını kontrol et. Varsa çalıştır.
        # ```sql...``` formatındaki metni bulmak için regex kullanıyoruz.
        sql_match = re.search(r"```sql\s*(.*?)\s*```", output, re.DOTALL)

        if sql_match:
            sql_query = sql_match.group(1).strip()
            logger.info(f"Agent returned a raw SQL query. Executing it: {sql_query}")
            
            # Sorguyu veritabanı motorunda çalıştırma
            with engine.connect() as connection:
                result_proxy = connection.execute(str(sql_query))
                
                # Sonuçları Dict formatına dönüştürme
                columns = result_proxy.keys()
                rows = [dict(zip(columns, row)) for row in result_proxy.fetchall()]
                
                logger.info(f"SQL execution successful. Returned {len(rows)} results.")
                return rows
        
        # Ajanın çıktısını doğrudan liste/tuple formatında değerlendiriyoruz.
        # Bu, en son AGENT_PROMPT_PREFIX'ine uygun davranışıdır.
        if isinstance(output, str):
            try:
                # ast.literal_eval, string'i güvenli bir şekilde Python listesine çevirir.
                parsed_output = ast.literal_eval(output)

                # Sonuç tuple listesiyse, sözlük listesine çeviriyoruz.
                if isinstance(parsed_output, list) and all(isinstance(item, tuple) for item in parsed_output):
                    
                    # Veritabanından gelen sütun isimlerini almak için küçük bir sorgu yapıyoruz.
                    with engine.connect() as connection:
                        columns_result = connection.execute(text("PRAGMA table_info(araba_ilanlari)"))
                        columns = [col[1] for col in columns_result.fetchall()]

                    # Tuple listesini sözlük listesine çeviriyoruz.
                    rows = [dict(zip(columns, row)) for row in parsed_output]
                    return rows

                # Eğer çıktı tuple listesi değilse boş liste döndürür.
                return []

            except (ValueError, SyntaxError):
                logger.error(f"Could not parse agent string output: {output}")
                return []
        
        # Eğer çıktı zaten doğrudan bir liste ise, onu döndür.
        return output if isinstance(output, list) else []

    except TimeoutException:
        logger.error("SQL agent execution timed out after 40 seconds")
        raise ValueError("Sorgu işlemi zaman aşımına uğradı. Lütfen daha basit bir sorgu deneyin.")
    except Exception as e:
        logger.error(f"An error occurred during SQL agent execution: {e}", exc_info=True)
        raise ValueError(f"Failed to execute search query due to an agent or database error: {e}")
    

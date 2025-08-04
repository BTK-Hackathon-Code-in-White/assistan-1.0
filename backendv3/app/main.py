# app/main.py

import sys
import os
import uuid
import logging
import json
logger = logging.getLogger(__name__)
from typing import List, Dict, Optional, Any

# --- Project Setup ---
# Ensures that modules within the 'app' directory can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# warnings.filterwarnings("ignore")

# --- FastAPI and Pydantic Imports ---
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --- Local Module Imports ---
import database
from engine import process_chat_turn, SearchExecutionError
from parser import Filters, Exclusions, Inferred, RawEntities

# --- Application Setup ---
app = FastAPI(
    title="Conversational Car Search API",
    description="An API that allows users to find cars through a stateful conversation.",
    version="2.0.0"
)

# In-memory session storage. For production, use Redis or a similar persistent store.
SESSIONS: Dict[str, Dict[str, Any]] = {}

# --- API Models ---

class ChatRequest(BaseModel):
    user_query: str = Field(..., description="The user's latest message in the conversation.")
    session_id: Optional[str] = Field(None, description="The ID of the ongoing conversation. If null, a new session is created.")

class ChatResponse(BaseModel):
    session_id: str = Field(..., description="The unique ID for the conversation session.")
    response: str = Field(..., description="An AI-generated summary of the search results.")
    results: List[Dict] = Field(..., description="A list of up to 25 cars matching the query.")
    active_filters: Dict = Field(..., description="The currently active filters for the search.")
    inferred_assumptions: List[str] = Field(..., description="A list of assumptions made by the AI.")

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React frontend adresi
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Application Events ---
@app.on_event("startup")
async def startup_event():
    """On application startup, initialize the database."""
    database.init_db()

# --- API Endpoints ---

@app.get("/health", summary="Health Check")
async def health_check():
    """Provides a simple health check endpoint."""
    return {"status": "ok", "message": "All good!"}

@app.post("/chat", response_model=ChatResponse, summary="Continue or Start a Conversation")
async def search_and_chat(request: ChatRequest):

    session_id = request.session_id or str(uuid.uuid4())
    # Retrieve conversation history and determine the last known state of filters
    conversation_history = database.get_history_for_session(session_id)
    last_state = json.loads(conversation_history[-1]['filters_json']) if conversation_history else {}

    
    logger.info(f"Processing turn for session_id: {session_id}")
    
    try:
        # The engine now manages the conversational turn and returns all necessary components
        processed_data = process_chat_turn(request.user_query, last_state, conversation_history)
        
        # Save the new turn to the database
        database.add_turn_to_history(
            session_id,
            request.user_query,
            processed_data["updated_session_state"]
        )
        
        # Construct the final response
        return ChatResponse(
            session_id=session_id,
            response=processed_data["comment"],
            results=processed_data["results"],
            active_filters=processed_data["updated_session_state"].get("filters", {}),
            inferred_assumptions=processed_data["updated_session_state"].get("inferred", {}).get("assumptions", [])
        )

    except SearchExecutionError as e:
        logger.error(f"SearchExecutionError in session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"An unexpected error occurred in session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred.")

# --- Main Entry ---
if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    uvicorn.run(app, host="0.0.0.0", port=8000)
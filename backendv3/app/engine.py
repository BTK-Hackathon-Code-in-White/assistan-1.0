# app/engine.py

import logging
from typing import List, Dict, Any
from copy import deepcopy

from parser import parse_user_query
import langchain_agent
from brand_mapping import map_region_to_brands, map_brands_list
from langchain_core.prompts import ChatPromptTemplate

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SearchExecutionError(Exception):
    """Custom exception for errors during the search process."""
    pass

def merge_filters(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges newly parsed query data with existing session data.
    Handles context changes and diversity requests.
    """
    if not old_data:
        return new_data

    merged = deepcopy(old_data)
    
    # Check if user wants to reset filters or seek diversity
    reset_filters = new_data.get("inferred", {}).get("reset_filters", False)
    seek_diversity = new_data.get("inferred", {}).get("seek_diversity", False)
    
    if reset_filters:
        # Clear brand filters for variety
        if "marka" in merged.get("filters", {}):
            merged["filters"]["marka"] = []
            new_data.setdefault("inferred", {}).setdefault("assumptions", []).append(
                "Marka filtreleri çeşitlilik için temizlendi."
            )
    
    if seek_diversity:
        # Ensure brand filters are cleared for diversity
        if "marka" in merged.get("filters", {}) and merged["filters"]["marka"]:
            merged["filters"]["marka"] = []
            new_data.setdefault("inferred", {}).setdefault("assumptions", []).append(
                "Çeşitlilik için marka filtreleri kaldırıldı."
            )
    
    # Merge filters: new data takes precedence
    for key, value in new_data.get("filters", {}).items():
        if value is not None and value != []:
            merged["filters"][key] = value

    # Merge exclusions
    for key, value in new_data.get("exclusions", {}).items():
        if value is not None and value != []:
            merged["exclusions"][key] = value

    # Combine assumptions
    new_assumptions = new_data.get("inferred", {}).get("assumptions", [])
    merged["inferred"]["assumptions"].extend(a for a in new_assumptions if a not in merged["inferred"]["assumptions"])

    # Copy over the new inferred flags
    merged["inferred"]["reset_filters"] = new_data.get("inferred", {}).get("reset_filters", False)
    merged["inferred"]["seek_diversity"] = new_data.get("inferred", {}).get("seek_diversity", False)

    merged["confidence"] = new_data["confidence"]
    return merged

def generate_summary_comment(user_query: str, db_rows: List[Dict], conversation_history: List[Dict[str, Any]]) -> str:
    """
    Uses an LLM to generate a friendly, insightful summary of the search results.
    """

    # Prepare a concise view of the results for the LLM, using new schema
    summary_view = [
        {
            "marka": row.get("marka"),
            "seri": row.get("seri"),
            "model": row.get("model"),
            "yil": row.get("yil"),
            "km": row.get("km"),
            "fiyat": row.get("fiyat")
        }
        for row in db_rows
    ]

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a friendly and helpful car sales assistant. Your goal is to summarize findings and guide the user. Be concise and speak in Turkish."),
        ("human", """
        Kullanıcının önceki konuşmaları: "{conversation_history}"  

        Kullanıcının son isteği şuydu: "{query}"

        Buna dayanarak bulduğumuz ilk 5 eşleşen araba şunlar:
        {results}

        Lütfen bu sonuçların kısa ve bilgilendirici bir özetini yap. İlginç kalıpları (örneğin, yaş, fiyat aralığı) belirt ve kullanıcının aramasını daha da daraltmasına yardımcı olacak mantıklı bir sonraki adım veya soru öner. Örneğin, vites, yakıt türü veya ilgili görünüyorsa belirli bir özellik hakkında soru sorabilirsin.
        """),
    ])
    
    chain = prompt | langchain_agent.llm
    try:
        response = chain.invoke({"query": user_query, "results": str(db_rows), "conversation_history": str(conversation_history)})
        return response.content
    except Exception as e:
        logger.error(f"Failed to generate summary comment: {e}")
        return "İsteğinize göre sonuçlar burada."
    
def generate_conversation(user_query: str, conversation_history: List[Dict[str, Any]]) -> str:
    """
    Uses an LLM to generate a friendly, insightful summary of the search results.
    """

    user_query_history = [q["user_query"] for q in conversation_history]

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a friendly and helpful car sales assistant. Your goal is to summarize findings and guide the user. Be concise and speak in Turkish."),
        ("human", """
        Kullanıcının önceki konuşmaları: "{user_query_history}"  

        Kullanıcının son isteği şuydu: "{query}"

        Buna dayanarak bir eşleşme bulunamadı. Kullanıcı arabalar dışında bir sohbet etmek istiyor olabilir. Onunla samimi bir sohbet yap.
        """),
    ])
    
    chain = prompt | langchain_agent.llm
    try:
        response = chain.invoke({"query": user_query, "user_query_history": user_query_history})
        return response.content
    except Exception as e:
        logger.error(f"Failed to generate summary comment: {e}")
        return "Buna cevap veremeyeceğim."
    
def generate_conversation_didnt_find(user_query: str, conversation_history: List[Dict[str, Any]], final_filters: str) -> str:
    """
    Uses an LLM to generate a friendly, insightful summary of the search results.
    """

    user_query_history = [q["user_query"] for q in conversation_history]

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a friendly and helpful car sales assistant. Your goal is to summarize findings and guide the user. Be concise and speak in Turkish."),
        ("human", """
        Kullanıcının önceki konuşmaları: "{user_query_history}"  

        Kullanıcının son isteği şuydu: "{query}"
         
        Kullanıcının isteğinden ortaya çıkan kriterler: "{final_filters}"

        Buna dayanarak bir eşleşme bulunamadı. Kullanıcının kriterleri biraz dar olabilir, kriterleri yanlış anlamış olabilirsin veya belki de sadece şanssız günündedir ve bu kriterlere uygun araç yoktur. Bunu doğrulamak adına kullanı ile konuş. 
        """),
    ])
    
    chain = prompt | langchain_agent.llm
    try:
        response = chain.invoke({"query": user_query, "user_query_history": user_query_history, "final_filters": final_filters})
        return response.content
    except Exception as e:
        logger.error(f"Failed to generate summary comment: {e}")
        return "Buna cevap veremeyeceğim."


def process_chat_turn(user_query: str, session_state: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Orchestrates a single turn of a conversation, from parsing to result summarization.
    """
    logger.info(f"Starting new turn for query: '{user_query}'")

    newly_parsed_data = parse_user_query(user_query)
    merged_data = merge_filters(session_state, newly_parsed_data)
    logger.info(f"Merged filters: {merged_data.get('filters')}")
    logger.info(f"Merged filters confidence: {merged_data['confidence']}")

    if merged_data['confidence'] < 0.3:
        comment = generate_conversation(user_query, conversation_history)
        return {
            "comment": comment,
            "results": [],
            "updated_session_state": session_state
        }
    
    # Handle region-to-brand mapping, using the 'marka' filter
    # region = merged_data.get('raw_entities', {}).get('region')
    # if region and not merged_data['filters'].get('marka'):
    #     regional_brands = map_region_to_brands(region)
    #     if regional_brands:
    #         merged_data['filters']['marka'] = regional_brands
    #         inferred_msg = f"'{region}' bölgesinden marka listesi çıkarıldı: {regional_brands}"
    #         if inferred_msg not in merged_data['inferred']['assumptions']:
    #             merged_data['inferred']['assumptions'].append(inferred_msg)

    # Apply fuzzy brand mapping to normalize user input brands to database brands
    if merged_data.get('filters', {}).get('marka'):
        original_brands = merged_data['filters']['marka']
        normalized_brands = map_brands_list(original_brands)
        
        if normalized_brands != original_brands:
            merged_data['filters']['marka'] = normalized_brands
            original_str = ', '.join(original_brands)
            normalized_str = ', '.join(normalized_brands)
            inferred_msg = f"Marka isimleri veritabanına uyarlandı: '{original_str}' -> '{normalized_str}'"
            if inferred_msg not in merged_data['inferred']['assumptions']:
                merged_data['inferred']['assumptions'].append(inferred_msg)
            logger.info(f"Normalized brands from {original_brands} to {normalized_brands}")

    # Prepare SQL query task description with diversity instructions if needed
    seek_diversity = merged_data.get('inferred', {}).get('seek_diversity', False)
    
    if seek_diversity:
        sql_agent_task_description = (
            f"Based on the cumulative conversation, find diverse cars from DIFFERENT BRANDS that match the criteria below. "
            f"IMPORTANT: Prioritize variety - select cars from different brands to ensure diversity. "
            f"The user's most recent request was: '{user_query}'. "
            f"Focus on showing cars from multiple different brands rather than multiple cars from the same brand."
        )
    else:
        sql_agent_task_description = (
            f"Based on the cumulative conversation, find the cars that match the criteria below. "
            f"The user's most recent request was: '{user_query}'."
        )

    try:
        results = langchain_agent.run_sql_query_from_text(task=sql_agent_task_description, constraints=merged_data)
        logger.info(f"Agent returned {len(results)} results.")
    except ValueError as e:
        raise SearchExecutionError(f"Could not complete search. Reason: {e}") from e

    top_5_for_summary = results[:5]
    if not top_5_for_summary:
        comment = generate_conversation_didnt_find(user_query, conversation_history, merged_data.get('filters'))
    else: 
        comment = generate_summary_comment(user_query, top_5_for_summary, conversation_history)

    return {
        "comment": comment,
        "results": results,
        "updated_session_state": merged_data
    }
import requests
import os
import logging
import json
from dotenv import load_dotenv
import time
import re
logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from a .env file

# Hugging Face API details
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
# API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-1B"
# API_URL = "https://api-inference.huggingface.co/models/codellama/CodeLlama-7b-hf"
# API_URL = "https://api.deepseek.com/v1/query"
API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN") # Get the token from the environment

if not API_TOKEN:
    raise ValueError("HUGGINGFACE_API_TOKEN is not set in the environment.")


headers = {
    "Authorization": f"Bearer {API_TOKEN}"
}

# Function to call HF API
def call_huggingface_api(prompt, max_retries=3):
    payload = {"inputs": prompt}
    
    for attempt in range(max_retries):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            print(f"API Response: {result}")  # <== Debug print
            
            if isinstance(result, list) and "generated_text" in result[0]:
                return result[0]["generated_text"]
            else:
                logger.error(f"Unexpected API response format: {result}")
                return "Error: Unexpected API response format"
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Hugging Face API (attempt {attempt+1}/{max_retries}): {e}")
            time.sleep(2)

    return "Error: Failed to process query after multiple attempts."



def load_schema(schema_file="db_schema.json"):
    """
    Load the database schema from a JSON file.
    """
    try:
        with open(schema_file, "r") as file:
            schema = json.load(file)
        return schema
    except FileNotFoundError:
        logger.error(f"Schema file '{schema_file}' not found.")
        return None
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from schema file '{schema_file}'.")
        return None


def format_schema(schema):
    """
    Format the schema into a human-readable string for the prompt.
    """
    if not schema:
        return "No schema information available."

    schema_details = []
    for table, columns in schema.items():
        column_names = [col["Field"] for col in columns]
        schema_details.append(f"Table '{table}': Columns ({', '.join(column_names)})")
    return "\n".join(schema_details)

def extract_sql(response):
    sql_match = re.search(r"(SELECT|SHOW)\s.*", response, re.IGNORECASE)
    return sql_match.group(0) if sql_match else "Error: Failed to extract SQL"


def process_query(user_query, schema_file="db_schema.json"):
    schema = load_schema(schema_file)
    if not schema:
        print("Schema loading failed!")
        return {"user_query": user_query, "structured_query": None, "error": "Database schema not loaded."}

    formatted_schema = format_schema(schema)
    print(f"Formatted Schema:\n{formatted_schema}")  # Debug print

    prompt = (
        f"You are a MySQL query generator. Based on the given schema, generate a valid SQL query.\n"
        f"Schema:\n{formatted_schema}\n\n"
        f"Example:\n"
        f"User Query: Show all users who registered last month.\n"
        f"SQL: SELECT * FROM users WHERE registration_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH);\n\n"
        f"User Query: {user_query}\nSQL:"
    )


    structured_query = call_huggingface_api(prompt)
    print(f"Raw AI Response: {structured_query}")  # Debug print

    sql_query = extract_sql(structured_query)
    print(f"Extracted SQL Query: {sql_query}")  # Debug print

    if not sql_query or sql_query.lower() == "error: unexpected api response format":
        return {"user_query": user_query, "structured_query": None, "error": "Failed to generate a valid SQL query."}

    if not sql_query.lower().startswith(("select", "show")):
        return {"user_query": user_query, "structured_query": None, "error": "Invalid query type generated."}

    for table in schema.keys():
        if table.lower() in sql_query.lower():
            return {"user_query": user_query, "structured_query": sql_query}

    return {"user_query": user_query, "structured_query": None, "error": "Generated query references unknown table."}


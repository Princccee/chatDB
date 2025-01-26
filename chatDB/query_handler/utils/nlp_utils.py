import requests
import os
import logging
import json
from dotenv import load_dotenv

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
def call_huggingface_api(prompt):
    """
    Send a prompt to the Hugging Face Inference API and return the response.
    """
    payload = {"inputs": prompt}
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        result = response.json()
        # Ensure the response has the expected format
        if isinstance(result, list) and "generated_text" in result[0]:
            logger.info(f"API Response: {result}")
            return result[0]["generated_text"]
        else:
            logger.error(f"Unexpected API response format: {result}")
            return "Error: Unexpected API response format"
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Hugging Face API: {e}")
        return f"Error: {e}"


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
    if "SQL:" in response:
        return response.split("SQL:")[1].strip().split("\n")[0]
    return response


def process_query(user_query, schema_file="db_schema.json"):
    """
    Process the user's natural language query using Hugging Face's API,
    incorporating database schema details for better accuracy.
    """
    # Load and format the schema
    schema = load_schema(schema_file)
    formatted_schema = format_schema(schema)

    # Refined prompt with schema details and examples
    prompt = (
    "You are a helpful assistant that generates mySQL queries from natural language descriptions.\n\n"
    "Here is the database schema:\n"
    "Table 'departments': Columns (id, name, location)\n"
    "Table 'employees': Columns (id, name, position, joined_date, salary)\n"
    "Table 'projects': Columns (id, name, start_date, end_date, department_id)\n\n"
    "Example 1:\n"
    "Question: List all employees who joined in 2022.\n"
    "SQL: SELECT * FROM employees WHERE join_date BETWEEN '2022-01-01' AND '2022-12-31';\n\n"
    "Now, generate the SQL query for the following question:\n"
    f"Question: {user_query}\n"
    "SQL:"
    )
    structured_query = call_huggingface_api(prompt)
    sql_query = extract_sql(structured_query)
    return {
        "user_query": user_query,
        "structured_query": sql_query
    }

def test_process_query():
    sample_query = "List all employees who joined in 2022."
    result = process_query(sample_query)
    assert "SELECT" in result["structured_query"], "Query generation failed"

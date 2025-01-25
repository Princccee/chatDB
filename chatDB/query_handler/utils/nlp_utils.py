import requests
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from a .env file

# Hugging Face API details
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-small"
API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN") # Get the token from the environment

if not API_TOKEN:
    raise ValueError("HUGGINGFACE_API_TOKEN is not set in the environment.")


headers = {
    "Authorization": f"Bearer {API_TOKEN}"
}

def call_huggingface_api(prompt):
    """
    Send a prompt to the Hugging Face Inference API and return the response.
    """
    payload = {"inputs": prompt}
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
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

    

def process_query(user_query):
    """
    Process the user's natural language query using Hugging Face's API.
    """
    # Refined prompt with an example
    prompt = (
        "You are a helpful assistant that generates SQL queries from natural language descriptions.\n\n"
        "Example 1:\n"
        "Question: List all employees who joined in 2022.\n"
        "SQL: SELECT * FROM employees WHERE join_date BETWEEN '2022-01-01' AND '2022-12-31';\n\n"
        "Example 2:\n"
        "Question: Find all customers who made a purchase in December 2023.\n"
        "SQL: SELECT * FROM customers WHERE purchase_date BETWEEN '2023-12-01' AND '2023-12-31';\n\n"
        "Now, convert the following question into an SQL query:\n"
        f"Question: {user_query}\nSQL:"
    )
    structured_query = call_huggingface_api(prompt)
    return {
        "user_query": user_query,
        "structured_query": structured_query
    }

def test_process_query():
    sample_query = "List all employees who joined in 2022."
    result = process_query(sample_query)
    assert "SELECT" in result["structured_query"], "Query generation failed"

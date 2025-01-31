from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserQuery
from .serializers import UserQuerySerializer
from .utils.nlp_utils import process_query, load_schema
from django.http import JsonResponse
from django.db import connections
import mysql.connector
from mysql.connector import Error
from rest_framework.decorators import api_view
import json
from dotenv import load_dotenv
import os
load_dotenv()

# Establish a reusable database connection
DB_CONNECTION = None
SCHEMA_FILE = "db_schema.json"

def get_db_connection():
    global DB_CONNECTION
    if DB_CONNECTION and DB_CONNECTION.is_connected():
        return DB_CONNECTION  # Reuse if already connected

    try:
        DB_CONNECTION = mysql.connector.connect(
            host='localhost',  
            user='root',
            password=os.getenv('env_password'),  
            database='django_db',  
            port=3306
        )
        
        # Extract schema and save it
        extract_and_save_schema(DB_CONNECTION)

        return DB_CONNECTION
    except mysql.connector.Error as e:
        print(f"Error connecting to database: {e}")
        DB_CONNECTION = None
        return None
    

def extract_and_save_schema(connection):
    """Extracts the database schema and saves it to a JSON file."""
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]

        schema = {}

        for table in tables:
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            schema[table] = [{"name": col[0], "type": col[1]} for col in columns]

        # Save schema to a JSON file
        with open(SCHEMA_FILE, "w") as f:
            json.dump(schema, f, indent=4, default=str)

        print(f"Database schema saved to {SCHEMA_FILE}")

    except mysql.connector.Error as e:
        print(f"Error extracting schema: {e}")

    finally:
        cursor.close()
            

def connect_database_view(request):  # Django view must take `request`
    connection = get_db_connection()
    
    if connection:
        return JsonResponse({"message": "Database connection successful"})
    else:
        return JsonResponse({"error": "Failed to connect to the database"}, status=500)


def execute_query(query):
    connection = get_db_connection()
    if not connection:
        return {"error": "Failed to connect to the database."}

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)

        # Determine if the query is SELECT
        if cursor.description:  # This is only populated for SELECT queries
            results = cursor.fetchall()
        else:
            connection.commit()  # Ensure changes are saved for non-SELECT queries
            results = {"message": "Query executed successfully"}

        cursor.close()
        return results
    except mysql.connector.Error as e:
        print(f"SQL Execution Error: {e}")
        return {"error": f"SQL Execution Error: {e}"}
    finally:
        if connection and connection.is_connected():
            cursor.close()  # Close only the cursor, not the connection


class QueryView(APIView):
    def post(self, request):
        # Step 1: Save user query
        serializer = UserQuerySerializer(data=request.data)
        if serializer.is_valid():
            user_query = serializer.validated_data['query']

            # Step 2: Process the query using NLP model
            nlp_result = process_query(user_query)
            # print("NLP Result:", nlp_result)

            # Step 3: Execute the generated SQL query
            structured_query = nlp_result.get('structured_query')
            print(f"Generated SQL Query: {structured_query}")  # Debugging

            if not structured_query:
                return JsonResponse({"error": "Failed to generate a structured query."}, status=400)

            query_results = execute_query(structured_query)

            if "error" in query_results:
                return JsonResponse({"error": query_results["error"]}, status=500)

            # Step 4: Save the structured query and response
            user_query_instance = serializer.save(
                generated_query=structured_query,
                response=json.dumps(query_results, default=str)  # Convert dates & non-serializable objects
            )

            # Step 5: Return the processed data and query results
            return Response({
                "query": user_query_instance.query,
                "generated_query": user_query_instance.generated_query,
                "results": query_results  # No need for json.dumps() here; DRF handles it
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

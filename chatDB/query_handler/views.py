from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserQuery
from .serializers import UserQuerySerializer
from .utils.nlp_utils import process_query, load_schema
from django.http import JsonResponse
import mysql.connector
# from mysql.connector import Error
# from rest_framework.decorators import api_view
import json
from dotenv import load_dotenv
import os
load_dotenv()

# Establish a reusable database connection
DB_CONNECTION = None

def get_db_connection():
    """
    Singleton for database connection.
    """
    global DB_CONNECTION
    if not DB_CONNECTION or not DB_CONNECTION.is_connected():
        try:
            DB_CONNECTION = mysql.connector.connect(
                host='localhost',  
                user='root',
                password=os.getenv('env_password'),  
                database='django_db',  
                port=3306
            )
        except mysql.connector.Error as e:
            print(f"Error connecting to database: {e}")
            return None
    return DB_CONNECTION


def execute_query(query):
    """
    Execute a SQL query and return results.
    """
    connection = get_db_connection()
    if not connection:
        return {"error": "Failed to connect to the database."}

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results
    except mysql.connector.Error as e:
        print(f"SQL Execution Error: {e}")
        return {"error": f"SQL Execution Error: {e}"}
    

class QueryView(APIView):
    def post(self, request):
        # Step 1: Save user query
        serializer = UserQuerySerializer(data=request.data)
        if serializer.is_valid():
            user_query = serializer.validated_data['query']

            # Step 2: Process the query using NLP model
            nlp_result = process_query(user_query)

            # Step 3: Execute the generated SQL query
            structured_query = nlp_result['structured_query']
            query_results = execute_query(structured_query)

            if "error" in query_results:
                return JsonResponse({"error": query_results["error"]}, status=500)

            # Step 4: Save the structured query and response
            user_query_instance = serializer.save(
                generated_query=structured_query,
                response=json.dumps(query_results)
            )

            # Step 5: Return the processed data and query results
            return Response({
                "query": user_query_instance.query,
                "generated_query": user_query_instance.generated_query,
                "results": json.dumps(query_results, default=str)
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


# class QueryView(APIView):
#     def post(self, request):
#         # Step 1: Save user query
#         serializer = UserQuerySerializer(data=request.data)
#         if serializer.is_valid():
#             user_query = serializer.validated_data['query']

#             # Step 2: Process the query using Hugging Face API
#             nlp_result = process_query(user_query)

#             # Step 3: Save the structured query
#             user_query_instance = serializer.save(
#                 generated_query=nlp_result['structured_query'], # avriable thatis storing the actual query for the user prompt
#                 response=f"Processed query: {nlp_result['structured_query']}"
#             )

#             # Step 4: Return the processed data
#             return Response(UserQuerySerializer(user_query_instance).data, status=status.HTTP_201_CREATED)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['POST'])
# def connect_to_mysql(request):
#     """
#     Connect to MySQL database using user-provided credentials, extract schema details, 
#     and save the schema in a file named db_schema.json.
#     """
#     data = request.data
#     host = data.get('host', 'localhost')  # Default to localhost
#     user = data.get('user', 'root')      # Default to root
#     password = data.get('password', '')  # No default password
#     port = data.get('port', 3306)        # Default MySQL port
#     database = data.get('database')      # Database name is required

#     if not database:
#         return JsonResponse({"error": "Database name is required."}, status=400)

#     try:
#         # Connect to the MySQL database
#         connection = mysql.connector.connect(
#             host=host,
#             user=user,
#             password=password,
#             port=port,
#             database=database
#         )

#         if connection.is_connected():
#             # Fetch schema details
#             cursor = connection.cursor(dictionary=True)
#             cursor.execute("SHOW TABLES;")
#             tables = cursor.fetchall()

#             schema_info = {}
#             for table in tables:
#                 table_name = table[f"Tables_in_{database}"]
#                 cursor.execute(f"DESCRIBE {table_name};")
#                 columns = cursor.fetchall()
#                 schema_info[table_name] = columns

#             # Save the schema to a JSON file
#             with open('db_schema.json', 'w') as json_file:
#                 json.dump(schema_info, json_file, indent=4)

#             return JsonResponse({
#                 "message": "Connected to the database successfully!",
#                 "schema": schema_info
#             }, status=200)

#     except Error as e:
#         return JsonResponse({"error": str(e)}, status=500)

#     finally:
#         if 'connection' in locals() and connection.is_connected():
#             connection.close()

# # Fucntion to execute 
# def execute_query(self, query, params=None):
#         """
#         Execute a query and return results.
#         """
#         try:
#             cursor = self.connection.cursor(dictionary=True)  # Use dictionary=True for rows as dict
#             cursor.execute(query, params)
#             results = cursor.fetchall()
#             cursor.close()
#             return results
#         except Error as e:
#             print(f"Error executing query: {e}")
#             return None


# @api_view(['POST'])
# # Fucntion to executes to SQL query
# def process_response_and_execute_query(response):
#     """
#     Extracts the query from the response object and executes it using the provided database connector.

#     :param response: JSON object containing the query response
#     :param db_connector: Instance of DatabaseConnector
#     """
#     try:
#         # Parse the response JSON to extract the query
#         query = response.get("generated_query", None)
#         if query:
#             print(f"Executing query: {query}")
#             results = execute_query(query)
#             print("Query Results:")
#             for row in results:
#                 print(row)
#         else:
#             print("No query found in the response object.")
#     except Exception as e:
#         print(f"Error processing response: {e}")            
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserQuery
from .serializers import UserQuerySerializer
from .utils.nlp_utils import process_query
from django.http import JsonResponse

import mysql.connector
from mysql.connector import Error
from rest_framework.decorators import api_view
import json

class QueryView(APIView):
    def post(self, request):
        # Step 1: Save user query
        serializer = UserQuerySerializer(data=request.data)
        if serializer.is_valid():
            user_query = serializer.validated_data['query']

            # Step 2: Process the query using Hugging Face API
            nlp_result = process_query(user_query)

            # Step 3: Save the structured query
            user_query_instance = serializer.save(
                generated_query=nlp_result['structured_query'],
                response=f"Processed query: {nlp_result['structured_query']}"
            )

            # Step 4: Return the processed data
            return Response(UserQuerySerializer(user_query_instance).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def connect_to_mysql(request):
    """
    Connect to MySQL database using user-provided credentials, extract schema details, 
    and save the schema in a file named db_schema.json.
    """
    data = request.data
    host = data.get('host', 'localhost')  # Default to localhost
    user = data.get('user', 'root')      # Default to root
    password = data.get('password', '')  # No default password
    port = data.get('port', 3306)        # Default MySQL port
    database = data.get('database')      # Database name is required

    if not database:
        return JsonResponse({"error": "Database name is required."}, status=400)

    try:
        # Connect to the MySQL database
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            port=port,
            database=database
        )

        if connection.is_connected():
            # Fetch schema details
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()

            schema_info = {}
            for table in tables:
                table_name = table[f"Tables_in_{database}"]
                cursor.execute(f"DESCRIBE {table_name};")
                columns = cursor.fetchall()
                schema_info[table_name] = columns

            # Save the schema to a JSON file
            with open('db_schema.json', 'w') as json_file:
                json.dump(schema_info, json_file, indent=4)

            return JsonResponse({
                "message": "Connected to the database successfully!",
                "schema": schema_info
            }, status=200)

    except Error as e:
        return JsonResponse({"error": str(e)}, status=500)

    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
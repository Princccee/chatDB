import json
import mysql.connector
from mysql.connector import Error

class DatabaseConnector:
    def __init__(self, host, user, password, database):
        """
        Initialize the database connector.
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        """
        Establish a connection to the database.
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                print("Connected to the database")
        except Error as e:
            print(f"Error connecting to database: {e}")

    def execute_query(self, query, params=None):
        """
        Execute a query and return results.
        """
        try:
            cursor = self.connection.cursor(dictionary=True)  # Use dictionary=True for rows as dict
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            print(f"Error executing query: {e}")
            return None

    def close(self):
        """
        Close the database connection.
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")


def process_response_and_execute_query(response, db_connector):
    """
    Extracts the query from the response object and executes it using the provided database connector.

    :param response: JSON object containing the query response
    :param db_connector: Instance of DatabaseConnector
    """
    try:
        # Parse the response JSON to extract the query
        query = response.get("generated_query", None)
        if query:
            print(f"Executing query: {query}")
            results = db_connector.execute_query(query)
            print("Query Results:")
            for row in results:
                print(row)
        else:
            print("No query found in the response object.")
    except Exception as e:
        print(f"Error processing response: {e}")


if __name__ == "__main__":
    # Database connection details
    HOST = "localhost"
    USER = "your_user"
    PASSWORD = "your_password"
    DATABASE = "your_database"

    # Example response object
    response = {
        "id": 36,
        "query": "Find all employees who work in the HR department.",
        "generated_query": "SELECT * FROM employees WHERE department = 'HR'",
        "response": "Processed query: SELECT * FROM employees WHERE department = 'HR'",
        "timestamp": "2025-01-27T09:16:59.363479Z"
    }

    # Initialize the database connector
    db = DatabaseConnector(host=HOST, user=USER, password=PASSWORD, database=DATABASE)

    # Connect to the database
    db.connect()

    # Process the response and execute the query
    process_response_and_execute_query(response, db)

    # Close the database connection
    db.close()

import subprocess
import sys

def install_requirements(requirements_file):
    try:
        # Execute the pip install command
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
        print(f"Successfully installed packages from {requirements_file}.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while installing packages: {e}")

# Usage
requirements_file = 'requirements.txt'  # Path to your requirements.txt file
install_requirements(requirements_file)

import mysql.connector

# Function to execute a .sql file
def execute_sql_file(file_path, host='localhost', user='root', password='1234'):
    # Establish connection to the MySQL server
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password
    )

    cursor = connection.cursor()

    cursor.execute('create database if not exists onlinebanksystem')
    cursor.execute('use onlinebanksystem')

    try:
        # Read the .sql file
        with open(file_path, 'r') as sql_file:
            sql_commands = sql_file.read()

        # Execute the SQL commands
        for command in sql_commands.split(';'):
            if command.strip():
                cursor.execute(command)

        # Commit changes
        connection.commit()
        print("SQL commands executed successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        connection.rollback()

    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()

file_path = 'onlinebanksystem.sql'
execute_sql_file(file_path)

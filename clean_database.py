"""
Database Reset Utility
Clears all data and resets auto-increment counters
"""

import sqlite3

DATABASE_LOCATION = "museum_data.db"

def clear_database_contents():
    """
    Remove all records from database tables
    Reset auto-increment sequence for clean restart
    """
    connection = None
    try:
        connection = sqlite3.connect(DATABASE_LOCATION)
        executor = connection.cursor()

        # Remove data in correct foreign key order
        tables_to_clear = [
            "guest_visit",
            "item_maintenance",
            "museum_item",
            "guest",
            "museum"
        ]

        for table in tables_to_clear:
            executor.execute(f"DELETE FROM {table}")

        # Reset sequence counters only if sqlite_sequence exists
        # First check if the table exists
        executor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='sqlite_sequence'
        """)

        if executor.fetchone():
            executor.execute("DELETE FROM sqlite_sequence")
            print("Auto-increment counters reset.")
        else:
            print("No auto-increment tables detected.")

        connection.commit()
        print("Database reset completed successfully.")

    except sqlite3.Error as db_error:
        print(f"Database error occurred: {db_error}")

    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    clear_database_contents()
import sqlite3
from pathlib import Path

DATABASE_PATH = Path.cwd() / "museum_data.db"

def initialize_database_structure():
    """
    Establishes database connection and creates necessary tables
    Returns connection object for immediate use
    """
    database_connection = sqlite3.connect(str(DATABASE_PATH))
    db_cursor = database_connection.cursor()

    table_definitions = [
        """
        CREATE TABLE IF NOT EXISTS museum (
            id INTEGER PRIMARY KEY,
            museum_name TEXT NOT NULL,
            city TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS museum_item (
            item_id INTEGER PRIMARY KEY,
            museum_ref INTEGER NOT NULL,
            item_title TEXT NOT NULL,
            item_type TEXT,
            date_acquired DATE,
            FOREIGN KEY (museum_ref) REFERENCES museum(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS item_maintenance (
            maintenance_id INTEGER PRIMARY KEY,
            item_ref INTEGER NOT NULL,
            maintenance_type TEXT NOT NULL,
            maintenance_date DATE NOT NULL,
            specialist_name TEXT,
            FOREIGN KEY (item_ref) REFERENCES museum_item(item_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS guest (
            guest_id INTEGER PRIMARY KEY,
            guest_name TEXT NOT NULL,
            contact_email TEXT UNIQUE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS guest_visit (
            visit_id INTEGER PRIMARY KEY,
            guest_ref INTEGER NOT NULL,
            museum_ref INTEGER NOT NULL,
            visit_date DATE NOT NULL,
            FOREIGN KEY (guest_ref) REFERENCES guest(guest_id),
            FOREIGN KEY (museum_ref) REFERENCES museum(id)
        );
        """
    ]

    for table_sql in table_definitions:
        db_cursor.execute(table_sql)

    database_connection.commit()
    database_connection.close()

    print("Museum database ready for operation.")
    return True

if __name__ == "__main__":
    initialize_database_structure()
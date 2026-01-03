import sqlite3
from pathlib import Path
import hashlib

DATABASE_PATH = Path.cwd() / "museum_data.db"

def initialize_database_structure():
    """
    Establishes database connection and creates necessary tables with:
    - Proper constraints for data integrity
    - Triggers for audit logging
    - Indexes for performance optimization
    - User authentication tables
    """
    database_connection = sqlite3.connect(str(DATABASE_PATH))
    db_cursor = database_connection.cursor()

    # Enable foreign key constraints
    db_cursor.execute("PRAGMA foreign_keys = ON;")

    table_definitions = [
        # User authentication table with role-based access
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'curator', 'viewer')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1))
        );
        """,

        # Audit log table for tracking changes
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            table_name TEXT NOT NULL,
            action TEXT NOT NULL CHECK(action IN ('INSERT', 'UPDATE', 'DELETE')),
            record_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        """,

        # Enhanced museum table with constraints
        """
        CREATE TABLE IF NOT EXISTS museum (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            museum_name TEXT NOT NULL CHECK(length(museum_name) > 0),
            city TEXT NOT NULL CHECK(length(city) > 0),
            address TEXT,
            phone TEXT,
            opening_hours TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(museum_name, city)
        );
        """,

        # Enhanced museum_item table with validation
        """
        CREATE TABLE IF NOT EXISTS museum_item (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            museum_ref INTEGER NOT NULL,
            item_title TEXT NOT NULL CHECK(length(item_title) > 0),
            item_type TEXT CHECK(length(item_type) > 0),
            date_acquired DATE NOT NULL,
            description TEXT,
            condition TEXT CHECK(condition IN ('Excellent', 'Good', 'Fair', 'Poor', 'Restoration Required')),
            value REAL CHECK(value >= 0),
            is_on_display INTEGER DEFAULT 1 CHECK(is_on_display IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (museum_ref) REFERENCES museum(id) ON DELETE CASCADE
        );
        """,

        # Enhanced maintenance table
        """
        CREATE TABLE IF NOT EXISTS item_maintenance (
            maintenance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_ref INTEGER NOT NULL,
            maintenance_type TEXT NOT NULL CHECK(length(maintenance_type) > 0),
            maintenance_date DATE NOT NULL CHECK(maintenance_date <= date('now')),
            specialist_name TEXT NOT NULL,
            cost REAL CHECK(cost >= 0),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_ref) REFERENCES museum_item(item_id) ON DELETE CASCADE
        );
        """,

        # Enhanced guest table with validation
        """
        CREATE TABLE IF NOT EXISTS guest (
            guest_id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_name TEXT NOT NULL CHECK(length(guest_name) > 0),
            contact_email TEXT UNIQUE NOT NULL CHECK(contact_email LIKE '%_@_%._%'),
            phone TEXT,
            membership_type TEXT CHECK(membership_type IN ('None', 'Basic', 'Premium', 'Family')),
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,

        # Enhanced visit table
        """
        CREATE TABLE IF NOT EXISTS guest_visit (
            visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_ref INTEGER NOT NULL,
            museum_ref INTEGER NOT NULL,
            visit_date DATE NOT NULL CHECK(visit_date <= date('now')),
            ticket_price REAL CHECK(ticket_price >= 0),
            rating INTEGER CHECK(rating BETWEEN 1 AND 5),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (guest_ref) REFERENCES guest(guest_id) ON DELETE CASCADE,
            FOREIGN KEY (museum_ref) REFERENCES museum(id) ON DELETE CASCADE
        );
        """
    ]

    for table_sql in table_definitions:
        db_cursor.execute(table_sql)

    # Create performance indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_museum_item_museum ON museum_item(museum_ref);",
        "CREATE INDEX IF NOT EXISTS idx_maintenance_item ON item_maintenance(item_ref);",
        "CREATE INDEX IF NOT EXISTS idx_maintenance_date ON item_maintenance(maintenance_date);",
        "CREATE INDEX IF NOT EXISTS idx_visit_guest ON guest_visit(guest_ref);",
        "CREATE INDEX IF NOT EXISTS idx_visit_museum ON guest_visit(museum_ref);",
        "CREATE INDEX IF NOT EXISTS idx_visit_date ON guest_visit(visit_date);",
        "CREATE INDEX IF NOT EXISTS idx_guest_email ON guest(contact_email);",
        "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);"
    ]

    for index_sql in indexes:
        db_cursor.execute(index_sql)

    # Create triggers for automatic timestamp updates
    triggers = [
        """
        CREATE TRIGGER IF NOT EXISTS update_museum_timestamp
        AFTER UPDATE ON museum
        BEGIN
            UPDATE museum SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
        """,
        """
        CREATE TRIGGER IF NOT EXISTS update_item_timestamp
        AFTER UPDATE ON museum_item
        BEGIN
            UPDATE museum_item SET updated_at = CURRENT_TIMESTAMP WHERE item_id = NEW.item_id;
        END;
        """,
        # Trigger to prevent deletion of items with maintenance history
        """
        CREATE TRIGGER IF NOT EXISTS prevent_item_deletion_with_history
        BEFORE DELETE ON museum_item
        WHEN (SELECT COUNT(*) FROM item_maintenance WHERE item_ref = OLD.item_id) > 0
        BEGIN
            SELECT RAISE(ABORT, 'Cannot delete item with maintenance history. Archive instead.');
        END;
        """,
        # Trigger to validate visit dates are not in future
        """
        CREATE TRIGGER IF NOT EXISTS validate_visit_date
        BEFORE INSERT ON guest_visit
        WHEN NEW.visit_date > date('now')
        BEGIN
            SELECT RAISE(ABORT, 'Visit date cannot be in the future');
        END;
        """
    ]

    for trigger_sql in triggers:
        db_cursor.execute(trigger_sql)

    # Create default admin user if not exists
    default_admin_password = hashlib.sha256("admin123".encode()).hexdigest()
    db_cursor.execute("""
        INSERT OR IGNORE INTO users (username, password_hash, role)
        VALUES (?, ?, ?)
    """, ("admin", default_admin_password, "admin"))

    database_connection.commit()
    database_connection.close()
    print("Enhanced museum database ready with security and integrity features.")
    return True

if __name__ == "__main__":
    initialize_database_structure()


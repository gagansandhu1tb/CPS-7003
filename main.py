import sqlite3

DATABASE_FILE = "museum_data.db"

class MuseumDB:
    """Database interaction handler for museum operations"""

    def __init__(self):
        self.db_file = DATABASE_FILE

    def _connect(self):
        """Create database connection"""
        return sqlite3.connect(self.db_file)

    def _execute_write(self, query, params=None):
        """Execute write operations with proper transaction handling"""
        with self._connect() as conn:
            if params:
                conn.execute(query, params)
            else:
                conn.execute(query)

    def _execute_read(self, query, params=None):
        """Execute read operations and return results"""
        with self._connect() as conn:
            if params:
                result = conn.execute(query, params).fetchall()
            else:
                result = conn.execute(query).fetchall()
        return result

    # Museum operations
    def add_museum(self, museum_name, city):
        """Register new museum"""
        self._execute_write(
            "INSERT OR IGNORE INTO museum (museum_name, city) VALUES (?, ?)",
            (museum_name, city)
        )

    def list_museums(self):
        """Retrieve all museum records"""
        return self._execute_read("SELECT * FROM museum ORDER BY id")

    def modify_museum(self, museum_id, new_name, new_city):
        """Update museum information"""
        self._execute_write(
            "UPDATE museum SET museum_name=?, city=? WHERE id=?",
            (new_name, new_city, museum_id)
        )

    def remove_museum(self, museum_id):
        """Delete museum record"""
        self._execute_write("DELETE FROM museum WHERE id=?", (museum_id,))

    # Exhibit operations
    def add_exhibit(self, museum_id, title, category, acquisition_date):
        """Add new exhibit to museum"""
        self._execute_write(
            """INSERT INTO museum_item (museum_ref, item_title, item_type, date_acquired)
               VALUES (?, ?, ?, ?)""",
            (museum_id, title, category, acquisition_date)
        )

    def list_exhibits(self):
        """Get all exhibits"""
        return self._execute_read("SELECT * FROM museum_item")

    def rename_exhibit(self, exhibit_id, new_title):
        """Update exhibit title"""
        self._execute_write(
            "UPDATE museum_item SET item_title=? WHERE item_id=?",
            (new_title, exhibit_id)
        )

    def remove_exhibit(self, exhibit_id):
        """Delete exhibit record"""
        self._execute_write("DELETE FROM museum_item WHERE item_id=?", (exhibit_id,))

    # Maintenance operations
    def record_maintenance(self, exhibit_id, action, date, specialist):
        """Log conservation activity"""
        self._execute_write(
            """INSERT INTO item_maintenance (item_ref, maintenance_type, maintenance_date, specialist_name)
               VALUES (?, ?, ?, ?)""",
            (exhibit_id, action, date, specialist)
        )

    def get_maintenance_log(self):
        """Retrieve all maintenance records"""
        return self._execute_read("SELECT * FROM item_maintenance")

    def update_maintenance_action(self, maintenance_id, new_action):
        """Modify maintenance record"""
        self._execute_write(
            "UPDATE item_maintenance SET maintenance_type=? WHERE maintenance_id=?",
            (new_action, maintenance_id)
        )

    def delete_maintenance_record(self, maintenance_id):
        """Remove maintenance entry"""
        self._execute_write("DELETE FROM item_maintenance WHERE maintenance_id=?", (maintenance_id,))

    # Visitor operations
    def register_visitor(self, name, email):
        """Add visitor to database"""
        self._execute_write(
            "INSERT OR IGNORE INTO guest (guest_name, contact_email) VALUES (?, ?)",
            (name, email)
        )

    def list_visitors(self):
        """Get all visitors"""
        return self._execute_read("SELECT * FROM guest")

    def update_visitor_email(self, visitor_id, new_email):
        """Change visitor email"""
        self._execute_write(
            "UPDATE guest SET contact_email=? WHERE guest_id=?",
            (new_email, visitor_id)
        )

    def delete_visitor(self, visitor_id):
        """Remove visitor record"""
        self._execute_write("DELETE FROM guest WHERE guest_id=?", (visitor_id,))

    # Visit operations
    def log_visit(self, visitor_id, museum_id, date):
        """Record museum visit"""
        self._execute_write(
            "INSERT INTO guest_visit (guest_ref, museum_ref, visit_date) VALUES (?, ?, ?)",
            (visitor_id, museum_id, date)
        )

    def get_visit_records(self):
        """Retrieve all visits"""
        return self._execute_read("SELECT * FROM guest_visit")

    def change_visit_date(self, visit_id, new_date):
        """Update visit date"""
        self._execute_write(
            "UPDATE guest_visit SET visit_date=? WHERE visit_id=?",
            (new_date, visit_id)
        )

    def remove_visit(self, visit_id):
        """Delete visit record"""
        self._execute_write("DELETE FROM guest_visit WHERE visit_id=?", (visit_id,))

    # Analytical queries
    def get_exhibits_with_museum_info(self):
        """Join exhibits with museum details"""
        return self._execute_read("""
            SELECT mi.item_title, mi.item_type, m.museum_name
            FROM museum_item mi
            INNER JOIN museum m ON mi.museum_ref = m.id
        """)

    def get_maintenance_history_sorted(self):
        """Maintenance records with exhibit info, sorted by date"""
        return self._execute_read("""
            SELECT mi.item_title, im.maintenance_type, im.maintenance_date, im.specialist_name
            FROM item_maintenance im
            JOIN museum_item mi ON im.item_ref = mi.item_id
            ORDER BY im.maintenance_date DESC
        """)

    def count_exhibits_by_museum(self):
        """Calculate exhibits per museum"""
        return self._execute_read("""
            SELECT m.museum_name, COUNT(mi.item_id) AS exhibit_count
            FROM museum m
            LEFT OUTER JOIN museum_item mi ON m.id = mi.museum_ref
            GROUP BY m.id
        """)

    def count_visits_by_museum(self):
        """Calculate visit frequency per museum"""
        return self._execute_read("""
            SELECT m.museum_name, COUNT(gv.visit_id) AS visitor_count
            FROM guest_visit gv
            INNER JOIN museum m ON gv.museum_ref = m.id
            GROUP BY m.id
        """)

    def get_visitor_timeline(self):
        """Visitor history with museum visits"""
        return self._execute_read("""
            SELECT g.guest_name, m.museum_name, gv.visit_date
            FROM guest_visit gv
            INNER JOIN guest g ON gv.guest_ref = g.guest_id
            INNER JOIN museum m ON gv.museum_ref = m.id
            ORDER BY gv.visit_date
        """)


def demonstrate_functionality():
    """Showcase database operations"""
    db_manager = MuseumDB()

    # Create sample data
    db_manager.add_museum("National History Museum", "Karachi")

    db_manager.add_exhibit(1, "Ancient Vase", "Archaeology", "2021-01-01")
    db_manager.add_exhibit(1, "Medieval Sword", "Weapons", "2022-03-15")
    db_manager.add_exhibit(1, "Historic Painting", "Art", "2023-05-10")

    db_manager.register_visitor("Ali Khan", "ali@example.com")
    db_manager.register_visitor("Sara Ahmed", "sara@example.com")
    db_manager.register_visitor("Usman Raza", "usman@example.com")

    db_manager.record_maintenance(1, "Cleaning", "2024-01-01", "Dr. Ahmed")
    db_manager.record_maintenance(2, "Rust Removal", "2024-02-01", "Ms. Fatima")
    db_manager.record_maintenance(3, "Frame Repair", "2024-03-01", "Mr. Hassan")

    db_manager.log_visit(1, 1, "2024-04-01")
    db_manager.log_visit(2, 1, "2024-04-02")
    db_manager.log_visit(3, 1, "2024-04-03")

    print("Registered Museums:", db_manager.list_museums())
    print("Current Exhibits:", db_manager.list_exhibits())

    # Update operations
    db_manager.rename_exhibit(1, "Ancient Greek Vase")
    db_manager.update_visitor_email(1, "ali.khan@example.com")

    # Delete operations
    db_manager.remove_visit(3)
    db_manager.delete_maintenance_record(2)

    print("Modified Exhibits:", db_manager.list_exhibits())
    print("Remaining Visits:", db_manager.get_visit_records())

    # Database Queries (GROUPING, JOINS, ORDER BY)
    print("\n--- Exhibits with Museum Details ---")
    for record in db_manager.get_exhibits_with_museum_info():
        print(record)

    print("\n--- Maintenance History (Recent First) ---")
    for record in db_manager.get_maintenance_history_sorted():
        print(record)

    print("\n--- Exhibit Distribution ---")
    for record in db_manager.count_exhibits_by_museum():
        print(record)

    print("\n--- Museum Popularity ---")
    for record in db_manager.count_visits_by_museum():
        print(record)

    print("\n--- Visitor Timeline ---")
    for record in db_manager.get_visitor_timeline():
        print(record)


if __name__ == "__main__":
    demonstrate_functionality()
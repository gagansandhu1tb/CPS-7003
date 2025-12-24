import sqlite3
from pathlib import Path

DB_PATH = Path.cwd() / "museum_data.db"


class DatabaseConnection:
    """Centralized DB connection handler"""

    @staticmethod
    def connect():
        return sqlite3.connect(DB_PATH)


class MuseumDAL:
    """Data Access Layer for museum operations"""

    def execute_write(self, query, params=()):
        with DatabaseConnection.connect() as conn:
            conn.execute(query, params)
            conn.commit()

    def execute_read(self, query, params=()):
        with DatabaseConnection.connect() as conn:
            return conn.execute(query, params).fetchall()


class MuseumRepository(MuseumDAL):

    def add_museum(self, name, city):
        self.execute_write(
            "INSERT OR IGNORE INTO museum (museum_name, city) VALUES (?, ?)",
            (name, city)
        )

    def get_all_museums(self):
        return self.execute_read("SELECT * FROM museum")


class ExhibitRepository(MuseumDAL):

    def add_exhibit(self, museum_id, title, category, date):
        self.execute_write(
            """INSERT INTO museum_item
               (museum_ref, item_title, item_type, date_acquired)
               VALUES (?, ?, ?, ?)""",
            (museum_id, title, category, date)
        )

    def get_all_exhibits(self):
        return self.execute_read("SELECT * FROM museum_item")

    def top_exhibits(self):
        """ADVANCED QUERY"""
        return self.execute_read("""
            SELECT mi.item_title, COUNT(im.maintenance_id) AS maintenance_count
            FROM museum_item mi
            LEFT JOIN item_maintenance im ON mi.item_id = im.item_ref
            GROUP BY mi.item_id
            ORDER BY maintenance_count DESC
        """)


class VisitorRepository(MuseumDAL):

    def register_visitor(self, name, email):
        self.execute_write(
            "INSERT OR IGNORE INTO guest (guest_name, contact_email) VALUES (?, ?)",
            (name, email)
        )

    def visitor_activity(self):
        """ADVANCED QUERY"""
        return self.execute_read("""
            SELECT g.guest_name, COUNT(gv.visit_id) AS visits
            FROM guest g
            JOIN guest_visit gv ON g.guest_id = gv.guest_ref
            GROUP BY g.guest_id
            ORDER BY visits DESC
        """)

    def log_visit(self, visitor_id, museum_id, date):
        self.execute_write(
            """INSERT INTO guest_visit
               (guest_ref, museum_ref, visit_date)
               VALUES (?, ?, ?)""",
            (visitor_id, museum_id, date)
        )


class MaintenanceRepository(MuseumDAL):

    def add_maintenance(self, item_id, action, date, specialist):
        self.execute_write(
            """INSERT INTO item_maintenance
               (item_ref, maintenance_type, maintenance_date, specialist_name)
               VALUES (?, ?, ?, ?)""",
            (item_id, action, date, specialist)
        )

    def maintenance_summary(self):
        """ADVANCED QUERY"""
        return self.execute_read("""
            SELECT mi.item_title, COUNT(im.maintenance_id) AS total_actions
            FROM museum_item mi
            JOIN item_maintenance im ON mi.item_id = im.item_ref
            GROUP BY mi.item_id
        """)

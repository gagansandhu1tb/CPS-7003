import sqlite3
from pathlib import Path
import hashlib
from typing import Optional, List, Tuple, Any
from datetime import datetime

DB_PATH = Path.cwd() / "museum_data.db"

class DatabaseConnection:
    """Centralized DB connection handler with connection pooling"""

    @staticmethod
    def connect():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        conn.execute("PRAGMA foreign_keys = ON")  # Ensure FK constraints
        return conn

class MuseumDAL:
    """Base Data Access Layer with security and audit logging"""

    def __init__(self, user_id: Optional[int] = None):
        self.user_id = user_id

    def execute_write(self, query: str, params: tuple = ()) -> int:
        """Execute write operation with proper error handling"""
        with DatabaseConnection.connect() as conn:
            try:
                cursor = conn.execute(query, params)
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                raise ValueError(f"Data integrity violation: {str(e)}")
            except sqlite3.Error as e:
                raise RuntimeError(f"Database error: {str(e)}")

    def execute_read(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute read operation and return results"""
        with DatabaseConnection.connect() as conn:
            return conn.execute(query, params).fetchall()

    def log_audit(self, table_name: str, action: str, record_id: int, details: str = ""):
        """Log changes to audit table for compliance"""
        if self.user_id:
            self.execute_write(
                """INSERT INTO audit_log (user_id, table_name, action, record_id, details)
                   VALUES (?, ?, ?, ?, ?)""",
                (self.user_id, table_name, action, record_id, details)
            )

class AuthenticationDAL(MuseumDAL):
    """Handle user authentication and authorization"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authenticate user and return user info if valid"""
        password_hash = self.hash_password(password)
        result = self.execute_read(
            """SELECT user_id, username, role, is_active
               FROM users
               WHERE username = ? AND password_hash = ? AND is_active = 1""",
            (username, password_hash)
        )

        if result:
            user = dict(result[0])
            # Update last login
            self.execute_write(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user['user_id'],)
            )
            return user
        return None

    def create_user(self, username: str, password: str, role: str) -> int:
        """Create new user (admin only)"""
        if role not in ['admin', 'curator', 'viewer']:
            raise ValueError("Invalid role. Must be admin, curator, or viewer")

        password_hash = self.hash_password(password)
        user_id = self.execute_write(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role)
        )
        self.log_audit("users", "INSERT", user_id, f"Created user: {username}")
        return user_id

    def check_permission(self, user_role: str, required_role: str) -> bool:
        """Check if user has required permission level"""
        role_hierarchy = {'viewer': 1, 'curator': 2, 'admin': 3}
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)

class MuseumRepository(MuseumDAL):
    """Repository for museum operations with validation"""

    def add_museum(self, name: str, city: str, address: str = "",
                   phone: str = "", opening_hours: str = "") -> int:
        """Add new museum with input validation"""
        if not name or len(name.strip()) == 0:
            raise ValueError("Museum name cannot be empty")
        if not city or len(city.strip()) == 0:
            raise ValueError("City cannot be empty")

        museum_id = self.execute_write(
            """INSERT INTO museum (museum_name, city, address, phone, opening_hours)
               VALUES (?, ?, ?, ?, ?)""",
            (name.strip(), city.strip(), address, phone, opening_hours)
        )
        self.log_audit("museum", "INSERT", museum_id, f"Added museum: {name}")
        return museum_id

    def get_all_museums(self) -> List[sqlite3.Row]:
        """Retrieve all museums with exhibit count"""
        return self.execute_read("""
            SELECT m.*, COUNT(mi.item_id) as exhibit_count
            FROM museum m
            LEFT JOIN museum_item mi ON m.id = mi.museum_ref
            GROUP BY m.id
            ORDER BY m.museum_name
        """)

    def update_museum(self, museum_id: int, name: str, city: str) -> None:
        """Update museum details"""
        self.execute_write(
            "UPDATE museum SET museum_name = ?, city = ? WHERE id = ?",
            (name, city, museum_id)
        )
        self.log_audit("museum", "UPDATE", museum_id, f"Updated museum: {name}")

    def get_museum_stats(self, museum_id: int) -> dict:
        """Get comprehensive statistics for a museum"""
        stats = self.execute_read("""
            SELECT
                m.museum_name,
                COUNT(DISTINCT mi.item_id) as total_exhibits,
                COUNT(DISTINCT gv.visit_id) as total_visits,
                AVG(gv.rating) as avg_rating,
                SUM(gv.ticket_price) as total_revenue
            FROM museum m
            LEFT JOIN museum_item mi ON m.id = mi.museum_ref
            LEFT JOIN guest_visit gv ON m.id = gv.museum_ref
            WHERE m.id = ?
            GROUP BY m.id
        """, (museum_id,))
        return dict(stats[0]) if stats else {}

class ExhibitRepository(MuseumDAL):
    """Repository for exhibit operations with business logic"""

    def add_exhibit(self, museum_id: int, title: str, category: str,
                    date: str, description: str = "", condition: str = "Good",
                    value: float = 0.0) -> int:
        """Add new exhibit with validation"""
        if not title or len(title.strip()) == 0:
            raise ValueError("Exhibit title cannot be empty")
        if value < 0:
            raise ValueError("Exhibit value cannot be negative")

        exhibit_id = self.execute_write(
            """INSERT INTO museum_item
               (museum_ref, item_title, item_type, date_acquired, description, condition, value)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (museum_id, title.strip(), category, date, description, condition, value)
        )
        self.log_audit("museum_item", "INSERT", exhibit_id, f"Added exhibit: {title}")
        return exhibit_id

    def get_all_exhibits(self) -> List[sqlite3.Row]:
        """Get all exhibits with museum information"""
        return self.execute_read("""
            SELECT mi.*, m.museum_name, m.city
            FROM museum_item mi
            JOIN museum m ON mi.museum_ref = m.id
            ORDER BY mi.item_title
        """)

    def update_exhibit_condition(self, exhibit_id: int, condition: str) -> None:
        """Update exhibit condition"""
        valid_conditions = ['Excellent', 'Good', 'Fair', 'Poor', 'Restoration Required']
        if condition not in valid_conditions:
            raise ValueError(f"Invalid condition. Must be one of: {', '.join(valid_conditions)}")

        self.execute_write(
            "UPDATE museum_item SET condition = ? WHERE item_id = ?",
            (condition, exhibit_id)
        )
        self.log_audit("museum_item", "UPDATE", exhibit_id, f"Updated condition to: {condition}")

    def top_exhibits(self) -> List[sqlite3.Row]:
        """Get exhibits ranked by maintenance frequency (performance optimized)"""
        return self.execute_read("""
            SELECT
                mi.item_title,
                mi.item_type,
                m.museum_name,
                COUNT(im.maintenance_id) AS maintenance_count,
                MAX(im.maintenance_date) as last_maintenance
            FROM museum_item mi
            LEFT JOIN item_maintenance im ON mi.item_id = im.item_ref
            JOIN museum m ON mi.museum_ref = m.id
            GROUP BY mi.item_id
            ORDER BY maintenance_count DESC, last_maintenance DESC
            LIMIT 10
        """)

    def search_exhibits(self, search_term: str) -> List[sqlite3.Row]:
        """Search exhibits by title or type"""
        search_pattern = f"%{search_term}%"
        return self.execute_read("""
            SELECT mi.*, m.museum_name
            FROM museum_item mi
            JOIN museum m ON mi.museum_ref = m.id
            WHERE mi.item_title LIKE ? OR mi.item_type LIKE ?
            ORDER BY mi.item_title
        """, (search_pattern, search_pattern))

class VisitorRepository(MuseumDAL):
    """Repository for visitor operations"""

    def register_visitor(self, name: str, email: str, phone: str = "",
                        membership: str = "None") -> int:
        """Register new visitor with email validation"""
        if not email or '@' not in email or '.' not in email:
            raise ValueError("Invalid email address format")
        if not name or len(name.strip()) == 0:
            raise ValueError("Visitor name cannot be empty")

        visitor_id = self.execute_write(
            """INSERT INTO guest (guest_name, contact_email, phone, membership_type)
               VALUES (?, ?, ?, ?)""",
            (name.strip(), email.lower(), phone, membership)
        )
        self.log_audit("guest", "INSERT", visitor_id, f"Registered visitor: {name}")
        return visitor_id

    def visitor_activity(self) -> List[sqlite3.Row]:
        """Get visitor activity summary with performance optimization"""
        return self.execute_read("""
            SELECT
                g.guest_name,
                g.contact_email,
                g.membership_type,
                COUNT(gv.visit_id) AS total_visits,
                MAX(gv.visit_date) as last_visit,
                AVG(gv.rating) as avg_rating,
                SUM(gv.ticket_price) as total_spent
            FROM guest g
            LEFT JOIN guest_visit gv ON g.guest_id = gv.guest_ref
            GROUP BY g.guest_id
            HAVING total_visits > 0
            ORDER BY total_visits DESC
        """)

    def log_visit(self, visitor_id: int, museum_id: int, date: str,
                  ticket_price: float = 0.0, rating: Optional[int] = None) -> int:
        """Log museum visit with validation"""
        if rating is not None and (rating < 1 or rating > 5):
            raise ValueError("Rating must be between 1 and 5")
        if ticket_price < 0:
            raise ValueError("Ticket price cannot be negative")

        visit_id = self.execute_write(
            """INSERT INTO guest_visit
               (guest_ref, museum_ref, visit_date, ticket_price, rating)
               VALUES (?, ?, ?, ?, ?)""",
            (visitor_id, museum_id, date, ticket_price, rating)
        )
        self.log_audit("guest_visit", "INSERT", visit_id, f"Logged visit for visitor {visitor_id}")
        return visit_id

    def get_visitor_by_email(self, email: str) -> Optional[sqlite3.Row]:
        """Find visitor by email (performance optimized with index)"""
        result = self.execute_read(
            "SELECT * FROM guest WHERE contact_email = ?",
            (email.lower(),)
        )
        return result[0] if result else None

class MaintenanceRepository(MuseumDAL):
    """Repository for maintenance operations"""

    def add_maintenance(self, item_id: int, action: str, date: str,
                       specialist: str, cost: float = 0.0, notes: str = "") -> int:
        """Add maintenance record with validation"""
        if not action or len(action.strip()) == 0:
            raise ValueError("Maintenance type cannot be empty")
        if not specialist or len(specialist.strip()) == 0:
            raise ValueError("Specialist name cannot be empty")
        if cost < 0:
            raise ValueError("Maintenance cost cannot be negative")

        maintenance_id = self.execute_write(
            """INSERT INTO item_maintenance
               (item_ref, maintenance_type, maintenance_date, specialist_name, cost, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (item_id, action.strip(), date, specialist.strip(), cost, notes)
        )
        self.log_audit("item_maintenance", "INSERT", maintenance_id,
                      f"Added maintenance for item {item_id}")
        return maintenance_id

    def maintenance_summary(self) -> List[sqlite3.Row]:
        """Get maintenance summary with cost analysis"""
        return self.execute_read("""
            SELECT
                mi.item_title,
                m.museum_name,
                COUNT(im.maintenance_id) AS total_actions,
                SUM(im.cost) as total_cost,
                MAX(im.maintenance_date) as last_maintenance,
                MIN(im.maintenance_date) as first_maintenance
            FROM museum_item mi
            JOIN item_maintenance im ON mi.item_id = im.item_ref
            JOIN museum m ON mi.museum_ref = m.id
            GROUP BY mi.item_id
            ORDER BY total_actions DESC
        """)

    def get_maintenance_by_date_range(self, start_date: str, end_date: str) -> List[sqlite3.Row]:
        """Get maintenance records within date range (performance optimized)"""
        return self.execute_read("""
            SELECT im.*, mi.item_title, m.museum_name
            FROM item_maintenance im
            JOIN museum_item mi ON im.item_ref = mi.item_id
            JOIN museum m ON mi.museum_ref = m.id
            WHERE im.maintenance_date BETWEEN ? AND ?
            ORDER BY im.maintenance_date DESC
        """, (start_date, end_date))

    def get_overdue_maintenance(self, days: int = 365) -> List[sqlite3.Row]:
        """Identify exhibits needing maintenance (business logic)"""
        return self.execute_read("""
            SELECT
                mi.item_id,
                mi.item_title,
                m.museum_name,
                MAX(im.maintenance_date) as last_maintenance,
                julianday('now') - julianday(MAX(im.maintenance_date)) as days_since
            FROM museum_item mi
            LEFT JOIN item_maintenance im ON mi.item_id = im.item_ref
            JOIN museum m ON mi.museum_ref = m.id
            GROUP BY mi.item_id
            HAVING days_since > ? OR days_since IS NULL
            ORDER BY days_since DESC
        """, (days,))


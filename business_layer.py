from data_access_layer import *
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import re

class AuthenticationService:
    """Handle authentication and authorization business logic"""

    def __init__(self):
        self.auth_dal = AuthenticationDAL()

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user
        Returns: User info dict or raises exception
        """
        if not username or not password:
            raise ValueError("Username and password are required")

        user = self.auth_dal.authenticate_user(username, password)
        if not user:
            raise ValueError("Invalid username or password")

        return user

    def create_new_user(self, username: str, password: str, role: str,
                       requester_role: str) -> int:
        """
        Create user with permission check
        Only admins can create users
        """
        if not self.auth_dal.check_permission(requester_role, 'admin'):
            raise PermissionError("Only administrators can create users")

        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters")

        return self.auth_dal.create_user(username, password, role)

    def check_access(self, user_role: str, required_role: str) -> bool:
        """Check if user has sufficient privileges"""
        return self.auth_dal.check_permission(user_role, required_role)

class MuseumService:
    """Business logic for museum operations"""

    def __init__(self, user_id: Optional[int] = None):
        self.repo = MuseumRepository(user_id)

    def create_museum(self, name: str, city: str, **kwargs) -> int:
        """
        Create museum with business validation
        Returns: Museum ID
        """
        # Business rule: Museum name must be unique per city
        existing = self.repo.execute_read(
            "SELECT id FROM museum WHERE museum_name = ? AND city = ?",
            (name, city)
        )
        if existing:
            raise ValueError(f"Museum '{name}' already exists in {city}")

        # Validate phone number format if provided
        if 'phone' in kwargs and kwargs['phone']:
            if not self._validate_phone(kwargs['phone']):
                raise ValueError("Invalid phone number format")

        return self.repo.add_museum(name, city, **kwargs)

    def get_all_museums(self) -> List[Dict[str, Any]]:
        """Get all museums with enriched data"""
        museums = self.repo.get_all_museums()
        return [dict(museum) for museum in museums]

    def get_museum_performance(self, museum_id: int) -> Dict[str, Any]:
        """
        Analyze museum performance metrics
        Business logic: Calculate KPIs and recommendations
        """
        stats = self.repo.get_museum_stats(museum_id)

        if not stats:
            raise ValueError(f"Museum {museum_id} not found")

        # Business logic: Calculate performance score
        performance = {
            **stats,
            'performance_score': self._calculate_performance_score(stats),
            'recommendations': self._generate_recommendations(stats)
        }

        return performance

    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        pattern = r'^[\d\s\-\+\(\)]+$'
        return bool(re.match(pattern, phone)) and len(re.sub(r'[\s\-\(\)]', '', phone)) >= 10

    def _calculate_performance_score(self, stats: Dict) -> float:
        """Business logic: Calculate museum performance score (0-100)"""
        score = 0.0

        # Exhibits contribute 30%
        if stats.get('total_exhibits', 0) > 0:
            score += min(30, stats['total_exhibits'] * 2)

        # Visits contribute 40%
        if stats.get('total_visits', 0) > 0:
            score += min(40, stats['total_visits'] * 0.5)

        # Rating contributes 30%
        if stats.get('avg_rating'):
            score += (stats['avg_rating'] / 5) * 30

        return round(score, 2)

    def _generate_recommendations(self, stats: Dict) -> List[str]:
        """Business logic: Generate actionable recommendations"""
        recommendations = []

        if stats.get('total_exhibits', 0) < 5:
            recommendations.append("Consider acquiring more exhibits to increase visitor interest")

        if stats.get('avg_rating') and stats['avg_rating'] < 3.5:
            recommendations.append("Visitor satisfaction is low. Review visitor feedback and improve experience")

        if stats.get('total_visits', 0) < 10:
            recommendations.append("Increase marketing efforts to attract more visitors")

        if not recommendations:
            recommendations.append("Museum performance is good. Maintain current standards")

        return recommendations

class ExhibitService:
    """Business logic for exhibit management"""

    def __init__(self, user_id: Optional[int] = None):
        self.repo = ExhibitRepository(user_id)

    def add_exhibit(self, museum_id: int, title: str, category: str,
                   date_acquired: str, **kwargs) -> int:
        """
        Add exhibit with business validation
        """
        # Business rule: Acquisition date cannot be in future
        if self._parse_date(date_acquired) > datetime.now():
            raise ValueError("Acquisition date cannot be in the future")

        # Business rule: High-value items require condition assessment
        value = kwargs.get('value', 0.0)
        if value > 10000 and not kwargs.get('condition'):
            raise ValueError("High-value items (>10000) must have condition specified")

        return self.repo.add_exhibit(museum_id, title, category, date_acquired, **kwargs)

    def get_exhibits_by_condition(self, condition: str) -> List[Dict[str, Any]]:
        """Get exhibits filtered by condition"""
        all_exhibits = self.repo.get_all_exhibits()
        return [dict(ex) for ex in all_exhibits if ex['condition'] == condition]

    def flag_for_restoration(self, exhibit_id: int) -> None:
        """
        Business logic: Flag exhibit for restoration
        Updates condition and creates maintenance reminder
        """
        self.repo.update_exhibit_condition(exhibit_id, 'Restoration Required')

    def get_valuable_exhibits(self, min_value: float = 5000) -> List[Dict[str, Any]]:
        """Business logic: Get high-value exhibits requiring insurance review"""
        result = self.repo.execute_read("""
            SELECT mi.*, m.museum_name
            FROM museum_item mi
            JOIN museum m ON mi.museum_ref = m.id
            WHERE mi.value >= ?
            ORDER BY mi.value DESC
        """, (min_value,))
        return [dict(row) for row in result]

    def search_exhibits(self, search_term: str) -> List[Dict[str, Any]]:
        """Search exhibits with input sanitization"""
        if not search_term or len(search_term.strip()) < 2:
            raise ValueError("Search term must be at least 2 characters")

        results = self.repo.search_exhibits(search_term.strip())
        return [dict(row) for row in results]

    def _parse_date(self, date_string: str) -> datetime:
        """Parse date string to datetime"""
        try:
            return datetime.strptime(date_string, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")

class VisitorService:
    """Business logic for visitor management"""

    def __init__(self, user_id: Optional[int] = None):
        self.repo = VisitorRepository(user_id)

    def register_visitor(self, name: str, email: str, **kwargs) -> int:
        """
        Register visitor with duplicate check
        """
        # Business rule: Check for existing visitor with same email
        existing = self.repo.get_visitor_by_email(email)
        if existing:
            raise ValueError(f"Visitor with email {email} already registered")

        return self.repo.register_visitor(name, email, **kwargs)

    def log_visit_with_pricing(self, visitor_id: int, museum_id: int,
                              visit_date: str, membership_type: str = "None",
                              rating: Optional[int] = None) -> int:
        """
        Business logic: Calculate ticket price based on membership
        """
        # Get base ticket price (business rule)
        base_price = 15.0

        # Apply membership discount
        discount_rates = {
            'None': 0.0,
            'Basic': 0.10,  # 10% off
            'Premium': 0.25,  # 25% off
            'Family': 0.30  # 30% off
        }

        discount = discount_rates.get(membership_type, 0.0)
        ticket_price = base_price * (1 - discount)

        return self.repo.log_visit(visitor_id, museum_id, visit_date, ticket_price, rating)

    def get_visitor_statistics(self) -> Dict[str, Any]:
        """
        Business analytics: Calculate visitor metrics
        """
        activity = self.repo.visitor_activity()

        if not activity:
            return {
                'total_visitors': 0,
                'total_visits': 0,
                'avg_visits_per_visitor': 0,
                'total_revenue': 0
            }

        total_visitors = len(activity)
        total_visits = sum(v['total_visits'] for v in activity)
        total_revenue = sum(v['total_spent'] or 0 for v in activity)

        return {
            'total_visitors': total_visitors,
            'total_visits': total_visits,
            'avg_visits_per_visitor': round(total_visits / total_visitors, 2),
            'total_revenue': round(total_revenue, 2),
            'top_visitors': [dict(v) for v in activity[:5]]
        }

    def identify_vip_visitors(self, min_visits: int = 5) -> List[Dict[str, Any]]:
        """
        Business logic: Identify VIP visitors for special offers
        """
        activity = self.repo.visitor_activity()
        vip_visitors = [dict(v) for v in activity if v['total_visits'] >= min_visits]
        return sorted(vip_visitors, key=lambda x: x['total_visits'], reverse=True)

    def get_visitor_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Business wrapper: look up a visitor by e-mail address."""
        result = self.repo.get_visitor_by_email(email)
        return dict(result) if result else None

class MaintenanceService:
    """Business logic for maintenance management"""

    def __init__(self, user_id: Optional[int] = None):
        self.repo = MaintenanceRepository(user_id)
        self.exhibit_repo = ExhibitRepository(user_id)

    def schedule_maintenance(self, item_id: int, action: str, date: str,
                           specialist: str, **kwargs) -> int:
        """
        Schedule maintenance with validation
        """
        # Business rule: Maintenance cannot be scheduled more than 1 year in advance
        maintenance_date = datetime.strptime(date, "%Y-%m-%d")
        if maintenance_date > datetime.now() + timedelta(days=365):
            raise ValueError("Cannot schedule maintenance more than 1 year in advance")

        return self.repo.add_maintenance(item_id, action, date, specialist, **kwargs)

    def get_maintenance_budget(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Business analytics: Calculate maintenance costs and budget
        """
        records = self.repo.get_maintenance_by_date_range(start_date, end_date)

        total_cost = sum(r['cost'] or 0 for r in records)
        avg_cost = total_cost / len(records) if records else 0

        return {
            'period': f"{start_date} to {end_date}",
            'total_maintenance_actions': len(records),
            'total_cost': round(total_cost, 2),
            'avg_cost_per_action': round(avg_cost, 2),
            'records': [dict(r) for r in records]
        }

    def generate_maintenance_plan(self, days_threshold: int = 365) -> List[Dict[str, Any]]:
        """
        Business logic: Generate prioritized maintenance plan
        """
        overdue = self.repo.get_overdue_maintenance(days_threshold)

        # Prioritize by condition and days since last maintenance
        plan = []
        for item in overdue:
            # Get current condition
            exhibit = self.exhibit_repo.execute_read(
                "SELECT condition, value FROM museum_item WHERE item_id = ?",
                (item['item_id'],)
            )

            if exhibit:
                condition = exhibit[0]['condition']
                value = exhibit[0]['value'] or 0

                # Calculate priority (higher = more urgent)
                priority_score = 0
                if condition == 'Poor' or condition == 'Restoration Required':
                    priority_score += 50
                elif condition == 'Fair':
                    priority_score += 30

                # High value items get priority
                if value > 10000:
                    priority_score += 30
                elif value > 5000:
                    priority_score += 20

                # Add time factor
                days_since = item['days_since'] or 999
                priority_score += min(20, days_since / 50)

                plan.append({
                    **dict(item),
                    'condition': condition,
                    'value': value,
                    'priority_score': round(priority_score, 2),
                    'urgency': self._get_urgency_level(priority_score)
                })

        return sorted(plan, key=lambda x: x['priority_score'], reverse=True)

    def _get_urgency_level(self, priority_score: float) -> str:
        """Business logic: Convert priority score to urgency level"""
        if priority_score >= 80:
            return "CRITICAL"
        elif priority_score >= 60:
            return "HIGH"
        elif priority_score >= 40:
            return "MEDIUM"
        else:
            return "LOW"
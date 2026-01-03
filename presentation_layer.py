from business_layer import *
import sys
from typing import Optional

class MuseumApplication:
    """Main application controller with role-based interface"""

    def __init__(self):
        self.auth_service = AuthenticationService()
        self.current_user = None
        self.museum_service = None
        self.exhibit_service = None
        self.visitor_service = None
        self.maintenance_service = None

    def run(self):
        """Main application loop"""
        print("="*60)
        print("HeritagePlus Museum Management System")
        print("Multi-Tiered Architecture with Security & Analytics")
        print("="*60)

        # Authentication
        if not self.login():
            print("Authentication failed. Exiting...")
            return

        # Initialize services with user context
        user_id = self.current_user['user_id']
        self.museum_service = MuseumService(user_id)
        self.exhibit_service = ExhibitService(user_id)
        self.visitor_service = VisitorService(user_id)
        self.maintenance_service = MaintenanceService(user_id)

        # Main menu loop
        while True:
            self.display_main_menu()
            choice = input("\nEnter your choice: ").strip()

            if choice == '0':
                print("\nThank you for using HeritagePlus Museum System!")
                break

            self.handle_menu_choice(choice)

    def login(self) -> bool:
        """Handle user authentication"""
        print("\n--- LOGIN ---")
        max_attempts = 3
        attempts = 0

        while attempts < max_attempts:
            username = input("Username: ").strip()
            password = input("Password: ").strip()

            try:
                self.current_user = self.auth_service.login(username, password)
                print(f"\n✓ Welcome, {self.current_user['username']}!")
                print(f"Role: {self.current_user['role'].upper()}")
                return True
            except ValueError as e:
                attempts += 1
                remaining = max_attempts - attempts
                print(f"✗ {e}")
                if remaining > 0:
                    print(f"Attempts remaining: {remaining}")
                else:
                    print("Maximum login attempts exceeded.")

        return False

    def display_main_menu(self):
        """Display role-appropriate menu"""
        print("\n" + "="*60)
        print("MAIN MENU")
        print("="*60)

        print("1. Museum Management")
        print("2. Exhibit Management")
        print("3. Visitor Management")
        print("4. Maintenance Management")
        print("5. Analytics & Reports")

        # Admin-only options
        if self.current_user['role'] == 'admin':
            print("6. User Management (Admin)")

        print("0. Exit")

    def handle_menu_choice(self, choice: str):
        """Route menu selection to appropriate handler"""
        handlers = {
            '1': self.museum_menu,
            '2': self.exhibit_menu,
            '3': self.visitor_menu,
            '4': self.maintenance_menu,
            '5': self.analytics_menu,
            '6': self.user_management_menu if self.current_user['role'] == 'admin' else None
        }

        handler = handlers.get(choice)
        if handler:
            try:
                handler()
            except Exception as e:
                print(f"\n✗ Error: {e}")
        else:
            print("\n✗ Invalid choice. Please try again.")

    def museum_menu(self):
        """Museum management submenu"""
        print("\n--- MUSEUM MANAGEMENT ---")
        print("1. View All Museums")
        print("2. Add New Museum")
        print("3. View Museum Performance")
        print("0. Back")

        choice = input("Choice: ").strip()

        if choice == '1':
            self.view_museums()
        elif choice == '2':
            if self.check_permission('curator'):
                self.add_museum()
        elif choice == '3':
            self.view_museum_performance()

    def view_museums(self):
        """Display all museums"""
        museums = self.museum_service.get_all_museums()

        print(f"\n{'ID':<5} {'Name':<30} {'City':<15} {'Exhibits':<10}")
        print("-" * 60)

        for museum in museums:
            print(f"{museum['id']:<5} {museum['museum_name']:<30} "
                  f"{museum['city']:<15} {museum['exhibit_count']:<10}")

    def add_museum(self):
        """Add new museum with input validation"""
        print("\n--- ADD NEW MUSEUM ---")

        try:
            name = input("Museum Name: ").strip()
            city = input("City: ").strip()
            address = input("Address (optional): ").strip()
            phone = input("Phone (optional): ").strip()
            hours = input("Opening Hours (optional): ").strip()

            museum_id = self.museum_service.create_museum(
                name, city, address=address, phone=phone, opening_hours=hours
            )
            print(f"\n✓ Museum added successfully! ID: {museum_id}")

        except ValueError as e:
            print(f"\n✗ Validation Error: {e}")

    def view_museum_performance(self):
        """Display museum performance metrics"""
        self.view_museums()

        try:
            museum_id = int(input("\nEnter Museum ID: "))
            performance = self.museum_service.get_museum_performance(museum_id)

            print(f"\n--- PERFORMANCE REPORT: {performance['museum_name']} ---")
            print(f"Total Exhibits: {performance.get('total_exhibits', 0)}")
            print(f"Total Visits: {performance.get('total_visits', 0)}")
            print(f"Average Rating: {performance.get('avg_rating', 0):.2f}/5.0")
            print(f"Total Revenue: ${performance.get('total_revenue', 0):.2f}")
            print(f"Performance Score: {performance['performance_score']:.2f}/100")

            print("\nRecommendations:")
            for i, rec in enumerate(performance['recommendations'], 1):
                print(f"{i}. {rec}")

        except (ValueError, KeyError) as e:
            print(f"\n✗ Error: {e}")

    def exhibit_menu(self):
        """Exhibit management submenu"""
        print("\n--- EXHIBIT MANAGEMENT ---")
        print("1. View All Exhibits")
        print("2. Add New Exhibit")
        print("3. Search Exhibits")
        print("4. View Top Exhibits")
        print("5. View High-Value Exhibits")
        print("0. Back")

        choice = input("Choice: ").strip()

        if choice == '1':
            self.view_exhibits()
        elif choice == '2':
            if self.check_permission('curator'):
                self.add_exhibit()
        elif choice == '3':
            self.search_exhibits()
        elif choice == '4':
            self.view_top_exhibits()
        elif choice == '5':
            self.view_valuable_exhibits()

    def view_exhibits(self):
        """Display all exhibits"""
        exhibits = self.exhibit_service.repo.get_all_exhibits()

        print(f"\n{'ID':<5} {'Title':<30} {'Museum':<25} {'Condition':<15}")
        print("-" * 75)

        for exhibit in exhibits[:20]:  # Limit display
            print(f"{exhibit['item_id']:<5} {exhibit['item_title']:<30} "
                  f"{exhibit['museum_name']:<25} {exhibit['condition']:<15}")

        if len(exhibits) > 20:
            print(f"\n... and {len(exhibits) - 20} more exhibits")

    def add_exhibit(self):
        """Add new exhibit"""
        print("\n--- ADD NEW EXHIBIT ---")

        try:
            self.view_museums()
            museum_id = int(input("Museum ID: "))
            title = input("Exhibit Title: ").strip()
            category = input("Category: ").strip()
            date = input("Acquisition Date (YYYY-MM-DD): ").strip()
            description = input("Description (optional): ").strip()

            print("\nCondition Options: Excellent, Good, Fair, Poor, Restoration Required")
            condition = input("Condition: ").strip() or "Good"

            value_str = input("Estimated Value (optional): ").strip()
            value = float(value_str) if value_str else 0.0

            exhibit_id = self.exhibit_service.add_exhibit(
                museum_id, title, category, date,
                description=description, condition=condition, value=value
            )
            print(f"\n✓ Exhibit added successfully! ID: {exhibit_id}")

        except ValueError as e:
            print(f"\n✗ Error: {e}")

    def search_exhibits(self):
        """Search exhibits by keyword"""
        search_term = input("\nEnter search term: ").strip()

        try:
            results = self.exhibit_service.search_exhibits(search_term)

            if not results:
                print("\n✗ No exhibits found matching your search.")
                return

            print(f"\nFound {len(results)} result(s):")
            for exhibit in results:
                print(f"\n- {exhibit['item_title']}")
                print(f"  Museum: {exhibit['museum_name']}")
                print(f"  Type: {exhibit['item_type']}")
                print(f"  Condition: {exhibit['condition']}")

        except ValueError as e:
            print(f"\n✗ {e}")

    def view_top_exhibits(self):
        """Display exhibits with most maintenance"""
        top = self.exhibit_service.repo.top_exhibits()

        print("\n--- TOP EXHIBITS (By Maintenance Frequency) ---")
        print(f"{'Title':<30} {'Museum':<25} {'Maintenance Count':<20}")
        print("-" * 75)

        for exhibit in top:
            print(f"{exhibit['item_title']:<30} {exhibit['museum_name']:<25} "
                  f"{exhibit['maintenance_count']:<20}")

    def view_valuable_exhibits(self):
        """Display high-value exhibits"""
        try:
            min_value_str = input("\nMinimum value (default 5000): ").strip()
            min_value = float(min_value_str) if min_value_str else 5000.0

            valuable = self.exhibit_service.get_valuable_exhibits(min_value)

            print(f"\n--- HIGH-VALUE EXHIBITS (>${min_value:.2f}) ---")
            print(f"{'Title':<30} {'Museum':<25} {'Value':<15}")
            print("-" * 70)

            for exhibit in valuable:
                print(f"{exhibit['item_title']:<30} {exhibit['museum_name']:<25} "
                      f"${exhibit['value']:.2f}")

        except ValueError as e:
            print(f"\n✗ {e}")

    def visitor_menu(self):
        """Visitor management submenu"""
        print("\n--- VISITOR MANAGEMENT ---")
        print("1. View Visitor Activity")
        print("2. Register New Visitor")
        print("3. Log Visit")
        print("4. View VIP Visitors")
        print("0. Back")

        choice = input("Choice: ").strip()

        if choice == '1':
            self.view_visitor_activity()
        elif choice == '2':
            self.register_visitor()
        elif choice == '3':
            self.log_visit()
        elif choice == '4':
            self.view_vip_visitors()

    def view_visitor_activity(self):
        """Display visitor statistics"""
        activity = self.visitor_service.repo.visitor_activity()

        print(f"\n{'Name':<25} {'Email':<30} {'Visits':<10} {'Avg Rating':<12}")
        print("-" * 77)

        for visitor in activity[:15]:
            avg_rating = visitor['avg_rating'] or 0
            print(f"{visitor['guest_name']:<25} {visitor['contact_email']:<30} "
                  f"{visitor['total_visits']:<10} {avg_rating:.2f}")

    def register_visitor(self):
        """Register new visitor"""
        print("\n--- REGISTER NEW VISITOR ---")

        try:
            name = input("Full Name: ").strip()
            email = input("Email: ").strip()
            phone = input("Phone (optional): ").strip()

            print("\nMembership Types: None, Basic, Premium, Family")
            membership = input("Membership Type: ").strip() or "None"

            visitor_id = self.visitor_service.register_visitor(
                name, email, phone=phone, membership=membership
            )
            print(f"\n✓ Visitor registered successfully! ID: {visitor_id}")

        except ValueError as e:
            print(f"\n✗ {e}")

    def log_visit(self):
        """Log museum visit"""
        print("\n--- LOG MUSEUM VISIT ---")

        try:
            visitor_id = int(input("Visitor ID: "))

            self.view_museums()
            museum_id = int(input("Museum ID: "))

            date = input("Visit Date (YYYY-MM-DD, or press Enter for today): ").strip()
            if not date:
                from datetime import datetime
                date = datetime.now().strftime("%Y-%m-%d")

            rating_str = input("Rating 1-5 (optional): ").strip()
            rating = int(rating_str) if rating_str else None

            # Get visitor's membership for pricing
            visitor = self.visitor_service.repo.execute_read(
                "SELECT membership_type FROM guest WHERE guest_id = ?",
                (visitor_id,)
            )
            membership = visitor[0]['membership_type'] if visitor else "None"

            visit_id = self.visitor_service.log_visit_with_pricing(
                visitor_id, museum_id, date, membership, rating
            )
            print(f"\n✓ Visit logged successfully! ID: {visit_id}")

        except ValueError as e:
            print(f"\n✗ {e}")

    def view_vip_visitors(self):
        """Display VIP visitors"""
        try:
            min_visits_str = input("\nMinimum visits for VIP status (default 5): ").strip()
            min_visits = int(min_visits_str) if min_visits_str else 5

            vip = self.visitor_service.identify_vip_visitors(min_visits)

            print(f"\n--- VIP VISITORS ({min_visits}+ visits) ---")
            print(f"{'Name':<25} {'Visits':<10} {'Total Spent':<15} {'Avg Rating':<12}")
            print("-" * 62)

            for visitor in vip:
                print(f"{visitor['guest_name']:<25} {visitor['total_visits']:<10} "
                      f"${visitor['total_spent']:.2f:<15} {visitor['avg_rating']:.2f}")

        except ValueError as e:
            print(f"\n✗ {e}")

    def maintenance_menu(self):
        """Maintenance management submenu"""
        print("\n--- MAINTENANCE MANAGEMENT ---")
        print("1. View Maintenance Summary")
        print("2. Schedule Maintenance")
        print("3. Generate Maintenance Plan")
        print("4. View Maintenance Budget")
        print("0. Back")

        choice = input("Choice: ").strip()

        if choice == '1':
            self.view_maintenance_summary()
        elif choice == '2':
            if self.check_permission('curator'):
                self.schedule_maintenance()
        elif choice == '3':
            self.generate_maintenance_plan()
        elif choice == '4':
            self.view_maintenance_budget()

    def view_maintenance_summary(self):
        """Display maintenance summary"""
        summary = self.maintenance_service.repo.maintenance_summary()

        print(f"\n{'Exhibit':<30} {'Museum':<25} {'Actions':<10} {'Total Cost':<12}")
        print("-" * 77)

        for item in summary:
            cost = item['total_cost'] or 0
            print(f"{item['item_title']:<30} {item['museum_name']:<25} "
                  f"{item['total_actions']:<10} ${cost:.2f}")

    def schedule_maintenance(self):
        """Schedule maintenance action"""
        print("\n--- SCHEDULE MAINTENANCE ---")

        try:
            item_id = int(input("Exhibit ID: "))
            action = input("Maintenance Type: ").strip()
            date = input("Date (YYYY-MM-DD): ").strip()
            specialist = input("Specialist Name: ").strip()

            cost_str = input("Estimated Cost (optional): ").strip()
            cost = float(cost_str) if cost_str else 0.0

            notes = input("Notes (optional): ").strip()

            maintenance_id = self.maintenance_service.schedule_maintenance(
                item_id, action, date, specialist, cost=cost, notes=notes
            )
            print(f"\n✓ Maintenance scheduled successfully! ID: {maintenance_id}")

        except ValueError as e:
            print(f"\n✗ {e}")

    def generate_maintenance_plan(self):
        """Generate prioritized maintenance plan"""
        print("\n--- MAINTENANCE PLAN ---")

        plan = self.maintenance_service.generate_maintenance_plan()

        if not plan:
            print("\n✓ All exhibits are up to date!")
            return

        print(f"\n{'Exhibit':<30} {'Days Since':<12} {'Priority':<10} {'Urgency':<10}")
        print("-" * 62)

        for item in plan[:15]:
            days = int(item['days_since']) if item['days_since'] else 999
            print(f"{item['item_title']:<30} {days:<12} "
                  f"{item['priority_score']:.1f:<10} {item['urgency']:<10}")

    def view_maintenance_budget(self):
        """View maintenance budget for date range"""
        print("\n--- MAINTENANCE BUDGET ---")

        try:
            start_date = input("Start Date (YYYY-MM-DD): ").strip()
            end_date = input("End Date (YYYY-MM-DD): ").strip()

            budget = self.maintenance_service.get_maintenance_budget(start_date, end_date)

            print(f"\nPeriod: {budget['period']}")
            print(f"Total Maintenance Actions: {budget['total_maintenance_actions']}")
            print(f"Total Cost: ${budget['total_cost']:.2f}")
            print(f"Average Cost per Action: ${budget['avg_cost_per_action']:.2f}")

        except ValueError as e:
            print(f"\n✗ {e}")

    def analytics_menu(self):
        """Analytics and reporting submenu"""
        print("\n--- ANALYTICS & REPORTS ---")
        print("1. Visitor Statistics")
        print("2. Museum Performance Comparison")
        print("0. Back")

        choice = input("Choice: ").strip()

        if choice == '1':
            self.visitor_statistics()
        elif choice == '2':
            self.museum_comparison()

    def visitor_statistics(self):
        """Display comprehensive visitor statistics"""
        stats = self.visitor_service.get_visitor_statistics()

        print("\n--- VISITOR STATISTICS ---")
        print(f"Total Visitors: {stats['total_visitors']}")
        print(f"Total Visits: {stats['total_visits']}")
        print(f"Average Visits per Visitor: {stats['avg_visits_per_visitor']}")
        print(f"Total Revenue: ${stats['total_revenue']:.2f}")

        if stats['top_visitors']:
            print("\nTop 5 Most Active Visitors:")
            for i, visitor in enumerate(stats['top_visitors'], 1):
                print(f"{i}. {visitor['guest_name']} - {visitor['total_visits']} visits")

    def museum_comparison(self):
        """Compare performance across museums"""
        museums = self.museum_service.get_all_museums()

        print("\n--- MUSEUM PERFORMANCE COMPARISON ---")
        print(f"{'Museum':<30} {'Exhibits':<10} {'Score':<10}")
        print("-" * 50)

        for museum in museums:
            try:
                perf = self.museum_service.get_museum_performance(museum['id'])
                print(f"{museum['museum_name']:<30} {museum['exhibit_count']:<10} "
                      f"{perf['performance_score']:.1f}/100")
            except:
                pass

    def user_management_menu(self):
        """Admin-only user management"""
        if not self.check_permission('admin', show_error=False):
            return

        print("\n--- USER MANAGEMENT (Admin Only) ---")
        print("1. Create New User")
        print("0. Back")

        choice = input("Choice: ").strip()

        if choice == '1':
            self.create_user()

    def create_user(self):
        """Create new user account"""
        print("\n--- CREATE NEW USER ---")

        try:
            username = input("Username: ").strip()
            password = input("Password (min 8 chars): ").strip()

            print("\nRoles: admin, curator, viewer")
            role = input("Role: ").strip().lower()

            user_id = self.auth_service.create_new_user(
                username, password, role, self.current_user['role']
            )
            print(f"\n✓ User created successfully! ID: {user_id}")

        except (ValueError, PermissionError) as e:
            print(f"\n✗ {e}")

    def check_permission(self, required_role: str, show_error: bool = True) -> bool:
        """Check if current user has required permission"""
        has_permission = self.auth_service.check_access(
            self.current_user['role'], required_role
        )

        if not has_permission and show_error:
            print(f"\n✗ Permission denied. {required_role.capitalize()} role required.")

        return has_permission

def main():
    """Application entry point"""
    app = MuseumApplication()

    try:
        app.run()
    except KeyboardInterrupt:
        print("\n\nApplication terminated by user.")
    except Exception as e:
        print(f"\n✗ Critical Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()


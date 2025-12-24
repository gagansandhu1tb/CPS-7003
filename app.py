from dal import (
    MuseumRepository,
    ExhibitRepository,
    VisitorRepository,
    MaintenanceRepository
)

def main():
    museum_repo = MuseumRepository()
    exhibit_repo = ExhibitRepository()
    visitor_repo = VisitorRepository()
    maintenance_repo = MaintenanceRepository()

    # Museums
    museum_repo.add_museum("British Museum", "London")
    museum_repo.add_museum("National Museum of Scotland", "Edinburgh")
    museum_repo.add_museum("Imperial War Museum", "London")
    museum_repo.add_museum("Science Museum", "London")
    museum_repo.add_museum("Tate Britain", "London")

    # Exhibits
    exhibit_repo.add_exhibit(1, "Rosetta Stone", "Ancient History", "1802-03-11")
    exhibit_repo.add_exhibit(1, "Parthenon Marbles", "Classical Sculpture", "1816-01-01")
    exhibit_repo.add_exhibit(1, "Egyptian Mummy", "Egyptology", "1850-06-15")

    exhibit_repo.add_exhibit(2, "Lewis Chessmen", "Medieval Artefacts", "1831-04-01")
    exhibit_repo.add_exhibit(2, "Maiden Castle Sword", "Iron Age", "1935-08-20")

    exhibit_repo.add_exhibit(3, "Spitfire Mk IX", "Military Aviation", "1946-07-10")
    exhibit_repo.add_exhibit(3, "World War I Trench Exhibit", "Military History", "1920-11-11")

    exhibit_repo.add_exhibit(4, "Stephenson's Rocket", "Engineering", "1829-10-08")
    exhibit_repo.add_exhibit(4, "Apollo 10 Command Module", "Space Exploration", "1969-05-18")

    exhibit_repo.add_exhibit(5, "Ophelia by John Everett Millais", "Fine Art", "1852-01-01")
    exhibit_repo.add_exhibit(5, "The Fighting Temeraire", "Fine Art", "1839-01-01")

    # Visitors
    visitor_repo.register_visitor("James Thornton", "j.thornton@example.co.uk")
    visitor_repo.register_visitor("Emily Watson", "emily.watson@example.co.uk")
    visitor_repo.register_visitor("Oliver Brown", "oliver.brown@example.co.uk")
    visitor_repo.register_visitor("Charlotte Green", "charlotte.green@example.co.uk")
    visitor_repo.register_visitor("Mohammed Rahman", "m.rahman@example.co.uk")
    visitor_repo.register_visitor("Ayesha Hussain", "ayesha.hussain@example.co.uk")
    visitor_repo.register_visitor("Daniel Clarke", "daniel.clarke@example.co.uk")
    visitor_repo.register_visitor("Sophia Patel", "sophia.patel@example.co.uk")

    maintenance_repo.add_maintenance(1, "Surface Cleaning", "2023-01-15", "Dr Emily Carter")
    maintenance_repo.add_maintenance(1, "Stone Preservation", "2024-02-10", "Dr James Wilson")
    maintenance_repo.add_maintenance(6, "Structural Inspection", "2023-06-05", "RAF Heritage Team")

    visitor_repo.log_visit(1, 1, "2024-01-10")
    visitor_repo.log_visit(1, 4, "2024-02-15")
    visitor_repo.log_visit(2, 1, "2024-03-01")

    # Advance Queries
    print("\n--- Top Exhibits (Maintenance Frequency) ---")
    for row in exhibit_repo.top_exhibits():
        print(row)

    print("\n--- Visitor Activity ---")
    for row in visitor_repo.visitor_activity():
        print(row)

    print("\n--- Maintenance Summary ---")
    for row in maintenance_repo.maintenance_summary():
        print(row)


if __name__ == "__main__":
    main()

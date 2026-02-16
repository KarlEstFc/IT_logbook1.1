from src.models import LogBook
from src.importer import import_csv_file


def run_cli():
    logbook = LogBook()

    while True:
        print("\n--- MENÜÜ ---")
        print("1. Lisa | 2. Vaata | 3. Otsi | 4. Filtreeri")
        print("5. Muuda staatust | 6. Kustuta | 7. Import | 8. Välju")

        valik = input("Valik: ").strip()

        if valik == "1":
            t = input("Pealkiri: ")
            d = input("Kirjeldus: ")
            # LOOGIKA: Kasutaja vigade püüdmine
            # Me ei tea, mida kasutaja sisestab. Püüame vea kinni, et programm ei krasšiks.
            try:
                logbook.add_entry(t, d)
                print("OK!")
            except ValueError as e:
                print(f"VIGA: {e}")

        elif valik == "2":
            # Lihtne kontroll: kui tühi, ütle kasutajale.
            if not logbook.entries:
                print("Tühi.")
            else:
                for e in logbook.entries: print(e)

        elif valik == "3":
            s = input("Otsing: ")
            for e in logbook.search(s): print(e)

        elif valik == "4":
            s = input("Staatus (OPEN/DONE): ").upper()
            for e in logbook.filter_by_status(s): print(e)

        elif valik == "5":
            uid = input("Sisesta kellaaeg (ID): ")
            if logbook.change_status(uid):
                print("Muudetud!")
            else:
                print("Ei leitud.")

        elif valik == "6":
            uid = input("Sisesta kellaaeg (ID): ")
            if logbook.delete_entry(uid):
                print("Kustutatud!")
            else:
                print("Ei leitud.")

        elif valik == "7":
            f = input("Failinimi: ")
            print(import_csv_file(f, logbook))

        elif valik == "8":
            break
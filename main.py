import sys
import os
import json
import csv
from datetime import datetime

# Lisame src kausta sys.path-sse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


# LogEntry klass ühe logikirje andmete töötlemiseks
class LogEntry:
    """
    Esindab ühte logikirjet.
    """

    def __init__(self, title, description, status="OPEN", created_at=None):
        # Kui aega pole antud, loome praeguse hetke
        if created_at:
            self.created_at = created_at
        else:
            now = datetime.now()
            self.created_at = now.strftime("%d.%m.%Y %H:%M:%S")

        self.title = title
        self.description = description
        self.status = status

    def validate(self):
        """
        Kontrollib, kas kirje vastab nõuetele.
        Tagastab (True, "") või (False, "veateade").
        """
        # Kontrolli kuupäeva formaati
        try:
            datetime.strptime(self.created_at, "%d.%m.%Y %H:%M:%S")
        except ValueError:
            # Proovime toetada ka ISO formaati, mis võib tulla CSV-st
            try:
                dt = datetime.strptime(self.created_at, "%Y-%m-%d %H:%M:%S")
                # Konverteerime kohe õigesse formaati
                self.created_at = dt.strftime("%d.%m.%Y %H:%M:%S")
            except ValueError:
                return False, "Vigane kuupäeva formaat"

        if not self.title or len(self.title) < 4:
            return False, "Pealkiri peab olema vähemalt 4 tähemärki pikk"

        if not self.description or len(self.description) < 10:
            return False, "Kirjeldus peab olema vähemalt 10 tähemärki pikk"

        if self.status not in ["OPEN", "DONE"]:
            return False, f"Staatus '{self.status}' ei ole lubatud (peab olema OPEN või DONE)"

        return True, ""

    def to_dict(self):
        """Muudab objekti sõnastikuks JSON-i jaoks."""
        return {
            "created_at": self.created_at,
            "title": self.title,
            "description": self.description,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data):
        """Loob sõnastikust objekti."""
        return cls(
            title=data["title"],
            description=data["description"],
            status=data["status"],
            created_at=data["created_at"]
        )

    def __str__(self):
        """Kasutajasõbralik kuju konsoolis kuvamiseks."""
        return f"{self.created_at} | [{self.status}] | {self.title} | {self.description}"


# LogBook klass, mis haldab logikirjade kogumiku (lisamine, kustutamine, otsing, faili I/O)
class LogBook:
    """
    Haldab logikirjete kollektsiooni (lisamine, kustutamine, otsing, faili I/O).
    """

    def __init__(self):
        self.entries = []
        self.load_data()

    def add_entry(self, entry):
        """Lisab kirje, kui see on unikaalne (created_at alusel)."""
        # Kontrollime duplikaate (nõue: samal sekundil ei looda kahte kirjet)
        for e in self.entries:
            if e.created_at == entry.created_at:
                return False, "Selle ajatempliga kirje on juba olemas!"

        self.entries.append(entry)
        return True, "Kirje lisatud."

    def delete_entry(self, created_at_id):
        """Kustutab kirje ajatempli järgi."""
        initial_count = len(self.entries)
        self.entries = [e for e in self.entries if e.created_at != created_at_id]
        return len(self.entries) < initial_count

    def search_entries(self, keyword):
        """Otsib märksõna pealkirjast või kirjeldusest."""
        result = []
        keyword = keyword.lower()
        for entry in self.entries:
            if keyword in entry.title.lower() or keyword in entry.description.lower():
                result.append(entry)
        return result

    def filter_by_status(self, status):
        """Filtreerib staatuse järgi (OPEN/DONE)."""
        return [e for e in self.entries if e.status == status]

    def change_status(self, created_at_id):
        """Muudab staatust (OPEN <-> DONE)."""
        for entry in self.entries:
            if entry.created_at == created_at_id:
                entry.status = "DONE" if entry.status == "OPEN" else "OPEN"
                return True
        return False

    def save_data(self):
        """Salvestab andmed JSON faili."""
        data = [e.to_dict() for e in self.entries]
        try:
            with open("logbook.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("Andmed on salvestatud faili 'logbook.json'.")
        except Exception as e:
            print(f"Viga andmete salvestamisel: {e}")

    def load_data(self):
        """Laeb andmed JSON failist."""
        try:
            with open("logbook.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    entry = LogEntry.from_dict(item)
                    # Lisame ilma duplikaadi kontrollita, kuna laeme olemasolevat andmebaasi
                    self.entries.append(entry)
            print(f"Laaditud {len(self.entries)} kirjet failist 'logbook.json'.")
        except FileNotFoundError:
            print("Faili 'logbook.json' ei leitud. Alustatakse tühja logiraamatuga.")
        except json.JSONDecodeError:
            print("Viga JSON faili lugemisel. Alustatakse tühja logiraamatuga.")
        except Exception as e:
            print(f"Viga andmete laadimisel: {e}")

    def import_from_csv(self, filename):
        """Impordib kirjeid CSV failist."""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                imported = 0
                skipped = 0

                for row in reader:
                    try:
                        # Loome uue kirje CSV realt
                        entry = LogEntry(
                            title=row.get("title", ""),
                            description=row.get("description", ""),
                            status=row.get("status", "OPEN").upper(),
                            created_at=row.get("created_at", "")
                        )

                        # Valideerime kirje
                        valid, msg = entry.validate()
                        if valid:
                            # Kontrollime duplikaate
                            success, _ = self.add_entry(entry)
                            if success:
                                imported += 1
                            else:
                                skipped += 1
                        else:
                            print(f"Vigane kirje vahele jäetud: {msg}")
                            skipped += 1

                    except Exception as e:
                        print(f"Viga rea töötlemisel: {e}")
                        skipped += 1

                print(f"\nImport lõpetatud: {imported} kirjet lisatud, {skipped} vahele jäetud.")

        except FileNotFoundError:
            print(f"Faili '{filename}' ei leitud.")
        except Exception as e:
            print(f"Viga CSV importimisel: {e}")


# Menüüd kuvatakse kasutajale
def print_menu():
    print("\n--- IT HOOLDUSPÄEVIK ---")
    print("1. Lisa uus logikirje")
    print("2. Kuva kõik logikirjed")
    print("3. Otsi kirjeid (pealkiri/kirjeldus)")
    print("4. Filtreeri staatuse järgi")
    print("5. Muuda kirje staatust (OPEN <-> DONE)")
    print("6. Kustuta kirje")
    print("7. IMPORTI failist (sample_import.csv)")
    print("8. Salvesta ja välju")


# Põhiprogramm, mis käivitab menüü ja võimaldab tegevusi valida
def main():
    # Loome LogBook objekti
    book = LogBook()

    while True:
        # Kuvame menüü
        print_menu()
        choice = input("Vali tegevus (1-8): ").strip()

        # Uue logikirje lisamine
        if choice == "1":
            print("\n--- Uus kirje ---")
            title = input("Pealkiri (min 4 märki): ").strip()
            desc = input("Kirjeldus (min 10 märki): ").strip()

            # Loome uue kirje (aeg tekib automaatselt)
            entry = LogEntry(title, desc)

            # Valideerime
            valid, msg = entry.validate()
            if valid:
                success, message = book.add_entry(entry)
                if success:
                    print("Kirje lisatud!")
                else:
                    print(f"VIGA: {message}")
            else:
                print(f"VIGA: {msg}")

        # Kõik logikirjed
        elif choice == "2":
            print("\n--- Kõik kirjed ---")
            if not book.entries:
                print("Logiraamat on tühi.")
            for entry in book.entries:
                print(entry)

        # Otsing logikirjed
        elif choice == "3":
            keyword = input("Sisesta otsingusõna: ").strip()
            results = book.search_entries(keyword)
            print(f"\nLeiti {len(results)} vastet:")
            for entry in results:
                print(entry)

        # Filtreeri staatuse järgi
        elif choice == "4":
            status = input("Sisesta staatus (OPEN või DONE): ").strip().upper()
            if status not in ["OPEN", "DONE"]:
                print("Vigane staatus.")
                continue
            results = book.filter_by_status(status)
            print(f"\nLeiti {len(results)} kirjet staatusega {status}:")
            for entry in results:
                print(entry)

        # Muuda kirje staatust (OPEN <-> DONE)
        elif choice == "5":
            entry_id = input("Sisesta kirje kellaaeg (ID) muutmiseks (DD.MM.YYYY HH:MM:SS): ").strip()
            if book.change_status(entry_id):
                print("Staatus muudetud!")
            else:
                print("Kirjet ei leitud.")

        # Kustuta kirje
        elif choice == "6":
            entry_id = input("Sisesta kirje kellaaeg (ID) kustutamiseks: ").strip()
            if book.delete_entry(entry_id):
                print("Kirje kustutatud.")
            else:
                print("Kirjet ei leitud.")

        # Importi failist
        elif choice == "7":
            filename = input("Sisesta failinimi (nt sample_import.csv): ").strip()
            if not filename:
                filename = "sample_import.csv"
            book.import_from_csv(filename)

        # Salvesta ja välju
        elif choice == "8":
            book.save_data()  # Salvestab andmed JSON faili
            print("Programm suletakse. Head aega!")
            break

        else:
            print("Tundmatu valik, proovi uuesti.")


if __name__ == "__main__":
    main()
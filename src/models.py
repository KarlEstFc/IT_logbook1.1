import json
import csv
from datetime import datetime

# KONSTANDID
DB_FILE = "logbook.json"
ERROR_LOG_FILE = "import_errors.log"


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
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("Andmed salvestatud.")
        except Exception as e:
            print(f"Viga salvestamisel: {e}")

    def load_data(self):
        """Laeb andmed JSON failist."""
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.entries = [LogEntry.from_dict(item) for item in data]
            print(f"Failist loeti {len(self.entries)} kirjet.")
        except FileNotFoundError:
            print("Logiraamatu faili ei leitud. Alustatakse tühja logiraamatuga.")
            self.entries = []
        except json.JSONDecodeError:
            print("Vigane JSON fail. Alustatakse tühjalt.")
            self.entries = []

    def import_from_csv(self, filename):
        """
        Spetsiaalne import funktsioon (Nõue punkt 4).
        Loeb CSV faili, valideerib ja sorteerib vigased eraldi faili.
        """
        success_count = 0
        error_logs = []

        try:
            with open(filename, "r", encoding="utf-8") as f:
                # Eeldame, et eraldaja on semikoolon nagu näidisfailis
                reader = csv.reader(f, delimiter=";")

                for row in reader:
                    # Kontroll: kas real on piisavalt välju
                    if len(row) < 4:
                        error_logs.append(f"Rida: {row} -> Viga: Puuduvad väljad")
                        continue

                    # CSV väljad: Date;Title;Desc;Status
                    raw_date, raw_title, raw_desc, raw_status = row[0].strip(), row[1].strip(), row[2].strip(), row[
                        3].strip()

                    # Loome ajutise objekti valideerimiseks
                    # NB! Siin anname raw_date otse sisse, valideerimine toimub klassis
                    temp_entry = LogEntry(raw_title, raw_desc, raw_status, raw_date)

                    is_valid, error_msg = temp_entry.validate()

                    if is_valid:
                        # Proovime lisada logiraamatusse (kontrollib ka ID unikaalsust)
                        added, msg = self.add_entry(temp_entry)
                        if added:
                            success_count += 1
                        else:
                            error_logs.append(f"Rida: {row} -> Viga: {msg}")
                    else:
                        error_logs.append(f"Rida: {row} -> Viga: {error_msg}")

            # Salvestame vigade logi
            if error_logs:
                with open(ERROR_LOG_FILE, "w", encoding="utf-8") as err_f:
                    for log in error_logs:
                        err_f.write(log + "\n")
                print(f"Leiti {len(error_logs)} vigast rida. Vaata: {ERROR_LOG_FILE}")

            print(f"Imporditi edukalt {success_count} kirjet.")
            self.save_data()  # Salvestame kohe õiged andmed JSONisse

        except FileNotFoundError:
            print(f"Faili '{filename}' ei leitud!")
        except Exception as e:
            print(f"Kriitiline viga importimisel: {e}")
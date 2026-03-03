import json
import csv
from datetime import datetime
import os

DB_FILE = "logbook.json"
ERROR_LOG_FILE = "import_errors.log"


class LogEntry:
    def __init__(self, id, title, description, status="OPEN", created_at=None):
        self.id = id  # UUS: Unikaalne ID number
        if created_at:
            self.created_at = created_at
        else:
            now = datetime.now()
            self.created_at = now.strftime("%d.%m.%Y %H:%M:%S")

        self.title = title
        self.description = description
        self.status = status

    def validate(self):
        if not self.title or len(self.title) < 4:
            return False, "Pealkiri peab olema vähemalt 4 tähemärki pikk"
        if not self.description or len(self.description) < 10:
            return False, "Kirjeldus peab olema vähemalt 10 tähemärki pikk"
        if self.status not in ["OPEN", "DONE"]:
            return False, "Staatus peab olema OPEN või DONE"
        return True, ""

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at,
            "title": self.title,
            "description": self.description,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),  # Laeme ID, kui see on olemas
            title=data["title"],
            description=data["description"],
            status=data["status"],
            created_at=data["created_at"]
        )

    def __str__(self):
        # Kuvame ID kõige ees, et kasutajal oleks lihtne valida
        return f"[{self.id}] {self.created_at} | {self.status} | {self.title} - {self.description}"


class LogBook:
    def __init__(self):
        self.entries = []
        self.next_id = 1  # Hoiab järgmist vaba ID numbrit
        self.load_data()

    def _update_next_id(self):
        """Leiab suurima ID ja seab lugeja selle järgi."""
        if self.entries:
            max_id = max(e.id for e in self.entries if e.id is not None)
            self.next_id = max_id + 1
        else:
            self.next_id = 1

    def add_entry(self, title, description, status="OPEN", created_at=None, force_id=None):
        # Kui importides on ID antud, kasuta seda, muidu genereeri uus
        new_id = force_id if force_id else self.next_id

        entry = LogEntry(new_id, title, description, status, created_at)

        valid, msg = entry.validate()
        if not valid:
            return False, msg

        self.entries.append(entry)
        if not force_id:
            self.next_id += 1  # Suurendame loendurit ainult uue kirje puhul

        self.save_data()  # UUS: Automaatne salvestus!
        return True, "Kirje lisatud."

    def delete_entry(self, entry_id):
        """Kustutab kirje ID (numbri) järgi."""
        try:
            entry_id = int(entry_id)
        except ValueError:
            return False, "ID peab olema number!"

        initial_count = len(self.entries)
        self.entries = [e for e in self.entries if e.id != entry_id]

        if len(self.entries) < initial_count:
            self.save_data()  # UUS: Automaatne salvestus!
            return True, "Kirje kustutatud."
        return False, "Kirjet selle ID-ga ei leitud."

    def change_status(self, entry_id):
        """Muudab staatust ID (numbri) järgi."""
        try:
            entry_id = int(entry_id)
        except ValueError:
            return False, "ID peab olema number!"

        for entry in self.entries:
            if entry.id == entry_id:
                entry.status = "DONE" if entry.status == "OPEN" else "OPEN"
                self.save_data()  # UUS: Automaatne salvestus!
                return True, f"Staatus muudetud: {entry.status}"

        return False, "Kirjet ei leitud."

    def search_entries(self, keyword):
        keyword = keyword.lower()
        return [e for e in self.entries if keyword in e.title.lower() or keyword in e.description.lower()]

    def filter_by_status(self, status):
        return [e for e in self.entries if e.status == status]

    def save_data(self):
        """Salvestab andmed koheselt kettale."""
        data = [e.to_dict() for e in self.entries]
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"KRIITILINE VIGA SALVESTAMISEL: {e}")

    def load_data(self):
        if not os.path.exists(DB_FILE):
            return

        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                temp_entries = []
                for item in data:
                    # Tagasiühilduvus: kui vanas JSONis pole ID-d, genereerime ajutise
                    if "id" not in item:
                        item["id"] = 0  # Ajutine, parandatakse _update_next_id käigus kui vaja oleks
                    temp_entries.append(LogEntry.from_dict(item))

                self.entries = temp_entries

                # Kui laadisime vanu andmeid ilma ID-ta, anname neile numbrid
                needs_save = False
                current_max = 0
                for e in self.entries:
                    if e.id == 0 or e.id is None:
                        current_max += 1
                        e.id = current_max
                        needs_save = True
                    else:
                        if e.id > current_max: current_max = e.id

                self._update_next_id()

                if needs_save:
                    self.save_data()

        except Exception as e:
            print(f"Viga laadimisel: {e}")

    def import_from_csv(self, filename):
        if not os.path.exists(filename):
            return f"Faili {filename} ei leitud."

        success = 0
        errors = 0

        try:
            with open(filename, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=";")
                for row in reader:
                    if len(row) < 3: continue
                    # CSV formaat: Date;Title;Desc;Status
                    # Me ei võta CSVst ID-d, vaid laseme programmil luua uue
                    res, msg = self.add_entry(
                        title=row[1],
                        description=row[2],
                        status=row[3] if len(row) > 3 else "OPEN",
                        created_at=row[0]
                    )
                    if res:
                        success += 1
                    else:
                        errors += 1

            self.save_data()  # Salvestame pärast importi
            return f"Imporditud {success}, vigu {errors}."
        except Exception as e:
            return f"Viga: {e}"
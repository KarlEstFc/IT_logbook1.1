import csv
from src.models import LogEntry


def import_csv_file(filename, logbook):
    success = 0
    errors = 0

    # LOOGIKA: Ressursside haldus (with open)
    # Failid tuleb ALATI sulgeda. "with open" teeb seda automaatselt,
    # isegi kui tekib viga. See väldib mälu lekkeid.
    try:
        with open(filename, "r", encoding="utf-8") as f_in, \
                open("import_errors.log", "w", encoding="utf-8") as f_err:

            # Sinu failis on eraldajaks semikoolon
            reader = csv.reader(f_in, delimiter=';')

            for row in reader:
                # 1. Kontrolli struktuuri (kas tulpi on piisavalt?)
                if not row or len(row) < 3:
                    continue

                    # 2. Valmista andmed ette
                raw_date = row[0].strip()
                title = row[1].strip()
                description = row[2].strip()
                status = row[3].strip() if len(row) > 3 else "OPEN"

                # 3. Proovi luua objekt (Try-Except)
                # See on kriitiline. Kui LogEntry klass ütleb "Viga!",
                # siis me ei lõpeta programmi, vaid kirjutame logisse ja võtame järgmise rea.
                try:
                    entry = LogEntry(title, description, status, created_at=raw_date)
                    logbook.add_entry(entry)
                    success += 1
                except ValueError as ve:
                    errors += 1
                    f_err.write(f"VIGA: {ve} -> RIDA: {row}\n")

    except FileNotFoundError:
        return "Faili ei leitud!"

    return f"Import valmis. Edukaid: {success}, Vigu: {errors} (vaata import_errors.log)"
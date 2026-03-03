from models import LogBook


def main():
    book = LogBook()

    print("Tere")

    while True:
        print("\n--- IT HOOLDUSPÄEVIK ---")
        print("1. Lisa uus")
        print("2. Kuva kõik")
        print("3. Otsi")
        print("4. Filtreeri (OPEN/DONE)")
        print("5. Muuda staatust (ID järgi)")
        print("6. Kustuta (ID järgi)")
        print("7. Import CSV")
        print("Q. Välju")

        valik = input("\nValik: ").strip().lower()

        if valik == '1':
            print("\n--- Uus kanne (Jäta tühjaks ja vajuta Enter, et katkestada) ---")

            # UUS: Tsükkel kordab küsimust kuni andmed on õiged või kasutaja loobub
            while True:
                title = input("Pealkiri (min 4): ").strip()
                if not title:
                    print("Katkestatud.")
                    break

                desc = input("Kirjeldus (min 10): ").strip()
                if not desc:
                    print("Katkestatud.")
                    break

                # Proovime lisada
                success, msg = book.add_entry(title, desc)
                if success:
                    print(f"OK! {msg}")
                    break  # Välju tsüklist, sest õnnestus
                else:
                    print(f"VIGA: {msg} - Proovi uuesti!")

        elif valik == '2':
            print("\n--- Nimekiri ---")
            if not book.entries:
                print("Tühi.")
            for e in book.entries:
                print(e)

        elif valik == '3':
            s = input("Otsing: ")
            results = book.search_entries(s)
            for e in results: print(e)

        elif valik == '4':
            s = input("Staatus (OPEN/DONE): ").upper()
            results = book.filter_by_status(s)
            for e in results: print(e)

        elif valik == '5':
            # UUS: Küsib ID numbrit
            uid = input("Sisesta kirje ID number (see number nurksulgudes []): ")
            success, msg = book.change_status(uid)
            print(msg)

        elif valik == '6':
            # UUS: Küsib ID numbrit
            uid = input("Sisesta kirje ID number kustutamiseks: ")
            success, msg = book.delete_entry(uid)
            print(msg)

        elif valik == '7':
            print("...")
            fn = input("Failinimi (nt sample_import.csv): ")
            print(book.import_from_csv(fn))

        elif valik == 'q':
            print("Head aega!")
            break


if __name__ == "__main__":
    main()
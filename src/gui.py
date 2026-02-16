import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from models import LogBook, LogEntry


class LogBookApp:
    def __init__(self, root):
        self.book = LogBook()
        self.root = root
        self.root.title("IT Hoolduspäevik")
        self.root.geometry("900x600")

        # Ülemine osa: nupud ja otsing
        top_frame = tk.Frame(root, pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Button(top_frame, text="Lisa uus", command=self.add_entry_window).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Muuda staatust", command=self.toggle_status).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Kustuta", command=self.delete_entry).pack(side=tk.LEFT, padx=5)

        tk.Label(top_frame, text="Otsing/Filter:").pack(side=tk.LEFT, padx=10)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.update_list)
        tk.Entry(top_frame, textvariable=self.search_var).pack(side=tk.LEFT)

        # Keskmine osa: Tabel (Treeview)
        self.tree = ttk.Treeview(root, columns=("time", "status", "title", "desc"), show="headings")
        self.tree.heading("time", text="Aeg")
        self.tree.heading("status", text="Staatus")
        self.tree.heading("title", text="Pealkiri")
        self.tree.heading("desc", text="Kirjeldus")

        self.tree.column("time", width=150)
        self.tree.column("status", width=80)
        self.tree.column("title", width=200)
        self.tree.column("desc", width=400)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Alumine osa: Salvestamine
        btn_frame = tk.Frame(root, pady=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Button(btn_frame, text="Salvesta andmed", command=self.save_data).pack(side=tk.RIGHT, padx=10)

        # Alglaadimine
        self.refresh_list()

    def refresh_list(self, entries=None):
        """Uuendab tabeli sisu."""
        for i in self.tree.get_children():
            self.tree.delete(i)

        data = entries if entries is not None else self.book.entries
        for entry in data:
            self.tree.insert("", tk.END, values=(entry.created_at, entry.status, entry.title, entry.description))

    def update_list(self, *args):
        """Filtreerib listi vastavalt otsingukastile."""
        keyword = self.search_var.get()
        if keyword:
            filtered = self.book.search_entries(keyword)
            self.refresh_list(filtered)
        else:
            self.refresh_list()

    def add_entry_window(self):
        """Aken uue kirje lisamiseks."""
        add_win = tk.Toplevel(self.root)
        add_win.title("Lisa kirje")

        tk.Label(add_win, text="Pealkiri (min 4):").pack()
        e_title = tk.Entry(add_win, width=40)
        e_title.pack()

        tk.Label(add_win, text="Kirjeldus (min 10):").pack()
        e_desc = tk.Entry(add_win, width=40)
        e_desc.pack()

        def save():
            title = e_title.get()
            desc = e_desc.get()
            entry = LogEntry(title, desc)
            valid, msg = entry.validate()
            if valid:
                self.book.add_entry(entry)
                self.refresh_list()
                add_win.destroy()
            else:
                messagebox.showerror("Viga", msg)

        tk.Button(add_win, text="Lisa", command=save).pack(pady=10)

    def toggle_status(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Hoiatus", "Vali kirje!")
            return

        item = self.tree.item(selected[0])
        created_at = item['values'][0]  # Esimene tulp on ID

        if self.book.change_status(created_at):
            self.refresh_list()

    def delete_entry(self):
        selected = self.tree.selection()
        if not selected:
            return

        if messagebox.askyesno("Kinnita", "Kas oled kindel?"):
            item = self.tree.item(selected[0])
            created_at = item['values'][0]
            self.book.delete_entry(created_at)
            self.refresh_list()

    def save_data(self):
        self.book.save_data()
        messagebox.showinfo("Info", "Andmed salvestatud!")


if __name__ == "__main__":
    root = tk.Tk()
    app = LogBookApp(root)
    root.mainloop()
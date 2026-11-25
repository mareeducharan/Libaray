"""
LIBRARY MANAGEMENT SYSTEM
Semester 3 Engineering - Programming with Python
Student: MAREEDU CHARAN

A desktop GUI application using Tkinter and SQLite.
Python 3.8+ | No third-party packages required.
"""

import csv
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, timedelta
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "library.db"
LOAN_DAYS = 14
FINE_PER_DAY = 2.0


class LibraryDB:
    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS books (
                book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                category TEXT DEFAULT '',
                isbn TEXT UNIQUE,
                total_copies INTEGER NOT NULL DEFAULT 1 CHECK(total_copies >= 0),
                available_copies INTEGER NOT NULL DEFAULT 1 CHECK(available_copies >= 0)
            );
            CREATE TABLE IF NOT EXISTS members (
                member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                phone TEXT DEFAULT '',
                email TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS loans (
                loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                member_id INTEGER NOT NULL,
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                return_date TEXT,
                fine REAL NOT NULL DEFAULT 0,
                FOREIGN KEY(book_id) REFERENCES books(book_id),
                FOREIGN KEY(member_id) REFERENCES members(member_id)
            );
        """)
        self.conn.commit()

    def rows(self, query, params=()):
        return self.conn.execute(query, params).fetchall()

    def add_book(self, title, author, category, isbn, copies):
        self.conn.execute(
            "INSERT INTO books(title,author,category,isbn,total_copies,available_copies) VALUES(?,?,?,?,?,?)",
            (title, author, category, isbn or None, copies, copies))
        self.conn.commit()

    def update_book(self, book_id, title, author, category, isbn, total):
        row = self.rows("SELECT * FROM books WHERE book_id=?", (book_id,))
        if not row:
            raise ValueError("Book not found.")
        book = row[0]
        issued = book["total_copies"] - book["available_copies"]
        if total < issued:
            raise ValueError(f"Total copies cannot be less than {issued} currently issued copies.")
        self.conn.execute(
            """UPDATE books SET title=?,author=?,category=?,isbn=?,
               total_copies=?,available_copies=? WHERE book_id=?""",
            (title, author, category, isbn or None, total, total-issued, book_id))
        self.conn.commit()

    def delete_book(self, book_id):
        if self.rows("SELECT 1 FROM loans WHERE book_id=? LIMIT 1", (book_id,)):
            raise ValueError("This book has loan history and cannot be deleted.")
        self.conn.execute("DELETE FROM books WHERE book_id=?", (book_id,))
        self.conn.commit()

    def add_member(self, name, class_name, phone, email):
        self.conn.execute(
            "INSERT INTO members(name,class_name,phone,email) VALUES(?,?,?,?)",
            (name, class_name, phone, email))
        self.conn.commit()

    def update_member(self, member_id, name, class_name, phone, email):
        self.conn.execute(
            "UPDATE members SET name=?,class_name=?,phone=?,email=? WHERE member_id=?",
            (name, class_name, phone, email, member_id))
        self.conn.commit()

    def delete_member(self, member_id):
        if self.rows("SELECT 1 FROM loans WHERE member_id=? LIMIT 1", (member_id,)):
            raise ValueError("This member has loan history and cannot be deleted.")
        self.conn.execute("DELETE FROM members WHERE member_id=?", (member_id,))
        self.conn.commit()

    def issue_book(self, book_id, member_id):
        book = self.rows("SELECT * FROM books WHERE book_id=?", (book_id,))
        member = self.rows("SELECT * FROM members WHERE member_id=?", (member_id,))
        if not book or not member:
            raise ValueError("Select a valid book and member.")
        if book[0]["available_copies"] < 1:
            raise ValueError("No copies of this book are currently available.")
        active = self.rows(
            "SELECT 1 FROM loans WHERE book_id=? AND member_id=? AND return_date IS NULL",
            (book_id, member_id))
        if active:
            raise ValueError("This member already has this book issued.")
        today = date.today()
        due = today + timedelta(days=LOAN_DAYS)
        with self.conn:
            self.conn.execute("UPDATE books SET available_copies=available_copies-1 WHERE book_id=?",
                              (book_id,))
            self.conn.execute(
                "INSERT INTO loans(book_id,member_id,issue_date,due_date) VALUES(?,?,?,?)",
                (book_id, member_id, today.isoformat(), due.isoformat()))

    def return_book(self, loan_id):
        loan = self.rows("SELECT * FROM loans WHERE loan_id=? AND return_date IS NULL", (loan_id,))
        if not loan:
            raise ValueError("Active issue record not found.")
        today = date.today()
        due = date.fromisoformat(loan[0]["due_date"])
        late_days = max(0, (today - due).days)
        fine = late_days * FINE_PER_DAY
        with self.conn:
            self.conn.execute("UPDATE loans SET return_date=?,fine=? WHERE loan_id=?",
                              (today.isoformat(), fine, loan_id))
            self.conn.execute("UPDATE books SET available_copies=available_copies+1 WHERE book_id=?",
                              (loan[0]["book_id"],))
        return late_days, fine

    def stats(self):
        return {
            "books": self.rows("SELECT COALESCE(SUM(total_copies),0) n FROM books")[0]["n"],
            "available": self.rows("SELECT COALESCE(SUM(available_copies),0) n FROM books")[0]["n"],
            "members": self.rows("SELECT COUNT(*) n FROM members")[0]["n"],
            "issued": self.rows("SELECT COUNT(*) n FROM loans WHERE return_date IS NULL")[0]["n"],
            "overdue": self.rows(
                "SELECT COUNT(*) n FROM loans WHERE return_date IS NULL AND due_date < ?",
                (date.today().isoformat(),))[0]["n"],
        }

    def close(self):
        self.conn.close()


class LibraryApp(tk.Tk):
    BG = "#F3F6FB"
    NAVY = "#172B4D"
    BLUE = "#2563EB"
    TEXT = "#243247"
    MUTED = "#64748B"
    WHITE = "#FFFFFF"

    def __init__(self):
        super().__init__()
        self.db = LibraryDB()
        self.title("Library Management System | MAREEDU CHARAN")
        self.geometry("1180x760")
        self.minsize(980, 650)
        self.configure(bg=self.BG)
        self.selected_book = None
        self.selected_member = None
        self._style()
        self._build_shell()
        self.show_dashboard()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", background="white", fieldbackground="white",
                        foreground=self.TEXT, rowheight=30, borderwidth=0)
        style.configure("Treeview.Heading", background="#E8EEF8", foreground=self.NAVY,
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#DBEAFE")],
                  foreground=[("selected", self.NAVY)])
        style.configure("TCombobox", padding=6)

    def _build_shell(self):
        header = tk.Frame(self, bg=self.NAVY, height=76)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="▣  LIBRARY MANAGEMENT SYSTEM", bg=self.NAVY,
                 fg="white", font=("Segoe UI", 17, "bold")).pack(side="left", padx=24)
        tk.Label(header, text="PYTHON PROJECT  •  SEMESTER 3",
                 bg=self.NAVY, fg="#B9C8E3", font=("Segoe UI", 9, "bold")).pack(side="right", padx=24)

        body = tk.Frame(self, bg=self.BG)
        body.pack(fill="both", expand=True)
        self.sidebar = tk.Frame(body, bg="#20385F", width=215)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="MAIN MENU", bg="#20385F", fg="#AFC2E2",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(24, 12))
        nav = [
            ("▦   Dashboard", self.show_dashboard),
            ("▤   Books", self.show_books),
            ("♙   Members", self.show_members),
            ("⇄   Issue / Return", self.show_loans),
            ("▧   Reports", self.show_reports),
        ]
        for label, command in nav:
            b = tk.Button(self.sidebar, text=label, command=command, anchor="w",
                          bg="#20385F", fg="white", activebackground="#31517F",
                          activeforeground="white", relief="flat", bd=0,
                          font=("Segoe UI", 10), padx=20, pady=13, cursor="hand2")
            b.pack(fill="x")
        tk.Frame(self.sidebar, bg="#496080", height=1).pack(fill="x", padx=18, pady=18)
        tk.Label(self.sidebar, text="Logged in as", bg="#20385F", fg="#AFC2E2",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=20)
        tk.Label(self.sidebar, text="MAREEDU CHARAN", bg="#20385F", fg="white",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(4, 0))

        self.content = tk.Frame(body, bg=self.BG)
        self.content.pack(side="left", fill="both", expand=True, padx=24, pady=22)
        self.status = tk.StringVar(value="Ready")
        footer = tk.Label(self, textvariable=self.status, anchor="w", bg="#E7EDF6",
                          fg=self.MUTED, padx=16, pady=7, font=("Segoe UI", 8))
        footer.pack(fill="x")

    def clear(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def page_title(self, title, subtitle=""):
        tk.Label(self.content, text=title, bg=self.BG, fg=self.NAVY,
                 font=("Segoe UI", 21, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(self.content, text=subtitle, bg=self.BG, fg=self.MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 16))
        else:
            tk.Frame(self.content, bg=self.BG, height=16).pack()

    def button(self, parent, text, command, primary=True):
        return tk.Button(parent, text=text, command=command,
                         bg=self.BLUE if primary else "#E2E8F0",
                         fg="white" if primary else self.TEXT,
                         activebackground="#1D4ED8" if primary else "#CBD5E1",
                         activeforeground="white" if primary else self.TEXT,
                         relief="flat", bd=0, padx=14, pady=8,
                         font=("Segoe UI", 9, "bold"), cursor="hand2")

    def tree(self, parent, columns, headings, widths=None):
        wrap = tk.Frame(parent, bg=self.WHITE)
        wrap.pack(fill="both", expand=True)
        tree = ttk.Treeview(wrap, columns=columns, show="headings")
        for i, (col, head) in enumerate(zip(columns, headings)):
            tree.heading(col, text=head)
            tree.column(col, width=(widths[i] if widths else 120), anchor="w")
        y = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        x = ttk.Scrollbar(wrap, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
        tree.grid(row=0, column=0, sticky="nsew")
        y.grid(row=0, column=1, sticky="ns")
        x.grid(row=1, column=0, sticky="ew")
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)
        return tree

    def show_dashboard(self):
        self.clear()
        self.page_title("Dashboard", "A quick overview of your library")
        stats = self.db.stats()
        cards = tk.Frame(self.content, bg=self.BG)
        cards.pack(fill="x", pady=(0, 20))
        items = [
            ("TOTAL BOOK COPIES", stats["books"], "#2563EB"),
            ("AVAILABLE COPIES", stats["available"], "#0F9F6E"),
            ("REGISTERED MEMBERS", stats["members"], "#7C3AED"),
            ("BOOKS ISSUED", stats["issued"], "#D97706"),
            ("OVERDUE ISSUES", stats["overdue"], "#DC2626"),
        ]
        for i, (label, value, color) in enumerate(items):
            card = tk.Frame(cards, bg=self.WHITE, highlightbackground="#E2E8F0",
                            highlightthickness=1, padx=16, pady=14)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            cards.columnconfigure(i, weight=1)
            tk.Frame(card, bg=color, height=4).pack(fill="x", pady=(0, 12))
            tk.Label(card, text=label, bg=self.WHITE, fg=self.MUTED,
                     font=("Segoe UI", 8, "bold"), wraplength=130).pack(anchor="w")
            tk.Label(card, text=str(value), bg=self.WHITE, fg=self.NAVY,
                     font=("Segoe UI", 23, "bold")).pack(anchor="w", pady=(6, 0))

        panel = tk.Frame(self.content, bg=self.WHITE, padx=18, pady=16,
                         highlightbackground="#E2E8F0", highlightthickness=1)
        panel.pack(fill="both", expand=True)
        tk.Label(panel, text="Currently issued books", bg=self.WHITE, fg=self.NAVY,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 12))
        tree = self.tree(panel, ("loan", "book", "member", "issue", "due"),
                         ("Loan ID", "Book", "Member", "Issue Date", "Due Date"),
                         (75, 250, 190, 120, 120))
        rows = self.db.rows("""
            SELECT l.loan_id,b.title book,m.name member,l.issue_date,l.due_date
            FROM loans l JOIN books b ON b.book_id=l.book_id
            JOIN members m ON m.member_id=l.member_id
            WHERE l.return_date IS NULL ORDER BY l.due_date
        """)
        for r in rows:
            tree.insert("", "end", values=(r["loan_id"], r["book"], r["member"],
                                           r["issue_date"], r["due_date"]))
        self.status.set("Dashboard refreshed")

    def show_books(self):
        self.clear()
        self.page_title("Book Catalogue", "Add, edit, remove and search the library collection")
        form = tk.Frame(self.content, bg=self.WHITE, padx=14, pady=12,
                        highlightbackground="#E2E8F0", highlightthickness=1)
        form.pack(fill="x", pady=(0, 14))
        fields = [("Title", 26), ("Author", 20), ("Category", 15), ("ISBN", 16), ("Copies", 7)]
        self.book_vars = {}
        for i, (label, width) in enumerate(fields):
            tk.Label(form, text=label, bg=self.WHITE, fg=self.MUTED,
                     font=("Segoe UI", 8, "bold")).grid(row=0, column=i, sticky="w", padx=5)
            var = tk.StringVar()
            self.book_vars[label] = var
            tk.Entry(form, textvariable=var, width=width, relief="solid", bd=1,
                     font=("Segoe UI", 9)).grid(row=1, column=i, padx=5, pady=(4, 8), ipady=5)
        actions = tk.Frame(form, bg=self.WHITE)
        actions.grid(row=2, column=0, columnspan=5, sticky="w", padx=5)
        self.button(actions, "Add Book", self.add_book).pack(side="left", padx=(0, 6))
        self.button(actions, "Update Selected", self.update_book, False).pack(side="left", padx=6)
        self.button(actions, "Delete Selected", self.delete_book, False).pack(side="left", padx=6)
        self.button(actions, "Clear Form", self.clear_book_form, False).pack(side="left", padx=6)

        searchrow = tk.Frame(self.content, bg=self.BG)
        searchrow.pack(fill="x", pady=(0, 8))
        self.book_search = tk.StringVar()
        tk.Label(searchrow, text="Search books:", bg=self.BG, fg=self.TEXT).pack(side="left")
        ent = tk.Entry(searchrow, textvariable=self.book_search, width=32, relief="solid", bd=1)
        ent.pack(side="left", padx=8, ipady=4)
        ent.bind("<KeyRelease>", lambda e: self.refresh_books())
        self.button(searchrow, "Refresh", self.refresh_books, False).pack(side="left")
        self.book_tree = self.tree(self.content,
            ("id", "title", "author", "category", "isbn", "total", "available"),
            ("ID", "Title", "Author", "Category", "ISBN", "Total", "Available"),
            (55, 230, 170, 120, 140, 65, 80))
        self.book_tree.bind("<<TreeviewSelect>>", self.select_book)
        self.refresh_books()

    def refresh_books(self):
        if not hasattr(self, "book_tree") or not self.book_tree.winfo_exists():
            return
        self.book_tree.delete(*self.book_tree.get_children())
        term = self.book_search.get().strip()
        rows = self.db.rows("""SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ? OR category LIKE ? OR isbn LIKE ?
            ORDER BY title""", tuple([f"%{term}%"] * 4))
        for r in rows:
            self.book_tree.insert("", "end", values=(r["book_id"], r["title"], r["author"],
                r["category"], r["isbn"] or "", r["total_copies"], r["available_copies"]))

    def select_book(self, _event=None):
        selected = self.book_tree.selection()
        if not selected:
            return
        values = self.book_tree.item(selected[0], "values")
        self.selected_book = int(values[0])
        for label, value in zip(("Title", "Author", "Category", "ISBN", "Copies"), values[1:6]):
            self.book_vars[label].set(value)

    def clear_book_form(self):
        self.selected_book = None
        for v in self.book_vars.values():
            v.set("")
        if hasattr(self, "book_tree"):
            self.book_tree.selection_remove(self.book_tree.selection())

    def add_book(self):
        v = {k: x.get().strip() for k, x in self.book_vars.items()}
        try:
            copies = int(v["Copies"])
            if not v["Title"] or not v["Author"] or copies < 1:
                raise ValueError("Enter title, author and a copies value of at least 1.")
            self.db.add_book(v["Title"], v["Author"], v["Category"], v["ISBN"], copies)
            self.refresh_books()
            self.clear_book_form()
            self.status.set("Book added successfully")
        except (ValueError, sqlite3.IntegrityError) as e:
            messagebox.showerror("Cannot add book", str(e))

    def update_book(self):
        if not self.selected_book:
            messagebox.showwarning("Select book", "Select a book from the table first.")
            return
        v = {k: x.get().strip() for k, x in self.book_vars.items()}
        try:
            copies = int(v["Copies"])
            if not v["Title"] or not v["Author"] or copies < 0:
                raise ValueError("Enter title, author and a valid copies value.")
            self.db.update_book(self.selected_book, v["Title"], v["Author"],
                                v["Category"], v["ISBN"], copies)
            self.refresh_books()
            self.clear_book_form()
            self.status.set("Book updated successfully")
        except (ValueError, sqlite3.IntegrityError) as e:
            messagebox.showerror("Cannot update book", str(e))

    def delete_book(self):
        if not self.selected_book:
            messagebox.showwarning("Select book", "Select a book from the table first.")
            return
        if messagebox.askyesno("Confirm delete", "Delete the selected book?"):
            try:
                self.db.delete_book(self.selected_book)
                self.refresh_books()
                self.clear_book_form()
                self.status.set("Book deleted")
            except ValueError as e:
                messagebox.showerror("Cannot delete book", str(e))

    def show_members(self):
        self.clear()
        self.page_title("Member Management", "Maintain student and library member details")
        form = tk.Frame(self.content, bg=self.WHITE, padx=14, pady=12,
                        highlightbackground="#E2E8F0", highlightthickness=1)
        form.pack(fill="x", pady=(0, 14))
        self.member_vars = {}
        for i, (label, width) in enumerate([("Name", 24), ("Class", 16), ("Phone", 17), ("Email", 28)]):
            tk.Label(form, text=label, bg=self.WHITE, fg=self.MUTED,
                     font=("Segoe UI", 8, "bold")).grid(row=0, column=i, sticky="w", padx=5)
            var = tk.StringVar()
            self.member_vars[label] = var
            tk.Entry(form, textvariable=var, width=width, relief="solid", bd=1).grid(
                row=1, column=i, padx=5, pady=(4, 8), ipady=5)
        actions = tk.Frame(form, bg=self.WHITE)
        actions.grid(row=2, column=0, columnspan=4, sticky="w", padx=5)
        self.button(actions, "Add Member", self.add_member).pack(side="left", padx=(0, 6))
        self.button(actions, "Update Selected", self.update_member, False).pack(side="left", padx=6)
        self.button(actions, "Delete Selected", self.delete_member, False).pack(side="left", padx=6)
        self.button(actions, "Clear Form", self.clear_member_form, False).pack(side="left", padx=6)
        self.member_tree = self.tree(self.content, ("id", "name", "class", "phone", "email"),
            ("Member ID", "Name", "Class", "Phone", "Email"), (90, 220, 130, 150, 250))
        self.member_tree.bind("<<TreeviewSelect>>", self.select_member)
        self.refresh_members()

    def refresh_members(self):
        if not hasattr(self, "member_tree") or not self.member_tree.winfo_exists():
            return
        self.member_tree.delete(*self.member_tree.get_children())
        for r in self.db.rows("SELECT * FROM members ORDER BY name"):
            self.member_tree.insert("", "end", values=(r["member_id"], r["name"],
                r["class_name"], r["phone"], r["email"]))

    def select_member(self, _event=None):
        selected = self.member_tree.selection()
        if not selected:
            return
        values = self.member_tree.item(selected[0], "values")
        self.selected_member = int(values[0])
        for label, value in zip(("Name", "Class", "Phone", "Email"), values[1:]):
            self.member_vars[label].set(value)

    def clear_member_form(self):
        self.selected_member = None
        for v in self.member_vars.values():
            v.set("")
        if hasattr(self, "member_tree"):
            self.member_tree.selection_remove(self.member_tree.selection())

    def add_member(self):
        v = {k: x.get().strip() for k, x in self.member_vars.items()}
        if not v["Name"] or not v["Class"]:
            messagebox.showerror("Missing details", "Name and class are required.")
            return
        self.db.add_member(v["Name"], v["Class"], v["Phone"], v["Email"])
        self.refresh_members()
        self.clear_member_form()
        self.status.set("Member added successfully")

    def update_member(self):
        if not self.selected_member:
            messagebox.showwarning("Select member", "Select a member from the table first.")
            return
        v = {k: x.get().strip() for k, x in self.member_vars.items()}
        if not v["Name"] or not v["Class"]:
            messagebox.showerror("Missing details", "Name and class are required.")
            return
        self.db.update_member(self.selected_member, v["Name"], v["Class"],
                              v["Phone"], v["Email"])
        self.refresh_members()
        self.clear_member_form()
        self.status.set("Member updated successfully")

    def delete_member(self):
        if not self.selected_member:
            messagebox.showwarning("Select member", "Select a member from the table first.")
            return
        if messagebox.askyesno("Confirm delete", "Delete the selected member?"):
            try:
                self.db.delete_member(self.selected_member)
                self.refresh_members()
                self.clear_member_form()
                self.status.set("Member deleted")
            except ValueError as e:
                messagebox.showerror("Cannot delete member", str(e))

    def show_loans(self):
        self.clear()
        self.page_title("Issue & Return", f"Standard loan period: {LOAN_DAYS} days  |  Late fine: ₹{FINE_PER_DAY:.0f} per day")
        panel = tk.Frame(self.content, bg=self.WHITE, padx=16, pady=14,
                         highlightbackground="#E2E8F0", highlightthickness=1)
        panel.pack(fill="x", pady=(0, 14))
        books = self.db.rows("SELECT book_id,title,available_copies FROM books WHERE available_copies>0 ORDER BY title")
        members = self.db.rows("SELECT member_id,name,class_name FROM members ORDER BY name")
        self.book_choices = {f"{r['book_id']} - {r['title']} (Available: {r['available_copies']})": r["book_id"] for r in books}
        self.member_choices = {f"{r['member_id']} - {r['name']} ({r['class_name']})": r["member_id"] for r in members}
        tk.Label(panel, text="Select book", bg=self.WHITE, fg=self.TEXT).grid(row=0, column=0, sticky="w")
        self.issue_book_var = tk.StringVar()
        self.issue_book_combo = ttk.Combobox(panel, textvariable=self.issue_book_var,
            values=list(self.book_choices), width=38, state="readonly")
        self.issue_book_combo.grid(row=1, column=0, padx=(0, 16), pady=6, sticky="w")
        tk.Label(panel, text="Select member", bg=self.WHITE, fg=self.TEXT).grid(row=0, column=1, sticky="w")
        self.issue_member_var = tk.StringVar()
        ttk.Combobox(panel, textvariable=self.issue_member_var,
            values=list(self.member_choices), width=38, state="readonly").grid(
                row=1, column=1, padx=(0, 16), pady=6, sticky="w")
        self.button(panel, "Issue Book", self.issue_book_action).grid(row=1, column=2, padx=5)
        self.button(panel, "Return Selected", self.return_book_action, False).grid(row=1, column=3, padx=5)
        tk.Label(self.content, text="Active issue records", bg=self.BG, fg=self.NAVY,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))
        self.loan_tree = self.tree(self.content,
            ("loan", "book", "member", "issue", "due", "overdue"),
            ("Loan ID", "Book", "Member", "Issue Date", "Due Date", "Status"),
            (70, 235, 190, 115, 115, 100))
        self.refresh_loans()

    def refresh_loans(self):
        if not hasattr(self, "loan_tree") or not self.loan_tree.winfo_exists():
            return
        self.loan_tree.delete(*self.loan_tree.get_children())
        rows = self.db.rows("""SELECT l.loan_id,b.title book,m.name member,l.issue_date,l.due_date
            FROM loans l JOIN books b ON b.book_id=l.book_id
            JOIN members m ON m.member_id=l.member_id
            WHERE l.return_date IS NULL ORDER BY l.due_date""")
        for r in rows:
            status = "OVERDUE" if r["due_date"] < date.today().isoformat() else "On time"
            self.loan_tree.insert("", "end", values=(r["loan_id"], r["book"], r["member"],
                r["issue_date"], r["due_date"], status))

    def issue_book_action(self):
        book_label = self.issue_book_var.get()
        member_label = self.issue_member_var.get()
        if not book_label or not member_label:
            messagebox.showwarning("Missing selection", "Choose both a book and a member.")
            return
        try:
            self.db.issue_book(self.book_choices[book_label], self.member_choices[member_label])
            messagebox.showinfo("Book issued", f"Book issued successfully.\nDue date: {date.today() + timedelta(days=LOAN_DAYS)}")
            self.show_loans()
        except ValueError as e:
            messagebox.showerror("Cannot issue book", str(e))

    def return_book_action(self):
        selected = self.loan_tree.selection()
        if not selected:
            messagebox.showwarning("Select issue", "Select an active issue record first.")
            return
        loan_id = int(self.loan_tree.item(selected[0], "values")[0])
        try:
            days, fine = self.db.return_book(loan_id)
            messagebox.showinfo("Book returned",
                f"Book returned successfully.\nLate days: {days}\nFine: ₹{fine:.2f}")
            self.show_loans()
        except ValueError as e:
            messagebox.showerror("Cannot return book", str(e))

    def show_reports(self):
        self.clear()
        self.page_title("Library Reports", "View current inventory, issue status and fine summary")
        stats = self.db.stats()
        summary = tk.Frame(self.content, bg=self.WHITE, padx=18, pady=16,
                           highlightbackground="#E2E8F0", highlightthickness=1)
        summary.pack(fill="x", pady=(0, 14))
        text = (f"Total book copies: {stats['books']}     |     Available: {stats['available']}     |     "
                f"Issued: {stats['issued']}     |     Members: {stats['members']}     |     Overdue: {stats['overdue']}")
        tk.Label(summary, text=text, bg=self.WHITE, fg=self.NAVY,
                 font=("Segoe UI", 10, "bold"), wraplength=850).pack(anchor="w")
        actions = tk.Frame(self.content, bg=self.BG)
        actions.pack(fill="x", pady=(0, 12))
        self.button(actions, "Export Books CSV", lambda: self.export_query(
            "SELECT book_id,title,author,category,isbn,total_copies,available_copies FROM books",
            "books_report.csv")).pack(side="left", padx=(0, 8))
        self.button(actions, "Export Members CSV", lambda: self.export_query(
            "SELECT member_id,name,class_name,phone,email FROM members",
            "members_report.csv"), False).pack(side="left", padx=8)
        self.button(actions, "Export Issue History CSV", lambda: self.export_query(
            """SELECT l.loan_id,b.title book,m.name member,l.issue_date,l.due_date,
               l.return_date,l.fine FROM loans l JOIN books b ON b.book_id=l.book_id
               JOIN members m ON m.member_id=l.member_id""",
            "issue_history.csv"), False).pack(side="left", padx=8)
        tk.Label(self.content, text="Recent transaction history", bg=self.BG, fg=self.NAVY,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(8, 8))
        tree = self.tree(self.content, ("id", "book", "member", "issue", "due", "returned", "fine"),
            ("Loan ID", "Book", "Member", "Issue Date", "Due Date", "Return Date", "Fine (₹)"),
            (70, 200, 160, 110, 110, 110, 80))
        rows = self.db.rows("""SELECT l.loan_id,b.title book,m.name member,l.issue_date,
            l.due_date,l.return_date,l.fine FROM loans l JOIN books b ON b.book_id=l.book_id
            JOIN members m ON m.member_id=l.member_id ORDER BY l.loan_id DESC LIMIT 100""")
        for r in rows:
            tree.insert("", "end", values=(r["loan_id"], r["book"], r["member"],
                r["issue_date"], r["due_date"], r["return_date"] or "Not returned",
                f"{r['fine']:.2f}"))

    def export_query(self, query, default_name):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
            initialfile=default_name, filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        rows = self.db.rows(query)
        if rows:
            headers = rows[0].keys()
        else:
            headers = [d[0] for d in self.db.conn.execute(query).description]
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            for row in rows:
                writer.writerow([row[h] for h in headers])
        messagebox.showinfo("Export complete", f"Report saved to:\n{path}")
        self.status.set(f"Exported {default_name}")

    def on_close(self):
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = LibraryApp()
    app.mainloop()

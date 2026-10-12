import os
import sqlite3
from datetime import datetime
from cryptography.fernet import Fernet
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Backend
class SecureFinanceDB:
    def __init__(self, db_filename="finance.db.encrypted"):
        self.db_filename = db_filename
        key_env = os.environ.get("TRACKER_KEY")
        if not key_env:
            raise ValueError("CRITICAL: TRACKER_KEY environment variable not found. Data cannot be secured.")
        
        self.cipher_suite = Fernet(key_env.encode())
        self.temp_db_name = "temp_unencrypted.db"
        self.setup_tables()

    def _decrypt_db(self):
        """Decrypts the DB into a temporary file for SQLite interaction."""
        if not os.path.exists(self.db_filename):
            open(self.temp_db_name, 'a').close() 
            return

        with open(self.db_filename, 'rb') as encrypted_file:
            encrypted_data = encrypted_file.read()
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
        
        with open(self.temp_db_name, 'wb') as temp_file:
            temp_file.write(decrypted_data)

    def _encrypt_db(self):
        """Re-encrypts the temporary file and securely purges the unencrypted version."""
        if os.path.exists(self.temp_db_name):
            with open(self.temp_db_name, 'rb') as temp_file:
                db_data = temp_file.read()
            
            encrypted_data = self.cipher_suite.encrypt(db_data)
            
            with open(self.db_filename, 'wb') as encrypted_file:
                encrypted_file.write(encrypted_data)
            
            os.remove(self.temp_db_name)

    def execute_query(self, query, params=(), fetch=False):
        """Executes a SQL query and guarantees re-encryption even if the query fails."""
        self._decrypt_db()
        results = None
        try:
            conn = sqlite3.connect(self.temp_db_name)
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if fetch:
                results = cursor.fetchall()
            else:
                conn.commit()
        except sqlite3.Error as e:
            print(f"Database Error: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
            self._encrypt_db()
            
        return results

    def setup_tables(self):
        """Initializes tables and injects starter data if empty."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL
        )
        """
        self.execute_query(create_table_query)
        
        check_query = "SELECT COUNT(*) FROM transactions"
        count = self.execute_query(check_query, fetch=True)[0][0]
        if count == 0:
            seed_data = [
                (datetime.now().strftime("%Y-%m-%d"), 1500.00, "Electronics"),
                (datetime.now().strftime("%Y-%m-%d"), 850.00, "Cloud Hosting"),
                (datetime.now().strftime("%Y-%m-%d"), 3200.00, "Hardware Tools"),
                (datetime.now().strftime("%Y-%m-%d"), 450.00, "Coffee")
            ]
            for data in seed_data:
                self.execute_query("INSERT INTO transactions (date, amount, category) VALUES (?, ?, ?)", data)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "finance_data.db")

# Frontend
import customtkinter as ctk

BG_COLOR = "#12141c"       
PANEL_COLOR = "#1f2333"    
TEXT_MUTED = "#8b94a5"     
GREEN = "#2ecc71"         
ORANGE = "#e67e22"         
BLUE_BTN = "#5a9cf8"
CYAN = "#58c6ce"   
DARK_GREY = "#2b3145"   
RED = "#e74c3c"

class FinancialTracker(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.setup_database()

        self.title("Financial Tracker")
        self.geometry("1100x700")
        self.configure(fg_color=BG_COLOR)

        self.grid_rowconfigure(2, weight=1) 
        
        self.grid_columnconfigure(0, weight=1, uniform="col")
        self.grid_columnconfigure(1, weight=1, uniform="col")
        self.grid_columnconfigure(2, weight=1, uniform="col")

        self.build_header()
        self.build_kpi_row()
        self.build_input_panel()
        self.build_history_panel()
        self.build_budget_panel()

    def setup_database(self):
        """Creates the local database file and the transaction table if they don't exist."""
        import sqlite3
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    note TEXT
                )
            """)
            conn.commit()
    
    def update_category_options(self, selected_type):
        """Swaps the category list based on whether Expense or Income is selected."""
        if selected_type == "Income":
            self.cat_opt.configure(values=self.income_cats)
            self.cat_opt.set(self.income_cats[0])
        else:
            self.cat_opt.configure(values=self.expense_cats)
            self.cat_opt.set(self.expense_cats[0])

    def build_header(self):
        """Top bar with Title and Month Selector[cite: 10]"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=20, pady=(20, 10))
        header.grid_columnconfigure(1, weight=1) 

        ctk.CTkLabel(header, text="Jamil Domingo", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w")

        month_frame = ctk.CTkFrame(header, fg_color="transparent")
        month_frame.grid(row=0, column=2, sticky="e")
        ctk.CTkLabel(month_frame, text="Month", text_color=TEXT_MUTED).pack(side="left", padx=10)
        ctk.CTkOptionMenu(
            month_frame, 
            values=["October 2026"], 
            fg_color=PANEL_COLOR, 
            button_color=PANEL_COLOR, 
            button_hover_color="#2b3145"
        ).pack(side="left")

    def build_kpi_row(self):
        """The 4 Top Indicator Cards"""
        kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        kpi_container.grid(row=1, column=0, columnspan=3, sticky="ew", padx=20, pady=10)
        kpi_container.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")

        self.lbl_income = self.create_kpi_card(kpi_container, 0, "Income", "₱0.00", GREEN)
        self.lbl_expenses = self.create_kpi_card(kpi_container, 1, "Expenses", "₱0.00", ORANGE)
        self.lbl_balance = self.create_kpi_card(kpi_container, 2, "Balance", "₱0.00", CYAN)
        self.lbl_savings = self.create_kpi_card(kpi_container, 3, "Savings rate", "—", "white")
        
        self.update_kpis()

    def create_kpi_card(self, parent, col, title, value, val_color):
        """Helper to standardize the KPI card design and return the value label"""
        card = ctk.CTkFrame(parent, fg_color=PANEL_COLOR, corner_radius=8)
        card.grid(row=0, column=col, sticky="nsew", padx=(0 if col==0 else 10, 0 if col==3 else 10))
        
        ctk.CTkLabel(card, text=title, text_color=TEXT_MUTED, font=("Arial", 12)).pack(anchor="w", padx=15, pady=(15, 0))
        
        val_label = ctk.CTkLabel(card, text=value, text_color=val_color, font=("Arial", 22, "bold"))
        val_label.pack(anchor="w", padx=15, pady=(0, 15))
        
        return val_label

    def build_input_panel(self):
        """Left Column: Add Transaction Form"""
        panel = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=8)
        panel.grid(row=2, column=0, sticky="nsew", padx=(20, 10), pady=10)
        panel.grid_columnconfigure((0,1), weight=1)
        
        ctk.CTkLabel(panel, text="Add transaction", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=15)
        
        self.expense_cats = ["Food", "Transport", "Bills", "Rent", "Tech", "Others", "Entertainment", "Online Shopping", "Subscription"]
        self.income_cats = ["Allowance", "Investments", "Gift"]
        
        self.type_opt = ctk.CTkOptionMenu(panel, values=["Out", "In"], fg_color=BG_COLOR, button_color=BG_COLOR, command=self.update_category_options)
        self.type_opt.grid(row=1, column=0, sticky="ew", padx=(15, 5), pady=10)
        
        self.cat_opt = ctk.CTkOptionMenu(panel, values=self.expense_cats, fg_color=BG_COLOR, button_color=BG_COLOR)
        self.cat_opt.grid(row=1, column=1, sticky="ew", padx=(5, 15), pady=10)
        
        self.amt_entry = ctk.CTkEntry(panel, placeholder_text="Amount (₱)", fg_color=BG_COLOR, border_width=0)
        self.amt_entry.grid(row=2, column=0, sticky="ew", padx=(15, 5), pady=10)
        
        self.date_entry = ctk.CTkEntry(panel, placeholder_text="10/10/2026", fg_color=BG_COLOR, border_width=0)
        self.date_entry.grid(row=2, column=1, sticky="ew", padx=(5, 15), pady=10)
        
        self.note_entry = ctk.CTkEntry(panel, placeholder_text="Note (optional)", fg_color=BG_COLOR, border_width=0)
        self.note_entry.grid(row=3, column=0, columnspan=2, sticky="ew", padx=15, pady=10)

        btn = ctk.CTkButton(panel, text="Add", fg_color=BLUE_BTN, hover_color="#3673db", corner_radius=6, command=self.save_transaction)
        btn.grid(row=4, column=0, columnspan=2, sticky="ew", padx=15, pady=20)

    def update_category_options(self, selected_type):
        """Swaps the category list based on whether Out or In is selected."""
        if selected_type == "In":
            self.cat_opt.configure(values=self.income_cats)
            self.cat_opt.set(self.income_cats[0])
        else:
            self.cat_opt.configure(values=self.expense_cats)
            self.cat_opt.set(self.expense_cats[0])

    def build_history_panel(self):
        """Middle Column: Transactions List"""
        panel = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=8)
        panel.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(panel, text="Transactions", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=15)
        
        div = ctk.CTkFrame(panel, height=1, fg_color=BG_COLOR)
        div.pack(fill="x", padx=15, pady=(0, 5))
        
        self.history_list_frame = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        self.history_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.refresh_history()

    def build_budget_panel(self):
        """Right Column: Scrollable Budgets List[cite: 10]"""
        panel = ctk.CTkScrollableFrame(self, fg_color=PANEL_COLOR, corner_radius=8)
        panel.grid(row=2, column=2, sticky="nsew", padx=(10, 20), pady=10)
        
        header_frame = ctk.CTkFrame(panel, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=(5, 10))
        
        ctk.CTkLabel(header_frame, text="Budgets", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkLabel(header_frame, text="(monthly limit per category)", text_color=TEXT_MUTED, font=("Arial", 12)).pack(side="left", padx=5, pady=(3, 0))
        
        categories = ["Food", "Transport", "Tech", "Bills", "Rent", "Online Shopping", "Entertainment", "Other"] #[cite: 10]
        
        for cat in categories:
            row = ctk.CTkFrame(panel, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=8)
            
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left")
            ctk.CTkLabel(info, text=cat, font=("Arial", 14)).pack(anchor="w")
            ctk.CTkLabel(info, text="₱0.00", text_color=TEXT_MUTED, font=("Arial", 11)).pack(anchor="w") #[cite: 10]
            
            limit_entry = ctk.CTkEntry(row, placeholder_text="Limit", width=80, fg_color=BG_COLOR, border_width=0)
            limit_entry.pack(side="right", pady=5)
            
            div = ctk.CTkFrame(panel, height=1, fg_color=BG_COLOR)
            div.pack(fill="x", padx=5, pady=2)
    
    def save_transaction(self):
        """Extracts UI data, validates it, and securely saves it to SQLite."""
        import sqlite3
        try:

            t_type = self.type_opt.get()
            category = self.cat_opt.get()
            amount = float(self.amt_entry.get()) 
            date = self.date_entry.get()
            if not date.strip():
                date = datetime.now().strftime("%m/%d/%Y")
            note = self.note_entry.get()
            
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO transactions (type, category, amount, date, note) 
                    VALUES (?, ?, ?, ?, ?)
                """, (t_type, category, amount, date, note))
                conn.commit()
            
            self.amt_entry.delete(0, 'end')
            self.date_entry.delete(0, 'end')
            self.note_entry.delete(0, 'end')
            
            print(f"[+] Successfully logged: {t_type} | {category} | ₱{amount}")
            self.refresh_history()
            self.update_kpis()

        except ValueError:
            print("[-] Error: Amount must be a valid number.")
     
    def refresh_history(self):
        """Fetches the latest transactions from SQLite and redraws the middle column."""
        import sqlite3
        
        for widget in self.history_list_frame.winfo_children():
            widget.destroy()
            
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, type, category, amount, date, note FROM transactions ORDER BY id DESC")
                rows = cursor.fetchall()
                
                if not rows:
                    ctk.CTkLabel(self.history_list_frame, text="No transactions this month.", text_color=TEXT_MUTED).pack(anchor="w", padx=10)
                    return
                    
                for row in rows:
                    t_id, t_type, category, amount, date, note = row 
                    
                    item_frame = ctk.CTkFrame(self.history_list_frame, fg_color="transparent")
                    item_frame.pack(fill="x", pady=5, padx=5)
                    
                    left_box = ctk.CTkFrame(item_frame, fg_color="transparent")
                    left_box.pack(side="left")
                    ctk.CTkLabel(left_box, text=category, font=("Arial", 14)).pack(anchor="w")
                    ctk.CTkLabel(left_box, text=date, text_color=TEXT_MUTED, font=("Arial", 11)).pack(anchor="w")
                    
                    if note and note.strip():
                        ctk.CTkLabel(left_box, text=f'↳ {note}', text_color=TEXT_MUTED, font=("Arial", 11, "italic")).pack(anchor="w", pady=(2, 0))
                       
                    right_box = ctk.CTkFrame(item_frame, fg_color="transparent")
                    right_box.pack(side="right")
                    
                    color = GREEN if t_type == "In" else ORANGE
                    sign = "+" if t_type == "In" else "-"
                    
                    ctk.CTkLabel(right_box, text=f"{sign}₱{amount:,.2f}", text_color=color, font=("Arial", 14, "bold")).pack(side="left", padx=(0, 10))
                 
                    
                    del_btn = ctk.CTkButton(
                        right_box, 
                        text="✕", 
                        width=28, 
                        fg_color=DARK_GREY, 
                        hover_color=RED,
                        command=lambda current_id=t_id: self.delete_transaction(current_id)
                    )
                    del_btn.pack(side="left")
                    
                    div = ctk.CTkFrame(self.history_list_frame, height=1, fg_color=BG_COLOR)
                    div.pack(fill="x", padx=10, pady=2)
                    
        except sqlite3.OperationalError:
            pass

    def update_kpis(self):
        """Calculates totals from the database and updates the top cards."""
        import sqlite3
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT type, amount FROM transactions")
                rows = cursor.fetchall()

            total_in = sum(row[1] for row in rows if row[0] == "In")
            total_out = sum(row[1] for row in rows if row[0] == "Out")
            balance = total_in - total_out

            if total_in > 0:
                savings_rate = ((total_in - total_out) / total_in) * 100
                savings_text = f"{savings_rate:.1f}%"
            else:
                savings_text = "—"

            self.lbl_income.configure(text=f"₱{total_in:,.2f}")
            self.lbl_expenses.configure(text=f"₱{total_out:,.2f}")
            self.lbl_balance.configure(text=f"₱{balance:,.2f}")
            self.lbl_savings.configure(text=savings_text)

        except sqlite3.OperationalError:
            pass

    def delete_transaction(self, transaction_id):
        """Securely removes a specific transaction by its unique ID and refreshes the UI."""
        import sqlite3
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            conn.commit()
            
        print(f"[*] Transaction {transaction_id} deleted successfully.")
        
        self.refresh_history()
        self.update_kpis()

if __name__ == "__main__":
    app = FinancialTracker()
    app.mainloop()
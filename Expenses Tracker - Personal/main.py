# ------------------ Imports and Theory ------------------
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from datetime import datetime
from tkcalendar import DateEntry  # Calendar picker for date input

# ------------------ Database Setup ------------------
conn = sqlite3.connect("expenses.db")  # Local SQLite DB
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    type TEXT,  -- Income / Expense / Debt
    category TEXT, -- Expense categories: Unwanted/Essential/Middle
    description TEXT,
    amount REAL,
    paid INTEGER DEFAULT 0 -- For Debts: 0=Not Paid, 1=Paid
)
""")
conn.commit()

# ------------------ Functions ------------------

def add_transaction():
    date = date_entry.get()
    t_type = type_var.get()
    category = category_var.get()
    description = desc_entry.get()
    amount = amount_entry.get()

    if not date or not amount:
        messagebox.showerror("Error", "Date and Amount are required!")
        return

    cursor.execute(
        "INSERT INTO transactions (date, type, category, description, amount) VALUES (?, ?, ?, ?, ?)",
        (date, t_type, category, description, float(amount))
    )
    conn.commit()
    load_transactions()
    clear_fields()

def load_transactions():
    for row in tree.get_children():
        tree.delete(row)

    cursor.execute("SELECT * FROM transactions ORDER BY date ASC, id ASC")
    rows = cursor.fetchall()

    running_balance = 0
    total_income = 0
    total_expense = 0
    total_debt = 0

    for row in rows:
        tid, date, t_type, category, description, amount, paid = row

        if t_type == "Income":
            running_balance += amount
            total_income += amount
            tag = "income"
        elif t_type == "Expense":
            running_balance -= amount
            total_expense += amount
            if category == "Unwanted":
                tag = "unwanted"
            elif category == "Essential":
                tag = "essential"
            else:
                tag = "middle"
        elif t_type == "Debt":
            if paid == 0:
                running_balance -= amount
                total_debt += amount
                tag = "debt_unpaid"
            else:
                tag = "debt_paid"

        values = (tid, date, t_type, category, description, amount, running_balance, "Paid" if paid else "Not Paid")
        tree.insert("", tk.END, values=values, tags=(tag,))

    balance_label.config(
        text=f"Balance: {running_balance:.2f} | Income: {total_income:.2f} | Spent: {total_expense:.2f} | Debts: {total_debt:.2f}"
    )

def clear_fields():
    date_entry.set_date(datetime.today())
    desc_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)
    category_var.set("")

def toggle_debt_paid():
    selected = tree.focus()
    if not selected:
        messagebox.showerror("Error", "Select a debt to update!")
        return
    values = tree.item(selected, "values")
    tid = values[0]
    current_status = values[-1]
    new_status = 0 if current_status == "Paid" else 1
    cursor.execute("UPDATE transactions SET paid=? WHERE id=?", (new_status, tid))
    conn.commit()
    load_transactions()

def delete_transaction():
    selected = tree.focus()
    if not selected:
        messagebox.showerror("Error", "Select a transaction to delete!")
        return
    values = tree.item(selected, "values")
    tid = values[0]
    confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this transaction?")
    if confirm:
        cursor.execute("DELETE FROM transactions WHERE id=?", (tid,))
        conn.commit()
        load_transactions()

def show_monthly_summary():
    cursor.execute("SELECT date, type, amount FROM transactions")
    rows = cursor.fetchall()

    monthly_income = {}
    monthly_expense = {}
    monthly_debt = {}

    for date, t_type, amount in rows:
        month = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")
        if t_type == "Income":
            monthly_income[month] = monthly_income.get(month, 0) + amount
        elif t_type == "Expense":
            monthly_expense[month] = monthly_expense.get(month, 0) + amount
        elif t_type == "Debt":
            monthly_debt[month] = monthly_debt.get(month, 0) + amount

    months = sorted(set(list(monthly_income.keys()) + list(monthly_expense.keys()) + list(monthly_debt.keys())))
    income_vals = [monthly_income.get(m, 0) for m in months]
    expense_vals = [monthly_expense.get(m, 0) for m in months]
    debt_vals = [monthly_debt.get(m, 0) for m in months]

    plt.figure(figsize=(10,6))
    plt.plot(months, income_vals, label="Income", color="green", marker='o')
    plt.plot(months, expense_vals, label="Expense", color="blue", marker='o')
    plt.plot(months, debt_vals, label="Debt", color="red", marker='o')
    plt.xlabel("Month")
    plt.ylabel("Amount")
    plt.title("Monthly Summary")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# ------------------ GUI Setup ------------------
root = tk.Tk()
root.title("Handy Wallet")
root.geometry("1150x700")
root.configure(bg="white")

# Change window icon (replace wallet_icon.ico with your icon)
#root.iconbitmap("wallet_icon.ico")

icon = tk.PhotoImage(file="C:\Projects - Personal\Expenses Tracker - Personal\wallet_icon.png")  # Use your PNG file
root.iconphoto(False, icon)


# TTK Styles
style = ttk.Style(root)
style.theme_use("clam")
style.configure("Treeview", background="white", foreground="black", rowheight=25, fieldbackground="white", font=('Arial', 10))
style.configure("Treeview.Heading", font=('Arial', 12,'bold'), background="#1E90FF", foreground="white")

# Input Frame
frame = tk.Frame(root, bg="white", bd=2, relief=tk.RIDGE, padx=10, pady=10)
frame.pack(pady=10, padx=10, fill=tk.X)

tk.Label(frame, text="Date", bg="white", font=("Arial",10)).grid(row=0, column=0, padx=5, pady=5, sticky='w')
date_entry = DateEntry(frame, width=18, background='blue', foreground='white', date_pattern='yyyy-mm-dd')
date_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(frame, text="Type", bg="white", font=("Arial",10)).grid(row=1, column=0, padx=5, pady=5, sticky='w')
type_var = tk.StringVar(value="Expense")
type_menu = ttk.Combobox(frame, textvariable=type_var, values=["Income", "Expense", "Debt"], width=18)
type_menu.grid(row=1, column=1, padx=5, pady=5)

tk.Label(frame, text="Category", bg="white", font=("Arial",10)).grid(row=2, column=0, padx=5, pady=5, sticky='w')
category_var = tk.StringVar()
category_menu = ttk.Combobox(frame, textvariable=category_var, values=["Unwanted", "Essential", "Middle"], width=18)
category_menu.grid(row=2, column=1, padx=5, pady=5)

tk.Label(frame, text="Description", bg="white", font=("Arial",10)).grid(row=3, column=0, padx=5, pady=5, sticky='w')
desc_entry = tk.Entry(frame, width=25)
desc_entry.grid(row=3, column=1, padx=5, pady=5)

tk.Label(frame, text="Amount", bg="white", font=("Arial",10)).grid(row=4, column=0, padx=5, pady=5, sticky='w')
amount_entry = tk.Entry(frame, width=25)
amount_entry.grid(row=4, column=1, padx=5, pady=5)

add_btn = tk.Button(frame, text="Add Transaction", bg="#1E90FF", fg="white", font=('Arial',10,'bold'), command=add_transaction)
add_btn.grid(row=5, column=0, columnspan=2, pady=10, ipadx=20)

# Transactions Treeview
tree_frame = tk.Frame(root, bg="white")
tree_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

tree_scroll = tk.Scrollbar(tree_frame)
tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

tree = ttk.Treeview(tree_frame, columns=("ID", "Date", "Type", "Category", "Description", "Amount", "Balance", "Status"),
                    show="headings", yscrollcommand=tree_scroll.set)
tree_scroll.config(command=tree.yview)

for col in ("ID", "Date", "Type", "Category", "Description", "Amount", "Balance", "Status"):
    tree.heading(col, text=col)
    tree.column(col, width=130, anchor='center')

tree.pack(fill=tk.BOTH, expand=True)

# Color coding
tree.tag_configure("income", foreground="green")
tree.tag_configure("unwanted", foreground="red")
tree.tag_configure("essential", foreground="blue")
tree.tag_configure("middle", foreground="orange")
tree.tag_configure("debt_unpaid", foreground="brown")
tree.tag_configure("debt_paid", foreground="gray")

# Balance label
balance_label = tk.Label(root, text="Balance: 0", bg="white", font=("Arial",12,'bold'))
balance_label.pack(pady=5)

# Buttons frame
btn_frame = tk.Frame(root, bg="white")
btn_frame.pack(pady=10)

toggle_debt_btn = tk.Button(btn_frame, text="Mark Debt Paid/Unpaid", bg="#1E90FF", fg="white", font=('Arial',10,'bold'), command=toggle_debt_paid)
toggle_debt_btn.grid(row=0, column=0, padx=10, ipadx=10)

summary_btn = tk.Button(btn_frame, text="Show Monthly Summary", bg="#1E90FF", fg="white", font=('Arial',10,'bold'), command=show_monthly_summary)
summary_btn.grid(row=0, column=1, padx=10, ipadx=10)

delete_btn = tk.Button(btn_frame, text="Delete Transaction", bg="#FF4500", fg="white", font=('Arial',10,'bold'), command=delete_transaction)
delete_btn.grid(row=0, column=2, padx=10, ipadx=10)

# Load initial data
load_transactions()

# Run the app
root.mainloop()

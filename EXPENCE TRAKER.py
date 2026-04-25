import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta

# Color palette for charts
CHART_COLORS = ['#FF6F61', '#6B5B95', '#88B04B', '#F7CAC9', '#92A8D1', '#955251', '#B565A7']

class ExpenseList:
    def __init__(self):
        self.expenses = []

    def add_expense(self, date, category, amount):
        self.expenses.append({'date': date, 'category': category, 'amount': amount})

    # Daily expenses
    def get_daily_expenses(self):
        dates = sorted(set(expense['date'] for expense in self.expenses))
        daily_data = []
        for date in dates:
            expenses_on_date = [expense for expense in self.expenses if expense['date'] == date]
            daily_data.append((date, expenses_on_date))
        return daily_data

    # Weekly expenses
    def get_weekly_expenses(self):
        if not self.expenses:
            return []
        dates = sorted(set(expense['date'] for expense in self.expenses))
        start_date = min(dates)
        end_date = max(dates)
        weekly_data = []

        while start_date <= end_date:
            week_end = start_date + timedelta(days=6)
            weekly_totals = {}
            for expense in self.expenses:
                if start_date <= expense['date'] <= week_end:
                    weekly_totals[expense['category']] = weekly_totals.get(expense['category'], 0) + expense['amount']
            if weekly_totals:
                weekly_data.append((start_date, week_end, weekly_totals))
            start_date += timedelta(days=7)
        return weekly_data

    # Monthly expenses
    def get_monthly_expenses(self):
        if not self.expenses:
            return []
        months = sorted(set(expense['date'].replace(day=1) for expense in self.expenses))
        monthly_data = []

        for month in months:
            month_totals = {}
            for expense in self.expenses:
                if expense['date'].year == month.year and expense['date'].month == month.month:
                    month_totals[expense['category']] = month_totals.get(expense['category'], 0) + expense['amount']
            if month_totals:
                monthly_data.append((month, month_totals))
        return monthly_data

    # Pie chart totals
    def get_category_totals(self):
        categories = set(expense['category'] for expense in self.expenses)
        category_amount = {category: sum(expense['amount'] for expense in self.expenses if expense['category'] == category) for category in categories}
        return category_amount

class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("💰 Expense Tracker 💰")
        self.root.geometry("900x650")
        self.root.configure(bg='#FFF8DC')
        self.expense_list = ExpenseList()

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook.Tab', font=('Helvetica', 12, 'bold'), padding=[10, 5])

        # Tabs
        self.tab_control = ttk.Notebook(root)
        self.add_tab = tk.Frame(self.tab_control, bg='#FFE4B5')
        self.visual_tab = tk.Frame(self.tab_control, bg='#E0FFFF')
        self.tab_control.add(self.add_tab, text="Add Expense")
        self.tab_control.add(self.visual_tab, text="Visualize")
        self.tab_control.pack(expand=1, fill="both")

        self.create_add_tab()
        self.create_visual_tab()

    def create_add_tab(self):
        tk.Label(self.add_tab, text="Date:", font=("Helvetica", 12, 'bold'), bg='#FFE4B5').grid(row=0, column=0, padx=10, pady=10, sticky='w')
        tk.Label(self.add_tab, text="Category:", font=("Helvetica", 12, 'bold'), bg='#FFE4B5').grid(row=1, column=0, padx=10, pady=10, sticky='w')
        tk.Label(self.add_tab, text="Amount:", font=("Helvetica", 12, 'bold'), bg='#FFE4B5').grid(row=2, column=0, padx=10, pady=10, sticky='w')

        self.date_entry = DateEntry(self.add_tab, width=15, background='blue', foreground='white', borderwidth=2)
        self.date_entry.grid(row=0, column=1, padx=10, pady=10)

        self.category_entry = tk.Entry(self.add_tab, width=20)
        self.category_entry.grid(row=1, column=1, padx=10, pady=10)

        self.amount_entry = tk.Entry(self.add_tab, width=20)
        self.amount_entry.grid(row=2, column=1, padx=10, pady=10)

        add_btn = tk.Button(self.add_tab, text="Add Expense", command=self.add_expense,
                            bg='#FF6F61', fg='white', font=('Helvetica', 12, 'bold'), activebackground='#FF8A80', activeforeground='white')
        add_btn.grid(row=3, column=0, columnspan=2, pady=20)

    def create_visual_tab(self):
        tk.Label(self.visual_tab, text="Select Visualization:", font=("Helvetica", 12, 'bold'), bg='#E0FFFF').pack(pady=10)
        self.visual_option = ttk.Combobox(self.visual_tab, values=["Daily", "Weekly", "Monthly", "Pie Chart"])
        self.visual_option.current(0)
        self.visual_option.pack(pady=10)

        show_btn = tk.Button(self.visual_tab, text="Show", command=self.show_visualization,
                             bg='#6B5B95', fg='white', font=('Helvetica', 12, 'bold'), activebackground='#957DAD', activeforeground='white')
        show_btn.pack(pady=10)

        self.canvas_frame = tk.Frame(self.visual_tab, bg='#E0FFFF')
        self.canvas_frame.pack(fill="both", expand=True)

    def add_expense(self):
        date = self.date_entry.get_date()
        category = self.category_entry.get()
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Amount must be a number.")
            return

        if not any(c.isalpha() for c in category):
            messagebox.showerror("Error", "Category must contain letters.")
            return

        self.expense_list.add_expense(date, category, amount)
        messagebox.showinfo("Success", "Expense added successfully!")
        self.category_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)

    def show_visualization(self):
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        choice = self.visual_option.get()

        if choice == "Daily":
            data = self.expense_list.get_daily_expenses()
            title = "Daily Expenses"
            x_label = "Categories"
            self.plot_bar_chart(data, title, x_label)

        elif choice == "Weekly":
            data = self.expense_list.get_weekly_expenses()
            if not data:
                messagebox.showwarning("No Data", "No weekly data available.")
                return
            fig, ax = plt.subplots(figsize=(8,5))
            color_index = 0
            for start, end, totals in data:
                categories = list(totals.keys())
                amounts = list(totals.values())
                ax.bar(categories, amounts, label=f"{start} to {end}", color=CHART_COLORS[color_index % len(CHART_COLORS)])
                color_index += 1
            ax.set_title("Weekly Expenses")
            ax.set_xlabel("Categories")
            ax.set_ylabel("Amount")
            ax.legend()
            ax.tick_params(axis='x', rotation=45)
            canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        elif choice == "Monthly":
            data = self.expense_list.get_monthly_expenses()
            if not data:
                messagebox.showwarning("No Data", "No monthly data available.")
                return
            fig, ax = plt.subplots(figsize=(8,5))
            color_index = 0
            for month, totals in data:
                categories = list(totals.keys())
                amounts = list(totals.values())
                ax.bar(categories, amounts, label=month.strftime("%B %Y"), color=CHART_COLORS[color_index % len(CHART_COLORS)])
                color_index += 1
            ax.set_title("Monthly Expenses")
            ax.set_xlabel("Categories")
            ax.set_ylabel("Amount")
            ax.legend()
            ax.tick_params(axis='x', rotation=45)
            canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        elif choice == "Pie Chart":
            totals = self.expense_list.get_category_totals()
            if not totals:
                messagebox.showwarning("No Data", "No data available.")
                return
            fig, ax = plt.subplots(figsize=(6,6))
            ax.pie(totals.values(), labels=totals.keys(), autopct='%1.1f%%', startangle=140, colors=CHART_COLORS)
            ax.set_title("Expenses by Category")
            canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

    def plot_bar_chart(self, data, title, x_label):
        if not data:
            messagebox.showwarning("No Data", "No expenses to visualize.")
            return
        fig, ax = plt.subplots(figsize=(8,5))
        color_index = 0
        for label, expenses_on_label in data:
            categories = [e['category'] for e in expenses_on_label]
            amounts = [e['amount'] for e in expenses_on_label]
            ax.bar(categories, amounts, label=str(label), color=CHART_COLORS[color_index % len(CHART_COLORS)])
            color_index += 1
        ax.set_title(title)
        ax.set_xlabel(x_label)
        ax.set_ylabel("Amount")
        ax.legend()
        ax.tick_params(axis='x', rotation=45)
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()

import sys
import importlib
import streamlit
importlib.reload(streamlit)
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, timedelta
import io
import base64
import sqlite3
import hashlib


# Set page title
st.set_page_config(page_title="🏠 Household Budget App")

def display_sidebar():
    col1, col2 = st.sidebar.columns(2)
    if st.session_state.get('logged_in', False):
        st.sidebar.write(f"Welcome, {st.session_state.username}!")
        if st.sidebar.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.show_login_form = False
            st.session_state.show_signup_form = False
            st.success("You have been logged out successfully.")
            st.experimental_rerun()
    else:
        with col1:
            if st.button("🔑 Login"):
                st.session_state.show_login_form = True
                st.session_state.show_signup_form = False
        with col2:
            if st.button("📝 Sign Up"):
                st.session_state.show_signup_form = True
                st.session_state.show_login_form = False



    if st.session_state.get('show_login_form', False):
        show_login_form()

    if st.session_state.get('show_signup_form', False):
        show_signup_form()

    st.sidebar.markdown("# ⚙️ Settings")

DB_FILE = 'users.db'
SETTINGS_CSV = "app_settings.csv"
CURRENCIES_BEFORE = {'$', '€', '£', '¥', '₹', 'A$', 'C$', 'S$', 'CHF'}


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, email, password):
    hashed_password = hash_password(password)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                  (username, email, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # This will catch duplicate username or email
        return False
    finally:
        conn.close()

def show_signup_form():
    with st.sidebar.form("signup_form"):
        st.write("## 📝 Sign Up")
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit_button = st.form_submit_button("Create Account")
        
        if submit_button:
            if not username or not email or not password:
                st.error("Please fill in all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                if add_user(username, email, password):
                    st.success(f"Account created for {username}!")
                    st.session_state.signed_up = True
                    st.experimental_rerun()
                else:
                    st.error("Username or email already exists.")


def show_login_form():
    with st.sidebar.form("login_form"):
        st.write("## 🔑 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Log In")
        
        if submit_button:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                if verify_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.show_login_form = False
                    st.success(f"Logged in as {username}!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password.")



def verify_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    hashed_password = hash_password(password)
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
    user = c.fetchone()
    conn.close()
    return user is not None

def load_settings():
    if os.path.exists(SETTINGS_CSV):
        settings = pd.read_csv(SETTINGS_CSV, index_col=0).to_dict()['value']
        return settings
    return {'currency': '$'}  # Default settings

def save_settings(settings):
    pd.DataFrame({'value': settings}, index=settings.keys()).to_csv(SETTINGS_CSV)

# Initialize settings in session state
if 'settings' not in st.session_state:
    st.session_state.settings = load_settings()

def format_currency(amount):
    currency = st.session_state.settings['currency']
    formatted_amount = f"{amount:.2f}"
    
    if currency in CURRENCIES_BEFORE:
        return f"{currency}{formatted_amount}"
    else:
        return f"{formatted_amount} {currency}"

def add_new_item():
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("➕ Add New Item")
        product = st.text_input("Product")
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        date = st.date_input("Date", value=datetime.now().date(), key="new_item_date_input")

        # Category selection for custom products
        category = get_category(product)
        if product and not category:
            category = st.selectbox("Category", options=list(st.session_state.product_categories.keys()) + ["Other"])

        add_item = st.button("Add Item")

        if add_item and product:
            if not category:
                category = "Other"
            new_item = {"Product": product, "Amount": amount, "Category": category, "Date": date}
            st.session_state.budget_items.append(new_item)
            df = pd.DataFrame(st.session_state.budget_items)
            save_budget_data(df)
        
        # Add new product to category if it's not already there
        if category != "Other":
            if category not in st.session_state.product_categories:
                st.session_state.product_categories[category] = []
            if product.lower() not in st.session_state.product_categories[category]:
                st.session_state.product_categories[category].append(product.lower())
                save_product_categories(st.session_state.product_categories)
        
        st.success(f"Item added successfully! Category: {category}")
        # Reset the product input
        product = ""

    with col2:
        display_budget_items()

def load_budget_data():
    if os.path.exists(BUDGET_CSV):
        df = pd.read_csv(BUDGET_CSV)
        if 'Date' not in df.columns:
            df['Date'] = datetime.now().date()  # Add a default date if missing
        else:
            df['Date'] = pd.to_datetime(df['Date'], format='mixed').dt.date  # Convert to date only, flexible format
        return df
    return pd.DataFrame(columns=["Product", "Amount", "Category", "Date"])

def load_product_categories():
    if os.path.exists(CATEGORIES_CSV):
        df = pd.read_csv(CATEGORIES_CSV)
        categories = {}
        for _, row in df.iterrows():
            category = row['Category']
            products = row['Products'].split(',') if pd.notna(row['Products']) else []
            categories[category] = products
        return categories
    return {}  # Return an empty dictionary if the file doesn't exist

def save_budget_data(df):
    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')  # Convert to string in YYYY-MM-DD format
    df.to_csv(BUDGET_CSV, index=False)

def save_product_categories(product_categories):
    df = pd.DataFrame([(category, ','.join(products)) for category, products in product_categories.items()],
                      columns=['Category', 'Products'])
    df.to_csv(CATEGORIES_CSV, index=False)

def get_category(product):
    product = product.lower()
    for category, items in st.session_state.product_categories.items():
        if product in items:
            return category
    return None

def load_monthly_budget():
    if os.path.exists(MONTHLY_BUDGET_CSV):
        df = pd.read_csv(MONTHLY_BUDGET_CSV)
        return df['Monthly Budget'].iloc[0] if not df.empty else 0.0
    return 0.0

def save_monthly_budget(monthly_budget):
    pd.DataFrame({'Monthly Budget': [monthly_budget]}).to_csv(MONTHLY_BUDGET_CSV, index=False)

def load_recurring_expenses():
    if os.path.exists(RECURRING_EXPENSES_CSV):
        return pd.read_csv(RECURRING_EXPENSES_CSV).to_dict('records')
    return []

def save_recurring_expenses(recurring_expenses):
    pd.DataFrame(recurring_expenses).to_csv(RECURRING_EXPENSES_CSV, index=False)

def load_savings_goal():
    if os.path.exists(SAVINGS_GOAL_CSV):
        df = pd.read_csv(SAVINGS_GOAL_CSV)
        if not df.empty:
            return {"amount": df['Amount'].iloc[0], "date": pd.to_datetime(df['Date'].iloc[0]).date()}
    return None

def save_savings_goal(goal):
    pd.DataFrame({'Amount': [goal['amount']], 'Date': [goal['date']]}).to_csv(SAVINGS_GOAL_CSV, index=False)

def load_spending_restrictions():
    if os.path.exists(SPENDING_RESTRICTIONS_CSV):
        df = pd.read_csv(SPENDING_RESTRICTIONS_CSV)
        return {row['Product']: {'limit': row['Limit'], 'period': row['Period']} for _, row in df.iterrows()}
    return {}

def save_spending_restrictions(restrictions):
    df = pd.DataFrame([
        {'Product': product, 'Limit': data['limit'], 'Period': data['period']}
        for product, data in restrictions.items()
    ])
    df.to_csv(SPENDING_RESTRICTIONS_CSV, index=False)

def set_monthly_budget():
    st.sidebar.markdown("---")
    st.sidebar.subheader("💰 Set Monthly Budget")
    monthly_budget = st.sidebar.number_input("Monthly Budget", min_value=0.0, step=10.0, value=st.session_state.monthly_budget)
    if st.sidebar.button("Save Budget"):
        st.session_state.monthly_budget = monthly_budget
        save_monthly_budget(monthly_budget)
        st.sidebar.success("Monthly budget saved!")
    st.sidebar.markdown("---")  # Horizontal rule

def manage_categories():
    st.sidebar.subheader("📊 Manage Categories")
    new_category = st.sidebar.text_input("New Category Name")
    new_emoji = st.sidebar.text_input("Category Emoji")
    if st.sidebar.button("Add Category"):
        if new_category and new_emoji:
            full_category_name = f"{new_emoji} {new_category}"
            st.session_state.product_categories[full_category_name] = []
            save_product_categories(st.session_state.product_categories)
            st.sidebar.success(f"Category {full_category_name} added!")
    st.sidebar.markdown("---")  # Horizontal rule

def export_data():
    df = pd.DataFrame(st.session_state.budget_items)
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="budget_data.csv">Download CSV File</a>'
    st.sidebar.markdown(href, unsafe_allow_html=True)

def add_recurring_expense():
    st.sidebar.subheader("🔄 Add Recurring Expense")
    rec_product = st.sidebar.text_input("Recurring Product")
    rec_amount = st.sidebar.number_input("Recurring Amount", min_value=0.0, step=0.01)
    rec_category = st.sidebar.selectbox("Recurring Category", options=list(st.session_state.product_categories.keys()))
    rec_frequency = st.sidebar.selectbox("Frequency", options=["Daily", "Weekly", "Monthly"])
    if st.sidebar.button("Add Recurring Expense"):
        if rec_product and rec_amount and rec_category:
            new_expense = {
                "Product": rec_product,
                "Amount": rec_amount,
                "Category": rec_category,
                "Frequency": rec_frequency
            }
            st.session_state.recurring_expenses.append(new_expense)
            save_recurring_expenses(st.session_state.recurring_expenses)
            st.sidebar.success("Recurring expense added!")
    st.sidebar.markdown("---")  # Horizontal rule

def set_savings_goal():
    st.sidebar.subheader("🎯 Set Savings Goal")
    goal_amount = st.sidebar.number_input("Savings Goal Amount", min_value=0.0, step=100.0, value=st.session_state.savings_goal['amount'] if st.session_state.savings_goal else 0.0)
    goal_date = st.sidebar.date_input("Target Date", value=st.session_state.savings_goal['date'] if st.session_state.savings_goal else datetime.now().date())
    if st.sidebar.button("Set Goal"):
        if goal_amount > 0:
            st.session_state.savings_goal = {"amount": goal_amount, "date": goal_date}
            save_savings_goal(st.session_state.savings_goal)
            st.sidebar.success("Savings goal set!")
        else:
            st.sidebar.error("Please enter a savings goal amount greater than zero.")
    st.sidebar.markdown("---")  # Horizontal rule

def add_to_savings():
    st.subheader("Add to Savings")
    
    col1, col2= st.columns(2)

    with col1:
        savings_amount = st.number_input("Amount to add to savings", min_value=0.0, step=0.01, key="savings_amount_input")

    with col2:
        savings_date = st.date_input("Date", value=datetime.now().date(), key="savings_date_input")


    add_savings_button = st.button("Add to Savings", key="add_savings_button")

    if add_savings_button:
        if savings_amount > 0:
            new_savings = {
                "Product": "Savings", 
                "Amount": savings_amount, 
                "Category": "Savings", 
                "Date": pd.to_datetime(savings_date)  # Convert to pandas datetime
            }
            st.session_state.budget_items.append(new_savings)
            df = pd.DataFrame(st.session_state.budget_items)
            save_budget_data(df)
            
            # Update the savings goal progress
            if 'savings_goal' in st.session_state and st.session_state.savings_goal is not None:
                total_savings = df[df['Product'] == 'Savings']['Amount'].sum()
                goal = st.session_state.savings_goal
                if total_savings >= goal['amount']:
                    st.success(f"{format_currency(savings_amount)} added to savings! Congratulations! You've reached your savings goal!")
                else:
                    remaining = goal['amount'] - total_savings
                    st.success(f"{format_currency(savings_amount)} added to savings! {format_currency(remaining)} left to reach your goal.")
            else:
                st.success(f"{format_currency(savings_amount)} added to savings!")
            
            # Force a rerun to update the display
            st.experimental_rerun()
        else:
            st.warning("Please enter an amount greater than zero.")

def process_recurring_expenses():
    today = datetime.now().date()
    if 'last_recurring_check' not in st.session_state:
        st.session_state.last_recurring_check = today - timedelta(days=1)
    
    if today > st.session_state.last_recurring_check:
        for expense in st.session_state.recurring_expenses:
            if expense['Frequency'] == 'Daily':
                days_to_add = (today - st.session_state.last_recurring_check).days
            elif expense['Frequency'] == 'Weekly':
                days_to_add = (today - st.session_state.last_recurring_check).days // 7
            elif expense['Frequency'] == 'Monthly':
                months = (today.year - st.session_state.last_recurring_check.year) * 12 + today.month - st.session_state.last_recurring_check.month
                days_to_add = months
            else:
                continue  # Skip if frequency is not recognized
            
            for _ in range(days_to_add):
                new_item = {
                    "Product": expense['Product'],
                    "Amount": expense['Amount'],
                    "Category": expense['Category'],
                    "Date": today
                }
                st.session_state.budget_items.append(new_item)
        
        # Save the updated budget items
        df = pd.DataFrame(st.session_state.budget_items)
        save_budget_data(df)
        
        # Update the last check date
        st.session_state.last_recurring_check = today

def display_savings_goal_progress():
    st.markdown("---")  # Add a separator
    st.title("🐷Savings")
    if 'savings_goal' in st.session_state and st.session_state.savings_goal is not None:
        st.subheader("Savings Goal Progress")
        goal = st.session_state.savings_goal
        df = pd.DataFrame(st.session_state.budget_items)
        total_savings = df[df['Product'] == 'Savings']['Amount'].sum()
        
        if goal['amount'] > 0:
            progress = min((total_savings / goal['amount']), 1.0)  # Ensure progress is between 0 and 1
            st.progress(progress)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"Saved: {format_currency(total_savings)} / {format_currency(goal['amount'])}")
            with col2:
                st.write(f"Target Date: {st.session_state.savings_goal['date']}")
            with col3:
                days_left = (goal['date'] - datetime.now().date()).days
                st.write(f"Days left to reach goal: {days_left}")
            
            if total_savings >= goal['amount']:
                st.success("Congratulations! You've reached your savings goal!")
            elif days_left > 0:
                daily_savings_needed = (goal['amount'] - total_savings) / days_left
                st.info(f"To reach your goal, you need to save {format_currency(daily_savings_needed)} per day.")
        else:
            st.write("Savings goal amount is not set or is zero.")
    else:
        st.info("No savings goal set. Use the sidebar to set a goal.")

def manage_spending_restrictions():
    st.sidebar.subheader("🚫 Manage Spending Restrictions")
    product = st.sidebar.selectbox("Select Product", options=[""] + list(set([item['Product'] for item in st.session_state.budget_items])))
    if product:
        existing_restriction = st.session_state.spending_restrictions.get(product, {})
        limit = st.sidebar.number_input(f"Set limit for {product}", 
                                        min_value=0.0, 
                                        step=1.0, 
                                        value=existing_restriction.get('limit', 0.0))
        period = st.sidebar.selectbox("Limit Period", 
                                      options=["Daily", "Weekly", "Monthly"], 
                                      index=["Daily", "Weekly", "Monthly"].index(existing_restriction.get('period', 'Monthly')))
        if st.sidebar.button("Set Restriction"):
            st.session_state.spending_restrictions[product] = {"limit": limit, "period": period}
            save_spending_restrictions(st.session_state.spending_restrictions)
            st.sidebar.success(f"Restriction set for {product}: {format_currency(limit)} {period.lower()}")

    if st.sidebar.button("Clear All Restrictions"):
        st.session_state.spending_restrictions.clear()
        save_spending_restrictions(st.session_state.spending_restrictions)
        st.sidebar.success("All spending restrictions cleared.")
    st.sidebar.markdown("---")  # Horizontal rule

def display_budget_items():
    st.subheader("📜 Budget Items History")

    if st.session_state.budget_items:
        df = pd.DataFrame(st.session_state.budget_items)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        df.index = range(1, len(df) + 1)

        
        def color_savings(val):
            color = 'green' if val == 'Savings' else ''
            return f'color: {color}'
        
        def color_amount(val, row):
            if row['Product'] == 'Savings':
                return 'color: green'
            elif row['Product'] in st.session_state.spending_restrictions:
                restriction = st.session_state.spending_restrictions[row['Product']]
                if restriction['period'] == 'Daily':
                    total_spent = df[(df['Product'] == row['Product']) & (df['Date'] == row['Date'])]['Amount'].sum()
                elif restriction['period'] == 'Weekly':
                    week_start = row['Date'] - pd.Timedelta(days=row['Date'].dayofweek)
                    total_spent = df[(df['Product'] == row['Product']) & (df['Date'] >= week_start) & (df['Date'] <= row['Date'])]['Amount'].sum()
                else:  # Monthly
                    month_start = row['Date'].replace(day=1)
                    total_spent = df[(df['Product'] == row['Product']) & (df['Date'] >= month_start) & (df['Date'] <= row['Date'])]['Amount'].sum()
                
                if total_spent > restriction['limit']:
                    return 'color: red'
            return ''
        
        st.dataframe(
            df.style
            .format({
                "Amount": lambda x: format_currency(x),
                "Date": lambda x: x.strftime("%Y-%m-%d")
            })
            .applymap(color_savings, subset=['Product'])
            .apply(lambda row: [color_amount(val, row) for val in row], axis=1)
        )
        
        # Calculate and display total
        total = df["Amount"].sum()
        st.markdown(f"***Sum of spendings: {format_currency(total)}***")
    else:
        st.info("No budget items added yet.")

def display_budget_vs_actual():
    if 'monthly_budget' in st.session_state:
        st.subheader("Budget vs. Actual Spending")
        current_month = datetime.now().replace(day=1).date()
        df = pd.DataFrame(st.session_state.budget_items)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Convert current_month to datetime64[ns] for comparison
        current_month = pd.to_datetime(current_month)
        
        monthly_spending = df[df['Date'] >= current_month]['Amount'].sum()
        remaining_budget = st.session_state.monthly_budget - monthly_spending
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Monthly Budget", format_currency(st.session_state.monthly_budget))
        col2.metric("Spent", format_currency(monthly_spending))
        col3.metric("Remaining", format_currency(remaining_budget))
        
        # Create a progress bar to show budget remaining
        progress = remaining_budget / st.session_state.monthly_budget
        col4.text(f"Budget Remaing")
        col4.progress(progress, text=f"{progress:.1%}")
    st.markdown('---')
        

def display_pie_chart():
    if st.session_state.budget_items:
        df = pd.DataFrame(st.session_state.budget_items)
        category_totals = df.groupby('Category')['Amount'].sum().reset_index()
        total_spending = category_totals['Amount'].sum()
        category_totals['Percentage'] = category_totals['Amount'] / total_spending * 100

        # Function to format labels
        def format_label(category, percentage):
            emoji = category.split()[0] if ' ' in category else '📊'  # Default emoji if not found
            if percentage >= 5:
                return f"{emoji} {category}: {percentage:.1f}%"
            else:
                return f"{percentage:.1f}%"

        category_totals['Label'] = category_totals.apply(lambda row: format_label(row['Category'], row['Percentage']), axis=1)

        fig = px.pie(category_totals, 
                     values='Amount', 
                     names='Category', 
                     title='Spending by Category',
                     labels='Label',
                     hole=0.3)  # Adding a hole to make it a donut chart for better readability

        fig.update_traces(textposition='inside', textinfo='label')
        fig.update_layout(showlegend=False)  # Hide legend as information is now in the chart

        st.plotly_chart(fig)

def display_spending_chart():
    if st.session_state.budget_items:
        df = pd.DataFrame(st.session_state.budget_items)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        df['Cumulative Sum'] = df['Amount'].cumsum()
        fig = px.line(df, x='Date', y='Cumulative Sum', title='Cumulative Spending Over Time')
        st.plotly_chart(fig)

def display_spending_restrictions():
    st.markdown("##### 🚫 Current Spending Restrictions")
    
    if st.session_state.spending_restrictions:
        # Create a DataFrame from the spending restrictions
        restrictions_df = pd.DataFrame.from_dict(
            st.session_state.spending_restrictions, 
            orient='index', 
            columns=['limit', 'period']
        ).reset_index()
        restrictions_df.columns = ['Product', 'Limit', 'Period']
        
        # Format the limit as currency
        restrictions_df['Limit'] = restrictions_df['Limit'].apply(lambda x: format_currency(x))
        
        # Display the DataFrame
        st.dataframe(
            restrictions_df,
            column_config={
                "Product": st.column_config.TextColumn("Product"),
                "Limit": st.column_config.TextColumn("Limit"),
                "Period": st.column_config.TextColumn("Period"),
            },
            hide_index=True,
        )
    else:
        st.info("No spending restrictions set. Use the sidebar to add restrictions.")

def set_currency():
    st.sidebar.subheader("💱 Set Currency")
    currencies = ['$', '€', '£', '¥', '₹', 'A$', 'C$', 'S$', 'CHF', 'zł', 'kr', 'R$', '₽', '₱', '₺', 'Kč', 'Ft', '₪', 'د.إ', '₩', '₫']
    current_currency = st.session_state.settings.get('currency', '$')
    selected_currency = st.sidebar.selectbox("Select Currency", currencies, index=currencies.index(current_currency))
    
    if selected_currency != current_currency:
        st.session_state.settings['currency'] = selected_currency
        save_settings(st.session_state.settings)
        st.sidebar.success(f"Currency updated to {selected_currency}")


# Sidebar
display_sidebar()

# Main script execution

st.title("🏠 Household Budget Tracker")

# File paths for CSV
BUDGET_CSV = "budget_data.csv"
CATEGORIES_CSV = "product_categories.csv"
MONTHLY_BUDGET_CSV = "monthly_budget.csv"
RECURRING_EXPENSES_CSV = "recurring_expenses.csv"
SAVINGS_GOAL_CSV = "savings_goal.csv"
SPENDING_RESTRICTIONS_CSV = "spending_restrictions.csv"

# Initialize session state
if 'budget_items' not in st.session_state:
    st.session_state.budget_items = load_budget_data().to_dict('records')
if 'product_categories' not in st.session_state:
    st.session_state.product_categories = load_product_categories()
if 'monthly_budget' not in st.session_state:
    st.session_state.monthly_budget = load_monthly_budget()
if 'recurring_expenses' not in st.session_state:
    st.session_state.recurring_expenses = load_recurring_expenses()
if 'savings_goal' not in st.session_state:
    st.session_state.savings_goal = load_savings_goal() or {"amount": 0, "date": datetime.now().date()}
if 'spending_restrictions' not in st.session_state:
    st.session_state.spending_restrictions = load_spending_restrictions()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'show_login_form' not in st.session_state:
    st.session_state.show_login_form = False
if 'show_signup_form' not in st.session_state:
    st.session_state.show_signup_form = False

# Flatten the product list for autocomplete
all_products = [item for sublist in st.session_state.product_categories.values() for item in sublist]

# Call the functions
set_monthly_budget()
manage_categories()
add_recurring_expense()
set_savings_goal()
manage_spending_restrictions()
set_currency()

display_budget_vs_actual()
add_new_item()

process_recurring_expenses()

st.markdown("---")
st.title("💸 Spendings")
col1, col2 = st.columns(2)
with col1:
    display_pie_chart()
with col2:
    display_spending_chart()

st.markdown("---")
st.title("💼 Budget Management")
col1, col2 = st.columns(2)

with col1:
    if 'recurring_expenses' in st.session_state:
        st.markdown("##### 🔄 Recurring Expenses")
        rec_df = pd.DataFrame(st.session_state.recurring_expenses)
        
        # Format the 'Amount' column with currency
        rec_df['Amount'] = rec_df['Amount'].apply(format_currency)
        
        # Display DataFrame without index
        st.dataframe(
            rec_df,
            column_config={
                "Product": st.column_config.TextColumn("Product"),
                "Amount": st.column_config.TextColumn("Amount"),
                "Category": st.column_config.TextColumn("Category"),
                "Frequency": st.column_config.TextColumn("Frequency"),
            },
            hide_index=True,
        )

with col2:
    display_spending_restrictions()


display_savings_goal_progress()
add_to_savings()

# Add an option to export data
st.sidebar.subheader("📊 Data Export")
if st.sidebar.button("Create Data Export"):
    export_data()


def main():
    if not os.path.exists(DB_FILE):
        init_db()
    
    st.title("🏠 Household Budget Tracker")
    display_sidebar()

    if st.session_state.get('logged_in', False):
        st.write(f"Welcome to your budget tracker, {st.session_state.username}!")
    else:
        st.write("Please log in or sign up to use the budget tracker.")


if __name__ == "__main__":
    main()




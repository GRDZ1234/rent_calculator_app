import pandas as pd
import streamlit as st

# Title of the page
st.title("Mortgage Calculator")

# Load Data from Excel File
file_path = r"C:\Users\Admin\OneDrive\allRentalData.xlsx"
data = pd.read_excel(file_path)

# Clean up data (drop rows with missing values for critical columns)
data = data.dropna(subset=["General Area", "Neighbourhood", "Bedrooms", "Bathrooms", "Monthly Rent"])

# Dropdown to select General Area or Neighborhood
filter_type = st.selectbox("Filter by:", ["General Area", "Neighborhood"])
if filter_type == "General Area":
    selected_general_area = st.selectbox("Select General Area", options=sorted(data["General Area"].dropna().unique()))
    filtered_data = data[data["General Area"] == selected_general_area]
else:
    selected_neighbourhood = st.selectbox("Select Neighborhood", options=sorted(data["Neighbourhood"].dropna().unique()))
    filtered_data = data[data["Neighbourhood"] == selected_neighbourhood]

# Input for number of units
units = st.number_input("Number of Units", min_value=1, step=1)

# Checkbox to enable filtering by Bathrooms
filter_bathrooms = st.checkbox("Filter by Bathrooms", value=False)

# Collect bedroom and bathroom inputs for each unit
st.write("## Enter Unit Details")
bedroom_cols = st.columns(3)
bathroom_cols = st.columns(3) if filter_bathrooms else None
unit_details = []

for i in range(units):
    with bedroom_cols[i % 3]:
        bedrooms = st.number_input(f"Unit {i + 1}: Bedrooms", min_value=1, step=1, key=f"bedrooms_{i}")
    if filter_bathrooms:
        with bathroom_cols[i % 3]:
            bathrooms = st.number_input(f"Unit {i + 1}: Bathrooms", min_value=1, step=1, key=f"bathrooms_{i}")
            unit_details.append((bedrooms, bathrooms))
    else:
        unit_details.append((bedrooms, None))

# Display grouped statistics for each unit
filtered_rent_data = []
for bedrooms, bathrooms in unit_details:
    if bathrooms is not None:
        unit_data = filtered_data[(filtered_data["Bedrooms"] == bedrooms) & (filtered_data["Bathrooms"] == bathrooms)]
    else:
        unit_data = filtered_data[(filtered_data["Bedrooms"] == bedrooms)]
    filtered_rent_data.append(unit_data)

st.write("## Unit Statistics")
for idx in range(0, len(filtered_rent_data), 3):
    unit_columns = st.columns(3)
    for col, unit_data in zip(unit_columns, filtered_rent_data[idx:idx + 3]):
        col.write(f"### Statistics for Unit {idx + 1}")
        if not unit_data.empty:
            grouped_stats = unit_data.agg(
                AverageRent=("Monthly Rent", "mean"),
                MedianRent=("Monthly Rent", "median"),
                Count=("Monthly Rent", "count")
            )
            col.write(grouped_stats)
        else:
            col.write("No data available.")

# Add Expense Logic with Checkbox
show_expenses = st.checkbox("Add Expense Inputs", value=False)

monthly_expense = 0
if show_expenses:
    st.write("## Expense Inputs")
    expense_col1, expense_col2, expense_col3 = st.columns(3)
    with expense_col1:
        maintenance = st.number_input("Annual Maintenance ($)", min_value=0, step=100)
    with expense_col2:
        insurance = st.number_input("Annual Insurance ($)", min_value=0, step=100)
    with expense_col3:
        taxes = st.number_input("Annual Taxes ($)", min_value=0, step=100)
    with expense_col1:
        hoa_fees = st.number_input("Annual HOA Fees ($)", min_value=0, step=100)
    with expense_col2:
        other_expenses = st.number_input("Annual Other Expenses ($)", min_value=0, step=100)

    total_annual_expenses = maintenance + insurance + taxes + hoa_fees + other_expenses
    monthly_expense = total_annual_expenses / 12
    st.write(f"Total Monthly Expense: ${monthly_expense:.2f}")

# Mortgage Calculation Logic
st.write("## Mortgage Calculation")
interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, step=0.1)
loan_terms = [20, 25, 30]
down_payments = [20, 25, 30, 35, 40, 45, 50]

total_average_rent = sum([unit_data["Monthly Rent"].mean() for unit_data in filtered_rent_data if not unit_data.empty])

st.write(f"### Total Average Rent for All Units: ${total_average_rent:,.2f} per month")
adjusted_monthly_income = total_average_rent - monthly_expense if show_expenses else total_average_rent

term_columns = st.columns(len(loan_terms))
for idx, term in enumerate(loan_terms):
    with term_columns[idx]:
        st.write(f"#### {term}-Year Mortgage")
        term_months = term * 12
        monthly_interest_rate = (interest_rate / 100) / 12

        for dp in down_payments:
            max_loan = adjusted_monthly_income * (1 - (1 + monthly_interest_rate) ** -term_months) / monthly_interest_rate
            total_mortgage_value = max_loan / (1 - dp / 100)
            required_down_payment = total_mortgage_value * (dp / 100)
            st.write(f"**{dp}% Down Payment**")
            st.write(f"Total Mortgage Value: ${total_mortgage_value:,.2f}")
            st.write(f"Required Down Payment: ${required_down_payment:,.2f}")
            st.write(f"Monthly Mortgage Payment: ${adjusted_monthly_income:,.2f}")
            st.write("---")

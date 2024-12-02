import pandas as pd
import streamlit as st

st.title("Mortgage Calculator")

# File Path or Direct Link to Google Sheets
file_path = "https://docs.google.com/uc?id=1dx5slnckpqhmPgyH8rSpXF9yHEiYJV0X&export=download"

# Load Data
data = pd.read_excel(file_path, engine="openpyxl")
data = data.dropna(subset=["General Area", "Neighbourhood", "Bedrooms", "Bathrooms", "Monthly Rent"])

# Filtering Options
filter_type = st.selectbox("Filter by:", ["General Area", "Neighborhood"])
if filter_type == "General Area":
    selected_general_area = st.selectbox("Select General Area", options=sorted(data["General Area"].dropna().unique()))
    filtered_data = data[data["General Area"] == selected_general_area]
else:
    selected_neighbourhood = st.selectbox("Select Neighborhood", options=sorted(data["Neighbourhood"].dropna().unique()))
    filtered_data = data[data["Neighbourhood"] == selected_neighbourhood]

# Number of Units
units = st.number_input("Number of Units", min_value=1, step=1)

# Checkbox for Bathroom Filtering
filter_bathrooms = st.checkbox("Filter by Bathrooms", value=False)

# Columns for Bedroom and Bathroom Inputs
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

# Processing Rent Data for Units
filtered_rent_data = []
for bedrooms, bathrooms in unit_details:
    if bathrooms is not None:
        unit_data = filtered_data[(filtered_data["Bedrooms"] == bedrooms) & (filtered_data["Bathrooms"] == bathrooms)]
    else:
        unit_data = filtered_data[(filtered_data["Bedrooms"] == bedrooms)]
    filtered_rent_data.append(unit_data)

# Calculate Total Monthly Rent
total_monthly_rent = sum(unit["Monthly Rent"].mean() for unit in filtered_rent_data if not unit.empty)
st.write(f"## Total Monthly Rent: ${int(total_monthly_rent):,}")

# Display Unit Statistics
st.write("## Unit Statistics")
for idx in range(0, len(filtered_rent_data), 3):
    unit_columns = st.columns(3)
    for col, unit_data in zip(unit_columns, filtered_rent_data[idx:idx + 3]):
        col.write(f"### Statistics for Unit {idx + 1}")
        if not unit_data.empty:
            avg_rent = unit_data["Monthly Rent"].mean()
            med_rent = unit_data["Monthly Rent"].median()
            rent_count = len(unit_data)

            # Format and Display Statistics
            col.write(f"**Average Rent:** ${int(avg_rent):,}")
            col.write(f"**Median Rent:** ${int(med_rent):,}")
            col.write(f"**Count:** {rent_count}")
        else:
            col.write("No data available.")

# Expense Logic
st.write("## Expense Calculation")
include_expenses = st.checkbox("Include Expenses in Calculations", value=False)
if include_expenses:
    maintenance = st.number_input("Annual Maintenance Cost ($)", min_value=0, value=0, step=100)
    insurance = st.number_input("Annual Insurance Cost ($)", min_value=0, value=0, step=100)
    taxes = st.number_input("Annual Taxes ($)", min_value=0, value=0, step=100)
    hoa_fees = st.number_input("Annual HOA Fees ($)", min_value=0, value=0, step=100)
    other_expenses = st.number_input("Other Annual Expenses ($)", min_value=0, value=0, step=100)

    total_expenses = maintenance + insurance + taxes + hoa_fees + other_expenses
    st.write(f"### Total Annual Expenses: ${total_expenses:,}")
else:
    total_expenses = 0

# Mortgage Calculation
st.write("## Mortgage Calculation")
interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, step=0.1, value=5.0)
terms = [20, 25, 30]  # Years for mortgage
down_payments = [20, 25, 30, 35, 40, 45, 50]  # Percentage

if filtered_rent_data:
    total_rent = total_monthly_rent * 12
    net_income = total_rent - total_expenses

    st.write(f"### Total Annual Rent: ${int(total_rent):,}")
    st.write(f"### Net Annual Income (Rent - Expenses): ${int(net_income):,}")

    for term in terms:
        st.write(f"### {term}-Year Mortgage")
        cols = st.columns(3)
        for idx, down_payment in enumerate(down_payments):
            with cols[idx % 3]:
                if net_income > 0:
                    # Monthly mortgage payment formula
                    monthly_interest_rate = (interest_rate / 100) / 12
                    num_payments = term * 12
                    max_monthly_payment = net_income / 12

                    max_mortgage = (
                        max_monthly_payment
                        * (1 - (1 + monthly_interest_rate) ** -num_payments)
                        / monthly_interest_rate
                    )
                    required_down = max_mortgage * (down_payment / 100)
                    total_value = max_mortgage + required_down
                    yearly_mortgage_payment = max_monthly_payment * 12

                    # Display Results
                    st.write(f"#### {down_payment}% Down Payment")
                    st.write(f"Maximum Mortgage: ${int(max_mortgage):,}")
                    st.write(f"Required Down Payment: ${int(required_down):,}")
                    st.write(f"Total Purchase Value: ${int(total_value):,}")
                    st.write(f"Yearly Mortgage Payment: ${int(yearly_mortgage_payment):,}")
                else:
                    st.write(f"#### {down_payment}% Down Payment")
                    st.write("Insufficient net income for mortgage.")
else:
    st.warning("No valid data to calculate mortgage.")

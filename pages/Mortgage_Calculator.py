import pandas as pd
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials
import io
from datetime import datetime

# Google Drive API Setup
SERVICE_ACCOUNT_FILE = 'rent-analysis-app-a436bd54ffda.json'  # Ensure this file is in the same directory
SCOPES = ['https://www.googleapis.com/auth/drive']

# Initialize credentials
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# Function to list files in the shared folder
def list_files_in_folder(folder_id):
    query = f"'{folder_id}' in parents and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    return files

# Function to download and read a file from Google Drive
def download_excel_file(file_id):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return pd.read_excel(fh, engine="openpyxl")

# Folder ID of your Google Drive folder
FOLDER_ID = "1XFA7TspvxyVq6trXwWCUa1Qvl0b0n2HU"

# Fetch available files
files = list_files_in_folder(FOLDER_ID)

# Extract file dates and sort them
file_dates = {file['name'][:8]: file['id'] for file in files if file['name'][:8].isdigit()}
sorted_dates = sorted(file_dates.keys(), reverse=True)

# Convert date format to "DD Mon YYYY"
formatted_dates = {
    date: datetime.strptime(date, "%Y%m%d").strftime("%d %b %Y").lower()
    for date in sorted_dates
}

# Streamlit UI
st.title("Mortgage Calculator")

# Display available dates
st.write("### Available Dates for Data:")
formatted_dates_display = ", ".join(formatted_dates[date] for date in sorted_dates)
st.write(formatted_dates_display)

# File selection
selected_formatted_dates = st.multiselect(
    "Select Dates to Use",
    options=[formatted_dates[date] for date in sorted_dates],
    default=[formatted_dates[sorted_dates[0]]]
)

use_recent = st.button("Use Most Recent Data")

# Reverse map formatted dates back to raw dates
if use_recent:
    most_recent_date = sorted_dates[0]
    selected_dates = [most_recent_date]
    selected_formatted_dates = [formatted_dates[most_recent_date]]
else:
    selected_dates = [
        date for date, formatted in formatted_dates.items() if formatted in selected_formatted_dates
    ]

selected_file_ids = [file_dates[date] for date in selected_dates]

# Combine data from selected files
data_frames = []
for date, file_id in zip(selected_dates, selected_file_ids):
    df = download_excel_file(file_id)
    df["HelperDate"] = date  # Add a helper column to indicate the file's date
    
    # Rename "Bracketed Text" to "General Area" if it exists in the file
    if "Bracketed Text" in df.columns:
        df.rename(columns={"Bracketed Text": "General Area"}, inplace=True)
    
    data_frames.append(df)

if data_frames:
    # Combine all selected data without deduplication
    combined_data = pd.concat(data_frames, ignore_index=True)

    # Clean and filter the data
    combined_data = combined_data.dropna(subset=["General Area", "Neighbourhood", "Bedrooms", "Bathrooms", "Monthly Rent"])

    # Filtering Options
    filter_type = st.selectbox("Filter by:", ["General Area", "Neighborhood"])
    if filter_type == "General Area":
        selected_general_area = st.selectbox("Select General Area", options=sorted(combined_data["General Area"].dropna().unique()))
        filtered_data = combined_data[combined_data["General Area"] == selected_general_area]
    else:
        selected_neighbourhood = st.selectbox("Select Neighborhood", options=sorted(combined_data["Neighbourhood"].dropna().unique()))
        filtered_data = combined_data[combined_data["Neighbourhood"] == selected_neighbourhood]

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
                    # Calculate monthly interest rate and number of payments
                    monthly_interest_rate = (interest_rate / 100) / 12
                    num_payments = term * 12

                    # Convert Net Annual Income to Monthly Net Income
                    monthly_net_income = net_income / 12

                    # Calculate Maximum Mortgage (Present Value of Payments)
                    max_mortgage = (
                        monthly_net_income
                        * (1 - (1 + monthly_interest_rate) ** -num_payments)
                        / monthly_interest_rate
                    )

                    # Calculate Total Purchase Value
                    total_value = max_mortgage / (1 - (down_payment / 100))

                    # Calculate Required Down Payment
                    required_down = total_value * (down_payment / 100)

                    # Display Results
                    st.write(f"#### {down_payment}% Down Payment")
                    st.write(f"Total Purchase Value: ${int(total_value):,}")
                    st.write(f"Maximum Mortgage: ${int(max_mortgage):,}")
                    st.write(f"Required Down Payment: ${int(required_down):,}")
                    st.write(f"Yearly Mortgage Payment: ${int(net_income):,}")
                else:
                    st.write(f"#### {down_payment}% Down Payment")
                    st.write("Insufficient net income for mortgage.")


else:
    st.write("No data selected or available.")

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
st.title("Dynamic Rent Analysis")

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



    # Adapt column names for compatibility
    if "General Area" not in combined_data.columns and "Bracketed Text" in combined_data.columns:
        combined_data.rename(columns={"Bracketed Text": "General Area"}, inplace=True)

    # Verify required columns
    required_columns = ["General Area", "Neighbourhood", "Bedrooms", "Bathrooms", "Monthly Rent", "Rooms"]
    missing_columns = [col for col in required_columns if col not in combined_data.columns]

    if missing_columns:
        st.error(f"The following required columns are missing: {', '.join(missing_columns)}")
    else:
        # Filter selection in Streamlit
        filter_type = st.selectbox("Filter by:", ["General Area", "Neighbourhood"])
        if filter_type == "General Area":
            selected_general_area = st.selectbox(
                "Select General Area",
                options=sorted(combined_data["General Area"].dropna().unique())
            )
            filtered_data = combined_data[combined_data["General Area"] == selected_general_area]
        else:
            selected_neighbourhood = st.selectbox(
                "Select Neighbourhood",
                options=sorted(combined_data["Neighbourhood"].dropna().unique())
            )
            filtered_data = combined_data[combined_data["Neighbourhood"] == selected_neighbourhood]

        # Include Bathrooms in Analysis
        include_bathrooms = st.checkbox("Include Bathrooms in Analysis", value=False)

        if include_bathrooms:
            grouped_stats = filtered_data.groupby(["Bedrooms", "Bathrooms"]).agg(
                AverageRent=("Monthly Rent", "mean"),
                MedianRent=("Monthly Rent", "median"),
                Count=("Monthly Rent", "count"),
                AverageRooms=("Rooms", "mean")
            ).reset_index()
        else:
            grouped_stats = filtered_data.groupby("Bedrooms").agg(
                AverageRent=("Monthly Rent", "mean"),
                MedianRent=("Monthly Rent", "median"),
                Count=("Monthly Rent", "count"),
                AverageRooms=("Rooms", "mean")
            ).reset_index()

        # Format numbers and add dollar signs
        grouped_stats["AverageRent"] = grouped_stats["AverageRent"].apply(lambda x: f"${int(x):,}")
        grouped_stats["MedianRent"] = grouped_stats["MedianRent"].apply(lambda x: f"${int(x):,}")
        grouped_stats["AverageRooms"] = grouped_stats["AverageRooms"].round(2)

        # Display Grouped Statistics
        st.write("### Grouped Statistics")
        st.dataframe(grouped_stats)
else:
    st.write("No data selected or available.")

import pandas as pd
import streamlit as st

# Title of the app
st.title("Dynamic Rent Analysis")

# Load Data from Excel File
file_url = r"https://docs.google.com/uc?id=1dx5slnckpqhmPgyH8rSpXF9yHEiYJV0X&export=download"

data = pd.read_excel(file_url, engine="openpyxl")

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

# Checkbox to include bathrooms in analysis
include_bathrooms = st.checkbox("Include Bathrooms in Analysis", value=False)

# Group and analyze data based on selected filters
if include_bathrooms:
    grouped_stats = filtered_data.groupby(["Bedrooms", "Bathrooms"]).agg(
        AverageRent=("Monthly Rent", "mean"),
        MedianRent=("Monthly Rent", "median"),
        Count=("Monthly Rent", "count")
    ).reset_index()  # Keep Bedrooms and Bathrooms, remove default index
else:
    grouped_stats = filtered_data.groupby("Bedrooms").agg(
        AverageRent=("Monthly Rent", "mean"),
        MedianRent=("Monthly Rent", "median"),
        Count=("Monthly Rent", "count")
    ).reset_index()  # Keep Bedrooms, remove default index

# Display grouped statistics
st.write("### Grouped Statistics")
st.dataframe(grouped_stats)

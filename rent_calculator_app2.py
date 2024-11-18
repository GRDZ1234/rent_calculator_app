import pandas as pd
import streamlit as st

st.title("Dynamic Rent Analysis")

file_url = "https://docs.google.com/uc?id=1dx5slnckpqhmPgyH8rSpXF9yHEiYJV0X&export=download"
data = pd.read_excel(file_url, engine="openpyxl")

data = data.dropna(subset=["General Area", "Neighbourhood", "Bedrooms", "Bathrooms", "Monthly Rent"])

filter_type = st.selectbox("Filter by:", ["General Area", "Neighborhood"])
if filter_type == "General Area":
    selected_general_area = st.selectbox("Select General Area", options=sorted(data["General Area"].dropna().unique()))
    filtered_data = data[data["General Area"] == selected_general_area]
else:
    selected_neighbourhood = st.selectbox("Select Neighborhood", options=sorted(data["Neighbourhood"].dropna().unique()))
    filtered_data = data[data["Neighbourhood"] == selected_neighbourhood]

include_bathrooms = st.checkbox("Include Bathrooms in Analysis", value=False)

if include_bathrooms:
    grouped_stats = filtered_data.groupby(["Bedrooms", "Bathrooms"]).agg(
        AverageRent=("Monthly Rent", "mean"),
        MedianRent=("Monthly Rent", "median"),
        Count=("Monthly Rent", "count")
    ).reset_index()
else:
    grouped_stats = filtered_data.groupby("Bedrooms").agg(
        AverageRent=("Monthly Rent", "mean"),
        MedianRent=("Monthly Rent", "median"),
        Count=("Monthly Rent", "count")
    ).reset_index()

# Format numbers and add dollar signs
grouped_stats["AverageRent"] = grouped_stats["AverageRent"].apply(lambda x: f"${int(x):,}")
grouped_stats["MedianRent"] = grouped_stats["MedianRent"].apply(lambda x: f"${int(x):,}")

st.write("### Grouped Statistics")
st.dataframe(grouped_stats)

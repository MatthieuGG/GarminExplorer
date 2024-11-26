import streamlit as st
import pandas as pd
import os
import altair as alt
import plotly.graph_objects as go

#################### Computation
def cleaning_data(df):
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by='Date', ascending=True)
    df['Favorite'] = df['Favorite'].astype(bool)
    # cleaning the 00:00:00.0 format into 00:00:00 in 'Time'
    df['Time'] = df['Time'].str.split('.').str[0] 
    df['Time'] = df['Time'].apply(lambda x: f"00:{x}" if len(x.split(':')) == 2 else x)
    # converting 'Time' in minutes
    df['Time'] = pd.to_timedelta(df['Time']) 
    df['Time'] = df['Time'].dt.total_seconds() / 60
    return df

def filtering_activity(df, activity_type):
    if 'Activity Type' not in df.columns:
        raise ValueError("No column 'Activity Type' in uploaded dataframe.")
    filtered_df = df[df['Activity Type'] == activity_type]
    return filtered_df

def add_cumulative_column(df, column_name):
    cumulative_column_name = f'{column_name}_cum'
    df[cumulative_column_name] = df[column_name].cumsum()
    return df

def convert_pace_to_minutes(pace_str):
    try:
        minutes, seconds = map(int, pace_str.split(':'))
        return minutes + seconds / 60  # Minutes en décimal
    except ValueError:
        return None

def date_range_slider_filter(df, date_column, title="Select a period", date_format="YYYY-MM-DD"):
    # identify start and stop
    min_date = df[date_column].min().date()
    max_date = df[date_column].max().date()

    selected_dates = st.slider(
        title,
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format=date_format,
    )

    # convert in datetime
    start_date = pd.to_datetime(selected_dates[0])
    end_date = pd.to_datetime(selected_dates[1])

    filtered_df = df[(df[date_column] >= start_date) & (df[date_column] <= end_date)]

    return filtered_df

############### Streamlit
st.set_page_config(page_title="Garmin Explorer", page_icon="🏃‍➡️")
st.title("Welcome to the Garmin Explorer!")

st.logo(os.path.join(os.getcwd(), 'images', 'yajirobe.jpg'), size="large", link="https://github.com/MatthieuGG", icon_image=None)
# Say thanks
recipient_email = "matthieu.gallou.guyot@gmail.com"
subject = "Thanks for the Garmin Explorer app!"
body = "Dear Matthieu, (...)."
mailto_link = f"mailto:{recipient_email}?subject={subject}&body={body}"

st.sidebar.link_button(
    label="Say Thanks",
    url=mailto_link,
    type="primary",
    icon="💌"
)

st.markdown("""
        Upload your data exported as CSV from Garmin.  
        *(note that only **running** activities are considered at the moment)*
    """)

# file upload
uploaded_file = st.file_uploader("", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df = cleaning_data(df)

with st.expander("Where to obtain these data?"):
    st.markdown('''
    The data can be obtained through the official [Garmin Connect](https://connect.garmin.com/modern/activities) website. 
    Please scroll down all the way down to consider all activities.
    ''')
    st.image(os.path.join(os.getcwd(), 'images', 'Screenshot 2024-11-26 093640.jpg'))

if uploaded_file is not None:
    running = filtering_activity(df, "Running")
    # converting Pace in minutes
    running['Avg Pace'] = running['Avg Pace'].apply(convert_pace_to_minutes)
    running['Best Pace'] = running['Best Pace'].apply(convert_pace_to_minutes)
    # converting Candecy in int
    running['Avg Run Cadence'] = pd.to_numeric(running['Avg Run Cadence'], errors='coerce').fillna(0).astype(int)
    running['Max Run Cadence'] = pd.to_numeric(running['Max Run Cadence'], errors='coerce').fillna(0).astype(int)
    # dealing with Ascent and Descent
    running['Total Ascent'] = pd.to_numeric(running['Total Ascent'], errors='coerce').fillna(0).astype(int)
    running['Total Descent'] = (pd.to_numeric(running['Total Descent'], errors='coerce').fillna(0).astype(int)* -1)    
   
    # st.dataframe(running)

    filtered_df = date_range_slider_filter(running, date_column="Date")
    #cumulative data
    filtered_df = add_cumulative_column(filtered_df, 'Distance')
    filtered_df = add_cumulative_column(filtered_df, 'Calories')
    filtered_df = add_cumulative_column(filtered_df, 'Time')
    filtered_df = add_cumulative_column(filtered_df, 'Total Ascent')
    filtered_df = add_cumulative_column(filtered_df, 'Total Descent')

### Running
st.header("Running")

# Calculs
if uploaded_file is not None:
    num_runs = len(filtered_df)  # Nombre de courses
    total_distance = filtered_df["Distance"].sum()  # Distance totale
    total_time = filtered_df["Time"].sum()  # Temps total

    # Affichage dans des colonnes
    col1, col2, col3 = st.columns(3)
    col1.metric("Sessions", f"{num_runs}")
    col2.metric("Distance", f"{total_distance:.0f} km")
    col3.metric("Time", f"{total_time:.0f}' ")

popover = st.popover("What are you interested in?")
distance = popover.checkbox("Distance", True)
duration = popover.checkbox("Duration", True)
pace = popover.checkbox("Pace", True)
heart_rate = popover.checkbox("Heart Rate", True)
cadence = popover.checkbox("Cadence", True)
elevation = popover.checkbox("Ascent - Descent", True)
calories = popover.checkbox("Calories", True)


color_palette = {
    "Distance": "#1f77b4",       
    "Duration": "#ff7f0e",       
    "Pace": ["#2ca02c", "#d62728"],  
    "Heart Rate": ["#f50606", "#cfc331"],  
    "Cadence": ["#0244b2", "#09caca"],  
    "Elevation": ["#17becf", "#bcbd22"],
    "Calories": "#bcbd22", 
}

tab1, tab2 = st.tabs(["Evolution over time", "Total over time"])
with tab1:
    if uploaded_file is not None:
        if distance: 
            st.subheader("Distance")
            st.area_chart(data=filtered_df, x='Date', y='Distance', x_label=None, y_label='Distance (km)', color=color_palette["Distance"], stack=None, width=700, height=300, use_container_width=False)
        if duration:
            st.subheader("Duration")
            st.area_chart(data=filtered_df, x='Date', y='Time', x_label=None, y_label='Duration (minutes)', color=color_palette["Duration"], width=700, height=300, use_container_width=False)
        if pace:
            st.subheader("Pace")
            st.area_chart(data=filtered_df,  x='Date', y=['Avg Pace', 'Best Pace'], x_label=None, y_label='Pace (minute/km)', color=color_palette["Pace"], stack=None, width=700, height=300, use_container_width=False)
        if heart_rate:
            st.subheader("Heart Rate")
            st.line_chart(data=filtered_df,  x='Date', y=['Avg HR', 'Max HR'], x_label=None, y_label='Heart rate (bpm)', color=color_palette["Heart Rate"], width=700, height=300, use_container_width=False)
        if cadence:
            st.subheader("Cadence")
            st.line_chart(data=filtered_df,  x='Date', y=['Avg Run Cadence', 'Max Run Cadence'], x_label=None, y_label='Run cadence (ppm)', color=color_palette["Cadence"], width=700, height=300, use_container_width=False)
        #plotly or altair for defined values (pace, HR, cadency) (ex: y = 130-150 bom)
        # also trends ?
        if elevation: 
            st.subheader("Elevation")
            st.area_chart(data=filtered_df,  x='Date', y=['Total Ascent', 'Total Descent'], x_label=None, y_label='Elevation (m)', color=color_palette["Elevation"], stack=None, width=700, height=300, use_container_width=False)
        if calories:
            st.subheader("Calories")
            st.area_chart(data=filtered_df, x='Date', y='Calories', x_label=None, y_label='Calories (kCal)', color=color_palette["Calories"], stack=None, width=700, height=300, use_container_width=False)
        # future: cum BPM, cum PPM, stride length, laps, elevation
with tab2:
    if uploaded_file is not None:
        if distance:
            st.subheader("Distance")
            st.area_chart(data=filtered_df, x='Date', y='Distance_cum', x_label=None, y_label='Cumulative distance (km)', color=color_palette["Distance"], stack=None, width=700, height=300, use_container_width=False)
        if duration:
            st.subheader("Duration")
            st.area_chart(data=filtered_df, x='Date', y='Time_cum', x_label=None, y_label='Cumulative time (minutes)', color=color_palette["Duration"], stack=None, width=700, height=300, use_container_width=False)
        if elevation:
            st.subheader("Elevation")
            st.area_chart(data=filtered_df,  x='Date', y=['Total Ascent_cum', 'Total Descent_cum'], x_label=None, y_label='Cumulative elevation (m)', color=color_palette["Elevation"], stack=None, width=700, height=300, use_container_width=False)
        if calories:
            st.subheader("Calories")
            st.area_chart(data=filtered_df, x='Date', y='Calories_cum', x_label=None, y_label='Cumulative calories (kCal)', color=color_palette["Calories"], stack=None, width=700, height=300, use_container_width=False)

st.divider()
with st.expander("Future fonctionalities to come"):
    st.write('''
        - amount of heart beats and steps, 
        - analysis of stride lengths, laps and elevation, 
        - treshold values (BPM / PPM)
        - favorites, training stress score, decompression
        - other garmin data API
        - HR values 
        - BMI
    ''')
st.caption('⚠️ Unofficial app, not provided by Garmin')

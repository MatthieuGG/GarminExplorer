import streamlit as st
import pandas as pd

# Nettoyage et transformation des données (identique à ce que vous aviez)
def cleaning_data(df):
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by='Date', ascending=True)
    df['Favorite'] = df['Favorite'].astype(bool)
    # df['Time'] = pd.to_timedelta(df['Time'])
    return df

def clean_time_column(time_value):
    try:
        # Si le temps est au format `MM:SS.m` ou `SS.m`, on ajuste
        if '.' in time_value:
            minutes, seconds = time_value.split(':') if ':' in time_value else ("0", time_value)
            seconds = seconds.split('.')[0]  # Prendre la partie avant la décimale
            time_value = f"0:{minutes.zfill(2)}:{seconds.zfill(2)}"  # Reformater

        # Convertir en timedelta pour uniformiser
        clean_time = pd.to_timedelta(time_value)
        # Revenir au format HH:MM:SS
        return str(clean_time.components.hours).zfill(2) + ":" + \
               str(clean_time.components.minutes).zfill(2) + ":" + \
               str(clean_time.components.seconds).zfill(2)
    except Exception as e:
        return None  # Retourner None pour les valeurs non valides

def filtering_activity(df, activity_type):
    if 'Activity Type' not in df.columns:
        raise ValueError("No column 'Activity Type' in uploaded dataframe.")
    filtered_df = df[df['Activity Type'] == activity_type]
    return filtered_df

def plot_column_relationship_with_line_chart(df, x_column, y_column, x_label=None, y_label=None):
    """
    Trace un graphique de ligne pour deux colonnes en utilisant `st.line_chart`.
    """
    if x_column not in df.columns or y_column not in df.columns:
        st.error(f"Le DataFrame doit contenir les colonnes '{x_column}' et '{y_column}'.")
        return

    # Préparer les données pour le graphique
    data_to_plot = df[[x_column, y_column]]

    # Afficher les titres et labels
    # st.write(f"Graphique de '{y_column}' en fonction de '{x_column}':")
    
    # Utiliser st.line_chart pour créer le graphique
    st.line_chart(data=data_to_plot.set_index(x_column), use_container_width=True)

import streamlit as st
import pandas as pd

def plot_two_columns_with_line_chart(df, x_column, y_column1, y_column2, x_label=None, y_label1=None, y_label2=None, start_date=None, end_date=None):
    """
    Trace un graphique de ligne avec une colonne en X et deux colonnes en Y, 
    après avoir filtré les données en fonction de la plage de dates.

    Parameters:
        df (pd.DataFrame): Le DataFrame contenant les données.
        x_column (str): Le nom de la colonne pour l'axe des X.
        y_column1 (str): Le nom de la première colonne pour l'axe des Y.
        y_column2 (str): Le nom de la deuxième colonne pour l'axe des Y.
        x_label (str, optional): Le label de l'axe des X. Par défaut, le nom de la colonne `x_column`.
        y_label1 (str, optional): Le label de la première colonne Y. Par défaut, le nom de la colonne `y_column1`.
        y_label2 (str, optional): Le label de la deuxième colonne Y. Par défaut, le nom de la colonne `y_column2`.
        start_date (datetime.date, optional): La date de début pour filtrer.
        end_date (datetime.date, optional): La date de fin pour filtrer.

    Returns:
        None: Affiche le graphique dans Streamlit.
    """
    # Vérification des colonnes
    if x_column not in df.columns or y_column1 not in df.columns or y_column2 not in df.columns:
        st.error(f"Le DataFrame doit contenir les colonnes '{x_column}', '{y_column1}' et '{y_column2}'.")
        return

    # Filtrer le DataFrame en fonction de la plage de dates (si fournie)
    if start_date and end_date:
        df = df[(df[x_column].dt.date >= pd.Timestamp(start_date)) & (df[x_column].dt.date <= pd.Timestamp(end_date))]

    # Paramètres par défaut
    x_label = x_label or x_column
    y_label1 = y_label1 or y_column1
    y_label2 = y_label2 or y_column2

    # Préparer les données pour le graphique
    data_to_plot = df[[x_column, y_column1, y_column2]]

    # Affichage des titres et labels
    # st.write(f"Graphique de '{y_column1}' et '{y_column2}' en fonction de '{x_column}':")
    
    # Utilisation de `st.line_chart` pour créer le graphique
    st.line_chart(data=data_to_plot.set_index(x_column), use_container_width=True)

############### Streamlit
st.set_page_config(page_title="Garmin Explorer", page_icon="🏃‍➡️")
st.write("# Welcome to the Garmin Explorer!")
st.markdown("""
    Please upload your data exported as CSV from Garmin
    *(note that only **running** is considered at the moment)*.
""")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df = cleaning_data(df)  # On applique la fonction de nettoyage et on assigne le résultat à df
    df['Time'] = df['Time'].apply(clean_time_column)
    st.write("Data Preview:")
    st.dataframe(df)

    ### Running
    st.subheader("Running")

    running = filtering_activity(df, "Running")
    st.dataframe(running)

    # Utiliser un slider pour définir l'intervalle de dates
    start_date = running['Date'].min().date()
    end_date = running['Date'].max().date()

    # Utilisation de slider pour choisir une plage de dates
    selected_dates = st.slider(
        "Sélectionnez la plage de dates",
        min_value=start_date,
        max_value=end_date,
        value=(start_date, end_date),
        format="YYYY-MM-DD"
    )

    # Filtrer les données en fonction de la plage sélectionnée
    start_date = pd.to_datetime(selected_dates[0])
    end_date = pd.to_datetime(selected_dates[1])

    # Filtrer les données
    filtered_df = running[(running['Date'] >= start_date) & (running['Date'] <= end_date)]

    tab1, tab2 = st.tabs(["Evolution over time", "Total over time"])

    with tab1:
        st.write("### Distance (km)")
        plot_column_relationship_with_line_chart(filtered_df, x_column='Date', y_column='Distance', x_label="Date", y_label="Distance parcourue")
        st.write("### Duration (HH:mm:ss)")
        plot_column_relationship_with_line_chart(filtered_df, x_column='Date', y_column='Time')
        st.write("### Pace (minute/km)")
        plot_two_columns_with_line_chart(filtered_df, x_column='Date', y_column1='Avg Pace', y_column2='Best Pace', x_label="Date", y_label1="Distance parcourue", y_label2="Pace (min/km)")
        st.write("### Steps cadency (PPM)")
        plot_two_columns_with_line_chart(filtered_df, x_column='Date', y_column1='Avg Run Cadence', y_column2='Max Run Cadence')
        st.write("### Heart Rate (BPM)")
        plot_two_columns_with_line_chart(filtered_df, x_column='Date', y_column1='Avg HR', y_column2='Max HR', x_label="Date", y_label1="Distance parcourue", y_label2="Pace (min/km)")
        st.write("### Calories (kcal)")
        plot_column_relationship_with_line_chart(filtered_df, x_column='Date', y_column='Calories')
        st.write("### Ascent / Descent")
        plot_two_columns_with_line_chart(filtered_df, x_column='Date', y_column1='Total Ascent', y_column2='Total Descent')
    with tab2:
        st.write("...")

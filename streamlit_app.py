# CxC SAP Challenge - Multi-Dimensional Poverty Index 

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import branca
import folium
from streamlit_folium import st_folium
from folium.features import GeoJsonTooltip
from streamlit_folium import st_folium

APP_TITLE = 'Multi-Dimensional Poverty Index'
APP_SUB_TITLE = 'SAP Sustainability & Multidimensional Poverty Index Challenge'

def display_time_filters(df):
    year_list = list(df['Year'].unique())
    year_list.sort()
    year = st.sidebar.selectbox('Year', year_list, len(year_list)-1)
    return year

def display_country_filter(df, country_name):
    country_list = list(df['Country Name'].unique())
    country_list.sort()
    country_index = country_list.index(country_name) if country_name and country_name in country_list else 0
    return st.sidebar.selectbox('Country', country_list, country_index)

def display_map(df, year):
    df = df[(df['Year'] == year)]
    df["sqrt_value"] = df["MPI"].apply(lambda x : np.sqrt(x))
    
    map = folium.Map(location=[50, 0], width="100", height="100", zoom_start=2, scrollWheelZoom=False, tiles='CartoDB positron')
    
    colormap = branca.colormap.LinearColormap(
        colors=["#ffffcc", "#c2e699", "#78c679", "#31a354", "#006837"],  # "YlGn" shades
        vmin=df["MPI"].min(),
        vmax=df["MPI"].max(),
        caption="MPI Values"
    )

    choropleth = folium.Choropleth(
        geo_data='data/world-map-boundaries.geojson',
        data=df,
        columns=('Country Name', 'sqrt_value'),
        key_on='feature.properties.name',
        line_opacity=0.8,
        highlight=True,
        nan_fill_color='black',
        fill_opacity=0.7,
        nan_fill_opacity=0.7,
        legend_name="MPI Values",
        name='MPI',
        fill_color="YlGn",
        bins=5
    )

    map.add_child(colormap)
    
    choropleth.geojson.add_to(map)

    df_indexed = df.set_index('Country Name')
    for feature in choropleth.geojson.data['features']:
        country_name = feature['properties']['name']
        feature['properties']['MPI'] = 'MPI: ' + str(round(df_indexed.loc[country_name, 'MPI'])) if country_name in list(df_indexed.index) else ''

        tooltip = GeoJsonTooltip(fields=['name', 'MPI'], labels=False)
        tooltip.add_to(choropleth.geojson)
    
    st_map = st_folium(map, width=700, height=600)

    country_name = ''
    if st_map['last_active_drawing']:
        country_name = st_map['last_active_drawing']['properties']['name']
    return country_name

def display_mpi_facts(df, year, country_name, field, title, string_format='${:,}', is_median=False):
    df = df[df['Year'] == year]

    if country_name:
        df = df[df['Country Name'] == country_name]
        
    df.drop_duplicates(inplace=True)
    total = df[field].sum()
    
    st.metric(title, string_format.format(round(total)))

def display_country_rank(df, year, country_name):
    df = df[df['Year'] == year]
    df = df.sort_values('MPI', ascending=False).reset_index(drop=True)
    rank = df.index[df["Country Name"] == country_name].tolist()[0] + 1
    st.metric('Country Rank', f"{rank}/{df.shape[0]}")
    
def plot_indicator(df, country, indicator):
    country_df = df[df["Country Name"] == country]
    
    median_values = df.groupby("Year")[indicator].median()
 
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(country_df["Year"], country_df[indicator], marker="o", linestyle="-", color="b", label=f"{country} {indicator}")
    ax.plot(country_df["Year"], median_values.values, marker="o", linestyle="-", color="purple", label=f"World Median {indicator}")

    ax.set_title(f"{country} - {indicator} (2000-2022)", fontsize=14)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel(indicator, fontsize=8)
    ax.legend()
    ax.grid(True)
    ax.set_ylim(ymin=0)

    st.pyplot(fig)
    
def main():
    st.set_page_config(APP_TITLE)
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)

    df_mpi = pd.read_csv('data/MPI Data.csv')
    df_detailed = pd.read_csv('data/Detailed MPI Data.csv')
    
    df_mpi = df_mpi[df_mpi["Year"] != 2023]
    df_detailed = df_detailed[df_detailed["Year"] != 2023]
    
    df_detailed["Country Name"] = df_mpi["Country Name"]

    year = display_time_filters(df_mpi)
    country_name = display_map(df_mpi, year)
    country_name = display_country_filter(df_mpi, country_name)

    st.subheader(f'{country_name} MPI Facts')

    col1, col2 = st.columns(2)
    with col1:
        display_mpi_facts(df_mpi, year, country_name, 'MPI', 'MPI', string_format='{:,}')
    with col2:
        display_country_rank(df_mpi, year, country_name)

    indicators = [col for col in df_detailed.columns if col not in ["Country Name", "Year"]]
    selected_indicator = st.selectbox("Select an Indicator", indicators)
    plot_indicator(df_detailed, country_name, selected_indicator)


if __name__ == "__main__":
    main()
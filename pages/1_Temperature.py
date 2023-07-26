import json
import pandas as pd
import streamlit as st
import requests
import altair as alt
import math

def get_data(start, end, lat, long):
    # create url
    url = 'https://archive-api.open-meteo.com/v1/archive?'
    timezone = '&timezone=auto'
    lat = 'latitude=' + lat
    long = '&longitude=' + long
    start = '&start_date=' + start
    end = '&end_date=' + end
    url = url + lat + long + start + end + timezone + '&daily=temperature_2m_max&daily=temperature_2m_min'
    #url = url.replace(" ", "")
    #print(url)
    # get the data
    response = requests.get(url)
    #print(response.content)
    response_data = json.loads(response.content)
    response_df = pd.DataFrame(response_data)
    return response_df

# set-up all data for one place
def place_set_up(lat, long):
    start = '1940-01-01'
    end = '2023-01-01'

    # get the data
    raw_data = get_data(start, end, lat, long)

    data = pd.DataFrame()
    data["date"] = raw_data["daily"]["time"]
    data["t_max"] = raw_data["daily"]["temperature_2m_max"]
    data["t_min"] = raw_data["daily"]["temperature_2m_min"]
    data["t_avg"] = (data["t_max"] + data["t_min"]) / 2

    # calculate yearly average
    # calculate the year for each date
    data["date"] = pd.to_datetime(data["date"])
    data["year"] = data["date"].dt.year

    # calculate the average temperature per year
    year_averages = data.groupby("year")["t_avg"].mean()

    # add the average yearly temperature to all entries in the data variable
    data["t_avg_year"] = data["year"].apply(lambda year: year_averages[year])

    # calculate the moving average
    window_size = 1080
    moving_average = data["t_avg"].rolling(window_size).mean()

    # add the moving average to the data variable
    data["moving_average"] = moving_average
    return data

def search_place(place):
    # search place
    # place = 'Zurich'
    url_place = 'https://nominatim.openstreetmap.org/search?q=' + place + '&limit=1&format=json'
    response_place = requests.get(url_place)
    data_place = json.loads(response_place.content)
    name = data_place[0]["display_name"]
    lat = data_place[0]["lat"]
    long = data_place[0]["lon"]
    country = name.rsplit(',', 1)[-1]
    name = name.split(',')[0]
    return name, lat, long, country

def create_chart(data):
    # Rename the axis labels
    x_axis_label = "Date"
    y_axis_label = "Average Temperatur [°C]"
    # calculate min and max temp value
    min_temp = math.floor(float(data["moving_average"].min()))
    max_temp = math.ceil(float(data["moving_average"].max()))
    # Create the line chart with custom axis labels
    chart = alt.Chart(data).mark_line().encode(
        x=alt.X('date:T', title=x_axis_label),
        y=alt.Y('moving_average:Q', title=y_axis_label, scale=alt.Scale(domain=(min_temp, max_temp)))
    ).interactive()
    return chart


st.set_page_config(page_title="Temperature",
                   layout="wide")
st.sidebar.header("Temperature")
st.title('Temperature Change 1940-2023')

col_input, col_result = st.columns([2, 4], gap="large")

with col_input:
    # get user input
    st.write("#### Selct a place")
    place = st.text_input("Search for a place", value="Zurich")
    name, lat, long, country = search_place(place)
    st.write(name + ',' + country)
    place = pd.DataFrame()
    place["lat"] = 0
    place["long"] = 0
    place.loc[0] = [float(lat), float(long)]
    st.map(place, latitude="lat", longitude="long", zoom=8, size=100)

# get all data for that place
data = place_set_up(lat, long)
# select the data according to user input
data_select = data.loc[data["year"] > 1940]
data_select = data.loc[data["year"] < 2023]

# get the value for the first and last date in the dataset
data_moving_avg = data[data["moving_average"] > 0]
min_val = round(float(data_moving_avg["moving_average"][data_moving_avg["date"] == data_moving_avg["date"].min()]),1)
max_val = round(float(data_moving_avg["moving_average"][data_moving_avg["date"] == data_moving_avg["date"].max()]),1)
delta = round(max_val - min_val,1)
if delta > 0:
    sign = '+'
else:
    sign = ''

chart = create_chart(data_moving_avg)

cont_results = st.container()

with col_result:
        # show the results
        st.write("#### Results")
        st.metric(label="average Temperature 2023", value=str(max_val)+' °C', delta=str(delta)+' °C since 1940')
        st.write("The average temperature in " + name + " changed by " + sign + str(delta)+' °C since 1940.')
        st.altair_chart(chart, use_container_width=True, theme='streamlit')
        with st.expander("Definitions"):
            st.write("As average, the three year moving average is shown.")
        #st.line_chart(data=data_select, x="date", y="moving_average")





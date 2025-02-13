import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime as dt
from tzlocal import get_localzone
from datetime import timezone




# UI Header
st.title("Trades today")


# Enter trade date
today =  dt.today().replace(tzinfo=get_localzone()).astimezone(timezone.utc)
selected_date = st.date_input("Select a date:", value=today ,format="DD/MM/YYYY")


# URL of the JSON data source (Modify with actual source)
DATA_URL = "https://app.altrafx.com:5012/api/user/getsavedtradingdatabydate/67056bc473123cdaf831abd1?key=date&date="  + selected_date.strftime("%Y.%m.%d")


# Function to fetch JSON data from a webpage
def fetch_json_data(url):
    try:
        response = requests.get(url)
        return response.json()  # Convert response to JSON
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return []


# Load data from the API
trade_data = fetch_json_data(DATA_URL)
if trade_data.get('status') == 200:
    trade_data_parsed = trade_data['documents'][0]['trades']

    # Load data from history if there is any
    file_name = "./src/trade_history.json"
    history:dict = json.load(open(file_name,"r"))
    historical_data = history.get(selected_date.strftime("%Y.%m.%d"))

    if  st.session_state.get('trade_status') is None:
        st.session_state['trade_status'] = {}

    # Display the trade data in an expandable format
    st.write("### Trade List (Click ID to Expand Details)")

    # Iterate through each trade and display it in an expandable section
    for trade in trade_data_parsed:
        if trade['trade'] == "Yes":
            trader = 'None'
            if historical_data is not None:
                trader = historical_data.get(trade['tradeid'])
            if st.session_state['trade_status'].get(trade['tradeid']) is None:
                st.session_state['trade_status'][trade['tradeid']] = trader
            else:
                trader = st.session_state['trade_status'][trade['tradeid']]
            df = pd.DataFrame(index=pd.Index(data=list(trade.keys()),name='keys'), data=list(trade.values()),columns=['values'])
            df = pd.concat([pd.DataFrame(index=pd.Index(data=['trader'],name='keys'), data=[trader], columns=['values']),df])

            col1, col2 = st.columns([2, 1])

            with col1:
                with st.expander(f"{trade['country']} : {trade['event']}"):
                    st.dataframe(df,use_container_width=True)  

            with col2:
                disable = today > dt.strptime(trade['date'] + ' ' + trade['time'],"%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc)
                options = ["None", "CS", "SDG"]
                st.session_state.trade_status[trade['tradeid']]  = st.selectbox("Trader : ", options=options, index='None' if trader not in options else options.index(trader), disabled=disable, key=trade['tradeid'])


    # Button to save modified trade data with assigned trade statuses
    if st.button("Save Trader data"):
        if history.get(selected_date.strftime("%Y.%m.%d")) is None:
            history[selected_date.strftime("%Y.%m.%d")] = {}
        for trade in trade_data_parsed:
            if trade['trade'] == "Yes":
                history[selected_date.strftime("%Y.%m.%d")][trade['tradeid']] = st.session_state.trade_status[trade['tradeid']]
        # Save updated data to a JSON file
        with open(file_name, "w") as f:
            json.dump(history, f, indent=4)

        st.success("Trade data saved successfully")
else:
    st.write('No trades for the given day')
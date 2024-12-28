import requests
import streamlit as st
from bs4 import BeautifulSoup

# URL and headers
url = 'https://uk.investing.com/economic-calendar/'
headers = {'User-Agent': 'Mozilla/5.0'}

@st.cache_data()
def get_events() -> dict:
    # Fetch the webpage
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Initialize the dictionary to store event data
    events = {}

    # Find all rows containing event data
    for row in soup.find_all('tr', id=lambda x: x and x.startswith("eventRowId_")):
        # Extract eventid
        event_id = row['id'].replace('eventRowId_', '')

        # Extract event name
        event_name_tag = row.find('td', class_='left event')
        if event_name_tag:
            event_name = event_name_tag.get_text(strip=True)
            events[event_id] = event_name

    return events

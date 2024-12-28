import sys, asyncio
import websockets
import json
import threading
import streamlit as st
from src.investing_events import get_events
from playwright.async_api import async_playwright
import MetaTrader5 as mt5


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

dictionary = get_events()

# Placeholder values for MT5 global variable
MT5_VARIABLE_NAME = "event_triggered"
MT5_VARIABLE_VALUE = "True"

# Shared state for stopping the thread
stop_thread = threading.Event()

# Function to initialize MetaTrader 5
def initialize_mt5():
    if not mt5.initialize():
        st.error("Failed to initialize MT5:", mt5.last_error())
        return False
    st.success("MT5 initialized successfully.")
    return True

# Function to set a global variable in MT5
def set_mt5_global_variable(name, value):
    success = mt5.global_variables_set(name, value)
    if success:
        st.success(f"Global variable '{name}' set to '{value}' in MT5.")
    else:
        st.error("Failed to set global variable in MT5.")

# Original Function: Capture WebSocket URL and event IDs using Playwright
async def capture_websocket_and_eventids():
    event_ids = []  # This will store event IDs dynamically
    websocket_url = None

    async with async_playwright() as p:
        # Launch browser (Chromium)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Capture console logs
        def on_console(msg):
            nonlocal websocket_url, event_ids
            print(f"Console Message: {msg.text}")

            # Capture WebSocket URL from console logs
            if 'Opening transport: websocket  url:' in msg.text:
                websocket_url = msg.text.split("url:")[1].strip()

            # Capture event IDs from console logs
            if 'Subscribed socket to:' in msg.text:
                # Extracting event IDs dynamically
                parts = msg.text.split(":")
                for part in parts:
                    if part.strip():
                        event_ids.append(part.strip())

        # Listen for console logs
        page.on("console", on_console)

        # Go to the Investing.com Economic Calendar page
        await page.goto("https://uk.investing.com/economic-calendar/")

        # Wait for the WebSocket to establish (increase wait time if necessary)
        await page.wait_for_timeout(20000)  # Increase timeout to allow the WebSocket connection to appear

        # Close the browser
        await browser.close()

    return websocket_url, event_ids

# Original Function: Connect to WebSocket and monitor messages
async def connect_to_websocket(websocket_url, event_ids, target_event_id):
    # Remove the ':443' from the URL (if it exists)
    if ':443' in websocket_url:
        websocket_url = websocket_url.replace(':443', '').replace('https', 'wss') 
        websocket_url = (websocket_url.split(" "))[0] + "/websocket"
    print(f"WebSocket URL: {websocket_url}")

    # Prepare the message to subscribe to events
    event_ids_message = ":%%".join(event_ids)
    subscribe_message = {
        "_event": "bulk-subscribe",
        "tzID": 55,
        "message": event_ids_message + ":"
    }

    # Prepare the heartbeat message
    heartbeat_message = {
        "_event": "heartbeat",
        "data": "h"
    }

    async with websockets.connect(websocket_url) as websocket:
        print(f"Connected to WebSocket: {websocket_url}")

        # Send the subscription message
        await websocket.send(json.dumps(subscribe_message))
        print(f"Subscribed to events: {event_ids_message}")

        # Function to send heartbeat every 3 seconds
        async def send_heartbeat():
            while not stop_thread.is_set():
                await websocket.send(json.dumps(heartbeat_message))
                print("Heartbeat sent")
                await asyncio.sleep(3)  # Wait 3 seconds before sending the next heartbeat

        # Start sending heartbeats in the background
        asyncio.create_task(send_heartbeat())

        # Monitor messages for the target event
        while not stop_thread.is_set():
            message = await websocket.recv()
            print(f"Received message: {message}")
            if target_event_id in message:
                print(f"Target event {target_event_id} detected!")
                set_mt5_global_variable(MT5_VARIABLE_NAME, MT5_VARIABLE_VALUE)
                stop_thread.set()

# Wrapper Function: Run asyncio tasks in a thread
def run_async_tasks(target_event_id):
    asyncio.run(main(target_event_id))

# Main Function: Capture WebSocket URL and monitor for events
async def main(target_event_id):
    # Initialize MetaTrader 5
    if not initialize_mt5():
        return

    # Step 1: Capture WebSocket URL and event IDs
    print("Capturing WebSocket URL and Event IDs using Playwright...")
    websocket_url, event_ids = await capture_websocket_and_eventids()

    if not websocket_url or not event_ids:
        print("Failed to capture WebSocket URL or event IDs.")
        return

    print(f"Captured WebSocket URL: {websocket_url}")
    print(f"Captured Event IDs: {event_ids}")

    # Step 2: Connect to WebSocket and monitor for the target event
    await connect_to_websocket(websocket_url, event_ids, target_event_id)

# Start Monitoring: Run in a separate thread
def start_event_monitoring(target_event_id):
    stop_thread.clear()  # Reset the stop flag
    thread = threading.Thread(target=run_async_tasks, args=(target_event_id,), daemon=True)
    thread.start()
    st.success("Event monitoring started.")

# Stop Monitoring
def stop_event_monitoring():
    stop_thread.set()
    st.warning("Event monitoring stopped.")

# Streamlit UI
st.title("Economic Event Monitor with MT5 Integration")

# Input for target event ID
events = {(dictionary.get(key) + " - " + key):key for key in dictionary.keys()}

target_event = st.selectbox("Enter Target Event : ", options=list(events.keys()))


# Button to start monitoring
if st.button("Start Monitoring"):
    start_event_monitoring(events.get(target_event))

# Button to stop monitoring
if st.button("Stop Monitoring"):
    stop_event_monitoring()

import time
import os
import random
import argparse
from datetime import datetime, timezone
from dotenv import load_dotenv
from azure.iot.device import IoTHubDeviceClient, Message

# load environment config
load_dotenv()
CONNECTION_STRING1 = os.getenv("CONNECTION_STRING1")
CONNECTION_STRING2 = os.getenv("CONNECTION_STRING2")
CONNECTION_STRING3 = os.getenv("CONNECTION_STRING3")

# locations where IoT device should be placed
location_connection_strings = {
    "Dow's Lake": os.getenv("CONNECTION_STRING1"),
    "NAC": os.getenv("CONNECTION_STRING2"),
    "Fifth Avenue": os.getenv("CONNECTION_STRING3")
}

def get_data():
    """simulate IoT sensor"""
    return {
        "surfaceTemperature": round(random.uniform(-20, 0), 1),
        "externalTemperature": round(random.uniform(-25, 0), 1),
        "iceThickness": round(random.uniform(10, 50), 1),
        "snowAccumulation": round(random.uniform(0, 15), 1),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

def send_data(client, location):
    """send data to Azure IoT Hub"""
    data = get_data()
    data["location"] = location
    message = Message(str(data))
    client.send_message(message)
    print(f"Sent message from {location}: {message}")

def main(test_mode):
    if test_mode:
        print("Test mode enabled. Printing simulated data every 10 seconds...")
        try:
            while True:
                for location in location_connection_strings.keys():
                    data = get_data()
                    data["location"] = location
                    print(data)
                time.sleep(10)
        except KeyboardInterrupt:
            print("Test mode stopped.")
    else:
        # create clients for every location
        clients = {location: IoTHubDeviceClient.create_from_connection_string(conn_str)
                   for location, conn_str in location_connection_strings.items()}

        print("Sending data to IoT Hub...")
        try:
            while True:
                for location, client in clients.items():
                    send_data(client, location)
                time.sleep(10)
        except KeyboardInterrupt:
            print("Stopped sending messages.")
        finally:
            for client in clients.values():
                client.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IoT Hub Simulation")
    parser.add_argument("--test", action="store_true", help="Enable test mode to print simulated data")
    args = parser.parse_args()
    main(args.test)
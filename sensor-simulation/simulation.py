import time
from datetime import datetime, timezone
import random
from azure.iot.device import IoTHubDeviceClient, Message

CONNECTION_STRING = "Your IoT Hub device connection string here"

locations = ["Dow's Lake", "NAC", "Fifth Avenue"]

def get_telemetry():
    return {
        "surfaceTemperature": random.uniform(-5.0, 3.0),
        "externalTemperature": random.uniform(-20.0, 10.0),
        "location": random.choice(locations),
        "iceThickness": random.uniform(10, 40),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

def main():
    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

    print("Sending telemetry to IoT Hub...")
    try:
        while True:
            telemetry = get_telemetry()
            message = Message(str(telemetry))
            client.send_message(message)
            print(f"Sent message: {message}")
            time.sleep(10)
    except KeyboardInterrupt:
        print("Stopped sending messages.")
    finally:
        client.disconnect()

if __name__ == "__main__":
    # main()
    print(get_telemetry())
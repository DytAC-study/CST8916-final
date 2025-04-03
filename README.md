# Real-time Monitoring System for Rideau Canal Skateway

## **Scenario Description**:

The Rideau Canal Skateway in Ottawa is celebrated as the world's largest naturally frozen ice rink, attracting thousands of visitors each winter. Ensuring the safety of skaters on this 7.8-kilometer stretch requires continuous monitoring of ice conditions and environmental factors. Traditionally, assessments have relied on manual methods, such as drilling ice samples and visual inspections, which may not provide real-time data. To enhance safety measures, the National Capital Commission (NCC) has commissioned the development of an automated real-time monitoring system. This system aims to simulate IoT sensors at key locations along the canal to collect data on ice thickness, surface temperature, snow accumulation, and external temperature. The collected data will be processed in real-time to detect unsafe conditions promptly and stored in Azure Blob Storage for further analysis. By leveraging modern technology, this initiative seeks to improve the accuracy and timeliness of ice condition assessments, thereby enhancing the overall safety and experience of skaters on the Rideau Canal Skateway.



## **System Architecture**:

![](./diagram.png)



## **Implementation Details**:

- IoT Sensor Simulation:

  - There will be three sensors created in Azure IoT Hub, simulating captured signals of the environment. Our `simulation.py` script simulates data in the following JSON structure

    ```json
    {
        "surfaceTemperature": -5.3,
        "externalTemperature": -7.1,
        "iceThickness": 25.4,
        "snowAccumulation": 4.2,
        "humidity": 85,
        "location": "Dow's Lake",
        "timestamp": "2025-04-02T21:31:58Z"
    }
    ```

  - The Python script is coded like this, using the random module to randomly simulate temperature, ice thickness, and snow accumulation data. All the data range is based on the real-world situation:

    ```python
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
    ```

    

- Azure IoT Hub Configuration

  - The endpoints and message routing are left as default.

  - Create three sensors to simulate the sensors located in three parts of the Rideau River, and record their primary connection string:

    ```txt
    # sensor1
    CONNECTION_STRING1="HostName=RideauCanalSkateway.azure-devices.net;DeviceId=sensor1;SharedAccessKey=dTBr6UPeSN0efOfW4x0qJRfL9f7PiRU+ZjtM3j088u4="
    
    # sensor2
    CONNECTION_STRING2="HostName=RideauCanalSkateway.azure-devices.net;DeviceId=sensor2;SharedAccessKey=evABl/W7UfineBW5tStMGpHyVhSqCDcXi2vaIbhIpHU="
    
    # sensor3
    CONNECTION_STRING3="HostName=RideauCanalSkateway.azure-devices.net;DeviceId=sensor3;SharedAccessKey=55sdzzYaFAzgOrn2ROmDIdCcOdMQPevv+32mBPYr9dU="
    ```

    

- Azure Stream Analytics Job

  - Describe the job configuration, including input sources, query logic, and output destinations.

  - For the Stream Analytics Job configuration:

    - Inputs:
      - Input alias: RideauCanalSkateway (Select IoT Hub from your subscriptions)
      - IoT Hub: RideauCanalSkateway
      - Consumer group: $Default
      - Shared access policy name: iothubowner
      - Endpoint: Messaging
      - Partition key: location
      - Event serialization format: JSON
      - Encoding: UTF-8
      - Event compression type: None
    - Outputs:
      - Output alias: streameddata (Select IoT Hub from your subscriptions)
      - Storage account: rideaucanal
      - Container: Use existing (streameddata)
      - Authentication mode: Connection string
      - Event serialization format: JSON
      - Format: Line separated
      - Encoding: UTF-8
      - Write mode: Append
      - Path pattern: output/{date}/{time}/{location}
      - Date format: YYYY/MM/DD
      - Time format: HH

  - Query logic: calculate the average value of ice thickness, snow accumulation, external temperature, and group by device ID and location. Perform this query every 5 minutes.

  - Sample queries used for data processing.

    ```
    SELECT
        IoTHub.ConnectionDeviceId AS DeviceId,
        location,
        AVG(iceThickness) AS AvgIceThickness,
        AVG(snowAccumulation) AS AvgSnowAccumulation,
        AVG(externalTemperature) AS AvgExternalTemperature,
        AVG(surfaceTemperature) AS AvgSurfaceTemperature,
        System.Timestamp AS EventTime
    INTO
        streameddata
    FROM
        RideauCanalSkateway
    GROUP BY
        IoTHub.ConnectionDeviceId, location, TumblingWindow(second, 300)
    ```

- Azure Blob Storage

  - The processed data is stored in Blob Storage under the container streameddata, the folder structure is sorted by time, when creating Stream Analytics Job Output, we set the folder structure to `output/{date}/{time}/{location}`, then after processing, the data will be stored by time date and their location in that directory. 

    - Dow's Lake: streameddata / output / 2025 / 04 / 02 / 22 / Dow's%20Lake
    - Fifth Avenue: streameddata / output / 2025 / 04 / 02 / 22 / Fifth%20Avenue
    - NAC: streameddata / output / 2025 / 04 / 02 / 22 / NAC

  - format of stored processed data (JSON):

    ```json
    {
        "DeviceId":"sensor2",
        "location":"NAC",
        "AvgIceThickness":28.839999999999996,
        "AvgSnowAccumulation":8.239999999999998,
        "AvgExternalTemperature":-8.2,
        "AvgSurfaceTemperature":-9.68,
        "EventTime":"2025-04-02T21:06:00.0000000Z"
    }
    ```

    format of stored monitor data (JSON):

    ```json
    { 
        "count": 14, 
        "total": 0, 
        "minimum": 0, 
        "maximum": 0, 
        "average": 0, 
        "resourceId": "/SUBSCRIPTIONS/22F60889-0AD3-47D4-9D41-7D026E7FF990/RESOURCEGROUPS/CST8916-FINAL/PROVIDERS/MICROSOFT.STREAMANALYTICS/STREAMINGJOBS/ANALYTIC1", 
        "time": "2025-04-02T21:17:00.0000000Z", 
        "metricName": "OutputWatermarkDelaySeconds", 
        "timeGrain": "PT1M"
    }
    ```

    

## **Usage Instructions**:

### Running the IoT Sensor Simulation

- Provide step-by-step instructions for running the simulation script or application.

- This `simulation.py` python script for simulate real-time IoT sensor data is running under a Linux (Ubuntu) system, with Python3.x.

- Install Python 3. x and check Python version

  ```shell
  # install python3
  sudo apt-get update
  sudo apt-get install python3
  
  # check python version
  python3 --version
  ```

- Install and activate Python virtual environment

  ```shell
  # install virtual environment
  sudo apt install python3-venv
  
  # create virtual environment
  python3 -m venv venv
  
  # activate virtual environment
  source venv/bin/activate
  ```

- Install dependencies:

  ```shell
  pip3 install -r requirements.txt
  ```

- Create .env file under the root directory to hold `CONNECTION_STRING`:

  ```shell
  echo 'CONNECTION_STRING1="Your connection string for sensor1 to Azure IoT Hub"' > .env
  echo 'CONNECTION_STRING2="Your connection string for sensor2 to Azure IoT Hub"' >> .env
  echo '"CONNECTION_STRING3=Your connection string for sensor3 to Azure IoT Hub"' >> .env
  ```

- Run test to see if this script works. This will output simulation data to terminal. use Ctrl+C to stop the test:

  ```shell
  python3 sensor-simulation/simulation.py --test
  ```

- Run the python script to send a simulated data stream to Azure IoT Hub:

  ```shell
  python3 simulation.py
  ```

### Configuring Azure Services

The following are the steps which set up and run the IoT Hub and Stream Analytics job.

- **Create an IoT Hub**

  1. In the Azure Portal, create a new resource group for this project.
  2. Search for **IoT Hub** and click **Create**.
  3. Provide a name for IoT Hub (RideauCanalSkateway) and select a resource group (CST8916-Final).
  4. Choose the **Free Tier** for testing purposes and create the IoT Hub.

- Register Devices

  1. In the IoT Hub, go to the **Devices** section and click **Add Device**.
  2. Provide a Device ID (e.g., `sensor1`) and click **Save**. Add three devices to create sensors for every location.
  3. After the devices are created, click on them to view the connection string. Copy the connection string for use in the Python script that going to simulate the sensor. Add these connection strings to `.env` file.

- Run the python script to send data to Azure IoT Hub.

- **Create the Stream Analytics Job**

  1. In the Azure Portal, search for Stream Analytics jobs and click Create.
  2. Provide a name for your job (analytic1) and select the appropriate resource group (CST8916-Final).
  3. Choose Cloud as the hosting environment and create the job.

- Define Input

  1. In the Stream Analytics job, go to the Inputs section and click Add.
  2. Choose IoT Hub as the input source.
  3. Provide the following details:
     - IoT Hub Namespace: Select your IoT Hub.
     - IoT Hub Policy Name: Use the iothubowner policy.
     - Consumer Group: Use $Default or create a new consumer group in your IoT Hub.
     - Serialization Format: Choose JSON.

- Create a blob storage

  1. In the Azure Portal, search for Storage accounts and click Create.
  2. Properly set Resource group (CST8916-Final), Storage account name (rideaucanal), Region (Canada Central), Primary service (Azure Blob Storage), Redundancy (Locally-redundant storage), then Create.
  3. Under Data storage, choose Containers and create a new container to store processed data (streameddata) and another container to store raw data (rawdata).

- Define Output

  1. Go to the Outputs section and click Add.
  2. Choose Blob Storage as the output destination.
  3. Provide the following details:
     - Storage Account: Select your Azure Storage Account.
     - Container: Create or choose an existing container for storing results.
     - Path Pattern: Define a folder structure (output/{date}/{time}/{location}) to manage the output data.

- Write the Stream Analytics Query

  Go to the Query tab and replace the default query with the following:

  ```
  SELECT
      IoTHub.ConnectionDeviceId AS DeviceId,
      location,
      AVG(iceThickness) AS AvgIceThickness,
      AVG(snowAccumulation) AS AvgSnowAccumulation,
      AVG(externalTemperature) AS AvgExternalTemperature,
      AVG(surfaceTemperature) AS AvgSurfaceTemperature,
      System.Timestamp AS EventTime
  INTO
      streameddata
  FROM
      RideauCanalSkateway
  GROUP BY
      IoTHub.ConnectionDeviceId, location, TumblingWindow(second, 300)
  ```

- Save and Start the Job

  Save the query and click Start on the Stream Analytics job.

- Set up Diagnostic setting for this analytics job. Monitor the Stream Analytics Job Navigate to the Monitoring tab of the job to view metrics and ensure data is being processed.

### Accessing Stored Data

- Check Blob Storage
  - Go to the Azure Storage Account.
  - Navigate to the container (streameddata) specified in the output.
  - The processed data is being stored inside streameddata/output/YYYY/MM/DD/HH/location.
  - The monitor data is being stored inside the insights-metrics directory (mine is insights-metrics-pt1m).
  - Verify that processed data is being stored in JSON format. (download and check).

## **Results**:

- **Key Findings:**

  - We could seed the average ice thickness, snow accumulation, external temperature, and surface temperature from each sensor. For instance:

    ```
    {"DeviceId":"sensor2","location":"NAC","AvgIceThickness":27.27142857142857,"AvgSnowAccumulation":7.964285714285715,"AvgExternalTemperature":-11.571428571428573,"AvgSurfaceTemperature":-9.028571428571428,"EventTime":"2025-04-02T23:00:00.0000000Z"}
    ```

    - DeviceId: sensor2
    - location: NAC
    - Average Ice Thickness: 27.3 cm
    - Average Snow Accumulation: 7.9 cm
    - Average External Temperature: -11.6°C
    - Average Surface Temperature: -9.0°C

  - These metrics provide insights into the overall conditions monitored during the simulation, helping us analyze the trend to review and forecast the weather conditions for each location.

- **Reference Sample Output Files:**

  - This is the storage file stored in Azure Blob Storage for NAC. (If this link is not accessible, it means I deleted the resource to save credits.)

    - Blob SAS URL：

    https://rideaucanal.blob.core.windows.net/streameddata/output/2025/04/02/23/NAC/0_17138e35107a487e9f19a4eac7bb5763_1.json?sp=r&st=2025-04-02T23:58:13Z&se=2025-04-03T07:58:13Z&spr=https&sv=2024-11-04&sr=b&sig=dqawiHfugH5mqF8wULaYkx2GWHGIazLbJMNxxfc%2FkVE%3D

  - Sample files can be accessed at this GitHub repo under `sampleOutput/`.

    

## **Reflection**:

- **Challenges Faced:**
  - *Data Quality and Integration:*
    - Ensuring the simulated data accurately reflected real-world conditions was challenging. Inconsistent or unrealistic data could damage the validity of the simulation.
    - *Path pattern set:* It needs a lot of adjustments to decide how to set the path pattern, making the processed data easy to locate.
  - *System Performance*:
    - Handling and processing large volumes of data in real-time posed performance issues.
    - *Solution:* Optimized the data processing pipeline by implementing efficient data structures and algorithms, and utilized Azure's scalable resources to manage load effectively.
- **Lessons Learned:**
  - The importance of thoroughly testing the simulation code to meet the project's needs.
  - The importance of the configuration of the path pattern of the output data, mak the results easy to locate and has clear directory structure for users.
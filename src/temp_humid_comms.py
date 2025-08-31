import requests
import json
import time
import os
import csv
from datetime import datetime, timedelta

# ========== CONFIGURATION ==========
EMAIL = "tempsensor78@gmail.com"
PASSWORD = os.getenv("SENSORPUSH_PASSWORD")  # Load password from environment variable

if PASSWORD is None:
    raise ValueError("Environment variable SENSORPUSH_PASSWORD is not set!")

BASE_URL = "https://api.sensorpush.com/api/v1"

LOG_FILE_PREFIX = "./sensor_data_"
QUERY_INTERVAL_MIN = 5        # How often to query samples (in minutes)
REAUTH_INTERVAL_MIN = 60      # Reauthorize every 60 minutes
DUPLICATE_CHECK_ROWS = 50     # Check last m rows in log file for duplicates
SAMPLE_LIMIT = 50             # Number of samples per query
# ====================================


def authorize(email, password):
    url = os.path.join(BASE_URL, "oauth/authorize")
    payload = {"email": email, "password": password}
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    auth_code = response.json().get("authorization")
    print(f"[{datetime.now()}] [+] Authorization code received")
    return auth_code

def get_access_token(auth_code):
    url = os.path.join(BASE_URL, "oauth/accesstoken")
    payload = {"authorization": auth_code}
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    access_token = response.json().get("accesstoken")
    print(f"[{datetime.now()}] [+] Access token received")
    return access_token


def list_gateways(access_token):
    url = os.path.join(BASE_URL, "devices/gateways")
    headers = {"accept": "application/json", "Authorization": access_token}
    payload = {}
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def list_sensors(access_token):
    url = os.path.join(BASE_URL, "devices/sensors")
    headers = {"accept": "application/json", "Authorization": access_token}
    payload = {}
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def query_samples_advanced(access_token, sensors, start_time, stop_time, limit=10000):
    url = os.path.join(BASE_URL, "samples")
    headers = {"accept": "application/json", "Authorization": access_token}
    payload = {
        "sensors": sensors,
        "limit": limit,
        "startTime": start_time,
        "stopTime": stop_time
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

"""
def get_last_logged_ids(n_rows):
    if not os.path.exists(LOG_FILE):
        return set()
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()[-n_rows:]
    ids = set()
    for line in lines:
        try:
            record = json.loads(line.strip())
            if "observed" in record:
                ids.add(record["observed"])
        except json.JSONDecodeError:
            continue
    return ids
"""

# def append_new_samples(samples):
#     if not samples.get("sensors"):
#         return 0
#     new_count = 0
#     with open(LOG_FILE, "a") as f:
#         for sensor_id, data_list in samples["sensors"].items():
#             for data in data_list:
#                 data_with_id = data.copy()
#                 data_with_id["sensor_id"] = sensor_id
#                 f.write(json.dumps(data_with_id) + "\n")
#                 new_count += 1
#     return new_count

def fahrenheit_to_celsius(temp_f):
    temp_c = (temp_f - 32)*5/9
    return temp_c

def append_new_samples(samples, sensor_id, log_file):
    if not samples.get("sensors"):
        return 0

    file_exists = os.path.isfile(log_file)
    new_count = 0

    with open(log_file, "a", newline="") as f:
        writer = None

        for sensor_id, data_list in samples["sensors"].items():
            for data in data_list:
                # Prepare the full record
                record = {
                    "sensor_id": float(sensor_id),
                    "temperature C": float(round(fahrenheit_to_celsius(data['temperature']), 1)),
                    "dewpoint C": float(round(fahrenheit_to_celsius(data["dewpoint"]), 1)),
                    "humidity": float(data["humidity"]),
                    "vpd": float(data["vpd"]),
                }

                # Initialize CSV writer with headers if the file is new
                if writer is None:
                    writer = csv.DictWriter(f, fieldnames=record.keys())
                    if not file_exists:
                        writer.writeheader()

                writer.writerow(record)
                new_count += 1

    return new_count





if __name__ == "__main__":
    print("[+] Starting SensorPush data logger...")
    next_auth_time = time.time()
    access_token = None

    while True:
        # Reauthorize every REAUTH_INTERVAL_MIN
        if time.time() >= next_auth_time or not access_token:
            try:
                auth_code = authorize(EMAIL, PASSWORD)
                access_token = get_access_token(auth_code)
                # TODO: use timedelta here
                next_auth_time = time.time() + (REAUTH_INTERVAL_MIN * 60)
            except Exception as e:
                print(f"[!] Authorization failed: {e}")
                time.sleep(60)
                continue
        
        # Get last DUPLICATE_CHECK_ROWS rows from log
        # existing_ids = get_last_logged_ids(DUPLICATE_CHECK_ROWS)

        # Query new samples
        try:
            sensors = list_sensors(access_token)
            sensor_ids = list(sensors.keys())
            sensor_names = [sensors[sid]['name'] for sid in sensor_ids]
            print(sensor_names)

            time_now = datetime.now()
            time_ret = datetime.now().astimezone() - timedelta(minutes=2*QUERY_INTERVAL_MIN)
            start_time = time_ret.strftime("%Y-%m-%dT%H:%M:%S%z")
            stop_time = datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")

            for sensor_id in sensor_ids:
                sensor_name = sensors[sensor_id]['name']
                log_file = LOG_FILE_PREFIX+sensor_name+'.csv'
                samples = query_samples_advanced(
                    access_token,
                    sensors=sensor_ids,
                    start_time=start_time,
                    stop_time=stop_time
                        )
                added = append_new_samples(samples, sensor_id, log_file)# , existing_ids)
                print(f"[{datetime.now()}] [+] Retrieved {added} new samples for sensor in {sensor_name}")
        except Exception as e:
            print(f"[!] Failed to query samples: {e}")

        # Wait before next query
        time.sleep(QUERY_INTERVAL_MIN * 60)





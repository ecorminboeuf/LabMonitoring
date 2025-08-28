
# %% 
import requests
import json
import os
from datetime import datetime, timedelta

# Base URL
BASE_URL = "https://api.sensorpush.com/api/v1"

# Replace with your SensorPush credentials
EMAIL = "tempsensor78@gmail.com"
PASSWORD = "perplexed shaping snowdrop swizzle"

def authorize(email, password):
    url = os.path.join(BASE_URL, "oauth/authorize")
    payload = {"email": email, "password": password}
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    auth_code = response.json().get("authorization")
    print("[+] Authorization code received")
    return auth_code

def get_access_token(auth_code):
    url = f"{BASE_URL}/oauth/accesstoken"
    payload = {"authorization": auth_code}
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    access_token = response.json().get("accesstoken")
    print("[+] Access token received")
    return access_token


def list_gateways(access_token):
    url = f"{BASE_URL}/devices/gateways"
    headers = {"accept": "application/json", "Authorization": access_token}
    payload = {}
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def list_sensors(access_token):
    url = f"{BASE_URL}/devices/sensors"
    headers = {"accept": "application/json", "Authorization": access_token}
    payload = {}
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def query_samples(access_token, limit=20):
    url = f"{BASE_URL}/samples"
    headers = {"accept": "application/json", "Authorization": access_token}
    payload = {"limit": limit}
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def query_samples_advanced(access_token, sensors, start_time, stop_time, limit=10000):
    url = f"{BASE_URL}/samples"
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


#%%

# Step 1: Get authorization code
auth_code = authorize(EMAIL, PASSWORD)

# Step 2: Get access token
access_token = get_access_token(auth_code)

# Step 3: List gateways
gateways = list_gateways(access_token)
print("[+] Gateways:", json.dumps(gateways, indent=2))


# %%
# Step 4: List sensors
sensors = list_sensors(access_token)
# print("[+] Sensors:", json.dumps(sensors, indent=2))

sensor_ids = list(sensors.keys())
sensor_names = [sensors[sid]['name'] for sid in sensor_ids]
refresh_rate_m = 60

# Step 5: Query samples
# samples = query_samples(access_token, limit=20)
# print("[+] Samples:", json.dumps(samples, indent=2))

# Step 6: Query samples for specific sensors and time range (example)
# Replace with actual sensor IDs and time range if needed
time_now = datetime.now()
time_ret = datetime.now().astimezone() - timedelta(minutes=refresh_rate_m)
start_time = time_ret.strftime("%Y-%m-%dT%H:%M:%S%z")
stop_time = datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")

advanced_samples = query_samples_advanced(
    access_token,
    sensors=sensor_ids,
    start_time=start_time,
    stop_time=stop_time
        )
    # print("[+] Advanced Samples:", json.dumps(advanced_samples, indent=2))

# %%

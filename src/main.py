from dotenv import dotenv_values, load_dotenv
import requests
import base64
import asyncio

# Load .env
load_dotenv(dotenv_path="../.env")
dotenv_variables = dotenv_values("../.env")

# Fetch environment variables
REFRESH_TOKEN = dotenv_variables.get('REFRESH_TOKEN')
CLIENT_ID = dotenv_variables.get("CLIENT_ID")
CLIENT_SECRET = dotenv_variables.get("CLIENT_SECRET")
PLAYBACK_DEVICE_NAME = dotenv_variables.get("PLAYBACK_DEVICE_NAME")

# Continue Scanning until a card is detected
def scan():
    return None

# Use refresh token to retrieve new access token
async def get_access_token():
    endpoint = "https://accounts.spotify.com/api/token"
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }
    response = requests.post(endpoint, headers=headers, data=data)
    if response.status_code == 200:
        new_access_token = response.json().get("access_token")
        print("Generated new access token")
        return new_access_token
    else:
        print(f"Failed to refresh access token: {response.status_code}, {response.json()}")
        return None

# Find playback device, in this case Raspberry PI
async def get_playback_device(access_token):
    playback_device = None
    endpoint = "https://api.spotify.com/v1/me/player/devices"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200:
        devices = response.json().get("devices", [])    
        if not devices:
            print("No active devices found.")

        for device in devices:
            if device['name'] == PLAYBACK_DEVICE_NAME:
                print("Device found.")
                playback_device = device['id']
                break
                
        if not playback_device:
            print("Cannot find device with specified name.")

        return playback_device
    else:
        print(f"Error fetching devices: {response.status_code}, {response.json()}")
        return None
    
    #return "8628d334-bfba-414f-8c9b-fd025046f74b_amzn_1"

# Function to play a specific track
async def play_album(access_token, album_uri, device_id=None):
    endpoint = "https://api.spotify.com/v1/me/player/play"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    body = {
        "context_uri": album_uri
    }

    if device_id:
        endpoint += f"?device_id={device_id}"
    
    response = requests.put(endpoint, json=body, headers=headers)
    
    if response.status_code == 204:
        print("Album started playing!")
    else:
        print(f"Failed to play album: {response.status_code}, {response.json()}")


# On Load generate a new access token
access_token = asyncio.run(get_access_token())

# Example usage
# Todo use scan function to get album_uri
album_uri = "spotify:album:1vhib5WLHRVdOpRjiTHk15"          # Stranger In Town - Bob Seger
device_id = asyncio.run(get_playback_device(access_token))

# play album is an async function
asyncio.run(play_album(access_token, album_uri, device_id))


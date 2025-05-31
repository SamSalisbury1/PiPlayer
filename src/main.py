import requests
import base64
import asyncio
import re
import RPi.GPIO as GPIO
import pn532.pn532 as nfc
from pn532 import *
from dotenv import dotenv_values, load_dotenv

# Load .env
load_dotenv(dotenv_path="../.env")
dotenv_variables = dotenv_values("../.env")

# Fetch environment variables
REFRESH_TOKEN = dotenv_variables.get('REFRESH_TOKEN')
CLIENT_ID = dotenv_variables.get("CLIENT_ID")
CLIENT_SECRET = dotenv_variables.get("CLIENT_SECRET")
PLAYBACK_DEVICE_NAME = dotenv_variables.get("PLAYBACK_DEVICE_NAME")

# UART connection
pn532 = PN532_UART(debug=False, reset=20)

# Configure PN532 to communicate with MiFare cards
pn532.SAM_configuration()

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

# Scan until card is detected
print("Listening! Please present card")
while True:
    # Check if a card is available to read
    uid = pn532.read_passive_target(timeout=0.5)
    print('.', end="")
    
    # Try again if no card is available.
    if uid is not None:
        break

print('Found card with UID:', [hex(i) for i in uid])

# Set key
key_a = b'\xFF\xFF\xFF\xFF\xFF\xFF'
data_blocks = []

for x in range (2):
    # We need blocks one and two so increment index
    index = x + 1
    
    # Authenticate and read block
    pn532.mifare_classic_authenticate_block(uid, block_number=index, key_number=nfc.MIFARE_CMD_AUTH_A, key=key_a)
    block = pn532.mifare_classic_read_block(index)
    
    # Filter block and append to list
    block =  block.replace(b'\x00', b'').decode('utf-8')
    data_blocks.append(block)

# Append blocks 1 and 2 
card_data = data_blocks[0] + data_blocks[1] # Assume we always read two blocks
album_uri = "spotify:album:" + card_data
device_id = asyncio.run(get_playback_device(access_token))

# play album is an async function
asyncio.run(play_album(access_token, album_uri, device_id))


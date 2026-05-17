import base64
import vlc
import time
import glob
import RPi.GPIO as GPIO
import pn532.pn532 as nfc
from pn532 import *
from natsort import natsorted

# UART connection
pn532 = PN532_UART(debug=False, reset=20)

# Configure PN532 to communicate with MiFare cards
pn532.SAM_configuration()

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
album_name = data_blocks[0] + data_blocks[1] # Assume we always read two blocks

# Get all songs in album - Order them into queue
mp3_files = list(
    glob.iglob('../albums/'+ album_name +'/*.mp3')
)
sorted_mp3_files = natsorted(mp3_files)

# Play queue
for mp3 in sorted_mp3_files:
    # Play song
    p = vlc.MediaPlayer(mp3)
    p.play()
    
    # Let vlc start
    time.sleep(5)
    
    # Keep programming running
    while p.is_playing():
        time.sleep(0.1)
    
print("Album finished!")



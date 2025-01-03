"""
Warning: DO NOT write the blocks of 4N+3 (3, 7, 11, ..., 63)
or else you will change the password for blocks 4N ~ 4N+2.

Note: 
1.  The first 6 bytes (KEY A) of the 4N+3 blocks are always shown as 0x00,
since 'KEY A' is unreadable. In contrast, the last 6 bytes (KEY B) of the 
4N+3 blocks are readable.
2.  Block 0 is unwritable. 
"""
import sys
import re
import RPi.GPIO as GPIO

import pn532.pn532 as nfc
from pn532 import *

# We need two arguments, script name and album URI
arguments = sys.argv
if len(arguments) != 2:
    print("Error: Incorrect number of arguments provided. Expected single album URI after script name.")
    sys.exit()

# Ensure that argument matches regex for valid spotify album
uri = arguments[1]
pattern = r"^spotify:album:[a-zA-Z0-9]+$"
if not re.match(pattern, uri):
    print("Error: This appears to be an invalid album uri. Regex validation failed")
    sys.exit()
    
# Ensure that album_id does not exceed max data size
album_id = uri.split("spotify:album:")[1]
max_id_length = 32
if len(album_id) > max_id_length:
    print("Error: URI ID is too long! Max size of 32 characters.")
    sys.exit()
    
# Encode album_id into byte array so it can be written to card
encoded_album_id = album_id.encode("utf-8").hex()

# Blocks can only hold 16 bytes each, uri is encoded into hexadecimal, 16 byte cut off is at index 32
indices = [32]

# Use list comprhension and slicing to split encoded_album_id into two blocks
data_blocks = [encoded_album_id[start:end] for start, end in zip([0] + indices, indices + [None])]

print('Successfully encoded album URI')

pn532 = PN532_UART(debug=False, reset=20)

ic, ver, rev, support = pn532.get_firmware_version()
print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))

# Configure PN532 to communicate with MiFare cards
pn532.SAM_configuration()

print('Waiting for RFID/NFC card to write to!')

while True:
    # Check if a card is available to read
    uid = pn532.read_passive_target(timeout=0.5)
    print('.', end="")
    # Try again if no card is available.
    if uid is not None:
        break

print('Found card with UID:', [hex(i) for i in uid])

try:
    # Set key, set block number to 1. We set to 1 as block 0 is read only.
    key_a = b'\xFF\xFF\xFF\xFF\xFF\xFF'
    block_number = 1
    
    for block in data_blocks:
        # Every 2 characters represents a byte, we need an array of bytes so split substring on every second charcter
        n = 2
        byte_array = [block[i:i+n] for i in range(0, len(block), n)]
        
        # Convert the hexadecimal pairs into actual byte values
        data = bytes([int(byte, 16) for byte in byte_array])
        
         # If the data is less than 16 bytes, extend it with 0x00 to make it exactly 16 bytes
        if len(data) < 16:
            data = data + bytes(16 - len(data))  # Append 0x00 bytes to make the length 16
    
        pn532.mifare_classic_authenticate_block(uid, block_number=block_number, key_number=nfc.MIFARE_CMD_AUTH_A, key=key_a)
        pn532.mifare_classic_write_block(block_number, data)
    
        if pn532.mifare_classic_read_block(block_number) == data:
            print('write block %d successfully' % block_number)
            
        # Increment block number
        block_number +=1
        
    print("WRITE SUCCESSFUL! Please remove card!")
          
except nfc.PN532Error as e:
    print(e.errmsg)

GPIO.cleanup()

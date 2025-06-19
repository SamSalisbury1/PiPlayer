import sys
import re
import RPi.GPIO as GPIO

import pn532.pn532 as nfc
from pn532 import *

# We need two arguments, script name and album name
arguments = sys.argv
if len(arguments) != 2:
    print("Error: Incorrect number of arguments provided. Expected album name after script name. If album name contains spaces please do not type them.")
    sys.exit()

# Ensure that argument matches regex for valid spotify album
album_name = arguments[1]

# Ensure that album_id does not exceed max data size
max_length = 32
if len(album_name) > max_length:
    print("Error: Album name is too long! Max size of 32 characters. Consider giving it a different name.")
    sys.exit()
    
# Encode album_id into byte array so it can be written to card
encoded_album_id = album_name.encode("utf-8").hex()

# Blocks can only hold 16 bytes each, album name is encoded into hexadecimal, 16 byte cut off is at index 32
indices = [32]

# Use list comprhension and slicing to split encoded_album_id into two blocks
data_blocks = [encoded_album_id[start:end] for start, end in zip([0] + indices, indices + [None])]

print('Successfully encoded album name')


# UART connection
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
            print('Write block %d successfully' % block_number)
            
        # Increment block number
        block_number +=1
        
    print("WRITE SUCCESSFUL! Please remove card!")
          
except nfc.PN532Error as e:
    print(e.errmsg)

GPIO.cleanup()

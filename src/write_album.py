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
data = album_id.encode("utf-8").hex()
print("Encoded Data is: " + data)

# If over 16 bytes split into two blocks
# Populate remeinder of second block with 00

sys.exit() # remove once finished writing validation code

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

# Stranger in the Night - Bob Seger
# Block 5: 31 76 68 69 62 35 57 4c 48 52 56 64 4f 70 52 6a
# Block 6: 69 54 48 6b 31 35 00 00 00 00 00 00 00 00 00 00

try:
    key_a = b'\xFF\xFF\xFF\xFF\xFF\xFF'
    
    # Write Block #5
    block_number = 5
    data = bytes([0x31, 0x76, 0x68, 0x69, 0x62, 0x35, 0x57, 0x4c, 0x48, 0x52, 0x56, 0x64, 0x4f, 0x70, 0x52, 0x6a])
    
    pn532.mifare_classic_authenticate_block(uid, block_number=block_number, key_number=nfc.MIFARE_CMD_AUTH_A, key=key_a)
    pn532.mifare_classic_write_block(block_number, data)
    
    if pn532.mifare_classic_read_block(block_number) == data:
        print('write block %d successfully' % block_number)
    
    # Write block #6
    block_number = 6
    data = bytes([0x69, 0x54, 0x48, 0x6b, 0x31, 0x35, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    
    pn532.mifare_classic_authenticate_block(uid, block_number=block_number, key_number=nfc.MIFARE_CMD_AUTH_A, key=key_a)
    pn532.mifare_classic_write_block(block_number, data)
    
    
    if pn532.mifare_classic_read_block(block_number) == data:
        print('write block %d successfully' % block_number)
          
except nfc.PN532Error as e:
    print(e.errmsg)

GPIO.cleanup()



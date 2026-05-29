#import base64
import vlc
import time
import glob
from natsort import natsorted
import curses
#import RPi.GPIO as GPIO
#import pn532.pn532 as nfc
#from pn532 import *

"""
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
"""

# Delete before commit
album_name = "Test"

# Get all songs in album - Order them into queue
mp3_files = list(
    glob.iglob('../albums/'+ album_name +'/*.mp3')
)
playlist = natsorted(mp3_files)

current_track = 0

player = vlc.MediaPlayer(playlist[current_track])
player.play()

paused = False

# Set up input
screen = curses.initscr()
curses.cbreak()
screen.keypad(True)

try:
    while True:
        key = screen.getch()

        if key == 10: # Enter
            if paused:
                player.pause()
                paused = False

            else:
                player.pause()
                paused = True

        elif key == curses.KEY_LEFT:   
            # If over 5 seconds has elapsed restart the song otherwise go to previous track
            if player.get_time() > 5000:
                player.set_time(0)
                continue

            # To Previous Track
            player.stop()

            current_track -= 1

            if current_track < 0:
                current_track = 0
            
            player = vlc.MediaPlayer(
                playlist[current_track]
            )

            player.play()

        elif key == curses.KEY_RIGHT:
            player.stop()

            current_track += 1

            if current_track >= len(playlist):
                screen.addstr("Album finished!")
                break

            player = vlc.MediaPlayer(
                playlist[current_track]
            )

            player.play()

        elif key == curses.KEY_DOWN:
            break

finally:
    curses.nocbreak()
    screen.keypad(False)
    curses.echo()
    curses.endwin()

print("Playback ended!")


# handle_scan()

# handle_pause()

# handle_back()

# handle_forward()

# handle_shutdown()

# handle_quit()

# update_state(state)

# album = handle_scan()
# album.play()

# while true:
    # Read controls and perform desired action
    # Render UI (clear everything and output global variables)

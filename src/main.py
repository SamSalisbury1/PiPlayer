import base64
import vlc
import glob
from natsort import natsorted
import curses
import RPi.GPIO as GPIO
import pn532.pn532 as nfc
from pn532 import *
from pathlib import Path
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ALBUMS_DIR = ROOT_DIR / "albums"

class Context:
    def __init__(self, initial_state, player, nfc_reader):
        self.state = None
        
        self.player = player
        self.nfc_reader = nfc_reader

        self.set_state(initial_state)

    # -------------------------
    # State Management
    # -------------------------

    def set_state(self, new_state):
        self.state = new_state
        self.state.enter(self)

    # -------------------------
    # State Behaviour
    # -------------------------

    def handle_key(self, key):
        self.state.handle_key(self, key)

    def handle_nfc(self, album_name):
        self.state.handle_nfc(self, album_name)

    def tick(self):
        self.state.tick(self)

    # -------------------------
    # Player Helpers
    # -------------------------

    def load_album(self, album_name):
        self.player.load_album(album_name)
    
    def unload_album(self):
        self.player.unload_album()

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    def next_track(self):
        self.player.next_track()

    def previous_track(self):
        self.player.previous_track()

    def has_song_ended(self):
        return self.player.has_song_ended()
    
    # -------------------------
    # NFC Helpers
    # -------------------------
    
    def poll(self):
        return self.nfc_reader.poll()

    # -------------------------
    # Getters
    # -------------------------

    def get_state_name(self):
        return self.state.get_state_name()
    
    def get_playlist(self):
        return self.player.get_playlist()
    
    def get_current_track(self):
        return self.player.get_current_track()


class State:
    def enter(self, context):
        """
        We call this when the state becomes active
        Use this when we want to start scanning, playing etc...
        """
        pass

    def handle_key(self, context, key):
        """
        Handle keyboard input
        """
        pass

    def handle_nfc(self, context, nfc_reader):
        """
        Handle NFC events
        """
        pass
    
    def tick(self, context):
        """
        Handle state specific actions during main loop
        """
        pass

    def get_state_name(self):
        """
        Debug function
        """
        pass


class Playing(State):
    def enter(self, context):
        context.play()

    def handle_key(self, context, key):
        if key == "ENTER":
            context.set_state(Paused())
        elif key == "LEFT":
            context.previous_track()
            context.play()
        elif key == "RIGHT":
            has_next = context.get_current_track() < len(context.get_playlist()) - 1
            if has_next: 
                context.next_track()
                context.play()
            else:
                context.set_state(Stopped())
        elif key == "UP":
            context.set_state(Scanning())
        elif key == "DOWN":
            context.set_state(Stopped())
            
    def tick(self, context):
        # If song has ended play the next track unless there is no next track in which case enter Stopped State
        if context.has_song_ended():
            has_next = context.get_current_track() < len(context.get_playlist()) - 1

            if has_next: 
                context.next_track()
                context.play()
            else:
                context.set_state(Stopped())

    def get_state_name(self):
        return "Playing"


class Paused(State):
    def enter(self, context):
        context.pause()

    def handle_key(self, context, key):
        if key == "ENTER":
            context.set_state(Playing())
        elif key == "LEFT":
            context.previous_track()
        elif key == "RIGHT":
            has_next = context.get_current_track() < len(context.get_playlist()) - 1
            if has_next: 
                context.next_track()
            else:
                context.set_state(Stopped())
        elif key == "UP":
            context.set_state(Scanning())
        elif key == "DOWN":
            context.set_state(Stopped())

    def get_state_name(self):
        return "Paused"


class Scanning(State):
    def enter(self, context):
        context.stop()
        context.unload_album()

    def handle_key(self, context, key):
        if key == "DOWN":
            context.set_state(Stopped())
    
    def handle_nfc(self, context, album_name):
        context.load_album(album_name)
        context.set_state(Playing())
        
    def tick(self, context):
        # Scan for NFC tag - Once found load and play
        if context.get_state_name() == "Scanning":
            album_name = context.poll()
            
            if album_name is not None:
                context.handle_nfc(album_name)

    def get_state_name(self):
        return "Scanning"


class Stopped(State):
    def enter(self, context):
        context.stop()
        context.unload_album()

    def handle_key(self, context, key):
        if key == "UP":
            context.set_state(Scanning())

    def get_state_name(self):
        return "Stopped"


class Player:
    def __init__(self):
        self.playlist = []
        self.current_track = 0
        self.player = None

    def load_album(self, album_name):
        # Get all songs in album - Order them into queue
        album_path = ALBUMS_DIR / album_name
        mp3_files = list(album_path.glob("*.mp3"))

        self.playlist = natsorted(mp3_files)
        self.current_track = 0
        self.player = vlc.MediaPlayer(
            self.playlist[self.current_track]
        )
        
    def unload_album(self):
        if self.playlist != []:
            self.playlist = []

    def play(self):
        if self.player:
            self.player.play()

    def pause(self):
        if self.player:
            self.player.pause()

    def stop(self):
        if self.player:
            self.player.stop()

    def next_track(self):
        self.stop()

        self.current_track += 1

        self.player = vlc.MediaPlayer(
            self.playlist[self.current_track]
        )

    def previous_track(self):
        # If over 5 seconds has elapsed restart the song otherwise go to previous track
        if self.player and self.player.get_time() > 5000:
            self.player.set_time(0)
            return

        # To Previous Track if we are on first track then restart first track
        self.stop()

        self.current_track -= 1

        if self.current_track < 0:
            self.current_track = 0
            
        self.player = vlc.MediaPlayer(
            self.playlist[self.current_track]
        )

    def has_song_ended(self):
        return ( self.player and self.player.get_state() == vlc.State.Ended )

    def get_playlist(self):
        return self.playlist

    def get_current_track(self):
        return self.current_track


class NFCReader:
    def __init__(self):
        # UART connection
        self.pn532 = PN532_UART(debug=False, reset=20)

        # Configure PN532 to communicate with MiFare cards
        self.pn532.SAM_configuration()
    
    def poll(self):
        # Check if a card is available to read
        uid = self.pn532.read_passive_target(timeout=0.5)
        
        if uid is None:
            return None
        
        # If so we attempt to read it
        try:
            # Set key
            key_a = b'\xFF\xFF\xFF\xFF\xFF\xFF'
            data_blocks = []

            for x in range (2):
                # We need blocks one and two so increment index
                index = x + 1
        
                # Authenticate and read block
                self.pn532.mifare_classic_authenticate_block(uid, block_number=index, key_number=nfc.MIFARE_CMD_AUTH_A, key=key_a)
                block = self.pn532.mifare_classic_read_block(index)
        
                # Filter block and append to list
                block =  block.replace(b'\x00', b'').decode('utf-8')
                data_blocks.append(block)

            # Append blocks 1 and 2 
            album_name = data_blocks[0] + data_blocks[1] # Assume we always read two blocks
            return album_name
        except:
            return None


def format_playlist(current_track, playlist):
    # Build output string from extracted file names in playlist - Highlight current track
    playlist_output = ""
    for index, song in enumerate(playlist):
        song_path = Path(song)
        formatted_song = song_path.stem

        if (index == current_track):
            formatted_song = "> " + formatted_song + " <"

        playlist_output += formatted_song + "\n"

    return playlist_output


def build_output(app, confirmation_action):
    # Return confirmation message if confirmation action is active
    if confirmation_action is not None:
        confirmation_action_output = ""
        if confirmation_action == "QUIT":
            confirmation_action_output = "quit"
        elif confirmation_action == "SHUTDOWN":
            confirmation_action_output = "shut down"
            
        return "Are you sure you want to " + confirmation_action_output + " [Y / N]"
    
    # Get app state - Add it to output
    state = app.get_state_name()
    output = state + "\n"

    # Stopped and Scanning states do not have playlists so output instructions
    if state == "Stopped":
        return output + "No album loaded. Press the up arrow to scan for an album"
    elif state == "Scanning":
        return output + "Please tap a card to load an album"
    
    # Get playlist - highlight current track - amend to output
    current_track = app.get_current_track()
    playlist = app.get_playlist()
    playlist_output = format_playlist(current_track, playlist) if playlist != [] else "No playlist found!"

    return output + playlist_output


def print_output(screen, output):
    # Clear screen, set output variables and transform output string into array
    screen.clear()
    max_y, max_x = screen.getmaxyx()
    lines = (output).split("\n")
    
    # Abort output if if output exceeds terminal size to prevent crashing.
    for i, line in enumerate(lines):
        if i >= max_y -1:
            break
        screen.addstr(i, 0, line[:max_x -1])

    screen.refresh()


def handle_output(app, screen, confirmation_action, previous_output):
    # Build output based on app state and whether a confirmation action has been chosen
    output = build_output(app, confirmation_action)

    # Do not unecessarily re-render - only render if output has been changed since last render
    if output != previous_output:
        print_output(screen, output)

    return output


def handle_action_input(app, key):
    confirmation_action = None

    if key == 10:
        app.handle_key("ENTER")
    elif key == curses.KEY_LEFT:
        app.handle_key("LEFT")
    elif key == curses.KEY_RIGHT:
        app.handle_key("RIGHT")
    elif key == curses.KEY_UP:
        app.handle_key("UP")
    elif key == curses.KEY_DOWN:
        app.handle_key("DOWN")
    elif key == ord("q") or key == ord("Q"):
        confirmation_action = "QUIT"
    elif key == curses.KEY_DC:
        confirmation_action = "SHUTDOWN"
    
    return confirmation_action


def handle_confirmation_input(key, confirmation_action):
    # If is "yes" continue with now confirmed action
    if key == ord("y") or key == ord("Y"):
        if confirmation_action == "QUIT":
            confirmation_action = "QUIT_CONFIRMED"
        elif confirmation_action == "SHUTDOWN":
            confirmation_action = "SHUTDOWN_CONFIRMED"

    # Otherwise reset confirmation_action to none
    elif key == ord("n") or key == ord("N"):
        confirmation_action = None
    else:
        pass    # Print bad input

    return confirmation_action


def system_shutdown():
    import subprocess
    subprocess.run(["sudo", "shutdown", "-h", "now"])


def main(screen):
    # Initialise application
    curses.cbreak()
    screen.keypad(True)
    curses.noecho()

    # Enable non-blocking input
    screen.nodelay(True)

    # Initialise classes
    player = Player()
    nfc_reader = NFCReader()
    app = Context(Stopped(), player, nfc_reader)

    # Used to handle special cases in app such as Quit and Shut Down - confirmation_action used by handle_output() to render action confirmation screen 
    confirmation_action = None
    shutdown_type = None

    # Store previous output to conditionally render UI if change is made - This stops UI flicker
    previous_output = None

    # Main loop
    running = True
    while running:
        key = screen.getch()

        # If input detected handle it
        if key != -1:
            if confirmation_action is None:
                confirmation_action = handle_action_input(app, key)
            else:
                confirmation_action = handle_confirmation_input(key, confirmation_action)
                
                if confirmation_action in ("QUIT_CONFIRMED", "SHUTDOWN_CONFIRMED"):
                    running = False
                    shutdown_type = confirmation_action
                    
        app.tick()

        # Build output based on state of app / confirmation_action and print
        previous_output = handle_output(app, screen, confirmation_action, previous_output)

    # If shutdown system if user wishes otherwise just let execution end
    if shutdown_type == "SHUTDOWN_CONFIRMED":
        system_shutdown()

curses.wrapper(main)

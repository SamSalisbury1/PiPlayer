#import base64
import vlc
import glob
from natsort import natsorted
import curses
#import RPi.GPIO as GPIO
#import pn532.pn532 as nfc
#from pn532 import *
from pathlib import Path
import time


class Context:
    def __init__(self, initial_state, player, nfc):
        self.state = None
        
        self.player = player
        self.nfc = nfc

        self.set_state(initial_state)

    # -------------------------
    # State Management
    # -------------------------

    def set_state(self, new_state):
        if self.state is not None:
            self.state.exit(self)
            
        self.state = new_state
        self.state.enter(self)

    # -------------------------
    # Input Management
    # -------------------------

    def handle_key(self, key):
        self.state.handle_key(self, key)

    def hanfle_nfc(self, nfc):
        self.state.handle_nfc(nfc)

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

    def exit(self, context):
        """
        We call this when we leave the state
        Use this for cleanup when needed
        """
        pass

    def handle_key(self, context, key):
        """
        Handle keyboard input
        """
        pass

    def handle_nfc(self, context, nfc):
        """
        Handle NFC events
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
    
    def exit(self, context):
        """
        Ignore
        """
        pass

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

    def get_state_name(self):
        return "Playing"


class Paused(State):
    def enter(self, context):
        context.pause()

    def exit(self, contex):
        """
        Ignore
        """
        pass

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
        #context.nfc.scan()
        context.load_album("Test")
        context.set_state(Playing())

    def exit(self, context):
        pass

    def handle_key(self, context, key):
        pass

    def get_state_name(self):
        return "Scanning"


class Stopped(State):
    def enter(self, context):
        context.stop()
        context.unload_album()

    def exit(self, context):
        pass

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
        mp3_files = list(
            glob.iglob('../albums/'+ album_name +'/*.mp3')
        )

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
    def scan(self):
        pass


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
        return "Are you sure you want to " + confirmation_action + " [Y / N]"
    
    # If user is not performing a confirmation action build playback UI
    state = app.get_state_name()
    current_track = app.get_current_track()
    playlist = app.get_playlist()

    playlist_output = format_playlist(current_track, playlist) if playlist != [] else "No album loaded. Press the up arrow to scan for an album"
    output = state + "\n" + playlist_output

    return output


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
    
    return confirmation_action


def handle_confirmation_input(key, confirmation_action):
    # If is "yes" continue with now confirmed action
    if key == ord("y") or key == ord("Y"):
        if confirmation_action == "QUIT":
            confirmation_action = "QUIT_CONFIRMED"
        elif confirmation_action == "SHUTDOWN":
            pass    # Shutdown - Do nothing right now, I do not want to test this yet

    # Otherwise reset confirmation_action to none
    elif key == ord("n") or key == ord("N"):
        confirmation_action = None
    else:
        pass    # Print bad input

    return confirmation_action


def main(screen):
    # Initialise application
    curses.cbreak()
    screen.keypad(True)
    curses.noecho()

    # Enable non-blocking input
    screen.nodelay(True)

    # Initialise classes
    player = Player()
    nfc = NFCReader()
    app = Context(Stopped(), player, nfc)

    # Used to handle special cases in app such as Quit and Shut Down - Used by handle_output() to render action confirmation screen 
    confirmation_action = None

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
                
                if confirmation_action == "QUIT_CONFIRMED":
                    running = False

        # If song has ended play the next track unless there is no next track in which case enter Stopped State
        if app.has_song_ended():
            has_next = app.get_current_track() < len(app.get_playlist()) - 1

            if has_next: 
                app.next_track()
                app.play()
            else:
                app.set_state(Stopped())

        # Build output based on state of app / confirmation_action and print
        previous_output = handle_output(app, screen, confirmation_action, previous_output)


curses.wrapper(main)

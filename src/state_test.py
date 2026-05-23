#import base64
import vlc
import glob
from natsort import natsorted
import curses
#import RPi.GPIO as GPIO
#import pn532.pn532 as nfc
#from pn532 import *
import pdb

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


    def get_state_name(self):
        return self.state.get_state_name()


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
            has_next = context.player.current_track < len(context.player.playlist) - 1
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
            has_next = context.player.current_track < len(context.player.playlist) - 1
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
        context.player.load_album("Hoist")
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


class NFCReader:
    def scan(self):
        pass


def main(screen):
    curses.cbreak()
    screen.keypad(True)
    curses.noecho()

    player = Player()
    nfc = NFCReader()
    
    app = Context(Stopped(), player, nfc)

    while True:
        key = screen.getch()

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

        state = app.get_state_name()
        screen.clear()
        screen.addstr(0, 0, state)
        screen.refresh()

curses.wrapper(main)
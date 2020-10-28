import json
import threading
import time
import pyautogui
import requests
import sys
from win10toast import ToastNotifier

from rich import print
from rich.style import Style
from rich.table import Table

###

DEBUG_COLORS = False
DEBUG_REQUESTS = True

###


def samecolor(c1, c2, t=20):
    return (abs(c1[0]-c2[0])+abs(c1[1]-c2[1])+abs(c1[2]-c2[2])) <= t

def firstmatchingcolor(c1, cs, t=20):
    for c in cs:
        if samecolor(c1, c[0], t):
            return c[1]
    return None

def matchesonecolor(c1, cs, t=10):
    for c in cs:
        if samecolor(c1, c, t):
            return True
    return False

def log(*args, **kwargs):
    print("[AmongUs Tracker] -", *args, *kwargs)

###

_X1 = 340
_X2 = 995
_Y = 265
_DY = 137

COORDS_M_PLAYERS = [
    (_X1, _Y+0*_DY),
    (_X1, _Y+1*_DY),
    (_X1, _Y+2*_DY),
    (_X1, _Y+3*_DY),
    (_X1, _Y+4*_DY),
    (_X2, _Y+0*_DY),
    (_X2, _Y+1*_DY),
    (_X2, _Y+2*_DY),
    (_X2, _Y+3*_DY),
    (_X2, _Y+4*_DY),
]

_DCX = 0
_DCY = -25

COORDS_M_PLAYERS = [
    (c, (c[0]+_DCX, c[1]+_DCY)) 
    for c in COORDS_M_PLAYERS
]

###

_ORIGINAL_AMONGUS_COLORS = {
    'red':      ("#C51111", (179, 17, 17),   ":heart:",                 '❤'),
    'blue':     ("#132FD2", (19, 47, 210),   ":blue_heart:",            '💙'),
    'green':    ("#127F2D", (18, 127, 45),   ":green_heart:",           '💚'),
    'pink':     ("#ED53B9", (237, 83, 185),  ":heartpulse:",            '💗'),
    'orange':   ("#EF7D0E", (239, 125, 14),  ":orange_heart:",          '🧡'),
    'yellow':   ("#F3F558", (243, 246, 88),  ":yellow_heart:",          '💛'),
    'black':    ("#3F484E", (63, 72, 78),    ":black_heart:",           '🖤'),
    'white':    ("#D5E0EF", (213, 224, 239), ":white_heart:",           '🤍'),
    'purple':   ("#6B30BC", (107, 48, 188),  ":purple_heart:",          '💜'),
    'brown':    ("#72491E", (114, 37, 30),   ":brown_heart:",           '🤎'),
    'cyan':     ("#39FEDB", (57, 254, 219),  ":regional_indicator_c:",  '🇨'),
    'lime':     ("#50EF3A", (80, 239, 58),   ":regional_indicator_l:",  '🇱'),
}

COLORS_M_ALIVE = [(108, 137, 151), (155, 205, 225)]
COLORS_M_DEAD = [(131, 69, 58)]
COLORS_M_NOPLAYER = [(171, 201, 229), (187, 211, 237)]

COLORS_M_PLAYERS = [
    # Grayed out
    ((125, 57, 64), "red"),
    ((54, 72, 146), "blue"),
    ((50, 103, 76), "green"),
    ((146, 88, 137), "pink"),
    ((145, 106, 67), "orange"),
    ((145, 152, 94), "yellow"),
    ((73, 82, 92), "black"),
    ((136, 146, 159), "white"),
    ((87, 70, 135), "purple"),
    ((96, 83, 71), "brown"),
    ((66, 156, 149), "cyan"),
    ((80, 153, 84), "lime"),

    # Light
    ((192, 62, 72), "red"),
    ((61, 89, 214), "blue"),
    ((60, 150, 89), "green"),
    ((225, 115, 202), "pink"),
    ((225, 144, 65), "orange"),
    ((229, 232, 125), "yellow"),
    ((91, 103, 117), "black"),
    ((208, 221, 240), "white"),
    ((125, 86, 195), "purple"),
    ((134, 106, 82), "brown"),
    ((91, 242, 227), "cyan"),
    ((107, 232, 102), "lime"),

    # While dead
    ((109, 9, 9), "red"),
    ((10, 25, 116), "blue"),
    ((9, 71, 25), "green"),
    ((130, 55, 108), "pink"),
    ((168, 88, 9), "orange"),
    ((136, 136, 48), "yellow"),
    ((35, 39, 43), "black"),
    ((119, 124, 133), "white"),
    ((59, 26, 104), "purple"),
    #(, "brown"),
    ((31, 141, 122), "cyan"),
    ((47, 140, 33), "lime"),
]

###

COORDS_DISCUSS = ((800, 800), (950, 800), (1100, 800))
COLORS_DISCUSS = ((251, 123, 0), (171, 238, 83), (23, 121, 2))

COORDS_DEFEAT = ((910, 165), (10, 10), (1910, 10))
COLORS_DEFEAT = ((254, 0, 5), (0, 0, 0), (0, 0, 0))

COORDS_VICTORY = ((960, 167), (10, 10), (1910, 10))
COLORS_VICTORY = ((0, 139, 255), (0, 0, 0), (0, 0, 0))

COORDS_MEETING = ((1615, 380), (1615, 760), (1500, 975))
COLORS_MEETING = ((143, 151, 164), (143, 151, 164), (171, 201, 229))

COORDS_SHHHHHHH = ((1120, 630), (1320, 590), (1300, 450))
COLORS_SHHHHHHH = ((198, 0, 1), (255, 129, 52), (255, 213, 77))

COORDS_CHAT = ((1500, 1000), (1000, 1000))
COLORS_CHAT = ((255, 255, 255), (255, 255, 255))

###

toaster = ToastNotifier()
toast = toaster.show_toast

###

class AmongUsTracker():
    def __init__(self, url: str, id: int, apikey: str):
        self.url = url
        self.id = id
        self.apikey = apikey

        self.topleft = (0, 0)
        self.size = tuple(pyautogui.size())

        self.last_state = "unknown"

    # Post data

    def _post(self, data, **kwargs):
        try:
            data = {
                "id": self.id,
                "api_key": self.apikey,
                **data,
                **kwargs
            }

            if DEBUG_REQUESTS:
                print("Post data:", data)

            r = requests.post(url=self.url, json=json.dumps(data))
            j = r.json()

            if "success" in j:
                log("Successfully posted data to server!")
            elif "error" in j:
                log("Error received from server:", j["error"] + (" - "+j["error_message"] if "error_message" in j else ""))
                if j["error"] == "invalid-api-key":
                    toast(title="[AmongUsTracker] Error!",
                          msg="Invalid API-Key! Please check your API key!")
                    sys.exit()
                elif j["error"] == "id-not-found":
                    toast(title="[AmongUsTracker] Error!",
                          msg="ID not found! Please check that your ID is correct!")
                    sys.exit()
                elif j["error"] == "invalid-data":
                    log("THIS IS A BUG!")
        except ConnectionError as e:
            log("ConnectionError:", e)
            toast(title="[AmongUsTracker] Error!",
                  msg="A ConnectionError occured! Please check your connection!")
        except ValueError as e:
            log("ValueError:", e)
            toast(title="[AmongUsTracker] Error!",
                  msg="Didn't receive a valid response! Are you sure the url is correct?")

    def post(self, data={}, **kwargs):
        thread = threading.Thread(target=self._post, args=(data,), kwargs=kwargs)
        thread.start()
        log("Posting in background...")

    # Detect state

    def _compare_coord_colors(self, coordlist, colorlist, screenshot=None, debugtitle=""):
        if screenshot is None:
            screenshot = pyautogui.screenshot(region=(*self.topleft, *self.size))

        colors = tuple(screenshot.getpixel(c) for c in coordlist)

        same = True
        for i in range(len(colors)):
            if not samecolor(colors[i], colorlist[i], 20):
                same = False
                break

        if DEBUG_COLORS:
            print(debugtitle, same, colors, colorlist)

        return same

    def _is_discuss_screen(self, screenshot=None):
        return self._compare_coord_colors(COORDS_DISCUSS, COLORS_DISCUSS, screenshot, "Discuss")

    def _is_defeat_screen(self, screenshot=None):
        return self._compare_coord_colors(COORDS_DEFEAT, COLORS_DEFEAT, screenshot, "Defeat")

    def _is_victory_screen(self, screenshot=None):
        return self._compare_coord_colors(COORDS_VICTORY, COLORS_VICTORY, screenshot, "Victory")

    def _is_end_screen(self, screenshot=None):
        return self._is_defeat_screen(screenshot) or self._is_victory_screen(screenshot)

    def _is_shhhhhhh_screen(self, screenshot=None):
        return self._compare_coord_colors(COORDS_SHHHHHHH, COLORS_SHHHHHHH, screenshot, "Shhhhhhh")

    def _is_meeting_screen(self, screenshot=None):
        return self._compare_coord_colors(COORDS_MEETING, COLORS_MEETING, screenshot, "Meeting")

    def _is_textbox_open(self, screenshot=None):
        return self._compare_coord_colors(COORDS_CHAT, COLORS_CHAT, screenshot, "Chat")

    def _get_state(self):
        im = pyautogui.screenshot(region=(*self.topleft, *self.size))
        
        if self._is_textbox_open(im):
            return self.last_state
        elif self._is_discuss_screen(im):
            return "discuss"
        elif self._is_meeting_screen(im):
            return "meeting"
        elif self._is_end_screen(im):
            return "end"
        elif self._is_shhhhhhh_screen(im):
            return "start"
        else:
            return "unknown"

    def _get_meeting_players(self):
        im = pyautogui.screenshot(region=(*self.topleft, *self.size))

        players = {}
        for i in range(len(COORDS_M_PLAYERS)):
            coords = COORDS_M_PLAYERS[i]
            c1 = im.getpixel(coords[0])
            if not matchesonecolor(c1, COLORS_M_NOPLAYER):
                c2 = im.getpixel(coords[1])
                color = firstmatchingcolor(c2, COLORS_M_PLAYERS, 50)
                if color is not None:
                    if matchesonecolor(c1, COLORS_M_ALIVE, 50):
                        players[color] = {
                            "exists": True,
                            "alive": True,
                        }
                    elif matchesonecolor(c1, COLORS_M_DEAD, 50):
                        players[color] = {
                            "exists": True,
                            "alive": False,
                        }
                    else:
                        print(f"[AmongUs Tracker] - Unknown state for {i+1}/10 - {color}: {c1}")
                else:
                    print(f"[AmongUs Tracker] - Unknown color for {i+1}/10: {c2}")
        return players

    # Actions

    def post_meeting_players(self):
        data = {
            "state": {
                "ingame": True,
                "meeting": True
            },
            "players": self._get_meeting_players(),
        }
        self.post(data)
        
    def post_reset(self):
        self.post({"reset": True})

    def post_ingame(self, **kwargs):
        self.post({"state": {"ingame": True, "meeting": False}}, **kwargs)

    def post_state(self):
        state = self._get_state()
        oldstate = self.last_state

        self.last_state = state

        if not oldstate == state:
            if state == "end":
                log("Game ended!")
                self.post_reset()
                toast(title="[AmongUsTracker] Game ended!",
                      msg="Successfully detected game end!",
                      threaded=True, duration=2)
            elif state == "start":
                log("Game started!")
                self.post_ingame(reset=True)
                toast(title="[AmongUsTracker] Game started!",
                      msg="Successfully detected game start!", 
                      threaded=True, duration=2)
            elif state == "discuss":
                log("Meeting starts soon!")
            elif state == "meeting":
                log("Meeting started!")
                time.sleep(0.2)
                self.post_meeting_players()
            elif oldstate == "meeting":
                log("Meeting ended!")
                self.post_ingame()
            else:
                print(f"[AmongUs Tracker] - State changed to {state}!")

    # Mainloop

    def main(self, speed=0.05):
        self._post({"test": True})

        log("Started tracking!")

        while True:
            self.post_state()
            time.sleep(speed)

if __name__ == "__main__":
    URL = "http://localhost/discordbot/amongus/tracker/post"
    ID = 16
    API_KEY = "2d8f5dd5-275b-411b-b302-f55919867ee9"

    tracker = AmongUsTracker(url=URL, id=ID, apikey=API_KEY)
    tracker.main(speed=0.1)

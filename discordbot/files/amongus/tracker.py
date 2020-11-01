# 2020 - Rafael Urben
# https://github.com/rafaelurben/django-discordbot/tree/master/discordbot/files/amongus

import json
import threading
import time
import pyautogui
import requests
import sys
from win10toast import ToastNotifier

from rich import print
from rich.table import Table
from rich.text import Text
from rich.style import Style

###

DEBUG_COORD_COLOR_COMPARISON = False
DEBUG_MEETING_COLORS = True
DEBUG_REQUESTS = False

IGNORE_CONNECTION_ERRORS = True

###

_X1 = 340
_X2 = 995
_Y = 265
_DY = 137

PLAYERCOORDS = [
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
    for c in PLAYERCOORDS
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

PLAYERCOLORS = {
    "red": [
        (125, 57, 64),
        (192, 62, 72),
        (109, 9, 9),
        (198, 17, 17),
        (81, 21, 22),
    ],
    "blue": [
        (54, 72, 146),
        (61, 89, 214),
        (10, 25, 116),
        (25, 28, 95),
        (19, 46, 210),
    ],
    "green": [
        (50, 103, 76),
        (60, 150, 89),
        (9, 71, 25),
        (17, 128, 45),
    ],
    "pink": [
        (146, 88, 137),
        (225, 115, 202),
        (130, 55, 108),
        (238, 84, 187),
    ],
    "orange": [
        (145, 106, 67),
        (225, 144, 65),
        (168, 88, 9),
        (241, 125, 14),
        (133, 69, 7),
    ],
    "yellow": [
        (145, 152, 94),
        (229, 232, 125),
        (136, 136, 48),
        (246, 246, 87),
        (104, 106, 47),
    ],
    "black": [
        (73, 82, 92),
        (91, 103, 117),
        (35, 39, 43),
        (62, 71, 78),
        (68, 81, 89)
    ],
    "white": [
        (136, 146, 159),
        (208, 221, 240),
        (119, 124, 133),
    ],
    "purple": [
        (86, 70, 135),
        (125, 86, 195),
        (59, 26, 104),
        (107, 47, 188),
    ],
    "brown": [
        (96, 83, 71),
        (134, 106, 82),
        (114, 73, 29),
        (62, 40, 17),
    ],
    "cyan": [
        (66, 156, 149),
        (91, 242, 227),
        (31, 141, 122),
        (56, 255, 221),
    ],
    "lime": [
        (80, 153, 84),
        (107, 232, 102),
        (47, 140, 33),
        (104, 233, 106),
        (40, 104, 36),
        (78, 233, 55),
    ],
}

COLORS_M_ALIVE = [(108, 137, 151), (155, 205, 225), (82, 112, 122)]
COLORS_M_DEAD = [(131, 69, 58), (116, 25, 4), (99, 31, 8), (82, 112, 122)]
COLORS_M_NOPLAYER = [(171, 201, 229), (187, 211, 237), (156, 183, 209)]

COLORS_M_PLAYERS = [(color, c) for c, colors in PLAYERCOLORS.items() for color in colors]


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

COORDS_CHAT = ((1300, 913), (1100, 913), (1364, 913))
COLORS_CHAT = ((255, 255, 255), (255, 255, 255), (2, 113, 228))

COORDS_HOMESCREEN = ((779, 989), (1148, 977))
COLORS_HOMESCREEN = ((232, 240, 242), (85, 102, 102))

COORDS_HOMESCREEN2 = ((194, 1013), (532, 282))
COLORS_HOMESCREEN2 = ((255, 255, 255), (52, 68, 95))

###

toaster = ToastNotifier()
toast = toaster.show_toast

###


def render(obj):
    if isinstance(obj, bool):
        return Text("True", style="green") if obj else Text("False", style="red")
    elif obj is None:
        return Text("None", style="blue")
    else:
        return str(obj)


def log(*args, **kwargs):
    print("[AmongUs Tracker] -", *args, *kwargs)


###


def samecolor(c1, c2, maxdiff=20):
    diff = (abs(c1[0]-c2[0])+abs(c1[1]-c2[1])+abs(c1[2]-c2[2]))
    return True if diff == 0 else diff if diff < maxdiff else False


def bestmatchingcolor(c1, cs, maxdiff=20):
    best_c = None
    best_diff = None

    for c in cs:
        diff = samecolor(c1, c[0], maxdiff)
        if diff == True:
            return c[1]
        elif bool(diff) and (best_diff is None or diff < best_diff):
            best_c = c[1]
            best_diff = diff
    return best_c


def matchesonecolor(c1, cs, maxdiff=10):
    for c in cs:
        if samecolor(c1, c, maxdiff):
            return True
    return False


###

class AmongUsTracker():
    def __init__(self, url: str, id: int, apikey: str):
        self.url = url
        self.id = id
        self.apikey = apikey

        self.topleft = (0, 0)
        self.size = tuple(pyautogui.size())

        self.last_state = "unknown"

    @property
    def screenshot(self):
        return pyautogui.screenshot(region=(*self.topleft, *self.size))

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
                print("[DEBUG] - POST Data:", data)

            r = requests.post(url=self.url, json=json.dumps(data))
            j = r.json()

            if "success" in j:
                log("POST - Successfully posted data to server!")
            elif "error" in j:
                log("POST - Error received from server:", j["error"] + (" - "+j["error_message"] if "error_message" in j else ""))
                if j["error"] == "invalid-api-key":
                    toast(title="[AmongUsTracker] Error!",
                          msg="Invalid API-Key! Please check your API key!")
                    sys.exit()
                elif j["error"] == "id-not-found":
                    toast(title="[AmongUsTracker] Error!",
                          msg="ID not found! Please check that your ID is correct!")
                    sys.exit()
                elif j["error"] == "invalid-data":
                    log("POST - THIS MIGHT BE A SERVER-SIDE BUG!")
        except (ConnectionError, requests.exceptions.ConnectionError) as e:
            log("POST - ConnectionError:", e)
            if not IGNORE_CONNECTION_ERRORS:
                toast(title="[AmongUsTracker] Error!",
                    msg="A ConnectionError occured! Please check your connection!")
                sys.exit()
        except ValueError as e:
            log("POST - ValueError:", e)
            toast(title="[AmongUsTracker] Error!",
                  msg="Didn't receive a valid response! Are you sure the url is correct?")
            sys.exit()

    def post(self, data={}, **kwargs):
        thread = threading.Thread(target=self._post, args=(data,), kwargs=kwargs)
        thread.start()
        log("POST - Posting in background...")

    # Detect state

    def _compare_coord_colors(self, coordlist, colorlist, screenshot=None, debugtitle="", maxdiff=20):
        screenshot = screenshot or self.screenshot

        colors = tuple(screenshot.getpixel(c) for c in coordlist)

        same = True
        for i in range(len(colors)):
            if not bool(samecolor(colors[i], colorlist[i], maxdiff)):
                same = False
                break

        if DEBUG_COORD_COLOR_COMPARISON:
            print(debugtitle, same, colors, colorlist)

        return same

    def _is_discuss_screen(self, screenshot=None):
        return self._compare_coord_colors(COORDS_DISCUSS, COLORS_DISCUSS, screenshot, "Discuss")

    def _is_defeat_screen(self, screenshot=None):
        return self._compare_coord_colors(COORDS_DEFEAT, COLORS_DEFEAT, screenshot, "Defeat")

    def _is_victory_screen(self, screenshot=None):
        return self._compare_coord_colors(COORDS_VICTORY, COLORS_VICTORY, screenshot, "Victory")

    def _is_homescreen(self, screenshot=None):
        return (self._compare_coord_colors(COORDS_HOMESCREEN, COLORS_HOMESCREEN, screenshot, "Homescreen") or 
                self._compare_coord_colors(COORDS_HOMESCREEN2, COLORS_HOMESCREEN2, screenshot, "Homescreen 2"))

    def _is_end_screen(self, screenshot=None):
        return self._is_defeat_screen(screenshot) or self._is_victory_screen(screenshot) or self._is_homescreen(screenshot)

    def _is_shhhhhhh_screen(self, screenshot=None):
        return self._compare_coord_colors(COORDS_SHHHHHHH, COLORS_SHHHHHHH, screenshot, "Shhhhhhh")

    def _is_meeting_screen(self, screenshot=None):
        return self._compare_coord_colors(COORDS_MEETING, COLORS_MEETING, screenshot, "Meeting")

    def _is_chat_open(self, screenshot=None):
        return self._compare_coord_colors(COORDS_CHAT, COLORS_CHAT, screenshot, "Chat")

    def _get_state(self, screenshot=None):
        screenshot = screenshot or self.screenshot
        
        if self._is_chat_open(screenshot):
            return "chat"
        elif self._is_homescreen(screenshot):
            return "homescreen"
        elif self._is_discuss_screen(screenshot):
            return "discuss"
        elif self._is_meeting_screen(screenshot):
            return "meeting"
        elif self._is_end_screen(screenshot):
            return "end"
        elif self._is_shhhhhhh_screen(screenshot):
            return "start"
        else:
            return "unknown"

    def _get_meeting_players(self, screenshot=None):
        screenshot = screenshot or self.screenshot

        error = False
        
        colors = []
        for i in range(len(COORDS_M_PLAYERS)):
            coords = COORDS_M_PLAYERS[i]

            c_state = screenshot.getpixel(coords[0])
            alive = matchesonecolor(c_state, COLORS_M_ALIVE, 50)
            dead = matchesonecolor(c_state, COLORS_M_DEAD, 50)
            inexistant = matchesonecolor(c_state, COLORS_M_NOPLAYER, 10)

            c_color = screenshot.getpixel(coords[1])
            color = bestmatchingcolor(c_color, COLORS_M_PLAYERS, 25)

            colors.append({
                "i": i+1,
                "c_state": c_state, 
                "alive": True if alive else False if dead else None, 
                "exists": False if inexistant else True if (alive or dead) else None, 
                "c_color": c_color, 
                "color": color,
            })

            if not inexistant and not alive and not dead:
                error = True

        players = {}
        for p in colors:
            color, alive = p["color"], p["alive"]
            if color is not None:
                if color in players:
                    error = True
                    
                if alive == True:
                    players[color] = {
                        "exists": True,
                        "alive": True,
                    }
                elif alive == False:
                    players[color] = {
                        "exists": True,
                        "alive": False,
                    }

        if DEBUG_MEETING_COLORS:
            tb = Table("i", "cs", "c_state", "exists", "alive", "cc", "c_color", "color")
            for p in colors:
                tb.add_row(
                    render(p["i"]),
                    Text("  ", style=Style(bgcolor="rgb"+str(p["c_state"]))),
                    render(p["c_state"]),
                    render(p["exists"]),
                    render(p["alive"]),
                    Text("  ", style=Style(bgcolor="rgb"+str(p["c_color"]))),
                    render(p["c_color"]),
                    render(p["color"]),
                ) 
            print(tb)

        if error:
            log("MEETING PLAYERS - Skipping due to possibly corrupted screenshot!")
            return None
        else:
            log("MEETING PLAYERS - Detected probably valid playerdata.")
            return players

    # Actions

    def post_meeting_players(self, screenshot=None):
        players = self._get_meeting_players(screenshot)
        if players is not None:
            data = {
                "state": {
                    "ingame": True,
                    "meeting": True
                },
                "players": players,
            }
            self.post(data)
            return True
        return False
        
    def post_reset(self):
        self.post({"reset": True})

    def post_ingame(self, **kwargs):
        self.post({"state": {"ingame": True, "meeting": False}}, **kwargs)

    def post_state(self):
        screenshot = self.screenshot

        state = self._get_state(screenshot)
        oldstate = self.last_state

        self.last_state = state

        if not oldstate == state:
            if state == "chat":
                log("STATE - Chat opened...")
            elif state == "end":
                log("STATE - Game ended!")
                self.post_reset()
                toast(title="[AmongUsTracker] Game ended!",
                      msg="Successfully detected game end!",
                      threaded=True, duration=2)
            elif state == "homescreen":
                log("STATE - Home screen detected! (Reset)")
                self.post_reset()
            elif state == "start":
                log("STATE - Game started!")
                self.post_ingame(reset=True)
                toast(title="[AmongUsTracker] Game started!",
                      msg="Successfully detected game start!", 
                      threaded=True, duration=2)
            elif state == "discuss":
                log("STATE - Meeting starts soon!")
            elif state == "meeting":
                log("STATE - Meeting started!")
                time.sleep(0.5)
                if not self.post_meeting_players(self.screenshot):
                    if not self.post_meeting_players(screenshot):
                        self.last_state = oldstate
            else:
                if oldstate in ["meeting", "chat"]:
                    log("STATE - Meeting ended! (Sleep 6s)")
                    time.sleep(6)
                    self.post_ingame()
                elif oldstate in ["end", "homescreen"]:
                    self.last_state = oldstate
                else:
                    log(f"STATE - State changed to {state}!")

    # Mainloop

    def main(self, speed=0.05):
        self.post_reset()

        log("TRACKER - Started tracking!")

        while True:
            self.post_state()
            time.sleep(speed)

if __name__ == "__main__":
    URL = "https://rafaelurben.herokuapp.com/discordbot/amongus/tracker/post"
    ID = 0
    API_KEY = ""

    try:
        tracker = AmongUsTracker(url=URL, id=ID, apikey=API_KEY)
        tracker.main(speed=0.1) 
    except KeyboardInterrupt:
        log("KeyboardInterrupt")

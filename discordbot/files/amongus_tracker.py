import requests
import json

###

class AmongUsTracker():
    def __init__(self, url, apikey=None):
        self.url = url
        self.apikey = apikey

    def _post(self, data):
        try:
            r = requests.post(url=self.url, json=json.dumps({
                "api_key": self.apikey,
                **data
            }))
            j = r.json()
            if "success" in j:
                print("[AmongUs Tracker] - Successfully posted data to server!")
                return True
            else:
                print("[AmongUs Tracker] - Error received from server:", (" - " + j["error"] if "error" in j else "") + (" - MSG: "+j["error_message"] if "error_message" in j else ""))
                return False
        except ConnectionError as e:
            print("[AmongUs Tracker] - ConnectionError:", e)


# Test

URL = "http://localhost/discordbot/amongus/tracker/13/post"
API_KEY = "10d20528-ccca-4ba2-9332-7bf38bf0538f"

AmongUsTracker(url=URL, apikey=API_KEY)._post({
    "state": {"ingame": False, "meeting": False},
    "code": "123456"
})

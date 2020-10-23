import requests
import json

URL = "http://localhost/discordbot/amongus/tracker/13/post"
API_KEY = "10d20528-ccca-4ba2-9332-7bf38bf0538f"

def post(data):
    r = requests.post(url=URL, json=json.dumps({
        "api_key": API_KEY,
        **data
    }))
    j = r.json()
    if "success" in j:
        return True
    else:
        print("[AmongUs Tracker] Error!", (" - " + j["error"] if "error" in j else "") + (" - MSG: "+j["error_message"] if "error_message" in j else ""))
        return False

post({
    "state": {"ingame": False},
    "code": "123456"
})

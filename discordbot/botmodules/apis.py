from discord.ext import commands
import requests, datetime, base64, os


class Minecraft():
    @classmethod
    def getProfile(self, NAME:str):
        r = requests.get('https://api.mojang.com/users/profiles/minecraft/'+NAME)
        if not r.status_code == 204:
            return r.json()
        else:
            raise commands.BadArgument(message="Spieler wurde nicht gefunden!")

    @classmethod
    def getProfiles(self, UUID:str):
        r = requests.get('https://api.mojang.com/user/profiles/'+str(UUID)+'/names')
        if not r.status_code == 204:
            data = r.json()
            for i in data:
                if "changedToAt" in i:
                    i["changedToAt"] = datetime.datetime.fromtimestamp(int(i["changedToAt"])/1000)
            return data
        else:
            raise commands.BadArgument(message="UUID wurde nicht gefunden!")

    @classmethod
    def getSkin(self, UUID:str):
        r = requests.get('https://sessionserver.mojang.com/session/minecraft/profile/'+str(UUID))
        if not r.status_code == 204:
            data = r.json()
            if not "error" in data:
                ppty = data["properties"][0]
                base64_message = ppty["value"]
                base64_bytes = base64_message.encode('ascii')
                message_bytes = base64.b64decode(base64_bytes)
                message = message_bytes.decode('ascii')
                dictmessage = eval(message)
                if not dictmessage["textures"] == {}:
                    skinurl = dictmessage["textures"]["SKIN"]["url"]
                    data["skin"] = skinurl
                else:
                    data["skin"] = None
                data.pop("properties")
                return data
            else:
                raise commands.BadArgument(message="Abfrage für einen Skin kann pro UUID maximal ein Mal pro Minute erfolgen!")
        else:
            raise commands.BadArgument(message="UUID wurde nicht gefunden!")


class Fortnite():
    __API_HEADERS = headers = {'TRN-Api-Key': os.environ.get("TRNAPIKEY")}

    @classmethod
    def getStore(self):
        r = requests.get('https://api.fortnitetracker.com/v1/store', headers=self.__API_HEADERS)
        return r.json()

    @classmethod
    def getChallenges(self):
        r = requests.get('https://api.fortnitetracker.com/v1/challenges', headers=self.__API_HEADERS)
        return r.json()["items"]

    @classmethod
    def getStats(self, platform:str, playername:str):
        if platform.lower() in ["pc","xbl","psn"]:
            r = requests.get(("https://api.fortnitetracker.com/v1/profile/%s/%s" % (platform.lower(),playername)), headers=self.__API_HEADERS)
            return r.json()
        else:
            raise commands.BadArgument("Die Plattform '"+platform+"' existiert nicht! Benutze pc, xbl oder psn!")

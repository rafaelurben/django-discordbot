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
    @classmethod
    def __get_headers(self):
        key = os.environ.get("TRNAPIKEY", None)
        if key is None:
            raise commands.CommandError(message="Der Fortnite-Befehl ist leider deaktiviert (nicht konfiguriert)!") 
        else:
            return {'TRN-Api-Key': key}

    @classmethod
    def __get_json(self, url, **kwargs):
        try:
            r = requests.get(url, headers=self.__get_headers())
            j = r.json(**kwargs)
            return j
        except (KeyError, ValueError) as e:
            print("[Fortnite API] - Error:", e)

    @classmethod
    def getStore(self):
        return self.__get_json('https://api.fortnitetracker.com/v1/store')

    @classmethod
    def getChallenges(self):
        return self.__get_json('https://api.fortnitetracker.com/v1/challenges')["items"]

    @classmethod
    def getStats(self, platform:str, playername:str):
        if platform.lower() in ["kbm","gamepad","touch"]:
            return self.__get_json(("https://api.fortnitetracker.com/v1/profile/%s/%s" % (platform.lower(), playername)))
        else:
            raise commands.BadArgument("Die Plattform '"+platform+"' existiert nicht! Benutze kbm, gamepad oder touch!")

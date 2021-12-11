from html.parser import HTMLParser as HTMLParserOriginal
import re
import requests


class HTMLCleaner(HTMLParserOriginal):
    def __init__(self, data, convert_charrefs=True):
        super().__init__(convert_charrefs=convert_charrefs)
        self.data = ""

        self.feed(data)

        for i in ["\n\r", "\r\n", "\n\n\n\n"]:
            while i in self.data:
                self.data = self.data.replace(i, "\n\n")

        self.data = self.data.strip(" ")

    def handle_data(self, data):
        data.replace("*", "\\*")
        data.replace("_", "\\_")
        data.replace("~", "\\~")
        data = data.strip(" \t ")
        data = data.strip()
        self.data += data+"\n"

    def handle_starttag(self, tag, attrs=None):
        if tag in ["del"]:
            self.data += "~~**"
        elif tag in ["li"]:
            self.data += "- "
        elif tag in ["b", "strong"]:
            self.data += "**"
        elif tag in ["i", "em"]:
            self.data += "_"
        elif tag in ["strike"]:
            self.data += "~~"
        elif tag in ["ins"]:
            self.data += "__"
        elif tag in ["hr"]:
            self.data += "\n---\n"

    def handle_endtag(self, tag):
        if tag in ["del"]:
            self.data += "**~~"
        elif tag in ["b", "strong"]:
            self.data += "**"
        elif tag in ["i", "em"]:
            self.data += "_"
        elif tag in ["strike"]:
            self.data += "~~"
        elif tag in ["ins"]:
            self.data += "__"

    @classmethod
    def from_data(cls, data):
        return cls(data).data

    @classmethod
    def from_url(cls, url):
        try:
            html = requests.get(url).text
            try:
                data = ">".join(html.split("<body")[1].split(">")[1:]).split("</body>")[0]
            except (AttributeError, ValueError, IndexError):
                print("HTMLParser Error: Couldn't strip body tag in '"+url+"'!")
                data = html
            return cls(data).data
        except requests.exceptions.RequestException as error:
            print("HTMLParser Error: The request to '"+url+"' raised an exception:", error)
            return "Beim Abfragen der URL '"+url+"' ist ein Fehler aufgetreten. \n" \
                   "Möglicherweise ist die Seite offline oder der Zugriff wurde verweigert."

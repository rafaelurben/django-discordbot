from html.parser import HTMLParser as HTMLParserOriginal
import zlib
import requests
from urllib.parse import urlparse

class HTMLCleaner(HTMLParserOriginal):
    def __init__(self, data, convert_charrefs=True, error=None, **kwargs):
        if error is not None:
            self.data = error
            return

        self.__skip_data = False
        self.__last_opened_tag = ""
        self.__link_url = ""
        self.__link_content = ""

        self.options = kwargs
        super().__init__(convert_charrefs=convert_charrefs)
        self.data = ""

        self.feed(data)

        for i in ["\n\r", "\r\n", "\n\n\n\n"]:
            while i in self.data:
                self.data = self.data.replace(i, "\n\n")

        self.data = self.data.strip(" ")

    def get_hash_str(self) -> str:
        return str(zlib.adler32(self.data.encode("utf-8")))

    def get_data(self) -> str:
        return self.data

    def handle_data(self, data):
        if self.__last_opened_tag in ["style", "script"]:
            return

        data.replace("*", "\\*")
        data.replace("_", "\\_")
        data.replace("~", "\\~")
        data = data.strip(" \t ")
        data = data.strip()

        if self.__link_url:
            self.__link_content += data.replace("\n", " ")
        else:
            self.data += data

    def handle_starttag(self, tag, attrs=None):
        attrs = dict(attrs or [])
        self.__last_opened_tag = tag

        data = ""

        if tag in ["del"]:
            data = " ~~**"
        elif tag in ["li"]:
            data = "\n- "
        elif tag in ["b", "strong"]:
            data = " **"
        elif tag in ["i", "em"]:
            cl = attrs.get("class", "")
            if "fas" in cl or "fa-" in cl:
                data = " _(icon)"
            else:
                data = " _"
        elif tag in ["strike"]:
            data = " ~~"
        elif tag in ["ins"]:
            data = " __"
        elif tag in ["hr"]:
            data = "\n---\n"
        elif tag in ["br"]:
            data = "\n"
        elif tag in ["a"]:
            data = " "
            href = attrs.get("href", "")
            if href.startswith("/") and "base_url" in self.options:
                href = self.options["base_url"] + href
            self.__link_url = href

        if self.__link_url:
            self.__link_content += data.replace("\n", " ")
        else:
            self.data += data

    def handle_endtag(self, tag):
        data = ""

        if tag in ["h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "ul", "ol", "tr", "table", "blockquote"]:
            data = "\n"
        elif tag in ["span"]:
            data = " "
        elif tag in ["del"]:
            data = "**~~ "
        elif tag in ["b", "strong"]:
            data = "** "
        elif tag in ["i", "em"]:
            data = "_ "
        elif tag in ["strike"]:
            data = "~~ "
        elif tag in ["ins"]:
            data = "__ "
        elif tag in ["a"]:
            data = f"[{self.__link_content}]({self.__link_url}) "
            self.__link_url = ""
            self.__link_content = ""

        if self.__link_url:
            self.__link_content += data.replace("\n", " ")
        else:
            self.data += data

    @classmethod
    def from_data(cls, data, **kwargs) -> "HTMLCleaner":
        return cls(data, **kwargs)

    @classmethod
    def from_url(cls, url, body_only=True) -> "HTMLCleaner":
        try:
            html = requests.get(url).text
            if body_only:
                try:
                    data = ">".join(html.split("<body")[1].split(">")[1:]).split("</body>")[0]
                except (AttributeError, ValueError, IndexError):
                    print("HTMLParser Error: Couldn't strip body tag in '"+url+"'!")
                    data = html

            parsedurl = urlparse(url)
            if parsedurl.scheme and parsedurl.netloc:
                base_url = parsedurl.scheme + "://" + parsedurl.netloc
                return cls.from_data(data, base_url=base_url)
            return cls.from_data(data)
        except requests.exceptions.RequestException as error:
            print("HTMLParser Error: The request to '"+url+"' raised an exception:", error)
            return cls(
                None,
                error="Beim Abfragen der URL '"+url+"' ist ein Fehler aufgetreten. \n" \
                      "Möglicherweise ist die Seite offline oder der Zugriff wurde verweigert."
            )

from models import Note
import requests

class RenshuuApi():
    session: str
    baseurl: str = "https://api.renshuu.org/v1/"
    headers: dict

    def __init__(self, apikey: str):
        self.session = apikey
        self.headers = {"Authorization": f"Bearer {apikey}"}

    def japanese(self, term):
        if term["kanji_full"] == "":
            return [self.reading(term)]
        return [t["term"] for t in term["aforms"]] + [term["kanji_full"]]

    def reading(self, term):
        return term["hiragana_full"]

    def english(self, term):
        return term.select(".vdict_def_block")[0].get_text().strip()

    def apiError(self, response):
        if "error" in response and response["error"]:
            return {"result": None, "error": response["error"]}
        else:
            return None

    def schedules(self):
        response = requests.get(f"{self.baseurl}lists", headers=self.headers).json()
        if (e := self.apiError(response)): return e

        # get lists of groups of vocab lists
        lists = [x for x in response["termtype_groups"] if x["termtype"] == "vocab"][0] or None
        if not lists: return []

        # list of lists in "it:groupname:title" format
        lists = [[y["list_id"] + ":" + x["group_title"] + ":" + y["title"] for y in x["lists"]] for x in lists["groups"]]
        # flatten list
        lists = [x for xs in lists for x in xs]
        return lists

    def lookup(self, note: Note):
        response = requests.get(f"{self.baseurl}word/search?value={note.japanese()}", headers = self.headers).json()
        if (e := self.apiError(response)): return e

        # compare dictionary id first
        for t in response["words"]:
            if note.jmdict() == t["edict_ent"]:
                return t["id"]
        # compare kanji+reading as fallback
        for t in response["words"]:
            if (self.reading(t) == note.reading() and
                note.japanese() in self.japanese(t)):
                return t["id"]

    def canAddNote(self, note: Note):
        return True

    def addNote(self, note: Note):
        termId = self.lookup(note)

        listId = note.deckName.split(":")[0]

        #if listId not in [x.split(":")[0] for x in self.schedules()]:
        #    return

        if termId is not None:
            resp = requests.put(f"{self.baseurl}word/{termId}",
                               headers = self.headers, json = {"list_id": listId+""})
            if not resp.ok and resp.json()["error"] != "This term is already present in the schedule.":
                print(resp.content)
                content = {"result": None, "error": resp.json()["error"]}
                return JSONResponse(content=content, status_code=status.HTTP_200_OK)
            return 1
        print("no match")
        #raise HTTPException(status_code = 500, detail = "No matching entry found")

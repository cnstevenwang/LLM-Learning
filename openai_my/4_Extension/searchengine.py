import requests
import json
from enum import Enum

help_portal_url_schema = "https://help.sap.com/http.svc/elasticsearch?area=content&version=&language=en-US&state=PRODUCTION&q={}&transtype=standard,html,pdf,others&product=&to=20&advancedSearch=0&excludeNotSearchable=1"

class SearchStatus(Enum):
    OK = "OK"

def search(keywords = []) -> str:
    if not keywords:
       return
    try:
        normalized_keywords = normalize_keywords(keywords)
        url = help_portal_url_schema.format(normalized_keywords)
        response = requests.get(url)
        json_response = json.loads(response.text)
        if json_response is not None and json_response["status"] is not None and SearchStatus.OK.value.lower() == json_response["status"].lower():
            print(f"""Search:{url}""")
            return json_response["data"]["results"]
        return
    except Exception as e:
        print(e)
        return

def normalize_keywords(keywords):
    return keywords.replace("\n", "").replace("\"","").strip("[").strip("]")
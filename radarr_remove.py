## Written by Actar/Slopedoo
##
## Script to remove movies containing words given in argument

import requests
import json
import sys

SCRIPT_NAME = sys.argv[0]
API_PATH = "/home/sigurd/tools/discobot/"
RADARR_MOVIE_LIST = "radarr_list.txt"

if len(sys.argv) > 1:
    radarr_address = "10.0.0.2"
    radarr_port = "7878"

    with open(API_PATH+'radarr.api', 'r') as apifile:
        api_key = apifile.read().replace('\n','')

    hdrs = {'content-type': 'application/json'}
    del_json = {'deleteFiles': 'true', 'addExclusion': 'true'}

    radarr = requests.get("http://" + radarr_address + ":" + radarr_port + "/api/movie?apikey=" + api_key)
    radarr = radarr.json()

    for i in sys.argv[1:]:
        for y in radarr:
            if 'title' in y:
                if i in y['title']:
                    radarr_url = "http://" + radarr_address + ":" + radarr_port + "/radarr/api/movie/" + str(y['id']) + "?apikey=" + api_key
                    r = requests.delete(radarr_url, params=del_json)

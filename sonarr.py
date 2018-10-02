import requests
import json

#https://realpython.com/python-json/

def request(imdb_id):
    sonarr_address = "http://localhost:8989/api/series?apikey="
    with open('sonarr.api', 'r') as myfile:
            api_key = myfile.read().replace('\n', '')
    PATH = "/home/sigurd/tv5/Series/"
    full_url = sonarr_address + api_key
    json_headers = {'content-type': 'application/json'}

    # tvdb needs an auth token in the request header

    auth_list = open('tvdb_auth.api').read().splitlines()
    auth_string = {
        "apikey": auth_list[0],
        "userkey": auth_list[1],
        "username": auth_list[2]
    }

    # get auth token from the auth_string
    auth = requests.post("https://api.thetvdb.com/login", json=auth_string, headers=json_headers)
    auth_token = json.loads(auth.text)
    auth_token = auth_token['token']

    # append the token to the json_header
    auth_header = {'Authorization' : 'Bearer '+auth_token}
    json_headers.update(auth_header)

    # get info by IMDb ID
    get_url = "https://api.thetvdb.com/search/series?imdbId=" + imdb_id
    get_series = requests.get(get_url, headers=json_headers)
    series = json.loads(get_series.text)
    series = series['data'][0]

    banner_url = "https://www.thetvdb.com/banners/"
    images_url = "https://api.thetvdb.com/series/" + str(series['id']) + "/images/"
    fanart = requests.get(images_url+"query?keyType=fanart", headers=json_headers)
    fanart = json.loads(fanart.text)
    fanart_url = banner_url + fanart['data'][0]['fileName']

    poster = requests.get(images_url+"query?keyType=poster", headers=json_headers)
    poster = json.loads(poster.text)
    poster_url = banner_url + poster['data'][0]['fileName']

    images = [
        { "coverType" : "fanart" , "url" : fanart_url },
        { "coverType" : "banner" , "url" : banner_url+series['banner'] },
        { "coverType" : "poster" , "url" : poster_url }
    ]

    # get seasons from tvdb
    seasons_url = "https://api.thetvdb.com/series/" + str(series['id']) + "/episodes/summary"
    seasons = requests.get(seasons_url, headers=json_headers)
    seasons = json.loads(seasons.text)
    num_seasons = seasons['data']['airedSeasons'] # a list of aired seasons (string format)

    seasons = []

    for i in num_seasons:
        if int(i) == 0: # don't monitor extras
            seasons.append({ 'seasonNumber': int(i) , 'monitored': 'false' })
        else:
            seasons.append({ 'seasonNumber': int(i) , 'monitored': 'true' }) # convert string to int since this is what Sonarr wants

    # put it all together to the structure that Sonarr wants
    series_structure = {
        "tvdbId" : series['id'],
        "title" : series['seriesName'],
        "rootFolderPath" : PATH,
        "qualityProfileId" : 3, # 1=Any, 2=SD, 3=720p, 4=1080p, 5=HD-All
        "titleSlug" : series['slug'],
        "images" : images,
        "seasons" : seasons,
        "addOptions":
        {
            "ignoreEpisodesWithFiles": "false",
            "ignoreEpisodesWithoutFiles": "false",
            "searchForMissingEpisodes": "true"
        }
    }

    print(series_structure)
    if series_structure['tvdbId'] != 0 or series_structure['title'] != "":
        json_headers = {'content-type': 'application/json'}
        r = requests.post(full_url, json=series_structure, headers=json_headers)
        return(r.status_code)

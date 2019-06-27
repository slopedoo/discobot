#!/usr/bin/python3
## Written by Actar/Slopedoo
##
## Discord Bot for Plex to help with automation and self-servicing for users
## Requires: discord, uptime, imdbpy, psutil, uptime

# -*- coding: utf-8 -*-
import discord
import subprocess
from discord.ext.commands import Bot
from discord.ext import commands
from uptime import uptime
from imdb import IMDb
import asyncio, time, requests, json, psutil, os

#import logging
#logging.basicConfig()

PREFIX = "!"
NETWORK_INTERFACE = "enp3s0"

# Path to API files
API_PATH = "/home/sigurd/tools/discobot/"

# Name of the API files. They should only contain the API key of the service and nothing else
TAUTULLI_API = "pp.api"
RADARR_API = "radarr.api"
DISCORD_API = "discord.api"
TMDB_API = "tmdb.api"
OMBI_API = "ombi.api"
TVDB_API = "tvdb_auth.api"

# A list of all Radarr movies in Json format. Updated through the Radarr API (wget http://localhost:7878/api/movie?apikey=XXXXXXX) with something like crontab
# 00 */2 * * * wget -q http://10.0.0.2:7878/api/movie?apikey=XXXXXXXXXXXXXXXXXXXXX -O /discobot/radarr_list.txt
RADARR_MOVIE_LIST = "radarr_list.txt"

# Host address and port numbers
HOST = "10.0.0.2"
TAUTULLI_PORT = "8181"
OMBI_PORT = "19999"

# Plex URL is typically app.plex.tv/desktop#!/server/<your identifier>/details. This url is used for linking to entries in the library
PLEX_URL = "http://plex.bjornerud.eu"

# Path to media folders. My mountpoints are named mov1, mov2, tv1, tv2 etc. so the disk usage function will filter based on "mov" and "tv"
MOV_PATH = "/mnt/mov"
TV_PATH = "/mnt/tv"

##################################################################################################################################################################
##################################################################################################################################################################

discClient = discord.Client()
bot = commands.Bot(command_prefix = PREFIX)

with open(API_PATH+TAUTULLI_API, 'r') as myfile:
    pp_apikey = myfile.read().replace('\n', '')

ppurl = "http://" + HOST + ":" + TAUTULLI_PORT + "/tautulli/api/v2?apikey=" + pp_apikey + "&cmd="

@bot.event
async def on_ready():
    print("Bot is ready")

@bot.command(pass_context=True)
async def toptv(ctx):
    """Prints a list over the most played TV shows the last month"""
    r = requests.get(ppurl+"get_home_stats")
    a = r.json()
    r = 1
    msg = ""

    for i in a['response']['data'][0]['rows']:
        title = i['title']
        plays = i['total_plays']
        msg += "{:45s}".format(str(r) + ". " + title) + "Total plays: " + "{:>4s}".format(str(plays)) + "\n"
        if r == 10:
            break
        r += 1
    await bot.send_message(ctx.message.channel, ":tv: Top TV Shows the last month: :tv: ```"+msg+"```")

@bot.command(pass_context=True)
async def topmovie(ctx):
    """Prints a list over the most played movies the last month"""
    r = requests.get(ppurl+"get_home_stats")
    a = r.json()
    r = 1
    msg = ""

    for i in a['response']['data'][2]['rows']:
        title = i['title']
        plays = i['total_plays']
        msg += "{:45s}".format(str(r) + ". " + title) + "Total plays: " + "{:>4s}".format(str(plays)) + "\n"
        if r == 10:
            break
        r += 1

    await bot.send_message(ctx.message.channel, ":film_frames: Top movies the last month: :film_frames: ```"+msg+"```")

@bot.command(pass_context=True)
async def library(ctx):
    """Prints movie/TV show/artist count"""
    r = requests.get(ppurl+"get_libraries")
    a = r.json()
    movies = a['response']['data'][0]['count']
    tv = a['response']['data'][1]['count']
    await bot.send_message(ctx.message.channel, "Library statistics:\n```Movies:   " + movies + "\n" +
            "TV Shows: " + tv + "```")

@bot.command(pass_context=True)
async def search(ctx, *, text):
    """Search for content on the Plex server. I.e. !search Toy Story"""
    r = requests.get(ppurl+"search"+"&query="+text)
    a = r.json()
    tv = movies = music = ""
    url = PLEX_URL + "?key=/library/metadata/"
    url2 = ""
    # Categorize search results
    for i in a['response']['data']['results_list']:
        if i == 'show':
            for r in a['response']['data']['results_list']['show']:
                # Make full URL to the Plex item
                url2 = url + r['rating_key']
                full_title = "`" + str(r['full_title'])
                full_title += " "*(45-len(full_title)) + " |` "
                tv += "\n" + full_title + "{}".format(url2)
        if i == 'movie':
            for r in a['response']['data']['results_list']['movie']:
                url2 = url + r['rating_key']
                full_title = "`" + str(r['full_title']) + " (" + str(r['year']) + ")"
                full_title += " "*(45-len(full_title)) + " |` "
                movies += "\n" + full_title + "{}".format(url2)
        if i == 'artist':
            for r in a['response']['data']['results_list']['artist']:
                url2 = url + r['rating_key']
                full_title = "`" + str(r['full_title'])
                full_title += " "*(45-len(full_title)) + " |` "
                music += "\n" + full_title + "{}".format(url2)

    # Only print categories where we have results
    msg = "Search results: \n"
    if movies != "":
        msg += "Movies: " + movies + "\n"
    if tv != "":
        msg += "\nTV Shows: " + tv + "\n"
    if music != "":
        msg += "\nArtists: " + music

    if movies == tv == music == "":
        await bot.send_message(ctx.message.channel, "No search results found.")
    else:
        await bot.send_message(ctx.message.channel, msg)

@bot.command(pass_context=True)
async def status(ctx):
    """Show server status (CPU, uptime, memory)"""
    cpu = psutil.cpu_percent()
    up = int(uptime()/60/60/24)
    mem = psutil.virtual_memory()
    memoryTot = int(mem[0]/1000000)
    memoryUse = memoryTot - int(mem[1]/1000000)
    temp = psutil.sensors_temperatures()['coretemp'][0][1]

    total = subprocess.check_output("df | grep "+MOV_PATH+" | awk '{print $2}'", shell=True).decode('ascii').splitlines()
    used = subprocess.check_output("df | grep "+MOV_PATH+" | awk '{print $3}'", shell=True).decode('ascii').splitlines()
    total_mov = used_mov = 0

    for i in total:
        total_mov += int(i)

    for i in used:
        used_mov += int(i)

    total_mov = round(total_mov / 1000000000, 1)
    used_mov = round(used_mov / 1000000000, 1)
    mov_pct = round(used_mov / total_mov*100, 1)

    total = subprocess.check_output("df | grep "+TV_PATH+" | awk '{print $2}'", shell=True).decode('ascii').splitlines()
    used = subprocess.check_output("df | grep "+TV_PATH+" | awk '{print $3}'", shell=True).decode('ascii').splitlines()
    total_tv = used_tv = 0

    for i in total:
        total_tv += int(i)

    for i in used:
        used_tv += int(i)

    total_tv = round(total_tv / 1000000000, 1)
    used_tv = round(used_tv / 1000000000, 1)
    tv_pct = round(used_tv / total_tv*100, 1)

    # Get current network usage
    tx = subprocess.check_output("vnstat -i "+NETWORK_INTERFACE+" -tr 2 | grep tx | awk '{print $2 \" \" $3}'", shell=True)
    rx = subprocess.check_output("vnstat -i "+NETWORK_INTERFACE+" -tr 2 | grep rx | awk '{print $2 \" \" $3}'", shell=True)
    tx = tx.decode('ascii').strip()
    rx = rx.decode('ascii').strip()

    # Get count of current streams
    r = requests.get(ppurl+"get_activity")
    a = r.json()
    stream_count = 0
    for i in a['response']['data']['sessions']:
        stream_count += 1

    msg = "System Status:\n```Current streams: "+str(stream_count)+"\n\nUptime:      " + str(up) + " days\nCPU usage:   " + str(cpu) + "%\n"
    msg += "Memory:      " + str(memoryUse) + "KB / " + str(memoryTot) + "KB\nTemp:        " + str(temp) + "°\n\nOut traffic: " + tx + "\nIn traffic:  " + rx + "\n\n"
    msg += "Movies:    " + str(used_mov) + " TB / " + str(total_mov) + " TB (" + str(mov_pct) + "% used)\n"
    msg += "TV Shows:  " + str(used_tv) + " TB / " + str(total_tv) + " TB (" + str(tv_pct) + "% used)```"
    await bot.send_message(ctx.message.channel, msg)

@bot.command(pass_context=True)
async def request(ctx, arg):
    """Request a movie with IMDB URL (TV shows not working)"""
    imdb = ""
    # Make sure it's a valid URL
    if arg.startswith('http'):
        # 4th argument in an IMDB URL is the movie ID
        if len(arg.split('/')) >= 4:
            temp = arg.split('/')[4]
            # Check that the movie ID is a valid IMDB ID (starts with tt)
            if temp.startswith('tt'):
                imdb = temp
                imdb_id = imdb[2:]
                ia = IMDb()
                msg = ""
                movie = ia.get_movie(imdb_id)
                # If the result is a movie:
                if 'movie' in movie['kind']:
                    # Check if the movie already exists in Radarr
                    # A crontab is downloading a list of movies every 2 hours using an API call to Radarr
                    with open(API_PATH+RADARR_MOVIE_LIST, 'r') as myfile:
                        radarr = myfile.read().replace('\n', '')
                    radarr = json.loads(radarr)
                    for i in radarr:
                        if 'imdbId' in i:
                            if i['imdbId'] == imdb:
                                if str(i['hasFile']) == "True":
                                    msg = "This movie is already downloaded and is available in Plex."
                                else:
                                    msg = "The movie already exists, but is not downloaded yet. It is either not released, or just not available for download. You can check pending requests with the `"+PREFIX+"requested` command."
                                    dates = release_date(imdb)
                                    digital_date = dates['digital']
                                    physical_date = dates['physical']
                                    if digital_date != "":
                                        msg += "```Digital Release date:  " + digital_date + "```"
                                    if physical_date != "":
                                        msg += "```Physical Release date: " + physical_date + "```"
                                    # Do a search for the movie since it hasn't downloaded yet
                                    with open(API_PATH+RADARR_API, 'r') as myfile:
                                        radarr_api = myfile.read().replace('\n', '')
                                    hdrs = {'content-type': 'application/json'}
                                    movie_ids = []
                                    movie_ids.append(i['id'])
                                    movsearch_json = {'name': "MoviesSearch", 'movieIds': movie_ids}
                                    movsearch_url = "http://10.0.0.2:7878/radarr/api/command?apikey=" + radarr_api
                                    r = requests.post(movsearch_url, json=movsearch_json, headers=hdrs)
                                break
                    # Send the request
                    if msg == "":
                        with open(API_PATH+TMDB_API, 'r') as myfile:
                            tmdb_api = myfile.read().replace('\n', '')
                        with open(API_PATH+OMBI_API, 'r') as myfile:
                            ombi_api = myfile.read().replace('\n', '')
                        r = requests.get("https://api.themoviedb.org/3/movie/"+temp+"/release_dates?api_key="+tmdb_api)
                        tmdbid = r.json()['id']

                        headers = {"Apikey" : ombi_api, "UserName" : "Discord"}
                        payload = {"theMovieDbId" : tmdbid}
                        r = requests.post("http://" + HOST + ":" + OMBI_PORT + "/ombi/api/v1/request/movie", json=payload, headers=headers)
                        if r.json()['isError'] == True:
                            # Request failed
                            msg = (r.json()['errorMessage'])
                        elif r.json()['isError'] == False:
                            # Request succeeded
                            msg = (r.json()['message'])
                    await bot.send_message(ctx.message.channel, msg)
                # If the result is a TV show:
                else:
                    json_headers = {'content-type': 'application/json'}
                    # Tvdb needs an auth token in the request header
                    auth_list = open(API_PATH+TVDB_API).read().splitlines()
                    auth_string = {
                        "apikey": auth_list[0],
                        "userkey": auth_list[1],
                        "username": auth_list[2]
                    }
                    with open(API_PATH+OMBI_API, 'r') as myfile:
                        ombi_api = myfile.read().replace('\n', '')
                    # Get auth token from the auth_string
                    auth = requests.post("https://api.thetvdb.com/login", json=auth_string, headers=json_headers)
                    auth_token = json.loads(auth.text)
                    auth_token = auth_token['token']

                    # Append the token to the json_header
                    auth_header = {'Authorization' : 'Bearer '+auth_token}
                    json_headers.update(auth_header)

                    # Get TVDB ID by IMDb ID
                    get_url = "https://api.thetvdb.com/search/series?imdbId=" + "tt"+imdb_id
                    get_series = requests.get(get_url, headers=json_headers)
                    tvdb_id = get_series.json()['data'][0]['id']

                    headers = {"Apikey" : ombi_api, "UserName" : "Discord"}
                    payload = {"tvdbid" : tvdb_id}
                    r = requests.post("http://" + HOST + ":" + OMBI_PORT + "/ombi/api/v1/request/tv", json=payload, headers=headers)
                    if r.json()['isError'] == True:
                        # Request failed
                        msg = (r.json()['errorMessage'])
                    elif r.json()['isError'] == False:
                        # Request succeeded
                        msg = ("Request successful! It will be downloaded shortly, and notified in <#432847333894389770> when available.")
                    await bot.send_message(ctx.message.channel, msg)
            else:
                await bot.send_message(ctx.message.channel, "Not a valid IMDB URL! It should look like this: https://www.imdb.com/title/tt123456")
        else:
            await bot.send_message(ctx.message.channel, "Not a valid IMDB URL!")
    else:
        # If the arg is not a URL we do a search for the movie on IMDb
        arg = ctx.message.content[9:]
        ia = IMDb()
        movie = ia.search_movie(arg)
        c = 0
        choices = []

        # Append the choices list with the top 10 search results
        for i in movie:
            if 'movie' in i['kind']:
                if c == 10:
                    break
                choices.append({'title' : i['long imdb title'] , 'imdb_url' : "<https://www.imdb.com/title/tt" + i.movieID + ">" , 'imdb_id' : "tt"+i.movieID})
                c += 1
        msg = ""
        c = 1

        if choices != "":
            msg += "The top results:\n"

            for i in choices:
                title = ""
                if len(i['title']) > 38:
                    s_title = i['title'][0:38] + "..."
                    title += "`" + str(c) + ". " + s_title
                else:
                    title += "`" + str(c) + ". " + i['title']
                title += " "*(46-len(title)) + "|`"
                msg += title + "{:<25}".format(i['imdb_url'] + "\n")
                c += 1

            await bot.send_message(ctx.message.channel, msg)
            await bot.send_message(ctx.message.channel, "Choose a movie by typing the corresponding number")
            response = await bot.wait_for_message(author=ctx.message.author,timeout=30)

            if response != None:
                msg = ""
                # Check that the response is within the range of options
                if int(response.content) > len(choices):
                    await bot.send_message(ctx.message.channel, "Not a valid option.")
                    return

                response = int(response.content)-1
                movie_title = choices[response]['title']
                imdb_id = choices[response]['imdb_id']

                # Check if the movie already exists
                with open(API_PATH+RADARR_MOVIE_LIST, 'r') as myfile:
                    radarr = myfile.read().replace('\n', '')
                radarr = json.loads(radarr)
                for i in radarr:
                    if 'imdbId' in i:
                        if i['imdbId'] == imdb_id:
                            if str(i['hasFile']) == "True":
                                msg = "This movie is already downloaded and is available in Plex."
                            elif str(i['hasFile']) == "False":
                                msg = "The movie already exists, but is not downloaded yet. It is either not released, or just not available for download. You can check pending requests with the `"+PREFIX+"requested` command."
                                dates = release_date(imdb_id)
                                digital_date = dates['digital']
                                physical_date = dates['physical']
                                if digital_date != "":
                                    msg += "```Digital Release date:  " + digital_date + "```"
                                if physical_date != "":
                                    msg += "```Physical Release date: " + physical_date + "```"
                            else:
                                msg = "Something broke..."
                            break
                # Send the request
                if msg == "":
                    with open(API_PATH+TMDB_API, 'r') as myfile:
                        tmdb_api = myfile.read().replace('\n', '')
                    with open(API_PATH+OMBI_API, 'r') as myfile:
                        ombi_api = myfile.read().replace('\n', '')
                    r = requests.get("https://api.themoviedb.org/3/movie/"+imdb_id+"/release_dates?api_key="+tmdb_api)
                    tmdbid = r.json()['id']

                    headers = {"Apikey" : ombi_api}
                    payload = {"theMovieDbId" : tmdbid}
                    r = requests.post("http://" + HOST + ":" + OMBI_PORT + "/ombi/api/v1/request/movie", json=payload, headers=headers)
                    print(r.json())
                    if r.json()['message'] == None:
                        # Request failed
                        msg = (r.json()['errorMessage'])
                    elif r.json()['errorMessage'] == None:
                        # Request succeeded
                        msg = (r.json()['message'])
                await bot.send_message(ctx.message.channel, msg)

@bot.command(pass_context=True)
async def requested(ctx):
    """Check pending requests"""
    with open(API_PATH+OMBI_API, 'r') as myfile:
        ombi_api = myfile.read().replace('\n', '')
    headers = {"Apikey" : ombi_api}
    rmov = requests.get("http://" + HOST + ":" + OMBI_PORT + "/ombi/api/v1/request/movie", headers=headers)
    rtv = requests.get("http://" + HOST + ":" + OMBI_PORT + "/ombi/api/v1/request/tv", headers=headers)

    msg = "\nPending Movie Requests:\n"
    msg += "```"
    msg += "{:30}".format("Title")
    msg += "{:30}".format("Requested Date")
    msg += "{:30}".format("Release Date")
    msg += "\n"

    for i in rmov.json():
        if i['markedAsAvailable'] == None:
            msg += "{:30}".format(i['title'])
            msg += "{:30}".format(i['requestedDate'][:10])
            msg += "{:30}".format(i['releaseDate'][:10])
            msg += "\n"

    msg += "```\n"
    msg += "Pending TV Requests:\n"
    msg += "```"
    msg += "{:30}".format("Title")
    msg += "{:30}".format("Requested Date")
    msg += "{:30}".format("Release Date")
    msg += "\n"

    for i in rtv.json():
        y = i['childRequests'][0]
        if y['markedAsAvailable'] == None:
            msg += "{:30}".format(y['title'])
            msg += "{:30}".format(y['requestedDate'][:10])
            msg += "{:30}".format(i['releaseDate'][:10])
            msg += "\n"

    msg += "```"

    await bot.send_message(ctx.message.channel, msg)


@bot.command(pass_context=True)
async def streams(ctx):
    """List of currently active streams"""
    r = requests.get(ppurl+"get_activity")
    a = r.json()
    msg = ""

    for i in a['response']['data']['sessions']:
        full_title = ""
        # If title length is longer than 25 we need to cut it
        if len(i['full_title']) > 25:
            full_title = i['full_title'][0:25] + "[...]"
        else:
            full_title = i['full_title']
        msg += "{:30}".format(full_title)
        msg += "{:>7}".format(i['bandwidth']) + " kbps | "
        msg += "{:<15}".format(i['stream_container_decision']) + " | " + "{:>3}".format(i['progress_percent']) + "% (" + i['state'] + ")\n"

    if msg != "":
        await bot.send_message(ctx.message.channel, "Current streams: ```" + msg + "```")
    else:
        await bot.send_message(ctx.message.channel, "No streams currently playing.")

@bot.command(pass_context=True)
async def specs(ctx):
    """Show system specs"""
    total = subprocess.check_output("df | grep -E '"+TV_PATH+"|"+MOV_PATH+"' | awk '{print $2}'", shell=True).decode('ascii').splitlines()
    used = subprocess.check_output("df | grep -E '"+TV_PATH+"|"+MOV_PATH+"' | awk '{print $3}'", shell=True).decode('ascii').splitlines()
    total_disks = used_disks = 0

    for i in total:
        total_disks += int(i)

    for i in used:
        used_disks += int(i)

    total_disks = round(total_disks / 1000000000, 1)
    used_disks = round(used_disks / 1000000000, 1)
    disks_pct = round(used_disks / total_disks*100, 1)

    cpu_name = subprocess.check_output("cat /proc/cpuinfo | grep -m 1 'model name' | cut -d: -f2", shell=True).decode('ascii').lstrip().splitlines()
    cpu_cores = subprocess.check_output("cat /proc/cpuinfo | grep -c 'model name'", shell=True).decode('ascii').splitlines()
    physical_cpus = subprocess.check_output("cat /proc/cpuinfo | grep 'physical id' | cut -d: -f2", shell=True).decode('ascii').splitlines()
    physical_cpus = len(set(physical_cpus))

    msg = "```" + str(physical_cpus) + "x " + cpu_name[0] + ", " + cpu_cores[0] + " cores\n"

    memory = subprocess.check_output("sudo dmidecode --type 17 | grep Size | grep -v 'No Module' | awk '{print $2}'", shell=True).decode('ascii').splitlines()
    mem_size = 0

    for i in memory:
        mem_size += int(i)

    mem_speed = subprocess.check_output("sudo dmidecode --type 17 | grep -m 1 Speed | grep -v 'No Module' | awk '{print $2}'", shell=True).decode('ascii').rstrip()
    mem_type = subprocess.check_output("sudo dmidecode --type 17 | grep -m 1 Type | grep -v 'No Module' | awk '{print $2}'", shell=True).decode('ascii').rstrip()

    msg +="Memory: " + str(mem_size) + " MB " + mem_type + " " + mem_speed + " MHz\n"
    msg +="Disks:  " + str(used_disks) + " TB / " + str(total_disks) + " TB (" + str(disks_pct) + "% used)```"
    await bot.send_message(ctx.message.channel, msg)

@bot.command(pass_context=True)
async def new(ctx):
    """List of the most recently added items"""
    r = requests.get(ppurl+"get_recently_added&count=10")
    a = r.json()
    msg = ""
    date_added =""
    c = 1

    for i in a['response']['data']['recently_added']:
        d = int(i['added_at'])
        date_added = time.strftime('%d.%m.%Y %H:%M', time.localtime(d))
        title = ""

        # Get the season/episode if its a TV show
        if i['parent_title'] != "":
            title = i['parent_title'] + ", "
        full_title = str(c) + ". " + title + i['title']

        # Add year for movies
        if i['media_type'] == "movie":
            full_title += " (" + str(i['year']) + ")"

        # If title length is longer than 35 we need to cut it
        if len(full_title) > 35:
            full_title = full_title[0:35] + "[...]"
        msg += "{:41s}".format(full_title) + "{:>8s}".format(i['library_name']) + " | Added at " + date_added + "\n"
        c = c + 1

    await bot.send_message(ctx.message.channel, "Most recently added items: ```" + msg + "```")

@bot.command(pass_context=True)
async def releasedate(ctx, arg):
    """Check release date with IMDB URL (TV shows not working)"""
    # Make sure it's a valid URL
    for char in '<>':
        arg = arg.replace(char, '')

    if arg.startswith('http'):
        # 4th argument in an IMDB URL is the movie ID
        if len(arg.split('/')) >= 4:
            temp = arg.split('/')[4]
            # Check that the movie ID is a valid IMDB ID (starts with tt)
            if temp.startswith('tt'):
                imdb = arg.split('/')[4]
                imdb_id = imdb[2:]
                ia = IMDb()
                movie = ia.get_movie(imdb_id)
                if 'movie' in movie['kind']:
                    movie_title = movie['title'] + " (" + str(movie['year']) + ")"
                    dates = release_date(imdb)
                    theatrical_date = dates['theatrical']
                    digital_date = dates['digital']
                    physical_date = dates['physical']
                    msg = "Release dates for " + movie_title + ":"
                    if theatrical_date != "":
                        msg += "```In theaters:           " + theatrical_date + "```"
                    if digital_date != "":
                        msg += "```Digital Release date:  " + digital_date + "```"
                    if physical_date != "":
                        msg += "```Physical Release date: " + physical_date + "```"
                    await bot.send_message(ctx.message.channel, msg)
            else:
                await bot.send_message(ctx.message.channel, "Not a valid IMDB URL!")
        else:
            await bot.send_message(ctx.message.channel, "Not a valid IMDB URL!")
    else:
        # If the arg is not a URL we do a search for the movie on IMDb
        arg = ctx.message.content[9:]
        ia = IMDb()
        movie = ia.search_movie(arg)
        c = 0
        choices = []

        # Append the choices list with the top 10 search results
        for i in movie:
            if 'movie' in i['kind']:
                if c == 10:
                    break
                choices.append({'title' : i['long imdb title'] , 'imdb_url' : "<https://www.imdb.com/title/tt" + i.movieID + ">" , 'imdb_id' : "tt"+i.movieID})
                c += 1
        msg = ""
        c = 1

        if choices != "":
            msg += "The top results:\n"

            for i in choices:
                title = ""
                if len(i['title']) > 38:
                    s_title = i['title'][0:38] + "..."
                    title += "`" + str(c) + ". " + s_title
                else:
                    title += "`" + str(c) + ". " + i['title']
                title += " "*(46-len(title)) + "|`"
                msg += title + "{:<25}".format(i['imdb_url'] + "\n")
                c += 1

            await bot.send_message(ctx.message.channel, msg)
            await bot.send_message(ctx.message.channel, "Choose a movie by typing the corresponding number")
            response = await bot.wait_for_message(author=ctx.message.author,timeout=60)

            if response != None:
                # Check that the response is within the range of options
                if int(response.content) > len(choices):
                    await bot.send_message(ctx.message.channel, "Not a valid option.")
                    return

                response = int(response.content)-1
                movie_title = choices[response]['title']
                imdb_id = choices[response]['imdb_id']
                print(imdb_id)

                dates = release_date(imdb_id)
                msg = "Release dates for " + movie_title

                if dates['theatrical'] != "":
                    msg += "```Theatrical Release date:  " + dates['theatrical'] + "```"
                if dates['digital'] != "":
                    msg += "```Digital Release date:  " + dates['digital'] + "```"
                if dates['physical'] != "":
                    msg += "```Physical Release date: " + dates['physical'] + "```"
                await bot.send_message(ctx.message.channel, msg)


# Functions to check release dates. Returns a dict with 'theatrical', 'digital' and 'physical' indexes
# Uses the TMDb API
def release_type(results, release_dates, country):
    for i in results:
        if country != "all":
            if i['iso_3166_1'] == country:
                for a in i['release_dates']:
                    if a['type'] == 3 and release_dates['theatrical'] == "":
                        release_dates['theatrical'] = a['release_date'][:10] + " (" + i['iso_3166_1'] + ")"
                    if a['type'] == 4 and release_dates['digital'] == "":
                        release_dates['digital'] = a['release_date'][:10] + " (" + i['iso_3166_1'] + ")"
                    if a['type'] == 5 and release_dates['physical'] == "":
                        release_dates['physical'] = a['release_date'][:10] + " (" + i['iso_3166_1'] + ")"
        else:
            for a in i['release_dates']:
                if a['type'] == 3 and release_dates['theatrical'] == "":
                    release_dates['theatrical'] = a['release_date'][:10] + " (" + i['iso_3166_1'] + ")"
                if a['type'] == 4 and release_dates['digital'] == "":
                    release_dates['digital'] = a['release_date'][:10] + " (" + i['iso_3166_1'] + ")"
                if a['type'] == 5 and release_dates['physical'] == "":
                    release_dates['physical'] = a['release_date'][:10] + " (" + i['iso_3166_1'] + ")"
    return release_dates

def release_date(imdb):
    with open(API_PATH+TMDB_API, 'r') as myfile:
        tmdb_api = myfile.read().replace('\n', '')

    r = requests.get("https://api.themoviedb.org/3/movie/" + imdb + "/release_dates?api_key=" + tmdb_api)
    results = r.json()
    results = results['results']
    release_dates = { 'theatrical':'' , 'digital':'' , 'physical':''}

    release_dates = release_type(results, release_dates, "US")
    release_dates = release_type(results, release_dates, "UK")
    release_dates = release_type(results, release_dates, "SE")
    release_dates = release_type(results, release_dates, "NO")
    release_dates = release_type(results, release_dates, "all")

    return release_dates


# Discord API key
with open(API_PATH+DISCORD_API, 'r') as myfile:
    disc_api = myfile.read().replace('\n', '')

bot.run(disc_api)

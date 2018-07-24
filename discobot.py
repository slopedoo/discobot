## Written by Actar/Slopedoo
##
## Discord Bot for Plex to help with automation and self-servicing for users
## API key files should be named pp_api.txt, cp_api.txt and discord_api.txt for PlexPy, Couchpotato and Discord respectively

# -*- coding: utf-8 -*-
import discord
from discord.ext.commands import Bot
from discord.ext import commands
from uptime import uptime
from pyshorteners import Shortener
from imdb import IMDb
import asyncio
import time
import requests
import json
import psutil
import os

import logging
logging.basicConfig()

### You can change these ###

PREFIX = "!"
API_PATH = "/home/sigurd/tools/discobot/"
PLEXPY_PORT = "8181"
COUCHPOTATO_PORT = "5050"
# Plex URL is typically app.plex.tv/desktop#!/server/<your identifier>/details. This url is used for linking to entries in the library
#PLEX_URL = "https://app.plex.tv/desktop#!/server/840fd4be6d4142952abf5182e8dc1cc4bfae60db/details"
PLEX_URL = "http://plex.nerud.no"

############################

discClient = discord.Client()
bot = commands.Bot(command_prefix = PREFIX)

# PlexPy API URL
pp_apikey = ""

with open(API_PATH+'pp_api.txt', 'r') as myfile:
    pp_apikey = myfile.read().replace('\n', '')

ppurl = "http://localhost:" + PLEXPY_PORT + "/api/v2?apikey=" + pp_apikey + "&cmd="

@bot.event
async def on_ready():
    print("Bot is ready")

@bot.command(pass_context=True)
async def toptv(ctx):
    """Prints a list over the most played TV shows the last month"""
    r = requests.get(ppurl+"get_home_stats")
    a = r.json()
    c = 0
    r = c+1
    msg = ""

    for i in a['response']['data'][0]['rows']:
        o = a['response']['data'][0]['rows'][c]['title']
        p = a['response']['data'][0]['rows'][c]['total_plays']
        o = str(r) + ". " + o
        msg = msg + "{:45s}".format(o) + "Total plays: " + "{:>4s}".format(str(p)) + "\n"
        c = c + 1
        r = c + 1
        if c == 10:
            break
    await bot.send_message(ctx.message.channel, ":tv: Top TV Shows the last month: :tv: ```"+msg+"```")

@bot.command(pass_context=True)
async def topmovie(ctx):
    """Prints a list over the most played movies the last month"""
    r = requests.get(ppurl+"get_home_stats")
    a = r.json()
    c = 0
    r = c+1
    msg = ""
    for i in a['response']['data'][2]['rows']:
        o = a['response']['data'][2]['rows'][c]['title']
        p = a['response']['data'][2]['rows'][c]['total_plays']
        o = str(r) + ". " + o
        msg = msg + "{:45s}".format(o) + "Total plays: " + "{:>4s}".format(str(p)) + "\n"
        c = c + 1
        r = c + 1
        if c == 10:
            break
    await bot.send_message(ctx.message.channel, ":film_frames: Top movies the last month: :film_frames: ```"+msg+"```")

@bot.command(pass_context=True)
async def library(ctx):
    """Prints movie/TV show/artist count"""
    r = requests.get(ppurl+"get_libraries")
    a = r.json()
    c = 0
    movies = a['response']['data'][0]['count']
    music = a['response']['data'][1]['count']
    tv = a['response']['data'][2]['count']
    await bot.send_message(ctx.message.channel, "Library statistics:\n```Movies:   " + movies + " films.\n" +
            "TV Shows: " + tv + " shows.\n" + "Artists:  " + music + "```")

@bot.command(pass_context=True)
async def search(ctx, *, text):
    """Search for content on the Plex server. I.e. !search Toy Story"""
    r = requests.get(ppurl+"search"+"&query="+text)
    a = r.json()
    tv = ""
    movies = ""
    music = ""
    url = PLEX_URL + "?key=/library/metadata/"
    url2 = ""
    # Categorize search results
    for i in a['response']['data']['results_list']:
        if i == 'show':
            for r in a['response']['data']['results_list']['show']:
                # Make full URL to the Plex item
                url2 = url + r['rating_key']
                #shortener = Shortener('Tinyurl')
                # A bit of formatting
                full_title = "`" + str(r['full_title'])
                full_title += " "*(45-len(full_title)) + ">` "
                # Print title + shortened URL
                #tv += "\n" + full_title + "{}".format(shortener.short(url2))
                tv += "\n" + full_title + "{}".format(url2)
        if i == 'movie':
            for r in a['response']['data']['results_list']['movie']:
                url2 = url + r['rating_key']
                #shortener = Shortener('Tinyurl')
                full_title = "`" + str(r['full_title']) + " (" + str(r['year']) + ")"
                full_title += " "*(45-len(full_title)) + ">` "
                #movies += "\n" + full_title + "{}".format(shortener.short(url2))
                movies += "\n" + full_title + "{}".format(url2)
        if i == 'artist':
            for r in a['response']['data']['results_list']['artist']:
                url2 = url + r['rating_key']
                #shortener = Shortener('Tinyurl')
                full_title = "`" + str(r['full_title'])
                full_title += " "*(45-len(full_title)) + ">` "
                #music += "\n" + full_title + "{}".format(shortener.short(url2))
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
    total_mov = psutil.disk_usage('/home/sigurd/mov1')[0] + psutil.disk_usage('/home/sigurd/mov2')[0] + psutil.disk_usage('/home/sigurd/mov3')[0] + psutil.disk_usage('/home/sigurd/mov4')[0] + psutil.disk_usage('/home/sigurd/mov5')[0] + psutil.disk_usage('/home/sigurd/owncloud')[0]
    used_mov = psutil.disk_usage('/home/sigurd/mov1')[1] + psutil.disk_usage('/home/sigurd/mov2')[1] + psutil.disk_usage('/home/sigurd/mov3')[1] + psutil.disk_usage('/home/sigurd/mov4')[1] + psutil.disk_usage('/home/sigurd/mov5')[1] + psutil.disk_usage('/home/sigurd/owncloud')[1]
    total_tv = psutil.disk_usage('/home/sigurd/tv1')[0] + psutil.disk_usage('/home/sigurd/tv2')[0] + psutil.disk_usage('/home/sigurd/tv3')[0] + psutil.disk_usage('/home/sigurd/tv4')[0]
    used_tv = psutil.disk_usage('/home/sigurd/tv1')[1] + psutil.disk_usage('/home/sigurd/tv2')[1] + psutil.disk_usage('/home/sigurd/tv3')[1] + psutil.disk_usage('/home/sigurd/tv4')[1]
    total_mov = round(total_mov / 1000000000000,1)
    used_mov = round(used_mov / 1000000000000,1)
    mov_pct = round(used_mov / total_mov*100,1)
    total_tv = round(total_tv / 1000000000000,1)
    used_tv = round(used_tv / 1000000000000,1)
    tv_pct = round(used_tv / total_tv*100,1)
    await bot.send_message(ctx.message.channel, "System Status:\n```Uptime:    " + str(up) + " days\nCPU usage: " + str(cpu) + "%\nMemory:    " + str(memoryUse) + "KB / " + str(memoryTot) + "KB\nTemp:      " + str(temp) + "°\n\nMovies:    " + str(used_mov) + " TB / " + str(total_mov) + " TB (" + str(mov_pct) + "% used)\nTV Shows:  " + str(used_tv) + " TB / " + str(total_tv) + " TB (" + str(tv_pct) + "% used)```")

@bot.command(pass_context=True)
async def request(ctx, arg):
    """Request a movie with IMDB URL (TV shows not working)"""
    # Couchpotato API URL. Gets put on watchlist, which is then grabbed by Radarr
    cp_api = ""

    with open(API_PATH+'cp_api.txt', 'r') as myfile:
        cp_api = myfile.read().replace('\n', '')

    url = "http://localhost:" + COUCHPOTATO_PORT + "/api/" + cp_api + "/movie.add?identifier="
    imdb = ""
    # Make sure it's a valid URL
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
		    # Send the request
                    requests.post(url+imdb)
                    movie_title = movie['title'] + " (" + str(movie['year']) + ")"
                    with open(API_PATH+'tmdb_api.txt', 'r') as myfile:
                        tmdb_api = myfile.read().replace('\n', '')

                    r = requests.get("https://api.themoviedb.org/3/movie/" + imdb + "/release_dates?api_key=" + tmdb_api)
                    results = r.json()
                    results = results['results']
                    digital_date = ""
                    physical_date = ""
                    # Find the digital and physical US release date.
                    for i in results:
                        if i['iso_3166_1'] == "US":
                            for a in i['release_dates']:
                                if a['type'] == 4 and digital_date == "":
                                    digital_date = a['release_date'][:10]
                                if a['type'] == 5 and physical_date == "":
                                    physical_date = a['release_date'][:10]
                        if i['iso_3166_1'] == "SE":
                            for a in i['release_dates']:
                                if a['type'] == 4 and digital_date == "":
                                    digital_date = a['release_date'][:10]
                                if a['type'] == 5 and physical_date == "":
                                    physical_date = a['release_date'][:10]
                    msg = "Request for " + movie_title + " sent to downloader! It will be notified in <#432847333894389770> when available."
                    if digital_date != "":
                        msg += "```Digital Release date:  " + digital_date + "```"
                    if physical_date != "":
                        msg += "```Physical Release date: " + physical_date + "```"
                    await bot.send_message(ctx.message.channel, msg)
                else:
                    await bot.send_message(ctx.message.channel, "Not a movie! Requests only works with Movies. <@!205394235522809867> fix manually plz.")
            else:
                await bot.send_message(ctx.message.channel, "Not a valid IMDB URL!")
        else:
            await bot.send_message(ctx.message.channel, "Not a valid IMDB URL!")
    else:
        await bot.send_message(ctx.message.channel, "Not a valid URL!")

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
                    with open(API_PATH+'tmdb_api.txt', 'r') as myfile:
                        tmdb_api = myfile.read().replace('\n', '')

                    r = requests.get("https://api.themoviedb.org/3/movie/" + imdb + "/release_dates?api_key=" + tmdb_api)
                    results = r.json()
                    results = results['results']
                    theatrical_date = ""
                    digital_date = ""
                    physical_date = ""
                    for i in results:
                        if i['iso_3166_1'] == "US":
                            for a in i['release_dates']:
                                if a['type'] == 3 and theatrical_date == "":
                                    theatrical_date = a['release_date'][:10]
                                if a['type'] == 4 and digital_date == "":
                                    digital_date = a['release_date'][:10]
                                if a['type'] == 5 and physical_date == "":
                                    physical_date = a['release_date'][:10]
                    for i in results:
                        if i['iso_3166_1'] == "SE":
                            for a in i['release_dates']:
                                if a['type'] == 3 and theatrical_date == "":
                                    theatrical_date = a['release_date'][:10]
                                if a['type'] == 4 and digital_date == "":
                                    digital_date = a['release_date'][:10]
                                if a['type'] == 5 and physical_date == "":
                                    physical_date = a['release_date'][:10]
                    msg = "Release dates for " + movie_title + ":"
                    if theatrical_date != "":
                        msg += "```In theaters:           " + theatrical_date + "```"
                    if digital_date != "":
                        msg += "```Digital Release date:  " + digital_date + "```"
                    if physical_date != "":
                        msg += "```Physical Release date: " + physical_date + "```"
                    await bot.send_message(ctx.message.channel, msg)
                else:
                    await bot.send_message(ctx.message.channel, "Not a movie! Requests only works with Movies. <@!205394235522809867> fix manually plz.")
            else:
                await bot.send_message(ctx.message.channel, "Not a valid IMDB URL!")
        else:
            await bot.send_message(ctx.message.channel, "Not a valid IMDB URL!")
    else:
        await bot.send_message(ctx.message.channel, "Not a valid URL!")

# Discord API key
disc_api = ""

with open(API_PATH+'discord_api.txt', 'r') as myfile:
    disc_api = myfile.read().replace('\n', '')

bot.run(disc_api)

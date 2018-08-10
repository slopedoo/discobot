## Written by Actar/Slopedoo
##
## Script to batch move movies in Radarr from one path to another. Handy for disk failures etc.

import requests
import json
import sys

SCRIPT_NAME = sys.argv[0]

if len(sys.argv) == 3:
    print("\nWARNING: This script will change root folder of several movies.\n"+
          "         Be sure that you have the correct paths.\n")
    input("Press ENTER to continue or ctrl+C to cancel...")
    radarr_address = "localhost"
    radarr_port = "7878"

    mov_command = "/api/movie?apikey="
    refresh_command = "/api/command?apikey="

    with open('radarr.api', 'r') as apifile:
        api_key = apifile.read().replace('\n','')

    old_path = sys.argv[1]
    new_path = sys.argv[2]

    # Make sure to add a trailing slash to the path if it does not exist
    if old_path[-1] != "/":
        old_path += "/"
    if new_path[-1] != "/":
        new_path += "/"

    mov_url = "http://" + radarr_address + ":" + radarr_port + mov_command + api_key
    refresh_url = "http://" + radarr_address + ":" + radarr_port + refresh_command + api_key

    r = requests.get(mov_url)
    result = json.loads(r.text)

    hdrs = {'content-type': 'application/json'}
    refresh_json = {'name': "RescanMovie", 'movieId': ""}

    success = 0
    failed = 0

    for i in result:
        # Check if the patch matches the one we want to move from
        # Use .split to get the 5th argument (the movie directory name) and append to old path
        m_dir = i['path'].split('/')[5]
        if i['path'] == old_path + m_dir:
            old_path_full = old_path + m_dir
            new_path_full = new_path + m_dir
            i['path'] = new_path_full
            i['folderName'] = new_path_full
            # Send the movie update request
            r = requests.put(mov_url, json=i, headers=hdrs)
            msg = "{:<70s}".format(old_path_full) + " -> " + "{:70s}".format(new_path_full)
            # Check the HTTP response code
            if r.status_code == 200 or r.status_code == 201 or r.status_code == 202:
                success += 1
                msg += "{:>30s}".format("SUCCESS")
            else:
                failed += 1
                msg += "{:>30s}".format("FAILURE")
            print(msg)
            refresh_json['movieId'] = i['id']
            # Send a refresh movie request
            r = requests.post(refresh_url, json=refresh_json, headers=hdrs)
    print(str(success) + " movies moved and refreshed successfully.\n")
    print(str(failed) + " movies failed to be moved.")
elif sys.argv[1] == "-h" or sys.argv[1] == "--help":
    print("\nThis script moves all movies from one path to another in Radarr.\n"+
          "Usage: " + SCRIPT_NAME + " /path/to/old/ /path/to/new/\n"+
          "\nThe script will update the Radarr database with the new path and send a rescan request")
else:
    print("Argument error. Provide old path and new path as arguments.\nEx: " + SCRIPT_NAME + " /path/to/old/ /path/to/new/")

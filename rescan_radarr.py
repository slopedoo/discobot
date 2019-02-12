## Written by Actar/Slopedoo
##
## Script to rescan all movies on a path

import requests
import json
import sys

SCRIPT_NAME = sys.argv[0]

if len(sys.argv) == 2:
    print("\nWARNING: This script will refresh and scan disk for several movies.\n"+
          "         Be sure that you have the correct path.\n")
    input("Press ENTER to continue or ctrl+C to cancel...")
    radarr_address = "10.0.0.2"
    radarr_port = "7878"

    mov_command = "/api/movie?apikey="
    refresh_command = "/api/command?apikey="

    with open('radarr.api', 'r') as apifile:
        api_key = apifile.read().replace('\n','')

    old_path = sys.argv[1]

    # Make sure to add a trailing slash to the path if it does not exist
    if old_path[-1] != "/":
        old_path += "/"

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
            # Send the movie update request
            msg = "{:<70s}".format(old_path_full)
            refresh_json['movieId'] = i['id']
            # Send a refresh movie request
            r = requests.post(refresh_url, json=refresh_json, headers=hdrs)
            # Check the HTTP response code
            if r.status_code == 200 or r.status_code == 201 or r.status_code == 202:
                success += 1
                msg += "{:>30s}".format("SUCCESS")
            else:
                failed += 1
                msg += "{:>30s}".format("FAILURE")
            print(msg)
    print(str(success) + " movies refreshed successfully.\n")
    print(str(failed) + " movies failed to refresh.")
elif sys.argv[1] == "-h" or sys.argv[1] == "--help":
    print("\nThis script rescans all movies on a defined path in Radarr.\n"+
          "Usage: " + SCRIPT_NAME + " /path/to/movies/\n")
else:
    print("Argument error. Provide path to movies as argument.\nEx: " + SCRIPT_NAME + " /path/to/movies/")

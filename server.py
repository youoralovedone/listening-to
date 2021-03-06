import time
import json
import base64
import pickle
import requests
import pypresence

LASTFM_API_URL = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={user}&api_key={key}&format=json"
DISCORD_API_POST_URL = "https://discord.com/api/v8/oauth2/applications/{client_id}/assets"


def main():
    try:
        with open("album_cache.p", "rb") as f:
            album_cache = pickle.load(f)
    except FileNotFoundError:
        album_cache = []
        with open("album_cache.p", "wb") as f:
            pickle.dump(album_cache, f)
    with open("config.json") as f:
        config = json.load(f)

    rpc = pypresence.Presence(config["client_id"], pipe=0)
    rpc.connect()

    old_trackname = ""

    while True:
        try:
            trackinfo = requests.get(LASTFM_API_URL.format(user=config["lastfm_name"],
                                                           key=config["lastfm_api_key"])).json()
            trackinfo = trackinfo["recenttracks"]["track"][0]

            album_text = trackinfo["album"]["#text"]
            album_name = album_text.replace(" ", "_").lower()[:32]

            if album_name not in album_cache and album_name:
                print(f"{album_text} not found in album cache, caching...")
                cover_img = requests.get(trackinfo["image"][1]["#text"]).content
                cover_img = "data:image/jpeg;base64," + str(base64.b64encode(cover_img), "utf-8")
                requests.post(DISCORD_API_POST_URL.format(client_id=config["client_id"]),
                              json={"name": album_name,
                                    "image": cover_img,
                                    "type": 1},
                              headers={"Authorization": config["discord_token"],
                                       "content-type": "application/json"})
                album_cache.append(album_name)
                with open("album_cache.p", "wb") as f:
                    pickle.dump(album_cache, f)

            rpc.update(details=album_text if album_text else "Single",
                       state=f"{trackinfo['artist']['#text']} - {trackinfo['name']}",
                       large_image=album_name if album_name else None)

            if old_trackname != trackinfo["name"]:
                print(f"updating rpc with current track {trackinfo['name']}...")
                old_trackname = trackinfo["name"]

            time.sleep(0.5)

        except Exception as e:
            print("exception occurred:", e)


if __name__ == '__main__':
    print("starting listening-to...")
    main()

from datetime import datetime
import warnings
from flask import Flask, redirect, session
from flask import render_template
from flask import request
import uuid
from rq_win.worker import WindowsWorker

from flask_session import Session
from flask.json import jsonify
from related_artist import RelatedArtistsFinderSpotipy, get_spotify
from config import *
from authorize_spotify import *
from generate_playlist import generate_playlist

user_state = {

}

app = Flask(__name__)
app.secret_key = "ahhhhh its a secret"
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


spotify =  get_spotify()
related_artist_finder = RelatedArtistsFinderSpotipy(spotify)

from redis import Redis
from rq import Queue, Connection, Worker
import redis


redis_host = "redis-15044.c278.us-east-1-4.ec2.cloud.redislabs.com"
redis_port = 15044
redis_password = "sPSPqmznaof65h2ltypLo9Bn1U29oLs1"



redis_conn = Redis(redis_host, redis_port, password = redis_password)
generate_playlist_queue = Queue(connection=redis_conn, ) 




   

@app.route("/")
def hello_world():
    session.clear()
    print(session)
    return render_template("main.html")

@app.route("/related_artist", methods = ['GET'])
def get_related_artist():
    return render_template("related_artist.html")

@app.route("/relatedartists", methods = ['POST'])
def get_related_artists():
    params = request.json
    relativity = int(params["relativity"])
    thoroughness = int(params["thoroughness"])
    algorithm:str = params["algorithm"].lower()
    results = related_artist_finder.search(starting_artists = params["artistURI"], selection_method = algorithm, max_layer = relativity, max_searches_per_layer = thoroughness)
    return jsonify(results)

@app.route("/search_artists/<artist>", methods = ['GET'])
def get_search_suggestions(artist):
    results = related_artist_finder.spotify.search(artist, type = "artist")
    results = [(suggest["name"], suggest["uri"], suggest["id"]) for suggest in results["artists"]["items"]]
    return jsonify(results)

@app.route("/login_to_spotify", methods = ['GET'])
def login_to_spotify():
    """Login to spotify"""
    state = uuid.uuid1()
    scope = 'user-read-private user-read-email playlist-modify-private playlist-modify-public'
    redirect_uri = request.base_url.replace("/login_to_spotify", "/related_artist_playlist_generator")
    print("Redirect uri", redirect_uri)
    return redirect_to_spotify_login(state, scope, redirect_uri)

@app.route("/related_artist_playlist_generator", methods = ["GET"])
def get_related_artist_playlist_generator():
    if ("access_token" not in session.keys() or "access_token_expiration_date" not in session.keys()) and "code" not in request.args:

        return redirect("/login_to_spotify")

    elif(("access_token" not in session.keys() or "access_token_expiration_date" not in session.keys()) and "code" in request.args):
        #get access code
        print("Getting access token from authorization code.")
        access_token_details = get_access_token(request.args["code"], request.base_url)
        print("User logged in with an access code of.", access_token_details["access_token"])
        session["access_token"] = access_token_details["access_token"]
        session["access_token_expiration_date"] = int(datetime.now().timestamp()) + int(access_token_details["expires_in"])
        session["refresh_token"] = access_token_details["refresh_token"]

    elif("access_token" in session.keys() and session["access_token_expiration_date"] < int(datetime.now().timestamp())):
        print("Access token expired for user. Sending refresh token.")
        access_token_details = get_refresh_token(session["refresh_token"])
        session["access_token"] = access_token_details["access_token"]
        session["access_token_expiration_date"] = int(datetime.now().timestamp()) + int(access_token_details["expires_in"])
        print("User logged in with an access code of.", access_token_details["access_token"])


    return render_template("generate_playlist.html")

@app.route("/related_artist_playlist_generator", methods = ["POST"])
def post_related_artist_playlist_generator():
    if "access_token" not in session.keys():
        return redirect("/login_to_spotify")
    params = request.json
    artist = params["artistID"]
    playlist_name = params["playlistName"]
    max_popularity = int(params["maxPopularity"])
    max_followers = int(params["maxFollowers"])
    artist_selection_method = params["artistSelectionMethod"]
    generate_playlist_queue.enqueue(generate_playlist, artist_id = artist, artist_selection_method = artist_selection_method, max_popularity = max_popularity, max_followers = max_followers, playlist_name = playlist_name, access_token = session["access_token"])


    


    return "1"
    




with Connection(redis_conn):
    print(1)
    try:
        w = Worker(["default"])
    except:
        warnings.warn("rq worker does not work on windows. Using windows compatible version.")
        w = WindowsWorker(["default"])
    w.work()

if __name__ == "__main__":  
    app.run()
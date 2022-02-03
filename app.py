from datetime import datetime
from flask import Flask, make_response, redirect, url_for, session
from flask import render_template
from flask import request
import uuid
from flask_session import Session
from requests.exceptions import RequestException
from flask.json import jsonify
from related_artist import RelatedArtistFinder, RelatedArtistsFinderSpotipy, get_spotify, PlaylistGenerator
from config import *
from authorize_spotify import *


user_state = {

}

app = Flask(__name__)
app.secret_key = "ahhhhh its a secret"
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


spotify =  get_spotify()
related_artist_finder = RelatedArtistsFinderSpotipy(spotify)



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


    #Find related artists
    related_artists = RelatedArtistFinder(session["access_token"], artist, artist_selection_method, 4, 3000, max_popularity, max_followers)

    try:
        print("User attempting to find related artists tree.")
        related_artists.search()
    except RequestException as err:
        app.logger.error("Error encountered while searching for related artists. Exception: " + str(err.response.status_code) + " " + err.response.reason)
        return str(err.response.status_code)
    
    #Generate and save playlist
    generated_playlist = PlaylistGenerator(session["access_token"], related_artists.artist_ids, playlist_name)

    try:
        print("User attempting to generate playlist.")
        generated_playlist.generate_playlist()
    except RequestException as err:
        app.logger.error("Error encountered while generating playlist. Exception: " + str(err.response.status_code) + " " + err.response.reason)
        return "0"

    try:
        print("User attempting to save playlist.")
        generated_playlist.save_playlist()
    except RequestException as err:
        app.logger.error("Error encountered while saving playlist. Exception: " + str(err.response.status_code) + " " + err.response.reason)
        return "0"

    print("Successfully generated playlist for", generated_playlist.user_id)


    return "1"
    





if __name__ == "__main__":  
    app.run()
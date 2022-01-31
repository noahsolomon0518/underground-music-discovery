import ast
from flask import Flask, make_response, redirect, url_for, session
from flask import render_template
from flask import request
import uuid
import requests
from flask_session import Session

from urllib import parse
from flask.json import jsonify
from related_artist import UnpopularRelated, get_spotify
from config import *
from authorize_spotify import *


#Can control 
user_state = {

}

app = Flask(__name__)
app.secret_key = "ahhhhh its a secret"
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


spotify =  get_spotify()
related_artist_finder = UnpopularRelated(spotify)



@app.route("/")
def hello_world():
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
    results = [(suggest["name"], suggest["uri"]) for suggest in results["artists"]["items"]]
    return jsonify(results)

@app.route("/login_to_spotify", methods = ['GET'])
def login_to_spotify():
    """Login to spotify"""
    state = uuid.uuid1()
    scope = 'user-read-private user-read-email';
    redirect_uri = request.base_url.replace("/login_to_spotify", "/related_artist_playlist_generator")
    app.logger.info("Redirect uri %s", redirect_uri)
    return redirect_to_spotify_login(state, scope, redirect_uri)

@app.route("/related_artist_playlist_generator", methods = ["GET"])
def related_artist_playlist_generator():
    if "access_token" not in session.keys() and "code" not in request.args:
        return redirect("/login_to_spotify")
    elif("access_token" not in session.keys() and "code" in request.args):
        #get access code
        app.logger.info("Getting access code")
        access_token = get_access_token(request.args["code"], request.base_url)
        app.logger.info("User logged in with an access code of %s", access_token)
        session["access_token"] = access_token
    return render_template("generate_playlist.html")



if __name__ == "__main__":  
    app.run()
import ast
from wsgiref import headers
from xmlrpc.client import ResponseError
from flask import Flask, make_response, redirect, url_for
from flask_caching import Cache
from flask import render_template
from flask import request
import base64
import uuid
import json
import requests
from urllib import parse, response
from flask.json import jsonify
from related_artist import CLIENT_SECRET, UnpopularRelated, get_spotify


#Can control 
user_state = {

}

app = Flask(__name__)

spotify =  get_spotify()
related_artist_finder = UnpopularRelated(spotify)

CLIENT_ID = "9e774700a78045659ac8d6d8c5a182fa"

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
    print(results)
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
    client_ID = CLIENT_ID
    scope = 'user-read-private user-read-email';
    redirect_uri = request.base_url.replace("/login_to_spotify", "/generate_playlist")
    
    return redirect("https://accounts.spotify.com/authorize?"+parse.urlencode({
        "state":state,
        "scope": scope,
        "redirect_uri": redirect_uri,
        "client_id": client_ID,
        "response_type": "code"
    }))

@app.route("/generate_playlist", methods = ["GET"])
def get_tokens():
    """Gets tokens for spotify api"""
    errors = None
    if("code" not in request.args.keys()):
        return jsonify({"status": 400})
    else:
        string = CLIENT_ID + ":" + CLIENT_SECRET
        string_bytes = string.encode("ascii")
        base64_bytes = base64.b64encode(string_bytes)
        base64_string = base64_bytes.decode("ascii")
        redirect_uri = request.base_url
        body = {
            "grant_type": "authorization_code",
            "code": request.args["code"],
            "redirect_uri": redirect_uri
        }
        headers = {
            "Authorization": "Basic " + base64_string,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post("https://accounts.spotify.com/api/token", data=body, headers=headers) 
        access_token = ast.literal_eval(response.text)
        return access_token


@app.route("/generate_playlist", methods = ["GET"])
def generate_playlist():
    """After log into spotify sent to this page which generates playlist"""
    if("code" not in request.args):
        return make_response("ERROR: Must login to spotify", 401)
    tokens = requests.get(request.base_url, params=request.args).text
    dict_token = ast.literal_eval(tokens.replace("\\", "").rstrip("\"").lstrip("\""))
    print(dict_token)

    return render_template("generate_playlist", token = dict_token)


if __name__ == "__main__":  
    app.run()
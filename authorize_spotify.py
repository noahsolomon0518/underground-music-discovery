import requests
import base64
from config import *
from flask import redirect
from urllib import parse

def get_access_token(code, redirect_uri):
    string = CLIENT_ID + ":" + CLIENT_SECRET
    string_bytes = string.encode("ascii")
    base64_bytes = base64.b64encode(string_bytes)
    base64_string = base64_bytes.decode("ascii")
    redirect_uri = redirect_uri
    body = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }
    headers = {
        "Authorization": "Basic " + base64_string,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post("https://accounts.spotify.com/api/token", data=body, headers=headers) 
    access_token = response.json()["access_token"]
    return access_token


def redirect_to_spotify_login(state, scope, redirect_uri):
    return redirect("https://accounts.spotify.com/authorize?"+parse.urlencode({
        "state":state,
        "scope": scope,
        "redirect_uri": redirect_uri,
        "client_id": CLIENT_ID,
        "response_type": "code"
    }))
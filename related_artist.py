from itertools import chain
import logging
import random
from urllib import response
import requests
from requests.exceptions import RequestException
from typing import Dict, Iterable, List, Union
from flask import Response, request
import spotipy
from spotipy.client import Spotify
import numpy as np
from config import *



birdy_uri = 'spotify:artist:2WX2uTcsvV5OnS0inACecP'
aldn_uri = "https://open.spotify.com/artist/2GUw9Wzha61PkZoRVv1PDD?si=Ov8MB150R0ONxByCv25EQg"
luke_uri = "https://open.spotify.com/artist/0BvkDsjIUla7X0k6CSWh1I?si=NxDIShP3QsuyV2IWBuoyVQ"
dylan_uri = "https://open.spotify.com/artist/2Cm6C9PNHioyjRKBfO7n9N?si=39hcxwJuSIeB6nRKTbCR6w"
brevin_uri = "https://open.spotify.com/artist/7lU8Gtn7moZmPqqu4oPkEh?si=vzbZe3EgScyEECqfrmJECQ"

def get_unpopular_related_artist(spotify: Spotify, artist_id):
  artist = spotify.artist(artist_id)
  return get_related_recursively(spotify, [artist], [artist], 0)


def get_related_recursively(spotify:Spotify, artist_id, layer_num = 0, max_layer = 3, artist_cache = []):
  
  related = spotify.artist_related_artists(artist_id)
  print(related)
  related = np.random.choice(related["artists"], min(5, len(related["artists"])), replace=False)
  related_artist_ids = [{"id":artist["id"], "popularity":artist["popularity"]} for artist in related if artist["id"] not in artist_cache]
  print(len(related_artist_ids))
  artist_cache.extend([artist["id"] for artist in related_artist_ids])
  if(layer_num<max_layer):
    return [] + [get_related_recursively(spotify, artist_id["id"], layer_num+1, max_layer, artist_cache) for artist_id in related_artist_ids]
  return [artist_id for artist_id in related_artist_ids]
  

class RelatedArtistsFinderSpotipy:
  """Gets unpopular artist related to an artist. Uses spotipy and does not require client to authenticate"""
  def __init__(self, spotipy: Spotify) -> None:
      self.spotify = spotipy
      self.number_of_artists_searched = 0 
      self.starting_artist = None
      self.max_artists = None
      self.max_layer = None
      self.max_followers = None
      self.max_popularity = None
      self.genres = None
      self.max_searches_per_layer = None
      self.selection_method = None
      self.searched = []
      self.qualifying_artists = []


  def search(self, starting_artists: Union[str, List[str]], max_artists = None, max_popularity = None, max_followers = None, genres = None, selection_method = "random", max_layer = 3, max_searches_per_layer = 5):
    self.starting_artists = starting_artists if type(starting_artists) == list else [starting_artists]
    self.selection_method = selection_method
    self.max_artists = max_artists
    self.max_popularity = max_popularity
    self.max_followers = max_followers
    self.genres = genres
    self.max_layer = max_layer
    self.number_of_artists_searched = 0 

    self.max_searches_per_layer = max_searches_per_layer
    self.qualifying_artists = []
    self.searched = []
    self._get_related_recursively(self.starting_artists)
    return self.qualifying_artists
  
  def _get_related_recursively(self, artists_ids: List, layer = 0):
    if(layer == self.max_layer):
      return
    for artist_id in artists_ids:
      self.number_of_artists_searched += 1 
      print(self.number_of_artists_searched)
      related =  self.spotify.artist_related_artists(artist_id)
      selected_artists = self._select_artists(related["artists"])    #artists to be searched next
      filtered_artists = self._filter_artists(selected_artists)     #qualifying artists
      if list(filtered_artists):
        self.qualifying_artists.extend([
          dict(
            name=artist["name"],
            url=artist["external_urls"]["spotify"],
            id=artist["id"],
            popularity=artist["popularity"],
            followers=artist["followers"]["total"],
            genres=artist["genres"]
          ) for artist in filtered_artists
        ])
      
      self._get_related_recursively([select["id"] for select in selected_artists], layer+1)


  def _filter_artists(self, artists):
    """Returns artists that fit restrainsts"""
    if(self.genres != None):
      artists = [artist for artist in artists if set(self.genres).intersection(artist["genres"])]
    if(self.max_popularity != None):
      artists = [artist for artist in artists if artist["popularity"]<self.max_popularity]
    if(self.max_followers != None):
      artists = [artist for artist in artists if artist["followers"]<self.max_followers]

    return artists



  def _select_artists(self, artists):
    """Determines which artists will be searched next"""
    artists = [artist for artist in artists if artist["name"] not in self.searched]
    if(self.selection_method == "random"):
      selected = np.random.choice(artists, min(self.max_searches_per_layer, len(artists)), replace=False)
    elif(self.selection_method == "lowest_popularity"):
      selected = list(sorted(artists, key=lambda x: x["popularity"]))[:self.max_searches_per_layer]
    elif(self.selection_method == "lowest_followers"):
      selected = list(sorted(artists, key=lambda x: x["followers"]["total"]))[:self.max_searches_per_layer]

    self.searched.extend([select["name"] for select in selected])
    return selected
  @property
  def sorted_by_popularity(self):
    return list(sorted(self.qualifying_artists, key=lambda x: x["popularity"]))
    
  @property
  def sorted_by_followers(self):
    return list(sorted(self.qualifying_artists, key=lambda x: x["followers"]))


def get_spotify():
  return Spotify(client_credentials_manager= spotipy.SpotifyClientCredentials(CLIENT_ID, CLIENT_SECRET))
    

class RelatedArtistFinder:
  """Finds related artists. Requires authentication"""
  def __init__(self, access_token, artist_id, artist_selection_method = "random", max_searches_per_artist = 4, number_of_artists = 100, max_popularity = 100, max_followers = 100_000_000):
    self.searched = []
    self.qualifying_artists = []
    self.qualifying_artists_ids = []
    self.artist_id = artist_id
    self.access_token = access_token
    self.max_searches_per_artist = max_searches_per_artist
    self.artist_selection_method = artist_selection_method
    self.max_popularity = max_popularity
    self.max_followers = max_followers
    self.number_of_artists = number_of_artists
    self.authorization_header = self.get_authorization_header()

  def get_authorization_header(self):
    return {
      "Authorization": "Bearer " + self.access_token,
      "Content-Type": "application/json"
    }

  def get_related_artists(self, artist_id):
    related_artists = requests.get(f"https://api.spotify.com/v1/artists/{str(artist_id)}/related-artists", headers= self.authorization_header)

    related_artists.raise_for_status()
    return related_artists.json()["artists"]




  def search(self):
    """Searches related artist tree"""
    n = 0
    self.searched = []
    self.qualifying_artists = []
    self.qualifying_artists_ids = []
    artists_to_be_searched = self.artist_id
    while n <= self.number_of_artists and artists_to_be_searched:
      current_artists_from_layer = self._get_related_artist_layer(artists_to_be_searched)
      qualifying_artists_from_layer = self._filter_artists(list(chain.from_iterable(current_artists_from_layer.copy())))
      self.qualifying_artists.extend(qualifying_artists_from_layer)
      n += len(qualifying_artists_from_layer)
      print(str(n) + " artists found.")
      if(n <= self.number_of_artists):
        artists_to_be_searched = self._select_artists(current_artists_from_layer)
    return "1"

    
    

  def _get_related_artist_layer(self, artist_ids: List):
    """Gets one layer of related artist"""
    if(type(artist_ids)!=list):
      artist_ids = [artist_ids]
    return [self.get_related_artists(artist_id) for artist_id in artist_ids if artist_id]
    

  
  def _filter_artists(self, artists: List):
    qualifying_artists = []
    for artist in artists:
      if(artist["popularity"] <= self.max_popularity and artist["followers"]["total"] <= self.max_followers and artist["id"] not in self.qualifying_artists_ids):
        
        qualifying_artists.append(artist)
        self.qualifying_artists_ids.append(artist["id"])

    return qualifying_artists
  

  def _select_artists(self, artists: List[List]):
      """Determines which artists will be searched next"""
      selected = []
      for partition in artists:
        potential_selected = [artist for artist in partition if artist["id"] not in self.searched]
        if(self.artist_selection_method == "random"):
          selected_in_partition = np.random.choice(potential_selected, min(self.max_searches_per_artist, len(potential_selected)), replace=False)
        elif(self.artist_selection_method == "popularity"):
          selected_in_partition = list(sorted(potential_selected, key=lambda x: x["popularity"]))[:self.max_searches_per_artist]
        elif(self.artist_selection_method == "followers"):
          selected_in_partition = list(sorted(potential_selected, key=lambda x: x["followers"]["total"]))[:self.max_searches_per_artist]
        selected_in_partition_ids = [select["id"] for select in selected_in_partition]
        selected.extend(selected_in_partition_ids)
        self.searched.extend(selected_in_partition_ids)
      return selected

  def __getitem__(self, ind):
    if(type(ind) != int):
      raise IndexError("Indices must be integers")
    if(len(self.qualifying_artists) == 0):
      raise IndexError("No qualifying related artist in list. Either none were found in previous search or search was never called.")
    return self.qualifying_artists[ind]

  @property
  def artist_ids(self):
    return self.qualifying_artists_ids

  def __str__(self):
    return str(self.qualifying_artists)
    
  def __len__(self):
    return len(self.qualifying_artists)
    


class PlaylistGenerator:
  """Class generates a playlist based on provided. Song selection method can either be random or most_popular"""
  def __init__(self, access_token, artist_ids: Iterable[Dict], playlist_name):
    self.playlist_name = playlist_name
    self.access_token = access_token
    self.artist_ids = random.sample(artist_ids, min((100, len(artist_ids))))    #limit to 100 artists
    self.playlist = []
    self.authorization_header = self.get_authorization_header()
    self.user_id = None

  def get_authorization_header(self):
    return {
      "Authorization": "Bearer " + self.access_token,
      "Content-Type": "application/json"
    }


  def generate_playlist(self):
    """Generates playlists by finding each song """
    self.playlist = []
    for id in self.artist_ids:
      song_uri = self._find_song(id)
      if(song_uri):
        self.playlist.append(song_uri)
    


  def save_playlist(self):
    """Creates and adds songs to users account playlist to users account"""
    if(len(self.playlist)==0):
      raise BaseException("No songs in playlists")

    user_id_request = requests.get("https://api.spotify.com/v1/me", headers=self.authorization_header)
    user_id_request.raise_for_status()
    logging.info("Get user id -> %s", user_id_request.status_code)
    user_id = user_id_request.json()["id"]
    self.user_id = user_id
    logging.info("user_id = %s", user_id)

    playlist_id_request = requests.post(f"https://api.spotify.com/v1/users/{user_id}/playlists", headers=self.authorization_header, json={"name":self.playlist_name})
    playlist_id_request.raise_for_status()
    logging.info("Create playlist -> %s", playlist_id_request.status_code)
    logging.info(playlist_id_request.text)
    playlist_id = playlist_id_request.json()["id"]


    add_tracks_request = requests.post(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", headers=self.authorization_header, json={"uris":self.playlist})
    add_tracks_request.raise_for_status()
    logging.info("Add tracks to playlist -> %s", add_tracks_request.status_code)


    

    


  def _find_song(self, artist_id):
    """Finds song from an artist randomly from top tracks"""
  
    response = requests.get(f"https://api.spotify.com/v1/artists/{str(artist_id)}/top-tracks", headers= self.authorization_header, params={"market":"US"})
    response.raise_for_status()
    track_uris = [track["uri"] for track in response.json()["tracks"]]
    track_uri = track_uris[random.choice(range(len(track_uris)))] if len(track_uris) > 0 else None
    return track_uri
  
  def __str__(self) -> str:
      return str(self.playlist)


  

    







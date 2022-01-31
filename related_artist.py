from typing import List, Union
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
  

class UnpopularRelated:
  """Gets unpopular artist related to an artist"""
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
    




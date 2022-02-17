from related_artist import RelatedArtistFinder, PlaylistGenerator
from requests.exceptions import *





def generate_playlist(artist_id, artist_selection_method, max_followers, max_popularity, playlist_name, access_token):
    """Can generate playlist in a end point without waiting for reponse"""
    print("GENERATING PLAYLIST")
    related_artists = RelatedArtistFinder(access_token, artist_id, artist_selection_method, 4, 100, max_popularity, max_followers)

    try:
        print("User attempting to find related artists tree.")
        related_artists.search()
    except RequestException as err:
        print("Error encountered while searching for related artists. Exception: " + str(err.response.status_code) + " " + err.response.reason)
        return str(err.response.status_code)
    
    #Generate and save playlist
    generated_playlist = PlaylistGenerator(access_token, related_artists.artist_ids, playlist_name)

    try:
        print("User attempting to generate playlist.")
        generated_playlist.generate_playlist()
    except RequestException as err:
        print("Error encountered while generating playlist. Exception: " + str(err.response.status_code) + " " + err.response.reason)
        return "0"

    try:
        print("User attempting to save playlist.")
        generated_playlist.save_playlist()
    except RequestException as err:
        print("Error encountered while saving playlist. Exception: " + str(err.response.status_code) + " " + err.response.reason)
        return "0"

    print("Successfully generated playlist for", generated_playlist.user_id)
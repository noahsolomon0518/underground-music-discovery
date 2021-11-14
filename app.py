from flask import Flask
from flask import render_template
from flask import request
from flask.json import jsonify
from related_artist import UnpopularRelated, get_spotify
app = Flask(__name__)
spotify =  get_spotify()
related_artist_finder = UnpopularRelated(spotify)


@app.route("/")
def hello_world():
    return render_template("main.html")

@app.route("/relatedartists", methods = ['POST'])
def get_related_artists():
    params = request.json
    relativity = 2*int(params["relativity"])
    thoroughness = 2*int(params["thoroughness"])
    algorithm:str = params["algorithm"].lower()
    results = related_artist_finder.search(starting_artists = params["artistURI"], selection_method = algorithm, max_layer = relativity, max_searches_per_layer = thoroughness)
    print(results)
    return jsonify(results)


if __name__ == "__main__":  
    app.run()
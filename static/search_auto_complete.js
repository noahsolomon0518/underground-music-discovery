function autocomplete(obj, arr) {
    console.log("hello worldsas")

    options = ""
    arr.forEach(element => {
        options += "<option value = \""+ element+ "\"></option>"
    })
    document.getElementById("artist-data").innerHTML = options
    console.log(options)
}
    
document.getElementById("artist-uri").addEventListener("keydown", (event)=>{
    console.log("searching artist")
    search = document.getElementById("artist-uri").value
    console.log(search)
    var xhr = new XMLHttpRequest();
    xhr.open("GET", '/search_artists/'+search);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () { // Call a function when the state changes.
        if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
            artists = JSON.parse(this.response)
            console.log(artists)
            autocomplete(document.getElementById("artist-uri"), artists.map((element)=>element[0]) );
        }
    }
    xhr.send()
    
})





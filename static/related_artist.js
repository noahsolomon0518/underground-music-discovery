var script = document.createElement('script');
script.src = 'https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js';
script.type = 'text/javascript';
document.getElementsByTagName('head')[0].appendChild(script);
artistMap = {}


function jsonToCSV(json){
    const items = json
    const replacer = (key, value) => value === null ? '' : value // specify how you want to handle null values here
    const header = Object.keys(items[0])
    const csv = [
    header.join(','), // header row first
    ...items.map(row => header.map(fieldName => JSON.stringify(row[fieldName], replacer)).join(','))
    ].join('\r\n')
    return csv
}

function waitAnimationForSearch (element, searchElement, waitingTime = 200) {
    //elements' text will animate ...
    if (!(searchElement.isSearching)) {
        element.innerHTML = "Search"
    } else {
        element.innerHTML = element.innerHTML.split(".").length - 1 == 3? "Searching": element.innerHTML + "."
        console.log(element.value.split(".").length - 1)
        setTimeout(waitAnimationForSearch, waitingTime, element, searchElement, waitingTime); // try again in 300 milliseconds
    }
}


tableButtons = `
<div class="fluid-container">
                <div class="row">
                    <div class="col-1">
                        <select id="sort-by" onchange="table.sortBy(this.value)" class="form-select form-select-sm mb-3" aria-label=".form-select-lg example">
                            <option selected>Sort By</option>
                            <option value="random">Random</option>
                            <option value="popularity">Popularity</option>
                            <option value="followers">Followers</option>
                        </select>
                    </div>
                    <div class="col-1">
                        <a id = "to-csv" class="btn btn-outline-secondary btn-sm" style="width: 100%; margin: 0px; background-color: white; border-color: gainsboro;">To CSV</a>
                    </div>
                    <div class="col-1">
                        <a class="btn btn-outline-secondary btn-sm" style="width: 100%; margin: 0px; background-color: white; border-color: gainsboro;" data-toggle="modal" data-target="#exampleModalCenter">
                            Generate Playlist
                        </a>
                    </div>
                </div>
            </div>
`

class Table {

    static HTML_ID = "search-results-table"
 

    constructor() {
        this.html_id = Table.HTML_ID
        this.table = document.getElementById(this.html_id)
        this.tableData = null
        this.isSearching = false
    }

    #getInputData() {
        var artistURI = document.getElementById("artist-uri").value
        var algorithm = document.getElementById("algorithm").value
        return {
            artistURI: artistMap[artistURI],
            algorithm: algorithm,
            relativity: 4,
            thoroughness: 4
        }
    }

    #getRelatedArtistData(inputData) {
        return new Promise(resolve => {
            setTimeout(() => {
                var xhr = new XMLHttpRequest();
                xhr.open("POST", '/relatedartists', true);
                xhr.setRequestHeader("Content-Type", "application/json");
                xhr.onreadystatechange = function () { // Call a function when the state changes.
                    if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                        resolve(JSON.parse(this.response))
                    }
                }
                xhr.send(JSON.stringify(inputData))
                
            }, 2000)
        })


    }

    #updateTableData(tableData, fields) {

        var rows = ''
        var body = ""
        var header = "<thead><tr>"
        var table = ""

        $.each(fields, function (index, field) {
            header += "<th style = \"text-align: center;\">" + field + "</th>"
        })

        header += "</tr></thead>"

        table += header

        body = "<tbody>"
        $.each(tableData, function (index, item) {
            if(index<50){
                var row = '<tr>';
                $.each(fields, function (index, field) {
                    if(field == "name"){
                        row += '<td style = "text-align: center;"><a target="_blank" style = "text-decoration: none;" href = ' + item["url"] + '>' + item[field + ''] + '</a></td>';
                    }else{
                        row += '<td style = "text-align: center;">' + item[field + ''] + '</td>';
                    }
                })
                rows += row + '</tr>'
            }
        })
        body += rows + "</tbody>"

        table += body
        this.tableData = tableData

        $('#' + this.html_id).html(table)
        $('#' + "table-buttons").html(tableButtons)
        $('#' + "to-csv").attr("href", 'data:text/csv;charset=utf-8,' + encodeURI(jsonToCSV(this.tableData)))
    
    }

    async search() {
        var inputData = this.#getInputData()

        if(typeof(inputData["artistURI"])!="undefined"){
            this.isSearching = true

            var searchButton = document.getElementById("search-button")
            waitAnimationForSearch(searchButton, this)
            searchButton.innerHTML = "Searching"
            var data = await this.#getRelatedArtistData(inputData)
            this.isSearching = false
            this.#updateTableData(data, ["name", "popularity", "followers"])
        }
        
        
    }


    sortBy(method){
        var sorted = null
        if(method == "popularity" || method == "followers"){
            sorted = this.tableData.sort((a,b) => a[method] - b[method])
        }
        if(method == "random"){

            var array = this.tableData
            for (var i = array.length - 1; i > 0; i--) {
                var j = Math.floor(Math.random() * (i + 1));
                var temp = array[i];
                array[i] = array[j];
                array[j] = temp;
            }
            sorted = array
        }
        if(sorted != null){
            this.#updateTableData(sorted, ["name", "popularity", "followers"])
        }
    }



}

var table = new Table()











function autocomplete(obj, arr) {

    options = ""
    arr.forEach(element => {
        options += "<option value = \"" + element[0] + "\"><data value = \""+ element[1] +"\"></option>"
    })
    document.getElementById("artist-data").innerHTML = options
}

function updateDict(artistAndURI){
    artistMap = {}
    artistAndURI.forEach((element) => {
        if (!(element[0] in artistMap)){
            artistMap[element[0]] = element[1]
        }
    })

}

    
document.getElementById("artist-uri").addEventListener("keyup", (event)=>{
    search = document.getElementById("artist-uri").value
    console.log(search.replace(/\s/g, '').length)
    if(search.replace(/\s/g, '').length != 0 ){
        var xhr = new XMLHttpRequest();
        xhr.open("GET", '/search_artists/'+search);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onreadystatechange = function () { // Call a function when the state changes.
            if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                artists = JSON.parse(this.response)
                console.log(artists)
                autocomplete(document.getElementById("artist-uri"), artists.map((element)=>element) );
                updateDict(artists)
            }else {
                console.log("Error", this.status);
            }
        }
        xhr.send()

    }

})
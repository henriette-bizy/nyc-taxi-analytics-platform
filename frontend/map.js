// initialize the map and attach it to Id = "map"

var map = L.map("map");

// set the view to a specific latitude, longitude and zoom level respectively
map.setView([40.7128, -74.006], 12);

// add the actual map graphics to the map using OpenStreetMap tiles
// max zoom allowed is 19
// attribution is required by OpenStreetMap
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution:
    '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

// ask the browswer to watch the user's position continuously
// and call the "success" function when a new position is available
// or the "error" function when there is an error
navigator.geolocation.watchPosition(success, error);

//make known variables to hold the marker and circle
let marker, circle;

// to ensure that the map zooms to the user's location
let zoomed = false;

// this function is called when a new position is available
function success(pos) {
  const lat = pos.coords.latitude; //get latitude
  const lng = pos.coords.longitude; //get longitude
  const accuracy = pos.coords.accuracy; //get accuracy in meters

  // if there is an existing marker and circle, remove them
  if (marker) {
    map.removeLayer(marker);
    map.removeLayer(circle);
  }

  // add a marker and circle to the map at the new location
  marker = L.marker([lat, lng]).addTo(map);
  circle = L.circle([lat, lng], { radius: accuracy }).addTo(map);

  // if this is the first time we are getting the location, zoom to it
  if (!zoomed) {
    zoomed = map.fitBounds(circle.getBounds());
  }

  // set the map view to the new location
  map.setView([lat, lng]);
}

// this function is called when there is an error getting the location
function error(err) {
  if (err.code == 1) {
    //permission denied
    alert("Please allow geolocation access");
  } else {
    //other errors
    alert("Cannot get your location");
  }
}

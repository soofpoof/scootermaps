const API_BASE = "http://127.0.0.1:8000";
const AMSTERDAM = { lat: 52.3676, lon: 4.9041 };

const map = new maplibregl.Map({
  container: "map",
  style: {
    version: 8,
    sources: {
      osm: {
        type: "raster",
        tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
        tileSize: 256,
        attribution: "© OpenStreetMap contributors",
      },
    },
    layers: [{ id: "osm", type: "raster", source: "osm" }],
  },
  center: [AMSTERDAM.lon, AMSTERDAM.lat],
  zoom: 13,
});

map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

let fromPoint = null;
let toPoint = null;
let fromMarker = null;
let toMarker = null;

function selectedProfile() {
  return document.querySelector('input[name="profile"]:checked').value;
}

function setInstruction(text) {
  document.getElementById("instructions").textContent = text;
}

function setStats(distance_m, duration_s) {
  const stats = document.getElementById("stats");
  if (distance_m == null || duration_s == null) {
    stats.hidden = true;
    return;
  }
  const km = (distance_m / 1000).toFixed(2);
  const min = Math.round(duration_s / 60);
  document.getElementById("stat-distance").textContent = `${km} km`;
  document.getElementById("stat-duration").textContent = `${min} min`;
  stats.hidden = false;
}

function clearRoute() {
  if (map.getLayer("route")) map.removeLayer("route");
  if (map.getSource("route")) map.removeSource("route");
}

function reset() {
  fromMarker?.remove();
  toMarker?.remove();
  fromMarker = null;
  toMarker = null;
  fromPoint = null;
  toPoint = null;
  clearRoute();
  setStats(null, null);
  setInstruction(
    "Click the map: first click sets the start, second click sets the destination."
  );
}

function drawRoute(geometry) {
  clearRoute();
  map.addSource("route", { type: "geojson", data: geometry });
  map.addLayer({
    id: "route",
    type: "line",
    source: "route",
    layout: { "line-join": "round", "line-cap": "round" },
    paint: { "line-color": "#ff5a36", "line-width": 5 },
  });
}

async function fetchRoute() {
  if (!fromPoint || !toPoint) return;
  const url =
    `${API_BASE}/route` +
    `?from_lat=${fromPoint.lat}&from_lon=${fromPoint.lng}` +
    `&to_lat=${toPoint.lat}&to_lon=${toPoint.lng}` +
    `&profile=${selectedProfile()}`;

  setInstruction("Computing route…");
  try {
    const res = await fetch(url);
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`HTTP ${res.status} · ${body}`);
    }
    const data = await res.json();
    drawRoute(data.geometry);
    setStats(data.distance_m, data.duration_s);
    setInstruction(`Route drawn for ${data.profile}.`);
  } catch (err) {
    setInstruction(
      `Failed to fetch route: ${err.message}. Is the backend running on ${API_BASE}?`
    );
  }
}

map.on("click", (e) => {
  if (!fromPoint) {
    fromPoint = e.lngLat;
    fromMarker = new maplibregl.Marker({ color: "#15a36a" })
      .setLngLat(e.lngLat)
      .addTo(map);
    setInstruction("Start set. Click again to set the destination.");
  } else if (!toPoint) {
    toPoint = e.lngLat;
    toMarker = new maplibregl.Marker({ color: "#d62828" })
      .setLngLat(e.lngLat)
      .addTo(map);
    fetchRoute();
  } else {
    reset();
  }
});

document.getElementById("reset").addEventListener("click", reset);
document.querySelectorAll('input[name="profile"]').forEach((el) => {
  el.addEventListener("change", () => {
    if (fromPoint && toPoint) fetchRoute();
  });
});

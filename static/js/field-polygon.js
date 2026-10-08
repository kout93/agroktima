/* Επεξεργαστής περιγράμματος κτήματος: κλικ στον χάρτη (δορυφορικό ή
   δρόμων) για να προσθέσεις σημεία, ή εισαγωγή συντεταγμένων από κείμενο
   (π.χ. από τοπογραφικό), με αυτόματο υπολογισμό εμβαδού σε στρέμματα. */
function initFieldPolygon(opts) {
  var initialPoints = opts.initialPoints || [];
  var centerLat = opts.centerLat || 38.2;
  var centerLng = opts.centerLng || 23.8;
  var zoom = initialPoints.length ? 19 : 6;

  var streets = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 23, maxNativeZoom: 19, attribution: '&copy; OpenStreetMap συνεισφέροντες'
  });
  var satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 24, maxNativeZoom: 19, attribution: 'Πλακίδια &copy; Esri — Source: Esri, Maxar, Earthstar Geographics'
  });

  var startCenter = initialPoints.length ? initialPoints[0] : [centerLat, centerLng];
  var map = L.map(opts.mapDivId, { layers: [satellite], maxZoom: 24 }).setView(startCenter, zoom);
  L.control.layers({ "Δορυφορικός": satellite, "Δρόμοι (OpenStreetMap)": streets }).addTo(map);

  var points = initialPoints.slice();
  var polygon = null;
  var markers = [];

  function metersPerDegree(lat) {
    var latRad = lat * Math.PI / 180;
    return { lat: 111320, lng: 111320 * Math.cos(latRad) };
  }

  function computeAreaStremma(pts) {
    if (pts.length < 3) return 0;
    var avgLat = pts.reduce(function (s, p) { return s + p[0]; }, 0) / pts.length;
    var mpd = metersPerDegree(avgLat);
    var xy = pts.map(function (p) { return [p[1] * mpd.lng, p[0] * mpd.lat]; });
    var area = 0;
    for (var i = 0; i < xy.length; i++) {
      var j = (i + 1) % xy.length;
      area += xy[i][0] * xy[j][1] - xy[j][0] * xy[i][1];
    }
    return Math.abs(area) / 2 / 1000;
  }

  function redraw() {
    if (polygon) { map.removeLayer(polygon); polygon = null; }
    markers.forEach(function (m) { map.removeLayer(m); });
    markers = [];

    points.forEach(function (p, idx) {
      var marker = L.circleMarker(p, { radius: 6, color: '#fff', weight: 2, fillColor: '#5B6B3E', fillOpacity: 1 }).addTo(map);
      marker.bindTooltip(String(idx + 1));
      markers.push(marker);
    });

    if (points.length >= 2) {
      polygon = L.polygon(points, { color: '#5B6B3E', weight: 2, fillOpacity: 0.25 }).addTo(map);
    }

    var area = computeAreaStremma(points);
    var areaEl = document.getElementById(opts.areaDisplayId);
    if (areaEl) {
      areaEl.textContent = points.length >= 3
        ? ('Εμβαδόν: ' + area.toFixed(2) + ' στρέμματα  (' + points.length + ' σημεία)')
        : (points.length + ' σημείο(α) καταχωρημένα — χρειάζονται τουλάχιστον 3 για υπολογισμό εμβαδού');
    }

    var input = document.getElementById(opts.pointsInputId);
    if (input) input.value = JSON.stringify(points);

    var saveBtn = document.getElementById(opts.saveBtnId);
    if (saveBtn) saveBtn.style.display = points.length >= 3 ? 'inline-block' : 'none';
  }

  map.on('click', function (e) {
    points.push([e.latlng.lat, e.latlng.lng]);
    redraw();
  });

  var undoBtn = document.getElementById(opts.undoBtnId);
  if (undoBtn) undoBtn.addEventListener('click', function (ev) {
    ev.preventDefault();
    points.pop();
    redraw();
  });

  var clearBtn = document.getElementById(opts.clearBtnId);
  if (clearBtn) clearBtn.addEventListener('click', function (ev) {
    ev.preventDefault();
    points = [];
    redraw();
  });

  var loadBtn = document.getElementById(opts.loadTextBtnId);
  if (loadBtn) loadBtn.addEventListener('click', function (ev) {
    ev.preventDefault();
    var textarea = document.getElementById(opts.textareaId);
    var raw = (textarea.value || '').trim();
    if (!raw) return;
    var parsed = [];
    raw.split('\n').forEach(function (line) {
      var parts = line.split(/[,;\s]+/).map(Number).filter(function (n) { return !isNaN(n); });
      if (parts.length >= 2) parsed.push([parts[0], parts[1]]);
    });
    if (parsed.length >= 3) {
      points = parsed;
      redraw();
      map.fitBounds(L.polygon(points).getBounds());
    } else {
      alert('Χρειάζονται τουλάχιστον 3 σημεία, ένα ανά γραμμή, σε μορφή: γεωγραφικό πλάτος, γεωγραφικό μήκος');
    }
  });

  if (opts.geoBtnId) {
    var geoBtn = document.getElementById(opts.geoBtnId);
    if (geoBtn) geoBtn.addEventListener('click', function (ev) {
      ev.preventDefault();
      if (!navigator.geolocation) { alert('Η τοποθεσία δεν υποστηρίζεται από τον browser.'); return; }
      navigator.geolocation.getCurrentPosition(function (pos) {
        points.push([pos.coords.latitude, pos.coords.longitude]);
        map.setView([pos.coords.latitude, pos.coords.longitude], 17);
        redraw();
      }, function () {
        alert('Δεν ήταν δυνατή η λήψη της τρέχουσας τοποθεσίας.');
      });
    });
  }

  redraw();
  setTimeout(function () { map.invalidateSize(); }, 150);

  return { getPoints: function () { return points; } };
}

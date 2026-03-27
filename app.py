import os
import math
import time
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_compress import Compress
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))

# Enable GZIP compression for faster response transfer
Compress(app)

GEOCODING_API = os.getenv("GEOCODING_API", "https://geocoding-api.open-meteo.com/v1/search")
WEATHER_API = os.getenv("WEATHER_API", "https://api.open-meteo.com/v1/forecast")

# Simple in-memory cache with TTL (5 minutes for cities, 10 minutes for weather)
_cache = {}
CACHE_TTL_CITIES = 300  # 5 minutes
CACHE_TTL_WEATHER = 600  # 10 minutes


def _cache_get(key: str) -> any:
    """Recupera un elemento dalla cache se non è scaduto."""
    if key in _cache:
        value, timestamp = _cache[key]
        if time.time() - timestamp < _cache[key][2]:  # Check TTL
            return value
        else:
            del _cache[key]
    return None


def _cache_set(key: str, value: any, ttl: int):
    """Memorizza un elemento in cache con TTL."""
    _cache[key] = (value, time.time(), ttl)


def _cache_key_city(city: str) -> str:
    """Genera una chiave di cache per la ricerca della città."""
    return f"city:{city.lower().strip()}"


def _cache_key_weather(lat: float, lon: float) -> str:
    """Genera una chiave di cache per i dati meteo."""
    return f"weather:{lat:.2f},{lon:.2f}"


def get_weather_type(weathercode: int) -> str:
    """Determina il tipo di tempo dal codice meteo di OpenMeteo per lo styling dinamico."""
    if weathercode in [0, 1]:
        return "sunny"
    elif weathercode in [2, 3]:
        return "cloudy"
    elif weathercode in [45, 48]:
        return "foggy"
    elif weathercode in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
        return "rainy"
    elif weathercode in [71, 73, 75, 77, 85, 86]:
        return "snowy"
    elif weathercode in [95, 96, 99]:
        return "stormy"
    else:
        return "cloudy"  # default


def normalize_city_name(raw_city: str) -> str:
    """Normalizza la stringa della città inserita in una forma pulita per la query API.

    Rimuove spazi extra e unifica il case. Mantiene accenti e caratteri non-ASCII.
    """
    if not isinstance(raw_city, str):
        raise ValueError("Nome della città non valido")
    city = " ".join(raw_city.strip().split())
    return city


def validate_city_name(city: str) -> bool:
    """Valida il formato del nome della città e rifiuta input chiaramente errati.

    - Rifiuta stringhe vuote o con solo spazi
    - Rifiuta stringhe contenenti cifre
    - Rifiuta stringhe con solo punteggiatura
    """
    # Strip whitespace for validation
    city = city.strip()
    
    if not city:
        return False
    if any(char.isdigit() for char in city):
        return False
    # Allow letters, spacing and common punctuation in city names
    if all(char in " .,'-" or char.isalpha() for char in city):
        return True
    return False


def search_city(city: str):
    """Interroga l'API di geocoding di Open-Meteo e restituisce la lista di località candidate.
    
    Usa caching in memoria per ridurre le chiamate API (TTL: 5 minuti).
    """
    # Check cache first
    cache_key = _cache_key_city(city)
    cached_result = _cache_get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Query API
    params = {
        "name": city,
        "count": 10,
        "language": "it",
        "format": "json",
    }
    response = requests.get(GEOCODING_API, params=params, timeout=8)
    response.raise_for_status()
    data = response.json()
    result = data.get("results", [])
    
    # Cache the result
    _cache_set(cache_key, result, CACHE_TTL_CITIES)
    
    return result


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcola la distanza in km tra due coordinate usando la formula di Haversine."""
    R = 6371  # Raggio della Terra in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def filter_best_candidates(candidates: list, search_query: str) -> list:
    """
    Filtra intelligentemente i candidati per evitare doppioni o risultati irrilevanti.
    
    Logica:
    1. Trova match esatti del nome città
    2. Predilige città con popolazione più grande
    3. Mostra TUTTE le città omonime in paesi diversi (es: Springfield USA vs Springfield IL ecc)
    4. Se molti match nello stesso paese, mostra solo il principale
    5. Ordinamento: popolazione decrescente
    """
    if not candidates:
        return []
    
    if len(candidates) == 1:
        return candidates
    
    # Normalizza la query per il confronto
    search_normalized = search_query.lower().strip()
    
    # Filtra candidati con nome esattamente corrispondente
    exact_matches = []
    for c in candidates:
        city_name = c.get("name", "").lower().strip()
        if city_name == search_normalized:
            exact_matches.append(c)
    
    # Se non ci sono exact matches, predigli per popolazione
    if not exact_matches:
        candidates_with_pop = [c for c in candidates if c.get("population")]
        if candidates_with_pop:
            candidates_with_pop.sort(key=lambda x: x.get("population", 0), reverse=True)
            return [candidates_with_pop[0]]
        return [candidates[0]]
    
    # Se c'è esattamente un match esatto, usalo
    if len(exact_matches) == 1:
        return exact_matches
    
    # Ordina per popolazione
    exact_matches_sorted = sorted(exact_matches, key=lambda x: x.get("population", 0), reverse=True)
    
    # Raggruppa per paese
    cities_by_country = {}
    for city in exact_matches_sorted:
        country = city.get("country", "Unknown")
        if country not in cities_by_country:
            cities_by_country[country] = []
        cities_by_country[country].append(city)
    
    # Se tutti i match esatti sono nello stesso paese, mostra il più grande
    if len(cities_by_country) == 1:
        country_cities = list(cities_by_country.values())[0]
        # Se tanti nello stesso paese, mostra solo il principale
        if len(country_cities) > 2:
            return [country_cities[0]]
        return country_cities
    
    # Se i match sono in paesi DIVERSI, mostra TUTTI i principali di ogni paese
    # Questo permette la scelta tra Springfield USA, Springfield UK, Springfield Canada, etc
    result = []
    for country, country_cities in sorted(cities_by_country.items()):
        # Prendi il più grande di ogni paese
        result.append(country_cities[0])
    
    # Riordina per popolazione globale
    result.sort(key=lambda x: x.get("population", 0), reverse=True)
    
    return result


def get_weather_data(latitude: float, longitude: float):
    """Ottieni il meteo corrente e la previsione a 5 giorni da Open-Meteo.

    Include umidità, vento e precipitazioni.
    Usa caching in memoria per ridurre le chiamate API (TTL: 10 minuti).
    """
    # Check cache first
    cache_key = _cache_key_weather(latitude, longitude)
    cached_result = _cache_get(cache_key)
    if cached_result is not None:
        return cached_result
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True,
        "hourly": "relativehumidity_2m",
        "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
        "forecast_days": 5,
        "timezone": "auto",
    }
    response = requests.get(WEATHER_API, params=params, timeout=8)
    response.raise_for_status()
    data = response.json()

    current = data.get("current_weather") or {}
    humidity = None
    
    # Optimized humidity extraction
    if current and "hourly" in data and "relativehumidity_2m" in data["hourly"]:
        try:
            now = current.get("time")
            times = data["hourly"].get("time", [])
            if now and times:
                try:
                    index = times.index(now)
                    humidity = data["hourly"]["relativehumidity_2m"][index]
                except (ValueError, IndexError):
                    humidity = None
        except Exception:
            humidity = None

    result = {
        "current": current,
        "daily": data.get("daily", {}),
        "humidity": humidity,
    }
    
    # Cache the result
    _cache_set(cache_key, result, CACHE_TTL_WEATHER)
    
    return result


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/find", methods=["POST"])
def find_city():
    raw_city = request.form.get("city", "")
    city = normalize_city_name(raw_city)

    if not validate_city_name(city):
        flash("Nome città non valido. Usa una città esistente, niente numeri o simboli strambi.", "danger")
        return redirect(url_for("index"))

    try:
        candidates = search_city(city)
    except requests.RequestException:
        flash("Errore di connessione ai servizi meteo. Riprova più tardi.", "danger")
        return redirect(url_for("index"))

    if not candidates:
        flash(f"Nessuna città trovata per '{city}'. Controlla l'ortografia.", "warning")
        return redirect(url_for("index"))

    # Filtra intelligentemente i candidati
    filtered_candidates = filter_best_candidates(candidates, city)

    if len(filtered_candidates) == 1:
        candidate = filtered_candidates[0]
        return redirect(
            url_for(
                "show_weather",
                latitude=candidate["latitude"],
                longitude=candidate["longitude"],
                name=f"{candidate.get('name', '')}, {candidate.get('country', '')}".strip(', '),
            )
        )

    # Se ci sono più opzioni (città omonime distanti), mostra la scelta
    return render_template("select.html", city=city, candidates=filtered_candidates)


@app.route("/weather", methods=["GET"])
def show_weather():
    city_name = request.args.get("name", "Località")
    try:
        latitude = float(request.args.get("latitude", ""))
        longitude = float(request.args.get("longitude", ""))
    except (ValueError, TypeError):
        flash("Coordinate non valide. Torna e riprova con una città valida.", "danger")
        return redirect(url_for("index"))

    try:
        weather_data = get_weather_data(latitude, longitude)
    except requests.RequestException:
        flash("Errore nel recupero del meteo. Riprova più tardi.", "danger")
        return redirect(url_for("index"))

    if not weather_data or not weather_data.get("current"):
        flash("Impossibile ottenere il meteo attuale per la località selezionata.", "warning")
        return redirect(url_for("index"))

    return render_template(
        "weather.html",
        city_name=city_name,
        weather=weather_data,
        latitude=latitude,
        longitude=longitude,
        weather_type=get_weather_type(weather_data["current"].get("weathercode", 3)),
    )


@app.after_request
def add_cache_headers(response):
    """Aggiungi cache headers per ridurre il carico di rete."""
    # Cache static assets for 1 hour
    if response.content_type and (
        'css' in response.content_type or
        'javascript' in response.content_type or
        'font' in response.content_type or
        'image' in response.content_type
    ):
        response.cache_control.max_age = 3600
    # Don't cache HTML pages (meteo può cambiare)
    else:
        response.cache_control.no_cache = True
        response.cache_control.no_store = True
    return response


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

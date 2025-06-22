import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import io
from functools import wraps

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from services.weather_service import WeatherService

app = Flask(__name__)
CORS(app, origins="*")

weather_service = WeatherService()

def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({"error": f"Invalid input: {str(e)}"}), 400
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
    return decorated_function

def validate_city(city):
    if not city or not city.strip():
        raise ValueError("City parameter is required and cannot be empty")
    if len(city.strip()) < 2:
        raise ValueError("City name must be at least 2 characters long")
    if len(city.strip()) > 100:
        raise ValueError("City name is too long")
    return city.strip()

def validate_days(days_str):
    try:
        days = int(days_str)
        if days < 1 or days > 7:
            raise ValueError("Days must be between 1 and 7")
        return days
    except (ValueError, TypeError):
        raise ValueError("Days must be a valid number between 1 and 7")

@app.route("/api", methods=["GET"])
@handle_errors
def health_check():
    return jsonify({
        "status": "healthy",
        "version": "2.0",
        "message": "Weather API is running",
        "endpoints": {
            "GET /api": "API information",
            "GET /weather": "Get current weather for a city",
            "GET /forecast": "Get weather forecast for a city",
            "GET /ascii": "Get ASCII art weather display"
        },
        "parameters": {
            "city": "City name (required for weather endpoints)",
            "days": "Number of forecast days 1-7 (optional, default: 5)",
            "mode": "ASCII display mode: 'current' or 'forecast' (optional, default: 'current')"
        }
    })

@app.route("/weather", methods=["GET"])
@handle_errors
def get_current_weather():
    city_param = request.args.get("city", "").strip()
    city = validate_city(city_param) if city_param else "London"
    
    data = weather_service.get_current_weather(city)
    
    if "error" in data:
        return jsonify(data), 404
    
    return jsonify(data)

@app.route("/forecast", methods=["GET"])
@handle_errors
def get_forecast():
    city_param = request.args.get("city", "").strip()
    days_param = request.args.get("days", "5")
    
    city = validate_city(city_param) if city_param else "London"
    days = validate_days(days_param)
    
    data = weather_service.get_forecast(city, days)
    
    if "error" in data:
        return jsonify(data), 404
    
    return jsonify(data)

@app.route("/ascii", methods=["GET"])
@handle_errors
def get_ascii_output():
    city_param = request.args.get("city", "").strip()
    mode = request.args.get("mode", "current").lower()
    
    city = validate_city(city_param) if city_param else "London"
    
    if mode not in ["current", "forecast"]:
        raise ValueError("Mode must be 'current' or 'forecast'")
    
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    
    try:
        if mode == "forecast":
            weather_service.display_forecast(city)
        else:
            weather_service.display_current_weather(city)
        
        ascii_output = buffer.getvalue()
        
        if not ascii_output.strip():
            raise Exception("No ASCII output generated")
            
        return jsonify({
            "city": city,
            "mode": mode,
            "ascii": ascii_output
        })
        
    finally:
        sys.stdout = old_stdout

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "message": "Available endpoints: /api, /weather, /forecast, /ascii",
        "available_endpoints": ["/api", "/weather", "/forecast", "/ascii"]
    }), 404

application = app 
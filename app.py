import os
import sys
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import io
from functools import wraps

from services.weather_service import WeatherService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app, origins="*")

weather_service = WeatherService()

@app.route("/", methods=["GET"])
def home():
    """Serve the landing page HTML"""
    try:
        return app.send_static_file('index.html')
    except Exception as e:
        logger.error(f"Error serving landing page: {str(e)}")
        return jsonify({
            "error": "Could not serve landing page",
            "message": "Please check that static/index.html exists",
            "api_info": "Use /api endpoint for API documentation"
        }), 500

def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error: {str(e)}")
            return jsonify({"error": f"Invalid input: {str(e)}"}), 400
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
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
            "GET /": "Landing page",
            "GET /api": "API information",
            "GET /weather": "Get current weather for a city",
            "GET /forecast": "Get weather forecast for a city",
            "GET /ascii": "Get ASCII art weather display"
        },
        "parameters": {
            "city": "City name (required for weather endpoints)",
            "days": "Number of forecast days 1-7 (optional, default: 5)",
            "mode": "ASCII display mode: 'current' or 'forecast' (optional, default: 'current')"
        },
        "examples": {
            "current_weather": "/weather?city=London",
            "forecast": "/forecast?city=Paris&days=3",
            "ascii_display": "/ascii?city=Tokyo&mode=current"
        }
    })

@app.route("/weather", methods=["GET"])
@handle_errors
def get_current_weather():
    city_param = request.args.get("city", "").strip()
    city = validate_city(city_param) if city_param else "London"
    
    logger.info(f"Fetching current weather for: {city}")
    data = weather_service.get_current_weather(city)
    
    if "error" in data:
        logger.warning(f"Weather fetch failed for {city}: {data['error']}")
        return jsonify(data), 404
    
    logger.info(f"Successfully fetched weather for: {city}")
    return jsonify(data)

@app.route("/forecast", methods=["GET"])
@handle_errors
def get_forecast():
    city_param = request.args.get("city", "").strip()
    days_param = request.args.get("days", "5")
    
    city = validate_city(city_param) if city_param else "London"
    days = validate_days(days_param)
    
    logger.info(f"Fetching {days}-day forecast for: {city}")
    data = weather_service.get_forecast(city, days)
    
    if "error" in data:
        logger.warning(f"Forecast fetch failed for {city}: {data['error']}")
        return jsonify(data), 404
    
    logger.info(f"Successfully fetched forecast for: {city}")
    return jsonify(data)

@app.route("/ascii", methods=["GET"])
@handle_errors
def get_ascii_output():
    city_param = request.args.get("city", "").strip()
    mode = request.args.get("mode", "current").lower()
    
    city = validate_city(city_param) if city_param else "London"
    
    if mode not in ["current", "forecast"]:
        raise ValueError("Mode must be 'current' or 'forecast'")
    
    logger.info(f"Generating ASCII {mode} display for: {city}")
    
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
            
        logger.info(f"Successfully generated ASCII display for: {city}")
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
        "message": "Please check the API documentation at the /api endpoint",
        "available_endpoints": ["/", "/api", "/weather", "/forecast", "/ascii"]
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": "Method not allowed",
        "message": "This endpoint only supports GET requests"
    }), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "error": "Internal server error",
        "message": "Something went wrong on our end"
    }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    logger.info(f"Starting Weather API on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug) 

#trigger vercel deployment

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
from .weather_models import WeatherArt, WeatherCodeMapper, TerminalGraph


logger = logging.getLogger(__name__)

class WeatherService:
    
    def __init__(self):
        self.geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"
        self.timeout = 10  
    
    def _make_request(self, url: str, params: Dict) -> Optional[Dict]:
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for URL: {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for URL: {url}, Error: {str(e)}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from URL: {url}")
            return None
    
    def get_coordinates(self, city: str) -> Dict:
        if not city or not city.strip():
            return {"error": "City name cannot be empty"}
        
        city = city.strip()
        logger.info(f"Fetching coordinates for: {city}")
        
        params = {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        
        data = self._make_request(self.geo_url, params)
        
        if not data:
            return {"error": f"Failed to fetch coordinates for {city}"}
        
        if not data.get("results") or len(data["results"]) == 0:
            return {"error": f"City '{city}' not found"}
        
        location = data["results"][0]
        result = {
            "lat": location["latitude"],
            "lon": location["longitude"],
            "name": location["name"],
            "country": location.get("country", "Unknown"),
            "admin1": location.get("admin1", "")
        }
        
        logger.info(f"Found coordinates for {result['name']}, {result['country']}")
        return result
    
    def get_weather_art(self, condition: str, is_night: bool = False) -> str:
        if is_night and condition.lower() in ["clear", "sunny"]:
            return WeatherArt.NIGHT
        
        condition = condition.lower()
        art_map = {
            "clear": WeatherArt.SUNNY,
            "sunny": WeatherArt.SUNNY,
            "rain": WeatherArt.RAINY,
            "storm": WeatherArt.STORMY,
            "snow": WeatherArt.SNOWY,
            "fog": WeatherArt.FOGGY,
            "cloudy": WeatherArt.CLOUDY,
            "overcast": WeatherArt.CLOUDY
        }
        
        for key, art in art_map.items():
            if key in condition:
                return art
        
        return WeatherArt.CLOUDY  
    
    def get_current_weather(self, city: str) -> Dict:
        coords = self.get_coordinates(city)
        if "error" in coords:
            return coords
        
        logger.info(f"Fetching current weather for {coords['name']}")
        
        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation",
                "weather_code",
                "surface_pressure",
                "wind_speed_10m",
                "wind_direction_10m"
            ],
            "timezone": "auto"
        }
        
        data = self._make_request(self.weather_url, params)
        
        if not data or "current" not in data:
            return {"error": f"Failed to fetch weather data for {coords['name']}"}
        
        current = data["current"]
        weather_code = current.get("weather_code", 0)
        description = WeatherCodeMapper.get_description(weather_code)
        condition = WeatherCodeMapper.get_condition(weather_code)
        
        
        result = {
            "location": {
                "name": coords["name"],
                "country": coords["country"],
                "coordinates": {
                    "lat": coords["lat"],
                    "lon": coords["lon"]
                }
            },
            "current": {
                "temperature": current.get("temperature_2m"),
                "feels_like": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "pressure": current.get("surface_pressure"),
                "wind_speed": current.get("wind_speed_10m"),
                "wind_direction": current.get("wind_direction_10m"),
                "precipitation": current.get("precipitation", 0)
            },
            "weather": {
                "code": weather_code,
                "description": description,
                "condition": condition
            },
            "timestamp": current.get("time"),
            
            "name": coords["name"],
            "main": {
                "temp": current.get("temperature_2m"),
                "feels_like": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "pressure": current.get("surface_pressure")
            },
            "weather": [{
                "main": condition.title(),
                "description": description
            }],
            "wind": {
                "speed": current.get("wind_speed_10m"),
                "deg": current.get("wind_direction_10m")
            }
        }
        
        logger.info(f"Successfully fetched weather for {coords['name']}")
        return result
    
    def get_forecast(self, city: str, days: int = 5) -> Dict:
        coords = self.get_coordinates(city)
        if "error" in coords:
            return coords
        
        if days < 1 or days > 7:
            return {"error": "Days must be between 1 and 7"}
        
        logger.info(f"Fetching {days}-day forecast for {coords['name']}")
        
        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "weather_code",
                "precipitation_sum",
                "wind_speed_10m_max",
                "wind_direction_10m_dominant"
            ],
            "timezone": "auto",
            "forecast_days": days
        }
        
        data = self._make_request(self.weather_url, params)
        
        if not data or "daily" not in data:
            return {"error": f"Failed to fetch forecast data for {coords['name']}"}
        
        daily = data["daily"]
        forecast_list = []
        
        for i in range(min(days, len(daily["time"]))):
            date = datetime.fromisoformat(daily["time"][i].replace('Z', '+00:00'))
            weather_code = daily["weather_code"][i]
            description = WeatherCodeMapper.get_description(weather_code)
            condition = WeatherCodeMapper.get_condition(weather_code)
            
            forecast_item = {
                "date": daily["time"][i],
                "temperature": {
                    "max": daily["temperature_2m_max"][i],
                    "min": daily["temperature_2m_min"][i]
                },
                "weather": {
                    "code": weather_code,
                    "description": description,
                    "condition": condition
                },
                "precipitation": daily["precipitation_sum"][i],
                "wind": {
                    "speed": daily["wind_speed_10m_max"][i],
                    "direction": daily["wind_direction_10m_dominant"][i]
                },
                
                "dt": date.timestamp(),
                "main": {
                    "temp": daily["temperature_2m_max"][i],
                    "temp_min": daily["temperature_2m_min"][i],
                    "temp_max": daily["temperature_2m_max"][i],
                    "humidity": 65  
                },
                "weather": [{
                    "main": condition.title(),
                    "description": description
                }],
                "wind": {
                    "speed": daily["wind_speed_10m_max"][i]
                }
            }
            
            forecast_list.append(forecast_item)
        
        result = {
            "location": {
                "name": coords["name"],
                "country": coords["country"]
            },
            "forecast": forecast_list,
            
            "list": forecast_list,
            "city": {"name": coords["name"]}
        }
        
        logger.info(f"Successfully fetched forecast for {coords['name']}")
        return result
    
    def get_mini_weather_art(self, condition: str) -> str:
        condition = condition.lower()
        icons = {
            "clear": "[SUN]",
            "sunny": "[SUN]",
            "rain": "[RAIN]",
            "storm": "[STORM]",
            "snow": "[SNOW]",
            "fog": "[FOG]",
            "cloudy": "[CLOUD]",
            "overcast": "[CLOUD]"
        }
        
        for key, icon in icons.items():
            if key in condition:
                return icon
        
        return "[CLOUD]"  
    
    def create_temp_bar(self, temp: float, min_range: float = -20, max_range: float = 50) -> str:
        bar_length = 50
        if temp < min_range:
            pos = 0
        elif temp > max_range:
            pos = bar_length - 1
        else:
            pos = int((temp - min_range) / (max_range - min_range) * (bar_length - 1))
        
        bar_chars = []
        for i in range(bar_length):
            if i == pos:
                bar_chars.append("●")
            elif i < pos:
                if temp < 0:
                    bar_chars.append("▓")  
                elif temp < 20:
                    bar_chars.append("▒")  
                else:
                    bar_chars.append("░")  
            else:
                bar_chars.append(".")
        
        bar = "[" + "".join(bar_chars) + "]"
        return f"{min_range}°C {bar} {max_range}°C\n        Current: {temp}°C"
    
    def display_current_weather(self, city: str):
        data = self.get_current_weather(city)
        
        if "error" in data:
            print(f"ERROR: {data['error']}")
            return
        
        location = data.get("location", {})
        current = data.get("current", data.get("main", {}))
        weather = data.get("weather", [{}])
        
        if isinstance(weather, list) and weather:
            weather_info = weather[0]
        else:
            weather_info = weather
        
        name = location.get("name", data.get("name", "Unknown"))
        country = location.get("country", "")
        temp = current.get("temperature", current.get("temp"))
        feels_like = current.get("feels_like", temp)
        humidity = current.get("humidity", 0)
        pressure = current.get("pressure", 0)
        
        wind_data = data.get("wind", {})
        wind_speed = wind_data.get("speed", current.get("wind_speed", 0))
        
        condition = weather_info.get("description", "Unknown")
        
        print("=" * 80)
        location_str = f"{name}, {country}" if country else name
        print(f"WEATHER DASHBOARD - {location_str.upper()}")
        print("=" * 80)
        
        
        current_hour = datetime.now().hour
        is_night = current_hour < 6 or current_hour > 20
        
        
        weather_condition = weather_info.get("main", condition)
        print(self.get_weather_art(weather_condition, is_night))
        
        
        print(f"TEMPERATURE: {temp}°C (feels like {feels_like}°C)")
        print(f"CONDITION: {condition}")
        print(f"HUMIDITY: {humidity}%")
        print(f"PRESSURE: {pressure} hPa")
        print(f"WIND: {wind_speed} m/s")
        
        precipitation = current.get("precipitation", 0)
        if precipitation > 0:
            print(f"PRECIPITATION: {precipitation} mm")
        
        print(f"\nTemperature Scale:")
        print(self.create_temp_bar(temp))
        print("=" * 80)
    
    def display_forecast(self, city: str, days: int = 5):
        data = self.get_forecast(city, days)
        
        if "error" in data:
            print(f"ERROR: {data['error']}")
            return
        
        location = data.get("location", {})
        forecast_list = data.get("forecast", data.get("list", []))
        
        name = location.get("name", data.get("city", {}).get("name", "Unknown"))
        country = location.get("country", "")
        
        location_str = f"{name}, {country}" if country else name
        print(f"\n{days}-DAY FORECAST - {location_str.upper()}")
        print("=" * 80)
        
        
        temps_max, temps_min, precipitation, wind_speeds, labels = [], [], [], [], []
        
        for item in forecast_list:
            
            if "date" in item:
                date = datetime.fromisoformat(item["date"].replace('Z', '+00:00'))
            else:
                date = datetime.fromtimestamp(item.get("dt", 0))
            
            temp_data = item.get("temperature", item.get("main", {}))
            weather_data = item.get("weather", [{}])
            
            if isinstance(weather_data, list) and weather_data:
                weather_info = weather_data[0]
            else:
                weather_info = weather_data
            
            temp_max = temp_data.get("max", temp_data.get("temp_max", temp_data.get("temp", 0)))
            temp_min = temp_data.get("min", temp_data.get("temp_min", temp_max))
            precip = item.get("precipitation", 0)
            wind_speed = item.get("wind", {}).get("speed", 0)
            
            condition = weather_info.get("main", weather_info.get("condition", "Unknown"))
            description = weather_info.get("description", condition)
            
            temps_max.append(temp_max)
            temps_min.append(temp_min)
            precipitation.append(precip)
            wind_speeds.append(wind_speed)
            labels.append(date.strftime("%m/%d"))
            
            
            day_str = date.strftime("%a %m/%d")
            icon = self.get_mini_weather_art(condition)
            print(f"{day_str:>8} | {icon:>8} | {temp_max:>5.1f}°C | {temp_min:>5.1f}°C | {description}")
        
        
        if len(temps_max) >= 2:
            print(TerminalGraph.create_line_graph(temps_max, labels, "Max Temperature Trend", unit="°C"))
            print(TerminalGraph.create_line_graph(temps_min, labels, "Min Temperature Trend", unit="°C"))
            
            if any(p > 0 for p in precipitation):
                print(TerminalGraph.create_line_graph(precipitation, labels, "Precipitation Trend", unit="mm"))
            
            if any(w > 0 for w in wind_speeds):
                print(TerminalGraph.create_line_graph(wind_speeds, labels, "Wind Speed Trend", unit="m/s"))
        
        print("=" * 80)
    
    def display_banner(self):
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                              WEATHER DASHBOARD                               ║
║                      Advanced Command Line Weather Service                   ║
║                            Powered by Open-Meteo API                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner) 
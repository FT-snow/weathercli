import sys
import argparse
from services.weather_service import WeatherService

def main():
    parser = argparse.ArgumentParser(
        description="Weather CLI - Get weather information from the command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s London                    
  %(prog)s --forecast Tokyo          
  %(prog)s --forecast --days 3 Paris 
  %(prog)s --banner                  
        """
    )
    
    parser.add_argument(
        "city",
        nargs="?",
        default="London",
        help="City name to get weather for (default: London)"
    )
    
    parser.add_argument(
        "--forecast", "-f",
        action="store_true",
        help="Show weather forecast instead of current weather"
    )
    
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=5,
        choices=range(1, 8),
        metavar="1-7",
        help="Number of forecast days (1-7, default: 5)"
    )
    
    parser.add_argument(
        "--banner", "-b",
        action="store_true",
        help="Show application banner"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="Weather CLI v2.0"
    )
    
    args = parser.parse_args()
    
    
    weather_service = WeatherService()
    
    try:
        if args.banner:
            weather_service.display_banner()
            return
        
        if args.forecast:
            weather_service.display_forecast(args.city, args.days)
        else:
            weather_service.display_current_weather(args.city)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
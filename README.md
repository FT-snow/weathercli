# Weather CLI & API

Get weather information from the command line or API.

## Setup

```bash
pip install -r requirements.txt
```

## CLI Usage

### Basic Commands
```bash
# get current weather
python cli.py London

# get weather forecast
python cli.py --forecast Tokyo

# get 3-day forecast
python cli.py --forecast --days 3 Paris

# show help
python cli.py --help
```

### Examples
```bash
python cli.py "New York"
python cli.py --forecast --days 7 Berlin
python cli.py --banner
```

## API Usage

### Start Server
```bash
py api/weather.py
```
Server runs on `http://localhost:5000`

### Public API Endpoints

#### Get Current Weather
```bash
curl -sL "https://weathercli.vercel.app/weather?city=London"
```

#### Get Forecast
```bash
curl -sL "https://weathercli.vercel.app/forecast?city=Paris&days=3"
```


[Live Demo](https://weathercli.vercel.app/)

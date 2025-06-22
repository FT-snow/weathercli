from typing import List

class WeatherArt:
    
    SUNNY = """
    \\   /
     .-.
  ‒ (   ) ‒
     `-'
    /   \\
    """
    
    CLOUDY = """
     .--.
  .-(    ).
 (___.__)__)
    """
    
    RAINY = """
     .--.
  .-(    ).
 (___.__)__)
  ʻ ʻ ʻ ʻ
 ʻ ʻ ʻ ʻ
    """
    
    STORMY = """
     .--.
  .-(    ).
 (___.__)__)
    * *
  * * *
    """
    
    SNOWY = """
     .--.
  .-(    ).
 (___.__)__)
   * * *
  * * *
    """
    
    FOGGY = """
     .--.
  .-(    ).
 (___.__)__)
 ≡ ≡ ≡ ≡ ≡
≡ ≡ ≡ ≡ ≡ ≡
    """
    
    NIGHT = """
      *
   *     *
 *    (   *
   *     *
      *
    """

class WeatherCodeMapper:
    
    WMO_CODES = {
        0: ("Clear sky", "clear"),
        1: ("Mainly clear", "clear"),
        2: ("Partly cloudy", "cloudy"),
        3: ("Overcast", "cloudy"),
        45: ("Fog", "fog"),
        48: ("Depositing rime fog", "fog"),
        51: ("Light drizzle", "rain"),
        53: ("Moderate drizzle", "rain"),
        55: ("Dense drizzle", "rain"),
        56: ("Light freezing drizzle", "rain"),
        57: ("Dense freezing drizzle", "rain"),
        61: ("Slight rain", "rain"),
        63: ("Moderate rain", "rain"),
        65: ("Heavy rain", "rain"),
        66: ("Light freezing rain", "rain"),
        67: ("Heavy freezing rain", "rain"),
        71: ("Slight snow fall", "snow"),
        73: ("Moderate snow fall", "snow"),
        75: ("Heavy snow fall", "snow"),
        77: ("Snow grains", "snow"),
        80: ("Slight rain showers", "rain"),
        81: ("Moderate rain showers", "rain"),
        82: ("Violent rain showers", "rain"),
        85: ("Slight snow showers", "snow"),
        86: ("Heavy snow showers", "snow"),
        95: ("Thunderstorm", "storm"),
        96: ("Thunderstorm with slight hail", "storm"),
        99: ("Thunderstorm with heavy hail", "storm"),
    }
    
    @classmethod
    def get_description(cls, code: int) -> str:
        return cls.WMO_CODES.get(code, ("Unknown", "unknown"))[0]
    
    @classmethod
    def get_condition(cls, code: int) -> str:
        return cls.WMO_CODES.get(code, ("Unknown", "unknown"))[1]

class TerminalGraph:
    
    @staticmethod
    def create_line_graph(data: List[float], labels: List[str], title: str, 
                         height: int = 10, unit: str = "") -> str:
        if not data or len(data) != len(labels) or len(data) < 2:
            return f"\n[GRAPH] {title}\nInsufficient data for graph display"

        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val if min_val != max_val else 1
        
        
        normalized = [(val - min_val) / range_val * (height - 1) for val in data]

        graph_lines = [f"\n[GRAPH] {title}", "=" * 60]
        
        
        for row in range(height - 1, -1, -1):
            y_value = max_val - (row * range_val / (height - 1))
            line = f"{y_value:6.1f}{unit} |"
            
            for i, norm_val in enumerate(normalized):
                if abs(norm_val - row) < 0.5:
                    line += "●"
                elif i > 0:
                    prev_val = normalized[i-1]
                    if (prev_val <= row <= norm_val) or (norm_val <= row <= prev_val):
                        line += "─"
                    else:
                        line += " "
                else:
                    line += " "
                line += " "
            
            graph_lines.append(line)
        
        
        x_axis = "        +" + "─" * (len(data) * 2 - 1)
        label_line = "         " + "  ".join([label[:3] for i, label in enumerate(labels)])
        graph_lines.extend([x_axis, label_line])
        
        return "\n".join(graph_lines) 
import requests
import os


def get_weather_data(city: str) -> str:
    """Get current weather for a city. Used by MCP server."""
    try:
        api_key = os.getenv("OPENWEATHER_API_KEY", "")
        if not api_key:
            return "Weather API key not configured. Add OPENWEATHER_API_KEY to .env. Get free key at openweathermap.org"

        res = requests.get(
            "http://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": api_key, "units": "metric"},
            timeout=10
        )
        data = res.json()

        if res.status_code != 200:
            return f"Could not fetch weather for '{city}'. Check the city name."

        return (
            f"🌤️ Weather in {city.title()}, {data['sys']['country']}:\n"
            f"• Condition: {data['weather'][0]['description'].capitalize()}\n"
            f"• Temperature: {data['main']['temp']}°C (Feels like {data['main']['feels_like']}°C)\n"
            f"• Humidity: {data['main']['humidity']}%\n"
            f"• Wind Speed: {data['wind']['speed']} m/s"
        )
    except Exception as e:
        return f"Error fetching weather: {str(e)}"
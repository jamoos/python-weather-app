import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeopyError
from groq import Groq
import logging
import ecs_logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("./logs/kweather-log.json")
handler.setFormatter(ecs_logging.StdlibFormatter())
logger.addHandler(handler)


class LongLat:
    geolocator = Nominatim(user_agent="KafriWeather")

    def __init__(self, location):
        self._location = location
        logger.debug(f"Attempting to geocode location: {self._location}")
        self.latitude = None
        self.longitude = None
        self.address = None
        self.error = None

        try:
            loc = self.geolocator.geocode(self._location, language="en")
            if loc is None:
                raise GeopyError("location not found")
        except GeopyError:
            self.error = {"error": f"{self._location} - Not Found"}
            logger.warning(f"Geocoding failed for {self._location}")
        else:
            self.latitude = loc.latitude
            self.longitude = loc.longitude
            self.address = loc.address
            logger.info(f"Geocoding successful for {self._location}: {self.address}")


class MeteoWeather:
    def __init__(self, location):
        self.forecast = None
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "forecast_days": 7,
            "hourly": ["temperature_2m", "relative_humidity_2m"],
            "timezone": "auto",
        }
        logger.debug(
            f"Fetching weather data for coordinates: ({location.latitude}, {location.longitude})"
        )

        try:
            r = requests.get(url, params=params)
            if r.status_code != 200:
                raise requests.exceptions.RequestException(r._content)
        except Exception as e:
            days = {"error": e}
            logger.error(f"Error fetching weather data: {e}")
        else:
            hourly = r.json()["hourly"]
            filterd = [
                {"time": time, "temp": temp, "hum": hum}
                for time, temp, hum in zip(
                    hourly["time"],
                    hourly["temperature_2m"],
                    hourly["relative_humidity_2m"],
                )
                if time[11:] in ["11:00", "23:00"]
            ]
            days = [
                {
                    "date": filterd[i]["time"][:-6],
                    "temp_am": filterd[i]["temp"],
                    "hum_am": filterd[i]["hum"],
                    "temp_pm": filterd[i + 1]["temp"],
                    "hum_pm": filterd[i + 1]["hum"],
                }
                for i in range(len(filterd))
                if i % 2 == 0
            ]
            logger.info("Weather data fetched successfully")
        finally:
            self.forecast = days


class GroqJoke:
    client = Groq(api_key="")

    def __init__(self, forecast):
        self.joke = ""
        logger.debug(f"Generating joke for forecast: {forecast.location.address}")
        completion = self.client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "for the following weather forecast json object including location and weekly forecast, create a joke that will be funny for devops / full stack developers and relate to the location and the weather for the week, never explain the joke, limit answer length to 3 sentneces and keep a cheeky stand up comedian style tone!",
                },
                {
                    "role": "user",
                    "content": str(forecast.location.address) + str(forecast.forecast),
                },
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )
        for chunk in completion:
            self.joke += chunk.choices[0].delta.content or ""
        logger.info("Joke generated successfully")

    def __repr__(self):
        return self.joke

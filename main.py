from flask import Flask, request
import jinja2
from weatherutils import MeteoWeather, LongLat, GroqJoke
from prometheus_flask_exporter import PrometheusMetrics
import logging
import ecs_logging

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info("app_info", "Application info", version="0.0.3")
tploader = jinja2.FileSystemLoader(searchpath=".")
tplenv = jinja2.Environment(loader=tploader)
template = tplenv.get_template("boot.html")

# Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("./logs/kweather-log.json")
handler.setFormatter(ecs_logging.StdlibFormatter())
logger.addHandler(handler)


class WeatherForecast:
    def __init__(self, location):
        self.location = LongLat(location)
        try:
            self.forecast = MeteoWeather(self.location).forecast
        except Exception as e:
            logger.error(f"Error fetching weather data for {location}: {e}")
            self.forecast = None
        self.joke = ""


@app.route("/")
def home():
    cities = [
        "Tel-Aviv",
        "Haifa",
        "Jerusalem",
        "New-York",
        "London",
        "Paris",
        "Bangkok",
        "San Francisco",
    ]
    forecasts = [WeatherForecast(loc) for loc in cities]
    logger.info("Homepage accessed, displaying forecasts for multiple cities")
    return template.render(cities=forecasts)


@app.route("/<location>")
@metrics.do_not_track()
@metrics.counter(
    "invoication_by_location",
    "Number of invocations per location",
    labels={"location": lambda: request.view_args["location"]},
)
def location(location):
    logger.info(f"Request received for location: {location}")
    forecast = WeatherForecast(location)
    if forecast.forecast is None:  # Handle error case
        logger.warning(f"No forecast available for {location}")
        return "Error fetching weather data. Please try again later."

    forecast.joke = GroqJoke(forecast)
    return template.render(forecast=forecast)


if __name__ == "__main__":
    app.run(debug=True)

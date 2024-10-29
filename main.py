from flask import Flask, request, render_template
import jinja2
from datetime import datetime
from weatherutils import MeteoWeather, LongLat, GroqJoke
from prometheus_flask_exporter import PrometheusMetrics
import logging
import ecs_logging
import json
import os
from dotenv import load_dotenv

load_dotenv()
BG_COLOR = os.getenv("BG_COLOR", "cyan")
app = Flask(__name__, static_folder="history")
metrics = PrometheusMetrics(app)
metrics.info("app_info", "Application info", version="0.0.3")
tplenv = app.jinja_env
tplenv.loader = jinja2.FileSystemLoader(searchpath=".")
template = tplenv.get_template("boot.html")

# Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# remove the dot before pushing
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
    return template.render(cities=forecasts, BG_COLOR=BG_COLOR)


@app.route("/history")
def history():
    json_files = []
    for filename in os.listdir("history"):  # List files in the current directory
        if filename.endswith(".json"):
            json_files.append(filename)
    print(json_files)
    return render_template("history.html", files=json_files)


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
    # Save search results to JSON file
    try:
        # Create filename with location and date
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"{location}-{today}.json"

        # Save data to JSON file
        with open(f"history/{filename}", "w") as f:
            json.dump(forecast.forecast, f, indent=4)
        logger.info(f"Forecast data saved to {filename}")

    except Exception as e:
        logger.error(f"Error saving forecast data to JSON file: {e}")
    return template.render(forecast=forecast, BG_COLOR=BG_COLOR)


if __name__ == "__main__":
    app.run(debug=True)

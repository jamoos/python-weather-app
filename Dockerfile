FROM python:3.8-slim-bullseye
RUN apt-get update && apt-get upgrade -y --no-install-recommends
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY . .
CMD ["gunicorn","--bind","0.0.0.0:5000","main:app"]

FROM python:3.12-slim

# Install pipenv and any other dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && pip install pipenv \
    && apt-get clean

WORKDIR /app

COPY data/movie_dataset.csv data/movie_dataset.csv
COPY ["Pipfile", "Pipfile.lock", "./"]

RUN pipenv install --deploy --ignore-pipfile --system

COPY movie_advisor .

EXPOSE 5000

ENV DATA_PATH="data/movie_dataset.csv"

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]


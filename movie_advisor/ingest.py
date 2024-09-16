import pandas as pd
import docker
from elasticsearch import Elasticsearch
from tqdm.auto import tqdm
from tqdm import tqdm
import time
import requests
import os

DATA_PATH = os.getenv("DATA_PATH", "../data/movie_dataset.csv")

def fetch_data(data_path = DATA_PATH):
    print("Fetching documents...")
    df = pd.read_csv(data_path)
    df = df[['id', 'title', 'year', 'plot', 'genres', 'director']]
    df['year'] = df['year'].apply(lambda i: str(i))
    documents = df.to_dict(orient='records')
    print(f"Fetched {len(documents)} documents")
    
    return documents


def es_container_run():
    print("Setting up Elasticsearch in docker container")
    client = docker.from_env()
    container_name = "elasticsearch"

    try:
        existing_container = client.containers.get(container_name)
        if existing_container.status != "running":
            existing_container.start()
            print(f"Started existing {container_name} container.")
        else:
            print(f"{container_name} container is already running.")
        container = existing_container
        
    except docker.errors.NotFound:
        # If the container doesn't exist, create and run it
        container = client.containers.run(
            "docker.elastic.co/elasticsearch/elasticsearch:8.4.3",
            name=container_name,
            detach=True,
            remove=True,
            mem_limit="4g",
            ports={
                '9200/tcp': 9200,
                '9300/tcp': 9300
            },
            environment={
                "discovery.type": "single-node",
                "xpack.security.enabled": "false"
            }
        )
        print(f"Created and started new {container_name} container.")

    print(f"Container {container.name} is running.")
    print("Waiting for Elasticsearch to be ready...")

    retries = 20  # Number of retries
    while retries > 0:
        try:
            response = requests.get('http://localhost:9200')
            if response.status_code == 200:
                print("Elasticsearch is ready!")
                break
        except requests.exceptions.ConnectionError:
            print("Elasticsearch is not ready yet. Waiting...")
            time.sleep(5)
            retries -= 1
    if retries == 0:
        raise RuntimeError("Elasticsearch failed to start.")

def setup_elasticsearch():
    print("Setting up Elasticsearch...")
    es_client = Elasticsearch('http://localhost:9200')
    index_name = "movie-questions"
    index_settings = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "title" : {"type": "text"},
                "plot" : {"type": "text"},
                "genres" : {"type": "text"},
                "director" : {"type": "text"},
                "year" : {"type": "text"},
            }
        }
    }

    es_client.indices.delete(index=index_name, ignore=[404])
    es_client.indices.create(index=index_name, body=index_settings)

    return es_client


def load_es():
    es_container_run()
    documents = fetch_data()
    es_client = setup_elasticsearch()
    
    index_name = "movie-questions"
    for doc in tqdm(documents):
        es_client.index(index=index_name, document=doc)
    
    return es_client

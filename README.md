# Movie advisor

## Problem Description

When trying to recall the title of a movie or deciding what to watch based on a specific plot or genre, many people struggle to find reliable recommendations or remember titles. With an overwhelming number of movies available, traditional search engines or platforms may not provide the best experience for personalized recommendations based on vague descriptions.

**Movie Advisor** addresses this challenge by using a Retrieval-Augmented Generation (RAG) approach to assist users in recalling movie titles based on partial plot descriptions or suggest movies to watch from a vast dataset. By leveraging both retrieval and generation techniques, the system provides relevant and accurate suggestions, enhancing the movie discovery process.

## Project Description
Movie Advisor interacts with users via a conversational interface, allowing them to either:

- Input partial or vague movie plot descriptions to recall the exact movie title.
- Request movie recommendations based on their preferred genres or specific plot elements.

The application employs a RAG-based model to retrieve relevant movie information and generate suitable suggestions, providing a seamless and efficient solution for movie selection and recall.

## Data Description

The dataset consists more than **122,000 movies**, each described by the following attributes:

- **Title**: The name of the movie
- **Year**: The release year
- **Plot**: A brief summary of the movie's storyline
- **Genres**: The categories the movie belongs to (e.g., comedy, drama)
- **Director**: The name of the director

A sample of the data is shown below:

```plaintext
[{'title': 'Patton Oswalt: Annihilation',
  'year': '2017',
  'plot': 'Patton Oswald, despite a personal tragedy, produces his best standup yet. Focusing on the tribulations of the Trump era and life after the loss of a loved one, Patton Oswald continues his journey to contribute joy to the world.',
  'genres': 'uncategorized',
  'director': 'Bobcat Goldthwait'},
 {'title': 'New York Doll',
  'year': '2005',
  'plot': 'A recovering alcoholic and recently converted Mormon, Arthur "Killer" Kane, of the rock band The New York Dolls, is given a chance at reuniting with his band after 30 years.',
  'genres': 'documentary, music',
  'director': 'Greg Whiteley'}]
```

## Running it

I used `pipenv` for managing dependencies and Python 3.12.

Make sure you have pipenv installed:

```bash
pip install pipenv
```
Install the dependencies:

```bash
pipenv install
```

Running Jypyter notebook for experiments:

```bash
cd notebooks
pipenv run jupyter notebook
```

## Evaluation

### Retrieval



### RAG Flow


### Monitoring


## Ingestion


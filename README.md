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


## Experiments

For experiments, I used Visual Studio Code.

The notebook with experiments is located in the `notebooks/rag-tests.ipynb` file.

To generate ground-truth questions for evaluation, use the `notebooks/evaluating-data-generation.ipynb` file.

### Retrieval

I evaluated 3 different retrieval methods:

- minisearch
- elastic-search
- elastic-search vector

Here are the results:
<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>search_function</th>
      <th>hit_rate</th>
      <th>mrr</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>minisearch</td>
      <td>0.392</td>
      <td>0.274533</td>
    </tr>
    <tr>
      <th>1</th>
      <td>elastic_search</td>
      <td>0.884</td>
      <td>0.836800</td>
    </tr>
    <tr>
      <th>2</th>
      <td>elastic_search_knn</td>
      <td>0.636</td>
      <td>0.540400</td>
    </tr>
  </tbody>
</table>
</div>

The best results are provided by `elastic-search retrieval`, so I will continue with it.

### RAG Flow
I evaluated 2 different LLMs:

- `gpt-4o-mini`
- `gpt-3.5-turbo-0125`

Here are the results:
<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th></th>
      <th>count</th>
      <th>count_norm</th>
    </tr>
    <tr>
      <th>model</th>
      <th>relevance</th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="3" valign="top">gpt-3.5-turbo-0125</th>
      <th>NON_RELEVANT</th>
      <td>44</td>
      <td>8.8%</td>
    </tr>
    <tr>
      <th>PARTLY_RELEVANT</th>
      <td>53</td>
      <td>10.6%</td>
    </tr>
    <tr>
      <th>RELEVANT</th>
      <td>153</td>
      <td>30.6%</td>
    </tr>
    <tr>
      <th rowspan="3" valign="top">gpt-4o-mini</th>
      <th>NON_RELEVANT</th>
      <td>7</td>
      <td>1.4%</td>
    </tr>
    <tr>
      <th>PARTLY_RELEVANT</th>
      <td>11</td>
      <td>2.2%</td>
    </tr>
    <tr>
      <th>RELEVANT</th>
      <td>232</td>
      <td>46.4%</td>
    </tr>
  </tbody>
</table>
</div>

The best results are provided by `gpt-4o-mini`, so I will continue with it.

### Monitoring


## Ingestion


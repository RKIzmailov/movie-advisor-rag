#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np

import os
from dotenv import load_dotenv
import json
import re

from tqdm.auto import tqdm
tqdm.pandas()


# In[2]:


from openai import OpenAI

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI()


# # 1. RAG-flow

# The RAG-flow will include:
# 1) Retrieval :: 3 differen approaches:
#     - minisearch
#     - elastic-search
#     - elastic-search vector
# 2) LLM :: "gpt-4o-mini"

# In[3]:


def build_prompt(query:str, search_results:list) -> str:
    prompt_template = """
You are a professional assistant in selecting movies.
Your task is to recommend a movie from our movie dataset that best matches the request or description provided by user. 
Without any preamble, provide information about the movie that best matches the QUESTION based on the provided CONTEXT.

QUESTION: {question}

CONTEXT:
{context}
""".strip()
    
    entry_template = """
title : {title}
plot : {plot}
genres : {genres}
director : {director}
year : {year}
""".strip()

    context = ""
    
    for doc in search_results:
        context = context + entry_template.format(**doc) + "\n\n"
    
    prompt = prompt_template.format(question=query, context=context).strip()

    return prompt

def llm(prompt:str):
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content


# ## Minisearch-Text_search

# In[6]:


df = pd.read_csv('../data/movie_dataset.csv')
print('Shape:', df.shape)
df.head(2)


# In[7]:


df.info()


# In[8]:


df = df[['id', 'title', 'year', 'plot', 'genres', 'director']]
df['year'] = df['year'].apply(lambda i: str(i))

documents = df.to_dict(orient='records')


# In[10]:


## Run to download the Minsearch

# import requests

# url = "https://raw.githubusercontent.com/alexeygrigorev/minsearch/main/minsearch.py"
# response = requests.get(url)

# # Сохранение файла
# with open("minsearch.py", "wb") as f:
#     f.write(response.content)


# In[9]:


import minsearch

index = minsearch.Index(
    text_fields=['title', 'year', 'plot', 'genres', 'director'],
    keyword_fields=[]
)

index.fit(documents)


# In[10]:


def minisearch(query:str) -> list:
    boost = {}

    results = index.search(
        query=query,
        filter_dict={},
        boost_dict=boost,
        num_results=5
    )

    return results


# In[11]:


queries = ['What does Ryan Bingham do for a living, and how does it relate to his frequent travels?',
 "How does Ryan's perspective on relationships change throughout the movie?",
 'What challenges does Natalie face regarding her new layoffs program, and how does Ryan respond to it?',
 "What significant events occur during Ryan's sister's wedding that impact his character development?",
 'What realization does Ryan come to about his life and personal philosophies towards the end of the film?']


print('Movie title:', documents[150]['title'], '\n')
i = 1
for query in queries:
    print(f'{i}: {query}')
    for doc in minisearch(query):
        print(f"--{doc['title']}", end = '\t')
    i+=1
    print('\n************')


# In[12]:


def rag(query):
    search_results = minisearch(query)
    prompt = build_prompt(query, search_results)
    answer = llm(prompt)

    return answer

query = 'What does Ryan Bingham do for a living, and how does it relate to his frequent travels?'

answer = rag(query)
print(answer)


# ## Elasticsearch-Text_search

# In[16]:


# %pip -q install elasticsearch


# Running Elasticsearch:
# 
# ```
# docker run -it \
#     --rm \
#     --name elasticsearch \
#     -m 4GB \
#     -p 9200:9200 \
#     -p 9300:9300 \
#     -e "discovery.type=single-node" \
#     -e "xpack.security.enabled=false" \
#     docker.elastic.co/elasticsearch/elasticsearch:8.4.3
# ```

# In[4]:


from elasticsearch import Elasticsearch

es_client = Elasticsearch('http://localhost:9200') 


# In[6]:


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

index_name = "movie-questions"

es_client.indices.delete(index=index_name, ignore_unavailable=True)
es_client.indices.create(index=index_name, body=index_settings)


# In[7]:


df = pd.read_csv('../data/movie_dataset.csv')
df = df[['title', 'year', 'plot', 'genres', 'director']]
df['year'] = df['year'].apply(lambda i: str(i))

documents = df.to_dict(orient='records')

for doc in tqdm(documents):
    es_client.index(index=index_name, document=doc)


# In[8]:


def elastic_search(query):
    search_query = {
        "size": 5,
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title", "plot", "genres", "director"],
                        "type": "best_fields"
                    }
                },
            }
        }
    }

    response = es_client.search(index=index_name, body=search_query)
    
    result_docs = []
    
    for hit in response['hits']['hits']:
        hit_dict = hit['_source']
        hit_dict['_score'] = hit['_score']
        result_docs.append(hit_dict)

    return result_docs


# In[9]:


queries = ['What does Ryan Bingham do for a living, and how does it relate to his frequent travels?',
           "How does Ryan's perspective on relationships change throughout the movie?",
           'What challenges does Natalie face regarding her new layoffs program, and how does Ryan respond to it?',
           "What significant events occur during Ryan's sister's wedding that impact his character development?",
           'What realization does Ryan come to about his life and personal philosophies towards the end of the film?']


print('Movie title:', documents[150]['title'], '\n')
i = 1
for query in queries:
    print(f'{i}: {query}')
    for doc in elastic_search(query):
        print(f"--{doc['title']}", end = '\t')
    i+=1
    print('\n************')


# In[10]:


query = 'What does Ryan Bingham do for a living, and how does it relate to his frequent travels?'
for doc in elastic_search(query):
    print(doc)


# In[11]:


def rag(query):
    search_results = elastic_search(query)
    prompt = build_prompt(query, search_results)
    answer = llm(prompt)
    return answer

query = 'What does Ryan Bingham do for a living, and how does it relate to his frequent travels?'

answer = rag(query)
print(answer)


# ## Elasticsearch-Vector_search

# In[26]:


from sentence_transformers import SentenceTransformer


# In[27]:


model_name = 'multi-qa-MiniLM-L6-cos-v1'
model = SentenceTransformer(model_name)


# In[ ]:


# df['vector'] = df.progress_apply(lambda row: model.encode(f"Title: {row['title']}\nPlot: {row['plot']}\nGenres: {row['genres']}\nDirector: {row['director']}"), axis = 1)

# df.to_csv('../data/movie_dataset.csv', index=False)


# In[28]:


df = pd.read_csv('../data/movie_dataset.csv')
print('Shape:', df.shape)
df.head(2)


# In[29]:


import ast

def str_to_vector(s:str):
    '''This functions converts str(vectror) to np.array(vector) type.'''
    
    s = s.replace('\n', ' ').strip()
    s = re.sub(r'(?<=\d)\s+(?=-?\d)', ',', s)
    
    try:
        return np.array(ast.literal_eval(s))
    except (SyntaxError, ValueError) as e:
        print(f"Error converting string to vector: {e}")
        return None


df['vector'] = df['vector'].progress_apply(str_to_vector)
df['year'] = df['year'].apply(lambda i: str(i))


# In[30]:


from elasticsearch import Elasticsearch

es_client_knn = Elasticsearch('http://localhost:9200') 

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
            "id": {"type": "keyword"},
            "vector": {
                "type": "dense_vector",
                "dims": 384,
                "index": True,
                "similarity": "cosine"
            },
        }
    }
}

index_name = "movie-questions"

es_client_knn.indices.delete(index=index_name, ignore_unavailable=True)
es_client_knn.indices.create(index=index_name, body=index_settings)


# In[31]:


documents = df.to_dict(orient='records')

for doc in tqdm(documents):
    es_client_knn.index(index=index_name, document=doc)


# In[32]:


def elastic_search_knn(query_vector):
    knn = {
        "field": 'vector',
        "query_vector": query_vector,
        "k": 5,
        "num_candidates": 10000,
    }

    search_query = {
        "knn": knn,
        "_source": ["title", "plot", "genres", "director", "id", "year"]
    }

    es_results = es_client_knn.search(
        index=index_name,
        body=search_query
    )
    
    result_docs = []
    
    for hit in es_results['hits']['hits']:
        hit_dict = hit['_source']
        hit_dict['_score'] = hit['_score']
        result_docs.append(hit_dict)

    return result_docs


# In[33]:


queries = ['What does Ryan Bingham do for a living, and how does it relate to his frequent travels?',
           "How does Ryan's perspective on relationships change throughout the movie?",
           'What challenges does Natalie face regarding her new layoffs program, and how does Ryan respond to it?',
           "What significant events occur during Ryan's sister's wedding that impact his character development?",
           'What realization does Ryan come to about his life and personal philosophies towards the end of the film?']


print('Movie title:', documents[150]['title'], '\n')
i = 1
for query in queries:
    print(f'{i}: {query}')
    for doc in elastic_search_knn(model.encode(query)):
        print(f"--{doc['title']}", end = '\t')
    i+=1
    print('\n************')


# In[34]:


def rag(query):
    search_results = elastic_search_knn(model.encode(query))
    prompt = build_prompt(query, search_results)
    answer = llm(prompt)
    return answer

query = 'What does Ryan Bingham do for a living, and how does it relate to his frequent travels?'

answer = rag(query)
print(answer)


# # 2. Retrieval evaluating

# I will evaluate 3 differen retrievals:
# - minisearch
# - elastic-search
# - elastic-search vector

# In[35]:


df_questions = pd.read_csv('../data/questions_ground_truth.csv')
ground_truth = df_questions.to_dict(orient='records')
ground_truth[0]


# In[36]:


def hit_rate(relevance_total):
    cnt = 0

    for line in relevance_total:
        if True in line:
            cnt = cnt + 1

    return cnt / len(relevance_total)


def mrr(relevance_total):
    total_score = 0.0

    for line in relevance_total:
        for rank in range(len(line)):
            if line[rank] == True:
                total_score = total_score + 1 / (rank + 1)

    return total_score / len(relevance_total)


def evaluate(ground_truth, search_function):
    relevance_total = []

    for q in tqdm(ground_truth):
        doc_id = q['id']
        results = search_function(q)
        relevance = [d['id'] == doc_id for d in results]
        relevance_total.append(relevance)

    return {
        'hit_rate': hit_rate(relevance_total),
        'mrr': mrr(relevance_total),
    }


# In[37]:


search_funtions = {'minisearch':minisearch,
                   'elastic_search':elastic_search,
                   'elastic_search_knn':elastic_search_knn}

for n, f in search_funtions.items():
    print(n, f)


# In[39]:


df_retrieval_eval = pd.DataFrame(columns=['search_function', 'hit_rate', 'mrr'])

for name, func in search_funtions.items():
    if name != 'elastic_search_knn':
        eval_res = evaluate(ground_truth, lambda q: func(q['question']))
    else:
        eval_res = evaluate(ground_truth, lambda q: func(model.encode(q['question'])))
    
    df_retrieval_eval.loc[len(df_retrieval_eval)] = {'search_function': name,
                                                     'hit_rate': eval_res['hit_rate'],
                                                     'mrr':eval_res['mrr']}


# In[40]:


df_retrieval_eval


# The best results are provided by `elastic-search retrieval`, so I will continue with it.

# In[50]:


def rag(query):
    search_results = elastic_search(query)
    prompt = build_prompt(query, search_results)
    answer = llm(prompt)
    return answer


# # 3. RAG Evaluation

# I will evaluate 2 different LLMs:
# 
# - `gpt-4o-mini`
# - `gpt-3.5-turbo-0125`

# In[12]:


prompt_judge_template = """
You are an expert evaluator for a RAG system that recommends a movie from the movie dataset that best matches the request or description provided by user.
Your task is to analyze the relevance of the generated answer to the given question.
Based on the relevance of the generated answer, you will classify it as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

Here is the data for evaluation:

Question: {question}

Generated Answer:
{answer_llm}

Please analyze the content and context of the generated answer in relation to the question
and provide your evaluation in parsable JSON without using code blocks:

{{
  "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
  "Explanation": "[Without preamble provide a brief explanation for your evaluation]"
}}
""".strip()


# In[13]:


df_questions = pd.read_csv('../data/questions_ground_truth.csv')
ground_truth = df_questions.to_dict(orient='records')
ground_truth[0]


# ## gpt-4o-mini

# In[87]:


## The cost is 0.26 USD

# evaluations_gpt_4o_mini = []

# def llm(prompt:str):
#     response = client.chat.completions.create(
#         model='gpt-4o-mini',
#         messages=[{"role": "user", "content": prompt}]
#     )
    
#     return response.choices[0].message.content

# for record in tqdm(ground_truth):
#     question = record['question']
#     answer_llm = rag(question) 

#     prompt = prompt_judge_template.format(
#         question=question,
#         answer_llm=answer_llm
#     )

#     evaluation = llm(prompt)
#     evaluation = json.loads(evaluation)

#     evaluations_gpt_4o_mini.append((record, answer_llm, evaluation))


# In[88]:


df_eval_1 = pd.DataFrame(evaluations_gpt_4o_mini, columns=['record', 'answer', 'evaluation'])

df_eval_1['model'] = 'gpt-4o-mini'
df_eval_1['id'] = df_eval_1.record.apply(lambda d: d['id'])
df_eval_1['question'] = df_eval_1.record.apply(lambda d: d['question'])

df_eval_1['relevance'] = df_eval_1.evaluation.apply(lambda d: d['Relevance'])
df_eval_1['explanation'] = df_eval_1.evaluation.apply(lambda d: d['Explanation'])


del df_eval_1['record']
del df_eval_1['evaluation']

df_eval_1 = df_eval_1[['id', 'question', 'model', 'answer', 'relevance', 'explanation']]


# In[96]:


df_eval_1.head(2)


# In[89]:


df_eval_1.relevance.value_counts(normalize=True)


# In[91]:


df_eval_1.to_csv('../data/rag-evaluation.csv', index=False)


# ## gpt-3.5-turbo-0125

# In[ ]:


evaluations_2 = []

def llm(prompt:str):
    response = client.chat.completions.create(
        model='gpt-3.5-turbo-0125',
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content


# In[36]:


# # The cost is 0.86 USD

# for record in tqdm(ground_truth):
#     question = record['question']
#     answer_llm = rag(question) 

#     prompt = prompt_judge_template.format(
#         question=question,
#         answer_llm=answer_llm
#     )

#     evaluation = llm(prompt)
#     evaluation = json.loads(evaluation)

#     evaluations_2.append((record, answer_llm, evaluation))


# In[37]:


len(evaluations_2)


# In[38]:


df_eval_2 = pd.DataFrame(evaluations_2, columns=['record', 'answer', 'evaluation'])

df_eval_2['model'] = 'gpt-3.5-turbo-0125'
df_eval_2['id'] = df_eval_2.record.apply(lambda d: d['id'])
df_eval_2['question'] = df_eval_2.record.apply(lambda d: d['question'])

df_eval_2['relevance'] = df_eval_2.evaluation.apply(lambda d: d['Relevance'])
df_eval_2['explanation'] = df_eval_2.evaluation.apply(lambda d: d['Explanation'])


del df_eval_2['record']
del df_eval_2['evaluation']

df_eval_2 = df_eval_2[['id', 'question', 'model', 'answer', 'relevance', 'explanation']]


# In[39]:


df_eval_2.head(2)


# In[40]:


df_eval_2.relevance.value_counts(normalize=True)


# In[46]:


df_eval = pd.concat([df_eval_1, df_eval_2], ignore_index=True)
df_eval.to_csv('../data/rag-evaluation.csv', index=False)


# In[67]:


grouped  = df_eval.groupby(['model', 'relevance']).agg({'relevance':'count'}).rename({'relevance':'count'}, axis=1)
grouped['count_norm'] = grouped['count'] / grouped['count'].sum()
grouped['count_norm'] = grouped['count_norm'].apply(lambda i: "{:.1%}".format(i))
grouped


import ingest

import os
from dotenv import load_dotenv
from openai import OpenAI

try:
    load_dotenv()
    openai_api_key = os.getenv('OPENAI_API_KEY')

    client = OpenAI()
    es_client = ingest.load_es()
    print('OpenAI client is ready')
except:
    print('OpenAI client is NOT ready. Make sure you have valid and installed API key.')

def elastic_search(query):
    index_name = "movie-questions"
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


def rag(query):
    search_results = elastic_search(query)
    prompt = build_prompt(query, search_results)
    answer = llm(prompt)

    return answer
import openai
from openai import OpenAI
import os
import json
from time import time
from dotenv import load_dotenv

import ingest

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    openai.api_key = openai_api_key
    client = OpenAI()
    print('OpenAI client is ready')
else:
    raise ValueError('API key not found in environment variables')

model = 'gpt-4o-mini'


# # Initialize the OpenAI client only in the main process
# client = None
# if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
#     if openai_api_key:
#         openai.api_key = openai_api_key
#         client = OpenAI()
#         print('OpenAI client is ready')
#     else:
#         raise ValueError('API key not found in environment variables')

# Initialize Elasticsearch only in the main process
es_client = None
if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    try:
        es_client = ingest.load_es()
        print('Elasticsearch client is ready')
    except Exception as e:
        print(f'[!!Warning!!] Elasticsearch client is NOT ready: {str(e)}')


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
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    
    answer = response.choices[0].message.content
    tokens = {
        'prompt_tokens': response.usage.prompt_tokens,
        'completion_tokens': response.usage.completion_tokens,
        'total_tokens': response.usage.total_tokens
    }

    return answer, tokens


def evaluate_relevance(question, answer):
    evaluation_prompt_template = """
You are an expert evaluator for a RAG system that recommends a movie from the movie dataset that best matches the request or description provided by user.
Your task is to analyze the relevance of the generated answer to the given question.
Based on the relevance of the generated answer, you will classify it as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

Here is the data for evaluation:

Question: {question}

Generated Answer:
{answer}

Please analyze the content and context of the generated answer in relation to the question
and provide your evaluation in parsable JSON without using code blocks:

{{
  "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
  "Explanation": "[Without preamble provide a brief explanation for your evaluation]"
}}
""".strip()

    prompt = evaluation_prompt_template.format(question=question, answer=answer)
    evaluation, tokens = llm(prompt)
    
    try:
        json_eval = json.loads(evaluation)
        return json_eval, tokens
    
    except json.JSONDecodeError:
        result = {
            "Relevance": "UNKNOWN",
            "Explanation": "Failed to parse evaluation",
        }
        return result, tokens


def rag(query):
    t_start = time()
    search_results = elastic_search(query)
    prompt = build_prompt(query, search_results)
    answer, tokens = llm(prompt)

    json_eval, eval_tokens = evaluate_relevance(query, answer)

    t_stop = time()
    time_took = t_stop - t_start

    openai_cost = (((tokens['prompt_tokens'] + eval_tokens["prompt_tokens"]) 
                   * 0.00015 + (tokens['completion_tokens'] + eval_tokens["completion_tokens"]) * 0.0006) / 1000)

    answer_data = {
        "answer": answer,
        "model_used": model,
        "response_time": time_took,
        "relevance": json_eval.get("Relevance", "UNKNOWN"),
        "relevance_explanation": json_eval.get("Explanation", "Failed to parse evaluation"),
        "prompt_tokens": tokens["prompt_tokens"],
        "completion_tokens": tokens["completion_tokens"],
        "total_tokens": tokens["total_tokens"],
        "eval_prompt_tokens": eval_tokens["prompt_tokens"],
        "eval_completion_tokens": eval_tokens["completion_tokens"],
        "eval_total_tokens": eval_tokens["total_tokens"],
        "openai_cost": openai_cost,
    }

    return answer_data
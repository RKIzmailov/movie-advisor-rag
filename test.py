import pandas as pd
import requests

df = pd.read_csv("./data/questions_ground_truth.csv")
question = df.sample(n=1).iloc[0]['question']
print("question: ", question)

url = "http://localhost:5000/ask"

data = {"question": question}

response = requests.post(url, json=data)
print(response.json())
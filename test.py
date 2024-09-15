import pandas as pd
import requests

question = "What does Ryan Bingham do for a living, and how does it relate to his frequent travels?"
url = "http://localhost:5000/ask"
print("question: ", question)

data = {"question": question}
response = requests.post(url, json=data)
print(response.json())
import sys
import os
import openai

request_txt = """
### Postgres SQL tables, with their properties:
#
# search_keywords(id, query, keyword, store_id)
# search_traffic_metrics(query_id, timestamp, traffic_count, ctr)
# stores(id, store_name:enum(Electronics,Mobiles,Fashion,Books,Accessories))
#
### Query to {}
"""

user_prompt_txt1 = "find top 100 keywords in Fashion store ordered by traffic count in last 30 days"
user_prompt_txt2 = "find top 10 keywords in Electronics store with the highest ctr in last 7 days"

# text-davinci-002,0.1,400
try:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=request_txt.format(user_prompt_txt2),
        temperature=0.1,
        max_tokens=400,
    )
    for choice in response.choices:
        print("Response (1 of n):")
        print(choice.text)

except openai.error.AuthenticationError as e:
    print("Authentication error: {}".format(e), file=sys.stderr)

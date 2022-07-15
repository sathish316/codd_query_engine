import sys
import os
import openai

request_txt = """
### Postgres SQL tables, with their properties:
#
# listings(listing_id,master_sku,title,rating,popularity)
# master_skus(master_sku,title)
# msku metrics - sku, marketplace, store, ratings, popularity
# Store - id, name
#
### Query to {}
"""

user_prompt_txt1 = "find skus in Meesho in fashion store with 5 star ratings not sold in Flipkart"
user_prompt_txt2 = "skus in Amazon in electronics store with popularity above 4.5 not sold in Flipkart"

# text-davinci-002,0.7,400
try:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Completion.create(
        engine="text-davinci-001",
        prompt=request_txt.format(user_prompt_txt1),
        temperature=0.2,
        max_tokens=400,
    )
    for choice in response.choices:
        print("Response (1 of n):")
        print(choice.text)

except openai.error.AuthenticationError as e:
    print("Authentication error: {}".format(e), file=sys.stderr)

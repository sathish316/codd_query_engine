import sys
import os
import openai

request_txt = """
### Postgres SQL tables, with their properties:
#
# listings(listing_id,master_sku,marketplace:enum(Flipkart),title,rating,popularity)
# master_skus(master_sku,title)
# msku metrics(sku, marketplace:enum(Meesho,Amazon,Flipkart), store:enum(Fashion,Electronics,Mobiles,Books,Furniture), ratings, popularity
#
### Query to {}
"""

user_prompt_txt1 = "find master skus in Meesho in Fashion store with 5 star ratings where the master sku does not exist in listings sold by Flipkart"
user_prompt_txt2 = "find master skus in Amazon in Electronics store with 5 star popularity where the master sku does not exist in listings sold by Flipkart"

# text-davinci-002,0.1,400
try:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=request_txt.format(user_prompt_txt1),
        temperature=0.1,
        max_tokens=400,
    )
    for choice in response.choices:
        print("Response (1 of n):")
        print(choice.text)

except openai.error.AuthenticationError as e:
    print("Authentication error: {}".format(e), file=sys.stderr)

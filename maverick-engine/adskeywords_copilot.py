import sys
import os
import openai

request_txt = """
### Postgres SQL tables, with their properties:
#
# search_queries(id, query, timestamp, store_id)
# search_traffic(id, timestamp, query_id, count)
# search_query_products(id, request_id, timestamp, query_id, product_id, position)
# keywords(id, keyword, store_id)
# query_keyword_mapping(keyword_id, query_id)
# stores(id, store_name:enum(Electronics,Mobiles,Fashion,Books,Accessories))
# products(id, title, store_id, price)
# product_page_views(product_id, timestamp, page_view_count) # timestamp is start of hour
# product_orders(product_id, timestamp, order_count))
#
### Query to {}
"""

user_prompt_txt1 = "find keywords which belong to Search queries only in Fashion store having search traffic of more than 1 million in last one month"
user_prompt_txt2 = "find top 1000 keywords which belong to Search queries in Fashion store in last one month ordered by search traffic count"

# text-davinci-002,0.7,400
try:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=request_txt.format(user_prompt_txt1),
        temperature=0.2,
        max_tokens=400,
    )
    for choice in response.choices:
        print("Response (1 of n):")
        print(choice.text)

except openai.error.AuthenticationError as e:
    print("Authentication error: {}".format(e), file=sys.stderr)

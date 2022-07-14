import os
import sys

import openai
import json
from flask import Flask, redirect, render_template, request, url_for, jsonify

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/text2sql', methods=['POST'])
def text2sql():
    print("HEREHERE:", request)
    print(request.data)
    prompt_request = json.loads(request.data)
    print("Request:" + prompt_request['prompt'])
    full_prompt = generate_prompt(prompt_request['database'], prompt_request['schema'], prompt_request['prompt'])
    query = generate_query(full_prompt, prompt_request['engine'], prompt_request['temperature'], prompt_request['tokens'])
    output = {'query': query}
    return json.dumps(output)

def generate_query(prompt, engine, temperature, tokens):
    try:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        response = openai.Completion.create(
            engine=engine,
            prompt=prompt,
            temperature=temperature,
            max_tokens=tokens,
        )
        for choice in response.choices:
            print("Response (1 of n):")
            print(choice.text)
        return response.choices[0].text

    except openai.error.AuthenticationError as e:
        print("Authentication error: {}".format(e), file=sys.stderr)


def generate_prompt(database, schema, prompt):
    prompt = """
    ### {} SQL tables, with their properties:
    #
    {}
    #
    ### Query to {}
    """.format(database, schema, prompt)
    return prompt

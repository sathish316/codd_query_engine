# Overview

Maverick Engine is the core Text2SQL Engine backend for Maverick.
It is powered by OpenAI Codex Text2SQL capabilities.

# APIs

POST /text2sql
Request:
{
    "database": "Postgres",
    "schema": "...",
    "prompt": "...",
    "engine": "text-davinci-001",
    "temperature": 0.2,
    "tokens": 400
}
Response:
{"query": "..."}


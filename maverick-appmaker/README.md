# Overview

Maverick AppMaker is the admin interface to define app and it's read flows and write flows

# Design

# Entity model
* App(id, name, schema, databasetype, engine_config) [S]
* Flow(id, name, app_id) [S]
* Panel(id, title, panel_type, natural_prompt:text, sql_query:text, flow_id) [M]

## Read flows

## Write flows

# APIs

## Read flows

## Write flows

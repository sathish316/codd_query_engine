# require 'models/text2sql'

class PanelsController < ApplicationController
    def create
        @app = App.find(params[:app_id])
        @flow = Flow.find(params[:flow_id])
        @panel = @flow.panels.create(panel_params)
        redirect_to app_flow_path(@app, @flow)
    end

    def update
        @app = App.find(params[:app_id])
        @flow = Flow.find(params[:flow_id])
        @panel = Panel.find(params[:id])
        sql_query = generate_sql_query(@app.text2sql_config, @panel.natural_prompt)
        result = @panel.update!(sql_query: sql_query.strip)
        redirect_to app_flow_path(@app, @flow)
    end

    private

    def panel_params
        params.require(:panel).permit(:title, :panel_type, :natural_prompt, :sql_query)
    end

    def generate_sql_query(config, prompt) 
        text2sql = Text2sql.new(config)
        sql_query = text2sql.convert(prompt)
        p "HERE"*100
        p sql_query['query']
        sql_query['query']
    end
end

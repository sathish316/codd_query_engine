class PanelsController < ApplicationController
    def create
        @app = App.find(params[:app_id])
        @flow = Flow.find(params[:flow_id])
        @panel = @flow.panels.create(panel_params)
        redirect_to app_flow_path(@app, @flow)
    end

    def generate_sql_query
        puts "HERE"*100
    end

    private

    def panel_params
        params.require(:panel).permit(:title, :panel_type, :natural_prompt, :sql_query)
    end
end

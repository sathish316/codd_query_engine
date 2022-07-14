require "httparty"

class Text2sql
    include HTTParty
    base_uri 'http://127.0.0.1:5000'

    def initialize(config)
        @config = config
    end

    def convert(prompt)
        request = {
            "database": @config.database,
            "schema": @config.schema,
            "prompt": prompt,
            "engine": @config.engine,
            "temperature": @config.temperature,
            "tokens": @config.tokens
        }.to_json
        response = self.class.post("/text2sql", 
            body: request, 
            headers: { 'Content-Type' => 'application/json' })
        resp_json = JSON.parse(response.body)
        resp_json
    end
end
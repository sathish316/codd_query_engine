class Text2sqlConfig
    attr_reader :database, :schema, :engine, :temperature, :tokens
    
    def initialize(database, schema, engine, temperature, tokens)
        @database = database
        @schema = schema
        @engine = engine
        @temperature = temperature
        @tokens = tokens
    end
end
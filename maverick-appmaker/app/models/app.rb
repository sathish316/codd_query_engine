require 'text2sql_config'
require 'text2sql'

class App < ApplicationRecord
    def text2sql_config
        engine_config = self.engine_config.split(",")
        config = Text2sqlConfig.new(self.databasetype, self.schema, engine_config[0], engine_config[1].to_f, engine_config[2].to_i)
        config
    end
end

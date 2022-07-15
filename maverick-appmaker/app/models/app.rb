require 'text2sql_config'
require 'text2sql'
require 'generic_db_config'
require 'generic_dao'

DB_CONFIG = {
    server: 'localhost',
    port: '3306',
    username: 'maverick',
    password: 'goose',
}

class App < ApplicationRecord
    def text2sql_config
        engine_config = self.engine_config.split(",")
        config = Text2sqlConfig.new(self.databasetype, self.schema, engine_config[0], engine_config[1].to_f, engine_config[2].to_i)
        config
    end

    def generic_db_config
        config = GenericDbConfig.new(self.databasetype, self.name.parameterize(separator: '_'), DB_CONFIG[:server], DB_CONFIG[:port], DB_CONFIG[:username], DB_CONFIG[:password])
        config
    end
end

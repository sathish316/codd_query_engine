class GenericDao
    def initialize(config)
        @config = config
    end

    def fetch_results(query)
        results = []
        begin
            client = get_connection
            results = client.query(query)
        rescue => e
            puts "Error: #{e.message}"
        end
        results
    end

    def get_connection
        #TODO: generalize this to support other database types
        get_mysql_connection
    end

    def get_mysql_connection
        begin
            connection = Mysql2::Client.new(
                host: @config.server,
                port: @config.port,
                username: @config.username,
                password: @config.password,
                database: @config.database
            )
        rescue => e
            puts "Error: #{e.message}"
        end
        connection
    end
end
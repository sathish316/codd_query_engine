class GenericDbConfig
    attr_reader :databasetype, :database, :server, :port, :username, :password
    
    def initialize(databasetype, database, server, port, username, password)
        @databasetype = databasetype
        @database = database
        @server = server
        @port = port
        @username = username
        @password = password
    end
end
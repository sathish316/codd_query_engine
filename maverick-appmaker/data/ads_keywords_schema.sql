create table search_keywords(id int not null, query VARCHAR(255), keyword VARCHAR(255), store_id int, primary key(id));
create table search_traffic_metrics(query_id int, timestamp DATETIME, traffic_count int, ctr double);
create table stores(id int not null, store_name VARCHAR(255), primary key (id));


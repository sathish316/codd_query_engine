create table search_queries(id int, query VARCHAR(255), timestamp DATETIME, store_id int); 

create table search_traffic(id int, timestamp DATETIME, query_id int, count int, store_id int);

create table search_query_products(id int, request_id VARCHAR(255), timestamp DATETIME, query_id int, product_id VARCHAR(255), position int); 

create table keywords(id int, keyword VARCHAR(255), store_id int);

create table query_keyword_mapping(keyword_id int, query_id int);

create table stores(id int, store_name VARCHAR(255));

create table products(id int, title VARCHAR(500), store_id int, price double);

create table product_page_views(product_id int, timestamp DATETIME, page_view_count int);

create table product_orders(product_id int, timestamp DATETIME, order_count int);
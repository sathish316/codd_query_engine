create table search_keywords(id int not null, query VARCHAR(255), keyword VARCHAR(255), store_id int, primary key(id));
create table search_traffic_metrics(query_id int, timestamp DATETIME, traffic_count int, ctr double);
create table stores(id int not null, store_name VARCHAR(255), primary key (id));

insert into stores (id, store_name) values (1, "Books");
insert into stores (id, store_name) values (2, "Fashion");
insert into stores (id, store_name) values (3, "Electronics");

select * from stores;

insert into search_keywords(id, query, keyword, store_id) values (10, "game of thrones", "game of thrones", 1);

insert into search_keywords(id, query, keyword, store_id) values (20, "nike shoes", "nike shoes", 2);
insert into search_keywords(id, query, keyword, store_id) values (21, "adidas shoes", "adidas shoes", 2);
insert into search_keywords(id, query, keyword, store_id) values (22, "aurelia", "aurelia", 2);
insert into search_keywords(id, query, keyword, store_id) values (23, "levis jeans", "levis jeans", 2);

insert into search_keywords(id, query, keyword, store_id) values (30, "nothing phone", "nothing phone", 3);
insert into search_keywords(id, query, keyword, store_id) values (31, "apple watch", "apple watch", 3);
insert into search_keywords(id, query, keyword, store_id) values (32, "mi 6", "mi 6", 3);
insert into search_keywords(id, query, keyword, store_id) values (33, "ipad", "ipad", 3);

select * from search_keywords;
 

insert into search_traffic_metrics(query_id, timestamp, traffic_count, ctr) values(10, NOW(), 1120, 1.5);
insert into search_traffic_metrics(query_id, timestamp, traffic_count, ctr) values(20, NOW(), 500, 2.5);
insert into search_traffic_metrics(query_id, timestamp, traffic_count, ctr) values(21, NOW(), 600, 1.9);
insert into search_traffic_metrics(query_id, timestamp, traffic_count, ctr) values(22, NOW(), 450, 1.4);
insert into search_traffic_metrics(query_id, timestamp, traffic_count, ctr) values(23, NOW(), 900, 3.2);
insert into search_traffic_metrics(query_id, timestamp, traffic_count, ctr) values(30, NOW(), 51000, 3.5);
insert into search_traffic_metrics(query_id, timestamp, traffic_count, ctr) values(31, NOW(), 33000, 2.1);
insert into search_traffic_metrics(query_id, timestamp, traffic_count, ctr) values(32, NOW(), 12500, 1.95);
insert into search_traffic_metrics(query_id, timestamp, traffic_count, ctr) values(33, NOW(), 40000, 2.25);

select * from search_traffic_metrics;

--working query 1
# select keyword, sum(traffic_count) as traffic_count
    # from search_traffic_metrics
    # join search_keywords on search_traffic_metrics.query_id = search_keywords.id
    # where store_id = (select id from stores where store_name = 'Fashion')
    # and timestamp >= date_sub(now(), interval 30 day)
    # group by keyword
    # order by traffic_count desc
    # limit 100;

--working query 2
# select keyword, avg(ctr) as avg_ctr
    # from search_keywords sk
    # join search_traffic_metrics stm on sk.id = stm.query_id
    # where sk.store_id = (select id from stores where store_name = 'Electronics')
    # group by sk.keyword
    # order by avg_ctr desc
    # limit 10;
    
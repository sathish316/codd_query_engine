create table listings(listing_id int not null,master_sku varchar(255),marketplace varchar(100),title VARCHAR(255),rating double,popularity DOUBLE, primary key(listing_id));
create table master_skus(master_sku varchar(100) not null,title varchar(255), primary key(master_sku));
create table msku_metrics(sku varchar(100), marketplace VARCHAR(100), store VARCHAR(100), ratings double, popularity double, primary key(sku));

# FK + Meesho listings in fashion
insert into listings(listing_id,master_sku,marketplace,title,rating,popularity) values(901, "MF101", "Flipkart", "Levis 503 jeans", 4.0, 4.2);
insert into master_skus(master_sku,title) values("MF101", "Levis 503 jeans");
insert into msku_metrics(sku, marketplace, store, ratings, popularity) values("MF101", "Meesho", "Fashion", 4.1, 4.5);

# Meesho only listings in fashion
insert into master_skus(master_sku,title) values("MF102", "Eagle jeans");
insert into msku_metrics(sku, marketplace, store, ratings, popularity) values("MF102", "Meesho", "Fashion", 5.0, 4.5);

insert into master_skus(master_sku,title) values("MF103", "Next jeans");
insert into msku_metrics(sku, marketplace, store, ratings, popularity) values("MF103", "Meesho", "Fashion", 2.5, 3.0);

select * from listings;
select * from master_skus;
select * from msku_metrics;
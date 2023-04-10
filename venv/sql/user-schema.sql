DROP SCHEMA IF EXISTS users_and_libraries;
CREATE SCHEMA users_and_libraries;
USE users_and_libraries;

DROP TABLE IF EXISTS User; 

create table User 
(username varchar(20) not null,
password varchar(20) not null,
type varchar(20) not null,
valid boolean not null,
primary key(username)
);
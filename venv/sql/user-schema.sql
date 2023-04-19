DROP SCHEMA IF EXISTS users_and_libraries;
CREATE SCHEMA users_and_libraries;
USE users_and_libraries;

DROP TABLE IF EXISTS User; 
DROP TABLE IF EXISTS Signup_Approval; 
DROP TABLE IF EXISTS School_Library; 




create table User 
(username varchar(20) not null,
password varchar(20) not null,
type varchar(20) not null check(type in ('student','teacher','librarian', 'admin')),
valid boolean not null,
primary key(username)
);

create table School_Library
(address varchar(50) NOT NULL,
name varchar(50),
city varchar(30),
phone char(10),
email   varchar(30),
principal  varchar(50),
library_admin   varchar(50),
primary key (address)
) ;

create table Signup_Approval
(
    username varchar(20) not null,
    address varchar(50) NOT NULL,
    primary key (username),
    foreign key (username) references User(username),
    foreign key (address) references School_Library(address)
);

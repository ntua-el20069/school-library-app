DROP SCHEMA IF EXISTS users_and_libraries;
DROP SCHEMA IF EXISTS users_and_libraries_backup;
DROP SCHEMA IF EXISTS users_libraries_books;
CREATE SCHEMA users_libraries_books;
USE users_libraries_books;

DROP TABLE IF EXISTS User; 
DROP TABLE IF EXISTS Signup_Approval; 
DROP TABLE IF EXISTS School_Library; 
DROP TABLE IF EXISTS Book;
DROP TABLE IF EXISTS Available;
DROP TABLE IF EXISTS Author;
DROP TABLE IF EXISTS Topic;
DROP TABLE IF EXISTS Keyword;     



create table User 
(username varchar(20) not null,
password varchar(20) not null,
type varchar(20) not null check(type in ('student','teacher','librarian', 'admin')),
valid boolean not null,
birth_date date,
first_name varchar(30),
last_name varchar(30),
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
    constraint foreign key (username) references User(username) on update restrict on delete restrict,
    constraint foreign key (address) references School_Library(address) on update restrict on delete restrict
);

create table Book
(
    ISBN varchar(20) not null,
    title varchar(100),
    publisher varchar(50),
    pages int check (pages>0),
    image varchar(200),
    language varchar(20),
    summary varchar(1000),
    primary key (ISBN)
);

create table Available
(
    ISBN varchar(20) not null,
    address varchar(50) NOT NULL,
    books_number int check(books_number>=0),
    primary key (ISBN, address),
    constraint foreign key (ISBN) references Book(ISBN) on update restrict on delete restrict,
    constraint foreign key (address) references School_Library(address) on update restrict on delete restrict
);

create table Author
(
    ISBN varchar(20) not null,
    name varchar(50) not null,
    primary key (ISBN, name),
    constraint foreign key (ISBN) references Book(ISBN) on update restrict on delete restrict
);

create table Topic 
(
    ISBN varchar(20) not null,
    topic varchar(50) not null,
    primary key (ISBN, topic),
    constraint foreign key (ISBN) references Book(ISBN) on update restrict on delete restrict
);

create table Keyword
(
    ISBN varchar(20) not null,
    keyword varchar(50) not null,
    primary key (ISBN, keyword),
    constraint foreign key (ISBN) references Book(ISBN) on update restrict on delete restrict
);
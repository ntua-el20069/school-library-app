DROP SCHEMA IF EXISTS school_library_network;
DROP SCHEMA IF EXISTS school_library_network_backup;
CREATE SCHEMA school_library_network;
USE school_library_network;

DROP TABLE IF EXISTS User; 
DROP TABLE IF EXISTS Signup_Approval; 
DROP TABLE IF EXISTS School_Library; 
DROP TABLE IF EXISTS Book;
DROP TABLE IF EXISTS Available;
DROP TABLE IF EXISTS Author;
DROP TABLE IF EXISTS Topic;
DROP TABLE IF EXISTS Keyword;     
DROP TABLE IF EXISTS Review;
DROP TABLE IF EXISTS Borrowing;
DROP TABLE IF EXISTS Reservation; 

/* 
    Some constraints need to be added
    In this time, we have on update restrict, on delete restrict in every foreign key...
    WARNING!!!!
    If you change something, change this comment too!
*/

create table User 
(username varchar(20) not null,
password varchar(20) not null,
type varchar(20) not null check(type in ('student','teacher','librarian', 'admin')),
valid boolean not null,
birth_date date,
first_name varchar(30),
last_name varchar(30),
address varchar(50),
primary key(username)
);

create table School_Library
(address varchar(50) NOT NULL,
name varchar(50),
city varchar(30),
phone char(10),
email   varchar(30),
principal  varchar(50),
username varchar(20) ,
primary key (address),
constraint  foreign key (username) references User(username) on update restrict on delete restrict
) ;

alter table User 
add constraint foreign key (address) references School_Library(address) on update restrict on delete restrict;

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

create table Review 
(
    username varchar(20) not null,
    ISBN varchar(20) not null,
    likert int check (likert in (1,2,3,4,5)),
    review_text text,
    approval boolean,
    primary key (username, ISBN),
    constraint foreign key (username) references User(username) on update restrict on delete restrict,
    constraint foreign key (ISBN) references Book(ISBN) on update restrict on delete restrict
);

create table Borrowing
(
    username varchar(20) not null,
    address varchar(50) NOT NULL,
    ISBN varchar(20) not null,
    start_date date,
    returned boolean,
    approval boolean,
    librarian varchar(20),
    demand_time timestamp,
    primary key (username, address, ISBN, demand_time),
    constraint foreign key (username) references User(username) on update restrict on delete restrict,
    constraint foreign key (address) references School_Library(address) on update restrict on delete restrict,
    constraint foreign key (ISBN) references Book(ISBN) on update restrict on delete restrict,
    constraint foreign key (librarian) references User(username) on update restrict on delete restrict
);

create table Reservation
(
    username varchar(20) not null,
    address varchar(50) NOT NULL,
    ISBN varchar(20) not null,
    start_date date,
    primary key (username, address, ISBN),
    constraint foreign key (username) references User(username) on update restrict on delete restrict,
    constraint foreign key (address) references School_Library(address) on update restrict on delete restrict,
    constraint foreign key (ISBN) references Book(ISBN) on update restrict on delete restrict
);

DELIMITER ;;

CREATE TRIGGER `borrow` AFTER INSERT ON `Borrowing` FOR EACH ROW BEGIN
    if new.approval=1 then 
        UPDATE Available A SET books_number=books_number - 1 where A.ISBN=new.ISBN and A.address=new.address;
    end if;
  END;;
CREATE TRIGGER `borrow_update` AFTER UPDATE ON `Borrowing` FOR EACH ROW
BEGIN
    IF NEW.approval = 1 AND OLD.approval <> 1 THEN 
        UPDATE Available A
        SET A.books_number = A.books_number - 1
        WHERE A.ISBN = NEW.ISBN AND A.address = NEW.address;
    ELSEIF NEW.approval = 1 AND OLD.approval = 1 AND NEW.returned = 1 AND OLD.returned = 0 THEN
        UPDATE Available A
        SET A.books_number = A.books_number + 1
        WHERE A.ISBN = NEW.ISBN AND A.address = NEW.address;
    end if;
end;;

DELIMITER ;
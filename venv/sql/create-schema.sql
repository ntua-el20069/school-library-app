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

create index index_first on User (first_name);
create index index_last on User (last_name);

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
CREATE INDEX index_title ON Book (title);

create table Available
(
    ISBN varchar(20) not null,
    address varchar(50) NOT NULL,
    books_number int check(books_number>=0),
    primary key (ISBN, address),
    constraint foreign key (ISBN) references Book(ISBN) on update restrict on delete restrict,
    constraint foreign key (address) references School_Library(address) on update restrict on delete restrict
);

CREATE INDEX index_books_number ON Available (books_number);

create table Author
(
    ISBN varchar(20) not null,
    name varchar(50) not null,
    primary key (ISBN, name),
    constraint foreign key (ISBN) references Book(ISBN) on update restrict on delete restrict
);

CREATE INDEX index_author ON Author (name);

create table Topic 
(
    ISBN varchar(20) not null,
    topic varchar(50) not null,
    primary key (ISBN, topic),
    constraint foreign key (ISBN) references Book(ISBN) on update restrict on delete restrict
);

CREATE INDEX index_topic ON Topic (topic);

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

CREATE INDEX index_review ON Review (username);

create table Borrowing
(
    username varchar(20) not null,
    address varchar(50) NOT NULL,
    ISBN varchar(20) not null,
    start_date date,
    returned boolean,
    librarian varchar(20),
    primary key (username, address, ISBN, start_date),
    constraint foreign key (username) references User(username) on update restrict on delete restrict,
    constraint foreign key (address) references School_Library(address) on update restrict on delete restrict,
    constraint foreign key (ISBN) references Book(ISBN) on update restrict on delete restrict,
    constraint foreign key (librarian) references User(username) on update restrict on delete restrict
);

create index index_start on Borrowing (start_date);

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

create view reservation_numbers as 
(select username, address, count(*) as number from Reservation group by username, address);

create view borrowing_numbers as 
(select username, address, returned,  count(*) as number from Borrowing group by username, address, returned);

create view unavailable_books as
(select ISBN, address, books_number from Available where books_number=0);

create view new_teachers as
(select * from User where type='teacher' and birth_date > DATE_SUB(CURDATE(), INTERVAL 40 YEAR));

create view author_num_books as
(select name, count(*) as books_written from Author group by name);

create view max_books_written as
(select max(books_written) from author_num_books);

create view review_book_topic as
(select username, B.ISBN, topic, likert from review R, book B, topic T  where R.ISBN=B.ISBN and B.ISBN=T.ISBN);

create view this_year_borrowings as 
(select * from Borrowing where start_date > DATE_SUB(CURDATE(), INTERVAL 1 YEAR));

create view reservation_available as
(select username, A.address as address, A.ISBN as ISBN, start_date, books_number 
from Reservation R, Available A  where A.ISBN=R.ISBN and A.address=R.address);

create view borrowing_available as
(select username, A.address as address, A.ISBN as ISBN, start_date, returned, librarian, books_number 
from Borrowing B, Available A  where A.ISBN=B.ISBN and A.address=B.address);

create view delayed_not_returned as
(select *  from Borrowing where returned=0 and DATE_ADD(start_date, INTERVAL 7 DAY) < CURDATE());

create view reservation_user_book as
(select R.username as username, R.address as address, R.ISBN as ISBN , start_date, first_name, last_name, type, title
from Reservation R, User U, Book B
where R.username=U.username and R.ISBN=B.ISBN);

create view borrowing_user_book as
(select bor.username as username, bor.address as address, bor.ISBN as ISBN , start_date, first_name, last_name, type, title, returned, librarian
from Borrowing bor, User U, Book B
where bor.username=U.username and bor.ISBN=B.ISBN);

-- 4.1.7 (Administrator question) 
-- Find all authors who have written at least 5 books less than the author with the most books.
create view frequent_authors as 
(select * from author_num_books where books_written >= (select * from max_books_written) - 5);

-- 4.2.3 (Librarian-Operator question)
-- Average Ratings per borrower and category (Search criteria: user/category)
-- per borrower:
create view avg_borrower_rating as 
(select username, avg(likert) as avg_likert from Review group by username);
-- per category-topic:
create view avg_category_rating as
(select topic, avg(likert) as avg_likert from review_book_topic group by topic);

DELIMITER ;;

CREATE TRIGGER `borrow` AFTER INSERT ON `Borrowing` FOR EACH ROW BEGIN
    declare books int;
    declare bor_num int;
    declare bor_type varchar(20);
    select books_number into books from Available A where A.ISBN=new.ISBN and A.address=new.address;
    select count(*) into bor_num from Borrowing where username = NEW.username and DATE_SUB(CURDATE(), INTERVAL 7 DAY) < start_date;
    select type into bor_type from User where username = NEW.username;
    IF books=0 then
        -- ??? here I should insert it into Reservation ? no use try-except in Python .. and insert to Reservation
        SIGNAL SQLSTATE '45000' 
            SET MESSAGE_TEXT = 'Borrowing is not allowed (book is not available).';
    ELSEIF (bor_type='student' and bor_num >= 3) then
        SIGNAL SQLSTATE '45000' 
            SET MESSAGE_TEXT = 'Borrowing is not allowed (students can borrow only 2 books per week).';
    ELSEIF (bor_type='teacher' and bor_num >= 2) then
        SIGNAL SQLSTATE '45000' 
            SET MESSAGE_TEXT = 'Borrowing is not allowed (teachers can borrow only 1 books per week).';
    ELSEIF books>0 and new.returned=0 then 
        UPDATE Available A SET books_number=books_number - 1 where A.ISBN=new.ISBN and A.address=new.address;
    end if;
  END;;

CREATE TRIGGER `borrow_update` AFTER UPDATE ON `Borrowing` FOR EACH ROW BEGIN
    IF NEW.returned = 1 AND OLD.returned = 0 THEN
        -- the book was returned so increment the books_number for this (ISBN, address) in Available
        UPDATE Available A
        SET A.books_number = A.books_number + 1
        WHERE A.ISBN = NEW.ISBN AND A.address = NEW.address;
    end if;
  end;;

CREATE TRIGGER `reserve` AFTER INSERT ON `Reservation` FOR EACH ROW BEGIN
    declare res_type varchar(20);
    declare res_num int;
    declare delayed_and_not_returned int;
    declare borrowed int;
    select type into res_type from User where username = NEW.username;
    select count(*) into res_num from Reservation where username = NEW.username;
    select count(*) into delayed_and_not_returned from Borrowing where username = NEW.username and returned=0 and DATE_ADD(start_date, INTERVAL 7 DAY) < CURDATE();
    select count(*) into borrowed from Borrowing where username = NEW.username and address = NEW.address and ISBN = NEW.ISBN  and returned=0;
    if (res_type='student' and res_num >= 3) then
        SIGNAL SQLSTATE '45000' 
            SET MESSAGE_TEXT = 'Reservation is not allowed (students can reserve only 2 books per week).';
    elseif (res_type='teacher' and res_num >= 2) then
        SIGNAL SQLSTATE '45000' 
            SET MESSAGE_TEXT = 'Reservation is not allowed (teachers can reserve only 1 book per week).';
    elseif (delayed_and_not_returned > 0) then
        SIGNAL SQLSTATE '45000' 
            SET MESSAGE_TEXT = 'Reservation is not allowed (when there are delayed not returned books).';          
    elseif (borrowed > 0) then
        SIGNAL SQLSTATE '45000' 
            SET MESSAGE_TEXT = 'Reservation is not allowed (this user has borrowed this book).';       
    end if; 
  END;;

CREATE PROCEDURE DeletePastReservations() BEGIN
    DELETE FROM Reservation where DATE_SUB(CURDATE(), INTERVAL 7 DAY) > start_date;
 END;;

-- prefix p_ is used for parameters 
CREATE PROCEDURE DeleteReservation(IN p_username VARCHAR(20), IN p_address varchar(50), IN p_ISBN VARCHAR(20)) BEGIN
    DELETE FROM Reservation WHERE username = p_username AND address = p_address AND ISBN = p_ISBN;
 END;;


DELIMITER ;
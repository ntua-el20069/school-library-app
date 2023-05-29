from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from datetime import datetime, timedelta

# Define a function to check if the request is from another route
def is_internal_request():
    return request.referrer and request.referrer.startswith(request.host_url)

def sample():
    return render_template('sample-page.html')

def create(db):
    
    fd = open('venv\\sql\\create-schema.sql', 'r', encoding="utf-8")
    sqlFile = fd.read()
    fd.close()

    # this does not work currently ...
    cursor = db.cursor()
    try:
        cursor.execute(sqlFile, multi=True)
        # Consume the result of the multi-statement query
        for _ in cursor.fetchall():
            pass
        db.commit()
        print("Database creation successful!")
    except mysql.connector.Error as error:
        print(f"Error creating database: {error}")
        db.rollback()
    finally:
        cursor.close()

    # this creates database but not triggers...
    '''
    sqlCommands = sqlFile.split(';')

    for command in sqlCommands:
        # This will skip and report errors
    # For example, if the tables do not yet exist, this will skip over
    # the DROP TABLE commands
        try:
            cursor = db.cursor()
            cursor.execute(command)
        except mysql.connector.Error as err:
            print("Something went wrong: ", err)
            
    '''
    return 'creates the DataBase from the sql script'

def get_schools_list(db):
    cursor = db.cursor()
    cursor.execute("SELECT name, address FROM School_Library")
    schools = cursor.fetchall()
    return jsonify(schools=schools)

def get_topics_list(db):
    cursor = db.cursor()
    cursor.execute("SELECT distinct(topic) FROM Topic")
    topics = cursor.fetchall()
    return jsonify(topics=topics)

def get_borrowings_list(db, borrower):
    cursor = db.cursor()
    sql = f"select username, address, ISBN, start_date, type, first_name, last_name, title,  returned, librarian from borrowing_user_book where username='{borrower}' order by returned"
    cursor.execute(sql)
    userBorrowings = cursor.fetchall()
    return jsonify(userBorrowings=userBorrowings)

def get_reservations_list(db, reservant):
    cursor = db.cursor()
    sql = f"select username, R.address, R.ISBN, start_date, type, first_name, last_name, title, books_number from reservation_user_book R, Available A where username='{reservant}' and R.address=A.address and R.ISBN=A.ISBN"
    cursor.execute(sql)
    userReservations = cursor.fetchall()
    return jsonify(userReservations=userReservations)

def books_in_system(db, username):
    out = 'Books in System <br><br><br>'
    cursor = db.cursor()
    sql = "select title, ISBN from Book;"
    cursor.execute(sql)
    books = cursor.fetchall()
    for book in books:
        if book: out += "Title: {},<br> ISBN: {} <br> <a href='/{}/{}/review'> Review </a> <br><br>".format(book[0], book[1], username, book[1])
    return out

def review(db, username, ISBN):
    cursor = db.cursor()
    if request.method == 'POST':
        out = ''
        likert = request.form.get('likert')
        review_text = request.form.get('review')
        sql = f"select type from User where username='{username}'"
        cursor.execute(sql)
        type = cursor.fetchall()[0][0]
        approval = 0 if type=='student' else 1
        try:
            sql = f"insert into Review  values ('{username}' , '{ISBN}' , {likert} , '{review_text}' , {approval})"
            cursor.execute(sql)
            db.commit()
            out = f'Review: ({likert}) was successfully inserted <br>'
        except mysql.connector.Error as err:
            print("Something went wrong: ", err)
            out += 'There is an error- maybe duplicate insert into Review <br>'
        return out
    else:
        sql = f"select title from Book where ISBN='{ISBN}'"
        cursor.execute(sql)
        title = cursor.fetchall()[0][0]
        return render_template('review.html', username=username, ISBN=ISBN, title=title) 

def books_in_this_school(db, address, username):
    out = 'Books in this School <br><br><br>'
    cursor = db.cursor()
    sql = "select title, B.ISBN from Book B, Available A where B.ISBN=A.ISBN and A.address='{}';".format(address)
    cursor.execute(sql)
    books = cursor.fetchall()
    for book in books:
        if book: out += "Title: {}, ISBN: {}  <a href='/librarian/{}/{}/update-book'>Update book info</a>  <br>".format(book[0], book[1], username, book[1])
    return out

def books_for_user(db, username, address):
    out = 'Books in this School <br><br><br>'
    cursor = db.cursor()
    sql = "select title, B.ISBN, image from Book B, Available A where B.ISBN=A.ISBN and A.address='{}';".format(address)
    cursor.execute(sql)
    books = cursor.fetchall()
    for book in books:
        if book: out += "Title: {}, ISBN: {}  <br> <img src='{}' width='200px'>  <br><br>".format(book[0], book[1],  book[2])
    return out

def add_existing_book(db, address):
    if request.method == 'POST':
        out = ''
        ISBN = request.form.get('ISBN')
        copies = request.form.get('copies')
        cursor = db.cursor()
        try:    
            sql = "insert into Available values('{}','{}',{})".format(ISBN, address, copies)
            cursor.execute(sql)
            db.commit()
            out += 'ISBN: {}, address of school: {}, copies={} <br> inserted successfully <br>'.format(ISBN, address, copies)
        except mysql.connector.Error as err:
            print("Something went wrong: ", err)
            out += 'There is an error- maybe duplicate insert into Available <br>'
        return out
    else:
        return render_template('add-existing-book.html')

def notValidUsers(db, lib_username):
    if not is_internal_request(): abort(401)
    q = "select address from User where username='{}'".format(lib_username)
    cursor = db.cursor()
    cursor.execute(q)
    address = cursor.fetchall()[0][0]
    if address: 
        q = "select username, type, address from User where address='{}' and valid=0 ".format(address)
        cursor.execute(q)
        notValidUsers = cursor.fetchall()
        return jsonify(notValidUsers=notValidUsers)
    
def ValidUsers(db, lib_username, valid_bool): # call it with 1 for valid users and with 0 for not valid users
    #if not is_internal_request(): abort(401)
    q = "select address from User where username='{}'".format(lib_username)
    cursor = db.cursor()
    cursor.execute(q)
    address = cursor.fetchall()[0][0]
    if address: 
        q = "select username, type, address from User where  address='{}' and valid={} and (type='teacher' or type='student') ;".format(address, valid_bool)
        cursor.execute(q)
        Users = cursor.fetchall()
        return jsonify(Users=Users)
    
def notApprovedReviews(db, address):
    cursor = db.cursor()
    sql = f"""select username, ISBN, likert, review_text from Review where approval=0
                and username in (select username from User where address="{address}")"""
    cursor.execute(sql)
    Reviews = cursor.fetchall()
    return jsonify(Reviews=Reviews)

from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random

## Here are functions for routes that create schema, insert into db, return something from a db 
## but they are not main routes of the application
## There is also a function that indicates if the request is internal (is_internal_request)
## They "help"

# Define a function to check if the request is from another route
def is_internal_request():
    return request.referrer and request.referrer.startswith(request.host_url)

def sample():
    return render_template('sample-page.html')

def insert(db):
    return insert_user(db) + insert_lib(db) + insert_signup_approval(db) + insert_book(db) + insert_available(db)

def create(db):

    fd = open('venv\\sql\\user-schema.sql', 'r')
    sqlFile = fd.read()
    fd.close()

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
            
        
    return 'creates a db and a table inside'

def insert_user(db):
    fd = open('venv\csv\insert-user.csv', 'r', encoding="utf-8")
    csvFile = fd.read()
    fd.close()
    cursor = db.cursor()
    csvTuples = csvFile.split('\n')
    out = ''
    #return csvTuples
    count = 0
    for user in csvTuples:
        count += 1
        if user:
            attr = user.split(',')
            username, password = attr
            ## accepts users with a probability of 0.5
            valid = 0 if random.randint(1,100)>50 else 1
            type = ''
            if count==5: 
                type='admin'
                valid=1 
            elif count%10 == 0: type = 'teacher'
            elif count%12==0: type = 'librarian'
            else: type = 'student'

            try:
                sql_query = """insert into User values('{u}','{p}','{t}',{v});"""
                cursor.execute(sql_query.format(u=username,p=password,t=type,v=valid))
                db.commit()
                out = out + 'Username:  ' + username + ' &emsp;  Password:  ' + password + '<br>'
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
        else:
            break
    return out

def insert_lib(db):
    fd = open('venv\csv\insert-lib.csv', 'r', encoding="utf-8")
    csvFile = fd.read()
    fd.close()
    cursor = db.cursor()
    csvTuples = csvFile.split('\n')
    out = ''
    #return csvTuples
    count = 0
    for lib in csvTuples:
        count += 1
        name = str(random.randint(1,50)) + ' '
        if count%3 == 0: name += 'Primary School'
        elif count%3==1: name += 'Junior High School'
        else: name += 'High School'
        if lib:
            attr = lib.split(',')
            address, city, phone, email, principal, library_admin = attr
        
            try:
                sql_query = """insert into School_Library values('{}','{}','{}','{}','{}','{}','{}');""".format(address, name, city, phone, email, principal, library_admin)
                cursor.execute(sql_query)
                db.commit()
                out = out + 'address={}, name={}, city={}, phone={}, email={}, principal={}, library_admin={}'.format(address, name, city, phone, email, principal, library_admin) + '<br>'
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
        else:
            break
            
    return out

def insert_signup_approval(db):
    cursor = db.cursor()
    cursor.execute("SELECT username FROM User")
    users = cursor.fetchall()
    cursor.execute("SELECT address FROM School_Library")
    libs = cursor.fetchall()
    out = ''
    for tup in users:
        address =  random.choice(libs)[0]
        username = tup[0]
        try:
            sql_query = "insert into Signup_Approval values('{}','{}');".format(username, address)
            cursor.execute(sql_query)
            db.commit()
            out = out + username + ' ' + address + '<br>'
        except mysql.connector.Error as err:
                print("Something went wrong: ", err)
    return out

def get_schools_list(db):
    cursor = db.cursor()
    cursor.execute("SELECT name, address FROM School_Library")
    schools = cursor.fetchall()
    return jsonify(schools=schools)

def notValidUsers(db, lib_username):
    if not is_internal_request(): abort(401)
    q = "select address from Signup_Approval where username='{}'".format(lib_username)
    cursor = db.cursor()
    cursor.execute(q)
    address = cursor.fetchall()[0][0]
    if address: 
        q = "select User.username, type, address from User, Signup_Approval where User.username=Signup_Approval.username and address='{}' and valid=0 ".format(address)
        cursor.execute(q)
        notValidUsers = cursor.fetchall()
        return jsonify(notValidUsers=notValidUsers)
    
def ValidUsers(db, lib_username, valid_bool): # call it with 1 for valid users and with 0 for not valid users
    #if not is_internal_request(): abort(401)
    q = "select address from Signup_Approval where username='{}'".format(lib_username)
    cursor = db.cursor()
    cursor.execute(q)
    address = cursor.fetchall()[0][0]
    if address: 
        q = "select User.username, type, address from User, Signup_Approval where User.username=Signup_Approval.username and address='{}' and valid={} and (type='teacher' or type='student') ;".format(address, valid_bool)
        cursor.execute(q)
        Users = cursor.fetchall()
        return jsonify(Users=Users)
    
def insert_book(db):
    fd = open('venv\csv\insert-book.csv', 'r', encoding="utf-8")
    csvFile = fd.read()
    fd.close()
    cursor = db.cursor()
    csvTuples = csvFile.split('\n')
    out = ''
    #return csvTuples
    count = 0
    for book in csvTuples:
        count += 1
        if book:
            
            ISBN, title, publisher, pages, image, language = book.split(",")[0:6]
            summary = ','.join(book.split(",")[6:])
            try:
                sql = '''insert into Book values ("{}","{}","{}",{},"{}","{}","{}")'''.format(ISBN, title, publisher, pages, image, language, summary)
                cursor.execute(sql)
                db.commit()
                out += "ISBN = {}, title = {}, publisher = {}, pages = {}, image = {}, language = {},<br> &emsp; summary = {} <br><br>".format(ISBN, title, publisher, pages, image, language, summary)
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
        else:
            break
    ##### insert Topics, keywords, authors
    #### read topics from csv
    fd = open('venv\csv\\topic.csv', 'r', encoding="utf-8")
    csvFile = fd.read()
    fd.close()
    csvTuples = csvFile.split('\n')
    topics = [top for top in csvTuples]
    
    #### read keywords from csv
    fd = open('venv\csv\keyword.csv', 'r', encoding="utf-8")
    csvFile = fd.read()
    fd.close()
    csvTuples = csvFile.split('\n')
    keywords = [key for key in csvTuples]

    #### read authors from csv
    fd = open('venv\csv\\author.csv', 'r', encoding="utf-8")
    csvFile = fd.read()
    fd.close()
    csvTuples = csvFile.split('\n')
    authors = [auth for auth in csvTuples]
    
    ###### 
    sql = "select ISBN from Book"
    cursor.execute(sql)
    books = cursor.fetchall()
    for book in books:
        
        for i in range(random.randint(1,2)): # inserts one or two topics
            try:
                topic = random.choice(topics)
                sql = "insert into Topic values('{}','{}')".format(book[0], topic)
                cursor.execute(sql)
                db.commit()
                out += "ISBN : {}, Topic: {} <br>".format(book[0], topic)
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
        for i in range(random.randint(3,5)): # inserts three to five keywords
            try:
                keyword = random.choice(keywords)
                sql = "insert into Keyword values('{}','{}')".format(book[0], keyword)
                cursor.execute(sql)
                db.commit()
                out += "ISBN : {}, Keyword: {} <br>".format(book[0], keyword)
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
        for i in range(random.randint(1,3)): # inserts one to three authors
            try:
                author = random.choice(authors)
                sql = "insert into Author values('{}','{}')".format(book[0], author)
                cursor.execute(sql)
                db.commit()
                out += "ISBN : {}, Author: {} <br>".format(book[0], author)
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
            
        
    return out    

def insert_available(db):
    cursor = db.cursor()
    sql = "select ISBN from Book"
    cursor.execute(sql)
    books = cursor.fetchall()
    cursor.execute("SELECT name, address FROM School_Library")
    out =''
    addresses = [ s[1] for s in cursor.fetchall() ]
    print(addresses)
    for book in books:
        for i in range(random.randint(2,5)): # a book can be inserted in 2 to 5 different schools
            try:
                # there can be 0 to 30 copies of a book
                address = random.choice(addresses)
                copies = random.randint(0,30)
                sql = '''insert into Available values ("{}","{}",{})'''.format(book[0], address, copies) 
                cursor.execute(sql)
                db.commit()
                out += 'ISBN: {}, address of school: {}, copies={} <br>'.format(book[0], address, copies)
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
    return out
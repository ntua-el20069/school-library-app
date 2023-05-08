from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from datetime import datetime, timedelta

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
    write_dml = True
    f ='venv\\sql\\insert-schema.sql'
    if write_dml:
        with open(f, 'w', encoding="utf-8") as fd: 
            fd.write("") # clear dml file
    return insert_user(db, f, write_dml) + insert_lib(db, f, write_dml) + insert_signup_approval(db, f, write_dml) + insert_book(db, f, write_dml) + insert_available(db, f, write_dml) + insert_review(db, f, write_dml)

def insert_from_dml(db):
    fd = open('venv\\sql\\insert-schema.sql', 'r', encoding="utf-8")
    sqlFile = fd.read()
    fd.close()
    sqlCommands = sqlFile.split(';')

    for command in sqlCommands:
        # This will skip and report errors
        try:
            cursor = db.cursor()
            cursor.execute(command)
            db.commit()
        except mysql.connector.Error as err:
            print("Something went wrong: ", err)
    return 'inserted data from dml script'
    
def create(db):

    fd = open('venv\\sql\\create-schema.sql', 'r', encoding="utf-8")
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

def insert_user(db, f, write_dml):
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
            username, password, birth_date, first_name, last_name  = attr
            ## accepts users with a probability of 0.5
            valid = 0 if random.randint(1,100)>50 else 1
            type = ''
            if count==5: 
                type='admin'
                valid=1 
            elif count%10 == 0: type = 'teacher'
            elif count%12==0: 
                type = 'librarian'
                valid = 1
            else: type = 'student'

            try:
                sql_query = """insert into User values('{u}','{p}','{t}',{v},'{d}','{f}','{l}', null);"""
                sql = sql_query.format(u=username,p=password,t=type,v=valid,d=birth_date,f=first_name,l=last_name)
                cursor.execute(sql)
                db.commit()
                out += 'Username:  {} &emsp;  Password:  {}, &emsp; type={}, valid={}, birth_date: {}, first={}, last={}<br>'.format(username, password, type, valid, birth_date, first_name, last_name)
                if write_dml:
                    with open(f, 'a', encoding="utf-8") as fd:
                        fd.write(sql + ';' + '\n')
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
        else:
            break
    return out

def insert_lib(db, f, write_dml):
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
            address, city, phone, email, principal, _ = attr
            try:
                sql = """insert into School_Library values('{}','{}','{}','{}','{}','{}',{});""".format(address, name, city, phone, email, principal, 'null')
                cursor.execute(sql)
                db.commit()
                out = out + 'address={}, name={}, city={}, phone={}, email={}, principal={}, library_admin={}'.format(address, name, city, phone, email, principal, 'null') + '<br>'
                if write_dml:
                    with open(f, 'a', encoding="utf-8") as fd:
                        fd.write(sql + ';' + '\n')
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
        else:
            break
            
    return out

def insert_signup_approval(db, f, write_dml):
    cursor = db.cursor()
    cursor.execute("SELECT username, type FROM User")
    users = cursor.fetchall()
    cursor.execute("SELECT address FROM School_Library")
    libs = cursor.fetchall()
    libs_for_librarians = [lib[0] for lib in libs] # that's the list we use for librarians
    out = '' 
    for tup in users:
        username, type = tup
        if type=='librarian': # this is used to make each school have up to one librarian
            if libs_for_librarians:
                address = libs_for_librarians[0]
                libs_for_librarians.pop(0)
                try:
                    sql = f"update School_Library set username='{username}' where address='{address}'"
                    cursor.execute(sql)
                    db.commit()
                except mysql.connector.Error as err:
                    print("Something went wrong: ", err) 
                    return "<h1>Update Error!!!</h1>"
                # set library_admin = lib.username in table School Library
                ############################################
            else:
                address =  random.choice(libs)[0]
                try: 
                    sql = f"update User set valid=0 where username='{username}'"
                    cursor.execute(sql)
                    db.commit()
                    out += f"user {username} has valid=0 now! <br>"
                    if write_dml:
                        with open(f, 'a', encoding="utf-8") as fd:
                            fd.write(sql + ';' + '\n')
                except mysql.connector.Error as err:
                    print("Something went wrong: ", err) 
                    return "<h1>Update Error!!!</h1>"   
        else:
            address =  random.choice(libs)[0]
        try:
            sql = "update User set address='{}' where username='{}';".format(address, username)
            cursor.execute(sql)
            db.commit()
            out = out + username + ' ' + address + '<br>'
            if write_dml:
                with open(f, 'a', encoding="utf-8") as fd:
                    fd.write(sql + ';' + '\n')
        except mysql.connector.Error as err:
            print("Something went wrong: ", err)
    return out

def get_schools_list(db):
    cursor = db.cursor()
    cursor.execute("SELECT name, address FROM School_Library")
    schools = cursor.fetchall()
    return jsonify(schools=schools)

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
        if book: out += "Title: {}, ISBN: {}  <a href='/librarian/{}/{}/update-book'>Update book info</a><br>".format(book[0], book[1], username, book[1])
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
    
def notApprovedReviews(db):
    cursor = db.cursor()
    sql = "select username, ISBN, likert, review_text from Review where approval=0"
    cursor.execute(sql)
    Reviews = cursor.fetchall()
    return jsonify(Reviews=Reviews)

def insert_book(db, f, write_dml):
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
            summary = summary.replace("'","").replace('"','').replace(";",",")
            try:
                sql = '''insert into Book values ("{}","{}","{}",{},"{}","{}","{}")'''.format(ISBN, title, publisher, pages, image, language, summary)
                cursor.execute(sql)
                db.commit()
                out += "ISBN = {}, title = {}, publisher = {}, pages = {}, image = {}, language = {},<br> &emsp; summary = {} <br><br>".format(ISBN, title, publisher, pages, image, language, summary)
                if write_dml:
                    with open(f, 'a', encoding="utf-8") as fd:
                        fd.write(sql + ';' + '\n')
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
                if write_dml:
                    with open(f, 'a', encoding="utf-8") as fd:
                        fd.write(sql + ';' + '\n')
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
        for i in range(random.randint(3,5)): # inserts three to five keywords
            try:
                keyword = random.choice(keywords)
                sql = "insert into Keyword values('{}','{}')".format(book[0], keyword)
                cursor.execute(sql)
                db.commit()
                out += "ISBN : {}, Keyword: {} <br>".format(book[0], keyword)
                if write_dml:
                    with open(f, 'a', encoding="utf-8") as fd:
                        fd.write(sql + ';' + '\n')
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
        for i in range(random.randint(1,3)): # inserts one to three authors
            try:
                author = random.choice(authors)
                sql = "insert into Author values('{}','{}')".format(book[0], author)
                cursor.execute(sql)
                db.commit()
                out += "ISBN : {}, Author: {} <br>".format(book[0], author)
                if write_dml:
                    with open(f, 'a', encoding="utf-8") as fd:
                        fd.write(sql + ';' + '\n')
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
            
        
    return out    

def insert_available(db, f, write_dml):
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
                if write_dml:
                    with open(f, 'a', encoding="utf-8") as fd:
                        fd.write(sql + ';' + '\n')
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
    return out

def insert_review(db, f, write_dml):
    # read csv with review texts
    fd = open('venv\csv\\review-texts.csv', 'r', encoding="utf-8")
    csvFile = fd.read()
    fd.close()
    csvTuples = csvFile.split('\n')
    out = ''
    
    cursor = db.cursor()
    sql = "select ISBN from Book"
    cursor.execute(sql)
    books = random.choices(cursor.fetchall(), k = 200)  # maybe a book can be choosed two or more times
    sql = "select username, type from User"
    cursor.execute(sql)
    users = random.choices(cursor.fetchall(), k = 200)
    
    for review_text in csvTuples:    
        ISBN = random.choice(books)[0]
        username, type = random.choice(users)
        likert = random.choice([1,2,3,4,5])
        approval = 1 if type!='student' or random.randint(1,100)<60 else 0  # approves the review of librarians, teachers, admin and for students with a probability of 0.6
        review_text = review_text.replace('"','').replace("'","").replace(";",",")
        try:
            sql = "insert into Review values ('{}','{}',{},'{}',{})".format(username, ISBN, likert, review_text, approval)
            cursor.execute(sql)
            db.commit()
            out += "username = {}, type={}, ISBN = {}, likert = {}, review_text = {}, approval = {} <br>".format(username, type, ISBN, likert, review_text, approval)
            if write_dml:
                    with open(f, 'a', encoding="utf-8") as fd:
                        fd.write(sql + ';' + '\n')
        except mysql.connector.Error as err:
                print("Something went wrong: ", err)
    
    return out

def insert_reservation(db, f, write_dml):
    cursor = db.cursor()
    
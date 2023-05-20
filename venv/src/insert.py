from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from .helpRoutes import is_internal_request
from datetime import date, datetime, timedelta, time

def insert(db):
    write_dml = True
    f ='venv\\sql\\insert-schema.sql'
    if write_dml:
        with open(f, 'w', encoding="utf-8") as fd: 
            fd.write("") # clear dml file

    return  insert_user(db, f, write_dml) \
     + insert_lib(db, f, write_dml) \
     + insert_signup_approval(db, f, write_dml) \
     + insert_book(db, f, write_dml) \
     + insert_available(db, f, write_dml) \
     + insert_review(db, f, write_dml) \
     + insert_borrowing(db, f, write_dml) \
     + insert_reservation(db, f, write_dml) 

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
            ## accepts users with a probability of 0.8
            valid = 1 if random.randint(1,100)<80 else 0
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
                    if write_dml:
                        with open(f, 'a', encoding="utf-8") as fd:
                            fd.write(sql + ';' + '\n')
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
        
        for i in range(random.randint(1,3)): # inserts one to three topics
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
    for book in books:
        for i in range(random.randint(3,5)): # a book can be inserted in 3 to 5 different schools
            try:
                # there can be 0 to 30 copies of a book
                address = random.choice(addresses)
                copies = 0 if random.randint(1,100) < 20 else random.randint(1,30) # Prob[a book is not available] = 0.20
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
    sql = "select username, address, type from User where type='student' or type='teacher'"
    cursor.execute(sql)
    users = cursor.fetchall()
    out = ''
    for user in users:
        username, address, type = user
        if random.randint(1,100) < 90:
            sql = f"select B.ISBN from Book B, Available A  where B.ISBN=A.ISBN and address='{address}' and books_number>=0" # reservations are for both available and unavailable books
            cursor.execute(sql)
            books = cursor.fetchall()
            if books:
                x = 1 if type=='teacher' else random.randint(1,2) # 1 reservation to teachers per week , up to 2 for students
                for i in range(x):
                    ISBN = random.choice(books)[0]
                    # Get today's date
                    today = date.today()
                    # Calculate the date 7 days ago
                    week_ago = today - timedelta(days=7) # should be days=7
                    # Generate a random number between 0 and 6
                    rand_num = random.randint(0, 6)
                    # Calculate the random date in the past week
                    start_date = week_ago + timedelta(days=rand_num)
                    try:
                        sql = f"insert into Reservation values ('{username}', '{address}', '{ISBN}', '{start_date}')"
                        cursor.execute(sql)
                        db.commit()
                        out += f"username: {username}, address: {address}, ISBN: {ISBN}, start_date: {start_date} <br>"
                        if write_dml:
                            with open(f, 'a', encoding="utf-8") as fd:
                                fd.write(sql + ';' + '\n')
                    except mysql.connector.Error as err:
                        print("Something went wrong: ", err)
    return out

def insert_borrowing(db, f, write_dml):
    cursor = db.cursor()
    sql = "select username, address, type from User where type='student' or type='teacher'"
    cursor.execute(sql)
    users = cursor.fetchall()
    out = ''
    current_datetime = datetime.now()
    today = date.today()
    for user in users:
        username, address, type = user
        if random.randint(1,100) < 60: # prob[a user has borrowed from library at least one time] = 0.60
            sql = f"select B.ISBN, books_number from Book B, Available A  where B.ISBN=A.ISBN and address='{address}' and books_number>=0" # I use >= 0 to check the trigger insert on borrowing
            cursor.execute(sql)
            books = cursor.fetchall()
            sql = f"select * from User where type='librarian' and valid=1 and address='{address}'"
            cursor.execute(sql)
            libs = cursor.fetchall()
            if books and libs:
                librarian = libs[0][0]
                x = random.randint(2,3) 
                for i in range(x):
                    if len(books)<3: break
                    ISBN, books_number = books[random.randint(1,100) % len(books)]
                    books.pop()
                    for i in range(random.randint(1,3)):
                        #  at least 70% of the borrowings are the last 100 days
                        days_before = 100 if random.randint(1,100)<70 else 3000
                        ## compute a random start_date between demand past_date and now
                        past_date = today - timedelta(days=days_before)
                        time_only = time(12, 0, 0)
                        start_timestamp = datetime.combine(past_date, time_only)
                        end_timestamp = datetime.combine(today, time_only)
                        random_timestamp = random.uniform(start_timestamp, end_timestamp)
                        start_date = random_timestamp.date()
                        # prob is the probability that the book has been returned
                        if start_date < date(2023, 5, 1): prob = 98 
                        elif  start_date < date(2023, 5, 14): prob = 70
                        else: prob = 30
                        returned = 1 if random.randint(1,100)<prob else 0
                        try:
                            sql = f"insert into Borrowing values('{username}','{address}','{ISBN}','{start_date}',{returned}, '{librarian}')"
                            cursor.execute(sql)
                            db.commit()
                            out += f"username= {username}, address= {address}, ISBN= {ISBN},<br> start_date= {start_date} , returned= {returned} , librarian={librarian} <br><br>"
                            if write_dml:
                                with open(f, 'a', encoding="utf-8") as fd:
                                    fd.write(sql + ';' + '\n')
                        except mysql.connector.Error as err:
                            print("Something went wrong: ", err)                   
    return out
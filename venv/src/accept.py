from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from .helpRoutes import is_internal_request, create
from datetime import datetime, timedelta, date
import subprocess


## Here are some functions for Routes that accept librarians (from admin), users (from librarian)
## insert school
## disable users (from librarian) due to library policy
## change password
## backup and restore

def accept_librarians(db):
    if request.method == 'POST':
        cursor = db.cursor()
        cursor.execute("select username, address from User where type='librarian' and valid=0")
        notValidLibrarians = cursor.fetchall()
        out = ''
        for lib in notValidLibrarians:
            mode = request.form.get(lib[0])
            if mode=='accept': 
                sql = f"select F.address, F.username from User F, User S where F.address = S.address and F.type='librarian' and F.valid=1 and S.username='{lib[0]}'"
                cursor.execute(sql)
                existing_librarian = cursor.fetchall()
                if not existing_librarian:
                    ## it is not an efficient way ...
                    try:
                        sql_query = "update User set valid=1 where username='{}'".format(lib[0])
                        cursor.execute(sql_query)
                        db.commit()
                        #sql_query = "update School_Library set username='{}' where address='{}'".format(lib[0],  lib[1])
                        #cursor.execute(sql_query)
                        #db.commit()
                        out += lib[0] + ' accepted <br>'
                    except mysql.connector.Error as err:
                        print("Something went wrong: ", err)
                        return 'Update Error <br> '
                else:
                    print(existing_librarian)
                    out += f"School with address {existing_librarian[0][0]} has existing librarian: {existing_librarian[0][1]}. So {lib[0]} cannot be approved <br>"
        #out += '<br> <a href="/admin">Admin page</a>'
        return out
    else:
        cursor = db.cursor()
        out = 'These Schools have librarians: <br>'
        sql = '''select address, username from  User 
                 where type = "librarian" and valid=1'''
        cursor.execute(sql)
        addresses = cursor.fetchall()
        for tup in addresses:
            out += f"address: {tup[0]} librarian: {tup[1]}<br>"
        return render_template('accept-librarians.html') + out
    
def disable_librarians(db):
    if request.method == 'POST':
        cursor = db.cursor()
        cursor.execute("select username, address from User where type='librarian' and valid=1")
        ValidLibrarians = cursor.fetchall()
        out = ''
        for lib in ValidLibrarians:
            mode = request.form.get(lib[0])
            if mode=='disable': 
                try:
                    sql_query = "update User set valid=0 where username='{}'".format(lib[0])
                    cursor.execute(sql_query)
                    db.commit()
                    out += lib[0] + ' disabled <br>'
                except mysql.connector.Error as err:
                    print("Something went wrong: ", err)
                    return 'Update Error <br> '
        return out
    else:
        return render_template('disable-librarians.html') 

def accept_users(db, lib_username):
    if not is_internal_request(): abort(401)
    if request.method == 'POST':
        cursor = db.cursor()
        cursor.execute("select username from User where type='student' or type='teacher' and valid=0")
        notValidUsers = cursor.fetchall()
        out = ''
        for user in notValidUsers:
            mode = request.form.get(user[0])
            if mode=='accept':  
                ## it is not an efficient way ...
                try:
                    sql_query = "update User set valid=1 where username='{}'".format(user[0])
                    cursor.execute(sql_query)
                    db.commit()
                    out += user[0] + ' accepted <br>'
                except mysql.connector.Error as err:
                    print("Something went wrong: ", err)
                    return 'Update Error <br> '
        out += '<br> <a href="/librarian/{}">librarian  page</a>'.format(lib_username)
        return out
    else:
        return render_template('accept-users.html', lib_username=lib_username)
    
def accept_review(db, username, address):
    if request.method == 'POST':
        cursor = db.cursor()
        
        cursor.execute(f"""select U.username, ISBN from Review R, User U where U.username=R.username and approval=0 and address="{address}" """)
        notValidReviews = cursor.fetchall()
        print(notValidReviews)
        out = ''
        for review in notValidReviews:
            mode = request.form.get(review[0]+review[1])
            print(mode)
            if mode=='accept':  
                ## it is not an efficient way ...
                try:
                    sql_query = "update Review set approval=1 where username='{}' and ISBN='{}'".format(review[0], review[1])
                    cursor.execute(sql_query)
                    db.commit()
                    out += 'Review of user: ' + review[0] + ' about book with ISBN: '+ review[1] + ' accepted <br>'
                except mysql.connector.Error as err:
                    print("Something went wrong: ", err)
                    return 'Update Error <br> '
                
        return out
    else:
        return render_template('accept-reviews.html', username=username) 

def insert_school(db):
    if not is_internal_request(): abort(401)
    if request.method == 'POST':
        address = request.form.get('address')
        city = request.form.get('city')
        name = request.form.get('schoolName')
        email = request.form.get('email')
        phone = request.form.get('phone')
        principal = request.form.get('principal')
        #library_admin = request.form.get('libAdmin')
        cursor = db.cursor()
        try:
            sql_query = """insert into School_Library values('{}','{}','{}','{}','{}','{}');""".format(address, name, city, phone, email, principal)
            cursor.execute(sql_query)
            db.commit()
            out = 'School with attributes <br>'
            out = out + 'address={}, name={}, city={}, phone={}, email={}, principal={}'.format(address, name, city, phone, email, principal) + '<br>'
            out = out + 'was successfully inserted into DataBase <br>'
            return out 
        except mysql.connector.Error as err:
            print("Something went wrong: ", err)
            return "Error: maybe duplicate entry for school <br>"

    else:
        return render_template('insert-school.html')

def insert_book_by_librarian(db, username):
    if not is_internal_request(): abort(401)
    cursor = db.cursor()
    sql = '''select School_Library.address, name 
            from User, School_Library
            where School_Library.address = User.address and User.username="{}" '''.format(username)
    cursor.execute(sql)
    school = cursor.fetchall()[0]
    print(school)
    address , name = school
    if request.method == 'POST':
        ISBN = request.form.get('ISBN')
        title = request.form.get('title')
        publisher = request.form.get('publisher')
        pages = request.form.get('pages')
        image = request.form.get('image')
        language = request.form.get('language')
        summary = request.form.get('summary').replace('<br>',' ').replace('\n',' ')
        authors = request.form.get('authors').split(',')
        topics = request.form.get('topics').split(',')
        keywords = request.form.get('keywords').split(',')
        copies = request.form.get('copies')
        out = ''
        try:
            sql = '''insert into Book values ("{}","{}","{}",{},"{}","{}","{}")'''.format(ISBN, title, publisher, pages, image, language, summary)
            cursor.execute(sql)
            for author in authors:
                sql = "insert into Author values('{}','{}')".format(ISBN, author.strip())
                cursor.execute(sql)
            for topic in topics:
                sql = "insert into Topic values('{}','{}')".format(ISBN, topic.strip())
                cursor.execute(sql)
            for keyword in keywords:
                sql = "insert into Keyword values('{}','{}')".format(ISBN, keyword.strip())
                cursor.execute(sql)
            sql = '''insert into Available values("{}","{}", {})'''.format(ISBN, address, copies)
            cursor.execute(sql)
            db.commit()
            out += "ISBN = {}, title = {}, publisher = {}, pages = {}, image = {}, language = {},<br> &emsp; summary = {} <br><br>".format(ISBN, title, publisher, pages, image, language, summary)
            out += "ISBN : {}, Authors: {} <br>".format(ISBN, authors)
            out += "ISBN : {}, Topics: {} <br>".format(ISBN, topics)
            out += "ISBN : {}, Keywords: {} <br>".format(ISBN, keywords)
            out += "ISBN : {}, Address of School: {}, copies: {}".format(ISBN, address, copies)
            return out
        except mysql.connector.Error as err:
            print("Something went wrong: ", err)
            return "Error: maybe duplicate entry for book <br>"
    else:
        return render_template('insert-book.html', address=address, name=name)

def disable_users(db, lib_username):
    if not is_internal_request(): abort(401)
    if request.method == 'POST':
        cursor = db.cursor()
        cursor.execute("select username from User where type='student' or type='teacher' and valid=1")
        notValidUsers = cursor.fetchall()
        out = ''
        for user in notValidUsers:
            mode = request.form.get(user[0])
            if mode=='disable': 
                ## it is not an efficient way ...
                sql_query = "update User set valid=0 where username='{}'".format(user[0])
                cursor.execute(sql_query)
                db.commit()
                out += user[0] + ' disabled <br>'
        out += '<br> <a href="/librarian/{}">librarian  page</a>'.format(lib_username)
        return out
    else:
        return render_template('disable-users.html', lib_username=lib_username)
    
def change_password(db, username):
    if not is_internal_request(): abort(401)
    if request.method == 'POST':
        try:    
            new_password = request.form.get('pass1')
            cursor = db.cursor()
            sql = "update User set password='{}' where username='{}'".format(new_password, username)
            cursor.execute(sql)
            db.commit()
            return 'Password changed succesfully! <br> <a href="/signin"> Sign in page </a> <br>'
        except mysql.connector.Error as err:
            print("Something went wrong: ", err)
            return "Error: maybe update constraint <br>"
    else:
        return render_template('change-password.html', username=username)


def backup(db, db_name):
    if request.method == 'POST':
        confirm = request.form.get('backup')
        if confirm=='no': return 'backup creation was denied'
        out = ''
        cursor = db.cursor()
        cursor.execute('SHOW FULL TABLES WHERE Table_type = "BASE TABLE"')
        table_names = []
        for record in cursor.fetchall():
            table_names.append(record[0])
        backup_dbname = db_name + '_backup'
        try:
            cursor.execute(f'DROP SCHEMA IF EXISTS {backup_dbname}')
            cursor.execute(f'CREATE DATABASE {backup_dbname}')
            out += 'backup was successfully created <br>'
        except mysql.connector.Error as err:
            print("Something went wrong: ", err)
            return 'an error occured so that backup was not created <br>'
        
        cursor.execute(f'USE {backup_dbname}')
  
        for table_name in table_names:
            cursor.execute(
                f'CREATE TABLE {table_name} SELECT * FROM {db_name}.{table_name}')
        cursor.execute(f'USE {db_name}')
        out += 'the original database is used now'
        return out
    else:
        return render_template('backup.html')

def restore(db, db_name):
    if request.method == 'POST':
        confirm = request.form.get('restore')
        if confirm=='no': return 'restore action was denied'
        out = ''
        cursor = db.cursor()
        backup_dbname = db_name + '_backup'
        try:    
            cursor.execute(f'USE {backup_dbname}')
        except mysql.connector.Error as err:
            print("Something went wrong: ", err)
            return 'there is no backup database'
        #cursor.execute('SHOW FULL TABLES WHERE Table_type = "BASE TABLE"')
        table_names = []
        all_tables = "School_Library User Book Available Author Topic Keyword Review Borrowing Reservation"
        table_names = all_tables.split(' ')
        reversed_list = table_names[::-1]
        print(table_names)
        #for record in cursor.fetchall():
            #table_names.append(record[0])
    
        #cursor.execute(f'DROP SCHEMA IF EXISTS {db_name}')
        #cursor.execute(f'CREATE DATABASE {db_name}')
        cursor.execute(f'USE {db_name}')
        for table_name in reversed_list:
            try:
                cursor.execute(f'DELETE FROM {table_name}')
                db.commit()
                print(f"deleted from {table_name}")
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
                return 'an error occured so the restore process cannot proceed <br>'
        # disable triggers to insert data
        cursor.execute("SET @var_trigger = 0;")

        for table_name in table_names:
            print(table_name)
            #cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
            cursor.execute(f"SELECT * FROM {backup_dbname}.{table_name}")
            tuples = cursor.fetchall()
            for tup in tuples:
                try:
                    converted_values = []
                    for val in tup:
                        if isinstance(val, date):
                            converted_values.append(val.strftime('{}-{}-{}').format(val.year, val.month, val.day))
                        else:
                            converted_values.append(val)
                    tup = tuple(converted_values)
                    cursor.execute(f"INSERT INTO {table_name} values{tup} ")
                    db.commit()
                except mysql.connector.Error as err:
                    print(tup)
                    #for val in tup:
                        #print(type(val))
                    print("Something went wrong: ", err)
            #cursor.execute(f'CREATE TABLE {table_name} SELECT * FROM {backup_dbname}.{table_name}')
        #cursor.execute(f'USE {db_name}')
        # enable triggers
        cursor.execute("SET @var_trigger = 1;")

        out += 'restore was done <br> the original database is used now'
        return out
    else:
        return render_template('restore.html')

        
def update_book(db, ISBN, address):
    cursor = db.cursor()
    if request.method == 'POST':
        ISBN = request.form.get('ISBN')
        title = request.form.get('title')
        publisher = request.form.get('publisher')
        pages = request.form.get('pages')
        image = request.form.get('image')
        language = request.form.get('language')
        summary = request.form.get('summary').replace('<br>',' ').replace('\n',' ')
        authors = request.form.get('authors').split(',')
        topics = request.form.get('topics').split(',')
        keywords = request.form.get('keywords').split(',')
        copies = request.form.get('copies')
        out = ''
        try:
            sql = '''update Book set title="{}", publisher='{}', pages={}, image='{}', language='{}', summary="{}" where ISBN="{}"'''.format( title, publisher, pages, image, language, summary, ISBN)
            cursor.execute(sql)
            sql = 'delete from Author where ISBN="{}"'.format(ISBN)
            cursor.execute(sql)
            sql = 'delete from Topic where ISBN="{}"'.format(ISBN)
            cursor.execute(sql)
            sql = 'delete from Keyword where ISBN="{}"'.format(ISBN)
            cursor.execute(sql)
            for author in authors:
                sql = "insert into Author values('{}','{}')".format(ISBN, author.strip())
                cursor.execute(sql)
            for topic in topics:           
                sql = "insert into Topic values('{}','{}')".format(ISBN, topic.strip())
                cursor.execute(sql)
            for keyword in keywords:
                sql = "insert into Keyword values('{}','{}')".format(ISBN, keyword.strip())
                cursor.execute(sql)
            sql = '''update Available set books_number={} where ISBN="{}"'''.format(copies, ISBN)
            cursor.execute(sql)
            db.commit()
            out += "ISBN = {}, title = {}, publisher = {}, pages = {}, image = {}, language = {},<br> &emsp; summary = {} <br><br>".format(ISBN, title, publisher, pages, image, language, summary)
            out += "ISBN : {}, Authors: {} <br>".format(ISBN, authors)
            out += "ISBN : {}, Topics: {} <br>".format(ISBN, topics)
            out += "ISBN : {}, Keywords: {} <br>".format(ISBN, keywords)
            out += "ISBN : {}, Address of School: {}, copies: {}".format(ISBN, address, copies)
            return out
        except mysql.connector.Error as err:
            print("Something went wrong: ", err)
            return "Error in update <br>"
    else:
        sql = "select title, publisher, pages, image, language, summary from Book where ISBN='{}'".format(ISBN)
        cursor.execute(sql)
        title, publisher, pages, image, language, summary = cursor.fetchall()[0]
        
        ### find authors
        sql = "select name from Author where ISBN='{}'".format(ISBN)
        cursor.execute(sql)
        authors = []
        for author in cursor.fetchall():
            authors.append(author[0])
        authors = ", ".join(authors) # convert to string
        
        ### find keywords
        sql = "select keyword from Keyword where ISBN='{}'".format(ISBN)
        cursor.execute(sql)
        keywords = []
        for keyword in cursor.fetchall():
            keywords.append(keyword[0])
        print(keywords)
        keywords = ", ".join(keywords) # convert to string
        print(keywords)
        
        ### find topics
        sql = "select topic from Topic where ISBN='{}'".format(ISBN)
        cursor.execute(sql)
        topics = []
        for topic in cursor.fetchall():
            topics.append(topic[0])
        topics = ", ".join(topics) # convert to string

        ### find copies
        sql = "select books_number from Available where ISBN='{}' and address='{}'".format(ISBN, address)
        cursor.execute(sql)
        copies = cursor.fetchall()[0][0]

        return render_template('update-book.html', ISBN=ISBN, title=title, publisher=publisher, pages=pages, image=image, language=language, summary=summary, authors=authors, keywords=keywords, topics=topics, copies=copies)

def update_user(db, username):
    cursor = db.cursor()
    if request.method == 'POST':
        birth_date = request.form.get('birth_date')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')    
        out = 'Update of user {}  <br>'.format(username)
        try:
            sql_query = """update User set birth_date='{d}', first_name='{f}', last_name='{l}' where username='{u}'"""
            cursor.execute(sql_query.format(d=birth_date, f=first_name, l=last_name, u=username))
            db.commit() 
            out += "birth_date='{}', first_name='{}', last_name='{}'".format(birth_date, first_name, last_name)
        except mysql.connector.Error as err:
            print("Something went wrong: ", err)
            return 'Update Error <br> '
        return out
    else:
        sql = "select type, birth_date, first_name, last_name from User where username='{}'".format(username)
        cursor.execute(sql)
        type, birth_date, first_name, last_name = cursor.fetchall()[0]
        if type=='teacher':
            return render_template('update-user.html', username=username, birth_date=birth_date, first_name=first_name, last_name=last_name)
        else:
            return 'only teachers can update their info <br>'
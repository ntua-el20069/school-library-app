from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from .helpRoutes import is_internal_request


## Here are some functions for Routes that accept librarians (from admin), users (from librarian)
## insert school
## disable users (from librarian) due to library policy
## change password
## backup and restore

def accept_librarians(db):
    if request.method == 'POST':
        cursor = db.cursor()
        cursor.execute("select username from User where type='librarian' and valid=0")
        notValidLibrarians = cursor.fetchall()
        out = ''
        for lib in notValidLibrarians:
            mode = request.form.get(lib[0])
            if mode=='accept': 
                out += lib[0] + ' accepted <br>' 
                ## it is not an efficient way ...
                sql_query = "update User set valid=1 where username='{}'".format(lib[0])
                cursor.execute(sql_query)
                db.commit()
            out += '<br> <a href="/admin">Admin page</a>'
        return out
    else:
        return render_template('accept-librarians.html')
    
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
                sql_query = "update User set valid=1 where username='{}'".format(user[0])
                cursor.execute(sql_query)
                db.commit()
                out += user[0] + ' accepted <br>'
        out += '<br> <a href="/librarian/{}">librarian  page</a>'.format(lib_username)
        return out
    else:
        return render_template('accept-users.html', lib_username=lib_username)
    
def insert_school(db):
    if not is_internal_request(): abort(401)
    if request.method == 'POST':
        address = request.form.get('address')
        city = request.form.get('city')
        name = request.form.get('schoolName')
        email = request.form.get('email')
        phone = request.form.get('phone')
        principal = request.form.get('principal')
        library_admin = request.form.get('libAdmin')
        cursor = db.cursor()
        try:
            sql_query = """insert into School_Library values('{}','{}','{}','{}','{}','{}','{}');""".format(address, name, city, phone, email, principal, library_admin)
            cursor.execute(sql_query)
            db.commit()
            out = 'School with attributes <br>'
            out = out + 'address={}, name={}, city={}, phone={}, email={}, principal={}, library_admin={}'.format(address, name, city, phone, email, principal, library_admin) + '<br>'
            out = out + 'was successfully inserted into DataBase <br>'
            return out 
        except mysql.connector.Error as err:
            print("Something went wrong: ", err)
            return "Error: maybe duplicate entry for school <br>"

    else:
        return render_template('insert-school.html')
    
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
        cursor.execute('show tables;')
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
        cursor.execute('show tables;')
        table_names = []
        for record in cursor.fetchall():
            table_names.append(record[0])
        try:
            cursor.execute(f'DROP SCHEMA IF EXISTS {db_name}')
            cursor.execute(f'CREATE DATABASE {db_name}')
            cursor.execute(f'USE {db_name}')
            for table_name in table_names:
                cursor.execute(
                f'CREATE TABLE {table_name} SELECT * FROM {backup_dbname}.{table_name}')
            cursor.execute(f'USE {db_name}')
            out += 'restore was done <br> the original database is used now'
            return out
        except mysql.connector.Error as err:
            print("Something went wrong: ", err)
            return 'an error occured so the restore process cannot proceed <br>'
    else:
        return render_template('restore.html')
from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from .helpRoutes import is_internal_request


## Here are some functions for Routes that accept librarians (from admin), users (from librarian)

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
                out += user[0] + ' accepted <br>' 
                ## it is not an efficient way ...
                sql_query = "update User set valid=1 where username='{}'".format(user[0])
                cursor.execute(sql_query)
                db.commit()
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
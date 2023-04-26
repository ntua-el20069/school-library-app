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
            out = out + 'Username:  ' + username + ' &emsp;  Password:  ' + password + '<br>'
            ## accepts users with a probability of 0.5
            valid = 0 if random.randint(1,100)>50 else 1
            type = ''
            if count%10 == 0: type = 'teacher'
            elif count%19==0: type = 'librarian'
            else: type = 'student'

            try:
                sql_query = """insert into User values('{u}','{p}','{t}',{v});"""
                cursor.execute(sql_query.format(u=username,p=password,t=type,v=valid))
                db.commit()
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
            out = out + 'address={}, name={}, city={}, phone={}, email={}, principal={}, library_admin={}'.format(address, name, city, phone, email, principal, library_admin) + '<br>'
        
            try:
                sql_query = """insert into School_Library values('{}','{}','{}','{}','{}','{}','{}');""".format(address, name, city, phone, email, principal, library_admin)
                cursor.execute(sql_query)
                db.commit()
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
        out = out + username + ' ' + address + '<br>'
        sql_query = "insert into Signup_Approval values('{}','{}');".format(username, address)
        cursor.execute(sql_query)
        db.commit()
    return out

def get_schools_list(db):
    cursor = db.cursor()
    cursor.execute("SELECT name, address FROM School_Library")
    schools = cursor.fetchall()
    return jsonify(schools=schools)
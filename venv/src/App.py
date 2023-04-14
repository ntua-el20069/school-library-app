from flask import Flask, render_template, request, url_for, flash, redirect, jsonify
import mysql.connector 
import random

app = Flask(__name__)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",                       # that's because I do not use a password... you may change it for your DBMS
    database="users_and_libraries"   # a database I created to play with...
)

## in order to use the db "users_and_libraries" 
## run the page '/create' which creates schema
## and then '/insert' which inserts data into table User
## sign in operates according to the database (or not if you use the JS comments in "sign-in.html" 
## and the appropriate code in python)
## Attention!! when you run '/create' database drops and a new is created 
## So all data are lost !

###### Example using sakila database ####### (change above database="sakila")
'''
@app.route("/categories")
def category():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM category")
    categories = cursor.fetchall()
    out = ''
    for tup in categories:
        out = out + tup[1] + '<br>'
    return out #str(categories)
'''

# run '/' to see the home page
@app.route("/")
def home():
    return render_template('home.html')

# This is a simple routing example 
# If you want to make an html page, you should put it into directory 'templates'
@app.route("/sample")
def sample():
    return render_template('sample-page.html')

# create schema ...
@app.route("/create")
def create():
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

# insert data into User 
@app.route('/insert-user')
def insert_user():
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
            valid = 0
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

# insert data into School_Library 
@app.route('/insert-lib')
def insert_lib():
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

@app.route('/insert-signup-approval')
def insert_signup_approval():
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

@app.route("/signup", methods=['GET', 'POST'])
def signup_form_redirect():
    if request.method == 'POST':
        username = request.form.get('username')    
        password = request.form.get('pass1')     ### pass1 is the name! of the input field
        type = request.form.get('userType')
        
        cursor = db.cursor()
        try:
            sql_query = """insert into User values('{u}', '{p}', '{t}','0')"""
            cursor.execute(sql_query.format(u=username, p=password, t=type))
            db.commit()
        except mysql.connector.Error as err:
                print("Something went wrong: ", err)
        return redirect(url_for('notApprovedUser'))
    else:
        return render_template('sign-up.html')

@app.route('/schools-list')
def get_schools_list():
    cursor = db.cursor()
    cursor.execute("SELECT name, address FROM School_Library")
    schools = cursor.fetchall()
    return jsonify(schools=schools)

@app.route("/signin", methods=['GET', 'POST'])
def handle_signin():
    if request.method == 'POST':     # here I handle post request by submitting the sign in form
        
        username = request.form.get('username')    
        password = request.form.get('pass')     ### pass is the name! of the input field
        
        # the below are written using the database

        cursor = db.cursor()
        sql_query = """select * from User where username='{u}'"""
        cursor.execute(sql_query.format(u=username))
        user = cursor.fetchall()
        if not user: return 'User not found'
        correct_password = user[0][1] 
        if password != correct_password: return 'Incorrect Password!'
        else: return 'Succesfull login! <br><br> &emsp;' + username
        
        ##### the below handles post request if you do not use a database
        '''
        if username == 'nikospapa':
            return redirect(url_for('student'))
        else:
            return redirect(url_for('notApprovedUser'))
        '''
    else:
        return render_template('sign-in.html')

@app.route("/not-approved-user")
def notApprovedUser():
    return render_template('not-approved-user.html')

@app.route('/admin')
def admin():
    cursor = db.cursor()
    # find librarians that are not approved yet
    cursor.execute("SELECT * FROM User where valid=0 and type='librarian';")
    notValidUsers = cursor.fetchall()
    out = 'Not valid librarians (username, password) <br>'
    for tup in notValidUsers:
        out = out + tup[0] + ' ' + tup[1] + ' ' + tup[2] + '<br>'
    return out 
    #return render_template('admin.html')

@app.route("/student")
def student():
    return render_template('student.html')

if __name__ == '__main__':
    app.run(debug=True)
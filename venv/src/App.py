from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from datetime import timedelta

app = Flask(__name__)
auth = HTTPBasicAuth()

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",                       # that's because I do not use a password... you may change it for your DBMS
    database="users_and_libraries"   # a database I created to play with...
)

# Set the username and password for authentication
# Use @auth.login_required to make a route private...
users = {
    "dev": "chatgpt"
}

# Verify the username and password for each request
@auth.verify_password
def verify_password(username, password):
    if username in users and password == users[username]:
        return username

# Add the authentication decorator to the route
@app.route('/page')
@auth.login_required
def private_page():
    # Your private route code here
    return jsonify({"message": "This is a private page"})

# A global variable to store the secret token
#secret_token = None

# Define a function to check if the request is from another route
def is_internal_request():
    return request.referrer and request.referrer.startswith(request.host_url)

## in order to use the db "users_and_libraries" 
##  Apache and MySQL should be running...
## run the page '/create' which creates db and schema
## and then '/insert-user' which inserts data into table User
## and then '/insert-lib' which inserts data into table School-Library
## and then '/insert-signup-approval' which inserts data into table SignUp_Approval
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
@auth.login_required
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
@auth.login_required
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
@auth.login_required
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

# inserts all existing in the DB Users to the table Signup_Approval
# correlated by a random school
# should be done only when Signup_Approval is empty set ! 
# so that there will be no duplicate entry errors
@app.route('/insert-signup-approval')
@auth.login_required
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
        school = request.form.get('school')
        print(school)
        address = school.split(',')[1]
        print(address)
        cursor = db.cursor()
                 
        query = "select * from School_Library where address='{}'".format(address)
        cursor.execute(query)
        schoolExists = cursor.fetchall()

        if schoolExists:
            # insert into User
            try:
                sql_query = """insert into User values('{u}', '{p}', '{t}','0')"""
                cursor.execute(sql_query.format(u=username, p=password, t=type))
                db.commit()
                # insert into Signup_Approval
                sql_query = """insert into Signup_Approval values('{}','{}')""".format(username, address)
                cursor.execute(sql_query)
                db.commit()
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
                return 'Insertion Error: <br> maybe username is already used!'
        else:
            return 'school selected does not exist in database'
        return redirect(url_for('notApprovedUser'))
    else:
        return render_template('sign-up.html')

# returns json object with schools from the database 
# in order to be used in JS - Sign-up page
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
        else: 
            valid = user[0][3]
            if valid: 
                if user[0][2]=='librarian':
                    return redirect('/librarian/{}'.format(username))
                else:
                    #return render_template('/simple-user/{}'.format(username))
                    return 'Succesfull login!  <br><br> valid user &emsp;' + username
            else: return redirect(url_for('notApprovedUser'))
        
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

@app.route('/notValidLibrarians')
@auth.login_required
def notValidLibrarians():
    cursor = db.cursor()
    # find librarians that are not approved yet
    cursor.execute("SELECT * FROM User join Signup_Approval on User.username = Signup_Approval.username where valid=0 and type='librarian';")
    notValidLibrarians = cursor.fetchall()
    # 
    out = 'Not valid librarians (username, password) <br>'
    for tup in notValidLibrarians:
        out = out + tup[0] + ' ' + tup[1] + ' ' + tup[2] + ' ' + str(tup[3]) + ' ' + tup[4] + ' ' + tup[5] +  '<br>'
    
    return jsonify(notValidLibrarians=notValidLibrarians) 

@app.route('/accept-librarians', methods=['GET', 'POST'])
@auth.login_required
def accept_librarians():
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
            
        return out
    else:
        return render_template('accept-librarians.html')
    

@app.route('/admin')
@auth.login_required
def admin():
    return render_template('admin.html')

@app.route("/simple-user/<username>")
def simple_user(username):
    if not is_internal_request(): abort(401)
    return render_template('simple-user.html', username=username)

@app.route("/librarian/<username>")
def librarian(username):
    if not is_internal_request(): abort(401)
    cursor = db.cursor()
    q = "select address from Signup_Approval where username='{}'".format(username)
    cursor.execute(q)
    address = cursor.fetchall()[0][0]
    if address:
        return render_template("librarian.html", username=username, address=address)
    else:
        return 'An error occured!'

@app.route("/librarian/<lib_username>/accept-users", methods=['GET', 'POST'])
def accept_users(lib_username):
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

@app.route('/librarian/<lib_username>/notValidUsers')
def notValidUsers(lib_username):
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
        

if __name__ == '__main__':
    app.run(debug=True)
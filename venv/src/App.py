from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from datetime import datetime, timedelta
from .helpRoutes import *   # this is used to import all functions from 'helpRoutes.py' 
from .accept import *
from .insert import *
from .borrow_reserve import *
from .user_questions import *
from .admin_questions import *
from .operator_questions import *


app = Flask(__name__)
auth = HTTPBasicAuth()

db_name = "school_library_network" 

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",                       # that's because I do not use a password... you may change it for your DBMS
    database=db_name   # a database I created to play with...
)

    

def get_admin():
    cursor = db.cursor()
    sql = "select username, password from User where type='admin';"
    cursor.execute(sql)
    p = cursor.fetchall()[0]
    #print(p)
    return p
# Set the username and password for authentication
# Use @auth.login_required to make a route private...
users = {
    "dev": "chatgpt"
}



# Verify the username and password for each request
@auth.verify_password
def verify_password(username, password):
    if username in users and password == users[username]: #or username==get_admin()[0] and password==get_admin()[1]:
        return username

# Add the authentication decorator to the route
@app.route('/page')
@auth.login_required
def private_page():
    # Your private route code here
    return jsonify({"message": "This is a private page"})

## in order to use the db "users_and_libraries" 
##  Apache and MySQL should be running...
## run the page '/create' which creates db and schema

## and then '/insert-user' which inserts data into table User
## and then '/insert-lib' which inserts data into table School-Library
## and then '/insert-signup-approval' which inserts data into table SignUp_Approval
## and then '/insert-book' which inserts books in db and their characteristics
## and then '/insert-available' which inserts books into several schools

## All these can be done with '/insert'

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
def sample_route():
    return sample()


# create schema ...
@app.route("/create")
@auth.login_required
def create_route():
    return create(db)

# (Route /insert) In order to insert all and write dml script...
# inserts data into User 
# inserts data into School_Library 
# updates all existing in the DB Users with the address of their school
# inserts data into Book and Author, Keyword, Topic
# inserts all the existing books in several schools ..
# inserts reviews
# inserts reservations ...
 
@app.route("/insert")
@auth.login_required
def insert_route():
    return insert(db)

# insert from dml
@app.route("/dml")
@auth.login_required
def dml():
    return insert_from_dml(db)

@app.route("/signup", methods=['GET', 'POST'])
def signup_form_redirect():
    if request.method == 'POST':
        username = request.form.get('username')    
        password = request.form.get('pass1')     ### pass1 is the name! of the input field
        type = request.form.get('userType')
        school = request.form.get('school')
        birth_date = request.form.get('birth_date')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
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
                sql_query = """insert into User values('{u}', '{p}', '{t}','0','{d}','{f}','{l}','{a}')"""
                cursor.execute(sql_query.format(u=username, p=password, t=type, d=birth_date, f=first_name, l=last_name, a=address))
                db.commit()
            except mysql.connector.Error as err:
                print("Something went wrong: ", err)
                return 'Insertion Error: <br> maybe username is already used!'
        else:
            return 'school selected does not exist in database'
        return redirect('not-approved-user/{}'.format(username))
    else:
        return render_template('sign-up.html')

# returns json object with schools from the database 
# in order to be used in JS - Sign-up page
@app.route('/schools-list')
def schools_list_route():
    return get_schools_list(db)

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
                type = user[0][2]
                if type=='librarian':
                    return redirect('/librarian/{}'.format(username))
                elif type == 'admin':
                    return redirect('/{}/admin'.format(username))
                else:
                    return redirect('/simple-user/{}/{}'.format(type,username))
                    #return 'Succesfull login!  <br><br> valid user &emsp;' + username
            else: return redirect('/not-approved-user/{}'.format(username))
        
        ##### the below handles post request if you do not use a database
        '''
        if username == 'nikospapa':
            return redirect(url_for('student'))
        else:
            return redirect(url_for('notApprovedUser'))
        '''
    else:
        return render_template('sign-in.html')

@app.route("/not-approved-user/<username>")
def notApprovedUser(username):
    cursor = db.cursor()
    sql = "select type from User where username='{}'".format(username)
    cursor.execute(sql)
    type = cursor.fetchall()[0][0]
    out = ''
    if type=='librarian': out += 'Wait for the admin to validate you <br>'
    else:
        sql = '''select L.username, L.address, L.type
                from User L, User S
                where S.username="{}" and  S.address=L.address and L.type="librarian" and L.valid=1;'''.format(username)
        cursor.execute(sql)
        librarians = cursor.fetchall()
        
        if not librarians: out += 'There are no valid librarians in this school. You will wait for your validation until there is a valid librarian for your school'
        else:
            out += 'One of those librarians may validate you: <br>'
            for lib in librarians:
                out += lib[0] + '<br>'
    return render_template('not-approved-user.html', username=username) + out

@app.route('/notApprovedReviews')
def not_approved_reviews_route():
    if not is_internal_request(): abort(401)
    return notApprovedReviews(db)

@app.route('/notValidLibrarians')
def notValidLibrarians():
    if not is_internal_request(): abort(401)
    cursor = db.cursor()
    # find librarians that are not approved yet
    cursor.execute("SELECT username, type, address FROM User  where valid=0 and type='librarian';")
    notValidLibrarians = cursor.fetchall()
    # 
    out = 'Not valid librarians (username, password) <br>'
    for tup in notValidLibrarians:
        out = out + tup[0] + ' ' + tup[1] + ' ' + tup[2] + '<br>'
    
    return jsonify(notValidLibrarians=notValidLibrarians) 

@app.route('/accept-librarians', methods=['GET', 'POST'])
def accept_libs_route():
    if not is_internal_request(): abort(401)
    return accept_librarians(db)

@app.route('/<username>/admin')
def admin(username):
    if not is_internal_request(): abort(401)
    return render_template('admin.html', username=username)

@app.route('/not-borrowed-authors')
def not_borrowed_authors_route():
    if not is_internal_request(): abort(401)
    return not_borrowed_authors(db)

@app.route('/top3-popular-topic-couples')
def top_three_popular_topic_couples_route():
    if not is_internal_request(): abort(401)
    return three_popular_topic_couples(db)

@app.route('/frequent-borrowing-new-teachers')
def frequent_borrowing_new_teachers_route():
    if not is_internal_request(): abort(401)
    return frequent_borrowing_new_teachers(db)

@app.route('/frequent-authors')
def frequent_authors_route():
    if not is_internal_request(): abort(401)
    return frequent_authors(db)

@app.route("/simple-user/<type>/<username>")
def simple_user(type, username):
    if not is_internal_request(): abort(401)
    return render_template('simple-user.html', type=type, username=username)

@app.route("/simple-user/<type>/<username>/books-borrowed")
def books_borrowed_route(type, username):
    if not is_internal_request(): abort(401)
    return books_borrowed(db, username)

@app.route("/simple-user/<type>/<username>/card")
def simple_user_card(type, username):
    if not is_internal_request(): abort(401)
    cursor = db.cursor()
    sql = "select birth_date, first_name, last_name from User where username='{}'".format(username)
    cursor.execute(sql)
    birth_date, first_name, last_name = cursor.fetchall()[0]
    return '''Card of the valid member of School Library Network <br> {} ({}) <br>
               Birth Date = {} <br>
                First Name = {} <br>
                 Last Name = {} <br> '''.format(username, type, birth_date, first_name, last_name)

@app.route("/<username>/update-user", methods=['GET', 'POST'])
def update_user_route(username):
    if not is_internal_request(): abort(401)
    return update_user(db, username)

@app.route("/librarian/<username>", methods=['GET', 'POST'])
def librarian(username):
    if not is_internal_request(): abort(401)
    cursor = db.cursor()
    q = "select address from User where username='{}'".format(username)
    cursor.execute(q)
    address = cursor.fetchall()[0][0]
    if request.method == 'POST':
        borrower = request.form.get("borrower")
        reservant = request.form.get("reservant")
        if borrower=='' and reservant=='':
            return 'you should write username either on the borrowing or the reservation field'
        elif borrower!='':
            return redirect(f'/librarian/{username}/user-borrowings/{borrower}')
        else:
            return 'Reservations for user - find has not been implemented yet'
    else:
        if address:
            return render_template("librarian.html", username=username, address=address)
        else:
            return 'An error occured!'

@app.route("/librarian/<username>/all-borrowings")
def all_borrowings_lib_route(username):
    if not is_internal_request(): abort(401)
    cursor = db.cursor()
    q = "select address from User where username='{}'".format(username)
    cursor.execute(q)
    address = cursor.fetchall()[0][0]
    if address:
        return all_borrowings_lib(db, address)
    else:
        return 'An error occured!'

@app.route("/librarian/<username>/all-reservations")
def all_reservations_lib_route(username):
    if not is_internal_request(): abort(401)
    cursor = db.cursor()
    q = "select address from User where username='{}'".format(username)
    cursor.execute(q)
    address = cursor.fetchall()[0][0]
    if address:
        return all_reservations_lib(db, address)
    else:
        return 'An error occured!'

@app.route("/librarian/<username>/delayed-not-returned")
def delayed_not_returned_route(username):
    if not is_internal_request(): abort(401)
    cursor = db.cursor()
    q = "select address from User where username='{}'".format(username)
    cursor.execute(q)
    address = cursor.fetchall()[0][0]
    if address:
        return delayed_not_returned_lib(db, address)
    else:
        return 'An error occured!'

@app.route("/librarian/<username>/user-borrowings/<borrower>", methods=['GET', 'POST'])
def user_borrowings_route(username, borrower):
    if not is_internal_request(): abort(401)
    cursor = db.cursor()
    sql = f"select * from User U, User L where L.username='{username}' and U.username='{borrower}' and L.address=U.address"
    cursor.execute(sql)
    if  not cursor.fetchall(): return 'This user is not in this school! <br>'
    return user_borrowings(db, borrower)

@app.route('/<borrower>/get-borrowings-list')
def get_borrowings_list_route(borrower):
    if not is_internal_request(): abort(401)
    return get_borrowings_list(db, borrower)

@app.route("/librarian/<lib_username>/accept-users", methods=['GET', 'POST'])
def accept_users_route(lib_username):
    return accept_users(db, lib_username)

@app.route("/librarian/<lib_username>/disable-users", methods=['GET', 'POST'])
def disable_users_route(lib_username):
    return disable_users(db, lib_username)

@app.route('/librarian/<lib_username>/notValidUsers')
def notValidUsers_route(lib_username):
    return ValidUsers(db, lib_username, 0)      # valid=0

@app.route('/librarian/<lib_username>/ValidUsers')
def ValidUsers_route(lib_username):
    return ValidUsers(db, lib_username, 1)     # valid=1

@app.route('/librarian/<username>/insert-book', methods = ['GET', 'POST'])
def insert_book_by_lib(username):
    return insert_book_by_librarian(db, username)

@app.route('/librarian/<username>/add-existing-book', methods = ['GET', 'POST'])
def add_existing_book_route(username):
    if not is_internal_request(): abort(401)
    cursor = db.cursor()
    sql = "select address from User where username='{}'".format(username)
    cursor.execute(sql)
    address = cursor.fetchall()[0][0]
    return add_existing_book(db, address)

@app.route('/librarian/<username>/<ISBN>/update-book', methods = ['GET', 'POST'])
def update_book_route(username, ISBN):
    if not is_internal_request(): abort(401)
    cursor = db.cursor()
    sql = "select address from User where username='{}'".format(username)
    cursor.execute(sql)
    address = cursor.fetchall()[0][0]
    return update_book(db, ISBN, address)

@app.route('/<username>/books-in-system')
def books_in_system_route(username):
    if not is_internal_request(): abort(401)
    return books_in_system(db, username)

@app.route('/<username>/<ISBN>/review', methods=['GET', 'POST'])
def review_route(username, ISBN):
    if not is_internal_request(): abort(401)
    return review(db, username, ISBN)

@app.route('/accept-review', methods=['GET', 'POST'])
def accept_review_route():
    if not is_internal_request(): abort(401)
    return accept_review(db)

@app.route('/<username>/books-in-this-school')
def books_in_this_school_route(username):
    if not is_internal_request(): abort(401)
    cursor = db.cursor()
    sql = "select address from User where username='{}'".format(username)
    cursor.execute(sql)
    address = cursor.fetchall()[0][0]
    return books_in_this_school(db, address, username)

@app.route('/insert-school', methods=['GET', 'POST'])
def insert_school_route():
    return insert_school(db)

@app.route('/<username>/change-password', methods=['GET', 'POST'])
def change_password_route(username):
    return change_password(db, username)

@app.route('/backup', methods = ['GET', 'POST'])
def backup_route():
    if not is_internal_request(): abort(401)
    return backup(db, db_name)

@app.route('/restore', methods = ['GET', 'POST'])
def restore_route():
    if not is_internal_request(): abort(401)
    return restore(db, db_name)


if __name__ == '__main__':
    app.run(debug=True)
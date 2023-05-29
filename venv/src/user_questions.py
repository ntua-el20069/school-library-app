from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from .helpRoutes import is_internal_request
from datetime import datetime, timedelta

# 4.3.1.List with all books (Search criteria: title/category/author), ability to select a book and create
#       a reservation request
# Attention!!!
# The list is solved in def (function) books_in_library which is in operator_questions.py
# Here this part of the question is implemented:
# ability to  select a book and create a reservation request
def reserve_book(db, username, address, ISBN):
    cursor = db.cursor()
    sql = f"select title from Book where ISBN='{ISBN}'"
    cursor.execute(sql)
    title = cursor.fetchall()[0][0]
    if request.method == 'POST':
        confirm = request.form.get('reserve')
        if confirm=='no': return 'reservation was denied by user'
        try:
            cursor.execute("call DeletePastReservations()")
            db.commit()
            sql = f"insert into Reservation values ('{username}','{address}', '{ISBN}', CURDATE())"
            cursor.execute(sql)
            db.commit()
            return 'Book is now reserved by you!'
        except mysql.connector.Error as err:
            print(err)
            error_msg = f"Error while reserving the book: <br> {err} <br>"
            if 'Duplicate' in error_msg:
                error_msg += 'That means that you have already reserved this book this week <br>'
            return error_msg
    return render_template('reserve-book.html', ISBN=ISBN, title=title, username=username)

### Question 4.3.2 List of all books borrowed by this user
def books_borrowed(db, username):
    cursor = db.cursor()
    #sql = f"select username, address, ISBN, start_date, type, first_name, last_name, title,  returned, librarian from borrowing_user_book where username='{username}' order by returned"
    sql = f"select ISBN, title, count(*) as times from borrowing_user_book where username='{username}' group by ISBN, title"
    cursor.execute(sql)
    borrowings = cursor.fetchall()
    out = '<h1>Books I have borrowed: </h1>'
    for borrowing in borrowings:
        #username, address, ISBN, start_date, type, first_name, last_name, title,  returned, librarian = borrowing
        ISBN, title, times = borrowing
        out += f"ISBN = {ISBN}, title = {title}, times = {times} <a href='/{username}/{ISBN}/review'> Review </a> <br>"
        #out += f'username = {username}, type = {type}, address = {address} <br> name = {first_name} {last_name}, <br> address = {address} , ISBN = {ISBN}, title = {title} <br> &emsp; start_date = {start_date}, returned = {bool(returned)}, librarian = {librarian} <br><br>'
    return out
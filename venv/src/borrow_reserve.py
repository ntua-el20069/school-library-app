from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from .helpRoutes import is_internal_request
from datetime import datetime, timedelta

def all_borrowings_lib(db, address):
    cursor = db.cursor()
    sql = f"select username, ISBN, start_date, type, first_name, last_name, title,  returned, librarian from borrowing_user_book where address='{address}' order by username"
    cursor.execute(sql)
    borrowings = cursor.fetchall()
    out = '<h1> All borrowings </h1>'
    for borrowing in borrowings:
        username, ISBN, start_date, type, first_name, last_name, title,  returned, librarian = borrowing
        out += f'username = {username}, type = {type}, <br> name = {first_name} {last_name}, <br> address = {address} , ISBN = {ISBN}, title = {title} <br> &emsp; start_date = {start_date}, returned = {bool(returned)}, librarian = {librarian} <br><br>'
    return out

def all_reservations_lib(db, address):
    cursor = db.cursor()
    sql = "call DeletePastReservations()"
    cursor.execute(sql)
    db.commit()
    sql = f"select username, ISBN, start_date, type, first_name, last_name, title from reservation_user_book where address='{address}' order by username"
    cursor.execute(sql)
    reservations = cursor.fetchall()
    out = '<h1> All reservations </h1>'
    for reservation in reservations:
        username, ISBN, start_date, type, first_name, last_name, title = reservation
        out += f'username = {username}, type = {type}, <br> name = {first_name} {last_name}, <br> address = {address} , ISBN = {ISBN}, title = {title} <br> &emsp; start_date = {start_date} <br><br>'
    return out

def delayed_not_returned_lib(db, address):
    cursor = db.cursor()
    sql = f"select username, ISBN, start_date, type, first_name, last_name, title,  returned, librarian from delayed_not_returned_user_book where address='{address}' order by start_date"
    cursor.execute(sql)
    borrowings = cursor.fetchall()
    out = '<h1> Delayed and not returned borrowings </h1>'
    for borrowing in borrowings:
        username, ISBN, start_date, type, first_name, last_name, title,  returned, librarian = borrowing
        out += f'username = {username}, type = {type}, <br> name = {first_name} {last_name}, <br> address = {address} , ISBN = {ISBN}, title = {title} <br> &emsp; start_date = {start_date}, returned = {bool(returned)}, librarian = {librarian} <br><br>'
    return out

def user_borrowings(db, borrower):
    if request.method == 'POST':
        cursor = db.cursor()
        sql = f"select username, address, ISBN, start_date from borrowing where username='{borrower}' and returned=0"
        cursor.execute(sql)
        not_returned_borrowings = cursor.fetchall()
        out = ''
        for bor in not_returned_borrowings:
            key = [bor[0], bor[1], bor[2], str(bor[3])]
            input_name = '+'.join(key)
            print(input_name)
            mode = request.form.get(input_name)
            if mode=='return':
                try:
                    sql = f"update Borrowing set returned=1 where username='{bor[0]}' and address='{bor[1]}' and ISBN='{bor[2]}' and start_date='{bor[3]}'"
                    cursor.execute(sql)
                    db.commit()
                    out += f'Book from Borrowing with username= {bor[0]} and address= {bor[1]} and ISBN= {bor[2]} and start_date= {bor[3]} was returned! <br>'
                except mysql.connector.Error as err:
                    print("Something went wrong: ", err)
                    return 'Update Error <br> '
        return out
    else:
        return render_template('user-borrowings.html', borrower=borrower)
        
    
      
from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from .helpRoutes import is_internal_request
from datetime import datetime, timedelta

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
        out += f"ISBN = {ISBN}, title = {title}, times = {times} <br>"
        #out += f'username = {username}, type = {type}, address = {address} <br> name = {first_name} {last_name}, <br> address = {address} , ISBN = {ISBN}, title = {title} <br> &emsp; start_date = {start_date}, returned = {bool(returned)}, librarian = {librarian} <br><br>'
    return out
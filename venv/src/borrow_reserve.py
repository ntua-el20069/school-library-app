from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from .helpRoutes import is_internal_request
from datetime import datetime, timedelta

def all_borrowings_lib(db, username, address):
    cursor = db.cursor()
    sql = f"select username, ISBN, start_date, type, first_name, last_name, title,  returned, librarian from borrowing_user_book where address='{address}' order by username"
    cursor.execute(sql)
    borrowings = cursor.fetchall()
    out = ''
    for borrowing in borrowings:
        username, ISBN, start_date, type, first_name, last_name, title,  returned, librarian = borrowing
        out += f'username = {username}, type = {type}, <br> name = {first_name} {last_name}, <br> address = {address} , ISBN = {ISBN}, title = {title} <br> &emsp; start_date = {start_date}, returned = {bool(returned)}, librarian = {librarian} <br><br>'
    return out

def all_reservations_lib(db, username, address):
    cursor = db.cursor()
    sql = "call DeletePastReservations()"
    cursor.execute(sql)
    db.commit()
    sql = f"select username, ISBN, start_date, type, first_name, last_name, title from reservation_user_book where address='{address}' order by username"
    cursor.execute(sql)
    reservations = cursor.fetchall()
    out = ''
    for reservation in reservations:
        username, ISBN, start_date, type, first_name, last_name, title = reservation
        out += f'username = {username}, type = {type}, <br> name = {first_name} {last_name}, <br> address = {address} , ISBN = {ISBN}, title = {title} <br> &emsp; start_date = {start_date} <br><br>'
    return out
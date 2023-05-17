from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from .helpRoutes import is_internal_request
from datetime import datetime, timedelta

# 4.1.4.Find authors whose books have not been borrowed.
def not_borrowed_authors(db):
    cursor = db.cursor()
    sql = 'select distinct(name) from Author except select distinct(name) from borrowing_author'
    cursor.execute(sql)
    authors = cursor.fetchall()
    out = '<h1>Authors whose books have never been borrowed</h1>'
    for author in authors:
        out += f'{author[0]}<br>'
    return out

# 4.1.7.Find all authors who have written at least 5 books less than the author with the most books
def frequent_authors(db):
    cursor = db.cursor()
    sql = 'select * from frequent_authors'
    cursor.execute(sql)
    authors = cursor.fetchall()
    out = '<h1>authors who have written at least 5 books less than the author with the most books</h1>'
    for author in authors:
        out += f'Author: {author[0]} Books written: {author[1]}<br>'
    return out
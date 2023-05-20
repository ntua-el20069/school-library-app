from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from .helpRoutes import is_internal_request
from datetime import datetime, timedelta

# 4.1.3.Find young teachers (age < 40 years) who have borrowed the most books and the number of books.
def frequent_borrowing_new_teachers(db):
    cursor = db.cursor()
    sql = 'select username, age, number from frequent_borrowing_new_teacher'
    cursor.execute(sql)
    teachers = cursor.fetchall()
    out = '<h1>New teachers that have borrowed max number of books</h1>'
    for teacher in teachers:
        out += f'teacher: {teacher[0]} with age: {teacher[1]} and max number of books: {teacher[2]}<br>'
    return out

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

# 4.1.6.Many books cover more than one category. Among field pairs (e.g., history and poetry) that
# are common in books, find the top-3 pairs that appeared in borrowings.
def three_popular_topic_couples(db):
    cursor = db.cursor()
    sql = 'select topic_a, topic_b, frequency from three_popular_topic_couples'
    cursor.execute(sql)
    couples = cursor.fetchall()
    out = '<h1>Top 3 topic couples in borrowings</h1>'
    for couple in couples:
        out += f'{couple[0]} - {couple[1]},    Times: {couple[2]}<br>'
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
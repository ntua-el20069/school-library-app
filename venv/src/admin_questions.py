from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from .helpRoutes import is_internal_request
from datetime import datetime, timedelta


# 4.1.1.List with the total number of loans per school (Search criteria: year, calendar month, e.g.January)
def borrowings_per_school_year_month(db):
    out = ''
    cursor = db.cursor()
    if request.method == 'POST':
        year = request.form.get('year')
        month = request.form.get('month')
        
        # for year only
        # query if you want to get all including 0
        # e.g. for 2021
        # (select name, address, number from borrowings_per_school_year where year=2021) union (select name, address, 0  from School_Library WHERE address NOT IN  (select distinct(address) from borrowings_per_school_year where year=2021)); 
        if month=='':
            out1 = f'<h1>Borrowings in each school in year {year}</h1>'
            sql = f"select name, address, number from borrowings_per_school_year where year={year}"
            cursor.execute(sql)
            schools = cursor.fetchall()
            
            out2 = f'<h1>schools with 0 borrowings in year {year}</h1>'
            sql = f"""select name, address  from School_Library WHERE address NOT IN (
                      select distinct(address) from borrowings_per_school_year where year={year})"""
            cursor.execute(sql)
            not_borrowed_schools = cursor.fetchall()

        # for year and month
        else:
            out1 = f'<h1>Borrowings in each school in month {month} of year {year}</h1>'
            sql = f"select name, address, number from borrowings_per_school_year_month where year={year} and month={month}"
            cursor.execute(sql)
            schools = cursor.fetchall()
            
            out2 = f'<h1>schools with 0 borrowings in month {month} of year {year}</h1>'
            sql = f"""select name, address  from School_Library WHERE address NOT IN (
                      select distinct(address) from borrowings_per_school_year_month where year={year} and month={month})"""
            cursor.execute(sql)
            not_borrowed_schools = cursor.fetchall()
    else: # handle GET request
        # query if you want to get all including 0
        # select S.address, IFNULL(count(B.address),0) from School_Library S left join Borrowing B on S.address=B.address group by S.address;
        out1 = f'<h1>Borrowings in each school (in all years)</h1>'
        sql = "select name, B.address as address, count(*) as number from Borrowing B, School_Library S where B.address=S.address group by name, address order by number desc"
        cursor.execute(sql)
        schools = cursor.fetchall()

        out2 = f'<h1>schools with 0 borrowings in all years</h1>'
        sql = f"""select name, address  from School_Library WHERE address NOT IN (
                    select distinct(B.address) from Borrowing B, School_Library S where B.address=S.address)"""
        cursor.execute(sql)
        not_borrowed_schools = cursor.fetchall()

    for school in schools:
        name, address, number = school
        out1 += f'{name} &emsp; {address} Borrowings = {number}<br>' 
    for school in not_borrowed_schools:
        name, address = school
        out2 += f'{name} &emsp; {address} Borrowings = 0<br>' 
    out = out1 + out2
    return render_template('year-month-admin.html') + out


# 4.1.2.For a given book category (user-selected), which authors belong to it and which teachers
# have borrowed books from that category in the last year?
def topic_authors_teachers(db):
    out = ''
    if request.method == 'POST':
        topic = request.form.get('topic')
        cursor = db.cursor()
        # for teachers
        sql = f"select distinct(username) from topic_this_year_borrowing_teacher where topic='{topic}'"
        cursor.execute(sql)
        teachers = cursor.fetchall()
        out1 = f'<h1>teachers who have borrowed books from category {topic} in the last year</h1>'
        for teacher in teachers:
            out1 += f'{teacher[0]}<br>'
        # for authors
        sql = f"select distinct(name) from topic_author where topic='{topic}' "
        cursor.execute(sql)
        authors = cursor.fetchall()
        out2 = f'<h1>authors who have written books having category {topic} </h1>'
        for author in authors:
            out2 += f'{author[0]} <br>'
        out = out1 + out2
    return render_template('topic-admin.html') + out 

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

# 4.1.5.Which operators have loaned the same number of books in a year with more than 20 loans?
def libs_lend_books(db):
    out = ''
    if request.method == 'POST':
        year = request.form.get('year')
        cursor = db.cursor()
        # for teachers
        sql = f"select librarian, count(*) from Borrowing where start_date between '{year}-01-01' and '{year}-12-31' group by librarian having count(*)>20 order by count(*) desc"
        cursor.execute(sql)
        librarians = cursor.fetchall()
        out = f'<h1>operators who have loaned the same number of books in a year with more than 20 loans</h1>'
        for lib in librarians:
            out += f'{lib[0]} number of loans in selected year: {lib[1]}<br>'
        
    return render_template('libs-lend-admin.html') + out 

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
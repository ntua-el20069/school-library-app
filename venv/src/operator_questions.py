from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector 
import random
from .helpRoutes import is_internal_request
from datetime import datetime, timedelta

# 4.2.1. All books by Title, Author (Search criteria: title/ category/ author/ copies).
# Also there is a a part of simple user question
#              4.3.1.List with all books (Search criteria: title/category/author)
def books_in_library(db, address, simple_user = False, type='librarian', username=''):
    out = ''
    cursor = db.cursor()
    order = 'title'
    temp = 'books-simple-user.html' if simple_user else 'books-librarian.html'
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        topic = request.form.get('topic')
        if simple_user:
            available = ''
        else:
            available = request.form.get('available')
        #order = request.form.get('order')
        
        if title!='':
            out = f'<h1>Books in this school with title = {title}</h1>'
            sql = f"""select ISBN, title, publisher, pages, image, language, summary,
                        address, books_number
                          from book_available 
                          where title='{title}' and address='{address}'
                          order by {order}"""
        elif author!='':
            out = f'<h1>Books in this school with author = {author}</h1>'
            sql = f"""select ISBN, title, publisher, pages, image, language, summary,
                        address, books_number
                          from book_author_available 
                          where name='{author}' and address='{address}'
                          order by {order}"""
        elif topic!='':
            out = f'<h1>Books in this school with topic = {topic}</h1>'
            sql = f"""select ISBN, title, publisher, pages, image, language, summary,
                        address, books_number
                          from book_topic_available 
                          where topic ='{topic}' and address='{address}'
                          order by {order}"""
        elif available!='':
            out = f'<h1>Books in this school with available copies >= {available}</h1>'
            sql = f"""select ISBN, title, publisher, pages, image, language, summary,
                        address, books_number
                          from book_available 
                          where books_number >= {available} and address='{address}'
                          order by {order}"""
        else:
            return "Error: Nothing was submitted. Please input exactly one field"
        
       
    else:
        out = f'<h1>All Books in this school</h1>'
        sql = f"""select ISBN, title, publisher, pages, image, language, summary,
                        address, books_number
                          from book_available 
                          where address='{address}'
                          order by {order}"""
    try:
        cursor.execute(sql)
        books = cursor.fetchall()
        for book in books:
            ISBN, title, publisher, pages, image, language, summary, address, books_number = book
            # print authors too
            sql = f"select name from Author where ISBN='{ISBN}'"
            cursor.execute(sql)
            authors = ', '.join([c[0] for c in cursor.fetchall()])
            # print topics too
            sql = f"select topic from Topic where ISBN='{ISBN}'"
            cursor.execute(sql)
            topics = ', '.join([c[0] for c in cursor.fetchall()])
            # ...
            link_reserve = f'<a href="/simple-user/{type}/{username}/books-in-library/reserve-book/{ISBN}">Reserve book</a><br>' if simple_user else ''
            out += f'ISBN = {ISBN} title = {title}<br> Authors: {authors} <br> Topics: {topics} <br> <img src="{image}" width="200px"> {link_reserve} <br><br>'     
    except ValueError as err:
        print(err)
        return "Not found!"
    return render_template(temp) + out

# 4.2.2.Find all borrowers who own at least one book and have delayed its return. (Search criteria:
# First Name, Last Name, Delay Days).
def delayed_not_returned_search(db, address):
    out = ''
    cursor = db.cursor()
    if request.method == 'POST':
        first_name = request.form.get('first')
        last_name = request.form.get('last')
        days_delayed = request.form.get('delay')
        if last_name!='':
            out= f'<h1>Users that have Delayed and not returned books in this Library and have last name = {last_name} </h1>'
            sql= f'select distinct(username), first_name, last_name from delayed_not_returned_user_book where address="{address}" and last_name="{last_name}"'
        elif first_name!='':
            out= f'<h1>Users that have Delayed and not returned books in this Library and have first name = {first_name} </h1>'
            sql= f'select distinct(username), first_name, last_name  from delayed_not_returned_user_book where address="{address}" and first_name="{first_name}"'
        elif days_delayed!='':
            out= f'<h1>Users that have Delayed and not returned books in this Library with delay days >= {days_delayed} </h1>'
            sql= f'select distinct(username), first_name, last_name from delayed_not_returned_user_book where address="{address}" and DATEDIFF(CURDATE(), start_date) - 7 >= {days_delayed}'
        else:
            return "Error: Nothing was submitted. Please input exactly one field"
    else:
        out = f'<h1>Users that have Delayed and not returned books in this Library </h1>'
        sql = f'select distinct(username), first_name, last_name from delayed_not_returned_user_book where address="{address}"'
    cursor.execute(sql)
    users = cursor.fetchall()
    for user in users:
        username, first_name, last_name = user
        cursor.execute(f"select max(DATEDIFF(CURDATE(), start_date) - 7) from delayed_not_returned_user_book where username='{username}' and address='{address}'")
        max_delay = cursor.fetchall()[0][0]
        out += f'username= {username}, name = {first_name} {last_name}, days of delay (max among delayed books) = {max_delay} <br>'
    return render_template('delayed-search.html') + out

# 4.2.3.Average Ratings per borrower and category (Search criteria: user/category)
def avg_ratings(db, address):
    out = ''
    out1 = ''
    out2 = ''
    cursor = db.cursor()
    if request.method == 'POST':
        topic = request.form.get('topic')
        username = request.form.get('username')
        if username!='':
            cursor.execute(f"select * from User where username='{username}' and address='{address}'")
            if not cursor.fetchall():
                return "User is not in this school"
            out1 = f'<h1>Average rating for user: {username}</h1>'
            sql1 = f'select username, avg_likert from avg_borrower_rating where username="{username}"'
        elif topic!='':
            out2 = f'<h1>Average rating for topic: {topic} (counting reviews from all schools)</h1>'
            sql2 = f'select topic, avg_likert from avg_category_rating where topic="{topic}"'
        else:
            return "Please input exactly one of the fields"
    else:
        out1 = f'<h1>Average rating per user in this school</h1>'
        sql1 = f'select username, avg_likert from avg_borrower_rating where username in (select username from User where address="{address}")'
        out2 = f'<h1>Average topic rating (counting reviews from all schools)</h1>'
        sql2 = f'select topic, avg_likert from avg_category_rating'
    if out1:
        cursor.execute(sql1)
        ratings_per_user = cursor.fetchall()
        for rating in ratings_per_user:
            username, avg_likert = rating 
            out1 += f'username: {username}, average likert rating: {avg_likert} <br>'
    if out2:
        cursor.execute(sql2)
        ratings_per_topic = cursor.fetchall()
        for rating in ratings_per_topic:
            topic, avg_likert = rating 
            out2 += f'username: {topic}, average likert rating: {avg_likert} <br>'
    out = out2 + out1
    return render_template('ratings.html') + out
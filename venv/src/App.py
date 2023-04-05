from flask import Flask, render_template


app = Flask(__name__)

@app.route("/")
def home():
    return '<h1>Hello</h1>'

@app.route("/sample")
def sample():
    return render_template('sample-page.html')

# This is a simple routing example 
# If you want to make an html page, you should put it into directory 'templates'

@app.route("/signup")
def signup():
    return render_template('sign-up.html')

@app.route("/signin")
def signin():
    return render_template('sign-in.html')

if __name__ == '__main__':
    app.run(debug=True)
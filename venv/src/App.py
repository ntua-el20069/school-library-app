from flask import Flask, render_template, request, url_for, flash, redirect

# ...


app = Flask(__name__)

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/sample")
def sample():
    return render_template('sample-page.html')

# This is a simple routing example 
# If you want to make an html page, you should put it into directory 'templates'

#@app.route("/signup")
#def signup():
#    return render_template('sign-up.html')

@app.route("/signup", methods=['GET', 'POST'])
def signup_form_redirect():
    if request.method == 'POST':
        return redirect(url_for('notApprovedUser'))
    else:
        return render_template('sign-up.html')
    
#@app.route("/signin")
#def signin():
#        return render_template('sign-in.html')
    
@app.route("/signin", methods=['GET', 'POST'])
def handle_signin():
    if request.method == 'POST':
        username = request.form.get('username')
        if username == 'nikospapa':
            return redirect(url_for('student'))
        else:
            return redirect(url_for('notApprovedUser'))
    else:
        return render_template('sign-in.html')

@app.route("/not-approved-user")
def notApprovedUser():
    return render_template('not-approved-user.html')

@app.route("/student")
def student():
    return render_template('student.html')

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import connectToMySQL
import re
from flask_bcrypt import Bcrypt
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app = Flask(__name__)
app.secret_key = "IAmGroot!"
bcrypt = Bcrypt(app)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/register', methods=['POST'])
def register():
    error = False
    if len(request.form['first_name']) < 3:
        flash("First Name must be 3 or more chars")
        error = True
    if len(request.form['last_name']) < 3:
        flash("Last Name must be 3 or more chars")
        error = True
    if len(request.form['password']) < 8:
        flash("Password must be 8 or more chars")
        error = True
    if request.form['password'] != request.form['c_password']:
        flash("Passwords must match")
        error = True
    if not request.form['first_name'].isalpha():
        flash("No bots allowed")
        error = True
    if not request.form['last_name'].isalpha():
        flash("No bots allowed - last_name")
        error = True
    if not EMAIL_REGEX.match(request.form['email']):
        flash("No bot emails")
        error = True

    data = {
        "email" : request.form['email']
    }
    query = "SELECT * FROM users WHERE email = %(email)s"
    mysql = connectToMySQL('wall_demo')
    matching_email_users = mysql.query_db(query,data)
    if len(matching_email_users) > 0:
        flash("Identity theft is not a joke")
        error = True
    if error:
        return redirect('/')
    data = {
        "first_name" : request.form['first_name'],
        "last_name"  : request.form['last_name'],
        "email"      : request.form['email'],
        "password"   : bcrypt.generate_password_hash(request.form['password'])
    }
    query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password)s, NOW(), NOW());"
    mysql = connectToMySQL('wall_demo')
    user_id = mysql.query_db(query, data)
    session['user_id'] = user_id
    return redirect('/wall')

@app.route('/login', methods=['POST'])
def login():
    data = {
        "email" : request.form['email']
    }
    query = "SELECT * FROM users WHERE email = %(email)s"
    mysql = connectToMySQL('wall_demo')
    matching_email_users = mysql.query_db(query,data)
    if len(matching_email_users) == 0:
        flash("Invalid Credentials")
        print("bad email")
        return redirect('/')
    user = matching_email_users[0]
    if bcrypt.check_password_hash(user['password'], request.form['password']):
        session['user_id'] = user['id']
        return redirect('/wall')
    flash("Invalid Credentials")
    print("bad pw")
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/wall')
def wall():
    if not 'user_id' in session:
        flash("Get out of here")
        return redirect('/')
    # logged user first name
    mysql = connectToMySQL('wall_demo')
    data = {
        "user_id" : session['user_id']
    }
    query = "SELECT first_name FROM users WHERE id = %(user_id)s"
    the_user = mysql.query_db(query, data)
    
    # messages sent to logged user
    mysql = connectToMySQL('wall_demo')
    query = "SELECT messages.id, first_name, messages.created_at, message FROM messages JOIN users ON sender_id = users.id WHERE rec_id = %(user_id)s"
    my_messages = mysql.query_db(query, data)
    
    # message sent by logged user
    mysql = connectToMySQL('wall_demo')
    query = "SELECT * FROM messages WHERE sender_id = %(user_id)s"
    sent_messages = mysql.query_db(query, data)

    # all other users first, id 
    mysql = connectToMySQL('wall_demo')
    query = "SELECT id, first_name FROM users WHERE id != %(user_id)s"
    others = mysql.query_db(query, data)
    context = {
        "the_user" : the_user[0],
        "my_messages" : my_messages,
        "count_sent" : len(sent_messages),
        "others" : others
    }
    return render_template("wall.html", **context)

@app.route('/message/<int:rec_id>', methods=['POST'])
def add_message(rec_id):
    data = {
        "message" : request.form['message'],
        "sender_id" : session['user_id'],
        "receiver_id" : rec_id
    }
    query = "INSERT INTO messages (message, sender_id, rec_id, created_at, updated_at) VALUES (%(message)s, %(sender_id)s, %(receiver_id)s, NOW(), NOW());"
    mysql = connectToMySQL('wall_demo')
    mysql.query_db(query, data)
    return redirect('/wall')

@app.route('/delete/<int:msg_id>')
def del_msg(msg_id):
    data = {
        "msg_id" : msg_id
    }
    query = "DELETE FROM messages WHERE id = %(msg_id)s"
    mysql = connectToMySQL('wall_demo')
    mysql.query_db(query, data)
    return redirect('/wall')

if __name__ == "__main__":
    app.run(debug=True)

# flash categories
# template filter

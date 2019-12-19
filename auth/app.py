from datetime import datetime
import hashlib
from gevent.pywsgi import WSGIServer

from flask import Flask, request, session, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from jwcrypto import jwt, jwk
import json
import ast
from flask_mail import Mail, Message
from flask_cors import CORS

import string
import random
import re

app = Flask(__name__)
CORS(app)

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": '5genesismanagement@gmail.com',
    "MAIL_PASSWORD": 'TestAtos'
}

app.config.update(mail_settings)
mail = Mail(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
key = None


class User(db.Model):
    """ Create user table"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True)
    email = db.Column(db.String(60), unique=True)
    password = db.Column(db.String(100))
    active = db.Column(db.Boolean)
    deleted = db.Column(db.Boolean)

    def __init__(self, username, email, password):
        self.username = username
        self.password = password
        self.email = email
        self.active = False
        self.deleted = False


class Registry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), db.ForeignKey('user.username'), nullable=False)
    action = db.Column(db.String(40), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    def __init__(self, username, action):
        self.username = username
        self.action = action
        self.date = datetime.now()


def validate_token(token, path):
    try:
        if not token:
            return 'Login or set a Token access is required'

        metadata = ast.literal_eval(jwt.JWT(key=key, jwt=token).claims)

        now = datetime.now()
        if metadata.get('timeout') >= datetime.timestamp(now):
            data = User.query.filter_by(username=metadata.get('username'), password=metadata.get('password')).first()
        else:
            return 'Token expired'
        if data is not None:
            new_action = Registry(username=metadata.get('username'), action=str(path))
            db.session.add(new_action)
            db.session.commit()
            pass
        else:
            raise Exception()
    except:
        return 'No valid Token given'


def preValidation(request, functional_part):
    username = request.authorization.username
    password = hashlib.md5(request.authorization.password.encode()).hexdigest()

    data = User.query.filter_by(username=username, password=password).first()
    if data is not None and data.active:
        now = datetime.now()
        Etoken = jwt.JWT(header={'alg': 'A256KW', 'enc': 'A256CBC-HS512'},
                         claims={'username': username, 'password': password, 'timeout': datetime.timestamp(now) + 120})

        Etoken.make_encrypted_token(key)
        token = Etoken.serialize()
        return functional_part(token)

    elif data is None:
        return jsonify(result='No user registered/active with that user/password'), 400

    else:
        return jsonify(result='User ' + username + ' is not activated'), 400


@app.route('/get_token', methods=['GET'])
def get_token():
    """Login Form"""

    def logic(token):

        try:
            new_action = Registry(username=request.authorization.username, action='GetToken')
            db.session.add(new_action)
            db.session.commit()
            return jsonify(result=token), 200

        except Exception as e:
            return jsonify(result=('Login fails: ' + str(e))), 400

    return preValidation(request, logic)


@app.route('/login', methods=['GET'])
def login():
    """Login Form"""

    def logic(token):
        try:
            session['token'] = token
            new_action = Registry(username=request.authorization.username, action='LogIn')
            db.session.add(new_action)
            db.session.commit()
            return jsonify(result='Logged')

        except Exception as e:
            return jsonify(result=('Login fails: ' + str(e))), 400

    return preValidation(request, logic)


@app.route('/change_password', methods=['PUT'])
def change_password():
    """change_Password Form"""

    name = request.authorization.username
    passw = hashlib.md5(request.authorization.password.encode()).hexdigest()
    new_password = hashlib.md5(request.form['password'].encode()).hexdigest()
    try:
        data = User.query.filter_by(username=name, password=passw).first()
        if data is not None and data.active:
            data.password = new_password
            new_action = Registry(username=request.authorization.username, action='ChangePassword')
            db.session.add(new_action)
            db.session.commit()
            return jsonify(result='New password for ' + name)
        else:
            return jsonify(result='No user registered/active with that user/password'), 400
    except Exception as e:
        return jsonify(result=('Change password failed: ' + str(e))), 400


def admin_confirmation(username, email):
    now = datetime.now()
    Etoken = jwt.JWT(header={'alg': 'A256KW', 'enc': 'A256CBC-HS512'},
                     claims={'username': username, 'email': email, 'action': 'delete', 'time': datetime.timestamp(now)})
    Etoken.make_encrypted_token(key)
    token_not_provide = str(Etoken.serialize())

    Etoken = jwt.JWT(header={'alg': 'A256KW', 'enc': 'A256CBC-HS512'},
                     claims={'username': username, 'email': email, 'action': 'activated',
                             'time': datetime.timestamp(now)})
    Etoken.make_encrypted_token(key)
    token_provide = str(Etoken.serialize())

    msg = Message(subject='User validation',
                  sender=app.config.get('MAIL_USERNAME'),
                  recipients=[app.config.get('MAIL_USERNAME')],  # replace with your email for testing
                  html=render_template('validate_user.html',
                                       user=username, email=email, token_provide=token_provide,
                                       token_not_provide=token_not_provide))
    mail.send(msg)


@app.route('/register', methods=['POST'])
def register():
    """Register Form"""
    try:
        username = request.form['username']
        password = hashlib.md5(request.form['password'].encode()).hexdigest()
        email = request.form['email']

        if not check_mail(email):
            return jsonify(result='Registration failed: Not valid email'), 400

        data = User.query.filter_by(username=username).first()
        if data and data.deleted:
            data.password = hashlib.md5(password.encode()).hexdigest()
            data.email = email
            data.deleted = False
            new_action = Registry(username=username, action='Re-Register')

        else:
            new_user = User(username=username, password=password, email=email)
            new_action = Registry(username=username, action='Register')
            db.session.add(new_user)
        db.session.add(new_action)
        db.session.commit()
        admin_confirmation(username, email)
        return jsonify(result='User registered. Keep an eye with your email for knowing when your account is activated')

    except Exception as e:
        if str(type(e)).find('IntegrityError') > 0:
            e = 'User already exists'
        return jsonify(result=('Registration failed: ' + str(e))), 400


@app.route('/validate_request', methods=['GET'])
def test():
    token_valid = True
    if request.authorization:
        username = request.authorization.username
        password = hashlib.md5(request.authorization.password.encode()).hexdigest()

        data = User.query.filter_by(username=username, password=password).first()
        if data is not None and data.active:
            return jsonify(result='Success')
        else:
            return jsonify(result='User/Password not valid'), 401

    # Take token by parameter
    token = request.headers.environ.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
    if token != '' is not None:
        token_valid = validate_token(token, request.path)

    # Take tokeb by sesion
    elif session.get('token') or session.get('token') is False:
        token = session.get('token')
        token_valid = validate_token(token, request.path)
    else:
        token_valid = "No valid Token or Basic Auth"
    # Validate token, None in this function means no problem detected
    if token_valid is not None:
        return jsonify(result=token_valid), 401

    return jsonify(result='Success')


@app.route('/drop_db', methods=['DELETE'])
def drop_db():
    """Register Form"""
    try:
        # Get User & Password
        username = request.authorization.username
        password = request.authorization.password

        if username == 'Admin' and password == 'Admin':
            # Drop DB & create a new instance of DB
            db.drop_all()
            db.session.commit()
            db.create_all()
            return jsonify(result='User Database dropped')
    except Exception as e:
        return jsonify(result=('Drop DataBase failed: ' + str(e))), 400


@app.route('/delete_user', methods=['DELETE'])
def delete_one_user():
    try:
        # Get User & Password for Admin permissions
        username = request.authorization.username
        password = request.authorization.password
        # User to be eliminated
        user = request.form['username']
        if username == 'Admin' and password == 'Admin':
            # Drop DB & create a new instance of DB
            Registry.query.filter_by(username=user).delete()
            User.query.filter_by(username=user).delete()
            db.session.commit()
            return jsonify(result=user + ' user is removed')
    except Exception as e:
        return jsonify(result=('Remove user' + user + 'failed: ' + str(e))), 400


@app.route('/show_users', methods=['GET'])
def show_users():
    try:
        # Get User & Password for Admin permissions
        username = request.authorization.username
        password = request.authorization.password
        if username != 'Admin' or password != 'Admin':
            return jsonify(result='Invalid Permission'), 401

        user = request.args.get('username')
        verbose = request.args.get('verbose')
        active = request.args.get('active')
        deleted = request.args.get('deleted')

        return jsonify(result=(get_users(username=user, verbose=verbose, active=active, deleted=deleted)))
    except Exception as e:
        return jsonify(result=('Remove user' + user + 'failed: ' + str(e))), 400


def get_users(username=None, verbose=False, active=False, deleted=False):
    users_dict = {}
    query = User.query

    if username:
        query = query.filter_by(username=username)
    if active:
        query = query.filter_by(active=True)
    if deleted:
        query = query.filter_by(deleted=True)

    for item in query.all():
        users_dict[item.username] = {
            'email': item.email,
            'active': item.active,
            'deleted': item.deleted
        }
    if verbose:
        for key in users_dict.keys():
            traces_list = []
            for item in Registry.query.filter_by(username=key).all():
                traces_list.append({'action': item.action, 'date': str(item.date)})
            users_dict[key]['traces'] = traces_list

    return users_dict


@app.route("/logout")
def logout():
    # Logout Form
    session['token'] = False
    return jsonify(result="Logged out"), 200


def randomPassword(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def check_mail(email):
    # pass the regualar expression
    # and the string in search() method
    if (re.search('^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$', email)):
        return True

    else:
        return False


@app.route('/recover_password', methods=['PUT'])
def recover_password():
    """change_Password Form"""

    email = request.form['email']
    if not check_mail(email):
        return jsonify(result='Not valid email'), 400

    new_password = randomPassword()

    try:
        data = User.query.filter_by(email=email).first()
        if data is not None and data.active:
            with app.app_context():
                data.password = hashlib.md5(new_password.encode()).hexdigest()
                new_action = Registry(username=data.username, action='recoverPassword')
                db.session.add(new_action)
                db.session.commit()
                msg = Message(subject='Password changed',
                              sender=app.config.get('MAIL_USERNAME'),
                              recipients=[email],  # replace with your email for testing
                              html=render_template('recover.html',
                                                   user=data.username, password=new_password))
                mail.send(msg)
            return jsonify(result='New password for ' + email + ' Look your email for getting it.')
        else:
            return jsonify(result='No user registered/active with that user/password'), 400
    except Exception as e:
        return jsonify(result=('Change password failed: ' + str(e))), 400


@app.route('/validate_user/<token>', methods=['GET', 'POST'])
def validate_user(token):
    try:
        metadata = ast.literal_eval(jwt.JWT(key=key, jwt=token).claims)

        user = metadata['username']
        action = metadata['action']

        email = User.query.filter_by(username=user).first().email
        if action == 'delete':
            Registry.query.filter_by(username=user).delete()
            User.query.filter_by(username=user).delete()
        else:
            data = User.query.filter_by(username=user).first()
            data.active = True
            data.deleted = False
            new_action = Registry(username=data.username, action='Activated')
            db.session.add(new_action)

        db.session.commit()
        notify_user(email, action)
        return jsonify(result='Changes applied')

    except Exception as e:
        return jsonify(result=('Validation process interrupted: ' + str(e))), 400


def notify_user(email, action):
    if action == 'delete':
        subject = 'Your account has been not validated'
        body = 'Dear sir or madam,\n\n' \
               'The Administrator decided to revoke your account creation. ' \
               'If you need access to the service, you should contact with the Admin before creating a new account.' \
               '\n\nThank you for your understanding,'
    else:
        subject = 'Your account has been validated'
        body = 'Dear sir or madam,\n\n' \
               'The Administrator decided to validate your account. ' \
               'Now you can access with your username and password. ' \
               '\n\nThanks for your patience and welcome,'

    msg = Message(subject=subject,
                  sender=app.config.get('MAIL_USERNAME'),
                  recipients=[email],  # replace with your email for testing
                  body=body)
    mail.send(msg)


if __name__ == '__main__':
    app.debug = True
    db.create_all()
    json1_file = open('key.json')
    json1_str = json1_file.read()
    json1_data = json.loads(json1_str)
    key = jwk.JWK(**json1_data)

    app.secret_key = '123'
    http_server = WSGIServer(('', 2000), app)
    http_server.serve_forever()

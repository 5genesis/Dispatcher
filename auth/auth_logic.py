from flask import Blueprint, request, jsonify, render_template
import hashlib
from datetime import datetime
import ast
from flask_mail import Message
from jwcrypto import jwt, jwk
import logging
import json
from Auth import app
from auth_utils import session, admin_auth, validate_token, preValidation, check_mail, randomPassword
from DB_Model import init_db, User, Registry, db
from MailConfig import mail

auth_logic = Blueprint('auth_page', __name__, template_folder='templates')


json1_file = open('key.json')
json1_str = json1_file.read()
json1_data = json.loads(json1_str)
key = jwk.JWK(**json1_data)
logger = logging.getLogger('REST API')


@auth_logic.route('/get_token', methods=['GET'])
def get_token():
    """Login Form"""
    logger.info(str(request))

    def logic(token):

        try:
            new_action = Registry(username=request.authorization.username, action='GetToken')
            db.session.add(new_action)
            db.session.commit()
            return jsonify(result=token), 200

        except Exception as e:
            return jsonify(result=('Login fails: ' + str(e))), 400

    return preValidation(request, logic)


@auth_logic.route('/login', methods=['GET'])
def login():
    """Login Form"""
    logger.info(str(request))

    def logic(token):
        try:
            session['token'] = token
            new_action = Registry(username=request.authorization.username, action='LogIn')
            db.session.add(new_action)
            db.session.commit()
            return jsonify(result='Logged')

        except Exception as e:
            return jsonify(result=('Login fails: ' + str(e))), 401

    return preValidation(request, logic)


@auth_logic.route('/validate_request', methods=['GET'])
def validate_request():
    logger.info(str(request))
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
        token_valid = validate_token(token, request)

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


@auth_logic.route('/change_password', methods=['PUT'])
def change_password():
    """change_Password Form"""
    logger.info(str(request))
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


@auth_logic.route('/register', methods=['POST'])
def register():
    """Register Form"""
    logger.info(str(request))
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


@auth_logic.route('/drop_db', methods=['DELETE'])
@admin_auth
def drop_db():
    """Register Form"""
    logger.info(str(request))
    try:
        # Drop DB & create a new instance of DB
        db.drop_all()
        db.session.commit()
        db.create_all()
        init_db()
        return jsonify(result='User Database dropped')
    except Exception as e:
        return jsonify(result=('Drop DataBase failed: ' + str(e))), 400


@auth_logic.route('/delete_user/<user>', methods=['DELETE'])
@admin_auth
def delete_one_user(user):
    logger.info(str(request))
    try:
        # Drop DB & create a new instance of DB
        Registry.query.filter_by(username=user).delete()
        User.query.filter_by(username=user).delete()
        db.session.commit()
        return jsonify(result=user + ' user is removed')
    except Exception as e:
        return jsonify(result=('Remove user' + user + 'failed: ' + str(e))), 400


@auth_logic.route('/show_users', methods=['GET'])
@admin_auth
def show_users():
    logger.info(str(request))
    user = request.args.get('username')
    verbose = request.args.get('verbose')

    try:
        if verbose == 'false' or verbose is False:
            verbose = None
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
        for aux_key in users_dict.keys():
            traces_list = []
            for item in Registry.query.filter_by(username=aux_key).all():
                if item.data:
                    traces_list.append({'action': item.action, 'data_provided': str(item.data), 'date': str(item.date)})
                else:
                    traces_list.append({'action': item.action, 'date': str(item.date)})
            users_dict[aux_key]['traces'] = traces_list

    return users_dict


@auth_logic.route("/logout")
def logout():
    # Logout Form
    logger.info(str(request))
    session['token'] = False
    return jsonify(result="Logged out"), 200


@auth_logic.route('/recover_password', methods=['PUT'])
def recover_password():
    """change_Password Form"""
    logger.info(str(request))
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


@auth_logic.route('/validate_user/<data>', methods=['GET'])
def validate_user(data):
    logger.info(str(request))
    try:

        metadata = ast.literal_eval(jwt.JWT(key=key, jwt=data).claims)
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


@auth_logic.route('/validate_user/<data>', methods=['PUT'])
@admin_auth
def validate_user_manually(data):
    logger.info(str(request))
    try:
        admin_auth(validate_user)
        user = data
        action = "create"
        email = User.query.filter_by(username=user).first().email

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

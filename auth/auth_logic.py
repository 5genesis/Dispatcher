from flask import Blueprint, request, jsonify, render_template
import hashlib
from datetime import datetime
import ast
from flask_mail import Message
from jwcrypto import jwt, jwk
import logging
import json
from auth import app
from auth_utils import session, admin_auth, validate_token, preValidation, check_mail, randomPassword, \
    string_to_boolean, get_user_from_token, get_platform_name, get_platform_id
from DB_Model import init_db, drop_users_db, User, Registry, Platform, db
from MailConfig import mail
import requests
from settings import Settings
import pymongo

auth_logic = Blueprint('auth_page', __name__, template_folder='templates')

json1_file = open('key.json')
json1_str = json1_file.read()
json1_data = json.loads(json1_str)
key = jwk.JWK(**json1_data)
logger = logging.getLogger('REST API')

# DB parameters
mongoDBClient = pymongo.MongoClient("mongodb://database:27017/")


@auth_logic.route('/get_token', methods=['GET'])
def get_token():
    """Get Token Form"""
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


@auth_logic.route('/get_user_from_token', methods=['GET'])
def get_user():
    logger.info(str(request))
    if request.headers.environ.get('HTTP_AUTHORIZATION', ''):
        token = request.headers.environ.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
    else:
        token = ''
    result, code = get_user_from_token(token)
    return jsonify(result=result), code


@auth_logic.route('/validate_request', methods=['GET'])
def validate_request():
    logger.info(str(request))
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


@auth_logic.route('/delete_account', methods=['DELETE'])
def delete_account():
    """change_Password Form"""
    logger.info(str(request))
    try:
        data = None
        if request.authorization:
            name = request.authorization.username
            passw = hashlib.md5(request.authorization.password.encode()).hexdigest()
            data = User.query.filter_by(username=name, password=passw).first()
        if data is not None and data.active and not data.deleted and data.username != 'Admin':
            data.active = False
            data.deleted = True
            new_action = Registry(username=request.authorization.username, action='account_deleted')
            db.session.add(new_action)
            db.session.commit()
            return jsonify(result=name + ' deleted')
        else:
            return jsonify(result='No user registered/active with that user/password'), 400
    except Exception as e:
        return jsonify(result=('Delete account failed: ' + str(e))), 400


@auth_logic.route('/change_password', methods=['PUT'])
def change_password():
    """change_Password Form"""
    logger.info(str(request))
    try:
        data = None
        if request.authorization:
            name = request.authorization.username
            passw = hashlib.md5(request.authorization.password.encode()).hexdigest()
            new_password = hashlib.md5(request.form['password'].encode()).hexdigest()
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
        admin_confirmation(email, username)
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
        drop_users_db()
        return jsonify(result='User Database dropped')
    except Exception as e:
        return jsonify(result=('Drop DataBase failed: ' + str(e))), 400


@auth_logic.route('/delete_user/<user>', methods=['DELETE'])
@admin_auth
def delete_one_user(user):
    logger.info(str(request))
    try:
        data = User.query.filter_by(username=user).first()
        if not data and user != 'Admin':
            return jsonify(result=user + ' user does not exist'), 404

        # Delete User
        Registry.query.filter_by(username=user).delete()
        User.query.filter_by(username=user).delete()
        db.session.commit()
        return jsonify(result=user + ' user is removed')
    except Exception as e:
        return jsonify(result=('Remove user' + user + 'failed: ' + str(e))), 400


@auth_logic.route('/delete_platform/<platformName>', methods=['DELETE'])
@admin_auth
def delete_platform(platformName):
    logger.info(str(request))
    try:
        mongodb = mongoDBClient["PlatformsDB"]
        platforms = mongodb["platforms"]

        data = Platform.query.filter_by(platformName=platformName).first()
        if not data:
            return jsonify(result=platformName + ' platform does not exist'), 404

        # Delete User

        Platform.query.filter_by(platformName=platformName).delete()
        db.session.commit()
        platforms.delete_one({"platform": platformName})
        return jsonify(result=platformName + ' platform is removed')
    except Exception as e:
        return jsonify(result=('Remove platform' + platformName + 'failed: ' + str(e))), 400


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
        return jsonify(result=('Show users failed: ' + str(e))), 400


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


def get_platforms(active=False):
    users_dict = {}
    query = Platform.query
    query = query.filter_by(active=active)

    for item in query.all():
        users_dict[item.platformName] = {
            'platform_id': item.platform_id,
            'ip': item.ip,
            'active': item.active
        }
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
        logger.info("The user {}, with mail {} is going to be validated".format(str(data), email))
        data = User.query.filter_by(username=user).first()
        data.active = True
        data.deleted = False
        new_action = Registry(username=data.username, action='Activated')
        db.session.add(new_action)
        db.session.commit()
        logger.info("The user {}, with mail {} is validated".format(str(data), email))
        notify_user(email, action)
        logger.info("A notification email is send to {}".format(email))
        return jsonify(result='Changes applied')

    except Exception as e:
        return jsonify(result=('Validation process interrupted: ' + str(e))), 400


@auth_logic.route('/register_platform/<platform_name>', methods=['POST'])
def register_platform(platform_name):
    logger.info(str(request))
    try:
        token = request.headers.environ.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if token != '' is not None:
            metadata = ast.literal_eval(jwt.JWT(key=key, jwt=token).claims)

            now = datetime.now()
            if metadata.get('timeout') < datetime.timestamp(now):
                return jsonify(result='Token expired'), 401

        ip = request.remote_addr
        if ip.find(':') != -1:
            ip = ip.split(':')[-1]

        data = Platform.query.filter_by(platformName=platform_name).first()
        if not data:
            data = Platform(platform_id=metadata.get('platform_id'), platformName=platform_name, ip=ip)
            db.session.add(data)
            db.session.commit()

        else:
            raise Exception('Platform already exists')

        admin_confirmation(platformName=platform_name, ip=ip)

        return jsonify(result='Platform registered. Keep an eye with your email for knowing when the platform allows '
                              'your platform')

    except Exception as e:
        if str(type(e)).find('IntegrityError') > 0:
            e = 'User already exists'
        return jsonify(result=('Platform registration failed: ' + str(e))), 400


@admin_auth
@auth_logic.route('/register_platform_in_platform', methods=['POST'])
def register_platform_in_platform():
    logger.info(str(request))
    # TODO set platform_name
    platform_name = get_platform_name()
    platform_id = get_platform_id()
    try:
        url = request.form['ip']

        if url.find('https') == -1:
            url = 'https://' + url
        now = datetime.now()
        Etoken = jwt.JWT(header={'alg': 'A256KW', 'enc': 'A256CBC-HS512'},
                         claims={'platform': platform_name, 'platform_id': platform_id,
                                 'timeout': datetime.timestamp(now) + 20})

        Etoken.make_encrypted_token(key)
        token = Etoken.serialize()
        header = {'Authorization': 'Bearer ' + str(token)}
        url = url + Settings.RequestPrefix + '/register_platform/' + platform_name

        req = requests.post(url, headers=header, verify=False)
        if req.status_code != 200:
            raise Exception(req.text)
        return jsonify(result='Platform registration Sucessfull'), 200
    except Exception as e:
        return jsonify(result=('Platform registration failed: ' + str(e))), 400


@auth_logic.route('/validate_platform/<data>', methods=['GET'])
def validate_platform(data):
    logger.info(str(request))
    try:
        mongodb = mongoDBClient["PlatformsDB"]
        platforms = mongodb["platforms"]

        metadata = ast.literal_eval(jwt.JWT(key=key, jwt=data).claims)
        platformName = metadata['platformName']
        action = metadata['action']

        if action == 'delete':

            Platform.query.filter_by(platformName=platformName).delete()
            db.session.commit()
        else:
            data = Platform.query.filter_by(platformName=platformName).first()
            data.active = True
            db.session.commit()

            Etoken = jwt.JWT(header={'alg': 'A256KW', 'enc': 'A256CBC-HS512'},
                             claims={'platform': platformName, 'platform_id': data.platform_id,
                                     'timeout': datetime(2025, 1, 1).timestamp()})

            Etoken.make_encrypted_token(key)
            token = str(Etoken.serialize())

            platforms.insert_one({'platform': platformName, 'token': token, 'ip': data.ip})

        return jsonify(result='Changes applied')

    except Exception as e:
        return jsonify(result=('Validation process interrupted: ' + str(e))), 400


@auth_logic.route('/show_platforms', methods=['GET'])
@admin_auth
def show_platforms():
    logger.info(str(request))
    try:

        active = string_to_boolean(request.args.get('activated', 't'))
        return jsonify(result=(get_platforms(active=active)))
    except Exception as e:
        return jsonify(result=('Show platforms failed: ' + str(e))), 400


@auth_logic.route('/validate_platform/<data>', methods=['PUT'])
@admin_auth
def validate_platform_manually(data):
    logger.info(str(request))
    try:
        admin_auth(validate_platform)
        platformName = data
        mongodb = mongoDBClient["PlatformsDB"]
        platforms = mongodb["platforms"]
        data = Platform.query.filter_by(platformName=platformName).first()
        data.active = True
        db.session.commit()
        Etoken = jwt.JWT(header={'alg': 'A256KW', 'enc': 'A256CBC-HS512'},
                         claims={'platform': platformName, 'platform_id': data.platform_id,
                                 'timeout': datetime(2025, 1, 1).timestamp()})
        Etoken.make_encrypted_token(key)
        token = str(Etoken.serialize())

        platforms.insert_one({'platform': platformName, 'token': token, 'ip': data.ip})
        return jsonify(result='Changes applied')

    except Exception as e:
        return jsonify(result=('Validation process interrupted: ' + str(e))), 400


def admin_confirmation(email=None, username=None, platformName=None, ip=None):
    now = datetime.now()
    header_token = {'alg': 'A256KW', 'enc': 'A256CBC-HS512'}
    if username:
        claims_not_provide = {'username': username, 'email': email, 'action': 'delete', 'time': datetime.timestamp(now)}
        claims_provide = {'username': username, 'email': email, 'action': 'activated',
                          'time': datetime.timestamp(now)}
    else:

        claims_not_provide = {'platformName': platformName, 'action': 'delete', 'time': datetime.timestamp(now)}
        claims_provide = {'platformName': platformName, 'action': 'activated', 'time': datetime.timestamp(now)}

    Etoken = jwt.JWT(header=header_token,
                     claims=claims_not_provide)
    Etoken.make_encrypted_token(key)
    token_not_provide = str(Etoken.serialize())

    Etoken = jwt.JWT(header=header_token,
                     claims=claims_provide)
    Etoken.make_encrypted_token(key)
    token_provide = str(Etoken.serialize())

    if username:
        subject = 'User validation'
        template = render_template('validate_user.html', user=username, email=email, token_provide=token_provide,
                                   token_not_provide=token_not_provide)
    else:
        subject = 'Platform validation'
        template = render_template('validate_platform.html', current_platform=get_platform_name(),
                                   platform=platformName, ip=ip, token_provide=token_provide,
                                   token_not_provide=token_not_provide)

    msg = Message(subject=subject,
                  sender=app.config.get('MAIL_USERNAME'),
                  recipients=[app.config.get('MAIL_USERNAME')],  # replace with your email for testing
                  html=template)
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

import string
import random
import re
from flask import request
import hashlib
from jwcrypto import jwt
from functools import wraps
import ast
from DB_Model import User, Registry, Rol, db
from flask import session, jsonify
from datetime import datetime
from settings import Settings

key = Settings().KEY

get_platform_name = lambda: open("platform_name", "r").read().split()[0]
get_platform_id = lambda: open("platformID", "r").read().split()[0]


def preValidation(request, functional_part):
    if request.authorization:
        username = request.authorization.username
        password = hashlib.md5(request.authorization.password.encode()).hexdigest()

        data = User.query.filter_by(username=username, password=password).first()
    else:
        data = None
    if data is not None and data.active:
        now = datetime.now()
        Etoken = jwt.JWT(header={'alg': 'A256KW', 'enc': 'A256CBC-HS512'},
                         claims={'username': username, 'password': password,
                                 'timeout': datetime.timestamp(now) + Settings.Timeout})

        Etoken.make_encrypted_token(key)
        token = Etoken.serialize()
        return functional_part(token)

    elif data is None:
        return jsonify(result='No user registered/active with that user/password'), 400

    else:
        return jsonify(result='User ' + username + ' is not activated'), 400


def auth(f):
    @wraps(f)
    def auth_validator(*args, **kwargs):
        auth = token_auth_validator(request)
        if not auth[0]:
            return auth[-1]
        return f(*args, **kwargs)

    return auth_validator


def admin_auth(f):
    @wraps(f)
    def auth_validator(*args, **kwargs):
        if request.authorization:
            username = request.authorization.username
            password = request.authorization.password
            data_user = User.query.filter_by(username=username,
                                             password=hashlib.md5(password.encode()).hexdigest()).first()
            data_rol = Rol.query.filter_by(username=username, rol_name='Admin').first()
            if not (data_user and data_rol):
                return jsonify(result='Invalid Permission'), 401
            return f(*args, **kwargs)
        else:
            return jsonify(result='Invalid Permission'), 401

    return auth_validator


def token_auth_validator(request=None):
    result = (True, None)
    if session.get('token') or session.get('token') is False:
        token = session.get('token')
        token_valid = validate_token(token, request)

        # Validate token, None in this function means no problem detected
    if token_valid is not None:
        result = (False, (jsonify(result=token_valid), 400))

    return result


def get_user_from_token(token):
    try:
        if not token:
            return 'Token access is required', 400

        return ast.literal_eval(jwt.JWT(key=key, jwt=token).claims).get('username'), 200

    except:
        return 'No valid Token given', 400


def validate_token(token, request):
    try:
        if not token:
            return 'Login or set a Token access is required'

        metadata = ast.literal_eval(jwt.JWT(key=key, jwt=token).claims)

        now = datetime.now()
        if metadata.get('timeout') >= datetime.timestamp(now):
            if metadata.get('username'):
                data = User.query.filter_by(username=metadata.get('username'), password=metadata.get('password')).first()
            else:
                if metadata.get('platform_id') == get_platform_id():
                    return
        else:
            return 'Token expired'
        if data is not None:

            if not isinstance(request, str) and request.data:
                new_action = Registry(username=metadata.get('username'),
                                      action=str(request.method + ' ' + request.path),
                                      data=str(request.get_json()))
            else:
                new_action = Registry(username=metadata.get('username'),
                                      action=str(request.method + ' ' + request.path))
            db.session.add(new_action)
            db.session.commit()
            pass
        else:
            raise Exception()
    except:
        return 'No valid Token given'


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


def string_to_boolean(string):
    if string.lower() in ['true', '1', 't', 'y', 'yes']:
        return True
    return False

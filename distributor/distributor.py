import ast
from flask import Flask, jsonify, request, Response
import json
import requests
from pymongo import MongoClient
import logging
from flask_cors import CORS
import fastjsonschema
from gevent.pywsgi import WSGIServer
import os

app = Flask(__name__)
CORS(app)

# Logging Parameters
logger = logging.getLogger("-Distributor-")
fh = logging.FileHandler('distributor.log')

stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
stream_formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
fh.setFormatter(formatter)
stream_handler.setFormatter(stream_formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.addHandler(stream_handler)

dbclient = MongoClient("mongodb://database:27017/")
app = Flask(__name__)



def authorization_requests(path):
    path_split = path.split('/')
    executionId = None
    db = dbclient["experimentsdb"]
    experiments = db["experiments"]

    if path_split[0] == 'execution':
        logger.info("User is going being checked")
        if path_split[-1] in ('cancel', 'delete', 'json', 'logs', 'results', 'descriptor'):
            executionId = path_split[-2]
        elif path_split[-1] != 'nextExecutionId':
            executionId = path_split[-1]

        if executionId:
            user = get_user()
            if user =='Admin':
                return
            logger.info("{} is going to be checked".format(user))
            if len(list(experiments.find({'executionId': executionId, 'user': user}))) == 0:
                error = 'Not enough permissions: user {} has not launch the executionID {}'.format(user, executionId)
                logger.error(error)
                raise Exception(error)


def get_user():
    token = request.headers.environ.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
    if not token:
        raise Exception("Not valid token, the user does not exist in the system")

    result = ast.literal_eval(
        requests.get('http://auth:2000/get_user_from_token', headers={'Authorization': str(token)}).text)['result']
    return result


@app.route('/<path:path>', methods=['GET', 'POST', 'DELETE'])
def proxy(path):
    logger.info(str(request))
    try:
        authorization_requests(path)

        if request.method == 'GET':
            resp = requests.get(f'{SITE_NAME}{path}')
        elif request.method == 'POST':
            resp = onboard_ed(SITE_NAME, path)
        elif request.method == 'DELETE':
            resp = requests.delete(f'{SITE_NAME}{path}')

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
    except Exception as exc:
        exc = str(exc)
        code = 400
        if 'user' in exc:
            code = 401
        response = (jsonify({'result': exc}), code)
    return response


def onboard_ed(site, path):
    try:
        logger.info("Onboarding Experiment descriptor")
        content = request.get_data()
        data = json.loads(content)
        logger.debug("Experiment descriptor: {}".format(data))

        # Validation process
        validate(data)
        # Check artifacts dependencies (nss, vnfs, images)
        for ns in data['NSs']:
            check_dependencies(ns[0], ns[1])

        logger.debug('Experiment validated')
        payload = {'ns': data['NS']}
        headers = {'User-Agent': 'Mozilla/5.0'}
        session = requests.Session()
        r = session.post('http://mano:5101/onboard', headers=headers, data=payload)
        if r.status_code > 300:
            if r.text.find('exists') < 0:
                raise Exception(r.text)
        r = requests.post(f'{site}{path}', json=request.get_json(), headers=headers)

        executionId = ast.literal_eval(r.text)['ExecutionId']
        experiments = dbclient["experimentsdb"]["experiments"]
        user = get_user()
        experiments.insert_one({'executionId': executionId, 'user': user})

    except fastjsonschema.JsonSchemaDefinitionException as ve:
        logger.warning("Problem while validating Experiment descriptor: {}".format(ve.message))
        return jsonify({"detail": ve.message, "code": "BAD_REQUEST", "status": 400}), 400
    except fastjsonschema.JsonSchemaException as ve:
        logger.warning("Problem while validating Experiment descriptor: {}".format(ve.message))
        return jsonify({"detail": ve.message, "code": "BAD_REQUEST", "status": 400}), 400
    except Exception as e:
        logger.warning("Problem while onboarding Experiment descriptor: {}".format(str(e)))
        return jsonify({"detail": str(e), "code": "BAD_REQUEST", "status": 400}), 400
    # TODO: include in the response data returned on the POST to the ELCM
    return r


@app.route('/validate/ed', methods=['POST'])
def validate_ed():
    try:
        logger.info("Validating Experiment descriptor")
        content = request.get_data()
        data = json.loads(content)
        logger.debug("Experiment descriptor: {}".format(data))
        # Validation process
        validate(data)
        # Check artifacts dependencies (nss, vnfs, images)
        for ns in data['NSs']:
            check_dependencies(ns[0], ns[1])

    except fastjsonschema.JsonSchemaDefinitionException as ve:
        logger.warning("Problem while validating Experiment descriptor: {}".format(ve.message))
        return jsonify({"detail": ve.message, "code": "BAD_REQUEST", "status": 400}), 400
    except fastjsonschema.JsonSchemaException as ve:
        logger.warning("Problem while validating Experiment descriptor: {}".format(ve.message))
        return jsonify({"detail": ve.message, "code": "BAD_REQUEST", "status": 400}), 400
    except Exception as e:
        logger.warning("Problem while validating Experiment descriptor: {}".format(str(e)))
    return jsonify({"detail": "Successful validation", "code": "OK", "status": 200}), 200


def check_dependencies(ns, vim):
    images = []
    dependencies = dbclient['dependencies']
    ns = dependencies['ns'].find_one({'id':ns})
    for vnf in ns['vnfs']:
        vdu_images = dependencies['vnf'].find_one({'id': vnf})['images']
        images.extend(vdu_images)
    for image in images:
        if not dbclient['images'][vim].find_one({'name': image}):
            raise Exception('Image {} not available in VIM {}'.format(image, vim))


if __name__ == '__main__':
    with open('schemas/experiment_schema.json', 'r') as f:
        ed_schema_data = f.read()
    SITE_NAME = os.environ['ELCM']
    ed_schema = json.loads(ed_schema_data)
    validate = fastjsonschema.compile(ed_schema)
    http_server = WSGIServer(('', 5100), app)
    http_server.serve_forever()

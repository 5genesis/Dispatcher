import hashlib
import sys
import time
import ast
from flask import Flask, jsonify, request
from flask_restful import Resource, Api
import json
import yaml
import requests
from pymongo import MongoClient
from datetime import datetime
import os
from gevent.pywsgi import WSGIServer
import logging

from flask_cors import CORS
from uuid import uuid4
from validator import validate_zip
import pymongo
app = Flask(__name__)
api = Api(app)
CORS(app)

# Logging Parameters
logger = logging.getLogger("-MANO API-")




dbclient = pymongo.MongoClient("mongodb://database:27017/")

@app.route('/set_config', methods=['POST'])
def set_config():
        """
        First Phase of PreOnboarding
        Input: form body with mandatory labels name, description and optional private
        Output: id of the preonboard session
        """
        try:
            id = str(uuid4())
            token = request.headers.environ.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
            form = request.form
            name = form.get('name')
            description = form.get('description')
            private = form.get('private')
            if not (name and description):
                raise Exception('name and description are mandatory labels')
            is_dir = os.path.isdir('/tmp/onboarding')
            if not is_dir:
                os.mkdir('/tmp/onboarding')

            target = "/tmp/onboarding/{}".format(id)
            os.mkdir(target)

            data = {'name': name, 'description': description}
            if private:
                private = True
            else:
                private = False
            data['private'] = private
            data['user'] = ast.literal_eval(
                requests.get('http://auth:2000/get_user_from_token', headers={'Authorization': str(token)}).text)[
                'result']

            data['timestamp'] = datetime.timestamp(datetime.now())
            with open(target + '/data.json', 'w') as outfile:
                json.dump(data, outfile)

            logger.info("PreOnboarding of id {} is initialized".format(id))
            return jsonify({'id': id}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

@app.route('/vnfd/<id>', methods=['POST'])
def vnfds(id):
    """
    Second Phase of PreOnboarding
    Input: VNFs
    Output: 200 code
    """
    try:
        global_code = 200
        with open('schemas/vnfd_schema.json', 'r') as f:
            vnfd_schema_data = f.read()
        vnfd_schema = json.loads(vnfd_schema_data)
        target = "/tmp/onboarding/{}/vnfds".format(id)
        if not os.path.isdir(target):
            os.mkdir(target)
        for upload in request.files.getlist("file"):
            filename = upload.filename.rsplit("/")[0]
            # Write package file to static directory and validate it
            logger.debug("Saving temporary VNFD")
            upload.save(target + '/' + filename)
            res, code = validate_zip(target + '/' + filename, vnfd_schema)
            if code != 200:
                os.remove(target + '/' + filename)
                global_code = 400

        files = []
        # r=root, d=directories, f = files
        for r, d, f in os.walk(target):
            for file in f:
                files.append(os.path.join(r, file))

        if global_code is not 200:
            # Valid descriptor: proceed with the onboarding
            raise Exception('Only ' + str(files) + ' are valid files. Please upload the rest of valid VNFDS"')
        return jsonify({'loaded VNFDs': files}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/nsd/<id>', methods=['POST'])
def preonboard_nsd(id):
    try:
        with open('schemas/nsd_schema.json', 'r') as f:
            nsd_schema = json.load(f)

        logger.info("Onbarding NSD")
        target = "/tmp/onboarding/{}/nsd".format(id)
        if not os.path.isdir(target):
            os.mkdir(target)
        file = request.files.get("file")
        # Write package file to static directory and validate it

        filename = file.filename.rsplit("/")[0]
        # Write package file to static directory and validate it
        logger.debug("Saving temporary NSD")
        file.save(target + '/' + filename)
        res, code = validate_zip(target + '/' + filename, nsd_schema)

        if code is not 200:
            # Valid descriptor: proceed with the onboarding
            os.remove(target + '/' + filename)

        # Delete package file when done with validation
        return jsonify({'loaded NSD': filename}), code
    except AttributeError as ae:
        logger.error("Problem while getting the nsd file: {}".format(str(ae)))
        return jsonify({"detail": str(ae), "code": "PRECONDITION_FAILED", "status": 412}), 412
    except NameError as ne:
        logger.error("Problem with the ENV vars: {}".format(str(ne)))
        return jsonify({"detail": str(ne), "code": "INTERNAL_SERVER_ERROR", "status": 500}), 500
    except Exception as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        logger.warning("Problem while onboarding NSD: {}".format(str(e)))
        return jsonify({"detail": message, "code": "BAD_REQUEST", "status": 400}), 400


@app.route('/vim/<id>', methods=['POST'])
def preonboard_vim_image(id):

    try:
        start_time = time.time()
        logger.info("Uploading image")

        # Save file to static directory and validate it
        target = "/tmp/onboarding/{}/vim".format(id)
        if not os.path.isdir(target):
            os.mkdir(target)
        checksum = hashlib.md5(request.files['file'].read(2**5)).hexdigest()
        print("--- %s seconds ---" % (time.time() - start_time))
        file = request.files.get("file")
        #TODO: Validate que no se haya subido antes la imagen, comprobarlo con el mongoDB

        filename = file.filename.rsplit("/")[0]
        # Write package file to static directory and validate it
        logger.debug("Saving temporary VIM")
        file.save(target + '/' + filename)
        filename, file_extension = os.path.splitext(target + '/' + filename)
        with open('/tmp/onboarding/{}/vim/data.json'.format(id), 'w+') as f:
            data={}
            data['vim_name'] = request.args.get('vim_name')
            data['file_extension'] = file_extension
            data['container_format'] = request.args.get('container_format')
            data['checksum'] = checksum
            # <--- add `id` value.
            json.dump(data, f, indent=4)
            f.truncate()
        print("--- %s seconds ---" % (time.time() - start_time))
    except AttributeError as ve:
        logger.error("Problem while getting the image file: {}".format(str(ve)))
        return jsonify({"detail": str(ve), "code": "UNPROCESSABLE_ENTITY", "status": 422}), 422
    except Exception as e:
        return jsonify({"detail": str(e), "code": type(e).__name__, "status": 400}), 400
    return jsonify({"status": "updated"}), 201


@app.route('/onboard/<id>', methods=['POST'])
def onboard(id):
    #TODO: Subir la imagen, las vnf, la nsd, actualizar info en mongoDB
    db = dbclient["onboarddb"]
    experiments = db["experiments"]
    pass


"""
def vim_onboard(id):

    path = "/tmp/onboarding/{}/vim".format(id)
    with open(path + '/data.json') as data:
        data = json.load(data)
        vim_name = data["vim_name"]
        file_extension = data["file_extension"]
        container_format = data["container_format"]
        checksum = data["checksum"]
    logger.info(
        "Adding VIM- Type: {}, Auth URL:{}, User:{}, Project:{}".format(vim["TYPE"], vim["AUTH_URL"], vim["USER"],
                                                                        vim["PROJECT"]))

    if vim["TYPE"] == "openstack":
        vim_conn = osUtils.connection(auth_url=vim["AUTH_URL"], region="RegionOne", project_name=vim["PROJECT"],
                                      username=vim["USER"], password=vim["PASSWORD"])
    else:
        raise KeyError("VIM type {} not supported".format(vim["TYPE"]))
    try:
        logger.info("Uploading image")

        # get image parameters
        if os.path.isfile(path + '/*' + file_extension):
            with open(path + '/*' + file_extension, 'rb') as file:
                r = osUtils.upload_image(vim_conn, file, file_extension, container_format)
                db = dbclient["onboarddb"]
                vims = db["vim"]
                vims.insert_one(data)

    except KeyError as ke:
        logger.error("VIM type {} not supported".format(vim["TYPE"]))
        return {"detail": str(ve), "code": "NOT_ACCEPTABLE", "status": 406}, 406
    except AttributeError as ve:
        logger.error("Problem while getting the image file: {}".format(str(ve)))
        return {"detail": str(ve), "code": "UNPROCESSABLE_ENTITY", "status": 422}, 422
    except Exception as e:
        return {"detail": str(e), "code": type(e).__name__, "status": 400}, 400
    # osUtils.list_images(vim_conn)
    return {"detail": "Image status: {}".format(r.status), "code": "CREATED", "status": 201}

def vnf_onboard(id):
    try:
        res = 'ok'
        code = 200
        for upload in os.listdir("/tmp/onboarding/{}/vnfds".format(id)):
            data_obj = open(upload, 'rb')
            print(MANO_VNFD_POST)
            r = requests.post(MANO_VNFD_POST, files={"vnfd": (filename, data_obj)})
            res = r.text
            code = r.status_code
            # Delete package file when done with validation

            logger.debug("Temporary VNFD deleted")
        return res, code
    except AttributeError as ae:
        logger.error("Problem while getting the vnfd the file: {}".format(str(ae)))
        return jsonify({"detail": str(ae), "code": "PRECONDITION_FAILED", "status": 412}), 412
    except NameError as ne:
        logger.error("Problem with the ENV vars: {}".format(str(ne)))
        return jsonify({"detail": str(ne), "code": "INTERNAL_SERVER_ERROR", "status": 500}), 500
    except Exception as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        logger.warning("Problem while onboarding VNFD: {}".format(str(e)))
        return jsonify({"detail": message, "code": "BAD_REQUEST", "status": 400}), 400

def ns_onboard(id):
    try:
        res = 'ok'
        code = 200
        for upload in os.listdir("/tmp/onboarding/{}/nsd".format(id)):
            data_obj = open(upload, 'rb')
            print(MANO_NSD_POST)
            r = requests.post(MANO_NSD_POST, files={"vnfd": (filename, data_obj)})
            res = r.text
            code = r.status_code
            # Delete package file when done with validation

            logger.debug("Temporary VNFD deleted")
        return res, code
    except AttributeError as ae:
        logger.error("Problem while getting the vnfd the file: {}".format(str(ae)))
        return jsonify({"detail": str(ae), "code": "PRECONDITION_FAILED", "status": 412}), 412
    except NameError as ne:
        logger.error("Problem with the ENV vars: {}".format(str(ne)))
        return jsonify({"detail": str(ne), "code": "INTERNAL_SERVER_ERROR", "status": 500}), 500
    except Exception as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        logger.warning("Problem while onboarding VNFD: {}".format(str(e)))
        return jsonify({"detail": message, "code": "BAD_REQUEST", "status": 400}), 400
"""
if __name__ == '__main__':

        http_server = WSGIServer(('', 5101), app)
        http_server.serve_forever()



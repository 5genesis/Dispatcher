import ast
from flask import Flask, jsonify, request
from flask_restful import Resource, Api
import json
from utils import init_directory, str_to_bool
import requests
from pymongo import MongoClient
from datetime import datetime
import os
from gevent.pywsgi import WSGIServer
import logging
import yaml
from flask_cors import CORS
from uuid import uuid4
from validator import validate_zip
from shutil import copyfile
import hashlib

app = Flask(__name__)
api = Api(app)
CORS(app)

logger = logging.getLogger("MANO")
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
stream_formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
fh = logging.FileHandler('mano.log')
fh.setFormatter(formatter)
stream_handler.setFormatter(stream_formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.addHandler(stream_handler)

dbclient = MongoClient("mongodb://database:27017/")
config_file = 'mano.conf'


# conf = ConfigObj(config_file)


@app.route('/vnfd', methods=['POST'])
def vnfds():
    """
    Input: VNFDs
    Output: 200 code
    """
    try:
        logger.info(str(request))
        token = request.headers.environ.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        user = ast.literal_eval(
            requests.get('http://auth:2000/get_user_from_token', headers={'Authorization': str(token)}).text)[
            'result']
        global_code = 200
        vnfd_schema = json.load(open('schemas/vnfd_schema.json', "r"))
        files_uploaded = {}
        for upload in request.files.getlist('file'):
            filename = upload.filename.rsplit("/")[0]
            # Write package file to static directory and validate it
            logger.debug('Saving temporary VNFD')
            upload.save(filename)
            res, code, fields = validate_zip(filename, vnfd_schema, type='vnf')
            fields['user'] = user
            fields['visibility'] = str_to_bool(request.form.get('visibility', 1))
            data_ind = {'name': fields['name'], 'description': fields['description'], 'vendor': fields['vendor']}
            if code != 200:
                global_code = 400
                files_uploaded[filename] = res

            if code == 200:
                final_path = '/repository/vnf/' + fields.get('id') + '/' + fields.get('version')
                if os.path.isdir('/repository/vnf/' + fields.get('id')):
                    if os.path.isdir(final_path):
                        files_uploaded[filename] = 'VNF with this version already exists'
                    else:
                        os.mkdir(final_path)
                        copyfile(filename,
                                 final_path + '/' + fields.get('id') + "-" + fields.get('version') + '.tar.gz')  # VNF
                        yaml.dump(fields, open(final_path + '/' + 'metadata.yaml', 'w'))  # metadata
                        index = yaml.load(open('/repository/index.yaml'), Loader=yaml.FullLoader)

                        index['vnf_packages'][fields.get('id')][fields.get('version')] = data_ind
                        yaml.dump(index, open('/repository/' + 'index.yaml', 'w'))  # metadata
                        files_uploaded[filename] = 'VNF version added'
                else:
                    os.mkdir("/repository/vnf/" + fields.get('id'))
                    os.mkdir(final_path)
                    copyfile(filename,
                             final_path + '/' + fields.get('id') + "-" + fields.get('version') + '.tar.gz')  # VNF
                    yaml.dump(fields, open(final_path + '/' + 'metadata.yaml', 'w'))  # metadata
                    index = yaml.load(open('/repository/index.yaml'), Loader=yaml.FullLoader)

                    index['vnf_packages'][fields.get('id')] = {fields.get('version'): data_ind}
                    yaml.dump(index, open('/repository/' + 'index.yaml', 'w'))  # metadata
                    files_uploaded[filename] = 'VNF added'
            os.remove(filename)
        # r=root, d=directories, f = files

        if global_code != 200:
            # Valid descriptor: proceed with the onboarding
            raise Exception('A VNF has invalid descriptors. Please reupload the invalid VNFD well formed."')
        return jsonify({'loaded VNFDs': files_uploaded}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'files_uploaded': files_uploaded}), 400


@app.route('/nsd', methods=['POST'])
def nsd():
    """
    Input: VNFDs
    Output: 200 code
    """
    try:
        logger.info(str(request))
        token = request.headers.environ.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        user = ast.literal_eval(
            requests.get('http://auth:2000/get_user_from_token', headers={'Authorization': str(token)}).text)[
            'result']
        global_code = 200
        nsd_schema = json.load(open('schemas/nsd_schema.json', "r"))
        files_uploaded = {}
        for upload in request.files.getlist('file'):
            filename = upload.filename.rsplit("/")[0]
            # Write package file to static directory and validate it
            logger.debug('Saving temporary VNFD')
            upload.save(filename)
            res, code, fields = validate_zip(filename, nsd_schema, type='ns')
            if code != 200:
                global_code = 400
                files_uploaded[filename] = res

            if code == 200:
                fields['user'] = user
                fields['visibility'] = str_to_bool(request.form.get('visibility', 1))
                data_ind = {'name': fields['name'], 'description': fields['description'], 'vendor': fields['vendor']}
                nsd_path = '/repository/ns'
                final_path = nsd_path + '/' + fields.get('id') + '/' + fields.get('version')
                if os.path.isdir(nsd_path + '/' + fields.get('id')):
                    if os.path.isdir(final_path):
                        files_uploaded[filename] = 'NSD with this version already exists'
                    else:
                        os.mkdir(final_path)
                        copyfile(filename,
                                 final_path + '/' + fields.get('id') + "-" + fields.get('version') + '.tar.gz')  # VNF
                        yaml.dump(fields, open(final_path + '/' + 'metadata.yaml', 'w'))  # metadata
                        index = yaml.load(open('/repository/index.yaml'), Loader=yaml.FullLoader)

                        index['nsd_packages'][fields.get('id')][fields.get('version')] = data_ind
                        yaml.dump(index, open('/repository/index.yaml', 'w'))  # metadata
                        files_uploaded[filename] = 'NSD version added'
                else:
                    os.mkdir(nsd_path + '/' + fields.get('id'))
                    os.mkdir(final_path)
                    copyfile(filename,
                             final_path + '/' + fields.get('id') + "-" + fields.get('version') + '.tar.gz')  # VNF
                    yaml.dump(fields, open(final_path + '/' + 'metadata.yaml', 'w'))  # metadata
                    index = yaml.load(open('/repository/index.yaml'), Loader=yaml.FullLoader)

                    index['nsd_packages'][fields.get('id')] = {fields.get('version'): data_ind}
                    yaml.dump(index, open('/repository/' + 'index.yaml', 'w'))  # metadata
                    files_uploaded[filename] = 'NSD added'
            os.remove(filename)

        if global_code != 200:
            # Valid descriptor: proceed with the onboarding
            raise Exception('A NSD has invalid descriptors. Please reupload the invalid VNFD well formed. ')
        return jsonify({'loaded VNFDs': files_uploaded}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'loaded VNFDs': files_uploaded}), 400


"""
@app.route('/image/', methods=['POST'])
def onboard_vim_image():

    try:
        logger.info("Uploading image")
        vim_id = request.form.get('vim_id')
        db = dbclient["images"]
        vim = db[request.form.get('vim_id')]
        # Save file to static directory and validate it
        target = "/tmp/vim"
        if not os.path.isdir(target):
            os.mkdir(target)
        checksum = hashlib.md5(request.files['file'].read(2**5)).hexdigest()

        file = request.files.get("file")

        if len(list(vim.find({'checksum': checksum}))) > 0:
            return jsonify({"status": "Image already exists in " + vim_id}), 400
        else:

            filename = file.filename.rsplit("/")[0]
            # Write package file to static directory and validate it
            logger.debug("Saving temporary VIM")
            file.save(target + '/' + filename)
            filename_without_extension, file_extension = os.path.splitext(target + '/' + filename)

    except AttributeError as ve:
        logger.error("Problem while getting the image file: {}".format(str(ve)))
        return jsonify({"detail": str(ve), "code": "UNPROCESSABLE_ENTITY", "status": 422}), 422
    except Exception as e:
        return jsonify({"detail": str(e), "code": type(e).__name__, "status": 400}), 400
    try:
        return jsonify({"status": "updated"}), 201
    finally:
        vim.insert_one({'checksum': checksum, 'filename': filename, })




def post_image(self, vim_name):
    import os
    vim = conf["VIM"][vim_name]
    # init the VIM
    logger.info("Adding VIM- Type: {}, Auth URL:{}, User:{}, Project:{}".format(vim["TYPE"], vim["AUTH_URL"], vim["USER"], vim["PROJECT"]))
    if vim["TYPE"] == "openstack":
        vim_conn = osUtils.connection(auth_url=vim["AUTH_URL"], region="RegionOne", project_name=vim["PROJECT"], username=vim["USER"], password=vim["PASSWORD"])
    else:
        raise KeyError("VIM type {} not supported".format(vim["TYPE"]))
    try:
        logger.info("Uploading image")
        file = request.files.get("image")
        if not file:
            raise AttributeError("Image file not present in the query or wrong headers")
        # Save file to static directory and validate it
        file.save(file.filename)

        # get image parameters
        disk_format = request.args.get('disk_format')
        container_format = request.args.get('container_format')

        r = osUtils.upload_image(vim_conn, file, disk_format, container_format)
        # Delete file when done with validation
        os.remove(file.filename)
    except KeyError as ke:
        logger.error("VIM type {} not supported".format(vim["TYPE"]))
        return {"detail": str(ve), "code":"NOT_ACCEPTABLE", "status": 406}, 406
    except AttributeError as ve:
        logger.error("Problem while getting the image file: {}".format(str(ve)))
        return {"detail": str(ve), "code":"UNPROCESSABLE_ENTITY", "status": 422}, 422
    except Exception as e:
        return {"detail": str(e), "code": type(e).__name__, "status": 400}, 400
    #osUtils.list_images(vim_conn)
    return {"detail": "Image status: {}".format(r.status), "code": "CREATED", "status": 201}, 201
"""
if __name__ == '__main__':
    init_directory()
    http_server = WSGIServer(('', 5101), app)
    http_server.serve_forever()

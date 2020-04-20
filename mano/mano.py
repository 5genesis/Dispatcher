import ast
from flask import Flask, jsonify, request
from flask_restful import Resource, Api
import json
from utils import init_directory, str_to_bool
import requests
from pymongo import MongoClient
from libs.openstack_util import OSUtils as osUtils
from libs.opennebula_util import Opennebula as oneUtils
import os
from gevent.pywsgi import WSGIServer
import logging
import yaml
from flask_cors import CORS
from configobj import ConfigObj
from validator import validate_zip
from shutil import copyfile
import hashlib
from packaging import version

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

            if code != 200:
                global_code = 400
                files_uploaded[filename] = res
            if code == 200:
                fields['user'] = user
                fields['visibility'] = str_to_bool(request.form.get('visibility', 1))
                existing_image_test(fields.get('images', []))
                data_ind = {'name': fields['name'], 'description': fields['description'], 'vendor': fields['vendor'],
                            'path': fields['path']}

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
                        if version.parse(index['vnf_packages'][fields.get('id')]['latest'])< version.parse(fields.get('version')):
                            index['vnf_packages'][fields.get('id')]['latest'] = fields.get('version')
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
                    index['vnf_packages'][fields.get('id')]['latest'] = fields.get('version')
                    yaml.dump(index, open('/repository/' + 'index.yaml', 'w'))  # metadata
                    files_uploaded[filename] = 'VNF added'
            os.remove(filename)
        # r=root, d=directories, f = files

        if global_code != 200:
            # Valid descriptor: proceed with the onboarding
            raise Exception('Some VNFs have invalid descriptors')
        return jsonify({'VNFs': files_uploaded}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'VNFs': files_uploaded}), 400


def existing_image_test(images):
    vim_list = list(dbclient["images"].list_collection_names())
    for name in images:
        result = False
        for vim in vim_list:
            if len(list(dbclient["images"][vim].find({'name': name}))) > 0:
                result = True
        if not result:
            raise Exception('None of VIM have the image requested by the VNF. Please Upload the image "' + name + '".')



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
            logger.debug('Saving temporary NSD')
            upload.save(filename)
            res, code, fields = validate_zip(filename, nsd_schema, type='ns')
            if code != 200:
                global_code = 400
                files_uploaded[filename] = res

            if code == 200:
                fields['user'] = user
                fields['visibility'] = str_to_bool(request.form.get('visibility', 1))
                data_ind = {'name': fields['name'], 'description': fields['description'], 'vendor': fields['vendor'],
                            'path': fields['path']}
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
                        if version.parse(index['nsd_packages'][fields.get('id')]['latest'])< version.parse(fields.get('version')):
                            index['nsd_packages'][fields.get('id')]['latest'] = fields.get('version')
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
                    index['nsd_packages'][fields.get('id')]['latest'] = fields.get('version')
                    yaml.dump(index, open('/repository/' + 'index.yaml', 'w'))  # metadata
                    files_uploaded[filename] = 'NSD added'
            os.remove(filename)

        if global_code != 200:
            # Valid descriptor: proceed with the onboarding
            raise Exception('Some NSD have invalid descriptors')
        return jsonify({'NSs': files_uploaded}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'NSs': files_uploaded}), 400


@app.route('/image', methods=['POST'])
def onboard_vim_image():
    """
    Input: Image
    Output: 200 code
    """
    try:
        logger.info("Uploading image")
        vim_id = request.form.get('vim_id')
        container_format = request.form.get('container_format', 'bare')
        vim = dbclient["images"][vim_id]
        # Save file to static directory and validate it

        checksum = hashlib.md5(request.files['file'].read(2 ** 5)).hexdigest()
        if len(list(vim.find({'checksum': checksum}))) > 0:
            return jsonify({'status': 'Image already exists in ' + vim_id + ' With image name "'
                                      + list(vim.find({'checksum': checksum}))[0].get('name') + '"'}), 400
        else:

            file = request.files.get("file")
            file.save(file.filename)
            # Write package file to static directory and validate it
            logger.debug("Saving temporary VIM")
            if str(conf["VIM"][vim_id]['TYPE']) == "openstack":
                r = openstack_upload_image(vim_id, file, container_format)
            elif str(conf["VIM"][vim_id]['TYPE']) == "opennebula":
                r = opennebula_upload_image(vim_id, file, container_format)
            else:
                raise Exception('VIM not supported: {}'.format(conf["VIM"][vim_id]['TYPE']))

            os.remove(file.filename)

    except AttributeError as ve:
        logger.error("Problem while getting the image file: {}".format(str(ve)))
        return jsonify({"detail": str(ve), "code": "UNPROCESSABLE_ENTITY", "status": 422}), 422
    except Exception as e:
        return jsonify({"detail": str(e), "code": type(e).__name__, "status": 400}), 400
    try:
        return jsonify({"status": "updated"}), 201
    finally:
        filename_without_extension, file_extension = os.path.splitext(file.filename)
        vim.insert_one({'checksum': checksum, 'name': filename_without_extension})


def openstack_upload_image(vim_id, file, container_format):
    vim_conf = conf["VIM"][vim_id]
    filename_without_extension, file_extension = os.path.splitext(file.filename)
    traductor = {
        '.qcow2': 'qcow2',
        '.img': 'qcow2',
        '.iso': 'iso',
        '.ova': 'ova',
        '.vhd': 'vhd'
    }
    disk_format = traductor[file_extension]

    vim_conn = osUtils.connection(auth_url=vim_conf["AUTH_URL"], region="RegionOne", project_name=vim_conf["PROJECT"],
                                  username=vim_conf["USER"], password=vim_conf["PASSWORD"])

    r = osUtils.upload_image(vim_conn, file, disk_format, container_format)
    return r


def opennebula_upload_image(vim_id, file, container_format):
    vim_conf = conf["VIM"][vim_id]
    filename_without_extension, file_extension = os.path.splitext(file.filename)
    traductor = {
        '.qcow2': 'qcow2',
        '.img': 'qcow2',
        '.iso': 'iso',
        '.ova': 'ova',
        '.vhd': 'vhd'
    }
    disk_format = traductor[file_extension]

    r = oneUtils.upload_image(auth_url=vim_conf["AUTH_URL"], one_username=vim_conf["USER"], one_password=vim_conf["PASSWORD"], \
                              f=file, server_ip="192.168.33.112", server_username="test", server_password="test", \
                              image_dir="/home/test/")
    return r

@app.route('/vims', methods=['GET'])
def get_vims():
    """
    Output: 200 code and list of current vims
    """
    logger.info("Retrieving VIMs list")
    aux_list = []
    try:
        for vim in conf["VIM"]:
            new_vim = {}
            new_vim["name"] = vim
            new_vim["type"] = conf["VIM"][vim]["TYPE"]
            new_vim["location"] = conf["VIM"][vim]["LOCATION"]
            aux_list.append(new_vim)
    except Exception as e:
        return jsonify({"detail": str(e), "code": type(e).__name__, "status": 400}), 400
    logger.debug("VIMs list: {}".format(aux_list))
    return jsonify(aux_list), 200

@app.route('/nsd', methods=['GET'])
def list_nsd():
    index = yaml.load(open('/repository/index.yaml'), Loader=yaml.FullLoader)
    return jsonify(index['nsd_packages']), 200


@app.route('/vnfd', methods=['GET'])
def list_vnf():
    index = yaml.load(open('/repository/index.yaml'), Loader=yaml.FullLoader)
    return jsonify(index['vnf_packages']), 200

if __name__ == '__main__':
    init_directory()
    conf = ConfigObj('mano.conf')
    http_server = WSGIServer(('', 5101), app)
    http_server.serve_forever()

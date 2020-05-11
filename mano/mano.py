import ast
from flask import Flask, jsonify, request
from flask_restful import Resource, Api
import json
from utils import init_directory, str_to_bool
import requests
from pymongo import MongoClient
from libs.openstack_util import OSUtils as osUtils
from libs.osm_nbi_util import NbiUtil as osmUtils
import os
from gevent.pywsgi import WSGIServer
import logging
import yaml
from flask_cors import CORS
from configobj import ConfigObj
from validator import validate_zip
from shutil import copyfile, rmtree
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
        global_code = 200
        vnfd_schema = json.load(open('schemas/vnfd_schema.json', "r"))
        files_uploaded = {}
        for upload in request.files.getlist('file'):
            filename = upload.filename.rsplit("/")[0]
            logger.debug('Saving temporary VNFD')
            upload.save(filename)
            res, code, fields = validate_zip(filename, vnfd_schema, type='vnf')
            if code != 200:
                global_code = 400
                files_uploaded[filename] = res
            if code == 200:
                existing_image_test(fields.get('images', []))
                final_path = '/repository/vnf/' + fields.get('id') + '/' + fields.get('version')
                if os.path.isdir('/repository/vnf/' + fields.get('id')):
                    if os.path.isdir(final_path):
                        files_uploaded[filename] = 'VNF with this version already exists'
                    else:
                        os.mkdir(final_path)
                        index_vnf(fields, filename, final_path, new_version=True)
                        files_uploaded[filename] = 'VNF version added'
                else:
                    os.mkdir("/repository/vnf/" + fields.get('id'))
                    os.mkdir(final_path)
                    index_vnf(fields, filename, final_path, new_version=False)
                    files_uploaded[filename] = 'VNF added'
            os.remove(filename)
        if global_code != 200:
            raise Exception('Some VNFs have invalid descriptors')
        return jsonify({'VNFs': files_uploaded}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'VNFs': files_uploaded}), 400


def index_vnf(fields, filename, final_path, new_version):
    """
    Indexing function for VNFs
    """

    user = get_user()
    fields['user'] = user
    fields['visibility'] = str_to_bool(request.form.get('visibility', 1))
    data_ind = {'name': fields['name'], 'description': fields['description'], 'vendor': fields['vendor'],
                'path': fields['path']}
    copyfile(filename,
             final_path + '/' + fields.get('id') + "-" + fields.get('version') + '.tar.gz')
    yaml.dump(fields, open(final_path + '/' + 'metadata.yaml', 'w'))
    index = yaml.load(open('/repository/index.yaml'), Loader=yaml.FullLoader)

    if new_version:
        index['vnf_packages'][fields.get('id')][fields.get('version')] = data_ind
        if version.parse(index['vnf_packages'][fields.get('id')]['latest']) < version.parse(
                fields.get('version')):
            index['vnf_packages'][fields.get('id')]['latest'] = fields.get('version')
    else:
        index['vnf_packages'][fields.get('id')] = {fields.get('version'): data_ind}
        index['vnf_packages'][fields.get('id')]['latest'] = fields.get('version')
    yaml.dump(index, open('/repository/' + 'index.yaml', 'w'))


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
        global_code = 200
        nsd_schema = json.load(open('schemas/nsd_schema.json', "r"))
        files_uploaded = {}
        for upload in request.files.getlist('file'):
            filename = upload.filename.rsplit("/")[0]
            logger.debug('Saving temporary NSD')
            upload.save(filename)
            res, code, fields = validate_zip(filename, nsd_schema, type='ns')
            if code != 200:
                global_code = 400
                files_uploaded[filename] = res
            if code == 200:
                nsd_path = '/repository/ns'
                final_path = nsd_path + '/' + fields.get('id') + '/' + fields.get('version')
                if os.path.isdir(nsd_path + '/' + fields.get('id')):
                    if os.path.isdir(final_path):
                        files_uploaded[filename] = 'NSD with this version already exists'
                    else:
                        os.mkdir(final_path)
                        index_ns(fields, filename, final_path, new_version=True)
                        files_uploaded[filename] = 'NSD version added'
                else:
                    os.mkdir(nsd_path + '/' + fields.get('id'))
                    os.mkdir(final_path)
                    index_ns(fields, filename, final_path, new_version=False)
                    files_uploaded[filename] = 'NSD added'
            os.remove(filename)
        if global_code != 200:
            raise Exception('Some NSD have invalid descriptors')
        return jsonify({'NSs': files_uploaded}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'NSs': files_uploaded}), 400


def index_ns(fields, filename, final_path, new_version):
    """
    indexing function for network services
    """
    user = get_user()
    fields['visibility'] = str_to_bool(request.form.get('visibility', 1))
    fields['user'] = user
    data_ind = {'name': fields['name'], 'description': fields['description'], 'vendor': fields['vendor'],
                'path': fields['path']}
    copyfile(filename,
             final_path + '/' + fields.get('id') + "-" + fields.get('version') + '.tar.gz')
    yaml.dump(fields, open(final_path + '/' + 'metadata.yaml', 'w'))
    index = yaml.load(open('/repository/index.yaml'), Loader=yaml.FullLoader)
    if new_version:
        index['ns_packages'][fields.get('id')][fields.get('version')] = data_ind
        if version.parse(index['ns_packages'][fields.get('id')]['latest']) < version.parse(fields.get('version')):
            index['ns_packages'][fields.get('id')]['latest'] = fields.get('version')
    else:
        index['ns_packages'][fields.get('id')] = {fields.get('version'): data_ind}
        index['ns_packages'][fields.get('id')]['latest'] = fields.get('version')
    yaml.dump(index, open('/repository/index.yaml', 'w'))


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
        checksum = hashlib.md5(request.files['file'].read(2 ** 5)).hexdigest()
        if len(list(vim.find({'checksum': checksum}))) > 0:
            return jsonify({'status': 'Image already exists in ' + vim_id + ' With image name "'
                                      + list(vim.find({'checksum': checksum}))[0].get('name') + '"'}), 400
        else:
            file = request.files.get("file")
            file.save(file.filename)
            logger.debug("Saving temporary VIM")
            if conf["VIM"][vim_id]['TYPE']:
                r = openstack_upload_image(vim_id, file, container_format)
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
    return jsonify(list(index['ns_packages'].keys())), 200


@app.route('/vnfd', methods=['GET'])
def list_vnf():
    index = yaml.load(open('/repository/index.yaml'), Loader=yaml.FullLoader)
    return jsonify(list(index['vnf_packages'].keys())), 200


@app.route('/onboard_ns', methods=['POST'])
def onboard_ns():
    try:
        r = {'detail': 'no detail'}
        ns = request.form.get('ns')
        if not ns:
            return jsonify({'result': 'argument ns in form is required'}), 404
        index = yaml.load(open('/repository/index.yaml'), Loader=yaml.FullLoader)
        if ns not in index['ns_packages'].keys():
            return jsonify({'result': '{} Network Service not found'.format(ns)}), 404
        latest = index['ns_packages'][ns]['latest']
        ns_metadata = yaml.load(open(os.path.join('/repository', 'ns', ns, latest, 'metadata.yaml')),
                                Loader=yaml.FullLoader)
        vnf_dependencies = ns_metadata['vnfd-id-ref']
        for vnf_dependency in vnf_dependencies:
            vnf = index['vnf_packages'][vnf_dependency]
            vnf_path = '/repository/' + vnf[vnf['latest']]['path']
            r, status_code = nbiUtil.upload_vnfd_package(vnf_path)
            if status_code >= 300:
                if not 'exists' in str(r):
                    raise Exception("VNF '{}' can not be onboarded".format(vnf_dependency))
            else:
                dbclient['onboarded']['vnf'].insert_one({'vnf': vnf_dependency, 'ns': ns, 'vnfid': r['id']})
        ns_package = '/repository/' + index['ns_packages'][ns][index['ns_packages'][ns]['latest']]['path']
        r, status_code = nbiUtil.upload_nsd_package(ns_package)
        if status_code >= 300:
            raise Exception("NS '{}' can not be onboarded".format(vnf_dependency))
    except Exception as e:
        return jsonify({'result': str(e), 'detail': r['detail'], 'status': 400}), 400
    dbclient['onboarded']['ns'].insert_one({'ns': ns, 'nsid': r['id']})
    return jsonify(r), status_code


def get_user():
    token = request.headers.environ.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
    return ast.literal_eval(
        requests.get('http://auth:2000/get_user_from_token', headers={'Authorization': str(token)}).text)[
        'result']


@app.route('/nsd/<nsdId>', methods=['DELETE'])
def delete_nsd(nsdId):
    """
    Network Service Delete on OSM and repository
    """
    try:
        logger.info("VNFD successfully modified")
        all = str_to_bool(request.form.get('all', 0))
        user = get_user()
        index = yaml.load(open('/repository/index.yaml'), Loader=yaml.FullLoader)
        ns = index.get('ns_packages').get(nsdId, {})
        if not len(ns):
            raise Exception('Network Service not found')
        latest = ns['latest']
        ns_metadata = yaml.load(open('/repository/ns/' + nsdId + '/' + latest + '/metadata.yaml'),
                                Loader=yaml.FullLoader)
        if user != ns_metadata['user']:
            raise Exception('User {} have not uploaded this Network Service. This user has not permissions for deleting'
                            ' this'.format(user))
        ns_id = dbclient['onboarded']['ns'].find_one({'ns': nsdId}).get('nsid')
        nbiUtil.delete_nsd(ns_id)
        logger.info('NS {} deleted in OSM'.format(nsdId))
        if all or len(ns) == 2:
            del index['ns_packages'][nsdId]
            rmtree('/repository/ns/' + nsdId)

        else:
            del index['ns_packages'][nsdId][latest]
            rmtree('/repository/ns/' + nsdId + '/' + latest)

        yaml.dump(index, open('/repository/' + 'index.yaml', 'w'))
        dbclient['onboarded']['ns'].delete_one({'ns': nsdId})
        return jsonify({}), 204
    except Exception as e:
        return jsonify({"detail": str(e), "code": type(e).__name__, "status": 400}), 400


if __name__ == '__main__':
    init_directory()
    conf = ConfigObj('mano.conf')
    if conf["NFVO"]["TYPE"] == "OSM":
        nbiUtil = osmUtils(osm_ip=conf["NFVO"]["IP"], username=conf["NFVO"]["USER"], password=conf["NFVO"]["PASSWORD"],
                           vim_account_id=None)
    else:
        logger.error("NFVO type {} not supported".format(conf["NFVO"]["TYPE"]))
        raise KeyError("NFVO type {} not supported".format(conf["NFVO"]["TYPE"]))
    http_server = WSGIServer(('', 5101), app)
    http_server.serve_forever()

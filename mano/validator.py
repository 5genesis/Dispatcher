import tarfile
import shutil
import glob
import yaml
import jsonschema
from flask import jsonify
import logging
import hashlib

logger = logging.getLogger("VALIDATOR")
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
stream_formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
fh = logging.FileHandler('validator.log')
fh.setFormatter(formatter)
stream_handler.setFormatter(stream_formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.addHandler(stream_handler)


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def fields_building(descriptor_json, file, type):
    fields = {}
    base_path ='/' + type + '/'
    if type == "vnf":
        aux_dict = descriptor_json.get('vnfd-catalog', {}).get('vnfd', [{}])[0]
        fields['name'] = aux_dict.get('name')
        fields['id'] = aux_dict.get('id')
        fields['description'] = aux_dict.get('description')
        fields['vendor'] = aux_dict.get('vendor')
        fields['version'] = aux_dict.get('version')
        images = []
        for vdu in aux_dict.get('vdu'):
            images.append(vdu.get('image'))
        fields['images'] = images
        fields['checksum'] = md5(file)
    if type == "ns":
        aux_dict = descriptor_json.get('nsd-catalog', {}).get('nsd', [{}])[0]
        fields['name'] = aux_dict.get('name')
        fields['id'] = aux_dict.get('id')
        fields['description'] = aux_dict.get('description')
        fields['vendor'] = aux_dict.get('vendor')
        fields['version'] = aux_dict.get('version')
        vnfs = []

        for vnf in aux_dict.get('constituent-vnfd'):
            vnfs.append(vnf.get('vnfd-id-ref'))
        logger.debug('Used VNFS in the NSD: ' + str(vnfs))
        check_existing_vnfs(vnfs)
        fields['vnfd-id-ref'] = vnfs
        fields['path'] = base_path + fields['id'] + '/' + fields['version'] + '/' + fields.get('id') + "-" + \
                         fields.get('version') + '.tar.gz'
        fields['checksum'] = md5(file)
    return fields


def check_existing_vnfs(vnfs):
    index = yaml.load(open('/repository/index.yaml'), Loader=yaml.FullLoader).get('vnf_packages', {})

    for vnf in vnfs:
        if vnf not in index:
            raise Exception(
                str("VNFD '" + str(vnf) + "' has not found in the repository, please upload it first, and then try "
                                          "to upload the NSD"))


def validate_zip(file, schema, type):
    try:
        logger.debug("Decompressing package file")
        # unzip the package
        tar = tarfile.open(file, "r:gz")
        folder = tar.getnames()[0]
        tar.extractall()
        tar.close()
        # pick the file that contains the main descriptor
        descriptor_file = glob.glob(folder + "/*.y*ml")[0]
        logger.debug("Opening descriptor file: {}".format(descriptor_file))
        with open(descriptor_file, 'r') as f:
            descriptor_data = f.read()
        # load the data inside the file in the 'descriptor_json' variable
        descriptor_json = yaml.safe_load(descriptor_data)

        fields = fields_building(descriptor_json, file, type)
        logger.debug("Descriptor: {}".format(descriptor_json))
        # compare the json with the proper schema
        jsonschema.validate(descriptor_json, schema)
        # Delete the folder we just created
        shutil.rmtree(folder, ignore_errors=True)
        logger.debug("Descriptor sucessfully validated")
        return jsonify({"detail": "VNFD successfully validated", "code": "OK", "status": 200}), 200, fields
    except jsonschema.exceptions.ValidationError as ve:
        # Delete the folder we just created
        shutil.rmtree(folder, ignore_errors=True)
        logger.warning("Problem while validating VNFD: {}".format(ve.message))
        return {"detail": "Problem while validating VNFD: {}".format(ve.message)}, 400, {}
    except Exception as e:
        # Delete the folder we just created
        shutil.rmtree(folder, ignore_errors=True)

        logger.warning("Problem while validating VNFD: {}".format(str(e)))
        return {"detail": str(e)}, 400, {}
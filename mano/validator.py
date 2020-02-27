import tarfile
import shutil
import glob
import yaml
import jsonschema
from flask import jsonify
import logging

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


def validate_zip(file, schema):
    try:
        # TODO: Switch from jsonschema to fastjsonschema
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
        logger.debug("Descriptor: {}".format(descriptor_json))
        # compare the json with the proper schema
        jsonschema.validate(descriptor_json, schema)
        # Delete the folder we just created
        shutil.rmtree(folder, ignore_errors=True)
        logger.debug("Descriptor sucessfully validated")
        return jsonify({"detail": "VNFD successfully validated", "code": "OK", "status": 200}), 200
    except jsonschema.exceptions.ValidationError as ve:
        # Delete the folder we just created
        shutil.rmtree(folder, ignore_errors=True)
        logger.warning("Problem while validating VNFD: {}".format(ve.message))
        return jsonify({"detail": "Problem while validating VNFD: {}".format(ve.message), "code": "BAD_REQUEST",
                        "status": 400}), 400
    except Exception as e:
        # Delete the folder we just created
        shutil.rmtree(folder, ignore_errors=True)
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        logger.warning("Problem while validating VNFD: {}".format(str(e)))
        return jsonify({"detail": message, "code": "BAD_REQUEST", "status": 400}), 400

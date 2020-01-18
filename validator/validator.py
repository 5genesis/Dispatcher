import jsonschema
import fastjsonschema
import simplejson as json
import os
from flask import Flask, jsonify, request
import requests
import pymongo
import logging

from gevent.pywsgi import WSGIServer

from flask_cors import CORS


app = Flask(__name__)
CORS(app)

#ELCM_ED_POST = 'ELCM_ED_POST' in os.environ ? os.environ['ELCM_ED_POST']:None
if 'ELCM_ED_POST' in os.environ: ELCM_ED_POST = os.environ['ELCM_ED_POST']
if 'MANO_VNFD_POST' in os.environ: MANO_VNFD_POST = os.environ['MANO_VNFD_POST']
if 'MANO_NSD_POST' in os.environ: MANO_NSD_POST = os.environ['MANO_NSD_POST']


json_obj = {
	"Id": 123,
	"Name":"sfafd",
	"User": 123,
	"Platform": "malaga",
	"TestCases": ["TC1", "TC2"],
	"UEs": ["UE1", "UE2"],
	"Slice": "slice id",
	"NS": "ns_id",
	"NS_Placement": "Core",
	"Limited": True,
	"Type_experiment": False,
	"Scenario": ["scenario1", "scemarop2"],
	"Application": ["app1"],
	"Attended": True,
	"Reservation_timme": 123
}

# DB parameters
dbclient = pymongo.MongoClient("mongodb://database:27017/")

# Logging Parameters
logger = logging.getLogger("-VALIDATOR API-")
fh = logging.FileHandler('validator.log')

stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
stream_formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
fh.setFormatter(formatter)
stream_handler.setFormatter(stream_formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.addHandler(stream_handler)


@app.route('/validate/ed', methods=['POST'])
def validate_ed():
    try:
        logger.info("Validating Experiment descriptor")
        content = request.get_data()
        data = json.loads(content)
        logger.debug("Experiment descriptor: {}".format(data))
        #jsonschema.validate(data, ed_schema)
        validate = fastjsonschema.compile(ed_schema)
        j = validate(data)
    except jsonschema.exceptions.ValidationError as ve:
        logger.warning("Problem while validating Experiment descriptor: {}".format(ve.message))
        return jsonify({"detail": ve.message, "code": "BAD_REQUEST", "status": 400}), 400
    except fastjsonschema.JsonSchemaDefinitionException as ve:
        logger.warning("Problem while validating Experiment descriptor: {}".format(ve.message))
        return jsonify({"detail": ve.message, "code": "BAD_REQUEST", "status": 400}), 400
    except fastjsonschema.JsonSchemaException as ve:
        logger.warning("Problem while validating Experiment descriptor: {}".format(ve.message))
        return jsonify({"detail": ve.message, "code": "BAD_REQUEST", "status": 400}), 400
    except Exception as e:
        logger.warning("Problem while validating Experiment descriptor: {}".format(str(e)))
    return jsonify({"detail": "Successful validation", "code": "OK", "status": 200}), 200


@app.route('/ed', methods=['GET'])
def list_descriptors():
    logger.info("Getting list of experiments")
    try:
        db = dbclient["experimentsdb"]
        experiments = db["experiments"]

        l = [] 
        # Create the list of experiments
        for exp in experiments.find():
            exp["_id"] = str(exp["_id"])
            l.append(exp)
    except Exception as e:
        logger.warning("Problem while obtaining the list of stored experiments: {}".format(str(e)))
        return jsonify({"detail": str(e), "code": "BAD_REQUEST", "status": 400}), 400
    return json.dumps(l), 200


@app.route('/ed/<string:exp_id>', methods=['GET', 'DELETE'])
def single_descriptor(exp_id):
    from bson.objectid import ObjectId
    import bson

    logger.info("Getting experiment descriptor {}".format(exp_id))
    try:
        db = dbclient["experimentsdb"]
        experiments = db["experiments"]

        exp_id_obj = ObjectId(exp_id)
        #exp = experiments.find_one({ "Id": exp_id },{ "_id": 0 })
        exp = experiments.find_one({ "_id": exp_id_obj })
        if not exp:
            logger.debug("Experiment with _id: {} not found in the database".format(str(exp_id)))
            return jsonify({"detail": "Experiment with _id: {} not found in the database".format(str(exp_id)), "status": 404, "code": "NOT_FOUND"}), 404
        if request.method == 'DELETE':
            logger.debug("Deleting experiment"
            exp = experiments.delete_one({ "_id": exp_id_obj })
            return 204
        exp["_id"] = str(exp["_id"])
        return json.dumps(exp), 200
        
    except bson.errors.InvalidId as e:
        logger.error("Parameter 'exp_id' format is not valid: {}".format(str(e)))
        return jsonify({"detail": str(e), "code": "BAD_REQUEST", "status": 400}), 400
    except Exception as e:
        logger.warning("Problem while obtaining experiment descriptor: {} - {}".format(str(e), type(e).__name__))
        return jsonify({"detail": str(e), "code": "BAD_REQUEST", "status": 400}), 400



def store_descriptor(descriptor):
    db = dbclient["experimentsdb"]
    experiments = db["experiments"]

    _id = experiments.insert_one(descriptor).inserted_id
    logger.debug("Experiment stored with _id: {}".format(str(_id)))
    return jsonify({"_id": str(_id)})



@app.route('/create/ed', methods=['POST'])
def onboard_ed():
    try:
        logger.info("Onboarding Experiment descriptor")
        content = request.get_data()
        data = json.loads(content)
        logger.debug("Experiment descriptor: {}".format(data))
        #jsonschema.validate(data, ed_schema)
        validate = fastjsonschema.compile(ed_schema)
        j = validate(data)
        headers = {'Content-type': 'application/json'}
        r = requests.post(ELCM_ED_POST, data=data, headers=headers)
        _id_json = store_descriptor(data)
    except jsonschema.exceptions.ValidationError as ve:
        logger.warning("Problem while validating Experiment descriptor: {}".format(ve.message))
        return jsonify({"detail": ve.message, "code": "BAD_REQUEST", "status": 400}), 400
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
    return _id_json, 200


def validate_zip(file, schema):
    import tarfile
    import shutil
    import glob
    import yaml

    try:
        # TODO: Switch from jsonschema to fastjsonschema
        logger.debug("Decompressing package file")
        # unzip the package
        tar = tarfile.open(file, "r:gz")
        folder = tar.getnames()[0]
        tar.extractall()
        tar.close()
        # pick the file that contains the main descriptor
        descriptor_file = glob.glob(folder+"/*.y*ml")[0]
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
        return jsonify({"detail": "Problem while validating VNFD: {}".format(ve.message), "code": "BAD_REQUEST", "status": 400}), 400
    except Exception as e:
        # Delete the folder we just created
        shutil.rmtree(folder, ignore_errors=True)
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        logger.warning("Problem while validating VNFD: {}".format(str(e)))
        return jsonify({"detail": message, "code": "BAD_REQUEST", "status": 400}), 400


@app.route('/validate/vnfd', methods=['POST'])
def validate_vnfd():
    try:
        logger.info("Validating VNFD")
        file = request.files.get("vnfd")
        if not file:
            raise AttributeError("VNFD file not present in the query or wrong headers")
        # Write package file to static directory and validate it
        logger.debug("Saving temporary VNFD")
        file.save(file.filename)
        r, code = validate_zip(file.filename, vnfd_schema)
        # Delete package file when done with validation
        os.remove(file.filename)
        logger.debug("Temporary VNFD deleted")
        return r, code
    except AttributeError as ae:
        logger.error("Problem while getting the vnfd the file: {}".format(str(ae)))
        return jsonify({"detail": str(ae), "code": "PRECONDITION_FAILED", "status": 412}), 412
    except Exception as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        logger.warning("Problem while validating VNFD: {}".format(str(e)))
        return jsonify({"detail": message, "code": "BAD_REQUEST", "status": 400}), 400

@app.route('/onboard/vnfd', methods=['POST'])
def onboard_vnfd():
    try:
        logger.info("Onboarding VNFD")
        file = request.files.get("vnfd")
        if not file:
            raise AttributeError("VNFD file not present in the query or wrong headers")
        # Write package file to static directory and validate it
        logger.debug("Saving temporary VNFD")
        file.save(file.filename)
        res, code = validate_zip(file.filename, vnfd_schema)
        if code is 200:
            # Valid descriptor: proceed with the onboarding
            logger.debug("Onboarding VNFD in the NFVO")
            data_obj = open(file.filename, 'rb')
            print(MANO_VNFD_POST)
            r = requests.post(MANO_VNFD_POST, files={"vnfd": (file.filename, data_obj)})
            res = r.text
            code = r.status_code
        # Delete package file when done with validation
        os.remove(file.filename)
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


@app.route('/validate/nsd', methods=['POST'])
def validate_nsd():
    try:
        logger.info("Validating NSD")
        file = request.files.get("nsd")
        if not file:
            raise AttributeError("NSD file not present in the query or wrong headers")
        # Write package file to static directory and validate it
        logger.debug("Saving temporary NSD")
        file.save(file.filename)
        r, code = validate_zip(file.filename, nsd_schema)
        # Delete package file when done with validation
        os.remove(file.filename)
        logger.debug("Temporary NSD deleted")
        return r, code
    except AttributeError as ve:
        logger.error("Problem while getting the nsd the file: {}".format(str(ve)))
        return jsonify({"detail": str(ve), "code": "PRECONDITION_FAILED", "status": 412}), 412
    except Exception as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        logger.warning("Problem while validating NSD: {}".format(str(e)))
        return jsonify({"detail": message, "code": "BAD_REQUEST", "status": 400}), 400

@app.route('/onboard/nsd', methods=['POST'])
def onboard_nsd():
    try:
        logger.info("Onbarding NSD")
        file = request.files.get("nsd")
        if not file:
            raise AttributeError("NSD file not present in the query or wrong headers")
        # Write package file to static directory and validate it
        logger.debug("Saving temporary NSD")
        file.save(file.filename)
        res, code = validate_zip(file.filename, nsd_schema)
        if code is 200:
            # Valid descriptor: proceed with the onboarding
            logger.debug("Onboarding NSD in the NFVO")
            data_obj = open(file.filename, 'rb')
            r = requests.post(MANO_NSD_POST, files={"nsd": (file.filename, data_obj)})
            res = r.text
            code = r.status_code
        # Delete package file when done with validation
        os.remove(file.filename)
        logger.debug("Temporary NSD deleted")
        return res, code
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


if __name__ == '__main__':
    logger.info("Starting app")
    # Load the schemas for validation
    with open('schemas/experiment_schema.json', 'r') as f:
        ed_schema_data = f.read()
    ed_schema = json.loads(ed_schema_data)
    logger.debug("Loaded Experiment descriptor schema")
    with open('schemas/vnfd_schema.json', 'r') as f:
        vnfd_schema_data = f.read()
    vnfd_schema = json.loads(vnfd_schema_data)
    logger.debug("Loaded VNF descriptor schema")
    with open('schemas/nsd_schema.json', 'r') as f:
        nsd_schema_data = f.read()
    nsd_schema = json.loads(nsd_schema_data)
    logger.debug("Loaded NS descriptor schema")

    http_server = WSGIServer(('', 5100), app)
    http_server.serve_forever()

    #app.run(host='0.0.0.0', debug=True)


import jsonschema
import simplejson as json
import os
from flask import Flask, jsonify, request
import requests

from gevent.pywsgi import WSGIServer
import logging

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


@app.route('/validate/ed', methods=['POST'])
def validate_ed():
    try:
        content = request.get_data()
        data = json.loads(content)
        jsonschema.validate(data, ed_schema)
    except jsonschema.exceptions.ValidationError as ve:
        return ve.message, 400
    except Exception as e:
        return str(e), 500
    return "ok", 200


@app.route('/onboard/ed', methods=['POST'])
def onboard_ed():
    try:
        content = request.get_data()
        data = json.loads(content)
        jsonschema.validate(data, ed_schema)
        headers = {'Content-type': 'application/json'}
        r = requests.post(ELCM_ED_POST, data=data, headers=headers)
    except jsonschema.exceptions.ValidationError as ve:
        return ve.message, 400
    except Exception as e:
        return str(e), 500
    return r.json(), r.status_code


def validate_zip(file, schema):
    import tarfile
    import shutil
    import glob
    import yaml

    try:
        # unzip the package
        tar = tarfile.open(file, "r:gz")
        folder = tar.getnames()[0]
        tar.extractall()
        tar.close()
        # pick the file that contains the main descriptor
        descriptor_file = glob.glob(folder+"/*.y*ml")[0]
        with open(descriptor_file, 'r') as f:
            descriptor_data = f.read()
        # load the data inside the file in the 'descriptor_json' variable
        descriptor_json = yaml.safe_load(descriptor_data)
        # compare the json with the proper schema
        jsonschema.validate(descriptor_json, schema)
        # Delete the folder we just created
        shutil.rmtree(folder, ignore_errors=True)
        return "ok", 200
    except jsonschema.exceptions.ValidationError as ve:
        # Delete the folder we just created
        shutil.rmtree(folder, ignore_errors=True)
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ve).__name__, ve.message)
        return message, 400
    except Exception as e:
        # Delete the folder we just created
        shutil.rmtree(folder, ignore_errors=True)
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        return message, 500


@app.route('/validate/vnfd', methods=['POST'])
def validate_vnfd():
    try:
        file = request.files.get("vnfd")
        if not file:
            return "VNFD file not present in the query", 404
        # Write package file to static directory and validate it
        file.save(file.filename)
        r, code = validate_zip(file.filename, vnfd_schema)
        # Delete package file when done with validation
        os.remove(file.filename)
        return r, code
    except Exception as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        return message, 500

@app.route('/onboard/vnfd', methods=['POST'])
def onboard_vnfd():
    try:
        file = request.files.get("vnfd")
        if not file:
            return "VNFD file not present in the query", 404
        # Write package file to static directory and validate it
        file.save(file.filename)
        res, code = validate_zip(file.filename, vnfd_schema)
        if code is 200:
            # Valid descriptor: proceed with the onboarding
            data_obj = open(file.filename, 'rb')
            r = requests.post(MANO_VNFD_POST, files={"vnfd": (file.filename, data_obj)})
            res = r.text
            code = r.status_code
        # Delete package file when done with validation
        os.remove(file.filename)
        return res, code
    except Exception as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        return message, 500


@app.route('/validate/nsd', methods=['POST'])
def validate_nsd():
    try:
        file = request.files.get("nsd")
        if not file:
            return "VNFD file not present in the query", 404
        # Write package file to static directory and validate it
        file.save(file.filename)
        r, code = validate_zip(file.filename, nsd_schema)
        # Delete package file when done with validation
        os.remove(file.filename)
        return r, code
    except Exception as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        return message, 500

@app.route('/onboard/nsd', methods=['POST'])
def onboard_nsd():
    try:
        file = request.files.get("nsd")
        if not file:
            return "NSD file not present in the query", 404
        # Write package file to static directory and validate it
        file.save(file.filename)
        res, code = validate_zip(file.filename, nsd_schema)
        if code is 200:
            # Valid descriptor: proceed with the onboarding
            data_obj = open(file.filename, 'rb')
            r = requests.post(MANO_NSD_POST, files={"nsd": (file.filename, data_obj)})
            res = r.text
            code = r.status_code
        # Delete package file when done with validation
        os.remove(file.filename)
        return res, code
    except Exception as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        return message, 500


if __name__ == '__main__':
    # Load the schemas for validation
    with open('experiment_schema.json', 'r') as f:
        ed_schema_data = f.read()
    ed_schema = json.loads(ed_schema_data)
    with open('vnfd_schema.json', 'r') as f:
        vnfd_schema_data = f.read()
    vnfd_schema = json.loads(vnfd_schema_data)
    with open('nsd_schema.json', 'r') as f:
        nsd_schema_data = f.read()
    nsd_schema = json.loads(nsd_schema_data)

    http_server = WSGIServer(('', 5100), app)
    http_server.serve_forever()

    #app.run(host='0.0.0.0', debug=True)


import jsonschema
import simplejson as json
from flask import Flask, jsonify, request

from gevent.pywsgi import WSGIServer
import logging

from flask_cors import CORS


app = Flask(__name__)
CORS(app)


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


@app.route('/', methods=['POST'])
def validate():
    try:
        content = request.get_data()
        data = json.loads(content)
        jsonschema.validate(data, schema)
    except jsonschema.exceptions.ValidationError as ve:
        return ve.message, 400
    except Exception as e:
        return str(e), 500
    return "ok", 200


if __name__ == '__main__':
    with open('experiment_schema.json', 'r') as f:
        schema_data = f.read()
    schema = json.loads(schema_data)

    http_server = WSGIServer(('', 5100), app)
    http_server.serve_forever()

    #app.run(host='0.0.0.0', debug=True)


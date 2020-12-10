from flask import Flask, request, jsonify
from waitress import serve

app = Flask(__name__)

id = 100
"""
    (â€œTestCasesâ€, â€œUEsâ€, â€œSliceDescriptorsâ€ y â€œScenariosâ€).

    {
        "TestCases": [
            {
                "Distributed": true,
                "Name": "Test",
                "Parameters": [],
                "PrivateCustom": [],
                "PublicCustom": false,
                "Standard": true
            }
        ]
    }

       GET / facility / baseSliceDescriptors
    GET / facility / testcases
    GET / facility / ues
    GET / facility / scenarios

"""


@app.route('/', defaults={'path': ""}, methods=['GET', 'POST', 'DELETE'])
@app.route('/<path:path>', methods=['GET', 'POST', 'DELETE'])
def hello(path):
    global id
    print("{} {}".format(request.method, path))
    print(request.remote_addr)
    if request.method == 'POST':
        id = id + 1
    if path.find('peerDetails') > 0:
        print(request.data)
        return jsonify({'execution_id': id}), 200
    if path.find('baseSliceDescriptors') > 0:
        return jsonify({'SliceDescriptors': ["slice1", "slice2"]}), 200
    if path.find('testcases') > 0:
        return jsonify({
            "TestCases": [
                {
                    "Distributed": True,
                    "Name": "Test1",
                    "Parameters": [],
                    "PrivateCustom": [],
                    "PublicCustom": True,
                    "Standard": True
                }
            ]
        }), 200
    if path.find('ues') > 0:
        return jsonify({'UEs': ["ue1", "ue2"]}), 200
    if path.find('scenarios') > 0:
        return jsonify({'Scenarios': ["scenario1", "scenario2"]}), 200
    return jsonify({'ExecutionId': id}), 200


if __name__ == '__main__':
    serve(app, port=5000)

# 5GENESIS Experiment descriptor Validator

This module validates the correct syntax of the Experiment descriptor 

## Experiment descriptor definition 
![](./images/ED.png)

## Experiment descriptor example

    {
	"Id": 123,
	"Name":"sfafd",
	"User": 123,
	"Platform": "malaga",
	"TestCases": ["TC1", "TC2"], 
	"UEs": ["UE1", "UE2"], 
	"Slice": "slice id", 
	"NS": "ns_id",
	"NS_Placement": "Edge",
	"Limited": true,
	"Type_experiment": false,
	"Scenario": ["scenario1", "scemarop2"], 
	"Application": ["app1"],
	"Attended": true, 
	"Reservation_time": 123 
    }    

## Try out the application
The Validator is available through the Dispatcher port (8082) and using the endpoint `/validator` with a POST method:

> curl -X POST -d @descriptor.json http://{dispatcher host}:8082/validator


## Next steps
- Control required fields that depend on the value of another field

## Authors
Javier Melian (javier.melian@atos.net)

## License

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   > http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


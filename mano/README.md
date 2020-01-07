# 5GENESIS MANO Wrapper

Standalone REST API part of 5Genesis' OSS for interactions with in the MANO.
This application uses the NFVO and VIM original API, bypassing security and abstracting the type of NVFO or VIM used to the user, that should not be aware of sensitive information but must use the functionalities of the underlying application.

The original documentation for the OSM API can be found [here](https://osm.etsi.org/wikipub/index.php/OSM_Scope_and_Functionality).

[OSM VNFD information model](http://osm-download.etsi.org/ftp/osm-doc/vnfd.html)

[OSM NSD information model](http://osm-download.etsi.org/ftp/osm-doc/nsd.html)

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Pre-requisites

For running the 5Genesis MANO wrapper you will need:

- docker version >= 18.09.6
- docker-compose version >= 1.17.1
- NFVO + VIM

### Config file

Modify the file `mano.conf` to adapt it to your testbed needs:

    [NFVO]
    TYPE=<type of NFVO. Currently only 'OSM' is supported>
    IP=<IP address of your NFVO>
    USER=<user name with admin rights within the NFVO>
    PASSWORD=<Password to the previous user>
    VIM_ACCOUNT=<Valid VIM account registered in your NFVO>
    
    [VIM]
    VIM_TYPE=<type of VIM. Currently only 'openstack' is supported>
    AUTH_URL=<VIM auth URL>
    USER=<VIM username>
    PASSWORD=<VIM username password>
    PROJECT=<VIM project>

#### Example

    [NFVO]
    TYPE=OSM
    IP=192.168.33.100
    USER=adminosm
    PASSWORD=*****
    VIM_ACCOUNT=MalagaOS_TestEnv
    
    [VIM]
    TYPE=openstack
    AUTH_URL=http://192.168.33.11:5000/v3
    USER=admin
    PASSWORD=**********
    PROJECT=admin

### Installation

`$ ./install.sh`

### Start

To start MANO wrapper, run:
`$ ./start.sh`

This will start your application on port 5001 along with a Swagger environment to test the API running on port 5002

### Stop

To stop MANO wrapper, run:
`$ ./stop.sh`

## Available features

![MANO Swagger](./images/MANO_swagger.PNG)

## Try out the application

You can find [here](https://osm-download.etsi.org/ftp/osm-6.0-six/7th-hackfest/packages/) examples of VNFD and NSD packages to populate and test the application

#### Examples on how to use it

You can test the API using your favorite REST client following these simple workflow:

- Insert a VNFD package:

    `curl -X POST -F "vnfd=@./<vnfd_package_file>" http://<host>:5001/vnfd`

    Result:

    >{"id": "VNFD_id_assigned_by_the_NFVO"}
- Insert a NSD package:

    `curl -X POST -F "nsd=@./<nsd_package_file>" http://<host>:5001/nsd`

    Result:

    >{"id": "NSD_id_assigned_by_the_NFVO"}
- List all available VNFDs:

    `curl -X GET "http://<host>:5001/vnfd" -H "accept: application/json"`

    Result:

    >List of available VNFDs in JSON format. (according to the NFVO information model)
- Retrieve an individual VNFD descriptor:

    `curl -X GET "http://<host>:5001/vnfd/<VNFD id>" -H "accept: application/json"`

    Result:

    >VNF descriptor in JSON format. (according to the NFVO information model)
- List all available NSDs:

    `curl -X GET "http://<host>:5001/nsd" -H "accept: application/json"`

    Result:

    >List of available NSDs in JSON format. (according to the NFVO information model)
- Retrieve an individual NSD descriptor:

    `curl -X GET "http://<host>:5001/NSd/<NSD id>" -H "accept: application/json"`

    Result:

    >NS descriptor in JSON format. (according to the NFVO information model)
- Delete an individual NSD:

    `curl -X DELETE "http://<host>:5001/nsd/<NSD _id>" -H "accept: application/json"`
- Delete an individual VNFD:

    `curl -X DELETE "http://<host>:5001/vnfd/<VNFD _id>" -H "accept: application/json"`

- Upload an image file in the VIM:

    `curl -X POST -F "image=@./<image_file>" http://<host>:5001/image?disk_format=<raw|qcow2>&container_format=bare`

    Result:

    >Image status: active

## Logs

Application logs are available in the application directory as `mano.log`

#### Example

    2019-11-13 17:26:42,678 -MANO API- INFO Validating VNFD hackfest_cloudinit_vnf.tar.gz
    2019-11-13 17:27:12,145 -MANO API- INFO Validating NSD file
    2019-11-13 17:27:12,155 -MANO API- INFO Unpacking file for validation
    2019-11-13 17:27:12,224 -MANO API- INFO Deleting temporary files
    2019-11-13 17:29:21,939 -MANO API- INFO Retrieving available VNFDs

## Versioning

- 1.0.0: First full stable version

## Bugs

- The NFVO sometimes does not include the "_id" field in the response when retrieving a descriptor, which is necessary for removing it. If this bug confirms, a *MANO Wrapper* database will be needed for storing such information associated to the descriptor "id".

## Authors

Javier Melian (javier.melian@atos.net)

## License

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   > <http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

# 5GENESIS Dispatcher

The 5GENESIS Dispatcher is the entry point to the system, offering the functionalities to an Experimenter through a single interface. These functionalites are know as the Open APIs, being able to interact with the key features of the underlying modules (as shown in the architecture diagram below) without actually exposing them
This implementation is based on a NGINX reverse proxy containerised in a Docker environment.

## Architecture
![](./images/dispatcher_arch.png)

## Available features
The available features will depend on the features exposed by each dispatched module. Stable features are:

##### MANO
- Onboard VNFD
- List VNFDs
- Retrieve single VNFD
- Delete VNFD
- Onboard NSD
- List NSDs
- Retrieve single NSD
- Delete NSD

##### ELCM
- Launch experiment (create)
- Cancel execution
- Get execution logs

##### Validator
- Validation service: Validate Experiment Descriptor as a standalone service
- Validate and onboard directly the Experiment Descriptor


## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Pre-requisites

For running the 5Genesis Dispatcher, you will need:
- docker version >= 18.09.6
- docker-compose version >= 1.17.1

### Config file and installation
The Dispatcher needs to be configured properly before it is deployed. For that a simplified configuration file is offered: `dispatcher.conf`, which will have to be edited and adapted.
The file contains information of all the modules the Dispatcher forwards information to and how to do it. It uses the following format:

    [module_name]
    protocol=[http|https]
    ip=x.x.x.x -> IP of the host component
    port=xxxx -> Port where the app API is available
    path=/ -> Base path of the application ("/" by default)

Once edited properly, the configuration should be applied and the containers deployed:
`$ ./install.sh`

#### Example
    [elcm]
    protocol=http
    ip=192.168.33.102
    port=4000
    path=/
    [validator]
    protocol=http
    ip=192.168.33.105
    port=5100
    path=/api
    [mano]
    protocol=http
    ip=192.168.33.105
    port=5001
    path=/
    
With the config file above, using the Validator as an example, the dispatcher will translate the original request to a new one:
> Original URL: http://192.168.33.105:5100/api/validate

> Translated URL: http://<dispatcher_ip>:<dispatcher:port>/validator/validate

### Start
The start script will deploy and run the Dispatcher container, the ED Validator and a Swagger environment to test the available features:

`$ ./start.sh`

### Stop
To stop the Dispatcher service just run the following: 

`$ ./stop.sh`

## Try out the application

## Next steps
- Improve the configuration file options
- Add user authentication and registration
- Add logging
- Add cross-platform features

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


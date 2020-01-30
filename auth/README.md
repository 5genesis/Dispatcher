# Auth

Auth is an API-REST in charge of manage the Authorization. Build under Python3.6 using Flak library and sqlite database.

## Features
Auth have the following  features for each rol:
- Users
  - User Registration
  - User LogIn
  - User Get  Token
  - User Change Password
  - User Recover password
- Admin
  - Register Platform in another platform
  - Show Users
  - Delete one User
  - Validate one User
  - Show Platforms
  - Validate Platform
  - Delete Platform
  - Drop Data Base

## Technologies
Pythhon 3.6 with dependencies:
```
jwcrypto
gevent
Flask
Flask-SQLAlchemy==2.1
requests
flask_mail
flask-cors
flask-restful
``` 
## File Structure
``` 
auth/                                   Main Folder
|
├─ swagger/                             Swagger Folder
|   └──swagger.json                     Swagger Specification
|
├─ templates/                           Folder for different templates
│   ├─ recover.html                     Recover password template
│   ├─ validate_platform.html           Validate platform template
|   └──validate_user.html               Validate users template
│ 
├─ auth.db                              SQL Database
├─ Auth.py                              Server
├─ auth_logic.py                        Service logic
├─ auth_utils.py                        Utils tools
├─ constants.py                         Constans file
├─ DB_Model.py                          Database Model
├─ DockerFile                           DockerFile for building the conatiner
├─ key.json                             Key for encrypt/desencrypt Tokens
├─ MailConfig.py                        Mail config
├─ requirements.txt                     Python  Dependencies
└─ settings.py                          Server settings
``` 

### Database Model
DB is defined in DB_Model.py and has the following structure:
![DB](./images/DB.PNG)
Once the DB is created, the Admin user is created, with username "Admin", password "Admin" and email "5genesismanagement@gmail.com", setted in the mail config.

There are 3 tables.
- For Role table we can found 3 attributes:
  - id   >>      Primary key
  - username >>  Foreign key to User table
  - rol_name >>  Rol in the system 
 - User table with 6 attributes:
   - id    >>     Primary key
   - username  >> Unique key to User
   - email  >> Unique in the system 
   - password >> Password for the user
   - active >> Account validated, true for validated, false for not.
   - deleted >> Account deleted by the users. But it persist for view the traces
  - Registry table with 5 attributes:
    - id    >>     Primary key
    - username  >> Foreign key to User table
    - action >> function requested by the User
    - data >> parameters for the request given
    - date >> timestamp with the exact time where the action was requested
### Email Config
Email config is defined in MailConfig.py

### Settings
Settings for the auth: 
- Loading the 'key.json' for encrypting and decrypting tokens.
- Setting the token timeout

## Install & Run
Auth is very easy to install and deploy in a Docker container.

By default, the Docker will expose port 2000, so change this within the Dockerfile if necessary. When ready, simply use the Dockerfile to build the image.

```sh
cd auth
docker build -t auth .
```
This will create the auth image and pull in the necessary dependencies.

Once done, run the Docker.


For run the image and map the port to whatever you wish on your host. 

```sh
sudo docker run -p 2000:2000 auth
```
The service will be exposed in port 2000.
## Sequence Diagrams

### User Registration
![User Registration](https://www.plantuml.com/plantuml/img/hLBDJiCm3BxtANm4QNk17j1sA18IuW3Y0KBYRa5DKiKEFs-FdTAYZY4uu4DbD_v-4dj7R3ANC3IDAPnY2K-O9RUSCZoIv5EwTy77fW69KG3U-j54XdtXOwEX1zeEswlwivsgZ0TFd0tx52ym63zieCX1D04tmaJqchAxhF3wCGF3pVKdsYKaY8a1tuG5V0G-8j0xCORQhQ5gi5LPjTX2LL6Kxxsjmj3B1LxCu9sKyR0WbsGbQgp5aT4jfrL4kIULhylDdJyOMvbJG0lTUMy-EYs5eGWbKL-6rSjzTum38NIt3ztopize_sHwxlm_qmlZMSiOtTh-gVKwM_fjk9ELEzc5EaYuFzMQTNGPTrB8IiC7)

### Password change
![Change pasword](https://www.plantuml.com/plantuml/img/ZL2x2W8n4Epp5LCgUDYd44LEEB0GH5k9kUWTv98ZsUZlcwmF41ktIFOnEpkxoqWgK1gi448byYuDPnEohya776BnnPWXlUv7vGYhH5rE2MGhPLGBpaciE-Mk1ZiLuzs7Tf9oTGQTGZ2EJkChFOCpzqyqPHv-b2Kq6ud6tPJjMoQVlyaOKQoCGbKjIbL-O-0yWNiPRMmqgBVxMkBu1-7t4jGPl3N2NpWk-_osFOLyD6ZkVobmRJxKCd_vldW0)

### Get Token
![Get Token](https://www.plantuml.com/plantuml/img/XO-z3i8m38HtFyMD856nPq1bAAXIDtxsq4OGaIPHui3hurGmu-byzdUosymwSPaTaIuSV9bl9eaUEIHSSjKKPSEEDchFs1T-Y4LrX6Qtz0f7m-VmD7vLnDuWwfpV8KrhqexH7nHw_zBEJXZ2tNh2jogCHb9gcaA5jpyMFZ0MY8pB1jrmwXIk_rEMGyZugPv9hGZv3Xy0)

### LogIn
![Get Token](https://www.plantuml.com/plantuml/img/XO-n3i8m34HtVyMD856nPq1bA5AbRXNieObAf3If4WT-7wV0ZAVpsUzajvbruh9u8bquXhBSRH8zSKouvgffbGqtkLK7nhdmGoog8pIdhLSOukp2heXtmAfpViLazgGzexyezE6flJEVBSAtAeb68cgKGeMFFnOXCZQ8hCyMtJ1s2hV_AJAShK31r2Ef5I6_uGq0)

### Change Password
![Change Password](https://www.plantuml.com/plantuml/img/ZL2x2W8n4Epp5LCgUDYd44LEEB0GH5k9kUWTv98ZsUZlcwmF41ktIFOnEpkxoqWgK1gi448byYuDPnEohya776BnnPWXlUv7vGYhH5rE2MGhPLGBpaciE-Mk1ZiLuzs7Tf9oTGQTGZ2EJkChFOCpzqyqPHv-b2Kq6ud6tPJjMoQVlyaOKQoCGbKjIbL-O-0yWNiPRMmqgBVxMkBu1-7t4jGPl3N2NpWk-_osFOLyD6ZkVobmRJxKCd_vldW0)

### Recover Password
![Recover Password](https://www.plantuml.com/plantuml/img/VL0nRiCm3DprYXlR8H_mK2HeNI10Xw15kZCsMmkG9KEYuk-NOf1c210E4day77dS5g4iTGxEYPV0s5MPyCb3EdF6WKfPKnvHuwYbJ8mtNnQIOUBig4gATJvfwcYGb74iBNUBIlh1BnJ5z1Hoq6XjR5uCw-w6FF5CFZmRy_PG4EpVE-pZcO8VOIJhjB1jDohPf3lqhOcO14Os6eV2w3---WxVZnGkIxrE57_Pd2vNy-d7wjhCFHoyUWKRDVBwR-koH1pr1blzzDJu0m00)

### Show registered users in the system
![Show registered users](https://www.plantuml.com/plantuml/img/VL2x2iCm3Dpp5RUN_426qXHI27Hf0ztTH1237y6MM_BtbPqXK6WzsDBfT2Vh55a5JjPKLQKIUvViauB48_k0ThBQIQLQXAH7lIZ7Q1FF0a5EgQC-5gp1CFitnXG22Ir52X47uAoY7hUktBDVoZ3wIuFUlPJHqqufqfAWpjBPezbovnc5MsXa8g6x3bs3np-1CjijKGWhUAQl2UK36OnhPB8_xUyK5-_4BtDBupQ2csGL9tbaXVW0)

### Drop users database
![Drop users DB](https://www.plantuml.com/plantuml/img/VL0n2iCm3DpzYjjBFk2XD2Kf1BeLkYk980R72RPSwE-hE8LChGVR9vtk95sIK9GyUsCCPLb2ddkE-XzaYQZ7sGNDhCfnWrif2EeiauOCz9GygdC9MZHnMJ6IK4-9SGAkbDomLspquo8lw6uMNNYHT-D1AQeAK6sgcxpTSLW4XLjexDMWlJzQY-S_WQCjcHWvSKpGZZUGtabu_cdQi6VXhriOTU2BFheeV000)

### Detele a single user from the database
![Delete user](https://www.plantuml.com/plantuml/img/VP312i8m38RlVOh_Bdk17cGJ9moy2Txh6bYXxKQR2hwzMIVi89f3cwHV_gHfCvl49NYbJE4vbl2W9Fx8Sq9dWujAgKKGDxh5H4PNU9AKWbXzHtEiIOqpUM92oPHm04uckt7ZLtW_Z6SC5uqXFertTaUgfWHeLirLN6znd1cLhHZvJEYljrxZ_a_WQoWPbYT2VZ65dmstWa-dQEMhhLoo8Rm1)

### Activate a single user from the database
![Activate user](https://www.plantuml.com/plantuml/img/JL2x3i8m3Dpp5HvR8NwW0se7n0X2m9wcgMhHEAXnGFmzJiBh9Z_ETxRRm7hXw6QbT6HFqVLsaTYmN-0S92vXDpWafMv2HeCtJGnTv4abW23tORt9rIPFmaNFE6X6Jz0_eQfssnCya2Su-Qkb6lP7g0xdTotA16bdLs-ff5FNMRiOIFxJxmpZNRCjHfdmmHzRwAdVmDPfd84yuuYcR3JAKKX3IYs4Q8mDOOmptBzBfyEAlw2rDCYNu0K0)

### Delete account
![Activate user](https://www.plantuml.com/plantuml/img/JKx13SCm2Fnx2XR80drKITKLEW0bI45AxCY6Tls2hKYz1phWZcDkYbNjs5D2qvBjU7DrJbegl5hmqmL2Sc9MM4ot5017h66wz-4DdhopCY1HCLT-HJTuO1CQfZ3q4js_gtcMV7XSwueBaJ9yZfdpwc_23m00)



## Authors

Luis Gómez (luis.gomez.external@atos.net)

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

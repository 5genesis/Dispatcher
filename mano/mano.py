import sys
sys.path.append('.')
from libs.osm_nbi_util import NbiUtil as osmUtils
from libs.openstack_util import OSUtils as osUtils
from flask import Flask, jsonify, request
from flask_restful import Resource, Api
import json
import yaml
import requests
from pymongo import MongoClient

from gevent.pywsgi import WSGIServer
import logging

from flask_cors import CORS



app = Flask(__name__)
api = Api(app)
CORS(app)

# Logging Parameters
logger = logging.getLogger("-MANO API-")
fh = logging.FileHandler('mano.log')

stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
stream_formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
fh.setFormatter(formatter)
stream_handler.setFormatter(stream_formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.addHandler(stream_handler)

from mano_2 import mano_cache
app.register_blueprint(mano_cache)

def reachable_interface(interface):
    """
    interface example:
    {
        "ns-vld-id": "public_vld",
        "ip-address": "192.168.100.101",
        "mac-address": "fa:16:3e:f6:11:7e",
        "name": "haproxy_vdu_eth1"
    }
    """
    import os
    ret = os.system("ping -n 3 {0}".format(interface["ip-address"]))
    if ret == 0:
        return True
    return False

def create_prometheus_target(ip="192.168.32.10", env="prod", target="localhost", port="9100", job="node",
                             service="test-service", service_id="T3SDavkl3pall9688g"):

    obj =\
        {
            "targets": ["{0}:{1}".format(target, port)],
            "labels": {
                "env": env,
                "job": job,
                "group": job,
                "service": service,
                "service_id": service_id
            }
        }
    print(obj)
    url = "http://{0}:5001/target".format(ip)
    headers = {"Accept": "application/json"}
    try:
        response = requests.post(url,
                                 headers=headers,
                                 verify=False,
                                 json=obj)
    except Exception as e:
        return {"error": str(e), "status": response.status_code}, response.status_code
    return json.loads(response.text), response.status_code


def send_prometheus_targets(ns_report):
    logger.info("Sending target to Prometheus to monitor the VDUs")
    for vdu in ns_report["interfaces"]:
        for interface in vdu["interfaces"]:
            if reachable_interface(interface):
                print("Interface {0} reachable: job: {1}, service: {2}, id: {3}".format(interface['ip-address'], interface["name"], ns_report["NS_name"], ns_report["NS_ID"]))
                create_prometheus_target(target=interface["ip-address"], job=interface["name"], service=ns_report["NS_name"], service_id=ns_report["NS_ID"])



class InstantiateNSD(Resource):
    def post(self, nsd_id):
        logger.info("Instantiating NSD: {}".format(nsd_id))
        response, status_code = nbiUtil.instantiate_by_nsd_id(nsd_id)
        # if the instantiation has been successful, we create the targets for monitoring the VDUs
        if status_code in [200, 201]:
            send_prometheus_targets(response)
        # TODO: hacer un rollback del servicio desplegado si no se ha completado todo el proceso
        return response, status_code


class NS_interfaces(Resource):
    def get(self, ns_id):
        logger.info("Retrieving interfaces for NS instance {}".format(ns_id))
        return nbiUtil.get_ns_interfaces_by_ns_id(ns_id)



class Prometheus(Resource):
    def post(self):
        input = request.get_json()
        print(str(request.remote_addr))
        return input


class VNFD_get(Resource):
    def get(self, vnf_name):
        logger.info("Retrieving VNFD: {}".format(vnf_name))
        return nbiUtil.get_vnfd_by_name(vnf_name)

    def delete(self, vnf_name):
        # vnf_name should be the _id for the VNFD in this case
        logger.info("Deleting VNFD: {}".format(vnf_name))
        return nbiUtil.delete_vnfd(vnf_name)

    def put(self, vnf_name):
        import os

        # vnf_name should be the _id for the VNFD in this case
        logger.info("Modifying VNFD: {}".format(vnf_name))
        try:
            file = request.files.get("vnfd")
            if not file:
                raise AttributeError("VNFD file not present in the query or wrong headers")
            logger.debug(file)
            # delete the old VNFD package
            r, status_code = nbiUtil.delete_vnfd(vnf_name)
            if status_code is 204:
                # the VNFD exists and was deleted successfully
                # Write package file to static directory
                file.save(file.filename)
                # upload the new package
                r, status_code = nbiUtil.upload_vnfd_package(file)
                os.remove(file.filename)
                logger.info("VNFD successfully modified")
            return r, status_code
        except AttributeError as ve:
            logger.error("Problem while getting the vnfd file: {}".format(str(ve)))
            return {"detail": str(ve), "code":"UNPROCESSABLE_ENTITY", "status": 422}, 422
        except Exception as e:
            return {"detail": str(e), "code": type(e).__name__, "status": 400}, 400


class VNFD(Resource):
    def post(self):
        import os

        try:
            file = request.files.get("vnfd")
            if not file:
                raise AttributeError("VNFD file not present in the query or wrong headers")
            logger.debug(file)
            # Write package file to static directory
            file.save(file.filename)
            r, status_code = nbiUtil.upload_vnfd_package(file)
            # Delete package file
            os.remove(file.filename)
            return r, status_code
        except AttributeError as ve:
            logger.error("Problem while getting the vnfd file: {}".format(str(ve)))
            return {"detail": str(ve), "code":"UNPROCESSABLE_ENTITY", "status": 422}, 422
        except Exception as e:
            return {"detail": str(e), "code": type(e).__name__, "status": 400}, 400
        


    def get(self):
        logger.info("Retrieving available VNFDs")
        r, code = nbiUtil.get_onboarded_vnfds()
        if r:
            logger.debug("VNFD list: {}".format(r))
        else:
            logger.error("Failed to retrieve VNFD list")
        return r, code


class NSD_get(Resource):
    def get(self, ns_name):
        logger.info("Retrieving NSD: {}".format(ns_name))
        r, code = nbiUtil.get_nsd_by_name(ns_name)
        if r:
            logger.debug("NSD: {}".format(r))
        else:
            logger.error("Failed to retrieve NSD")
        return r, code
        

    def delete(self, ns_name):
        logger.info("Deleting NSD: {}".format(ns_name))
        r, code = nbiUtil.delete_nsd(ns_name)
        if code is 204:
            logger.debug("NSD successfully deleted")
        else:
            logger.debug("NSD cannot be deleted: {} - {}".format(r, code))
        return r, code


    def put(self, ns_name):
        import os

        # vnf_name should be the _id for the VNFD in this case
        logger.info("Modifying NSD: {}".format(ns_name))
        try:
            file = request.files.get("nsd")
            if not file:
                raise AttributeError("VNFD file not present in the query or wrong headers")
            logger.debug(file)
            # delete the old NSD package
            r, status_code = nbiUtil.delete_nsd(ns_name)
            if status_code is 204:
                # the NSD exists and was deleted successfully
                # Write package file to static directory
                file.save(file.filename)
                # upload the new package
                r, status_code = nbiUtil.upload_nsd_package(file)
                os.remove(file.filename)
                logger.info("NSD successfully modified")
            return r, status_code
        except AttributeError as ve:
            logger.error("Problem while getting the nsd file: {}".format(str(ve)))
            return {"detail": str(ve), "code":"UNPROCESSABLE_ENTITY", "status": 422}, 422
        except Exception as e:
            return {"detail": str(e), "code": type(e).__name__, "status": 400}, 400



class NSD_post(Resource):
    def post(self):
        import os

        try:
            logger.info("Uploading NSD")
            file = request.files.get("nsd")
            if not file:
                raise AttributeError("VNFD file not present in the query or wrong headers")
            # Write package file to static directory and validate it
            file.save(file.filename)
            r, status_code = nbiUtil.upload_nsd_package(file)
            #print(status_code)
            # Delete package file when done with validation
            os.remove(file.filename)
            return r, status_code
        except AttributeError as ve:
            logger.error("Problem while getting the nsd file: {}".format(str(ve)))
            return {"detail": str(ve), "code":"UNPROCESSABLE_ENTITY", "status": 422}, 422
        except Exception as e:
            return {"detail": str(e), "code": type(e).__name__, "status": 400}, 400


    def get(self):
        logger.info("Retrieving available NSDs")
        r, code = nbiUtil.get_onboarded_nsds()
        logger.debug(r)
        return r, code


class VIM_image_post(Resource):
    def post(self, vim_name):
        import os
        vim = conf["VIM"][vim_name]
        # init the VIM
        logger.info("Adding VIM- Type: {}, Auth URL:{}, User:{}, Project:{}".format(vim["TYPE"], vim["AUTH_URL"], vim["USER"], vim["PROJECT"]))
        if vim["TYPE"] == "openstack":
            vim_conn = osUtils.connection(auth_url=vim["AUTH_URL"], region="RegionOne", project_name=vim["PROJECT"], username=vim["USER"], password=vim["PASSWORD"])
        else:
            raise KeyError("VIM type {} not supported".format(vim["TYPE"]))
        try:
            logger.info("Uploading image")
            file = request.files.get("image")
            if not file:
                raise AttributeError("Image file not present in the query or wrong headers")
            # Save file to static directory and validate it
            file.save(file.filename)

            # get image parameters
            disk_format = request.args.get('disk_format')
            container_format = request.args.get('container_format')

            r = osUtils.upload_image(vim_conn, file, disk_format, container_format)
            # Delete file when done with validation
            os.remove(file.filename)
        except KeyError as ke:
            logger.error("VIM type {} not supported".format(vim["TYPE"]))
            return {"detail": str(ve), "code":"NOT_ACCEPTABLE", "status": 406}, 406
        except AttributeError as ve:
            logger.error("Problem while getting the image file: {}".format(str(ve)))
            return {"detail": str(ve), "code":"UNPROCESSABLE_ENTITY", "status": 422}, 422
        except Exception as e:
            return {"detail": str(e), "code": type(e).__name__, "status": 400}, 400
        #osUtils.list_images(vim_conn) 
        return {"detail": "Image status: {}".format(r.status), "code": "CREATED", "status": 201}, 201


class VIM_list(Resource):
    def get(self):
        logger.info("Retrieving VIMs list")
        list = []
        try:
            for vim in conf["VIM"]:
                new_vim = {}
                new_vim["name"] = conf["VIM"][vim]["NAME"]
                new_vim["type"] = conf["VIM"][vim]["TYPE"]
                new_vim["location"] = conf["VIM"][vim]["LOCATION"]
                list.append(new_vim) 
        except Exception as e:
            return {"detail": str(e), "code": type(e).__name__, "status": 400}, 400
        logger.debug("VIMs list: {}".format(list))
        return list, 200


#api.add_resource(InstantiateNSD, '/instantiate_nsd/<string:nsd_id>')
#api.add_resource(NS_interfaces, '/get_interfaces/<string:ns_id>')
api.add_resource(VNFD_get, '/vnfd/<string:vnf_name>')
api.add_resource(VNFD, '/vnfd')
api.add_resource(NSD_post, '/nsd')
api.add_resource(NSD_get, '/nsd/<string:ns_name>')
api.add_resource(VIM_image_post, '/image/<string:vim_name>')
api.add_resource(VIM_list, '/vims')

api.add_resource(Prometheus, '/prometheus')


if __name__ == '__main__':
    from configobj import ConfigObj
    
    config_file = 'mano.conf'

    # load the NFVO parameters from the config file
    try:
        '''
        config format after reading the config file
        {
	"NFVO":{
		"TYPE":"xxx",
		"IP":"xxxx"
                ...
	},
	"VIM":{
		"vim-name-1":{
			"NAME":"vim-name-1",
			"TYPE":"openstack",
			"LOCATION":"core",
                        ...
		},
		"vim-name-2":{
			"NAME":"vim-name-2",
			"TYPE":"opennebula",
			"LOCATION":"edge",
                        ...
		}
	}
        }
        '''
        conf = ConfigObj(config_file)
        
        logger.info("Starting app")
        # init the NFVO
        logger.info("Adding NFVO- Type: {}, IP:{}, User:{}".format(conf["NFVO"]["TYPE"], conf["NFVO"]["IP"], conf["NFVO"]["USER"]))
        if conf["NFVO"]["TYPE"] == "OSM":
            nbiUtil = osmUtils(osm_ip=conf["NFVO"]["IP"], username=conf["NFVO"]["USER"], password=conf["NFVO"]["PASSWORD"], vim_account_id=None)
        else:
            logger.error("NFVO type {} not supported".format(conf["NFVO"]["TYPE"]))
            raise KeyError("NFVO type {} not supported".format(conf["NFVO"]["TYPE"]))
        #app.run(host='0.0.0.0', debug=True)
        http_server = WSGIServer(('', 5101), app)
        http_server.serve_forever()
    except KeyError as ex:
        logger.error("Config file {} badly formed: {}".format (config_file, ex.args))
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        logger.error(message)


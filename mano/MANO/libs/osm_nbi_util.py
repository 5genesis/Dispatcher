import os
import json
import time
import yaml

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
#Disable the InsecureRequestWarning for the requests to OSM
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)



def check_authorization(f):
    """
    Decorator to validate authorization prior API call
    """
    def wrapper(*args):
        response = requests.get(args[0].ns_descriptors_url,
                                headers=args[0].headers,
                                verify=False)
        if response.status_code == 401:
            args[0].new_token(args[0].username, args[0].password)
        return f(*args)
    return wrapper

class NbiUtil():
    """
    Class to interact with OSM API

    ...

    Attributes
    ----------
    none

    Methods
    -------
    get_osm_token()
        Gets the authorisation token for future requests
    """

    def __init__(self, username=None, password=None, project="admin", osm_ip=None,
                 vim_account_id=None):
        self.username = username
        self.password = password
        self.project = project
        self.osm_nbi_url = "https://" + osm_ip + ":9999/osm"
        self.vim_account_id = vim_account_id
        self.base_url = self.osm_nbi_url
        self.token_url = "{0}/admin/v1/tokens".format(self.base_url)
        self.instantiate_url = self.osm_nbi_url + "/nslcm/v1/ns_instances"
        self.ns_descriptors_url = "{0}/nsd/v1/ns_descriptors".format(self.base_url)
        self.vnf_descriptors_url = "{0}/vnfd/v1/vnf_descriptors".format(self.base_url)

        self.headers = {"Accept": "application/json"}

        self.token = None

    def new_token(self, username=None, password=None):
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password
        response = requests.post(self.token_url,
                                json={"username": self.username,
                                    "password": self.password},
                                headers=self.headers,
                                verify=False)
        token = json.loads(response.text).get("id")
        self.headers.update({"Authorization": "Bearer {0}".format(token)})
        return token


    @check_authorization
    def get_nsd(self, id=None):
        """
        Gets the list of NDSs in the OSM catalogue or a single one if specified

        Parameters
        ----------
        id: str, optional
            Id of a specific NSD(default is None)

        Raises
        ------
        Exception
            If there has been any errors in the request

        Returns
        ------
        NSDs list in json format : str
        token : str
        """

        url = self.ns_descriptors_url
        if id:
            url = url + "/" + str(id)
        headers = dict(self.headers)
        headers["Content-type"] = "application/yaml"
        try:
            r = requests.get(url, params=None, verify=False, stream=True, headers=headers)
        except Exception as e:
            print("ERROR - get_nsd: ", e)
            return e, type(e).__name__
        return r.text, r.status_code

    @check_authorization
    def get_nsd_by_name(self, name=None):
        """
        Gets the NSD in the OSM catalogue filtered by name

        Parameters
        ----------
        name: str, optional
            Id of a specific NSD(default is None)

        Raises
        ------
        Exception
            If there has been any errors in the request

        Returns
        ------
        NSDs list in json format : json object
        status code
        """
        if not name:
            return {}, 404
        url = self.ns_descriptors_url

        try:
            headers = dict(self.headers)
            headers["Content-type"] = "application/yaml"
            r = requests.get(url, params=None, verify=False, stream=True, headers=headers)
            nsd_list = json.loads(r.text)
            for nsd in nsd_list:
                if nsd["id"] == name:
                    return nsd, 200
        except Exception as e:
            print("ERROR - get_nsd: ", e)
            return e, type(e).__name__
        return [], 404


    @check_authorization
    def get_onboarded_nsds(self, id=None):
        """
        Gets the list of NDSs in the OSM catalogue or a single one if specified

        Parameters
        ----------
        id: str, optional
            Id of a specific NSD(default is None)

        Raises
        ------
        Exception
            If there has been any errors in the request

        Returns
        ------
        NSDs list in json format : json object
        status code
        """

        #print("INFO - Getting onboarded NSDs...")

        url = self.ns_descriptors_url
        if id:
            url = url + "/" + str(id)
        headers = dict(self.headers)
        headers["Content-type"] = "application/yaml"
        try:
            r = requests.get(url, params=None, verify=False, stream=True, headers=headers)
        except Exception as e:
            print("ERROR - get_onboarded_nsds: ", e)
            return e, type(e).__name__
        #print("INFO - NSDs query finalised")
        # print("\nNSD list: \n"+ r.text)
        return json.loads(r.text), r.status_code


    @check_authorization
    def get_onboarded_vnfds(self, filter=None):
        """
        Gets the list of VNF packages in the OSM catalogue

        Parameters
        ----------
        filter: str, optional (default is None)

        Raises
        ------
        Exception
            If there has been any errors in the request

        Returns
        ------
        VNF packages list in json format : json object
        status code
        """

        #print("INFO - Getting onboarded VNFDs...")

        result = {'error': True, 'data': ''}
        query_path = ''
        if filter:
            query_path = '?_admin.type=' + filter
        url = "{0}/vnfpkgm/v1/vnf_packages_content{1}".format(self.osm_nbi_url, query_path)
        headers = dict(self.headers)
        headers["Content-type"] = "application/json"
        try:
            r = requests.get(url, params=None, verify=False, stream=True, headers=headers)
            if r.status_code == requests.codes.ok:
                result['error'] = False
        except Exception as e:
            print("ERROR - get_onboarded_vnfds: ", e)
            return e, type(e).__name__
        print("INFO - VNFDs list successfully retrieved")
        # print("\nVNFD list: \n" + r.text)
        return json.loads(r.text), 200


    @check_authorization
    def get_vnfd(self, id):
        """
        Gets a particular VNFD identified by its id assigned by OSM

        Parameters
        ----------
        id: str
            OSM id of a specific VNFD (example: d308cd9b-81f3-4b5f-a9ac-77f399daa3f8)

        Raises
        ------
        Exception
            If there has been any errors in the request

        Returns
        ------
        VNFD in json format : json object
        status code
        """

        #print("INFO - Getting VNFD with id: ", id)

        url = "{0}/vnfpkgm/v1/vnf_packages/{1}/vnfd".format(self.osm_nbi_url, id)
        headers = dict(self.headers)
        headers["Accept"] = "text/plain"
        try:
            r = requests.get(url, params=None, verify=False, stream=True, headers=headers)
            if r.status_code == requests.codes.ok:
                #print("INFO - VNFD %s successfully retrieved" % id)
                vnfd = yaml.load(r.text)
                return vnfd, r.status_code
                if 'vnfd-catalog' in vnfd:
                    return vnfd['vnfd-catalog'], r.status_code
                if 'vnfd:vnfd-catalog' in vnfd:
                    return vnfd['vnfd:vnfd-catalog'], r.status_code
        except Exception as e:
            print("ERROR - get_vnfd: ", e)
            return e, type(e).__name__
        return r.text, r.status_code


    @check_authorization
    def get_vnfd_by_name(self, vnfd_name):
        """
        Gets a particular VNFD identified by its id assigned by the user

        Parameters
        ----------
        id: str
            User assigned OSM id of a specific VNFD (example: hackfest1-vnf)

        Raises
        ------
        Exception
            If there has been any errors in the request

        Returns
        ------
        VNFD in json format : str
        status code
        """

        #print("INFO - Getting VNFDs with name: ", vnfd_name)

        vnfd_list_url = "{0}/vnfpkgm/v1/vnf_packages_content".format(self.osm_nbi_url)
        headers = dict(self.headers)
        headers["Accept"] = "application/json"
        try:
            r1 = requests.get(vnfd_list_url, params=None, verify=False, stream=True, headers=headers)
            for vnfd in json.loads(r1.text):
                if (vnfd['id'] == vnfd_name):
                    #print("\n VNFD: {} - {} - ID: {}".format(vnfd['id'], vnfd_name, vnfd['_id']))
                    vnfd, status_code = self.get_vnfd(vnfd['_id'])
                    return vnfd, status_code
        except Exception as e:
            print("ERROR - get VNFD: ", e)
            return {"error": str(e), "status": type(e).__name__}
            #return r1.text, r1.status_code
        #print("INFO - The VNFD with name %s does not exist" % vnfd_name)
        return "VNFD not found", 404


    @check_authorization
    def upload_vnfd_package(self, file):
        """
        Onboards a VNFD package

        Parameters
        ----------
        file: 

        Raises
        ------
        Exception
            If there has been any errors in the request

        Returns
        ------
        ID of the VNFD package generated by OSM: json object
        status code
        """

        #print("INFO - Uploading VNFD: ", file.filename)
        if not os.path.exists(file.filename):
            return "File '{}' does not exist".format(file.filename), 404
        data = open(file.filename, 'rb').read()

        vnfd_url = "{0}/vnfpkgm/v1/vnf_packages_content".format(self.osm_nbi_url)

        headers = dict(self.headers)
        headers["Accept"] = "application/json"
        headers["Content-type"] = "application/gzip"
        try:
            r = requests.post(vnfd_url, params=None, verify=False, stream=True, data=data, headers=headers)
            return r.text, r.status_code
        except Exception as e:
            print("ERROR - post VNFD: ", e)
            return r.text, r.status_code


    @check_authorization
    def delete_vnfd(self, id):
        """
        Deletes a particular VNFD identified by its id assigned by OSM

        Parameters
        ----------
        id: str
            OSM id of a specific VNFD (example: d308cd9b-81f3-4b5f-a9ac-77f399daa3f8)

        Raises
        ------
        Exception
            If there has been any errors in the request

        Returns
        ------
        status code
        """

        #print("INFO - Deleting VNFD with id: ", id)

        #url = "{0}/vnfpkgm/v1/vnf_packages_content/{1}".format(self.osm_nbi_url, id)
        url = "{0}/vnfpkgm/v1/vnf_packages/{1}".format(self.osm_nbi_url, id)
        headers = dict(self.headers)
        headers["Accept"] = "application/json"
        headers["Content-type"] = "application/yaml"
        try:
            r = requests.delete(url, params=None, verify=False, stream=True, headers=headers)
            if r.status_code == requests.codes.ok:
                print("INFO - VNFD %s successfully deleted" % id)
        except Exception as e:
            print("ERROR - delete_vnfd: ", e)
            return e, type(e).__name__
        return yaml.load(r.text), r.status_code


    @check_authorization
    def upload_nsd_package(self, file):
        """
        Onboards a NSD package

        Parameters
        ----------
        file: 

        Raises
        ------
        Exception
            If there has been any errors in the request

        Returns
        ------
        ID of the NSD package generated by OSM: json object
        status code
        """

        #print("INFO - Uploading NSD: ", file.filename)
        if not os.path.exists(file.filename):
            return "File '{}' does not exist".format(file.filename), 404
        data = open(file.filename, 'rb').read()

        nsd_url = "{0}/nsd/v1/ns_descriptors_content".format(self.osm_nbi_url)

        headers = dict(self.headers)
        headers["Accept"] = "application/json"
        headers["Content-type"] = "application/gzip"
        try:
            r = requests.post(nsd_url, params=None, verify=False, stream=True, data=data, headers=headers)
            return r.text, r.status_code
        except Exception as e:
            print("ERROR - post NSD: ", e)
            return r.text, r.status_code


    @check_authorization
    def delete_nsd(self, id):
        """
        Deletes a particular NS identified by its id assigned by OSM

        Parameters
        ----------
        id: str
            OSM id of a specific NSD (example: d308cd9b-81f3-4b5f-a9ac-77f399daa3f8)

        Raises
        ------
        Exception
            If there has been any errors in the request

        Returns
        ------
        status code
        """

        #print("INFO - Deleting NSD with id: ", id)

        url = "{0}/nsd/v1/ns_descriptors_content/{1}".format(self.osm_nbi_url, id)
        headers = dict(self.headers)
        headers["Accept"] = "application/json"
        headers["Content-type"] = "application/yaml"
        try:
            r = requests.delete(url, params=None, verify=False, stream=True, headers=headers)
            if r.status_code == requests.codes.ok:
                print("INFO - NSD %s successfully deleted" % id)
        except Exception as e:
            print("ERROR - delete_nsd: ", e)
            return e, type(e).__name__
        return yaml.load(r.text), r.status_code


    @check_authorization
    def update_vnfd(self, id):
        """
        Updates a particular VNFD package identified by its id assigned by OSM

        Parameters
        ----------
        id: str
            OSM id of a specific VNFD package (example: d308cd9b-81f3-4b5f-a9ac-77f399daa3f8)

        Raises
        ------
        Exception
            If there has been any errors in the request

        Returns
        ------
        status code
        """

        #print("INFO - Updating VNFD with id: ", id)

        #url = "{0}/vnfpkgm/v1/vnf_packages_content/{1}".format(self.osm_nbi_url, id)
        url = "{0}/vnfpkgm/v1/vnf_packages/{1}".format(self.osm_nbi_url, id)
        headers = dict(self.headers)
        headers["Accept"] = "application/json"
        headers["Content-type"] = "application/json"
        try:
            r = requests.patch(url, params=None, verify=False, stream=True, headers=headers)
            if r.status_code == requests.codes.ok:
                print("INFO - VNFD %s successfully updated" % id)
        except Exception as e:
            print("ERROR - update_vnfd: ", e)
            return e, type(e).__name__
        return r.json(), r.status_code



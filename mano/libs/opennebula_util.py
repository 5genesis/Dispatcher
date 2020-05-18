  
"""
Copyright 2019 Atos
Contact: Javier Melián <javimelian@gmail.com>
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
    
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import pyone
import functools
from multiprocessing import Process
import logging
#File transfer imports
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient

# Logging Parameters
logger = logging.getLogger("ONE")
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
stream_formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
fh = logging.FileHandler('one.log')
fh.setFormatter(formatter)
stream_handler.setFormatter(stream_formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.addHandler(stream_handler)


def timeout(func):
    """
    Wrapper for function, terminate after 5 seconds
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        action = Process(target=func, args=args, kwargs=kwargs)
        action.start()
        action.join(timeout=5)
        if action.is_alive():
            # terminate function
            action.terminate()
            # clean up
            action.join()
            raise (TimeoutError)
        # if process is not 0, is not successful
        if action.exitcode != 0:
            # raise Attribute Error, which is the most probable
            raise (AttributeError)
    return (wrapper)


def ssh_scp_files(ssh_host, ssh_user, ssh_password, source_volume, destination_volume, ssh_port=22):
    """

    """
    logger.info("Transfering file {} to the server".format(source_volume))
    try:
        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect(ssh_host, username=ssh_user, password=ssh_password, look_for_keys=False)
        with SCPClient(ssh.get_transport()) as scp:
            scp.put(source_volume, recursive=True, remote_path=destination_volume)
        logger.info("File transfered")
    except Exception as e:
        logger.exception("Failure while transfering the file to the server: {}".format(str(e)))
    ssh.close()

def delete_remote_file(ssh_host, ssh_user, ssh_password, path, ssh_port=22):
    """

    """
    logger.info("Deleting cached file")
    try:
        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect(ssh_host, username=ssh_user, password=ssh_password, look_for_keys=False)
        sftp = ssh.open_sftp()
        logger.debug("path: {}".format(path))
        sftp.remove(path)
        logger.info("File deleted")
    except Exception as e:
        logger.exception("Failure while cached file: {}".format(str(e)))
    ssh.close()

class Opennebula():
    """
    Class implementing the communication API with OpenNebula
    """
    # Note: Cannot use conn as a self variable, as it is not possible to
    # serialize it and store it in a db

    def __init__(self, uuid, auth_url, project_name, username, password):
        """
        Initialize an object of the class
        """
        self.uuid = uuid
        self.auth_url = auth_url
        self.project_name = project_name
        self.username = username
        self.password = password
        
        conn = pyone.OneServer(
            self.auth_url,
            session="{0}:{1}".format(username, password)
            )

    def create_project(self, conn, name, description=""):
        """
        Creates a new OpenNebula group
        """
        group = conn.group.allocate(name, description)
        # returns Project object
        return group

    def create_user(self, conn, name, password, group):
        """
        Creates a new openstack project
        """
        user = conn.user.allocate(name, password, "", [group])
        return user

    def create_sec_group(self, conn, name, project):
        """
        Creates the security group to be assigned to the new tenant
        """
        sec_group = conn.create_security_group(
            name=name, description="Security Group",
            project_id=project.id)
        conn.create_security_group_rule(sec_group)
        return sec_group

    def delete_user(self, conn, user_id):
        """
        Deletes the user
        """
        try:
            return conn.user.delete(user_id)
        except pyone.OneNoExistsException as e:
            logger.exception("Failed. Trying to delete user: doesn't exist - ", user_id)
        except Exception as e:
            logger.exception("Failed. Trying to delete user: ", user_id)

    def delete_user_by_name(self, conn, name):
        """
        Deletes the user
        """
        userpool = conn.userpool.info(-1, -1, -1)
        for user in userpool.USER:
            if user.get_NAME() == name:
                return conn.user.delete(user.get_ID())

    def delete_project(self, conn, group_id):
        """
        Deletes the group
        """
        try:
            return conn.group.delete(group_id)
        except pyone.OneNoExistsException as e:
            logger.exception("Failed. Trying to delete group: doesn't exist - ", group_id)
        except Exception as e:
            logger.exception("Failed. Trying to delete group: ", group_id)

    def delete_project_by_name(self, conn, name):
        """
        Deletes the group
        """
        grouppool = conn.grouppool.info(-1, -1, -1)
        for group in grouppool.GROUP:
            if group.get_NAME() == name:
                return conn.group.delete(group.get_ID())

    def delete_proj_user(self, user_id):
        """
        Deletes user and project
        """
        conn = pyone.OneServer(
            self.auth_url,
            session="{0}:{1}".format(self.username, self.password)
            )
        try:
            user = conn.user.info(user_id)
            group = user.get_GROUPS().ID[0]
            # delete group
            conn.group.delete(group)
            # delete user
            return conn.user.delete(user.get_ID())
        except pyone.OneNoExistsException as e:
            logger.exception("Failed. User trying to delete, doesn't exist: ", user_id)
        except Exception as e:
            logger.exception("Failed. User trying to delete, group doesn't exist: ", user_id)

    def delete_proj_user_by_name(self, name):
        """
        Deletes user and project
        """
        conn = pyone.OneServer(
            self.auth_url,
            session="{0}:{1}".format(self.username, self.password)
            )
        userpool = conn.userpool.info(-1,-1,-1)
        for user in userpool.USER:
            if user.get_NAME() ==  name:
                group = user.get_GROUPS()[0]
                # delete group
                conn.group.delete(group)
                # delete user
                return conn.user.delete(user.get_ID())
        logger.warning("Delete user ONE: user does not exist: ", name)

    def create_slice_prerequisites(self, tenant_project_name,
                                   tenant_project_description,
                                   tenant_project_user,
                                   tenant_project_password,
                                   slice_uuid):
        """
        Creates the tenant (project, user, security_group) on the specified vim
        """
        conn = pyone.OneServer(
            self.auth_url,
            session="{0}:{1}".format(self.username, self.password)
            )
        # creates the project in OpenNebula
        project = self.create_project(conn, tenant_project_name,
                                      tenant_project_description)

        # creates the user
        user = self.create_user(conn, tenant_project_user, "password", project)

        # creates the security group and rules
        # sec_group = self.create_sec_group(conn, tenant_project_name, project)
        sec_group = "dummy"

        return {"sliceProjectName": project, "sliceUserName": user,
                "secGroupName": sec_group}


    def upload_image (auth_url, one_username, one_password, f, server_ip, server_username, server_password, image_dir, ssh_port=22, image_type = "OS"):
        """
        Transfers the image file to the ONE server and registers it to the ONE
        """
        import os

        try:
            ssh_scp_files(server_ip, server_username, server_password, f.filename, image_dir, ssh_port)

            # sife of the file in bytes
            size = os.path.getsize(f.filename)
            # convert to MB
            size = int(size/(1024*1024))

            # Resgister the image
            conn = pyone.OneServer(
                auth_url,
                session="{0}:{1}".format(one_username, one_password)
                )
            name, file_extension = os.path.splitext(f.filename)
            description = f.filename
            source = image_dir + f.filename
    
            # find the default datastore
            dsid = 0
            datastores = conn.datastorepool.info()
            for ds in datastores.DATASTORE:
                if ds.NAME == "default":
                    dsid = ds.ID
                    break

            # creation of the image template and registration
            template='''\nNAME="%s"\nSOURCE="%s"\nTYPE="%s"\nDESCRIPTION="%s"\nSIZE="%d"''' % \
                     (name, source, image_type, description, size*3)
            logger.debug("template: {}".format(template))
            r = conn.image.allocate(template,dsid)
            delete_remote_file(server_ip, server_username, server_password, str(image_dir + f.filename), ssh_port)
        except Exception as e:
            logger.exception("Failed uploading image: {}".format(str(e)))



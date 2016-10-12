# VM based authorization for docker volumes
# Copyright 2016 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License

""" VM based authorization for docker volumes and tenant management.

"""

import sqlite3
import uuid
import os
import vmdk_utils
import vmdk_ops
import logging
import auth_data_const
 
class DbConnectionError(Exception):
    """ An exception thrown when connection to a sqlite database fails. """

    def __init__(self, db_path):
        self.db_path = db_path

    def __str__(self):
        return "DB connection error %s" % self.db_path

class DockerVolumeTenant:
    """ This class abstracts the operations to manage a DockerVolumeTenant.

    The interfaces it provides include:
    - add VMs to tenant
    - revmove VMs from tenant
    - change tenant name and description
    - set datastore and privileges for a tenant

    """

    def __init__(self, name, description, default_datastore, default_privileges,
                    vms, privileges, id=None):
            """ Constuct a DockerVOlumeTenant object. """
            self.name = name
            self.description = description
            self.default_datastore = default_datastore
            self.default_privileges = default_privileges
            self.vms = vms
            self.privileges = privileges
            if not id:
                self.id = str(uuid.uuid4())
            else:
                self.id = id
        
    def add_vms(self, conn, vms):
        """ Add vms in the vms table for this tenant. """
        tenant_id = self.id
        vms = [(vm_id, vm_name, tenant_id) for (vm_id, vm_name) in vms]
        if vms:
            try:
                conn.executemany(
                  "INSERT INTO vms(vm_id, vm_name, tenant_id) VALUES (?, ?, ?)",
                  vms
                )
                conn.commit()
            except sqlite3.Error, e:
                logging.error("Error %s when insert into vms table with vm_id %s vm_name %s"
                "tenant_id %s", e, vm_id, vm_name, tenenat_id)
                 

    def remove_vms(self, conn, vms):
        """ Remove vms from the vms table for this tenant. """
        tenant_id = self.id
        vms = [(vm_id, tenant_id) for (vm_id, vm_name) in vms]
        try:
            conn.executemany(
                    "DELETE FROM vms WHERE vm_id=? AND tenant_id=?", 
                    vms
            )
            conn.commit()
        except sqlite3.Error, e:
            logging.error("Error %s when remove from vms table with vm_id %s tenant_id"
                "tenant_id %s", e, vm_id,tenenat_id)

    def set_name(self, conn, name):
        """ Set name column in tenant table for this tenant. """
        tenant_id = self.id
        try:
            conn.execute(
                    "UPDATE tenants SET name=? WHERE id=?", 
                    (name, tenant_id)
            )
            conn.commit()
        except sqlite3.Error, e:
            logging.error("Error %s when update tenants table with tenant_id"
                "tenant_id %s", e, tenenat_id)

    
    def set_description(self, conn, description):
        """ Set description column in tenant table for this tenant. """
        tenant_id = self.id
        try:
            conn.execute(
                    "UPDATE tenants SET description=? WHERE id=?", 
                    (description, tenant_id)
             )
            conn.commit()
        except sqlite3.Error, e:
            logging.error("Error %s when update tenants table with tenant_id"
                "tenant_id %s", e, tenenat_id)
        
    def set_default_datastore_and_privileges(self, conn, datastore, privileges):
        "Set default_datastore and default privileges for this tenant."
        tenant_id = self.id
        exist_default_datastore = self.default_datastore
        try:
            conn.execute(
                    "UPDATE tenants SET default_datastore=? WHERE id=?", 
                    (datastore, tenant_id)
            )

            # remove the old entry
            conn.execute(
                    "DELETE FROM privileges WHERE tenant_id=? AND datastore=?", 
                    [tenant_id, exist_default_datastore]
            )

            for p in privileges:
                p[auth_data_const.TENANT_ID] = tenant_id
            conn.executemany(
                """
                INSERT INTO privileges VALUES
                (:tenant_id, :datastore, :global_visibility, :create_volume,
                :delete_volume, :mount_volume, :max_volume_size, :usage_quota)
                """,
                privileges
            )

            conn.commit()
        except sqlite3.Error, e:
            logging.error("Error %s when setting dafault dtastore and privileges for tenant_id %s", 
                          e, tenant_id)

            
    def set_datastore_access_privileges(self, conn, privileges):
        """ Set datastore and privileges for this tenant.

            "privileges"" is an array of dict
            each dict represent a privilege that the tenant has for a given datastore

            Example:
            privileges = [{'datastore': 'datastore1',
                           'global_visibility': 0,
                           'create_volume': 0,
                           'delete_volume': 0,
                           'mount_volume': 1,
                           'max_volume_size': 0,
                           'usage_quota': 0},
                          {'datastore': 'datastore2',
                           'global_visibility': 0,
                           'create_volume': 1,
                           'delete_volume': 1,
                           'mount_volume': 1,
                           'max_volume_size': 0,
                           'usage_quota': 0}]
        
        """
        tenant_id = self.id
        for p in privileges:
            p[auth_data_const.TENANT_ID] = tenant_id
                            
        try:
            conn.executemany(
                """
                INSERT OR IGNORE INTO privileges VALUES
                (:tenant_id, :datastore, :global_visibility, :create_volume,
                :delete_volume, :mount_volume, :max_volume_size, :usage_quota)
                """,
                privileges
            )
            
            for p in privileges:
                # privileges ia an array of dict
                # each dict represent a privilege that the tenant has for a given datastore
                # for each dict, add a new element which maps 'tenant_id' to tenant_id 
                p[auth_data_const.TENANT_ID] = tenant_id
                column_list = ['tenant_id', 'datastore', 'global_visibility', 'create_volume',
                                'delete_volume', 'mount_volume', 'max_volume_size', 'usage_quota']
                update_list = []
                update_list = [p[col] for col in column_list]    
                update_list.append(tenant_id)
                update_list.append(p[auth_data_const.DATASTORE])    
                
                logging.debug("set_datastore_access_privileges: update_list %s", update_list)

                conn.execute(
                    """
                    UPDATE OR IGNORE privileges SET
                        tenant_id =?, 
                        datastore=?, 
                        global_visibility=?,
                        create_volume=?,
                        delete_volume=?,
                        mount_volume=?,
                        max_volume_size=?,
                        usage_quota=?
                    WHERE tenant_id=? AND datastore=?
                    """,
                    update_list
                )
            conn.commit()
        except sqlite3.Error, e:
            logging.error("Error %s when setting datastore and privileges for tenant_id %s", 
                          e, tenant_id)

class AuthorizationDataManager:
    """ This class abstracts the creation, modification and retrieval of
    authorization data used by vmdk_ops as well as the VMODL interface for
    Docker volume management.

    init arg:
    The constructor of this class take "db_path" as an argument.
    "db_path" specify the path of sqlite3 database
    If caller does not pass the value of this argument, function "get_auth_db_path"
    will be called to figure out the value
    otherwise, the value passed by caller will be used

    """

    def __init__(self, db_path=None):
        if not db_path:
            self.db_path = self.get_auth_db_path()
        else:
            self.db_path = db_path
        self.conn = None

    def __del__(self):
        if self.conn:
            self.conn.close()
    
    def get_auth_db_path(self):
        """ Return the path of authorization database.

        DB tables should be stored in VSAN datastore
        DB file should be stored under /vmfs/volume/VSAN_datastore/
        See issue #618
        Currently, it is hardcoded.

        """
        path = '/tmp/test-auth.db'
        return path

    def connect(self):
        """ Connect to a sqlite database file given by `db_path`. 
        
        Ensure foreign key
        constraints are enabled on the database and set the return type for
        select operations to dict-like 'Rows' instead of tuples.

        Raises a ConnectionFailed exception when connect fails.

        """
        self.conn = sqlite3.connect(self.db_path)

        # Return rows as Row instances instead of tuples
        self.conn.row_factory = sqlite3.Row

        if not self.conn:
            raise DbConnectionError(self.db_path)

    def create_tables(self):
        """ Create tables used for per-datastore authorization.  
        
        This function should only be called once per datastore.  
        It will raise an exception if the schema file isn't 
        accessible or the tables already exist.

        """
        with open('./docker-volume-auth-schema.sql') as f:
            sql = f.read()
            self.conn.executescript(sql)
            self.conn.commit()

    def create_tenant(self, name, description, default_datastore, default_privileges, 
                      vms, privileges):
        """ Create a tenant in the database. 
        
        A tenant id will be auto-generated and returned. 
        vms are (vm_id, vm_name) pairs. Privileges are dictionaries
        with keys matching the row names in the privileges table. Tenant id is
        filled in for both the vm and privileges tables.

        """

        # Create the entry in the tenants table
        tenant = DockerVolumeTenant(name, description, default_datastore,
                                    default_privileges, vms, privileges)
        id = tenant.id

        try:
            self.conn.execute(
                "INSERT INTO tenants(id, name, description, default_datastore) VALUES (?, ?, ?, ?)",
                (id, name, description, default_datastore)
            )

            # Create the entries in the vms table
            vms = [(vm_id, vm_name, id) for (vm_id, vm_name) in vms]
                
            if vms:
                self.conn.executemany(
                "INSERT INTO vms(vm_id, vm_name, tenant_id) VALUES (?, ?, ?)",
                vms
                )

            # Create the entries in the privileges table
            # TODO: data scrubbing, ensure all keys exist
            for p in default_privileges:
                p[auth_data_const.TENANT_ID] = id
            self.conn.executemany(
                """
                INSERT INTO privileges VALUES
                (:tenant_id, :datastore, :global_visibility, :create_volume,
                :delete_volume, :mount_volume, :max_volume_size, :usage_quota)
                """,
                default_privileges
            )

            for p in privileges:
                p[auth_data_const.TENANT_ID] = id
            self.conn.executemany(
                """
                INSERT INTO privileges VALUES
                (:tenant_id, :datastore, :global_visibility, :create_volume,
                :delete_volume, :mount_volume, :max_volume_size, :usage_quota)
                """,
                privileges
            )
            self.conn.commit()
        except sqlite3.Error, e:
            logging.error("Error %s when setting datastore and privileges for tenant_id %s", 
                          e, tenant_id)    
        return tenant
    
    def list_tenants(self):
        """ Return a list of DockerVolumeTenants objects. """
        tenant_list = []
        try:
            cur = self.conn.execute(
            "SELECT * FROM tenants"
            )
            result = cur.fetchall()
        
            for r in result:
                # loop through each tenant
                id = r[auth_data_const.ID]
                name = r[auth_data_const.NAME]
                description = r[auth_data_const.DESCRIPTION]
                default_datastore = r[auth_data_const.DEFAULT_DATASTORE]
                
                # search vms for this tenant
                vms = []
                cur = self.conn.execute(
                    "SELECT * FROM vms WHERE tenant_id = ?",
                    (id,)
                )
                vms = cur.fetchall()
                
                # search privileges and default_privileges for this tenant
                privileges = []
                cur = self.conn.execute(
                    "SELECT * FROM privileges WHERE tenant_id = ? AND datastore != ?",
                    (id,default_datastore)    
                )
                privileges = cur.fetchall()

                default_privileges = []
                cur = self.conn.execute(
                    "SELECT * FROM privileges WHERE tenant_id=? AND datastore=?",
                    (id,default_datastore)    
                )
                default_privileges = cur.fetchall()
                tenant = DockerVolumeTenant(name, description, default_datastore,
                                            default_privileges, vms, privileges, id)
                tenant_list.append(tenant)
        except sqlite3.Error, e:    
            logging.error("Error %s when listting all tenants", e)

        return tenant_list   
    
    def remove_volumes_from_volume_table(self, tenant_id):
        """ Remove all volumes from volumes table. """
        try:
            self.conn.execute(
                    "DELETE FROM volumes WHERE tenant_id=?",  
                    [tenant_id]
            )

            self.conn.commit()
        except sqlite3.Error, e:
            logging.error("Error %s when removing volumes from volumes table for tenant_id %s",
                          e, tenant_id)
    
    def _remove_volumes_for_tenant(self, tenant_id):
        """ Delete all volumes belongs to this tenant.

            Do not use it outside of removing a tenant.

        """
        try:
            cur = self.conn.execute(
            "SELECT name FROM tenants WHERE id=?",
            (tenant_id,)
            )
            result = cur.fetchone()
        except sqlite3.Error, e:
            logging.error("Error %s when querying from tenants table", e)

        logging.debug("remove_volumes_for_tenant: %s %s", tenant_id, result)
        tenant_name = result[0]
        vmdks = vmdk_utils.get_volumes(tenant_name)
        # Delete all volumes for this tenant. 
        dir_path = None
        for vmdk in vmdks:
            vmdk_path = os.path.join(vmdk['path'], "{0}".format(vmdk['filename']))
            if not dir_path:
                dir_path = vmdk['path']
            print("path=%s filename=%s", vmdk['path'], vmdk['filename'])    
            logging.debug("Deleting volume path%s", vmdk_path)
            err = vmdk_ops.removeVMDK(vmdk_path)
            if err:
                logging.error("remove vmdk %s failed with error %s", vmdk_path, err)
        
        # Delete path /vmfs/volumes/datastore_name/tenant_name
        logging.debug("Deleting dir path%s", dir_path)
        # TODO:
        # "rm -rf" only work for VMFS
        # Need to figure out how to remove dir in vSAN 

        #RM_DIR_CMD = "rm -rf "
        #cmd = "{0} {1}".format(RM_DIR_CMD, dir_path)
        #rc, out = RunCommand(cmd)
        #if rc != 0:
        try:
            os.rmdir(dir_path)
        except os.error as e:
            logging.error("remove dir %s failed with error %s", dir_path, e)
                
        self.remove_volumes_from_volume_table(tenant_id)

    def remove_tenant(self, tenant_id, remove_volumes):
        """ Remove a tenant with given id.

            A row with given tenant_id will be removed from table tenants, vms, 
            and privileges.
            All the volumes created by this tenant will be removed if remove_volumes
            is set to True. 

        """
        if remove_volumes:
            self._remove_volumes_for_tenant(tenant_id)

        try:
            self.conn.execute(
                    "DELETE FROM vms WHERE tenant_id=?", 
                    [tenant_id]
            )

            self.conn.execute(
                    "DELETE FROM privileges WHERE tenant_id=?", 
                    [tenant_id]
            )
            self.conn.execute(
                    "DELETE FROM tenants WHERE id=?", 
                    [tenant_id]
            )

            self.conn.commit()
        except sqlite3.Error, e:
            logging.error("Error %s when removing tables", e)
  
   

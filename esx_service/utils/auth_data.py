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

"""
VM based authorization for docker volumes and tenant management.

"""

import sqlite3
import uuid
import os
import vmdk_utils
import vmdk_ops
import logging

 
class DbConnectionError(Exception):
    """ An exception thrown when connection to a sqlite database fails """

    def __init__(self, db_path):
        self.db_path = db_path

    def __str__(self):
        return "DB connection error %s" % self.db_path

class DockerVolumeTenant:
    """
    This class abstracts the operations to manage a DockerVolumeTenant
    The interfaces it provides include:
    - add VMs to tenant
    - revmove VMs from tenant
    - change tenant name and description
    - set datastore and privileges for a tenant

    """

    def __init__(self, name, description, default_datastore, default_privileges,
                    vms, privileges, id=None):
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
        
    def add_vms_to_tenant(self, conn, vms):
        tenant_id = self.id
        vms = [(vm_id, vm_name, tenant_id) for (vm_id, vm_name) in vms]
        if vms:
            conn.executemany(
              "insert into vms(vm_id, vm_name, tenant_id) values (?, ?, ?)",
              vms
            )
        conn.commit()

    def remove_vms_from_tenant(self, conn, vms):
        tenant_id = self.id
        vms = [(vm_id, tenant_id) for (vm_id, vm_name) in vms]
        conn.executemany(
                "delete from vms where vm_id=? AND tenant_id=?", 
                vms
        )
        conn.commit()

    def set_name(self, conn, name):
        tenant_id = self.id
        conn.execute(
                "update tenants set name=? where id=?", 
                (name, tenant_id)
        )
        conn.commit()
    
    def set_description(self, conn, description):
        tenant_id = self.id
        conn.execute(
                "update tenants set description=? where id=?", 
                (description, tenant_id)
            )
        conn.commit()
        
    def set_default_datastore_and_privileges(self, conn, datastore, privileges):
        tenant_id = self.id
        exist_default_datastore = self.default_datastore
        conn.execute(
                "update tenants set default_datastore=? where id=?", 
                (datastore, tenant_id)
        )

        # remove the old entry
        conn.execute(
                "delete from privileges where tenant_id=? and datastore=?", 
                [tenant_id, exist_default_datastore]
        )

        for p in privileges:
            p['tenant_id'] = tenant_id
        conn.executemany(
            """
            insert into privileges values
            (:tenant_id, :datastore, :global_visibility, :create_volume,
            :delete_volume, :mount_volume, :max_volume_size, :usage_quota)
            """,
            privileges
        )

        conn.commit()
            
    def set_datastore_access_privileges(self, conn, privileges):
        # If we want to change privileges for <tenant1, ds1> and <tenant2, ds2>
        # Do we call this function one time or two times?
        tenant_id = self.id
        for p in privileges:
            p['tenant_id'] = tenant_id
                            
        conn.executemany(
            """
            insert or ignore into privileges values
            (:tenant_id, :datastore, :global_visibility, :create_volume,
            :delete_volume, :mount_volume, :max_volume_size, :usage_quota)
            """,
            privileges
        )
        
        for p in privileges:
            p['tenant_id'] = tenant_id
            column_list = ['tenant_id', 'datastore', 'global_visibility', 'create_volume',
                            'delete_volume', 'mount_volume', 'max_volume_size', 'usage_quota']
            update_list = []
            for col in column_list:
                update_list.append(p[col])
            update_list.append(tenant_id)
            update_list.append(p['datastore'])    
            
            #print update_list

            conn.execute(
                """
                update or ignore privileges set
                tenant_id =?, 
                datastore=?, 
                global_visibility=?,
                create_volume=?,
                delete_volume=?,
                mount_volume=?,
                max_volume_size=?,
                usage_quota=?
                where tenant_id=? and datastore=?
                """,
                update_list
            )
        conn.commit()

class AuthorizationDataManager:
    """
    This class abstracts the creation, modification and retrieval of
    authorization data used by vmdk_ops as well as the VMODL interface for
    Docker volume management.

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
        """
        DB tables should be stored in VSAN datastore
        DB file should be stored under /vmfs/volume/VSAN_datastore/
        Currently, it is hardcoded

        """
        path = '/tmp/test-auth.db'
        return path

    def connect(self):
        """
        Connect to a sqlite database file given by `db_path`. Ensure foreign key
        constraints are enabled on the database and set the return type for
        select operations to dict-like 'Rows' instead of tuples.

        Raises a ConnectionFailed exception of
        """
        self.conn = sqlite3.connect(self.db_path)

        # Return rows as Row instances instead of tuples
        self.conn.row_factory = sqlite3.Row

        if not self.conn:
            raise DbConnectionError(self.db_path)

    def create_tables(self):
        """
        Create the 3 tables used for per-datastore authorization.  This function
        should only be called once per datastore.  It will raise an exception if
        the schema file isn't accessible or the tables already exist.
        """
        
        with open('./docker-volume-auth-schema.sql') as f:
            sql = f.read()
            self.conn.executescript(sql)
            self.conn.commit()

    def create_tenant(self, name, description, default_datastore, default_privileges, 
                      vms, privileges):
        """
        Create a tenant in the database. A tenant id will be auto-generated and
        returned. vms are (vm_id, vm_name) pairs. Privileges are dictionaries
        with keys matching the row names in the privileges table. Tenant id is
        filled in for both the vm and privileges tables.
        """

        # Create the entry in the tenants table
        tenant = DockerVolumeTenant(name, description, default_datastore,
                                    default_privileges, vms, privileges)
        id = tenant.id
        self.conn.execute(
            "insert into tenants(id, name, description, default_datastore) values (?, ?, ?, ?)",
            (id, name, description, default_datastore)
        )

        # Create the entries in the vms table
        vms = [(vm_id, vm_name, id) for (vm_id, vm_name) in vms]
        #print vms
        if vms:
            self.conn.executemany(
              "insert into vms(vm_id, vm_name, tenant_id) values (?, ?, ?)",
              vms
            )

        # Create the entries in the privileges table
        # TODO: data scrubbing, ensure all keys exist
        for p in default_privileges:
            p['tenant_id'] = id
        self.conn.executemany(
            """
            insert into privileges values
            (:tenant_id, :datastore, :global_visibility, :create_volume,
             :delete_volume, :mount_volume, :max_volume_size, :usage_quota)
            """,
            default_privileges
        )

        for p in privileges:
            p['tenant_id'] = id
        self.conn.executemany(
            """
            insert into privileges values
            (:tenant_id, :datastore, :global_visibility, :create_volume,
             :delete_volume, :mount_volume, :max_volume_size, :usage_quota)
            """,
            privileges
        )
        self.conn.commit()
        return tenant
    
    def list_tenants(self):
        """
            Return a list of DockerVolumeTenants objects.
        """
        tenant_list = []
        cur = self.conn.execute(
           "select * from tenants"
        )
        result = cur.fetchall()
       
        for r in result:
            # loop through each tenant
            id = r['id']
            name = r['name']
            description = r['description']
            default_datastore = r['default_datastore']
            
            # search vms for this tenant
            vms = []
            cur = self.conn.execute(
                "select * from vms where tenant_id=?",
                (id,)
            )
            vms = cur.fetchall()
            
            # search privileges and default_privileges for this tenant
            privileges = []
            cur = self.conn.execute(
                "select * from privileges where tenant_id=? and datastore!=?",
                (id,default_datastore)    
            )
            privileges = cur.fetchall()

            default_privileges = []
            cur = self.conn.execute(
                "select * from privileges where tenant_id=? and datastore=?",
                (id,default_datastore)    
            )
            default_privileges = cur.fetchall()
            tenant = DockerVolumeTenant(name, description, default_datastore,
                                        default_privileges, vms, privileges, id)
            tenant_list.append(tenant)

        return tenant_list   
    
    def remove_volumes_from_volume_table(self, tenant_id):
          
        self.conn.execute(
                "delete from volumes where tenant_id=?", 
                [tenant_id]
        )

        self.conn.commit()
    
    def remove_volumes_for_tenant(self, tenant_id):
        cur = self.conn.execute(
           "select * from tenants where id=?",
           (tenant_id,)
        )
        result = cur.fetchone()
        logging.debug("remove_volumes_for_tenant: %s %s", tenant_id, result)
        tenant_name = result['name']
        vmdks = vmdk_utils.get_volumes(tenant_name)
        # Delete all volumes for this tenant. 
        # Do we need to remove the path /vmfs/volumes/datastore_name/tenant_name??
        for vmdk in vmdks:
            vmdk_path = vmdk['path']+"/"+vmdk['filename']
            logging.debug("Deleting volume path%s", vmdk_path)
            err = vmdk_ops.removeVMDK(vmdk_path)
            if err:
                logging.error("remove vmdk %s failed with error %s", vmdk_path, err)
        
        self.remove_volumes_from_volume_table(tenant_id)

    def remove_tenant(self, tenant_id, remove_volumes):
        """
            Remove a tenant with given id
            A row with given tenant_id will be removed from table tenants, vms, 
            and privileges
            All the volumes created by this tenant will be removed if remove_volumes
            is set to True 
        """
        if remove_volumes:
            self.remove_volumes_for_tenant(tenant_id)

        self.conn.execute(
                "delete from tenants where id=?", 
                [tenant_id]
        )

        self.conn.execute(
                "delete from vms where tenant_id=?", 
                [tenant_id]
        )

        self.conn.execute(
                "delete from privileges where tenant_id=?", 
                [tenant_id]
        )

        self.conn.commit()
  
   

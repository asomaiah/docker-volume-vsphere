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
# limitations under the License.

""" Module to provide APIs for authorization checking for VMDK ops.

"""
import random
import logging
import auth_data
import os
import convert
import auth_data_const

# All supported vmdk commands
CREATE = 'create'
REMOVE = 'remove'
LIST = 'list'
GET = 'get'
ATTACH = 'attach'
DETACH = 'detach'

SIZE = 'size'

_auth_mgr = None
def connect_auth_db():
    """ Get a connection to auth DB. """
    global _auth_mgr
    if not _auth_mgr:
        _auth_mgr = auth_data.AuthorizationDataManager()
        _auth_mgr.connect()
       
def get_tenant(vm_uuid):
    """ Get tenant which owns this VM by querying the auth DB. """
    global _auth_mgr
    try:
        cur = _auth_mgr.conn.execute(
                    "SELECT tenant_id FROM vms WHERE vm_id=?",
                    (vm_uuid,)
        )
        result = cur.fetchone()
    except sqlite3.Error, e:
        logging.error("Error %s when querying from vms table for vm_id %s", e, vm_uuid)
    if result:
        logging.debug("get tenant vm_uuid=%s tenant_id=%s", vm_uuid, result[0])
   
    tenant_uuid = None
    tenant_name = None
    if result:
        tenant_uuid = result[0]
        try:
            cur = _auth_mgr.conn.execute(
                    "SELECT name FROM tenants WHERE id=?",
                    (tenant_uuid,)
            )
            result = cur.fetchone()
        except sqlite3.Error, e:
            logging.error("Error %s when querying from tenants table for tenant_id %s", e, tenant_uuid)

        if result:
            tenant_name = result[0]
            logging.debug("Found tenant_uuid %s, tenant_name", tenant_uuid, tenant_name)

    return tenant_uuid, tenant_name

def get_privileges(tenant_uuid, datastore):
    """ Return privileges for given (tenant_uuid, datastore) pair by
        querying the auth DB.

    """
    global _auth_mgr
    privileges = []
    logging.debug("get_privileges tenant_uuid=%s datastore=%s", tenant_uuid, datastore)
    try:
        cur = _auth_mgr.conn.execute(
                    "SELECT * FROM privileges WHERE tenant_id=? and datastore=?",
                    (tenant_uuid,datastore)    
        )
        privileges = cur.fetchone()
    except sqlite3.Error, e:
        logging.error("Error %s when querying privileges table for tenant_id %s and datastore %s", 
                      e, tenant_uuid, datastore)
    return privileges

def has_privilege(privileges, type):
    """ Check the privileges has the specific type of privilege set. """
    logging.debug(privileges)
    if not privileges:
        return False
    logging.debug("%s=%d", type, privileges[type])
    return privileges[type]

def get_vol_size(opts):
    """ get volume size. """
    if not opts or not opts.has_key(SIZE):
        logging.error("Volume size not specified")
    return opts[SIZE]    


def check_max_volume_size(opts, privileges):
    """ Check wheter the size of the volume to be created exceeds
        the max volume size specified in the privileges.

    """
    vol_size_in_MB = convert.convert_to_MB(get_vol_size(opts))
    max_vol_size_in_MB = privileges[auth_data_const.MAX_VOLUME_SIZE]
    return vol_size_in_MB <= max_vol_size_in_MB

def get_total_storage_used(tenant_uuid, datastore):
    """ Return total storage used by (tenant_uuid, datastore)
        by querying auth DB.

    """
    total_storage_used = 0
    try:
        cur = _auth_mgr.conn.execute(
                    "SELECT SUM(volume_size) FROM volumes WHERE tenant_id=? and datastore=?",
                    (tenant_uuid,datastore)    
        )
    except sqlite3.Error, e:
        logging.error("Error %s when querying storage table for tenant_id %s and datastore %s", 
                      e, tenant_uuid, datastore)
    result = cur.fetchone()
    if result:
        if result[0]:
            total_storage_used = result[0]
            logging.debug("total storage used for (tenant %s datastore %s) is %s MB", tenant_uuid, 
                          datastore, total_storage_used)         
        return total_storage_used

def check_usage_quota(opts, tenant_uuid, datastore, privileges):
    """ Check if the volume can be created without violating the quota. """
    vol_size_in_MB = convert.convert_to_MB(get_vol_size(opts))
    total_storage_used = get_total_storage_used(tenant_uuid, datastore)
    usage_quota = privileges[auth_data_const.USAGE_QUOTA]
    return vol_size_in_MB + total_storage_used <= usage_quota

def check_privileges_for_command(cmd, opts, tenant_uuid, datastore, privileges):
    """
        Check whether the (tenant_uuid, datastore) has the privileges to run 
        the given command.

    """
    result = None
    cmd_need_mount_privilege = [LIST, GET, ATTACH, DETACH]
    if cmd in cmd_need_mount_privilege:
        if not has_privilege(privileges, MOUNT_VOLUME):
            result = "No mount privilege"
    
    if cmd == CREATE:
        if not has_privilege(privileges, CREATE_VOLUME):
            result = "No create privilege"
        if not check_max_volume_size(opts, privileges):
            result = "volume size exceeds the max volume size limit"
        if not check_usage_quota(opts, tenant_uuid, datastore, privileges):
            result = "The total volume size exceeds the usage quota"        
    
    if cmd == REMOVE:
        if not has_privilege(privileges, DELETE_VOLUME):
            result = "No delete privilege"
            
    return result        

def tables_exist():
    """ Check tables needed for authorization exist or not. """
    global _auth_mgr

    try:
        cur = _auth_mgr.conn.execute("SELECT name FROM sqlite_master WHERE type='table' and name='tenants';")
        result = cur.fetchall()
    except sqlite3.Error, e:
        logging.error("Error %s when check wheter table tenants exist or not", e)

    if not result:
        logging.debug("table tenants does not exist")
        return False
    
    try:
        cur = _auth_mgr.conn.execute("SELECT name FROM sqlite_master WHERE type='table' and name='vms';")
        result = cur.fetchall()
    except sqlite3.Error, e:
        logging.error("Error %s when check wheter table vms exist or not", e)

    if not result:
        logging.debug("table vms does not exist")
        return False

    try:
        cur = _auth_mgr.conn.execute("SELECT name FROM sqlite_master WHERE type='table' and name='privileges';")
        result = cur.fetchall()
    except sqlite3.Error, e:
        logging.error("Error %s when check wheter table privileges exist or not", e)

    if not result:
        logging.debug("table privileges does not exist")
        return False
    
    try:
        cur = _auth_mgr.conn.execute("SELECT name FROM sqlite_master WHERE type='table' and name='volumes';")
        result = cur.fetchall()
    except sqlite3.Error, e:
        logging.error("Error %s when check wheter table volumes exist or not", e)

    if not result:
        logging.debug("table volumes does not exist")
        return False
    
    return True

def authorize(vm_uuid, datastore, cmd, opts):
    """ Check whether the command can be run on this VM.

        Return value: result, tenant_uuid, tenant_name

        - result: return None if the command can be run on this VM, otherwise, return 
        corresponding error message
        - tenant_uuid: If the VM belongs to a tenant, return tenant_uuid, otherwise, return
        None
        - tenant_name: If the VM belongs to a tenant, return tenant_name, otherwise, return 
        None

    """
    logging.debug("Authorize: vm_uuid=%s", vm_uuid)
    logging.debug("Authorize: datastore=%s", datastore)
    logging.debug("Authorize: cmd=%s", cmd)
    logging.debug("Authorize: opt=%s", opts)

    connect_auth_db()

    # If table "tenants", "vms", "privileges" or "volumes" does not exist
    # don't need auth check
    if not tables_exist():
        logging.debug("Required tables in auth db do not exist")
        return None, None, None

    tenant_uuid, tenant_name = get_tenant(vm_uuid)
    if not tenant_uuid:
        # This VM does not associate any tenant, don't need auth check
        logging.debug("VM %s does not belong to any tenant", vm_uuid)
        return None, None, None
    else:
        privileges = get_privileges(tenant_uuid, datastore)
        result = check_privileges_for_command(cmd, opts, tenant_uuid, datastore, privileges)

    return result, tenant_uuid, tenant_name

def add_volume_to_volumes_table(tenant_uuid, datastore, vol_name, vol_size_in_MB):
    """ Insert volume to volumes table. """
    logging.debug("add to volumes table(%s %s %s %s)", tenant_uuid, datastore,
                  vol_name, vol_size_in_MB)
    try:              
        _auth_mgr.conn.execute(
                    "INSERT INTO volumes(tenant_id, datastore, volume_name, volume_size) VALUES (?, ?, ?, ?)",
                    (tenant_uuid, datastore, vol_name, vol_size_in_MB)    
        )
    except sqlite3.Error, e:
        logging.error("Error %s when insert into volumes table for tenant_id %s and datastore %s", 
                      e, tenant_uuid, datastore)

    _auth_mgr.conn.commit()
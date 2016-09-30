import random
import logging
import auth_data
import os

auth_mgr = None
def connect_auth_db():
    global auth_mgr
    if not auth_mgr:
        db_path = os.path.join(auth_data.get_auth_db_path())
        auth_mgr = auth_data.AuthorizationDataManager(db_path)
        auth_mgr.connect()
       
def find_tenant_by_vm(vm_uuid):
    """
        Find tenant which owns this VM by querying the auth DB
    """
    global auth_mgr
    cur = auth_mgr.conn.execute(
                "select * from vms where vm_id=?",
                (vm_uuid,)
    )
    tenant_uuid = None
    tenant_name = None
    result = cur.fetchone()
    if result:
        tenant_uuid = result[2]
        cur = auth_mgr.conn.execute(
                "select * from tenants where id=?",
                (tenant_uuid,)
        )
        result = cur.fetchone()
        if result:
            tenant_name = result[1]
            logging.debug("Found tenant_uuid %s, tenant_name", tenant_uuid, tenant_name)

    return tenant_uuid, tenant_name

def find_privileges_by_tenant_and_datastore(tenant_uuid, datastore):
    """
        Return privileges for given (tenant_uuid, datastore) pair by
        querying the auth DB 
    """
    global auth_mgr
    privileges = []
    logging.debug("find_privileges tenant_uuid=%s datastore=%s", tenant_uuid, datastore)
    cur = auth_mgr.conn.execute(
                "select * from privileges where tenant_id=? and datastore=?",
                (tenant_uuid,datastore)    
    )
    privileges = cur.fetchone()
    return privileges

def has_mount_privilege(privileges):
    logging.debug(privileges)
    if not privileges:
        return False
    logging.debug("mount_volume=%d", privileges['mount_volume'])
    return privileges['mount_volume']

def has_create_privilege(privileges):
    logging.debug(privileges)
    if not privileges:
        return False
    logging.debug("create_volume=%d", privileges['create_volume'])
    return privileges['create_volume']   

def has_delete_privilege(privileges):
    logging.debug(privileges)
    if not privileges:
        return False
    logging.debug("delete_volume=%d", privileges['delete_volume'])
    return privileges['delete_volume']

"""
    For a given size string, return values in MB.
    Example:
    '100MB': return 100
    '100GB': return 100*1024
"""
def convert_to_MB(vol_size_str):
    unit = vol_size_str[-2:]
    value = int(vol_size_str[:-2])
    convertions = {'MB' : 1,
                   'GB' : 1024,
                   'TB' : 1024*1024,
                   'PB' : 1024*1024*1024,
    }
    
    if unit.upper() in convertions.keys():
        value = value*convertions[unit]
    else:
        logging.error("Invalid volume size")
    return value  

def get_vol_size(opts):
    if not opts:
        logging.error("Volume size does not specified")
    return opts['size']    

"""
    Check wheter the size of the volume to be created exceeds
    the max volume size specified in the privileges
"""
def check_max_volume_size(opts, privileges):
    vol_size_in_MB = convert_to_MB(get_vol_size(opts))
    max_vol_size_in_MB = privileges['max_volume_size']
    return vol_size_in_MB <= max_vol_size_in_MB

"""
    Return total storage used by (tenant_uuid, datastore)
    by querying auth DB    
"""
def get_total_storage_used(tenant_uuid, datastore):
    total_storage_used = 0
    cur = auth_mgr.conn.execute(
                "select * from volumes where tenant_id=? and datastore=?",
                (tenant_uuid,datastore)    
    )
    volumes = cur.fetchall()
    for volume in volumes:
        # volume[3] is the volume_size filed in the volume table
        total_storage_used = total_storage_used+volume[3]

    logging.debug("taotal storage used for (tenant %s datastore %s) is %s MB", tenant_uuid, 
                  datastore, total_storage_used)         
    return total_storage_used

"""
    Check whether total storage used by this (tenant_uuid, datastore) pair exceed
    the usage_quota in the privileges if creating this volume    
"""
def check_usage_quota(opts, tenant_uuid, datastore, privileges):
    vol_size_in_MB = convert_to_MB(get_vol_size(opts))
    total_storage_used = get_total_storage_used(tenant_uuid, datastore)
    usage_quota = privileges['usage_quota']
    return vol_size_in_MB+total_storage_used <= usage_quota

"""
    Check whether the (tenant_uuid, datastore) has the privileges to run the given command
"""
def check_privileges_for_command(cmd, opts, tenant_uuid, datastore, privileges):
    result = None
    cmd_need_mount_privilege = ['list', 'get', 'attach', 'detach']
    if cmd in cmd_need_mount_privilege:
        if not has_mount_privilege(privileges):
            result = "no mount privilege"
    
    if cmd == 'create':
        if not has_create_privilege(privileges):
            result = "no create privilege"
        if not check_max_volume_size(opts, privileges):
            result = "volume size exceeds the max volume size limit"
        if not check_usage_quota(opts, tenant_uuid, datastore, privileges):
            result = "The total volume size exceeds the usage quota"        
    
    if cmd == 'remove':
        if not has_delete_privilege(privileges):
            result = "no delete privilege"
            
    return result        

"""
    Check whether the command can be run on this VM
    Return value: result, tenant_uuid, tenant_name
    result: return None if the command can be run on this VM, otherwise, return 
    corresponding error message
    tenant_uuid: If the VM belongs to a tenant, return tenant_uuid, otherwise, return
    None
    tenant_name: If the VM belongs to a tenant, return tenant_name, otherwise, return 
    None  
"""
def authorize(vm_uuid, datastore, cmd, opts):
   #return random.choice([None, 'Some error msg'])
   logging.debug("Authorize: vm_uuid=%s", vm_uuid)
   logging.debug("Authorize: datastore=%s", datastore)
   logging.debug("Authorize: cmd=%s", cmd)
   logging.debug("Authorize: opt=%s", opts)

   connect_auth_db()
   tenant_uuid, tenant_name = find_tenant_by_vm(vm_uuid)
   if not tenant_uuid:
       # This VM does not associate any tenant, don't need auth check
       return None, None, None
   else:
       privileges = find_privileges_by_tenant_and_datastore(tenant_uuid, datastore)
       result = check_privileges_for_command(cmd, opts, tenant_uuid, datastore, privileges)

   return result, tenant_uuid, tenant_name

def add_volume_to_volumes_table(tenant_uuid, datastore, vol_name, vol_size_in_MB):
    logging.debug("add to volumes table(%s %s %s %s)", tenant_uuid, datastore,
                  vol_name, vol_size_in_MB)
    auth_mgr.conn.execute(
                "insert into volumes(tenant_id, datastore, volume_name, volume_size) values (?, ?, ?, ?)",
                (tenant_uuid, datastore, vol_name, vol_size_in_MB)    
    )

    auth_mgr.conn.commit()
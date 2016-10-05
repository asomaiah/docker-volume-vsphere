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

# Tests for auth.py

import unittest
import os
import os.path
import auth_data
import uuid

class TestAuthDataModel(unittest.TestCase):
    """
    Test the Authorization data model via the AuthorizationDataManager
    """
    db_path = "/tmp/test-auth.db"
    
    def setUp(self):
        
        try:
            os.unlink(self.db_path)
        except:
            pass
            
        self.auth_mgr = auth_data.AuthorizationDataManager(self.db_path)
        self.auth_mgr.connect()
        self.auth_mgr.create_tables()

    def tearDown(self):
        os.unlink(self.db_path)
    def get_privileges(self):
        privileges = [{'datastore': 'datastore1',
                     'global_visibility': 0,
                      'create_volume': 0,
                      'delete_volume': 0,
                     'mount_volume': 0,
                      'max_volume_size': 0,
                      'usage_quota': 0}]
        return privileges
    
    def get_default_datastore_and_privileges(self):
        default_datastore = 'default_ds'
        default_privileges = [{'datastore': default_datastore,
                              'global_visibility': 0,
                              'create_volume': 0,
                              'delete_volume': 0,
                              'mount_volume': 0,
                              'max_volume_size': 0,
                              'usage_quota': 0}]
        return default_datastore, default_privileges

    def test_create_tenant(self):
        vms = [(str(uuid.uuid4()), 'vm1')]
        
        #privileges = []
        privileges = self.get_privileges()
        default_datastore, default_privileges = self.get_default_datastore_and_privileges()
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant1.id))
        
        vms = []
        privileges = []
        tenant2 = self.auth_mgr.create_tenant('tenant2', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant2.id))
      
    def test_add_vms_to_tenant(self): 
        vms = []
        privileges = []
        default_datastore, default_privileges = self.get_default_datastore_and_privileges()
        
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant1.id))
            
        vms = [(str(uuid.uuid4()), 'vm1'), (str(uuid.uuid4()), 'vm2')]
        tenant1.add_vms_to_tenant(self.auth_mgr.conn, vms)
    
    def test_remove_vms_from_tenant(self):
        vms = [(str(uuid.uuid4()), 'vm1')]
        
        privileges = self.get_privileges()
        default_datastore, default_privileges = self.get_default_datastore_and_privileges()
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)

        vms = [(str(uuid.uuid4()), 'vm2')]
        tenant2 = self.auth_mgr.create_tenant('tenant2', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant2.id))

        vms = [(str(uuid.uuid4()), 'vm3'), (str(uuid.uuid4()), 'vm4')]
        tenant3 = self.auth_mgr.create_tenant('tenant3', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant3.id))

        tenant3.remove_vms_from_tenant(self.auth_mgr.conn, vms)
    
    def test_set_name(self):
        vms = [(str(uuid.uuid4()), 'vm1')]
        
        privileges = self.get_privileges()
        default_datastore, default_privileges = self.get_default_datastore_and_privileges()
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant1.id))

        tenant1.set_name(self.auth_mgr.conn, 'new_tenant1')

    
    def test_set_description(self):
        vms = [(str(uuid.uuid4()), 'vm1')]
        
        privileges = self.get_privileges()
        default_datastore, default_privileges = self.get_default_datastore_and_privileges()
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant1.id))
        tenant1.set_description(self.auth_mgr.conn, 'new description')
    
    def test_set_default_datastore_and_privileges(self):
        vms = [(str(uuid.uuid4()), 'vm1')]
        
        privileges = self.get_privileges()
        default_datastore, default_privileges = self.get_default_datastore_and_privileges()
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant1.id))

        default_datastore = 'new_default_ds'
        default_privileges = [{'datastore': default_datastore,
                              'global_visibility': 0,
                              'create_volume': 1,
                              'delete_volume': 1,
                              'mount_volume': 1,
                              'max_volume_size': 0,
                              'usage_quota': 0}]
        tenant1.set_default_datastore_and_privileges(self.auth_mgr.conn, default_datastore, default_privileges)                              

    
    def test_add_datastore_access_privileges(self):
        vms = [(str(uuid.uuid4()), 'vm1')]
        privileges = []
        
        default_datastore, default_privileges = self.get_default_datastore_and_privileges()
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant1.id))
        
        vms = [(str(uuid.uuid4()), 'vm2')]
        privileges = []
        tenant2 = self.auth_mgr.create_tenant('tenant2', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant2.id))
        
        privileges = [{'datastore': 'datastore1',
                       'global_visibility': 0,
                       'create_volume': 0,
                       'delete_volume': 0,
                       'mount_volume': 0,
                       'max_volume_size': 0,
                       'usage_quota': 0}]

        tenant1.set_datastore_access_privileges(self.auth_mgr.conn, privileges)

        privileges = [{'datastore': 'datastore1',
                        'global_visibility': 0,
                        'create_volume': 1,
                        'delete_volume': 1,
                        'mount_volume': 0,
                        'max_volume_size': 0,
                        'usage_quota': 0}]
        
        tenant1.set_datastore_access_privileges(self.auth_mgr.conn, privileges)
    

    def test_list_tenants(self):
        vms = [(str(uuid.uuid4()), 'vm1')]
        privileges = []
        default_datastore, default_privileges = self.get_default_datastore_and_privileges()
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant1.id))
        
        vms = [(str(uuid.uuid4()), 'vm2'), (str(uuid.uuid4()), 'vm3')]
        privileges = []
        tenant2 = self.auth_mgr.create_tenant('tenant2', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant2.id))
        
        privileges = [{'datastore': 'datastore1',
                       'global_visibility': 0,
                       'create_volume': 0,
                       'delete_volume': 0,
                       'mount_volume': 0,
                       'max_volume_size': 0,
                       'usage_quota': 0}]

        tenant1.set_datastore_access_privileges(self.auth_mgr.conn, privileges)
        tenants_list = self.auth_mgr.list_tenants()
        for tenant in tenants_list:
            print "Tenant Info Start"
            print tenant.name
            print tenant.description
            print tenant.default_datastore
            print tenant.default_privileges
            print tenant.vms
            print tenant.privileges
            print "Tenant Info End"
            
    
    def test_remove_tenants(self):
        vms = [(str(uuid.uuid4()), 'vm1')]
        
        privileges = self.get_privileges()
        default_datastore, default_privileges = self.get_default_datastore_and_privileges()
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant1.id))
        
        vms = [(str(uuid.uuid4()), 'vm2'), (str(uuid.uuid4()), 'vm3')]
        privileges = []
        tenant2 = self.auth_mgr.create_tenant('tenant2', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant2.id))
  
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

        tenant2.set_datastore_access_privileges(self.auth_mgr.conn, privileges)
        self.auth_mgr.remove_tenant(tenant2.id, False)

    """
        This test function is used to temporaryly for debug, and will be REMOVED
        later!!!
    """
    def test_util(self):
        #vms = [(str(uuid.uuid4()), 'vm1')]
        vms = [('564df562-3d58-c99a-e76e-e8792b77ca2d', 'vm1')]
        privileges = [{'datastore': 'datastore1',
                              'global_visibility': 0,
                              'create_volume': 1,
                              'delete_volume': 1,
                              'mount_volume': 1,
                              'max_volume_size': 500,
                              'usage_quota': 1000}]
        default_datastore = 'default_ds'
        default_privileges = [{'datastore': default_datastore,
                              'global_visibility': 0,
                              'create_volume': 0,
                              'delete_volume': 0,
                              'mount_volume': 0,
                              'max_volume_size': 0,
                              'usage_quota': 0}]
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant1.id))
                
        #self.auth_mgr.remove_tenant(tenant1.id, True)

if __name__ == "__main__":
    unittest.main()

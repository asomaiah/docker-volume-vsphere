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
import auth_data_const

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

    # def tearDown(self):
    #     os.unlink(self.db_path)
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
    
    def get_row_from_tenants_table(self, tenant_uuid):
        try:
            cur = self.auth_mgr.conn.execute(
            "SELECT * FROM tenants WHERE id=?",
            (tenant_uuid,)
            )
        except sqlite3.Error, e:
            print "Error: %s when query tenants table for tenant %s", e, tenant_uuid

        result = cur.fetchone()
        return result
    
    def get_row_from_vms_table(self, tenant_uuid):
        try:
            cur = self.auth_mgr.conn.execute(
            "SELECT * FROM vms WHERE tenant_id=?",
            (tenant_uuid,)
            )
        except sqlite3.Error, e:
            print "Error: %s when query vms table for tenant %s", e, tenant_uuid

        result = cur.fetchall()
        return result
    
    def get_row_from_privileges_table(self, tenant_uuid):
        try:
            cur = self.auth_mgr.conn.execute(
            "SELECT * FROM privileges WHERE tenant_id=?",
            (tenant_uuid,)
            )
        except sqlite3.Error, e:
            print "Error: %s when query privileges table for tenant %s", e, tenant_uuid

        result = cur.fetchall()
        return result   
             
    def test_create_tenant(self):
        vm1_uuid = str(uuid.uuid4())
        vms = [(vm1_uuid, 'vm1')]
        
        #privileges = []
        privileges = self.get_privileges()
        default_datastore, default_privileges = self.get_default_datastore_and_privileges()
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant1.id))

        # Check tenants table
        tenants_row = self.get_row_from_tenants_table(tenant1.id)
        print "tenants table for tenant1 with id ", tenant1.id, tenants_row
        expected_output = [tenant1.id,
                           'tenant1',
                           'Some tenant',
                           'default_ds']
        actual_output = [tenants_row[auth_data_const.ID],
                         tenants_row[auth_data_const.NAME],
                         tenants_row[auth_data_const.DESCRIPTION],
                         tenants_row[auth_data_const.DEFAULT_DATASTORE]
                        ]
                          
        self.assertEqual(actual_output, expected_output)

        # check vms table 
        vms_row = self.get_row_from_vms_table(tenant1.id)
        print "vms table for tenant1 with id ", tenant1.id, vms_row
        expected_output = [vm1_uuid,
                           'vm1',
                           tenant1.id]
        self.assertEqual(len(vms_row), 1)

        actual_output = [vms_row[0][auth_data_const.VM_ID],
                         vms_row[0][auth_data_const.VM_NAME],
                         vms_row[0][auth_data_const.TENANT_ID]
                        ]
        self.assertTrue(actual_output, expected_output)

        # check privileges table
        privileges_row = self.get_row_from_privileges_table(tenant1.id)
        print "privileges table for tenant1 with id ", tenant1.id, privileges_row

        self.assertEqual(len(privileges_row), 2)

        expected_privileges = [privileges[0][auth_data_const.TENANT_ID],
                               privileges[0][auth_data_const.DATASTORE],
                               privileges[0][auth_data_const.GLOBAL_VISIBILITY],
                               privileges[0][auth_data_const.CREATE_VOLUME],
                               privileges[0][auth_data_const.DELETE_VOLUME],
                               privileges[0][auth_data_const.MOUNT_VOLUME],
                               privileges[0][auth_data_const.MAX_VOLUME_SIZE],
                               privileges[0][auth_data_const.USAGE_QUOTA]
                              ]
        expected_default_privileges = [default_privileges[0][auth_data_const.TENANT_ID],
                                       default_privileges[0][auth_data_const.DATASTORE],
                                       default_privileges[0][auth_data_const.GLOBAL_VISIBILITY],
                                       default_privileges[0][auth_data_const.CREATE_VOLUME],
                                       default_privileges[0][auth_data_const.DELETE_VOLUME],
                                       default_privileges[0][auth_data_const.MOUNT_VOLUME],
                                       default_privileges[0][auth_data_const.MAX_VOLUME_SIZE],
                                       default_privileges[0][auth_data_const.USAGE_QUOTA]
                                      ]

        expected_output = [expected_privileges, 
                           expected_default_privileges
                          ]
         
        print "expected_output"
        print expected_output
        actual_privileges = [privileges_row[0][auth_data_const.TENANT_ID],
                             privileges_row[0][auth_data_const.DATASTORE],
                             privileges_row[0][auth_data_const.GLOBAL_VISIBILITY],
                             privileges_row[0][auth_data_const.CREATE_VOLUME],
                             privileges_row[0][auth_data_const.DELETE_VOLUME],
                             privileges_row[0][auth_data_const.MOUNT_VOLUME],
                             privileges_row[0][auth_data_const.MAX_VOLUME_SIZE],
                             privileges_row[0][auth_data_const.USAGE_QUOTA]
                             ]
        actual_default_privileges = [privileges_row[1][auth_data_const.TENANT_ID],
                                     privileges_row[1][auth_data_const.DATASTORE],
                                     privileges_row[1][auth_data_const.GLOBAL_VISIBILITY],
                                     privileges_row[1][auth_data_const.CREATE_VOLUME],
                                     privileges_row[1][auth_data_const.DELETE_VOLUME],
                                     privileges_row[1][auth_data_const.MOUNT_VOLUME],
                                     privileges_row[1][auth_data_const.MAX_VOLUME_SIZE],
                                     privileges_row[1][auth_data_const.USAGE_QUOTA]
                                    ]
        actual_output = [actual_privileges, actual_default_privileges]
        print "actual_output"
        print actual_output
        self.assertEqual(actual_output, expected_output)        
            
    def test_add_vms(self): 
        vms = []
        privileges = []
        default_datastore, default_privileges = self.get_default_datastore_and_privileges()
        
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant1.id))
        
        vm1_uuid = str(uuid.uuid4())
        vm2_uuid = str(uuid.uuid4())
        vms = [(vm1_uuid, 'vm1'), (vm2_uuid, 'vm2')]
        tenant1.add_vms(self.auth_mgr.conn, vms)

         # check vms table 
        vms_row = self.get_row_from_vms_table(tenant1.id)
        print "vms table for tenant1 with id ", tenant1.id, vms_row
        expected_output = [(vm1_uuid, 'vm1', tenant1.id),
                           (vm2_uuid, 'vm2', tenant1.id) 
                          ]
        self.assertEqual(len(vms_row), 2)

        actual_output = [(vms_row[0][auth_data_const.VM_ID],
                          vms_row[0][auth_data_const.VM_NAME],
                          vms_row[0][auth_data_const.TENANT_ID]),
                         (vms_row[1][auth_data_const.VM_ID],
                          vms_row[1][auth_data_const.VM_NAME],
                          vms_row[1][auth_data_const.TENANT_ID]),
                        ]
        print "test_add_vms"
        print "expected_output"
        print expected_output
        print "actual_output"
        print actual_output
        self.assertTrue(actual_output, expected_output)
    
    def test_remove_vms(self):
            
        privileges = self.get_privileges()
        default_datastore, default_privileges = self.get_default_datastore_and_privileges()
        
        vm1_uuid = str(uuid.uuid4())
        vm2_uuid = str(uuid.uuid4())
        vms = [(vm1_uuid, 'vm1'), (vm2_uuid, 'vm2')]
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant1.id))
        tenant1.remove_vms(self.auth_mgr.conn, vms)
        vms_row = self.get_row_from_vms_table(tenant1.id)
        print "test_remove_vms"
        print vms_row
        self.assertEqual(vms_row, [])
        
    
    def test_set_name(self):
        vm1_uuid = str(uuid.uuid4())
        vms = [(vm1_uuid, 'vm1')]
        
        privileges = self.get_privileges()
        default_datastore, default_privileges = self.get_default_datastore_and_privileges()
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant1.id))

        tenant1.set_name(self.auth_mgr.conn, 'new_tenant1')
        tenants_row = self.get_row_from_tenants_table(tenant1.id)
        expected_output = 'new_tenant1'
        actual_output = tenants_row[auth_data_const.NAME]
        self.assertEqual(actual_output, expected_output)

    
    def test_set_description(self):
        vm1_uuid = str(uuid.uuid4())
        vms = [(vm1_uuid, 'vm1')]
        privileges = self.get_privileges()
        default_datastore, default_privileges = self.get_default_datastore_and_privileges()
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant1.id))
        tenant1.set_description(self.auth_mgr.conn, 'new description')

        tenants_row = self.get_row_from_tenants_table(tenant1.id)
        expected_output = 'new description'
        actual_output = tenants_row[auth_data_const.DESCRIPTION]
        self.assertEqual(actual_output, expected_output)
    
    def test_set_default_datastore_and_privileges(self):
        vm1_uuid = str(uuid.uuid4())
        vms = [(vm1_uuid, 'vm1')]
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

        # Check tenants table
        tenants_row = self.get_row_from_tenants_table(tenant1.id)
        print "tenants table for tenant1 with id ", tenant1.id, tenants_row
        expected_output = 'new_default_ds'
        actual_output = tenants_row[auth_data_const.DEFAULT_DATASTORE]
        self.assertTrue(actual_output, expected_output)

        #check privileges table
        privileges_row = self.get_row_from_privileges_table(tenant1.id)
        self.assertTrue(len(privileges_row), 2)
        expected_default_privileges = [default_privileges[0][auth_data_const.TENANT_ID],
                                       default_privileges[0][auth_data_const.DATASTORE],
                                       default_privileges[0][auth_data_const.GLOBAL_VISIBILITY],
                                       default_privileges[0][auth_data_const.CREATE_VOLUME],
                                       default_privileges[0][auth_data_const.DELETE_VOLUME],
                                       default_privileges[0][auth_data_const.MOUNT_VOLUME],
                                       default_privileges[0][auth_data_const.MAX_VOLUME_SIZE],
                                       default_privileges[0][auth_data_const.USAGE_QUOTA]
                                      ]
                 
        actual_default_privileges = [privileges_row[1][auth_data_const.TENANT_ID],
                                     privileges_row[1][auth_data_const.DATASTORE],
                                     privileges_row[1][auth_data_const.GLOBAL_VISIBILITY],
                                     privileges_row[1][auth_data_const.CREATE_VOLUME],
                                     privileges_row[1][auth_data_const.DELETE_VOLUME],
                                     privileges_row[1][auth_data_const.MOUNT_VOLUME],
                                     privileges_row[1][auth_data_const.MAX_VOLUME_SIZE],
                                     privileges_row[1][auth_data_const.USAGE_QUOTA]
                                    ]
        self.assertEqual(actual_default_privileges, expected_default_privileges)                
                                                      
    
    def test_add_datastore_access_privileges(self):
        vm1_uuid = str(uuid.uuid4())
        vms = [(vm1_uuid, 'vm1')]
        privileges = []
        
        default_datastore, default_privileges = self.get_default_datastore_and_privileges()
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant1.id))
               
        privileges = [{'datastore': 'datastore1',
                        'global_visibility': 0,
                        'create_volume': 1,
                        'delete_volume': 1,
                        'mount_volume': 0,
                        'max_volume_size': 0,
                        'usage_quota': 0}]
        
        tenant1.set_datastore_access_privileges(self.auth_mgr.conn, privileges)

        #check privileges table
        privileges_row = self.get_row_from_privileges_table(tenant1.id)
        self.assertTrue(len(privileges_row), 2)
        expected_privileges = [privileges[0][auth_data_const.TENANT_ID],
                               privileges[0][auth_data_const.DATASTORE],
                               privileges[0][auth_data_const.GLOBAL_VISIBILITY],
                               privileges[0][auth_data_const.CREATE_VOLUME],
                               privileges[0][auth_data_const.DELETE_VOLUME],
                               privileges[0][auth_data_const.MOUNT_VOLUME],
                               privileges[0][auth_data_const.MAX_VOLUME_SIZE],
                               privileges[0][auth_data_const.USAGE_QUOTA]
                              ]
                 
        actual_privileges = [privileges_row[0][auth_data_const.TENANT_ID],
                             privileges_row[0][auth_data_const.DATASTORE],
                             privileges_row[0][auth_data_const.GLOBAL_VISIBILITY],
                             privileges_row[0][auth_data_const.CREATE_VOLUME],
                             privileges_row[0][auth_data_const.DELETE_VOLUME],
                             privileges_row[0][auth_data_const.MOUNT_VOLUME],
                             privileges_row[0][auth_data_const.MAX_VOLUME_SIZE],
                             privileges_row[0][auth_data_const.USAGE_QUOTA]
                             ]
        print "expected_privileges"
        print expected_privileges
        print "actual_privileges"
        print actual_privileges
        self.assertEqual(actual_privileges, expected_privileges)
    

    def test_list_tenants(self):
        vm1_uuid = str(uuid.uuid4())
        vms = [(vm1_uuid, 'vm1')]
        privileges = []
        default_datastore, default_privileges = self.get_default_datastore_and_privileges()
        tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
                                              default_privileges, vms, privileges)
        self.assertTrue(uuid.UUID(tenant1.id))
        
        vm2_uuid = str(uuid.uuid4())
        vm3_uuid = str(uuid.uuid4())
        vms = [(vm2_uuid, 'vm2'), (vm3_uuid, 'vm3')]
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
        

        #Check tenants.id tenant.name, tenant.description and tenant.default_datastore
        self.assertTrue(len(tenants_list), 2)
        tenant1_expected_output = [
                                   tenant1.id,
                                   'tenant1',
                                   'Some tenant',
                                   'default_ds',
                                  ]
        tenant1_actual_output = [
                                 tenants_list[0].id,
                                 tenants_list[0].name,
                                 tenants_list[0].description,
                                 tenants_list[0].default_datastore,
                                ]
        self.assertEqual(tenant1_actual_output, tenant1_expected_output)

        # check vms
        tenant1_expected_output = [(vm1_uuid, 'vm1', tenant1.id),
                                  ]
        tenant1_actual_output = tenants_list[0].vms

        print "check vms expected_output"
        print tenant1_expected_output
        print "check vms actual_output"
        print tenant1_actual_output

        # check default_privileges
        tenant1_expected_output = default_privileges
        tenant1_actual_output = tenants_list[0].default_privileges
        print "check default_privileges expected_output"
        print tenant1_expected_output
        print "check default_privileges actual_output"
        print tenant1_actual_output

        # check privileges
        tenant1_expected_output = privileges 
        tenant1_actual_output = tenants_list[0].privileges
        print "check privileges expected_output"
        print tenant1_expected_output
        print "check privileges actual_output"
        print tenant1_actual_output                    
            
    
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
  
       
       
        tenant2.set_datastore_access_privileges(self.auth_mgr.conn, privileges)
        self.auth_mgr.remove_tenant(tenant2.id, False)

    """
        This test function is used to temporaryly for debug, and will be REMOVED
        later!!!
    """
    # def test_util(self):
    #     #vms = [(str(uuid.uuid4()), 'vm1')]
    #     vms = [('564df562-3d58-c99a-e76e-e8792b77ca2d', 'vm1')]
    #     privileges = [{'datastore': 'datastore1',
    #                           'global_visibility': 0,
    #                           'create_volume': 1,
    #                           'delete_volume': 1,
    #                           'mount_volume': 1,
    #                           'max_volume_size': 500,
    #                           'usage_quota': 1000}]
    #     default_datastore = 'default_ds'
    #     default_privileges = [{'datastore': default_datastore,
    #                           'global_visibility': 0,
    #                           'create_volume': 0,
    #                           'delete_volume': 0,
    #                           'mount_volume': 0,
    #                           'max_volume_size': 0,
    #                           'usage_quota': 0}]
    #     tenant1 = self.auth_mgr.create_tenant('tenant1', 'Some tenant', default_datastore,
    #                                           default_privileges, vms, privileges)
    #     self.assertTrue(uuid.UUID(tenant1.id))
                
    #     self.auth_mgr.remove_tenant(tenant1.id, True)

if __name__ == "__main__":
    unittest.main()

## VM based authorization for docker volumes
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

""" Define string constant for column name for table in authorization DB"""

# column name in tenants table
ID = 'id'
NAME = 'name'
DESCRIPTION = 'description'
DEFAULT_DATASTORE = 'default_datastore'

# column name in vms table
VM_ID = 'vm_id'
VM_NAME = 'vm_name'
TENANT_ID = 'tenant_id'

# column name in privileges table
DATASTORE = 'datastore'
GLOBAL_VISIBILITY = 'global_visibility'
MOUNT_VOLUME = 'mount_volume'
CREATE_VOLUME = 'create_volume'
DELETE_VOLUME = 'delete_volume'
VOLUME_SIZE = 'volume_size'
MAX_VOLUME_SIZE = 'max_volume_size'
USAGE_QUOTA = 'usage_quota'

# column name in volume table
VOLUME_NAME = 'volume_name'
VOLUME_SIZE = 'volume_size' 





/*
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
*/

PRAGMA foreign_key = ON;

CREATE TABLE tenants(
  id TEXT PRIMARY KEY NOT NULL,
  name TEXT,
  description TEXT,
  default_datastore TEXT
);

CREATE TABLE vms(
  vm_id TEXT PRIMARY KEY NOT NULL,
  vm_name TEXT,
  tenant_id TEXT NOT NULL,
  FOREIGN KEY(tenant_id) REFERENCES tenants(id)
);

CREATE TABLE privileges (
  tenant_id TEXT NOT NULL,
  datastore TEXT NOT NULL,
  global_visibility INTEGER,
  create_volume INTEGER,
  delete_volume INTEGER,
  mount_volume INTEGER,
  -- The unit of "max_volume_size" is "MB"
  max_volume_size INTEGER,
  -- The unit of usage_quota is "MB"
  usage_quota INTEGER,
  PRIMARY KEY (tenant_id, datastore),
  FOREIGN KEY(tenant_id) REFERENCES tenants(id)
);

CREATE TABLE volumes (
  tenant_id TEXT NOT NULL,
  datastore TEXT NOT NULL,
  volume_name TEXT,
  -- The unit of "volume_size" is "MB"
  volume_size INTEGER,
  PRIMARY KEY(tenant_id, datastore, volume_name),
  FOREIGN KEY(tenant_id) REFERENCES tenants(id)
);

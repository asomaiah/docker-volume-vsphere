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
  max_volume_size INTEGER,
  usage_quota INTEGER,
  PRIMARY KEY (tenant_id, datastore),
  FOREIGN KEY(tenant_id) REFERENCES tenants(id)
);

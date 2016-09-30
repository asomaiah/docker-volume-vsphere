import vmodl.*;

/**
 *
 * DockerVolumeAuthManager is the top-level managed object that provides APIs to manage docker volume
 *  authorization objects such as tenants and datastore access privileges.
 *
 * <p>
 * <b>Tenants</b> are a group of VMs that are granted privileges to create, delete and mount
 * docker volumes (VMDKs) on one or more datastores. Tenants provide for full isolation of these
 * volumes such that one tenant cannot see or manipulate volumes of another tenant even if both
 * tenants have volumes residing on the same datastore. The sole exception to this rule is if the
 * global_visibility privilege is assigned to a given datastore. In that case the tenant has all the
 * other privileges granted for all volumes in the datastore, not just ones it created.
 * <p>
 * <b>DatastoreAccessPrivileges</b> are predefined operations against a datastore and limits on those
 * operations.
 */
@managed public interface DockerVolumeAuthManager {

   /* An array of references to Tenant managed entities */
   @readonly @optional Tenant[] tenants();

   /* VMs that are not members of a tenant */
   @readonly @optional VirtualMachine[] availableVMs();

   @task Tenant createTenant(
         String name,
         String description,
         VirtualMachine[] vms,
         DatastoreAccessPrivileges[] privileges)
   throws AlreadyExists;

   @task Tenant removeTenant(String id, Boolean deleteVolumes);
   @task Tenant[] listTenants();
   /* TBD: which infomation need to be returned by this function
   @task String audit(String id);
   */

};

@managed public interface DockerVolumeTenant {
   /* A unique generated ID that cannot be changed */
   @readonly String id();

   /* A modifiable string */
   @readonly String name();
   @readonly String description();
   @readonly String defaultDatastore;
   @readonly DatastoreAccessPrivileges defaulPrivileges;
   @readonly @optional VirtualMachine[] vms();
   @readonly @optional DatastoreAccessPrivileges[] privileges();

   @task void addVms(VirtualMachine[] vm) throws AlreadyExists;
   @task void removeVms(VirtualMachine[] vm) throws NotFound;

   
   @task void setDatastoreAccessPrivileges(
         DatastoreAccessPrivileges[] privileges);
          
   @task void setName(String name);
   @task void setDescription(String name);

};


/* A set of privileges applied to a specific datastore for a given tenant */
@data public static class DatastoreAccessPrivileges {
   Datastore datastore;
   boolean createVolumes;
   boolean deleteVolumes;
   boolean mountVolumes;
   boolean globalVisibility;  // TODO: need to rethink this!!!

   // The maximum size of any volume created in this datastore
   int maxVolumeSize;

   // The maximum amount of storage that can be used in a datastore in bytes
   int usageQuota;
}

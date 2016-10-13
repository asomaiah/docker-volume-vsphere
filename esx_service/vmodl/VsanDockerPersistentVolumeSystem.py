"""
Copyright 2016 VMware, Inc.  All rights reserved. -- VMware Confidential
"""

from VmodlDecorators import ManagedType, EnumType, Method, \
   Return, RegisterVmodlTypes, F_OPTIONAL, Param, DataType, Attribute
from pyVmomi import Vmodl
from pyVmomi.VmomiSupport import newestVersions

try:
   from asyncVmodlEmitterLib import JavaDocs, Internal
except ImportError:
   pass
   def JavaDocs(parent, docs):
      def Decorate(f):
         return f
      return Decorate
   def Internal(parent):
      def Decorate(f):
         return f
      return Decorate


# _VERSION = newestVersions.Get("vim")
_VERSION = 'vim.version.version10'

# Vmodl Names

class VsanDockerPersistentVolumeTenantList:
   _name = "vim.vsan.VsanDockerPersistentVolumeTenantList"
   @JavaDocs(parent=_name, docs =
   """
   This class encapsulates the Docker Volume Tenant List Result.
   """
   )
   
   @DataType(name=_name, version=_VERSION)
   def __init__(self):
      pass

   @JavaDocs(parent=_name, docs =
   """
   Defines a list of tenants
   """
   )
   @Attribute(parent=_name, typ="string[]")
   def tenants(self):
      pass


class VsanDockerPersistentVolumeSystem:
   ''' This is the API to Docker Persistent Volumes on VSAN'''

   _name = "vim.host.VsanDockerPersistentVolumeSystem"

   @Internal(parent=_name)
   @ManagedType(name=_name, version=_VERSION)
   def __init__(self):
      pass

   @JavaDocs(parent=_name, docs=
   """
   Query the tenant list. This method returns a list of tenants, as strings. 
   The method is blocking on requires DB IO. 
   It SHOULD be converted to async task, eventually.
   """
   )
   @Method(parent=_name, wsdlName="GetTenantList")
   @Return(typ="vim.vsan.VsanDockerPersistentVolumeTenantList")
   def GetTenantList(self):
      pass


RegisterVmodlTypes()

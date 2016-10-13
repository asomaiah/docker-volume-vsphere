#!/usr/bin/env python

"""
Copyright 2015-2016 VMware, Inc.  All rights reserved.
-- VMware Confidential

"""
__author__ = "VMware, Inc"

import os
import traceback 

import logging
import sys


from pyVmomi import Vim, vim, vmodl
from MoManager import GetMoManager

sys.path.append('/usr/lib/vmware/hostd/hmo/')
sys.path.append('/usr/lib/vmware/vsan/perfsvc/')

# FFU: Needed for long running tasks:
#import VsanTaskTracker
#import VsanTaskTrackerImpl

logger = logging.getLogger()

class VsanDockerPersistentVolumeSystemImpl(vim.host.VsanDockerPersistentVolumeSystem):
    '''Example Implementation of DockVol ESX VMODL support'''

    def __init__(self, moId):
        vim.host.VsanDockerPersistentVolumeSystem.__init__(self, moId)


    def GetTenantList(self):
        logger.info("Running GetTenantList() method")
        try:
            ## fetch data from DB
            # Note: we should be using HostD tasks for long running work.
            # See usage of CreateRunHostdTask in  VSAN .py code. 
            # For now, we do blocking calls
            output = ["Tenant", "TenantWhoCares", "super Tenant"]
            logger.info("list of tenants: %s" % output)

            # now place it in the output type and return the result
            result = vim.vsan.VsanDockerPersistentVolumeTenantList()
            result.tenants = output
            return result 
        except:
            logger.info("Failed to fetch tenants list", exc_info=1)


GetMoManager().RegisterObjects([VsanDockerPersistentVolumeSystemImpl("vsan-docker-persistent-volumes")])


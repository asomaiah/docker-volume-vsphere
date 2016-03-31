#!/bin/sh

# This scripts runs the end to end tests.

usage() {
  echo "./end2end.sh <ESX IP> <VM1 IP> <VM2 IP> <Optional Build id>"
  echo "root user will be used for all operations"
  echo "Advisable to setup ssh keys"
  echo "Run this script from the root of the repo"
}

export ESX=$1
export VM1=$2
export VM2=$3
export BUILD_NUMBER=$4

SSH="ssh -o StrictHostKeyChecking=no"
USER=root
LOGFILE="/var/log/docker-vmdk-plugin.log"
STDLOG="/tmp/plugin.log"
if [ $# -lt 3 ]
then
  usage
  exit 1
fi

. ./drone-scripts/cleanup.sh

echo "*************************************************************************"
echo "tests starting"
echo "*************************************************************************"

dump_log_esx() {
  echo ""
  echo "*** dumping log: ESX " $ESX
  echo "*************************************************************************"
  set -x
  $SSH $USER@$ESX cat /var/log/vmware/docker-vmdk-plugin.log
  $SSH $USER@$ESX cat /tmp/plugin.log
  set +x
  echo "*************************************************************************"
}

dump_log_vm(){
  echo ""
  echo "*** dumping log: VM " $1
  echo "*************************************************************************"
  set -x
  $SSH $USER@$1 cat $STDLOG
  $SSH $USER@$1 cat $LOGFILE
  set +x
  echo "*************************************************************************"
}

dump_log() {
  dump_log_esx
  dump_log_vm $VM1
  dump_log_vm $VM2
}

if make testremote TEST_VOL_NAME=vol-build$BUILD_NUMBER
then
  echo "*************************************************************************"
  echo "tests done"
  echo ""
  dump_log
  stop_build $VM1 $BUILD_NUMBER
else
  echo "*************************************************************************"
  echo "tests failed"
  echo ""
  dump_log
  echo "*************************************************************************"
  echo "cleaning up"
  echo "*************************************************************************"

  stop_build $VM1 $BUILD_NUMBER
  exit 1
fi
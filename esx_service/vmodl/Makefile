# trivial makefile to validate and package python stuff
#
# DO NOT FORGET TO SET PROPER TARGET_LOCATION below (no automation for that so far). 
# On ESX 6.0 U2 and U3 it's PY2, on ESX 6.5 it's PY3
#
# example: 
# ESX=10.132.15.22 make test # deploys to ESX, runs *_test.py files to validate the stuff
# 

PY3_COMMON = /lib64/python3.5
PY2_COMMON = /lib/python2.7

# MOIDFY THIS LINE TO POINT TO CORRECT PYTHON VERSION
TARGET_LOC = $(PY3_COMMON)/site-packages/pyMo/vim/vsan

# Note: in ESX source, here are the location: 
#bora/vsan/<component>/esx/pyMo (Impl and __init)
#bora/vsan/pyvmodl (model)

NAME := VsanDockerPersistentVolumeSystem
MODEL = $(NAME).py
EXT = $(NAME)__ext_init__.py
IMPL = $(NAME)Impl.py

PYFILES = $(MODEL) $(EXT) $(IMPL)
TESTFILES := $(shell find . -name '*_test.py')
TMP_LOC    := $(shell echo /tmp/dockvol-vmodl_unittest$$RANDOM)

SSH := $(DEBUG) ssh -kTax -o StrictHostKeyChecking=no
SCP := $(DEBUG) scp -r -q -o StrictHostKeyChecking=no


deploy: 
	@echo Making test dir...
	@$(SSH) root@$(ESX) 'mkdir -p $(TMP_LOC)'
	@echo Copying VMODL python files to root@$(ESX):$(TARGET_LOC) ...
	@$(SCP) $(PYFILES) root@$(ESX):$(TARGET_LOC)/
	@echo Copying test file to root@$(ESX):$(TMP_LOC) ...
	@$(SCP) $(TESTFILES) $(TO_ESX_BIN) $(TO_ESX_PY) root@$(ESX):$(TMP_LOC)

lint: 
	pylint $(PYFILES)

# Testing. Note that vsanmgmtd neeeds a second or two between 'restart' returns
# and the daemon start to really listen 
test: deploy 
	@echo Restarting VSAN mgmt daemon and running tests...
	@$(SSH) root@$(ESX) \
        'set -x ; \
		/etc/init.d/vsanmgmtd restart ; sleep 3 ; \
		for i in $(TMP_LOC)/*_test.py ; \
			do python $$i ; \
            status=$$((status + $$?)) ;\
        done ; \
		rm -rf $(TMP_LOC) ;\
        set +x ; exit $$status'


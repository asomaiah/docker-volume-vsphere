import random

def authorize(vm_uuid, datastore, cmd, opts):
   return random.choice([None, 'Some error msg'])

'''

Create a VM with vlan L3 network and a data volume offering.

@author: Youyk
'''
import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.test_state as test_state
import os

test_stub = test_lib.lib_get_test_stub()
test_obj_dict = test_state.TestStateDict()

def test():
    global test_obj_dict
    #print test description and write this message to action log
    test_util.test_dsc('Create test vm and check. VR only has DNS and DHCP services')
    #get the value of the environment variable, use this value as a parameter to create a vm with a data volume
    vm = test_stub.create_vlan_vm_with_volume(os.environ.get('l3VlanNetworkName1'))
    #add vm to vm_dict[Running]
    test_obj_dict.add_vm(vm)
    #check vm state
    vm.check()
    #Get the length of allVolumes list, that is, the number of volume
    volumes_number = len(test_lib.lib_get_all_volumes(vm.vm))
    #if the list length is not equal to 2, record test log and test result, throw exception
    #otherwise print msg, record test log
    if volumes_number != 2:
        test_util.test_fail('Did not find 2 volumes for [vm:] %s. But we assigned 1 data volume when create the vm. We only catch %s volumes' % (vm.vm.uuid, volumes_number))
    else:
        test_util.test_logger('Find 2 volumes for [vm:] %s.' % vm.vm.uuid)

    #destroy vm
    vm.destroy()
    #test pass:print msg, record test log and test result
    test_util.test_pass('Create VirtualRouter VM DNS DHCP Test Success')

#Will be called only if exception happens in test().
def error_cleanup():
    global test_obj_dict
    #clean up the environment when error occurred
    test_lib.lib_error_cleanup(test_obj_dict)

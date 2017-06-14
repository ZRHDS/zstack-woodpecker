'''
New Integration Test for KVM VM network disconnect and connect check vm status
Notice that there is no MN HA, considering of plug off the net cable, the MN 
should not be impacted after none vm have been killed
@author: SyZhao
'''

import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_state as test_state
import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.operations.resource_operations as res_ops
import zstackwoodpecker.operations.host_operations as host_ops
import zstackwoodpecker.zstack_test.zstack_test_vm as test_vm_header
import zstackwoodpecker.header.vm as vm_header
import zstackwoodpecker.operations.ha_operations as ha_ops
import zstackwoodpecker.operations.vm_operations as vm_ops
import apibinding.inventory as inventory
import time
import os

vm = None
host_uuid = None
host_ip = None
max_attempts = None
storagechecker_timeout = None
test_stub = test_lib.lib_get_test_stub()

def test():
    global vm
    global host_uuid
    global host_ip
    global max_attempts
    global storagechecker_timeout
    if test_lib.lib_get_ha_enable() != 'true':
        test_util.test_skip("vm ha not enabled. Skip test")

    max_attempts = test_lib.lib_get_ha_selffencer_maxattempts()
    test_lib.lib_set_ha_selffencer_maxattempts('3')
    storagechecker_timeout = test_lib.lib_get_ha_selffencer_storagechecker_timeout()
    test_lib.lib_set_ha_selffencer_storagechecker_timeout('5')

    vm_creation_option = test_util.VmOption()
    image_name = os.environ.get('imageName_s')
    image_uuid = test_lib.lib_get_image_by_name(image_name).uuid
    #l3_name = os.environ.get('l3NoVlanNetworkName1')
    l3_name = os.environ.get('l3VlanNetworkName1')
    l3_net_uuid = test_lib.lib_get_l3_by_name(l3_name).uuid
    vrs = test_lib.lib_find_vr_by_l3_uuid(l3_net_uuid)
    vr_host_ips = []
    for vr in vrs:
        vr_host_ips.append(test_lib.lib_find_host_by_vr(vr).managementIp)
	if test_lib.lib_is_vm_running(vr) != True:
	    vm_ops.start_vm(vr.uuid)
    time.sleep(60)

    mn_ip = res_ops.query_resource(res_ops.MANAGEMENT_NODE)[0].hostName
    conditions = res_ops.gen_query_conditions('type', '=', 'UserVm')
    instance_offering_uuid = res_ops.query_resource(res_ops.INSTANCE_OFFERING, conditions)[0].uuid
    conditions = res_ops.gen_query_conditions('state', '=', 'Enabled')
    conditions = res_ops.gen_query_conditions('status', '=', 'Connected', conditions)
    conditions = res_ops.gen_query_conditions('managementIp', '!=', mn_ip, conditions)
    for vr_host_ip in vr_host_ips:
        conditions = res_ops.gen_query_conditions('managementIp', '!=', vr_host_ip, conditions)
    host_uuid = res_ops.query_resource(res_ops.HOST, conditions)[0].uuid
    vm_creation_option.set_host_uuid(host_uuid)
    vm_creation_option.set_l3_uuids([l3_net_uuid])
    vm_creation_option.set_image_uuid(image_uuid)
    vm_creation_option.set_instance_offering_uuid(instance_offering_uuid)
    vm_creation_option.set_name('multihost_basic_vm_status_runnning')
    vm = test_vm_header.ZstackTestVm()
    vm.set_creation_option(vm_creation_option)
    vm.create()
    vm.check()

    if not test_lib.lib_check_vm_live_migration_cap(vm.vm):
        test_util.test_skip('skip ha if live migrate not supported')

    ps = test_lib.lib_get_primary_storage_by_uuid(vm.get_vm().allVolumes[0].primaryStorageUuid)
    if ps.type == inventory.LOCAL_STORAGE_TYPE:
        test_util.test_skip('Skip test on localstorage')

    #vm.check()
    host_ip = test_lib.lib_find_host_by_vm(vm.get_vm()).managementIp
    host_port = test_lib.lib_get_host_port(host_ip)
    test_util.test_logger("host %s is disconnecting" %(host_ip))

    test_stub.down_host_network(host_ip, test_lib.all_scenario_config)

    test_util.test_logger("wait for 60 seconds")
    time.sleep(60)

    test_stub.up_host_network(host_ip, test_lib.all_scenario_config)

    vm.set_state(vm_header.STOPPED)
    vm.check()
    vm.destroy()


    #check mn service works normally
    vm.create()
    vm.check()
    vm.destroy()

    test_util.test_pass('Test vm checking status after network disconnect and connect success')

#Will be called only if exception happens in test().
def error_cleanup():
    global vm

    if vm:
        try:
            vm.destroy()
        except:
            pass



def env_recover():
    test_util.test_logger("recover host: %s" % (test_host.ip_))
    test_lib.lib_set_ha_selffencer_maxattempts(max_attempts)
    test_lib.lib_set_ha_selffencer_storagechecker_timeout(storagechecker_timeout)
    try:
        test_stub.down_host_network(host_ip, test_lib.all_scenario_config)
    except:
        pass

    try:
        test_stub.up_host_network(host_ip, test_lib.all_scenario_config)
    except:
        pass
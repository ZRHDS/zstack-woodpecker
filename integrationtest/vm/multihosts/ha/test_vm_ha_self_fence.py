'''

New Integration Test for creating KVM VM.

@author: Quarkonics
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
import time
import os

vm = None
host_uuid = None
host_ip = None
max_attempts = None
storagechecker_timeout = None

def test():
    global vm
    global host_uuid
    global host_ip
    global max_attempts
    global storagechecker_timeout

    if test_lib.lib_get_ha_enable() != 'true':
        test_util.test_skip("vm ha not enabled. Skip test")


    vm_creation_option = test_util.VmOption()
    image_name = os.environ.get('imageName_s')
    image_uuid = test_lib.lib_get_image_by_name(image_name).uuid
    #l3_name = os.environ.get('l3NoVlanNetworkName1')
    l3_name = os.environ.get('l3VlanNetworkName1')
    l3_net_uuid = test_lib.lib_get_l3_by_name(l3_name).uuid
    vrs = test_lib.lib_find_vr_by_l3_uuid(l3_net_uuid)
    for vr in vrs:
	if test_lib.lib_is_vm_running(vr) != True:
	    vm_ops.start_vm(vr.uuid)
    time.sleep(60)

    mn_ip = res_ops.query_resource(res_ops.MANAGEMENT_NODE)[0].hostName
    conditions = res_ops.gen_query_conditions('type', '=', 'UserVm')
    instance_offering_uuid = res_ops.query_resource(res_ops.INSTANCE_OFFERING, conditions)[0].uuid
    conditions = res_ops.gen_query_conditions('state', '=', 'Enabled')
    conditions = res_ops.gen_query_conditions('status', '=', 'Connected', conditions)
    conditions = res_ops.gen_query_conditions('managementIp', '!=', mn_ip, conditions)
    host_uuid = res_ops.query_resource(res_ops.HOST, conditions)[0].uuid
    vm_creation_option.set_host_uuid(host_uuid)
    vm_creation_option.set_l3_uuids([l3_net_uuid])
    vm_creation_option.set_image_uuid(image_uuid)
    vm_creation_option.set_instance_offering_uuid(instance_offering_uuid)
    vm_creation_option.set_name('multihost_basic_vm')
    vm = test_vm_header.ZstackTestVm()
    vm.set_creation_option(vm_creation_option)
    vm.create()
    #vm.check()
    host_ip = test_lib.lib_find_host_by_vm(vm.get_vm()).managementIp
    host_uuid = test_lib.lib_find_host_by_vm(vm.get_vm()).uuid
    ha_ops.set_vm_instance_ha_level(vm.get_vm().uuid, "OnHostFailure")
    l2_network_interface = os.environ.get('l2ManagementNetworkInterface')

    host_username = os.environ.get('hostUsername')
    host_password = os.environ.get('hostPassword')
    cmd = "ifdown %s && sleep 180 && ifup %s" % (l2_network_interface, l2_network_interface)
    rsp = test_lib.lib_execute_ssh_cmd(host_ip, host_username, host_password, cmd, 180)
    if rsp:
	test_util.test_fail("host is expected to shutdown after its network down for a while")
    else:
        test_util.test_logger("host may have been shutdown")

    cmd = "date"
    rsp = test_lib.lib_execute_ssh_cmd(host_ip, host_username, host_password, cmd)
    if rsp:
	test_util.test_fail("host is expected to shutdown after its network down for a while")
    else:
        test_util.test_logger("host have been shutdown")

    try:
        vm.destroy()
    except:
	test_util.test_logger("destroy vm may time out since host is down")

    test_lib.lib_set_ha_selffencer_maxattempts(max_attempts)
    test_lib.lib_set_ha_selffencer_storagechecker_timeout(storagechecker_timeout)
    os.system('bash -ex %s %s' % (os.environ.get('hostRecoverScript'), host_ip))
    host_ops.reconnect_host(host_uuid)


    test_util.test_pass('Test Host Self fence Success')

#Will be called only if exception happens in test().
def error_cleanup():
    global vm
    global host_ip
    global host_uuid
    global max_attempts
    global storagechecker_timeout

    if vm:
        try:
            vm.destroy()
        except:
            pass

    os.system('bash -ex %s %s' % (os.environ.get('hostRecoverScript'), host_ip))
    host_ops.reconnect_host(host_uuid)

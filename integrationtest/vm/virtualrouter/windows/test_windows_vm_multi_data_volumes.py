'''

New Integration Test for Starting Windows VM with Multi Data Volumes.

@author: Mirabel
'''

import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.test_state as test_state
import zstackwoodpecker.operations.resource_operations as res_ops
import os
import telnetlib
import time

test_stub = test_lib.lib_get_test_stub()
test_obj_dict = test_state.TestStateDict()

def test():
    cpuNum = 2
    memorySize = 512 * 1024 * 1024
    new_offering = test_lib.lib_create_instance_offering(cpuNum = cpuNum,\
            memorySize = memorySize)

    test_obj_dict.add_instance_offering(new_offering)
    new_offering_uuid = new_offering.uuid

    l3_name = os.environ.get('l3VlanNetworkName1')
    disk_offering = test_lib.lib_get_disk_offering_by_name(os.environ.get('smallDiskOfferingName'))

    data_volume_uuids = [disk_offering.uuid,disk_offering.uuid,disk_offering.uuid]
    data_volume_num = 3
    volume_list = []
    try:
        vm = test_stub.create_windows_vm_2(l3_name, instance_offering_uuid = new_offering_uuid)
        test_obj_dict.add_vm(vm)
        for i in range(data_volume_num):
            volume_list.append(test_stub.create_volume())
            test_obj_dict.add_volume(volume_list[i])
            volume_list[i].attach(vm)
    except:
        test_lib.lib_robot_cleanup(test_obj_dict)
        test_util.test_fail('Create Windows VM with Multi Data volumes Test Fail')

    vm_inv = vm.get_vm()
    print"vm_uuid:%s"%(vm_inv.uuid)
    host_inv = test_lib.lib_find_host_by_vm(vm_inv)
    host_ip = host_inv.managementIp
    host_username = host_inv.username
    print"host_username%s"%(host_username)
    host_password = host_inv.password
    cmd = "virsh domiflist %s|grep vnic|awk '{print $3}'"% (vm_inv.uuid)
    br_eth0 = test_lib.lib_execute_ssh_cmd(host_ip, host_username, host_password, cmd, 60)
    cmd2 = 'ip a add 10.11.254.254/8 dev %s'% (br_eth0)
    test_lib.lib_execute_ssh_cmd(host_ip, host_username, host_password, cmd2, 60)

    vm_ip = vm.get_vm().vmNics[0].ip
    test_lib.lib_wait_target_up(vm_ip, '23', 720)
    vm_username = os.environ.get('winImageUsername')
    vm_password = os.environ.get('winImagePassword')
    tn=telnetlib.Telnet(vm_ip)
    tn.read_until("login: ")
    tn.write(vm_username+"\r\n")
    tn.read_until("password: ")
    tn.write(vm_password+"\r\n")
    tn.read_until(vm_username+">")
    tn.write("wmic diskdrive\r\n")
    vm_data_volumes=tn.read_until(vm_username+">")
    tn.close()

    if len(vm_data_volumes.split('\r\n')) != (data_volume_num + 6):
        test_lib.lib_robot_cleanup(test_obj_dict)
        test_util.test_fail('Create Windows VM with Multi Data volumes Test Fail')

    try:
        vm.reboot()
    except:
        test_lib.lib_robot_cleanup(test_obj_dict)
        test_util.test_fail('Reboot Windows VM with Multi Data volumes fail')

    vm_ip = vm.get_vm().vmNics[0].ip
    test_lib.lib_wait_target_up(vm_ip, '23', 360)
    vm_username = os.environ.get('winImageUsername')
    vm_password = os.environ.get('winImagePassword')
    tn=telnetlib.Telnet(vm_ip)
    tn.read_until("login: ")
    tn.write(vm_username+"\r\n")
    tn.read_until("password: ")
    tn.write(vm_password+"\r\n")
    tn.read_until(vm_username+">")
    tn.write("wmic diskdrive\r\n")
    vm_data_volumes=tn.read_until(vm_username+">")
    tn.close()

    if len(vm_data_volumes.split('\r\n')) == (data_volume_num + 6):
        test_lib.lib_robot_cleanup(test_obj_dict)
        test_util.test_pass('Create Windows VM with Multi Data Volumes Test Success')
    else:
        test_lib.lib_robot_cleanup(test_obj_dict)
        test_util.test_fail('Create Windows VM with Multi Data volumes Test Fail')
#Will be called only if exception happens in test().
def error_cleanup():
    global vm
    if vm:
        vm.destroy()

'''

Test Attach/Detach many Port Forwarding

@author: Quarkonics
'''
import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.test_state as test_state
import zstackwoodpecker.zstack_test.zstack_test_port_forwarding as zstack_pf_header
import apibinding.inventory as inventory

import os

PfRule = test_state.PfRule
Port = test_state.Port
test_stub = test_lib.lib_get_test_stub()
test_obj_dict = test_state.TestStateDict()

def test():
    pf_vm1 = test_stub.create_dnat_vm()
    test_obj_dict.add_vm(pf_vm1)

    l3_name = os.environ.get('l3VlanNetworkName1')
    vr1 = test_stub.create_vr_vm(test_obj_dict, l3_name)

    vr1_pub_ip = test_lib.lib_find_vr_pub_ip(vr1)
    
    pf_vm1.check()

    vm_nic1 = pf_vm1.vm.vmNics[0]
    vm_nic_uuid1 = vm_nic1.uuid
    pri_l3_uuid = vm_nic1.l3NetworkUuid
    vr = test_lib.lib_find_vr_by_l3_uuid(pri_l3_uuid)[0]
    vr_pub_nic = test_lib.lib_find_vr_pub_nic(vr)
    l3_uuid = vr_pub_nic.l3NetworkUuid
    vip = test_stub.create_vip('pf_attach_test', l3_uuid)
    test_obj_dict.add_vip(vip)
    vip_uuid = vip.get_vip().uuid

    for i in range(1, 2000):
        test_util.test_logger('round %s' % (i))
        pf_creation_opt1 = PfRule.generate_pf_rule_option(vr1_pub_ip, protocol=inventory.TCP, vip_target_rule=Port.rule5_ports, private_target_rule=Port.rule5_ports, vip_uuid=vip_uuid)
        pf_creation_opt1.set_vip_ports(i, i)
        pf_creation_opt1.set_private_ports(i, i)
        test_pf1 = zstack_pf_header.ZstackTestPortForwarding()
        test_pf1.set_creation_option(pf_creation_opt1)
        test_pf1.create()
        vip.attach_pf(test_pf1)
        test_pf1.attach(vm_nic_uuid1, pf_vm1)
	test_pf1.detach()

    vip.delete()
    test_obj_dict.rm_vip(vip)
    pf_vm1.destroy()
    test_obj_dict.rm_vm(pf_vm1)

    test_util.test_pass("Test Port Forwarding Attach/Detach Successfully")

#Will be called only if exception happens in test().
def error_cleanup():
    global test_obj_dict
    test_lib.lib_error_cleanup(test_obj_dict)

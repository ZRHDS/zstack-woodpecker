'''
@author: FangSun
'''

import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.test_state as test_state
import zstackwoodpecker.operations.primarystorage_operations as ps_ops
import apibinding.inventory as inventory

_config_ = {
        'timeout' : 3000,
        'noparallel' : True
        }


test_stub = test_lib.lib_get_test_stub()
test_obj_dict = test_state.TestStateDict()
VM_COUNT = 1
VOLUME_NUMBER = 0
new_ps_list = []


def test():
    env = test_stub.TwoPrimaryStorageEnv(test_object_dict=test_obj_dict,
                                         first_ps_vm_number=VM_COUNT,
                                         second_ps_vm_number=VM_COUNT,
                                         first_ps_volume_number=VOLUME_NUMBER,
                                         second_ps_volume_number=VOLUME_NUMBER)
    env.check_env()
    env.deploy_env()

    first_ps_vm = env.first_ps_vm_list[0]
    second_ps_vm = env.second_ps_vm_list[0]
    if env.new_ps:
        new_ps_list.append(env.second_ps)

    test_util.test_dsc("migrate VM in first Primary Storage")

    test_stub.migrate_vm_to_random_host(first_ps_vm)
    first_ps_vm.check()


    test_util.test_dsc("migrate vm in second Primary Storage")

    test_stub.migrate_vm_to_random_host(second_ps_vm)
    second_ps_vm.check()


def env_recover():
    test_lib.lib_error_cleanup(test_obj_dict)
    if new_ps_list:
        for new_ps in new_ps_list:
            ps_ops.detach_primary_storage(new_ps.uuid, new_ps.attachedClusterUuids[0])
            ps_ops.delete_primary_storage(new_ps.uuid)
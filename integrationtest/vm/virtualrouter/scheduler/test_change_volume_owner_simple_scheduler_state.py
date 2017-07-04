'''

@author: MengLai
'''

import os
import time
import zstackwoodpecker.operations.vm_operations as vm_ops
import zstackwoodpecker.operations.scheduler_operations as schd_ops
import zstackwoodpecker.operations.volume_operations as vol_ops
import zstackwoodpecker.operations.account_operations as account_operations
import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.test_state as test_state
import zstackwoodpecker.operations.resource_operations as res_ops

test_stub = test_lib.lib_get_test_stub()
test_obj_dict = test_state.TestStateDict()
vm = None
schd_job1 = None
schd_job2 = None
schd_trigger1 = None
schd_trigger2 = None

def query_snapshot_number(snapshot_name):
    cond = res_ops.gen_query_conditions('name', '=', snapshot_name)
    return res_ops.query_resource_count(res_ops.VOLUME_SNAPSHOT, cond)

def check_scheduler_state(schd, target_state):
    conditions = res_ops.gen_query_conditions('uuid', '=', schd.uuid)
    schd_state = res_ops.query_resource(res_ops.SCHEDULER, conditions)[0].state
    if schd_state != target_state:
        test_util.test_fail('check scheduler state, it is expected to be %s, but it is %s' % (target_state, schd_state))

    return True

def test():
    global vm
    global schd_job1
    global schd_job2
    global schd_trigger1
    global schd_trigger2
    global new_account

    vm = test_stub.create_vlan_vm()
    test_obj_dict.add_vm(vm)

    disk_offering = test_lib.lib_get_disk_offering_by_name(os.environ.get('smallDiskOfferingName'))
    volume_creation_option = test_util.VolumeOption()
    volume_creation_option.set_name('volume for snapshot scheduler testing')
    volume_creation_option.set_disk_offering_uuid(disk_offering.uuid)
    volume = test_stub.create_volume(volume_creation_option)
    test_obj_dict.add_volume(volume)

    volume.attach(vm)
    volume.detach()

    test_util.test_dsc('create snapshot scheduler')
    start_date = int(time.time())
    sp_option = test_util.SnapshotOption()
    sp_option.set_name('simple_schduler_snapshot')
    sp_option.set_volume_uuid(volume.get_volume().uuid)

    schd = vol_ops.create_snapshot_scheduler(sp_option, 'simple', 'simple_create_snapshot_scheduler',  start_date+60, 120)

    check_scheduler_state(schd, 'Enabled')

    snapshot_num = 0
    for i in range(0, 3):
        test_util.test_logger('round %s' % (i))
        test_stub.sleep_util(start_date + 60 + 120*i - 2)
        test_util.test_logger('check volume snapshot number at %s, there should be %s' % (start_date + 60 + 120*i - 2, snapshot_num))
        new_snapshot_num = query_snapshot_number('simple_schduler_snapshot')
        if snapshot_num != new_snapshot_num:
            test_util.test_fail('there sholuld be %s snapshots' % (snapshot_num))
        snapshot_num += 1

        test_stub.sleep_util(start_date + 60 + 120*i + 60)
        test_util.test_logger('check volume snapshot number at %s, there should be %s' % (start_date + 60 + 120*i + 65, snapshot_num+1))
        new_snapshot_num = query_snapshot_number('simple_schduler_snapshot')
        if snapshot_num != new_snapshot_num:
            test_util.test_fail('there sholuld be %s snapshots' % (snapshot_num))

    new_account = account_operations.create_account('new_account', 'password', 'Normal')

    res_ops.change_recource_owner(new_account.uuid, volume.get_volume().uuid)

    test_util.test_dsc('check scheduler state after changing the owner of volume')
    check_scheduler_state(schd, 'Disabled')

    current_time = int(time.time())
    except_start_time =  start_date + 120 * (((current_time - start_date) % 120) + 1)

    for i in range(0, 3):
        test_util.test_logger('round %s' % (i))
        test_stub.sleep_util(except_start_time + 60 + 120*i - 2)
        test_util.test_logger('check volume snapshot number at %s, there should be %s' % (except_start_time + 60 + 120*i - 2, snapshot_num))
        new_snapshot_num = query_snapshot_number('simple_schduler_snapshot')
        if snapshot_num != new_snapshot_num:
            test_util.test_fail('there sholuld be %s snapshots' % (snapshot_num))

        test_stub.sleep_util(except_start_time + 60 + 120*i + 60)
        test_util.test_logger('check volume snapshot number at %s, there should be %s' % (except_start_time + 60 + 120*i + 65, snapshot_num+1))
        new_snapshot_num = query_snapshot_number('simple_schduler_snapshot')
        if snapshot_num != new_snapshot_num:
            test_util.test_fail('there sholuld be %s snapshots' % (snapshot_num))

    schd_ops.delete_scheduler(schd.uuid)
    vm.destroy()
    account_operations.delete_account(new_account.uuid)

    test_util.test_pass('Check Scheduler State after Changing Volume Owner Success')

#Will be called only if exception happens in test().
def error_cleanup():
    global vm
    global schd_job1
    global schd_job2
    global schd_trigger1
    global schd_trigger2
    global new_account
 
    test_lib.lib_error_cleanup(test_obj_dict)

    if schd:
	schd_ops.delete_scheduler(schd.uuid)

    if new_account:
       account_operations.delete_account(new_account.uuid) 

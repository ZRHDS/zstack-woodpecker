'''
Test for auto reconnect host 

@author: quarkonics
'''

import os
import time
import commands
#import sys

import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_state as test_state
import zstackwoodpecker.operations.resource_operations as res_ops
import zstackwoodpecker.operations.primarystorage_operations as ps_ops

_config_ = {
        'timeout' : 360,
        'noparallel' : True
        }

def test():
    test_util.test_dsc('host auto reconnection check test')

    host_inv = res_ops.query_resource(res_ops.HOST, [])[0]
    host_username = os.environ.get('hostUsername')
    host_password = os.environ.get('hostPassword')
    cmd = "service zstack-kvmagent stop"
    if test_lib.lib_execute_ssh_cmd(host_inv.managementIp, host_username, host_password, cmd,  timeout = 120) == False:
        test_util.test_fail("CMD:%s execute failed on %s" %(cmd, mn_ip))

    test_util.test_logger("host %s is expected to disconnect and start reconnect automatically")
    conditions = res_ops.gen_query_conditions('uuid', '=', host_inv.uuid)
    count = 0
    while count < 12:
        host = res_ops.query_resource(res_ops.HOST)[0]
        if host.status == "Connecting":
            break
        time.sleep(5)

    if host.status != "Connecting":
        test_util.test_fail("host %s is not disconnect and start reconnect automatically in 60 seconds")

    count = 0
    while count < 12:
        host = res_ops.query_resource(res_ops.HOST)[0]
        if host.status == "Connected":
            break
        time.sleep(5)

    if host.status != "Connected":
        test_util.test_fail("host %s not reconnect success automatically in 60 seconds")
       
    test_util.test_pass("Auto reconnect host pass")

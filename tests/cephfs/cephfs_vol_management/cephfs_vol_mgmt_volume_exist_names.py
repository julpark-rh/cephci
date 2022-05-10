import random
import string
import traceback

from tests.cephfs.cephfs_utilsV1 import FsUtils
from utility.log import Log

log = Log(__name__)


def run(ceph_cluster, **kw):
    """
    pre-requisites:
    1. Try to create a volume
    2. Try to create a subvolume in the volume
    3. Try to create a subvolume group in the volume
    Test operation:
    1. Try to create a volume with exist name
    2. Try to create a subvolume in the volume with exist name
    3. Try to create a subvolume group in the volume with exist name
    """
    try:

        tc = "CEPH-83573428"
        log.info(f"Running CephFS tests{tc}")
        fs_util = FsUtils(ceph_cluster)
        clients = ceph_cluster.get_ceph_objects("client")
        client1 = clients[0]
        fs_details = fs_util.get_fs_info(client1)
        if not fs_details:
            fs_util.create_fs(client1, "cephfs")
        fs_util.auth_list([client1])
        fs_name="cephfs_sample"
        subvol_name="subvol_sample"
        subvol_group_name="subvol_group_name_sample"
        client1.exec_command(sudo=True,cmd=f"ceph fs volume create {fs_name}")
        fs_util.create_subvolume(client1,fs_name,subvol_name)
        fs_util.create_subvolumegroup(client1,fs_name,subvol_group_name)
        log.info("FS and Subvolume and Subvolume group are created")
        out1,err1=client1.exec_command(sudo=True,cmd=f"ceph fs volume create {fs_name}")
        out2,err2=fs_util.create_subvolume(client1, fs_name, subvol_name)
        out3,err3=fs_util.create_subvolumegroup(client1, fs_name, subvol_group_name)
        if out1 == 0 or out2 == 0 or out3 == 0:
            return 1
        log.info("Cleaning up the FS and subvolume and Subvolume group")
        client1.exec_command(
            sudo=True, cmd="ceph config set mon mon_allow_pool_delete true"
        )
        fs_util.remove_fs(client1,fs_name)
        return 0
    except Exception as e:
        log.info(e)
        log.info(traceback.format_exc())
        return 1

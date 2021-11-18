import logging
import random
import string
import traceback
import json
from ceph.ceph import CommandFailed
from tests.cephfs.cephfs_utilsV1 import FsUtils

log = logging.getLogger(__name__)

def run(ceph_cluster, **kw):
    try:
        bz = '1980920'

        fs_util = FsUtils(ceph_cluster)

        log.info('Running cephfs test for bug %s' % bz)

        clients = ceph_cluster.get_ceph_objects("client")

        client1 = clients[0]

        create_cephfs = "ceph fs volume create cephfs"

        client1.exec_command(sudo=True, cmd=create_cephfs)

        fs_details = fs_util.get_fs_info(client1)
        subvolume_name = "".join(random.choice(string.ascii_lowercase + string.digits)for _ in list(range(5)))
        subvolume = {
            "vol_name": "cephfs",
            "subvol_name": "subvol_"+str(subvolume_name),
            "size": "5368706371",
        }

        fs_util.create_subvolume(client1, **subvolume)

        log.info("Get the path of sub volume")

        subvol_path, rc = client1.exec_command(sudo=True,cmd=f"ceph fs subvolume getpath cephfs subvol_"+str(subvolume_name),)

        mounting_dir = "".join(random.choice(string.ascii_lowercase + string.digits)for _ in list(range(10)))

        kernel_mounting_dir_1 = f"/mnt/cephfs_kernel{mounting_dir}_1/"

        mon_node_ips = fs_util.get_mon_node_ips()

        fs_util.auth_list([client1])

        fs_util.kernel_mount([client1],kernel_mounting_dir_1,",".join(mon_node_ips),sub_dir=f"{subvol_path.read().decode().strip()}",)

        for i in range(500):
            client1.exec_command(sudo=True, cmd=f"dd if=/dev/zero of={kernel_mounting_dir_1}"+str(i)+".txt bs=10 count=0 seek=10M" ,long_running=True)


        fs_util.mount_dir_update(kernel_mounting_dir_1)
        # fs_util.stress_io([client1], mounting_dir, kernel_mounting_dir_1, 1, 10000, iotype="smallfile_create")
        log.info("checking Pre-requisites")

        # client_info,rc = fs_util.get_clients(build)
        # fs_util.create_subvolume()
        #
        # fs_util.fuse_mount(fuse_clients=client_info["fuse_clients"][0],mount_point=client_info["mounting_dir"])

        # fs_util.stress_io(client_info["fuse_clients"][0],mounting_dir=client_info["mounting_dir"],dir_name="dir")

        fs_util.create_snapshot(client1,"cephfs","subvol_"+subvolume_name,"subvol_1_snap"+subvolume_name)
        start=1
        end=4
        for i in range(start,end):
            fs_util.create_clone(client1,"cephfs","subvol_"+subvolume_name,"subvol_1_snap"+subvolume_name,"subvol_1_snap_clone"+str(subvolume_name)+str(i))
            out1 , err1 = client1.exec_command(sudo=True, cmd="ceph fs clone status cephfs subvol_1_snap_clone"+str(subvolume_name)+str(i))
            output1 = json.loads(out1.read().decode())
            result1 = output1["status"]["state"]
            print(output1)
            client1.exec_command(sudo=True, cmd="ceph fs clone cancel cephfs subvol_1_snap_clone" + str(subvolume_name) + str(1))


        out,err = client1.exec_command(sudo=True,cmd="ceph fs clone status cephfs subvol_1_snap_clone"+str(subvolume_name)+str(1)+" --format json")
        output = json.loads(out.read().decode())

        result = output["status"]["state"]
        if result == "pending":
            print("pending")
            return 0
        print("not pending")
        return 1
    except Exception as e:
        print("exception occued")
        log.info(e)
        log.info(traceback.format_exc())
        return 1
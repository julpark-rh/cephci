import copy
from time import sleep

from smb_operations import (
    deploy_smb_service_declarative,
    smb_cleanup,
    smbclient_check_shares,
)

from cli.exceptions import ConfigError
from utility.log import Log

log = Log(__name__)


def run(ceph_cluster, **kw):
    """Deploy samba with auth_mode 'user' using declarative style(Spec File)
    Args:
        **kw: Key/value pairs of configuration information to be used in the test
    """
    # Get config
    config = kw.get("config")

    # Check mandatory parameter file_type
    if not config.get("file_type"):
        raise ConfigError("Mandatory config 'file_type' not provided")

    # Get spec file type
    file_type = config.get("file_type")

    # Check mandatory parameter spec
    if not config.get("spec"):
        raise ConfigError("Mandatory config 'spec' not provided")

    # Get smb spec
    smb_spec = config.get("spec")

    # Get smb spec file mount path
    file_mount = config.get("file_mount", "/tmp")

    # Get installer node
    installer = ceph_cluster.get_nodes(role="installer")[0]

    # Get smb nodes
    smb_nodes = ceph_cluster.get_nodes("smb")

    # get client node
    client = ceph_cluster.get_nodes(role="client")[0]

    # Get smb subvolume mode
    smb_subvolume_mode = config.get("smb_subvolume_mode", "0777")

    # Get total shares
    total_smb_shares = int(config.get("smb_shares", 500))

    # Get smb service value from spec file
    smb_shares = []
    smb_subvols = []

    for spec in smb_spec:
        if spec["resource_type"] == "ceph.smb.cluster":
            smb_cluster_id = spec["cluster_id"]
            auth_mode = spec["auth_mode"]
            if "domain_settings" in spec:
                domain_realm = spec["domain_settings"]["realm"]
            else:
                domain_realm = None
        elif spec["resource_type"] == "ceph.smb.usersgroups":
            smb_user_name = spec["values"]["users"][0]["name"]
            smb_user_password = spec["values"]["users"][0]["password"]
        elif spec["resource_type"] == "ceph.smb.join.auth":
            smb_user_name = spec["auth"]["username"]
            smb_user_password = spec["auth"]["password"]
    spec_share = smb_spec[-1]
    smb_spec = smb_spec[:-1]
    for smb_share in range(1, total_smb_shares + 1):
        cephfs_vol = spec["cephfs"]["volume"]
        smb_subvol_group = spec["cephfs"]["subvolumegroup"]
        smb_subvols.append(spec["cephfs"]["subvolume"] + str(smb_share))
        smb_shares.append(spec["share_id"] + str(smb_share))
        new_share = copy.deepcopy(spec_share)
        new_share["share_id"] = f"share{smb_share}"
        new_share["cephfs"]["subvolume"] = f"sv{smb_share}"
        smb_spec.append(new_share)

    try:
        # deploy smb services
        deploy_smb_service_declarative(
            installer,
            cephfs_vol,
            smb_subvol_group,
            smb_subvols,
            smb_cluster_id,
            smb_subvolume_mode,
            file_type,
            smb_spec,
            file_mount,
        )

        sleep(60)

        # Check smb share using smbclient
        smbclient_check_shares(
            smb_nodes,
            client,
            smb_shares,
            smb_user_name,
            smb_user_password,
            auth_mode,
            domain_realm,
        )
    except Exception as e:
        log.error(f"Failed to deploy samba with auth_mode 'user' : {e}")
        return 1
    finally:
        smb_cleanup(installer, smb_shares, smb_cluster_id)
    return 0

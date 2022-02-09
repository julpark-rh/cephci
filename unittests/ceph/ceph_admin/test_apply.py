import mock
import pytest

from ceph.ceph_admin.apply import ApplyMixin, OrchApplyServiceFailure


class MockApplyMixinTestWithShellOutput(ApplyMixin):
    def __init__(self):
        self.cluster = None
        self.service_name = "rgw"

    def shell(self, args):
        return "Scheduled rgw update", 0

    def check_service_exists(self, service_name="rgw"):
        return True


class MockApplyMixinTestWithOutShellOutput(ApplyMixin):
    def __init__(self):
        self.cluster = None
        self.service_name = "rgw"

    def shell(self, args):
        return 0, 0

    def check_service_exists(self, service_name="rgw"):
        return True


class MockApplyMixinTestWithOutServiceOutput(ApplyMixin):
    def __init__(self):
        self.cluster = None
        self.service_name = "rgw"

    def shell(self, args):
        return 0, 0

    def check_service_exists(self, service_name="rgw"):
        return False


class TestApply:
    @mock.patch("ceph.ceph_admin.apply.config_dict_to_string")
    def test_apply_with_shell_output(self, mock_config):
        config = {
            "command": "apply",
            "service": "rgw",
            "args": {
                "all-available-devices": True,
                "placement": {
                    "label": "rgw_south",
                    "nodes": ["node1", "*"],
                    "limit": 3,
                    "sep": "",
                    "count-per-host": 1,
                },
                "dry-run": True,
            },
            "verify": False,
            "base_cmd_args": {"verbose": True},
            "pos_args": ["node1", "dev/vdb", "dev"],
        }
        mock_config.return_value = ["ceph", "orch", " --verbose"]
        self._apply = MockApplyMixinTestWithShellOutput()
        self._apply.SERVICE_NAME = "rgw"
        self._apply.apply(config)
        assert mock_config.call_count == 2

    @mock.patch("ceph.ceph_admin.apply.config_dict_to_string")
    def test_apply_without_shell_output(self, mock_config):
        try:
            config = {
                "command": "apply",
                "service": "rgw",
                "args": {
                    "all-available-devices": True,
                    "placement": {
                        "label": "rgw_south",
                        "nodes": ["node1", "["],
                        "limit": 3,
                        "sep": "",
                        "count-per-host": 1,
                    },
                    "dry-run": True,
                },
                "verify": False,
                "base_cmd_args": {"verbose": True},
                "pos_args": ["node1", "dev/vdb", "dev"],
            }
            mock_config.return_value = ["ceph", "orch", " --verbose"]
            self._apply = MockApplyMixinTestWithOutShellOutput()
            self._apply.SERVICE_NAME = "rgw"
            self._apply.apply(config)
        except OrchApplyServiceFailure:
            assert self._apply.SERVICE_NAME == "rgw"
        assert mock_config.call_count == 2

    @mock.patch("ceph.ceph_admin.apply.config_dict_to_string")
    def test_apply_without_service_output(self, mock_config):
        try:
            config = {
                "command": "apply",
                "service": "rgw",
                "args": {
                    "all-available-devices": True,
                    "placement": {
                        "label": "rgw_south",
                        "nodes": ["node1", "*"],
                        "sep": "",
                        "count-per-host": 1,
                    },
                    "dry-run": True,
                },
                "verify": False,
                "base_cmd_args": {"verbose": True},
                "pos_args": ["node1", "dev/vdb", "dev"],
            }
            mock_config.return_value = ["ceph", "orch", " --verbose"]
            self._apply = MockApplyMixinTestWithOutServiceOutput()
            self._apply.SERVICE_NAME = "rgw"
            self._apply.apply(config)
        except OrchApplyServiceFailure:
            assert self._apply.SERVICE_NAME == "rgw"
        assert mock_config.call_count == 2

    @mock.patch("ceph.ceph_admin.apply.config_dict_to_string")
    def test_apply_without_placement(self, mock_config):
        try:
            config_without_placement = {
                "command": "apply",
                "service": "rgw",
                "args": {
                    "all-available-devices": True,
                    "dry-run": True,
                },
                "verify": False,
                "base_cmd_args": {"verbose": True},
                "pos_args": ["node1", "dev/vdb", "dev"],
            }
            mock_config.return_value = ["ceph", "orch", " --verbose"]
            self._apply = MockApplyMixinTestWithOutServiceOutput()
            self._apply.SERVICE_NAME = "rgw"
            self._apply.apply(config_without_placement)
        except OrchApplyServiceFailure:
            assert self._apply.SERVICE_NAME == "rgw"
        assert mock_config.call_count == 2


if __name__ == "__main__":
    pytest.main()

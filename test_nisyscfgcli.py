from unittest import TestCase
import nisyscfg.system
import nisyscfg.hardware_resource
from click.testing import CliRunner
from nisyscfgcli import nisyscfgcli
from unittest.mock import patch


class Mock_NI_Hardware_Item:
    def __init__(self, expert_user_alias, product_name):
        self.expert_user_alias = expert_user_alias
        self.product_name = product_name

    def get_property(self, name, default):
        return self.product_name

    def rename(self, new_name):
        return None

    def delete(self):
        return None

    def self_test(self):
        return None

    def upgrade_firmware(self, version):
        return None


fake_1 = Mock_NI_Hardware_Item("A", "NI_Product")
fake_2 = Mock_NI_Hardware_Item("B", "NI_Product")
fake_3 = Mock_NI_Hardware_Item("C", "NI_Product")
fake_4 = Mock_NI_Hardware_Item("D", "NI_Product")
example_data = [fake_1, fake_2, fake_3]


# =======================================================List Tests=====================================================
class TestListCommand(TestCase):
    def test_list_no_flags(self):
        with patch.object(
            nisyscfg.system.Session,
            "find_hardware",
            return_value=[Mock_NI_Hardware_Item("A", "NI_Product")],
        ):
            runner = CliRunner()
            command = "list"
            result = runner.invoke(nisyscfgcli, [command])
            assert "A" in result.output
            assert result.exit_code == 0

    def test_list_verbose_flag(self):
        with patch.object(
            nisyscfg.system.Session,
            "find_hardware",
            return_value=[Mock_NI_Hardware_Item("A", "NI_Product")],
        ):
            runner = CliRunner()
            command = "list"
            flag = "-v"
            result = runner.invoke(nisyscfgcli, [command, flag])
            assert "A" in result.output
            assert "--Product Name:" in result.output
            assert result.exit_code == 0

    # empty string is understood as 'localhost' so no need to put any arguments
    # this should not work as Click expects an argument when this flag is used
    def test_list_RT_with_flag_no_arg(self):
        runner = CliRunner()
        command = "list"
        flag = "-r"
        result = runner.invoke(nisyscfgcli, [command, flag])
        assert result.exit_code == 2

    def test_list_RT_with_flag_with_arg(self):
        runner = CliRunner()
        command = "list"
        flag = "-r"
        arg = "localhost"
        result = runner.invoke(nisyscfgcli, [command, flag, arg])
        assert result.exit_code == 0
        assert f"Scanning {arg}" in result.output


# =======================================================Delete Tests===================================================
class TestDeleteCommand(TestCase):
    def test_delete_non_existing_device(self):
        runner = CliRunner()
        result = runner.invoke(nisyscfgcli, ["delete", "x"])
        assert result.exit_code == 0
        assert "retry" in result.output

    def test_delete_existing_device(self):
        assert 0 == 0
        with patch.object(
            nisyscfg.system.Session,
            "find_hardware",
            return_value=[Mock_NI_Hardware_Item("A", "NI_Product")],
        ):
            runner = CliRunner()
            result = runner.invoke(nisyscfgcli, ["delete", "A"])
            assert result.exit_code == 1
            assert "you sure" in result.output

    def test_delete_with_force_flag(self):
        with patch.object(
            nisyscfg.system.Session,
            "find_hardware",
            return_value=[Mock_NI_Hardware_Item("A", "NI_Product")],
        ):
            runner = CliRunner()
            name = fake_1.expert_user_alias
            command = "delete"
            flag = "-y"
            result = runner.invoke(nisyscfgcli, [command, flag, name])
            assert result.exit_code == 0
            assert "deleted" in result.output


# =======================================================Rename Tests===================================================
class TestRenameCommand(TestCase):
    def test_rename_no_args(self):
        runner = CliRunner()
        command = "rename"
        result = runner.invoke(nisyscfgcli, [command])
        assert result.exit_code == 2

    # doesnt let the user rename with empty string
    def test_rename_one_arg(self):
        runner = CliRunner()
        command = "rename"
        name = "name"
        result = runner.invoke(nisyscfgcli, [command, name])
        assert result.exit_code == 2

    def test_rename_with_not_available_device(self):
        runner = CliRunner()
        command = "rename"
        name_1 = "not real"
        name_2 = "not real"
        result = runner.invoke(nisyscfgcli, [command, name_1, name_2])
        assert result.exit_code == 0
        assert "No items with matching alias" in result.output

    def test_rename_to_existing_name(self):
        with patch.object(
            nisyscfg.system.Session, "find_hardware", return_value=example_data
        ):
            runner = CliRunner()
            command = "rename"
            name_1 = fake_1.expert_user_alias
            name_2 = fake_3.expert_user_alias
            result = runner.invoke(nisyscfgcli, [command, name_1, name_2])
            assert result.exit_code == 0
            assert "already in use" in result.output

    def test_rename_with_everything_correct(self):
        with patch.object(
            nisyscfg.system.Session, "find_hardware", return_value=example_data
        ):
            runner = CliRunner()
            command = "rename"
            name_1 = fake_1.expert_user_alias
            name_2 = fake_4.expert_user_alias
            result = runner.invoke(nisyscfgcli, [command, name_1, name_2])
            assert result.exit_code == 0
            assert "Rename successful!" in result.output


# =======================================================Info Tests=====================================================
class TestInfoCommand(TestCase):
    def test_info_with_not_available_device(self):
        runner = CliRunner()
        command = "info"
        result = runner.invoke(nisyscfgcli, [command])
        assert result.exit_code == 2

    def test_info_with_available_device(self):
        with patch.object(
            nisyscfg.system.Session, "find_hardware", return_value=example_data
        ):
            runner = CliRunner()
            command = "info"
            name = fake_1.expert_user_alias
            result = runner.invoke(nisyscfgcli, [command, name])
            assert result.exit_code == 0
            assert "--Product Name:" in result.output


# =======================================================self_test Tests================================================
class TestSelfTestCommand(TestCase):
    def test_self_test_with_no_alias(self):
        runner = CliRunner()
        command = "self_test"
        result = runner.invoke(nisyscfgcli, [command])
        assert result.exit_code == 2

    def test_self_test_with_non_existing_alias(self):
        runner = CliRunner()
        command = "self_test"
        alias = "nothing"
        result = runner.invoke(nisyscfgcli, [command, alias])
        assert result.exit_code == 0
        assert "No items with matching alias" in result.output

    def test_self_test_with_existing_alias(self):
        with patch.object(
            nisyscfg.system.Session, "find_hardware", return_value=example_data
        ):
            runner = CliRunner()
            command = "self_test"
            alias = fake_1.expert_user_alias
            result = runner.invoke(nisyscfgcli, [command, alias])
            assert result.exit_code == 0
            assert "completed successfully" in result.output


# =======================================================upgrade_firmware Tests=========================================
class TestUpgradeFirmwareCommand(TestCase):
    def test_upgrade_firmware_with_no_alias(self):
        runner = CliRunner()
        command = "upgrade_firmware"
        result = runner.invoke(nisyscfgcli, [command])
        assert result.exit_code == 2

    def test_upgrade_firmware_with_non_existing_alias(self):
        runner = CliRunner()
        command = "upgrade_firmware"
        alias = "nothing"
        result = runner.invoke(nisyscfgcli, [command, alias])
        assert result.exit_code == 0
        assert "No items with matching alias" in result.output

    def test_upgrade_firmware_with_existing_alias(self):
        with patch.object(
            nisyscfg.system.Session, "find_hardware", return_value=example_data
        ):
            runner = CliRunner()
            command = "upgrade_firmware"
            alias = fake_1.expert_user_alias
            result = runner.invoke(nisyscfgcli, [command, alias])
            assert result.exit_code == 0
            assert "Firmware upgraded" in result.output

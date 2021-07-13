#!/usr/bin/python3
import click
import nisyscfg
from nisyscfg.errors import LibraryError


class DeviceNotFoundError(Exception):
    pass

@click.group()
def nisyscfgcli():
    """Manipulate hardware resources detected by NI System Configuration API
    ========================================================================"""


@nisyscfgcli.command(name="list")
@click.option(
    "-v", is_flag=True, help=": displays detailed information about all aliases"
)
@click.option("-r",
              default="",
              help=": specify IP address or hostname of remote target"
              )
def list_command(v, r):
    """: displays all NI aliases"""
    with nisyscfg.Session(r) as nisyscfg_session:
        _list_aliases(v, r, nisyscfg_session)


@click.command(name="rename")
@click.argument("old_alias")
@click.argument("new_alias")
@click.option("-r", help=": specify IP address or hostname of remote target", default="")
def rename_command(old_alias, new_alias, r):
    """: change the alias of an item <old name> <new name>"""
    with nisyscfg.Session(r) as nisyscfg_session:
        if not _valid_alias(old_alias, nisyscfg_session):
            return
        if _valid_alias(new_alias, nisyscfg_session, rename_flag=True):
            print(f"The name '{new_alias}' is already in use. Try a different name.")
            return
        _rename_hardware(old_alias, new_alias, nisyscfg_session)


@click.command(name="delete")
@click.argument("alias_name")
@click.option("-y", is_flag=True, help=": Bypasses the '[y/n]?' check")
@click.option("-r", help=": specify IP address or hostname of remote target", default="")
def delete_command(alias_name, y, r):
    """: delete the specified item"""
    with nisyscfg.Session(r) as nisyscfg_session:
        if not _valid_alias(alias_name, nisyscfg_session):
            return
        delete_helper(y, alias_name, nisyscfg_session)


@click.command(name="info")
@click.argument("alias_name")
@click.option("-r", help=": specify IP address or hostname of remote target", default="")
def info_command(alias_name, r):
    """: provides detailed info about the specified alias"""
    with nisyscfg.Session(r) as nisyscfg_session:
        if not _valid_alias(alias_name, nisyscfg_session):
            return
        _info_alias(alias_name, nisyscfg_session)


@click.command(name="self_test")
@click.argument("alias_name")
@click.option("-r", help=": specify IP address or hostname of remote target", default="")
def self_test_command(alias_name, r):
    """: verifies alias is able to perform basic I/O functions"""
    with nisyscfg.Session(r) as nisyscfg_session:
        if not _valid_alias(alias_name, nisyscfg_session):
            return
        _self_test_alias(alias_name, nisyscfg_session)


@click.command(name="upgrade_firmware")
@click.argument("alias_name")
@click.option("-v", help=": update firmware to specified version")
@click.option("-r", help=": specify IP address or hostname of remote target", default="")
def upgrade_firmware_command(alias_name, v, r):
    """: upgrades alias firmware to latest version"""
    with nisyscfg.Session(r) as nisyscfg_session:
        if not _valid_alias(alias_name, nisyscfg_session):
            return
        _upgrade_alias_firmware(alias_name, v, nisyscfg_session)




# ======================================================================================================================


def _list_aliases(verbose, r, session):
    print(f"Scanning {r if r else 'localhost'} for devices...\n")
    alias_filter = session.create_filter()
    alias_filter.is_ni_product = True
    alias_filter.is_device = True
    for alias in session.find_hardware(alias_filter):
        _print_hardware_info(alias, verbose)


def _rename_hardware(old_name, new_name, session):
    hardware_to_rename = _get_hardware(session, old_name)
    hardware_to_rename.rename(new_name)
    print(f"Rename successful! '{old_name}' renamed to '{new_name}'")


def _del_hardware(alias, session):
    hardware_to_delete = _get_hardware(session, alias)
    hardware_to_delete.delete()


def delete_helper(flag, alias, session):
    if flag:
        _del_hardware(alias, session)
        print(f"Item '{alias}' deleted.")

        return
    while True:
        print(f"Are you sure you want to delete item {alias} [y/n]?")
        response = input()
        response = response.lower()
        if response == "y" or response == "yes":
            _del_hardware(alias, session)
            print(f"Item {alias} deleted")
            break
        if response == "n" or response == "no":
            print("Delete aborted")
            break
        else:
            continue


def _info_alias(alias, session):
    hardware_to_get_info = _get_hardware(session, alias)
    _print_hardware_info(hardware_to_get_info, verbose=True)


def _self_test_alias(alias, session):
    hardware_to_test = _get_hardware(session, alias)
    try:
        hardware_to_test.self_test()
        print("Self test completed successfully!")
    except LibraryError as err:
        print("Self test failed")
        print("Errors: ", err)
    return


def _upgrade_alias_firmware(alias, version, session):
    hardware_to_upgrade = _get_hardware(session, alias)
    try:
        hardware_to_upgrade.upgrade_firmware(str(version) if version else "0")
        print("Firmware upgraded to latest version")
    except LibraryError as err:
        if err.code == nisyscfg.errors.Status.RESOURCE_IS_SIMULATED:
            print("Firmware upgrades not available for simulated aliases")
            return
        else:
            print("Firmware Upgrade Failed")
            print("Error: ", err)
            return


def _get_hardware(session, alias):
    hardware_filter = session.create_filter()
    hardware_filter.user_alias = alias
    hardware_found = next(iter(session.find_hardware(hardware_filter)))
    return hardware_found


def _valid_alias(alias, session, rename_flag=False):
    available_aliases = _available_aliases(session)
    if alias in available_aliases:
        return True
    if rename_flag:
        return False
    print(
        f"No items with matching alias '{alias}' Please retry with a valid alias. "
        f"Use 'nisyscfgcli list' to see all available aliases.\n"
    )
    return False


def _available_aliases(session):
    alias_filter = session.create_filter()
    alias_filter.is_ni_product = True
    alias_filter.is_device = True
    aliases = []
    for alias in session.find_hardware(alias_filter):
        aliases.append(alias.expert_user_alias[0])
    return aliases


def _print_hardware_info(alias, verbose):
    if verbose:
        attributes = {"Product Name": alias.get_property("product_name", default=""),
                      "IP Address": alias.get_property("tcp_ip_address", default=""),
                      "Slot": alias.get_property("slot_number", default=""),
                      "Serial Number": alias.get_property("serial_number", default=""),
                      "Vendor ID": alias.get_property("vendor_id", default=""),
                      "Product ID": alias.get_property("product_id", default=""),
                      "Firmware Revision": alias.get_property("firmware_revision", default=""),
                      "Current Temp": alias.get_property("current_temp", default=""),
                      "Number of Slots": alias.get_property("number_of_slots", default=""),
                      }
        _print_alias_name(alias, verbose)
        for label, attribute in attributes.items():
            _print_tag(label, attribute)
        print()
    else:
        _print_alias_name(alias, verbose)


def _print_tag(label, attribute):
    if attribute:
        print(f"--{label+':':<30}{attribute}")


def _print_alias_name(alias, verbose):
    try:
        print(alias.expert_user_alias[0])
    except DeviceNotFoundError:
        if verbose:
            return
        pass
        
if __name__ == '__main__':
	nisyscfgcli.add_command(list_command)
	nisyscfgcli.add_command(rename_command)
	nisyscfgcli.add_command(delete_command)
	nisyscfgcli.add_command(info_command)
	nisyscfgcli.add_command(self_test_command)
	nisyscfgcli.add_command(upgrade_firmware_command)
	nisyscfgcli()

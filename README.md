# clean_leases

## Overview

`clean_leases` is a Python script designed to clean up DHCP lease files by removing entries associated with specific MAC addresses retrieved from an LDAP server. This is useful for maintaining a clean and accurate DHCP lease file, ensuring that outdated or unwanted leases are removed.

The script performs the following steps:
1. Connects to an LDAP server to retrieve a list of MAC addresses.
2. Processes the DHCP lease file to identify and remove leases associated with the retrieved MAC addresses.
3. Creates a backup of the original lease file before applying changes.
4. Updates the lease file with the cleaned version.

## Prerequisites

Before running the script, ensure the following:
- Python 3 is installed on your system.
- The `python-ldap` library is installed. You can install it using:
  ```bash
  pip install python-ldap
```

## Usage

### Running the Script

To execute the script, use the following command:

```bash
python remove_leases.py
```

### Configuration

The script uses the following default settings:
- **LDAP Server**: `ldap://localhost`
- **LDAP Base DN**: `cn=group1,cn=INTERNAL,cn=DHCP Config,dc=instituto,dc=extremadura,dc=es`
- **DHCP Lease File**: `/var/lib/dhcp/dhcpd.leases`

If you need to modify these settings, you can edit the script directly or pass arguments (if implemented).

### Example

Suppose you have the following DHCP lease file (`dhcpd.leases`):

```
lease 192.168.1.10 {
  starts 3 2023/10/11 12:00:00;
  ends 3 2023/10/11 14:00:00;
  hardware ethernet 00:11:22:33:44:55;
}
lease 192.168.1.11 {
  starts 3 2023/10/11 12:00:00;
  ends 3 2023/10/11 14:00:00;
  hardware ethernet 66:77:88:99:AA:BB;
}
```

And the LDAP server contains the following MAC addresses:

```
00:11:22:33:44:55
```

Run the script:

```bash
python remove_leases.py
```

### Output

The script will:
1. Retrieve MAC addresses from the LDAP server.
2. Create a backup of the original lease file (`dhcpd.leases.bak.<timestamp>`).
3. Remove the lease associated with the MAC address `00:11:22:33:44:55`.

The updated `dhcpd.leases` file will look like this:

```
lease 192.168.1.11 {
  starts 3 2023/10/11 12:00:00;
  ends 3 2023/10/11 14:00:00;
  hardware ethernet 66:77:88:99:AA:BB;
}
```

The script will also print a summary:

```
Getting MACs from LDAP...
Found 1 MAC addresses to process.
Processing leases file...
Removing lease with MAC: 00:11:22:33:44:55
Process completed.
Removed 1 lease entries out of a total of 2.
A backup has been created at /var/lib/dhcp/dhcpd.leases.bak.<timestamp>
The file /var/lib/dhcp/dhcpd.leases has been updated.
```

### Notes

- Ensure the script has the necessary permissions to read and write to the lease file and its directory.
- Always verify the cleaned lease file to ensure no unintended changes were made.
- If the LDAP server is unreachable or misconfigured, the script will log an error and exit without making changes.
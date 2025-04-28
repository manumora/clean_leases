#!/usr/bin/env python3

import os
import re
import subprocess
import tempfile
import shutil
from datetime import datetime

def get_macs_from_ldap():
    print("Getting MACs from LDAP...")
    
    import ldap
    
    ldap_server = "ldap://localhost"
    ldap_base = "cn=group1,cn=INTERNAL,cn=DHCP Config,dc=instituto,dc=extremadura,dc=es"
    ldap_filter = "(objectClass=dhcpHost)"
    ldap_attrs = ["dhcpHWAddress"]
    
    macs = []
    
    try:
        ldap_conn = ldap.initialize(ldap_server)
        ldap_conn.set_option(ldap.OPT_REFERRALS, 0)

        results = ldap_conn.search_s(ldap_base, ldap.SCOPE_SUBTREE, ldap_filter, ldap_attrs)
        
        for _, entry in results:
            if entry and 'dhcpHWAddress' in entry:
                for hw_address in entry['dhcpHWAddress']:
                    if isinstance(hw_address, bytes):
                        hw_address = hw_address.decode('utf-8')

                    match = re.search(r'ethernet\s+([0-9a-f:]+)', hw_address.lower())
                    if match:
                        macs.append(match.group(1))

        ldap_conn.unbind_s()
        return macs
        
    except ldap.LDAPError as e:
        print(f"LDAP connection error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def process_leases_file(leases_file, macs):
    if not os.path.exists(leases_file):
        print(f"Error: The leases file {leases_file} does not exist.")
        return False
    
    print("Processing leases file...")
    temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
    
    in_lease_block = False
    skip_current_block = False
    current_block = []
    current_mac = None
    
    with open(leases_file, 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            
            if re.match(r'^lease\s', line):
                if in_lease_block and not skip_current_block:
                    temp_file.write('\n'.join(current_block) + '\n')
                
                in_lease_block = True
                skip_current_block = False
                current_block = [line]
                current_mac = None
            
            elif in_lease_block:
                current_block.append(line)
                
                mac_match = re.search(r'hardware\s+ethernet\s+([0-9a-f:]+);', line.lower())
                if mac_match:
                    found_mac = mac_match.group(1)
                    current_mac = found_mac
                    if found_mac.lower() in [m.lower() for m in macs]:
                        skip_current_block = True
                
                if line.strip() == '}':
                    if not skip_current_block:
                        temp_file.write('\n'.join(current_block) + '\n')
                    else:
                        print(f"Removing lease with MAC: {current_mac}")
                    
                    in_lease_block = False
                    current_block = []
            
            else:
                temp_file.write(line + '\n')
    
    temp_file.close()
    return temp_file.name

def main():
    leases_file = "/var/lib/dhcp/dhcpd.leases"
    
    macs = get_macs_from_ldap()
    
    if not macs:
        print("No MACs found in LDAP or there was an error during the search.")
        return 1
    
    print(f"Found {len(macs)} MAC addresses to process.")
    
    new_file = process_leases_file(leases_file, macs)
    if not new_file:
        return 1
    
    with open(leases_file, 'r') as f:
        original_count = len(re.findall(r'^lease\s', f.read(), re.MULTILINE))
    
    with open(new_file, 'r') as f:
        new_count = len(re.findall(r'^lease\s', f.read(), re.MULTILINE))
    
    removed_count = original_count - new_count
    
    print("Process completed.")
    print(f"Removed {removed_count} lease entries out of a total of {original_count}.")
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_file = f"{leases_file}.bak.{timestamp}"
    shutil.copy2(leases_file, backup_file)
    print(f"A backup has been created at {backup_file}")
    
    shutil.copy2(new_file, leases_file)
    os.unlink(new_file)
    print(f"The file {leases_file} has been updated.")
    
    return 0

if __name__ == "__main__":
    exit(main())

# Netmiko-Cisco-Switch-FTP-Firmware-Downloader
Netmiko Cisco Switch FTP Firmware Downloader

This script was written to prep ~100 Cisco 37XX and 38XX switches for a firmware upgrade. It uses Netmiko Python library for handling SSH sessions, and PrettyTables for displaying output. It is also multi-threaded, so it connects to all the switches simultaneously.

Overview:
- Read all hostnames from switch_list.txt, save as a list
- For each hostname in the list, start a new thread, passing hostname to it
- Each thread connects to a switch using Netmiko library
- Uses 'USER' and 'PASSWORD' variables at the top to login to switch
- Issues 'show inv' command on switch
- Checks output to see if it contains 3750 or 3850
- Issues 'show ver' command and checks output to determine if the switch has already been upgraded
- If the switch has not been upgraded yet, it issues 'dir flash:' to check to see if the new .bin firmware file exists
- If the switch is a 3850, it will issue the 'software clean' command to delete old firmwares and make room for the new one
- If the new firmware is not present on the switch, it will issue the command 'copy ftp://cisco:cisco@10.1.1.2/c3750e-universalk9-mz.150-2.SE11.bin flash:' to download the firmware over FTP (using different firmware for each switch model)
- If the the FTP transfer fails due to not enough disk space, it will save that to the 'no_space' var for later output
- If the FTP transfer was successful, it will issue 'dir flash:' again to verify the new firmware is there
- Finally it will add a row to the 'PrettyTable'
- When all threads complete, the 'PrettyTable' will be output. Example below:

<pre>
+----------------+-------+------------------+------------------+--------------+---------+--------------+--------------------+
|    Hostname    | Model | Software cleaned | Already upgraded | Already FTPd |  FTP    | BIN verified |     Enough space   |
+----------------+-------+------------------+------------------+--------------+---------+--------------+--------------------+
|  switch1main   |  3850 |       No         |       Yes        |      No      |  N/A    |     N/A      |         Good       |
|    switch2f    |  3850 |       No         |       Yes        |      No      |  N/A    |     N/A      |         Good       |
|    switch3s    |  3750 |       N/A        |       Yes        |      No      |  N/A    |     N/A      |         Good       |
|   switch9xds   |  3750 |       N/A        |        No        |      No      | Success |     Yes      |         Good       |
|    switchsf    |  3750 |       N/A        |        No        |      No      | Failed  |     No       |         Bad        |
|    switch2d    |  3750 |       N/A        |        No        |     Yes      |  N/A    |     N/A      |         Good       |
+----------------+-------+------------------+------------------+--------------+--------+--------------+--------------------+
</pre>

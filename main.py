import threading
from Queue import Queue
from netmiko import ConnectHandler
from datetime import datetime
from prettytable import PrettyTable

USER = 'username'
PASSWORD = 'password'


def ssh_session(row, output_q):
    no_space = "Good"
    output_dict = {}
    hostname = row
    bin_verified = "N/A"
    software_cleaned = "Unknown"
    already_ftpd = "No"
    switch = {
        'device_type': 'cisco_ios',
        'ip': hostname,
        'username': USER,
        'password': PASSWORD,
        'port': 22,  # optional, defaults to 22
        'secret': '',  # optional, defaults to ''
        'verbose': False,  # optional, defaults to False
    }

    net_connect = ConnectHandler(**switch)
    output = net_connect.send_command_timing('show inv', delay_factor=4, max_loops=1000)

    output_list = []
    output_list.append(output)
    model = "None"

    if "3750" in output:
        model = "3750"
    elif "3850" in output:
        model = "3850"

    if model == "3750":
        software_cleaned = "N/A"

    output = net_connect.send_command_timing('show ver', delay_factor=4, max_loops=1000)
    output_list.append(output)
    already_upgraded = "No"

    if model == "3750":
        if "15.0(2)SE11" in output:
            already_upgraded = "Yes"


    elif model == "3850":
        if "16.3.3" in output:
            already_upgraded = "Yes"

    ftp_success = "Failed"

    if already_upgraded == "Yes":
        ftp_success = "N/A"

    if already_upgraded == "No":

        if model == "3750":
            output = net_connect.send_command_timing('dir flash:', delay_factor=4, max_loops=1000)
            output_list.append(output)
            if "c3750e-universalk9-mz.150-2.SE11.bin" in output:
                already_ftpd = "Yes"
                ftp_success = "N/A"

            if already_ftpd == "No":
                output = net_connect.send_command_timing('copy ftp://cisco:cisco@10.1.1.2/c3750e-universalk9-mz.150-2.SE11.bin flash:', delay_factor=30, max_loops=1000)
                output_list.append(output)
                if 'Destination filename' in output:
                    # switch back to send_command() here as this might be slow
                    output += net_connect.send_command_timing('c3750e-universalk9-mz.150-2.SE11.bin', delay_factor=30, max_loops=1000)
                    output_list.append(output)
                if "[OK " in output:
                    ftp_success = "Success"
                    output = net_connect.send_command_timing('dir flash:', delay_factor=4, max_loops=1000)
                    output_list.append(output)
                    if "c3750e-universalk9-mz.150-2.SE11.bin" in output:
                        bin_verified = "Success"
                    else:
                        bin_verified = "Failed"
                if "No space" in output:
                    outfile.write(hostname + ': No space left on device\n')
                    no_space = "Bad"


        elif model == "3850":
            output = net_connect.send_command_timing('dir flash:', delay_factor=4, max_loops=1000)
            output_list.append(output)
            if "cat3k_caa-universalk9.16.03.03.SPA.bin" in output:
                already_ftpd = "Yes"
                ftp_success = "N/A"
                software_cleaned = "No"

            else:
                output = net_connect.send_command_timing('software clean force', delay_factor=4, max_loops=1000)
                output_list.append(output)

                if "Clean up completed" in output:
                    software_cleaned = "Yes"

                elif "No unnecessary" in output:
                    software_cleaned = "Not needed"

            if already_ftpd == "No":
                output = net_connect.send_command_timing('copy ftp://cisco:ciso@10.1.1.2/cat3k_caa-universalk9.16.03.03.SPA.bin flash:', delay_factor=6, max_loops=1000)
                output_list.append(output)
                if 'Destination filename' in output:
                    # switch back to send_command() here as this might be slow
                    output += net_connect.send_command_timing('cat3k_caa-universalk9.16.03.03.SPA.bin', delay_factor=50, max_loops=1000)
                    output_list.append(output)

                if "[OK " in output:
                    ftp_success = "Success"
                    output = net_connect.send_command_timing('dir flash:', delay_factor=4, max_loops=1000)
                    output_list.append(output)
                    if "cat3k_caa-universalk9.16.03.03.SPA.bin" in output:
                        bin_verified = "Success"
                    else:
                        bin_verified = "Fail"
                if "No space" in output:
                    outfile.write(hostname + ': No space left on device\n')

    t.add_row([hostname, str(model), str(software_cleaned), already_upgraded, already_ftpd, ftp_success, bin_verified, no_space])
    output_list.append(t)
    print t
    # Add data to the queue
    final_output = ''
    for item in output_list:
        final_output += '\n' + str(item)

    output_dict['@@@@@@@@@@@' + hostname + '@@@@@@@@@@@'] = final_output
    output_q.put(output_dict)
    print output_dict['@@@@@@@@@@@' + hostname + '@@@@@@@@@@@']


if __name__ == "__main__":

    print datetime.now()

    output_q = Queue()
    t = PrettyTable(
        ['Hostname', 'Model', 'Software cleaned', 'Already upgraded', 'Already FTPd', 'FTP', 'BIN verified', 'Enough space'])

    with open("switch_list.txt") as f:
        switch_dump = f.readlines()

    switch_list = [x.strip() for x in switch_dump]

    outfile = open('output-threading.txt', 'w')

    for row in switch_list:
        # Start all threads
        print row
        my_thread = threading.Thread(target=ssh_session, args=(row, output_q))
        my_thread.start()

    # Wait for all threads to complete
    main_thread = threading.currentThread()
    for some_thread in threading.enumerate():
        if some_thread != main_thread:
            some_thread.join()

    # Retrieve everything off the queue
    while not output_q.empty():
        my_dict = output_q.get()
        for k, val in my_dict.iteritems():
            print k
            print val

            # Write info to file
            # outfile.write(output)

    outfile.close()
    print datetime.now()

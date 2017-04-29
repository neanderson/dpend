#PAPA - Palto Alto Performance Analyzer
#DP Monitor Parse

import re
import os
import time
import sys
from calendar import timegm

# Variables imported from bash

#dp_file = os.environ["dp_file"]
dp_file = "s3-dp0"
dp_name = dp_file.replace('s','Slot ')
dp_name = dp_name.replace('-dp',' DP ')

#num_panio = os.environ["num_panio"]
num_panio = 315

# Redirect stdout to file and open other output files

orig_stdout = sys.stdout
out_file = open('papa_high_all', 'w')
sys.stdout = out_file

high_cpu = open('papa_high_cpu', 'a')
print(dp_name + "\nHigh CPU", end="\n", file=high_cpu)
high_res = open('papa_high_res', 'a')
print(dp_name + "\nHigh Resource Utilization", end="\n", file=high_res)
high_panio_timestamps = open('papa_high_panio_timestamps', 'a')
print(dp_name + "\nPanio Timestamps with High CPU or Resource Utilization (RUN)\n\tNumber of matches follow timestamps", end="\n", file=high_panio_timestamps)
panio_timestamps = open('papa_panio_timestamps', 'a')
print(dp_name + "\nAll Panio Timestamps", end="\n", file=panio_timestamps)

# Variables and arrays to store data

panio_timestamp = [None] * num_panio
panio_epoch = [None] * num_panio

cpu_load_sampling = [None] * num_panio
for i in range(num_panio):
    cpu_load_sampling[i] = [None] * 15
cpu_load_sampling_groups = [ "flow_lookup", "flow_fastpath", "flow_slowpath", "flow_forwarding", "flow_mgmt", "flow_ctrl", "nac_result", "flow_np", "dfa_result", "module_internal", "aho_result", "zip_result", "pktlog_forwarding", "lwm", "flow_host" ]

cpu_load_15_sec = [None] * num_panio
for i in range(num_panio):
    cpu_load_15_sec[i] = [None] * 30

res_ut_15_sec = [None] * num_panio
for i in range(num_panio):
    res_ut_15_sec[i] = [None] * 4

cpu_load_15_min = [None] * num_panio
for i in range(num_panio):
    cpu_load_15_min[i] = [None] * 60

res_ut_15_min = [None] * num_panio
for i in range(num_panio):
    res_ut_15_min[i] = [None] * 8

# Variables to keep track of panio section

get_cpu_load_sampling = 0
get_cpu_load_15_sec = 0
get_res_ut_15_sec = 0
get_cpu_load_15_min = 0
get_res_ut_15_min = 0

# counter increments by one for each Panio section
# line_num increments by one only if a match is found within a particular Panio section

counter = -1
line_num = 0

# Keep track of high CPU, descriptors, and buffers

high_limit = 90
high_total = 0
high_cpu_sec_hit = 0
high_cpu_min_hit = 0
high_res_sec_hit = 0
num_high_res = [0,0]
num_high_res = [0,0]
high_cpu_load_sampling = []
high_cpu_load_15_sec = []
high_res_ut_15_sec = []
high_cpu_load_15_min = []
high_res_ut_15_min = []

# Variables to keep track of labels and print events

panio_time_print = True
high_event_print = True
high_cpu_sec_hit = 0
high_cpu_min_hit = 0
high_res_sec_hit = 0
event_time_print = True
cpu_print = True
core_label = ""
avg_max = ":     avg max avg max avg max avg max avg max avg max avg max avg max"

# Function to convert panio timestamp to epoch time

def epoch_time( panio_time ):
    utc_time = time.strptime(panio_time, "%Y-%m-%d %H:%M:%S.%f")
    ep_time = timegm(utc_time)
    return ep_time

# Function to convert epoch time to standard time

def standard_time( epoch_time ):
    std_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(epoch_time))
    return std_time

# Function to process CPU load sampling

def proc_cpu_load_sampling():

    global cpu_load_sampling

    for i in range(15):
        match_cpu_sampling = re.match(":{0}.*?(\d+)%".format(cpu_load_sampling_groups[i]), line)
        if match_cpu_sampling:
            cpu_load_sampling[counter][i] = match_cpu_sampling.group(1)

# Function to process resource utilization

def proc_res_ut( time_sec ):

    global line_num, res_label, panio_time_print, high_event_print, num_high_res
    global res_ut_15_sec, res_ut_15_min 

    match_res_label = re.match(":(s|p).*", line)
    if match_res_label:
        res_label = match_res_label.group(0)

    match_res_ut = re.match(": .*?(\d+).*", line)
    if match_res_ut:
        if time_sec:
            res_ut_15_sec[counter][line_num] = match_res_ut.group(0)
            match_high_res = re.findall("[9][0-9]|100", res_ut_15_sec[counter][line_num]) 
        else:
            res_ut_15_min[counter][line_num] = match_res_ut.group(0)
            match_high_res = re.findall("[9][0-9]|100", res_ut_15_min[counter][line_num])
        if match_high_res:

            # Keep track of matches
            
            if time_sec:
                num_high_res[0] += len(match_high_res)
            else:
                num_high_res[1] += len(match_high_res)

            # Print panio timestamps

            if panio_time_print:
                print(panio_timestamp[counter])
                print(panio_timestamp[counter], end="", file=high_res)
                print("\n" + panio_timestamp[counter], end=" - ", file=high_panio_timestamps)
                panio_time_print = False

            if high_event_print:

            # Print high resource utilization if this is the first instance

                if time_sec:
                    print("\n\tHigh Resource Utilization Last 15 Seconds:\n")
                    print("\n\tHigh Resource Utilization Last 15 Seconds:\n", end="", file=high_res)
                else:
                    print("\n\tHigh Resource Utilization Last 15 Minutes:\n")
                    print("\n\tHigh Resource Utilization Last 15 Seconds:\n", end="", file=high_res)
                high_event_print = False

        # Print the label and the line with high resource utilization

            print("\t\t" + res_label)
            print("\t\t" + res_label + "\n", end="", file=high_res)
            if time_sec:
                print("\t\t" + res_ut_15_sec[counter][line_num] + "\n")
                print("\t\t" + res_ut_15_sec[counter][line_num] + "\n", end="", file=high_res)
            else:
                print("\t\t" + res_ut_15_min[counter][line_num] + "\n")
                print("\t\t" + res_ut_15_min[counter][line_num] + "\n", end="", file=high_res)

            line_num += 1

# Function to process CPU load

def proc_cpu_load( time_sec ):

    # Global variables (gasp!) to keep track of line numbers and labels
    
    global line_num, core_label, panio_time_print, high_event_print, event_time_print, num_high_cpu_sec, num_high_cpu_min
    global cpu_load_15_sec, cpu_load_15_min

    # Get the core label for the high CPU output

    match_core_label = re.match (":core.*", line)
    if match_core_label:
        core_label = match_core_label.group(0)

    # Get the CPU load per line

    match_cpu_load = re.match (": +(\d+).*", line)
    if match_cpu_load:
        if (time_sec):

            # Check if CPU load is higher than a certain number (15 seconds)

            cpu_load_15_sec[counter][line_num] = match_cpu_load.group(0)
            match_high_cpu = re.findall("[9][0-9]|100", cpu_load_15_sec[counter][line_num])
        else:

            # Check if CPU load is higher than a certain number (15 minutes)

            cpu_load_15_min[counter][line_num] = match_cpu_load.group(0)
            match_high_cpu = re.findall("[9][0-9]|100", cpu_load_15_min[counter][line_num])
        if match_high_cpu:

            # Keep track of matches

            if time_sec:
                num_high_cpu[0] += len(match_high_cpu)
            else:
                num_high_cpu[1] += len(match_high_cpu)

            # Print panio timestamps

            if panio_time_print:
                print(panio_timestamp[counter])
                print(panio_timestamp[counter], end="", file=high_cpu)
                print("\n" + panio_timestamp[counter], end=" - ", file=high_panio_timestamps)
                panio_time_print = False

            if high_event_print:

                # Print high CPU label if this is the first instance

                if time_sec:
                    print("\n\tHigh CPU Last 15 Seconds:\n")
                    print("\n\tHigh CPU Last 15 Seconds:\n", end="", file=high_cpu)
                else:
                    print("\n\tHigh CPU Last 15 Minutes:\n")
                    print("\n\tHigh CPU Last 15 Minutes:\n", end="", file=high_cpu)
                high_event_print = False
            
            # Determine high CPU time offset from panio time based on line number

            if time_sec:
                time_diff = line_num % 15
            else:
                time_diff = (line_num % 15) * 60
            event_time = epoch_time(panio_timestamp[counter]) - time_diff

            # Print the core label and the line with high CPU
            # Print the event timestamp only if it's the first instance for last 15 minutes
            # For the last 15 seconds, print the event timestamp every time

            if ((event_time_print and not time_sec) or time_sec):
                print("\t\t" + standard_time(event_time) + "\n")
                print("\t\t" + standard_time(event_time) + "\n", end="", file=high_cpu)
                event_time_print = False
            if time_sec:
                print("\t\t" + core_label + "\n\t\t" + cpu_load_15_sec[counter][line_num] + "\n")
                print("\t\t" + core_label + "\n\t\t" + cpu_load_15_sec[counter][line_num] + "\n", end="", file=high_cpu)
            else:
                print("\t\t" + core_label + "\n\t\t" + avg_max + "\n\t\t" + cpu_load_15_min[counter][line_num] + "\n")
                print("\t\t" + core_label + "\n\t\t" + avg_max + "\n\t\t" + cpu_load_15_min[counter][line_num] + "\n", end="", file=high_cpu) 
        
        line_num += 1

# The fun begins. Start parsing the DP monitor merged files

with open("s3-dp0-merged.log", 'rt') as f:
    for line in f:

        # Get panio timestamp

        match_panio_timestamp = re.match("^(.*?) \+0000  --- panio", line)
        if match_panio_timestamp:

            # Increment counter and make panio_time_print true
            # When high CPU/buffers/descriptors are found, Panio time should only be printed once, even when there are multiple instances within the same Panio time

            counter += 1
            panio_time_print = True
            num_high_cpu = [0,0]
            num_high_res = [0,0]

            # Convert Panio time to epoch time
            # Makes it easy to compute time differences on CPU load by line
            
            panio_timestamp[counter] = match_panio_timestamp.group(1)
            panio_epoch[counter] = epoch_time(panio_timestamp[counter])
        
        # Check for line ":CPU load sampling by group:"

        match_cpu_load_sampling_string = re.match(":CPU load sampling by group", line)
        if match_cpu_load_sampling_string:

            # Turn on CPU load sampling flag

            get_cpu_load_sampling = 1

        if (get_cpu_load_sampling == 1):
            proc_cpu_load_sampling()
                        
        # Check for line ":CPU load (%) during last 15 seconds:"

        match_cpu_load_15_sec_string = re.match(":CPU load \(%\) during last 15 seconds", line)
        if match_cpu_load_15_sec_string:

            # Turn off CPU load sampling flag
            # Turn on CPU load last 15 seconds flag
            # Reset line number

            get_cpu_load_15_sec = 1
            get_cpu_load_sampling = 0
            line_num = 0

        if (get_cpu_load_15_sec == 1):

            # Get CPU load during last 15 seconds
            # Passing "True" to time_sec in function proc_cpu_load

            proc_cpu_load(True)

        # Check for line ":Resource utilization (%) during last 15 seconds:" 

        match_res_ut_string = re.match(":Resource utilization \(%\) during last 15 seconds", line)
        if match_res_ut_string:
            get_res_ut_15_sec = 1
            get_cpu_load_15_sec = 0
            high_event_print = True
            line_num = 0

        if (get_res_ut_15_sec == 1):

            # Get resource utilization last 15 seconds
            
            proc_res_ut(True)

        # Check for line "Resource monitoring statistics (per minute):"

        match_res_mon_string = re.match(":Resource monitoring statistics \(per minute\)", line)
        if match_res_mon_string:
            
            # Done processing resource utilization last 15 seconds. Turn off flag
            # Turn on CPU load last 15 minutes flag
            # Reset print events and line number

            get_cpu_load_15_min = 1
            get_res_ut_15_sec = 0
            high_event_print = True
            event_time_print = True
            line_num = 0
        
        if (get_cpu_load_15_min == 1):

            # Get CPU load during last 15 minutes

            proc_cpu_load(False)

        # Check for line "Resource utilization (%) during last 15 minutes:"

        match_res_ut_string = re.match(":Resource utilization \(%\) during last 15 minutes", line)
        if match_res_ut_string:
            get_res_ut_15_min = 1
            get_cpu_load_15_min = 0
            high_event_print = True
            event_time_print = True
            line_num = 0

        if (get_res_ut_15_min == 1):
            
            # Get resource utilization last 15 minutes

            proc_res_ut(False)

        # End for now

        match_supported_sessions= re.match(":Number of sessions supported", line)
        if match_supported_sessions:
            get_res_ut_15_min = 0
            line_num = 0

            if (num_high_res[0] > 0 or num_high_res[1] > 0 or num_high_cpu[0] > 0 or num_high_cpu[1] > 0):
                print("RUN (sec): " + str(num_high_res[0]), end=" ", file=high_panio_timestamps)
                print("CPU (sec): " + str(num_high_cpu[0]), end=" ", file=high_panio_timestamps)
                print("RUN (min): " + str(num_high_res[1]), end=" ", file=high_panio_timestamps)
                print("CPU (min): " + str(num_high_cpu[1]), end=" ", file=high_panio_timestamps)

# Close all open files
f.close()
sys.stdout = orig_stdout
out_file.close()
high_cpu.close()
high_res.close()
high_panio_timestamps.close()
panio_timestamps.close()

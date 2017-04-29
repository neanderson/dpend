#dpend

import re
import os
import time
import sys
from calendar import timegm

# Variables imported from bash

dp_file = os.environ["dp_file"]
dp_name = dp_file.replace('s','Slot ')
dp_name = dp_name.replace('dp', 'DP ')
dp_name = dp_name.replace('-','')
dp_name = dp_name.replace('merged.log','')
dp_out = dp_file.replace('-merged.log','')
num_panio = int(os.environ["num_panio"])

# Create and open all output files

high_all = open('%s-high-all' % dp_out, 'a')
print(dp_name + "\nHigh CPU and High Resource Utilization", end="", file=high_all)
high_cpu = open('%s-high-cpu' % dp_out, 'a')
print(dp_name + "\nHigh CPU", end="", file=high_cpu)
high_res = open('%s-high-ru' % dp_out, 'a')
print(dp_name + "\nHigh Resource Utilization", end="", file=high_res)
high_panio_timestamps = open('%s-high-timestamps' % dp_out, 'a')
print(dp_name + "\nHigh Panio Timestamps - RU (sec), CPU (sec), RU (min), CPU (min)\n", end="", file=high_panio_timestamps)
panio_timestamps = open('%s-timestamps' % dp_out, 'a')
print(dp_name + "\n" + str(num_panio) + " Panio Timestamps\n", end="", file=panio_timestamps)
high_counters = open('%s-high-counters' % dp_out, 'a')
print(dp_name + "\nGlobal Counter Rate Changes", end="", file=high_counters)
dp_statistics = open('%s-high-stats' % dp_out, 'a')
print(dp_name + "\nData Plane Statistics", end="", file=dp_statistics)


# Variables and arrays to store data

panio_timestamp = [None] * num_panio
panio_epoch = [None] * num_panio

total_counters = [None] * num_panio

cpu_load_sampling_dict = [dict() for i in range(num_panio)]

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

session_info_dict = [dict() for i in range(num_panio)]
global_counter_dict = [dict() for i in range(num_panio)]
hw_pool_dict = [dict() for i in range(num_panio)]
sw_pool_dict = [dict() for i in range(num_panio)]
group_dict = [dict() for i in range(num_panio)]
func_dict = [dict() for i in range(num_panio)]

# Variables to keep track of panio section

get_cpu_load_sampling = 0
get_cpu_load_15_sec = 0
get_res_ut_15_sec = 0
get_cpu_load_15_min = 0
get_res_ut_15_min = 0
get_session_info = 0
get_global_counters = 0
get_hardware_pools = 0
get_software_pools = 0
get_groups = 0
get_funcs = 0

# counter increments by one for each Panio section
# line_num increments by one only if a match is found within a particular Panio section

counter = -1
line_num = 0
end_of_script = False

# Keep track of high CPU, descriptors, and buffers

num_high_cpu = [0,0]
num_high_res = [0,0]

# Variables to keep track of labels and print events

panio_time_print = True
high_event_print = True
time_res_unique = True
time_cpu_unique = True
print_cpu_label = True
event_time_print = True
cpu_print = True
core_label = ""
avg_max = ""

# Function to convert panio timestamp to epoch time

def epoch_time( panio_time ):
    utc_time = time.strptime(panio_time, "%Y-%m-%d %H:%M:%S.%f")
    ep_time = timegm(utc_time)
    return ep_time

# Function to convert epoch time to standard time

def standard_time( epoch_time ):
    std_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(epoch_time))
    return std_time

# Function to process resource utilization

def proc_res_ut( time_sec ):

    global line_num, res_label, panio_time_print, time_res_unique, high_event_print, num_high_res
    global res_ut_15_sec, res_ut_15_min 

    match_res_label = re.match(":(s|p).*", line)
    if match_res_label:
        res_label = match_res_label.group(0)

    match_res_ut = re.match(": .*?(\d+).*", line)
    if match_res_ut:
        if time_sec:
            res_ut_15_sec[counter][line_num] = match_res_ut.group(0)
            match_high_res = re.findall("[8-9][0-9]|100", res_ut_15_sec[counter][line_num]) 
        else:
            res_ut_15_min[counter][line_num] = match_res_ut.group(0)
            match_high_res = re.findall("[8-9][0-9]|100", res_ut_15_min[counter][line_num])
        if match_high_res:

            # Keep track of matches
            
            if time_sec:
                num_high_res[0] += len(match_high_res)
            else:
                num_high_res[1] += len(match_high_res)

            # Print panio timestamps

            if panio_time_print:
                print("\n\n" + panio_timestamp[counter], end="", file=high_all)
                print("\n" + panio_timestamp[counter], end="", file=high_panio_timestamps)
                panio_time_print = False

            if time_res_unique:
                print("\n\n" + panio_timestamp[counter], end="", file=high_res)
                time_res_unique= False

            if high_event_print:

            # Print high resource utilization if this is the first instance

                if time_sec:
                    print("\n\n\tHigh Resource Utilization Last 15 Seconds:", end="", file=high_all)
                    print("\n\n\tHigh Resource Utilization Last 15 Seconds:", end="", file=high_res)
                else:
                    print("\n\n\tHigh Resource Utilization Last 15 Minutes:", end="", file=high_all)
                    print("\n\n\tHigh Resource Utilization Last 15 Minutes:", end="", file=high_res)
                high_event_print = False

        # Print the label and the line with high resource utilization

            print("\n\n\t\t" + res_label + "\n", end="", file=high_all)
            print("\n\n\t\t" + res_label + "\n", end="", file=high_res)
            if time_sec:
                print("\t\t" + res_ut_15_sec[counter][line_num], end="", file=high_all)
                print("\t\t" + res_ut_15_sec[counter][line_num], end="", file=high_res)
            else:
                print("\t\t" + res_ut_15_min[counter][line_num], end="", file=high_all)
                print("\t\t" + res_ut_15_min[counter][line_num], end="", file=high_res)

        line_num += 1

# Function to process CPU load

def proc_cpu_load( time_sec ):

    # Global variables to keep track of line numbers and labels
    
    global line_num, core_label, avg_max, panio_time_print, time_cpu_unique, high_event_print, event_time_print, num_high_cpu_sec, num_high_cpu_min, print_cpu_label
    global cpu_load_15_sec, cpu_load_15_min

    if line_num % 15 == 0:
        print_cpu_label = True

    # Get the core label for the high CPU output

    match_core_label = re.match (":core.*", line)
    if match_core_label:
        core_label = match_core_label.group(0)
		
    match_avg_max = re.match (":.*avg max.*", line)
    if match_avg_max:
        avg_max = match_avg_max.group(0)

    # Get the CPU load per line

    match_cpu_load = re.match (": +(\d+).*", line)
    if match_cpu_load:
        if (time_sec):

            # Check if CPU load is higher than a certain number (15 seconds)

            cpu_load_15_sec[counter][line_num] = match_cpu_load.group(0)
            match_high_cpu = re.findall("[8-9][0-9]|100", cpu_load_15_sec[counter][line_num])
        else:

            # Check if CPU load is higher than a certain number (15 minutes)

            cpu_load_15_min[counter][line_num] = match_cpu_load.group(0)
            match_high_cpu = re.findall("[8-9][0-9]|100", cpu_load_15_min[counter][line_num])
        if match_high_cpu:

            # Keep track of matches

            if time_sec:
                num_high_cpu[0] += len(match_high_cpu)
            else:
                num_high_cpu[1] += len(match_high_cpu)

            # Print panio timestamps

            if panio_time_print:
                print("\n\n" + panio_timestamp[counter], end="", file=high_all)
                print("\n" + panio_timestamp[counter], end="", file=high_panio_timestamps)
                panio_time_print = False

            if time_cpu_unique:
                print("\n\n" + panio_timestamp[counter], end="", file=high_cpu)
                time_cpu_unique = False

            if high_event_print:

                # Print high CPU label if this is the first instance

                if time_sec:
                    print("\n\n\tHigh CPU Last 15 Seconds:", end="", file=high_all)
                    print("\n\n\tHigh CPU Last 15 Seconds:", end="", file=high_cpu)
                else:
                    print("\n\n\tHigh CPU Last 15 Minutes:", end="", file=high_all)
                    print("\n\n\tHigh CPU Last 15 Minutes:", end="", file=high_cpu)
                high_event_print = False
            
            # Determine high CPU time offset from panio time based on line number

            if time_sec:
                time_diff = line_num % 15
            else:
                time_diff = (line_num % 15) * 60
            event_time = epoch_time(panio_timestamp[counter]) - time_diff

            # Print the core label and the line with high CPU

            if time_sec:
                if ((line_num < 15 or 15 <= line_num < 30) and print_cpu_label):
                    print("\n\n\t\t\t\t" + core_label, end="", file=high_all)
                    print("\n\n\t\t\t\t" + core_label, end="", file=high_cpu)
                    print_cpu_label = False
                print("\n\t     " + standard_time(event_time) + cpu_load_15_sec[counter][line_num], end="", file=high_all)
                print("\n\t     " + standard_time(event_time) + cpu_load_15_sec[counter][line_num], end="", file=high_cpu)
            else:
                if ((line_num < 15 or 15 <= line_num < 30 or 30 <= line_num < 45 or 45 <= line_num < 60) and print_cpu_label):
                    print("\n\n\t\t\t\t" + core_label + "\n\t\t\t\t" + avg_max, end="", file=high_all)
                    print("\n\n\t\t\t\t" + core_label + "\n\t\t\t\t" + avg_max, end="", file=high_cpu)
                    print_cpu_label = False
                print("\n\t     " + standard_time(event_time) + cpu_load_15_min[counter][line_num], end="", file=high_all) 
                print("\n\t     " + standard_time(event_time) + cpu_load_15_min[counter][line_num], end="", file=high_cpu) 
        line_num += 1

def output_high_timestamps():

    global num_high_res, num_high_cpu
    
    print(" - " + str(num_high_res[0]), end=", ", file=high_panio_timestamps)
    print(str(num_high_cpu[0]), end=", ", file=high_panio_timestamps)
    print(str(num_high_res[1]), end=", ", file=high_panio_timestamps)
    print(str(num_high_cpu[1]), end="", file=high_panio_timestamps)

def output_global_counters():
    
    key_match = 0
    count_diff = 0
    rate_over_50 = {}
    rate_over_25 = {}
    rate_over_10 = {}
    rate_over_0 = {}
    prev_rate_0 = {}
    new_counter = {}

    print("\n\n" + panio_timestamp[counter], end="", file=high_counters)

    for key in global_counter_dict[counter]:
        for key2 in global_counter_dict[counter-1]:
            if key == key2:
                key_match = 1
                count1 = global_counter_dict[counter][key]
                count2 = global_counter_dict[counter-1][key2]
                count_diff = int(count1) - int(count2)
                
                if (count_diff != 0 and int(count2) != 0):
                    diff_percent = abs(count_diff) / int(count2)
                    if (diff_percent >= 0.5):
                        rate_over_50[key] = str(count_diff)
                    elif (diff_percent >= .25):
                        rate_over_25[key] = str(count_diff)
                    elif (diff_percent >= .1):
                        rate_over_10[key] = str(count_diff)
                    elif (diff_percent < .1):
                        rate_over_0[key] = str(count_diff)

                if (count_diff > 0 and int(count2) == 0):
                    prev_rate_0[key] = str(count_diff)

        if key_match == 0:
            new_counter[key] = global_counter_dict[counter][key]

    print("\n\n\tCounters with Previous Rate = 0\n", end="", file=high_counters)
    for key in prev_rate_0:
        print("\n\t\t" + key + ": " + prev_rate_0[key], end="", file=high_counters)

    print("\n\n\tCounters with Rate Change >= 50%\n", end="", file=high_counters)
    for key in rate_over_50:
        print("\n\t\t" + key + ": " + rate_over_50[key], end="", file=high_counters)

    print("\n\n\tCounters with Rate Change >= 25%\n", end="", file=high_counters)
    for key in rate_over_25:
        print("\n\t\t" + key + ": " + rate_over_25[key], end="", file=high_counters)

    print("\n\n\tCounters with Rate Change >= 10%\n", end="", file=high_counters)
    for key in rate_over_10:
        print("\n\t\t" + key + ": " + rate_over_10[key], end="", file=high_counters)

    print("\n\n\tCounters with Rate Change < 10%\n", end="", file=high_counters)
    for key in rate_over_0:
        print("\n\t\t" + key + ": " + rate_over_0[key], end="", file=high_counters)

    if new_counter:

        print("\n\n\tNew Counters", end="", file=high_counters)
        for key in new_counter:
            print("\n\t\t" + key + ": " + new_counter[key], end="", file=high_counters)

def output_dp_stats():

    print_label = True

    print("\n\n" + panio_timestamp[counter], end="", file=dp_statistics)

    for key in cpu_load_sampling_dict[counter]:
        for key2 in cpu_load_sampling_dict[counter-1]:
            if key == key2:
                value1 = cpu_load_sampling_dict[counter][key]                   
                value2 = cpu_load_sampling_dict[counter-1][key2]
                diff = int(value1) - int(value2)
                if diff > 0:
                    if print_label == True:
                        print("\n\n\tIncrease in CPU Load Sampling Group", end="", file=dp_statistics)
                        print_label = False
                    print("\n\t\t" + key + ": +" + str(diff) + "%", end="", file=dp_statistics)

    print_label = True

    for key in session_info_dict[counter]:
        for key2 in session_info_dict[counter-1]:
            if key == key2:
                value1 = session_info_dict[counter][key]
                value2 = session_info_dict[counter-1][key2]
                diff = int(value1) - int(value2)
                if diff > 0:
                    if print_label == True:
                        print("\n\n\tIncrease in Session Stats", end="", file=dp_statistics)
                        print_label = False
                    print("\n\t\t" + key + ": +" + str(diff), end="", file=dp_statistics)
    
    print_label = True

    for key in hw_pool_dict[counter]:
        for key2 in hw_pool_dict[counter-1]:
            if key == key2:
                value1 = hw_pool_dict[counter][key]
                value2 = hw_pool_dict[counter-1][key2]
                diff = int(value1) - int(value2)
                if diff < 0:
                    if print_label == True:
                        print("\n\n\tDecrease in Hardware Pools", end="", file=dp_statistics)
                        print_label = False
                    print("\n\t\t" + key + ": " + str(diff), end="", file=dp_statistics)
    
    print_label = True

    for key in sw_pool_dict[counter]:
        for key2 in sw_pool_dict[counter-1]:
            if key == key2:
                value1 = sw_pool_dict[counter][key]
                value2 = sw_pool_dict[counter-1][key2]
                diff = int(value1) - int(value2)
                if diff < 0:
                    if print_label == True:
                        print("\n\n\tIncrease in Group Average Process Time", end="", file=dp_statistics)
                        print_label = False
                    print("\n\t\t" + key + ": " + str(diff), end="", file=dp_statistics)

    print_label = True

    for key in group_dict[counter]:
        for key2 in group_dict[counter-1]:
            if key == key2:
                value1 = group_dict[counter][key]
                value2 = group_dict[counter-1][key2]
                diff = int(value1) - int(value2)
                if diff > 0:
                    if print_label == True:
                        print("\n\n\tIncrease in Group Average Process Time", end="", file=dp_statistics)
                        print_label = False
                    print("\n\t\t" + key + ": +" + str(diff), end="", file=dp_statistics)
    
    print_label = True

    for key in func_dict[counter]:
        for key2 in func_dict[counter-1]:
            if key == key2:
                value1 = func_dict[counter][key]
                value2 = func_dict[counter-1][key2]
                diff = int(value1) - int(value2)
                if (diff > 0 and key != "urlcache_lru_count"):
                    if print_label == True:
                        print("\n\n\tIncrease in Func Average Process Time", end="", file=dp_statistics)
                        print_label = False
                    print("\n\t\t" + key + ": +" + str(diff), end="", file=dp_statistics)
                elif (diff > 0 and key == "urlcache_lru_count"):
                    print ("\n\n\tIncrease in LRU Count: +" + str(diff), end="", file=dp_statistics)

# The fun begins. Start parsing the DP monitor merged files

with open(dp_file, 'rt') as f:
    for line in f:

        # Get panio timestamp

        match_panio_timestamp = re.match("(.*)? (\+|-).* --- panio", line)
        if match_panio_timestamp:

            # Increment counter and make panio_time_print true
            # When high CPU/buffers/descriptors are found, Panio time should only be printed once, even when there are multiple instances within the same Panio time

            counter += 1
            panio_time_print = True
            time_res_unique = True
            time_cpu_unique = True
            end_of_script = False
            num_high_cpu = [0,0]
            num_high_res = [0,0]

            # Convert Panio time to epoch time
            # Makes it easy to compute time differences on CPU load by line

            panio_timestamp[counter] = match_panio_timestamp.group(1)
            panio_epoch[counter] = epoch_time(panio_timestamp[counter])
            print("\n" + panio_timestamp[counter], end="", file=panio_timestamps)
        
        # Check for line ":CPU load sampling by group:"

        match_cpu_load_sampling_string = re.match(":CPU load sampling by group", line)
        if match_cpu_load_sampling_string:

            # Turn on CPU load sampling flag

            get_cpu_load_sampling = 1

        if (get_cpu_load_sampling == 1):
            match_cpu_load_group = re.match(":([a-z_]+).*(\d+)", line)
            if match_cpu_load_group:
                group_name = match_cpu_load_group.group(1)
                group_value = match_cpu_load_group.group(2)
                cpu_load_sampling_dict[counter][group_name] = group_value
                        
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

        # Check for line ":Number of sessions supported:"

        match_supported_sessions = re.match(":Number of sessions supported", line)
        if match_supported_sessions:
            get_res_ut_15_min = 0
            get_session_info = 1
            line_num = 0

        # Get session information

        if (get_session_info == 1):
            match_session_info = re.match(":(.*?):.*?(\d+)", line)
            if match_session_info:
                session_name = match_session_info.group(1)
                session_value = match_session_info.group(2)
                session_info_dict[counter][session_name] = session_value

        match_session_timeout = re.match(":Session timeout", line)
        if match_session_timeout:
            get_session_info = 0
            line_num = 0

        # Check for line ":Max pending queued mcast packets"
        # There are two global counter outputs per panio. This only gets the first.

        match_global_counters = re.match(":Max pending queued mcast packets", line)
        if match_global_counters:
            get_global_counters = 1

        # Get global counters and place them in an array of dictionaries

        if (get_global_counters == 1):
            match_counter = re.match(":([a-z_]+).*?\d+.*?(\d+)", line)
            if match_counter:
                counter_name = match_counter.group(1)
                counter_rate = match_counter.group(2)
                global_counter_dict[counter][counter_name] = counter_rate

            match_total_counters = re.match(":Total counters shown: (\d+)", line)
            if match_total_counters:
                total_counters[counter] = match_total_counters.group(1)
                get_global_counters = 0
        
        match_hardware_pools = re.match("Hardware Pools", line)
        if match_hardware_pools:
            get_hardware_pools = 1

        if (get_hardware_pools == 1):
            match_pool = re.match(":(\[.*)?:.*?(\d+)\/", line)
            if match_pool:
                pool_name = match_pool.group(1)
                pool_value = match_pool.group(2)
                hw_pool_dict[counter][pool_name] = pool_value

        match_software_pools = re.match("Software Pools", line)
        if match_software_pools:
            get_hardware_pools = 0
            get_software_pools = 1

        if (get_software_pools == 1):
            match_pool = re.match(":(\[.*)?\(.*:.*?(\d+)", line)
            if match_pool:
                pool_name = match_pool.group(1)
                pool_value = match_pool.group(2)
                sw_pool_dict[counter][pool_name] = pool_value

        match_groups = re.match(":group.*max. proc us", line)
        if match_groups:
            get_software_pools = 0
            get_groups = 1

        if (get_groups == 1):
            match_group = re.match(":([a-z_]+).*?\d+.*?(\d+)", line)
            if match_group:
                group_name = match_group.group(1)
                group_avg_time = match_group.group(2)
                group_dict[counter][group_name] = group_avg_time

        match_funcs = re.match(":func.*max. proc us", line)
        if match_funcs:
            get_groups = 0
            get_funcs = 1

        if (get_funcs == 1):
            match_func = re.match(":([a-z_]+).*?\d+.*?(\d+)", line)
            if match_func:
                func_name = match_func.group(1)
                func_avg_time = match_func.group(2)
                func_dict[counter][func_name] = func_avg_time

            match_lru_count = re.match(":urlcache_lru.*?\d+.*?\d+.*?(\d+)", line)
            if match_lru_count:
                lru_count_value = match_lru_count.group(1)
                func_dict[counter]["urlcache_lru_count"] = lru_count_value

        match_range = re.match(":.*range \(ticks\)", line)
        if match_range:
            get_funcs = 0
        
            # Finally, print total high CPU and resource utilization counts to high_panio timestamps
            if end_of_script == False:
                if (num_high_res[0] > 0 or num_high_res[1] > 0 or num_high_cpu[0] > 0 or num_high_cpu[1] > 0):
                    output_high_timestamps()
                    output_global_counters()
                    output_dp_stats()
                    end_of_script = True

# Close all open files
f.close()
high_all.close()
high_cpu.close()
high_res.close()
high_panio_timestamps.close()
panio_timestamps.close()
high_counters.close()
dp_statistics.close()

#!/bin/bash
#dpend

[ $# -ge 1 -a -f "$1" ] && ts_file="$1" || input="-"
valid_ts_file=$(file $ts_file | grep 'gzip compressed data')

if [ -z "$ts_file" ]; then
	echo "Error: No tech support file specified."
elif [ ! "$valid_ts_file" ]; then
	echo "Error: $ts_file is not a valid tech support file."
else
	dp_files='*dp-monitor.log*'
	dir="dpend_"`echo $ts_file | rev | cut -c 5- | rev`
	if [ ! -d "$dir" ]; then
		mkdir $dir
	fi
	cd $dir

	echo "Extracting DP Monitor logs from $ts_file"

	tar zxvf ../$ts_file --wildcards $dp_files

	dp_files=($(find . -iname *dp-monitor* | cat | sort -r))

	echo "[DONE]"
	echo -n "Merging DP Monitor logs..."

	for file in "${dp_files[@]}"; do

		pa7000=$(echo $file | grep -o -P 's.*dp')
		pa5000=$(echo $file | grep -o -P 'var\.dp')

		if [ $pa7000 ]; then 
			cat $file >> $(echo $file | grep -o -P '(?<=var/).*(?=/log/)' | tr / -)"-merged.log"
		elif [ $pa5000 ]; then
			cat $file >> $(echo $file | grep -o -P '(?<=var\.).*(?=/log)')"-merged.log"
		else
			cat $file >> dp-merged.log
		fi
		echo -n "."
	done

	echo " [DONE]"
	echo -n "Processing DP Monitor logs..."

	dpend_files=($(ls *merged.log | cat | sort))
	dp_list=""

	for dp_file in "${dpend_files[@]}"; do
		trim_file=$(echo $dp_file | grep -o -P '.*(?=-merged)')
		echo -n "$trim_file..."
		dp_list+="$trim_file, "
		num_panio=$(grep "\--- panio" $dp_file | wc -l)
		export num_panio
		export dp_file
		python3 /home/nanderson/dpend.py
	done

	echo " [DONE]"
fi

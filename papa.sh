#!/bin/bash
#PAPA - Palo Alto Performance Analyzer

[ $# -ge 1 -a -f "$1" ] && ts_file="$1" || input="-"

dp_files='*dp-monitor.log*'
dir="papa_"`echo $ts_file | rev | cut -c 5- | rev`
mkdir $dir
cd $dir

echo "Extracting DP Monitor logs from $ts_file"

tar zxvf ../$ts_file --wildcards $dp_files

dp_files=($(find . -iname *dp-monitor* | cat | sort -r))

echo " [DONE]"
echo -n "Merging DP Monitor logs..."

for file in "${dp_files[@]}"; do
	cat $file >> $(echo $file | grep -o -P '(?<=var/).*(?=/log/)' | tr / -)"-merged.log"
		echo -n "."
done

echo " [DONE]"
echo -n "Processing DP Monitor logs..."

papa_files=($(ls *merged.log | cat | sort))

for dp_file in "${papa_files[@]}"; do
		trim_file=$(echo $dp_file | grep -o -P '.*(?=-merged)')
		echo -n "$trim_file..."
		num_panio=$(grep '/--- panio' $dp_file | wc -l)
		export num_panio
		echo $num_panio
		export dp_file
		echo $dp_file
		echo "Test"
		python ../papa.py > $(echo $dp_file | grep -o -P '.*(?=-merged)' | tr / -)"-highCPU.papa"
done

echo " [DONE]"

#!/bin/bash
#change test and training sets


echo "Do you want to use extension '$1'[y/n]"?
read user_input
if [ "$user_input" = "y" ]; then
	for BASE in "testing" "training" "ResultsTestSet" "species_id"
	do
                echo $BASE$1".csv --> $BASE.csv"
		cp $BASE$1".csv" $BASE".csv"
	done
fi

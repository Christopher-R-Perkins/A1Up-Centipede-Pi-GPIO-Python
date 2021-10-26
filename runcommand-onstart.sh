#!/bin/bash
NAME=$(basename $3 .zip)
echo "$1"
if [ "$1" = "arcade" ]
then 
	if [ "$NAME" = "quantum" ] || [ "$NAME" = "ccastles" ] || [ "$NAME" = "centiped" ] || [ "$NAME" = "gt2k" ] || [ "$NAME" = "lemmings"] || [ "$NAME" = "marble" ] || [ "$NAME" = "milliped" ] || [ "$NAME" = "missile" ] || [ "$NAME" = "rampart" ] || [ "$NAME" = "shufshot" ] || [ "$NAME" = "shuuz"] || [ "$NAME" = "sonic" ] || [ "$NAME" = "syvalion" ] || [ "$NAME" = "wcbowl" ]
	then
		echo "1" | nc localhost 5269
	else
		echo "0" | nc localhost 5269
	fi
elif [ "$1" = "scummvm" ]
then
	echo "2" | nc localhost 5269
fi
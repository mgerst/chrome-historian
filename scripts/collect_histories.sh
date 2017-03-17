#!/bin/bash
userlist=$(getent passwd | cut -d: -f1,6)
DEST=$HOME/histories
DEBUG=false

mkdir -p $DEST

if [[ "$1" == "-d" || "$1" == "--debug" ]]; then
    DEBUG=true
    echo "D: Debug mode on"
fi

echo "Dumping chrome-historian compatible histories to $DEST"

for entry in $userlist; do
	user=$(echo $entry | cut -d: -f1)
	homedir=$(echo $entry | cut -d: -f2)

    $DEBUG && echo "D: Found user $user with home $homedir"

	histfile=$homedir/.config/google-chrome/Default/History
	if [[ -f $histfile ]]; then
		echo "Found history for $user at $histfile"

        if $DEBUG; then
            cp -v $histfile $DEST/$user
        else
            cp $histfile $DEST/$user
        fi
    fi
done
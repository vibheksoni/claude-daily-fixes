#!/bin/bash

##
## Use this when claude code says its outdated and when you do claude update it says another instance is updating even
## though there is no other instance updating.
##

echo "Cleaning up old Claude locks..."
rm -f ~/.claude/.update.lock
rm -rf ~/.claude/.update.tmp*

echo "Running Claude update..."
claude update

echo "Verifying installed Claude versions..."
CLAUDE_BIN_PATHS=$(which -a claude)
for path in $CLAUDE_BIN_PATHS; do
    version_output=$($path --version 2>/dev/null)
    echo "  $path => $version_output"
done

main_path=$(which claude)
main_version=$($main_path --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')

if [ -x /usr/local/bin/claude ]; then
    local_version=$(/usr/local/bin/claude --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
    if [ "$local_version" != "$main_version" ]; then
        echo "Removing outdated /usr/local/bin/claude (version $local_version)..."
        sudo rm /usr/local/bin/claude
    fi
fi

echo "Refreshing shell command cache..."
hash -r

echo "Update complete. Claude version now:"
which claude
claude --version

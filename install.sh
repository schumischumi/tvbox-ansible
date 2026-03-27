#!/bin/bash

# Script: install.sh
# Usage: ./install.sh <git|curl|wget>

if [ $# -eq 0 ]; then
    echo "INFO: No argument provided."
    echo "INFO: Using git as default. <git|curl|wget>"
    TOOL="git"
else
    TOOL=$1
fi

http_url="https://github.com/schumischumi/tvbox-ansible/archive/refs/heads/main.zip"
git_url="https://github.com/schumischumi/tvbox-ansible.git"
default_tools="ansible"

cd /tmp
sudo apt-get update
case "$TOOL" in
    git)
        output_folder="tvbox-ansible"
        packages="$default_tools git"
        echo "=== Installing system packages ==="
        echo "Packages: $packages"
        sudo apt-get install -y $packages
        echo "=== Deleting output folder $output_folder ==="
        rm -rf $output_folder
        echo "=== Git checkout ==="
        echo "Remote repositories: $git_url"
        git clone $git_url
        cd $$output_folder
        ;;

    curl)
        output_folder="tvbox-ansible-main"
        packages="$default_tools curl"
        echo "=== Installing system packages ==="
        echo "Packages: $packages"
        sudo apt-get install -y $packages
        echo "=== Deleting output folder $output_folder ==="
        rm -rf $output_folder
        echo "=== Download with curl & unzip ==="
        echo "Url: $http_url"
        curl -L $http_url -o repo.zip
        unzip repo.zip
        cd $output_folder
        ;;

    wget)
        output_folder="tvbox-ansible-main"
        packages="$default_tools wget"
        echo "=== Installing system packages ==="
        echo "Packages: $packages"
        sudo apt-get install -y $packages
        echo "=== Deleting output folder $output_folder ==="
        rm -rf $output_folder
        echo "=== Download with wget & unzip ==="
        echo "Url: $http_url"
        wget -L $http_url -O repo.zip
        unzip repo.zip
        cd $output_folder
        ;;

    *)
        echo "Error: Invalid argument '$TOOL'"
        echo "Valid options are: git, curl, or wget"
        echo "Usage: $0 <git|curl|wget>"
        exit 1
        ;;
esac

sudo ansible-playbook playbook.yml

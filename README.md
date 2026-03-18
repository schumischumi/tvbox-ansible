# TVBox-Ansible

This repo is for setting up an alternative to an android tv box / stick.
The base is kubuntu 26.04 lts which needs to be installed with a user that also has sudo permissions.

## Preparation

- Download and install kubuntu 26.04 lts
- Add a user with sudo permissions
- Install ansible: `sudo apt install ansible`
- Use wget / curl / git to download this repo:

``` bash
# Example for wget (recommended for one time usage)
wget https://github.com/schumischumi/tvbox-ansible/archive/refs/heads/main.zip -O repo.zip
unzip repo.zip
cd tvbox-ansible-main

# Example for curl
curl -L https://github.com/schumischumi/tvbox-ansible/archive/refs/heads/main.zip -o repo.zip
unzip repo.zip
cd tvbox-ansible-main

# Example for git (git needs to be installed manually)
git clone https://github.com/schumischumi/tvbox-ansible.git
unzip repo.zip
cd tvbox-ansible
```

## Usage

Run

``` bash
sudo ansible-playbook playbook.yml

> Enter username for auto login and general config
Provide the (current) username that should be used for the current setup. Rhe setup will try to provide the current user as default value.
```


## Manual Steps

These steps will never be automated by Ansible, because they are quite hw specific:
- hardware acceleration for nvidia (no hw to test)
- auto wifi config ( can be done while installing / running kubuntu)
- auto login (should be done while installing kubuntu)
- cec config (no hw to test). I would suggest using a HID remote like the Rii mini i25 (supports wake up from hibernation) if CEC is not available
- login to jellyfin
- vacuum login
- retroarch config
- steam login

## Status

### Working Features

- Installing base packages
- Installing the flatpaks vacuum, retro Arch, Steam Link, VLC and jellyfin-media-player
- Installing TVLauncher v 1.0.0 (https://github.com/Darkvinx88/TvLauncher)
- Automatically starting TVLauncher
- Detect GPU for hardware acceleration ENV (iHD / i965 / radeonsi)
- overwrite timeout config so no auth is necessary after sleep
- ...

### Planned Features

- update button for easy system update


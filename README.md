# TVBox-Ansible

This repo is for setting up an alternative to an android tv box.
The base is fedora sway spin which needs to be installed with a user that also has sudo permissions.

## Preparation

- Download and install fedora sway spin
- Add a user with sudo permissions
- Install ansible: `sudo dnf install ansible`
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

# Example for git (git needs to be installed)
git clone https://github.com/schumischumi/tvbox-ansible.git
unzip repo.zip
cd tvbox-ansible
```

## Usage

Run

``` bash
sudo ansible-playbook playbook.yml

> Which is the user executing sway
Provide the (current) username that should be used for the current setup
```


## Manual Steps

These steps will never be automated by Ansible, because they are quite hw specific:
- hardware acceleration for nvidia (no hw to test)
- auto wifi config
- cec config (no hw to test). I would suggest using a HID remote like the Rii mini i25 (supports wake up from hibernation) if CEC is not available
- login to jellyfin
- vacuum login
- retroarch config
- steam login

## Status

### Working Features

- Installing base packages
- Adding rpm fusion free & non-free repos
- Installing DVD Autoplay if wished for
- Installing the flatpaks vacuum, retro Arch, steam and jellyfin-media-player
- Automatically starting vacuum (workspace 1), retro Arch (workspace 3), SteamLink (workspace 4) and jellyfin-media-player (workspace 2)
- Provide an update button (workspace 5) for system and flatpak updates 
- Detect GPU for hardware acceleration ENV (iHD / i965 / radeonsi)
- auto login
- overwrite timeout config so no auth is necessary after sleep
- increase font size for foot terminal
- ...

### Planned Features

- better user handling in ansible
- ask what should be installed
- dvd udevrules
- better dvd script
- blu-ray support
- better update button structure
- better ansible structure
- gpg check for rpm fusion

## Known Issues
- Sometimes the system demands authentication after waking up

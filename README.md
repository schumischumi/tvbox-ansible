# TVBox-Ansible

This repo is for setting up an alternative to an android tv box.
The base is fedora sway spin which needs to be installed with a user that also has sudo permissions.

## Preparation

- Download and install fedora sway spin.
- Add a user with sudo permissions
- Install ansible with pip(x): `pipx install ansible`
- Use wget / curl / git to download this repo:

``` bash
# Example for wget (recommended)

# Example for curl

# Example for git (needs to be installed)

```

## Usage

Switch to the folder you downloaded the repo and run

``` bash
ansible-playbook playbook.yml
```


## Manual Steps

These steps will never be automated by Ansible, because they are quite hw specific:
- hardware acceleration for nvidia (no hw to test)
- auto wifi config
- cec config (no hw to test). I would suggest using a HID remote like the Rii mini i25 (supports wake up from hibernation) if CEC is not available
- login to jellyfin
- jellyfin fullscreen
- vacuum login
- vacuum fullscreen
- retroarch config


## Status

### Working Features

- Installing base packages
- Adding rpm fusion free & non-free repos
- Installing DVD Autoplay if wished for
- Installing the flatpaks vacuum, retro Arch and jellyfin-media-player
- Automatically starting vacuum (workspace 1), retro Arch (workspace 3) and jellyfin-media-player (workspace 2)
- Auto update the OS anf flatpaks at 8 am
- Detect GPU for hardware acceleration ENV (iHD / i965 / radeonsi)
- auto login
- overwrite timeout config so no auth is necessary after sleep
- ...

### Planned Features

- use current user for everything
- ask what should be installed
- dvd udevrules
- better dvd script
- blu-ray support
- better update button structure
- grant vacuum access to dri

## Known Issues
- Sometimes the system demands authentication after waking up

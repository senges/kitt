# Kitt

Kitt is a container based portable shell environment.

Spawn your shell, with your tools, and your config, anywhere.

## Installation

Install [podman](https://podman.io/getting-started/installation) ([here](https://podman.io/new/2021/06/16/new.html) for ubuntu < 20.10), and python3.

```
➜  apt install podman
➜  pip install --user kitt-shell
```

> Kitt should better run with podman, but still offers Docker compatibility.
> See [Containerization section](#Containerization) for technical details.

## How to use Kitt

Fill a configuration file (see [examples folder](./examples)) either in `toml` or `json` format. 
Feed it to Kitt and let the magic happend !

```
➜  kitt build -f examples/devops.conf devops
➜  kitt run devops
root@kitt:~# 
```

## Configuration
### Basics

```toml
[options]
bind_home_folder = false    # Bind $HOME with docker $HOME (read-write)
bind_ssh_folder = false     # Bind $HOME/.ssh (read-only)
docker_in_docker = false    # Share docker socket
forward_x11 = false         # Configure x11 forward

[workspace]
tools = []          # Catalog tools
hostname = "kitt"   # Container hostname

# [[workspace.envs]]  # Container exported ENV (multiple)
# name = ""
# value = ""

# [[workspace.volumes]]   # Container bind volumes (multiple)
# host = ""   # Local directory
# bind = ""   # Bin inside container
# mode = ""   # Mode (default is 'rw')
```

For more details about **Catalog** tool installer, see [tools installation](#Tools-installation) section.

### Plugins

Kitt offers multiple _optional_ plugins to improve environment customization.

| Plugin     | Description                           |
|------------|---------------------------------------|
| _bash_     | configure bash                        |
| _zsh_      | install and setup Zsh (oh-my-zsh)     |
| _copy_     | copy local files inside container     |
| _download_ | download ressources inside container  |
| _git_      | clone git repository inside container |
| _tmux_     | configure Tmux                        |
| _screen_   | configure GNU Screen                  |
| _sercrets_ | add secrets (not yet implemented)     |

See [PLUGINS.md](./PLUGINS.md) for configuration details.

See [plugins.py](./plugins.py) to implement your own plugin.

## How does it work ?

Kitt will build an [OCI Container Image](https://github.com/opencontainers/image-spec) (compatible with Docker, Podman, ...), 
according to the provided configuration file. It will install requested tools inside, setup your desired shell(s), shortcuts, completion, plugins, and add your configuration files.

At runtime, Kitt will create a container from this image, spawn a shell inside and attach it to your current TTY. 

### Tools installation

For the tool installation part, Kitt relies on [Catalog](https://github.com/senges/catalog). 
It does provide an uniform way of installing tools inside containers, and can be extended if necessary.

Catalog is also available inside the container :

```
➜  kitt run devops
root@kitt:~# catalog htop pulumi

[+] Installing htop
...
```

### Containerization

Kitt is built to work with `Podman` as containerization engine. Podman has great advantages compared to docker: it's 
easy to install, lightweight (`~110MB` vs `~530MB`), and rootless by design.

However, if you insist, you can also use Kitt with docker (see `kitt config --driver`). 
Setup docker rootless mode if you want to preseve `uid` reflection benefits.

**What is rootless and why is it great ?**

> TL;DR: Rootless is great for shared folders file rigths (amongst others advantages).

Rootless means you can run Kitt containers without root privileges. The user inside the container will have
the exact same `uid` as your current host user. It will still be shown as `uid=0(root)`, but that's just a binding for
compatibility reasons. 

So if you bind a directory (your home for example), any file created by the user inside the container will be own by your user 
on the host side instead of root.

Example :

```
alice@host$  id
uid=1000(alice) gid=1000(alice) groups=1000(alice)

alice@host$  docker run -it -v /home/alice:/root ubuntu
➜ id
uid=0(root) gid=0(root) groups=0(root)
➜ touch /root/myfile.txt  <= This file will be owned by root in host /home/alice/myfile.txt

$ kitt run myimage
➜ id
uid=0(root) gid=0(root) groups=0(root)
➜ touch /root/myfile.txt  <= This file will be owned by alice in host /home/alice/myfile.txt (because kitt runs rootless)
```
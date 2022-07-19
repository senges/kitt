# Kitt

Kitt is a container based portable shell environment.

Spawn your shell, with your tools, and your config, anywhere.

## Installation

Install [Docker](https://docs.docker.com/get-docker) and python3.

```
➜  curl -sSL https://get.docker.io | bash
➜  pip install kitt-shell
```

## How to use Kitt

Fill a configuration file (see [examples folder](./examples)) either in `toml` or `json` format. 
Feed it to Kitt and let the magic happend !

```
➜  kitt build -f examples/devops.conf devops
✓ Build success !

➜  kitt run devops
user@kitt:~# 
```

### Kitt CLI reference

```
➜  kitt --help

Usage: kitt.py [OPTIONS] COMMAND [ARGS]...

Options:
  -h, --help   Show this message and exit.
  -d, --debug  Debug mode

Commands:
  build    Build image from source config file
  list     List local images
  patch    Patch image runtime metadata
  prune    Prune local images
  pull     Pull image and exit
  push     Push image to registry
  refresh  Pull latest version of local images
  remove   Remove local image
  run      Run kitt shell
  version  Show version
```

## Configuration
### Basics

```toml
[options]
docker_in_docker = false    # Share docker socket
forward_x11 = false         # Configure x11 forward

[workspace]
tools = []              # Catalog tools
user = "user"           # Username inside container
hostname = "kitt"       # Container hostname
default_shell = "bash"  # One of bash, zsh, sh, dash

# [[workspace.envs]]  # Container exported ENV (multiple)
# name = ""
# value = ""

# [[workspace.volumes]]   # Container bind volumes (multiple)
# host = ""   # Local directory
# bind = ""   # Bind inside container
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
| _sercrets_ | add secrets                           |

See [PLUGINS.md](./PLUGINS.md) for configuration details.

See [plugins.py](./kitt/plugins.py) to implement your own plugin.

## How does it work ?

Kitt will build an [OCI Container Image](https://github.com/opencontainers/image-spec) (compatible with Docker, Podman, ...), according to the provided configuration file. It will install requested tools inside, setup your desired shell(s), shortcuts, completion, plugins, and add your configuration files.

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

> At first, kitt was meant to run with Podman as it is rootless by design (which solves uig/gid mapping problems).  
> However, for multiple reasons, it should now mainly run with Docker.
> Podman support is in progress, see branch `feat/podman`.

**What is UID/GID reflexion ?**

> TL;DR: It's great for shared folders file rigths.

Kitt uses [fixuid](https://github.com/boxboat/fixuid) project to reflect host user UID/GID inside the container. What does that means ?

As Docker containers run as root (except rootless ones, but still), if you have a shared volume
between your host and container, files created inside the container will be owned by root on the host. This mecanism makes working with volumes for user owned files very unconvenient.

With `fixuid`, the user inside the container will have the exact same real `uid` as your current host user. So if you bind a directory (your `home` for example), any file created by the user inside the container will be own by your user on the host side instead of root.
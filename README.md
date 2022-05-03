# Kitt

Kitt is a container based portable shell environment.

Spawn your shell, with your tools, and your config, anywhere.

## Installation

Install [podman](https://podman.io/getting-started/installation) ([here](https://podman.io/new/2021/06/16/new.html) for ubuntu < 20.10), and python3.

```
➜  apt install podman
➜  pip install --user -r requirements.txt
```

## How to use Kitt

Fill a configuration file (see [examples folder](./examples)) either in `toml` or `json` format. 
Feed it to Kitt and let the magic happend !

```
➜  kitt build -f examples/devops.conf devops
➜  kitt run devops
root@kitt:~# 
```

## Features

* configuration utils (bind `$HOME`, bind `.ssh` read-only, dind..)
* forward x11 for GUI apps
* custom volumes and envs (buildtime, runtime)
* extensible tool installer (see [Catalog](https://github.com/senges/catalog))
* easy to add plugins (see [plugins.py](./plugins.py))
* host `uid` mapping inside container
* support both Podman and Docker

## How does it work ?

Kitt will build an [OCI Container Image](https://github.com/opencontainers/image-spec) (compatible with Docker, Podman, ...), 
according to the provided configuration file. It will install requested tools inside, setup your desired shell, shortcuts, completion, plugins, and add your configuration files.

At runtime, Kitt will create a container from this image, spawn a shell inside and attach it to your current TTY. 

### Tools installation

For the tool installation part, Kitt relies on [Catalog](https://github.com/senges/catalog). 
It does provides an uniform way of installing tools inside containers, and can be extended if necessary.

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

```bash
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
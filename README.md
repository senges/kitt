# Kitt

Kitt is a container based portable shell environment manager.

Bring in seconds your own shell ecosystem (dotfiles, tools, ricing) to any container capable computer.

> [!NOTE]
> Previous Kitt implementation was archived in [senges/kitt.py](https://github.com/senges/kitt) repository.

## TL;DR

Kitt is just sugar around OCI.

Any standard image can be converted into a kitt shell image.
Environment setup and user mapping is managed under the hood.

Running a kitt shell image yield its own associated runtime flags.

```shell
$ podman run my-shell
run --rm -it [...] --entrypoint=/bin/bash my-shell

$ podman $(podman run my-shell)
[new shell]
```

This trick makes it super convenient and portable.
To avoid running arbitraty scripts on the host, command must always be leaded by an explicit `podman` call. Way more safe.
<!-- STILL VERY DANGEROUS -->

```
# Bad bad bad
$ podman run my-shell | bash
$ eval podman run my-shell
```

## Usage

Kitt is built to run natively with your container manager, no dependency, batteries included.

```shell
# Build you kitt shell image 
$ podman $(podman run kitt.sh/kitt.sh [source] [name])

# Run your kitt shell image, from anywhere in the world
$ podman $(podman run [name])
```

A convenience bash wrapper CLI is also availabe.

```shell
$ wget kitt.sh
$ ./kitt.sh -h
```

## Example

**Step 1. build any base image**

```dockerfile
FROM debian:trixie

RUN apt-get update \
    && apt-get install -y ansible terraform kubectl
```

```shell
$ podman build -t my-devops .
```

**Step 2. build kitt image**

```shell
$ podman $(podman run kitt.sh/kitt.sh my-devops my-shell)
```

**Step 3. run your shell anywhere**

```shell
$ podman $(podman run my-shell)

[user@kitt]$ kubectl version
Client Version: v1.32.3
```

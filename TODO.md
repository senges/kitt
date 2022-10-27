# TODO
## Fixs

- [x] Path is not properly exported for root, cannot find catalog bin folder
- [x] Docker group GID do not match host group GID
- [x] X11 forwarding mostly works, but xeyes is super laggy
- [ ] Bug with duplicate `/home`
```
» id
uid=1000(user) gid=1000(user) groups=1000(user)

» tree -L 2 /home
/home
├── basique
└── charles
    └── host
```

- [ ] pip version check make it unusable (temp fix is : `--disable-pip-version-check`) ([NixOS open issue](https://github.com/NixOS/nixpkgs/issues/198059))
```
FileNotFoundError: [Errno 2] No such file or directory: '/nix/store/...-python3-3.10.7/bin/pip'
Call stack:
    [...]
Message: '[present-rich] %s'
Arguments: (UpgradePrompt(old='22.2.2', new='22.3'),)    
```

## Short term

- [x] Add static files onboarding
- [x] Add dind managment with new user
- [x] Add push strategy
- [x] Add secret managment
- [x] Handle local user not in docker group (run as other user ?)
- [x] Make sure local catalog image is updated
- [ ] Execute `which` for each tool to make sure it's not OS embeded (ex: curl for most distros)
- [ ] Add layer caching for prebuild
- [ ] Better logging
- [x] Should we properly handle runtimes ? (go, python, ..) => Probably not as exploiting Nix dependencies ?
- [ ] Shoud share PID with host ? (--pid=host)
- [ ] Only remap UID/GID when volumes (?)
- [x] Make plugins J2 generated
- [ ] Add bash / zsh completion
- [ ] Proper host home mapping of folders / dotfiles
- [ ] Add custom part for Dockerfile
- [ ] package location instead of __file__ : http://peak.telecommunity.com/DevCenter/PythonEggs#accessing-package-resources
- [ ] Refresh only one image
- [ ] Waiter on prune
- [ ] Manually pull nixos and alpine images, add waiter and done status on that step
- [ ] Auto handle plugins requirements
- [ ] sudo might be : su - root -c '...'
- [ ] When pulling image, untag pulled image to keep `kitt remove` working
- [ ] download plugins : create target folder if not exist
- [ ] add pipenv so it works with host vscode

## Mid-Long term

- [x] Kitt inside kitt ? (=> added to catalog)
- [ ] Attach other TTY to running kitt container
- [ ] CLI completion
- [x] Catalog custom input file not supported yet => fixed by Nix
- [ ] Display building logs (see Image.build second argument as JSON stream)
- [ ] Add sound (see [docker-pulseaudio-example](https://github.com/TheBiggerGuy/docker-pulseaudio-example))
- [ ] Lint tools list to see if they exist on NisOS Search DB
- [ ] Cache any Nix layer as Nixery does
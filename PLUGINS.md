# Plugins

Plugins should be declared in `[plugins]` top level section of your
configuration file.

If you see `(multiple)` marker, it means plugin expect a [toml nested array of table](https://toml.io/en/v1.0.0#array-of-tables) (could be 0 elements). JSON equivalents would be :

<details>

```toml

[plugins.foo]
x = 42
[[plugins.foo.bar]] # Is (multiple)
a = true
b = false

[[plugins.foo.bar]] # Is (multiple)
a = false
b = true
```

```json
"plugins": {
    "foo": {
        "x": 42,
        "bar": [
            {
                "a": true,
                "b": false
            },
            {
                "a": false,
                "b": true
            }
        ]
    }
}
```

Could be empty set :

```toml
[plugins.foo]
x = 42
```

```json
"plugins": {
    "foo": {
        "x": 42
    }
}
```

</details>

## SH

This is the most basic plugin **but also quite an anti-pattern**.

You should only invoke sh plugin for edge cases, when no other plugin is fitting your needs.

```toml
[plugins.sh]
cmd = []
```

<details>

```toml
[plugins.sh]
cmd = [
    "ln -s $(find / -name *.pc | head -n 1) /etc/pkg-build",
    "ssh-keygen -t rsa -b 2048 -f /usr/share/key -N $(echo $PASS | md5sum | cut -d ' ' -f 1)",
]
```

Is the Dockerfile equivalent of :

```dockerfile
RUN ln -s $(find / -name *.pc | head -n 1) /etc/pkg-build
RUN ssh-keygen -t rsa -b 2048 -f /usr/share/key -N $(echo $PASS | md5sum | cut -d ' ' -f 1)
```

</details>

## ZSH

Install and configure Zsh (oh-my-zsh) as you like.

```toml
[plugins.zsh]
theme = "afowler"
plugins = []    # Plugins name or link
extras = []     # Extra line for .zshrc

# Add zsh aliases (multiple)
[[plugins.zsh.aliases]]
name = ""
cmd = ""
```

## COPY 

Copy host local files inside container. 

> **warning** 
> Do not use this plugin to put any sensible file (private keys, tokens, passwords) inside your image,
> especially if you aim tu push it to a container registry.  
> Use `[secrets]` instead.

```toml
[plugins.copy]

[[plugins.copy.files]]   # File / directory entry (multiple)
src = ""                 # Host path
dest = ""                # Container path
```

## DOWNLOAD 

Download ressource from any URL. Underlying code will use `wget` to fetch ressource(s).

```toml
[plugins.download]

[[plugins.download.ressources]]   # Ressource to download (multiple)
url = ""                          # Ressource public URL
target = ""                       # Target container path for download
```

## GIT CLONE 

Clone a git repository inside your conainer.

```toml
[plugins.git]

[[plugins.git.repos]]   # Ressource to download (multiple)
url = ""                # Repository URL
target = ""             # Target clone directory in container
```

## PIP INSTALL

Install pip packages.

```toml
[plugins.pip]
packages = []       # String array of packages
extra_indexes = []  # String array of extra index url
```

## Custom plugins

To add your very own plugin, create a jinja file and add it inside `kitt/static/plugins`.
Then, you can use it directly inside your config file without any code change.

For example, if you wish to implement a `tmux` plugin, create a `tmux.j2` file and set the variables
inside your config file if necessary.

```jinja
RUN echo {{ data }} >> ${HOME}/.tmux.conf
```

```toml
[plugins.tmux]
data = "..."
```

Only the first line is mandatory to include it in the build process.
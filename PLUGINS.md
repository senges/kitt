# Plugins

Plugins should be declared in `[plugins]` top level section of your
configuration file.

If you see `(multiple)` marker, it means plugin expect a [toml nested array of table](https://toml.io/en/v1.0.0#array-of-tables) (could be 0 elements). JSON equivalents would be :

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

## BASH (builtin)

Bash is already installed by default in kitt base image, but you can customize it.

```toml
[plugins.bash]
extras = []     # Extra line for .bashrc

# Add bash alias (multiple)
[[plugins.bash.alias]]
name = ""
cmd = ""
```

## ZSH

Install and configure Zsh (oh-my-zsh) as you like.

```toml
[plugins.zsh]
theme = "afowler"
plugins = []    # Plugins name or link
extras = []     # Extra line for .zshrc

# Add zsh alias (multiple)
[[plugins.zsh.alias]]
name = ""
cmd = ""
```

## COPY 

Copy host local files inside container. 

**DO NOT** put any sensible file (private keys, tokens, passwords) inside your container if you aim tu push 
the image to a container registry. Use [secrets](#SECRETS-(Not-yet-implemented)) plugin instead.

```toml
[plugins.copy]    # Copy local file / directory

[[plugins.copy.files]]   # File / directory entry (multiple)
src = ""                 # Host path
dest = ""                # Container path
```

## DOWNLOAD 

Download ressource from any URL. 
Uderlying code will use builtin `wget` to fetch ressource(s).

```toml
[plugins.download]    # Download ressource from URL

[[plugins.download.ressources]]   # Ressource to download (multiple)
url = ""                          # Ressource public URL
target = ""                       # Target container path for download
```

## GIT CLONE 

Clone a git repository inside your conainer.

```toml
[plugins.git]    # Download ressource from URL

[[plugins.git.repos]]   # Ressource to download (multiple)
url = ""                # Repository URL
target = ""             # Target clone directory in container
```

## TMUX

Configure Tmux terminal splitter.

```toml
[plugins.tmux]
config = []
```

## GNU SCREEN 

Configure GNU Screen terminal splitter.

```toml
[plugins.screen]
config = []
```

## SECRETS (Not yet implemented)

Add secrets in your container image.

```toml
[plugins.secrets]
files = []
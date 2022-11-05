# Doco installation

We assume that you use `bash` as your main shell.

If you use `zsh` or `fish`, you need to do different things
everywhere where `bash` is mentioned.

## Install for a single user

### Requirements

- [pipx](https://pypa.github.io/pipx/installation/)

### Install

```bash
pipx install doco-cli
```

To install a specific version, f.ex. `1.0.0`,
you would replace `doco-cli` above with `doco-cli==1.0.0`.

Install shell completion:
```bash
doco --install-completion
```

### Uninstall

```bash
pipx uninstall doco-cli
```

Uninstall shell completion:
```bash
rm ~/.bash_completions/doco.sh
sed -i '\#^'"source $HOME/.bash_completions/doco.sh"'$#d' ~/.bashrc
```

## Install for all users

### Requirements

- [pipx](https://pypa.github.io/pipx/installation/)

    Make sure you install globally, f.ex.:
    ```bash
    sudo python3 -m pip install pipx
    ```

### Install

```bash
sudo PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin pipx install doco-cli
```

To install a specific version, f.ex. `1.0.0`,
you would replace `doco-cli` above with `doco-cli==1.0.0`.

### Uninstall

```bash
sudo pipx uninstall doco-cli
```

## Install from source

### Requirements

- [pyenv](https://github.com/pyenv/pyenv#installation)
- [pipx](https://pypa.github.io/pipx/installation/)
- [Poetry](https://python-poetry.org/docs/#installation)

### Install

```bash
# Change to root
cd "$(git rev-parse --show-toplevel)"

# Deactivate possibly activated venv
source deactivate || true

# Create virtual environment
pyenv install -s
poetry env use $(pyenv which python)
poetry install

# Install shell completion
scripts/bin/doco --install-completion

# Add to $PATH
echo 'PATH="$PATH:'"$PWD/scripts/bin"'"' >>~/.bashrc
```

You then need to restart your shell
(open a new terminal or re-login or run `exec $SHELL`).

### Uninstall

```bash
rm ~/.bash_completions/doco.sh
sed -i '\#^'"source $HOME/.bash_completions/doco.sh"'$#d' ~/.bashrc
sed -i '\#^PATH="$PATH:'"$PWD/scripts/bin"'"$#d' ~/.bashrc
```

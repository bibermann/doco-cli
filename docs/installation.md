# Doco installation

## Install in system

### Install

```bash
pipx install doco-cli
doco --install-completion
```

### Uninstall

```bash
pipx uninstall doco-cli
rm ~/.bash_completions/doco.sh
sed -i '\#^'"source $HOME/.bash_completions/doco.sh"'$#d' ~/.bashrc
```

## Install from source

We assume that you use `bash` as your main shell.

If you use `zsh` or `fish`, you need to do different things at these steps:
- Install » `# Add to $PATH`
- Uninstall

### Install

Requirements:
- `poetry`
- `pyenv`

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

You then need to restart your shell (open a new terminal or re-login).

### Uninstall

```bash
rm ~/.bash_completions/doco.sh
sed -i '\#^'"source $HOME/.bash_completions/doco.sh"'$#d' ~/.bashrc
sed -i '\#^PATH="$PATH:'"$PWD/scripts/bin"'"$#d' ~/.bashrc
```

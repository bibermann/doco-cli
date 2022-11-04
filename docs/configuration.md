# Doco configuration

Doco uses the first `doco.config.toml` or `doco.config.json` file it finds,
beginning at the current working directory,
going upwards the directory hierarchy.

Environment variables can override the settings found in the configuration file.

## Configuration possibilities

Example configuration file
`doco.config.toml` ([TOML syntax](https://toml.io/en/)):
```toml
[[output.text_substitutions.bind_mount_volume_path]]
pattern = "^/var/(.*)$"
replace = "[red]/var/\\1[/]"

[backup.rsync]
rsh = "ssh -p 22 -i /home/johndoe/.ssh/id_ed25519"
host = "backup-user@my-nas.example.com"
module = "NetBackup"
root = "/docker-projects"
```

Instead of `doco.config.toml` you may give a
`doco.config.json` (JSON syntax).

Example environment variables:
```bash
DOCO_BACKUP_RSYNC_RSH="ssh -p 22 -i /home/johndoe/.ssh/id_ed25519"
DOCO_BACKUP_RSYNC_HOST="backup-user@my-nas.example.com"
DOCO_BACKUP_RSYNC_MODULE="NetBackup"
DOCO_BACKUP_RSYNC_ROOT="/docker-projects"
```

## Configuration details

### Output

In `.output.text_substitutions.bind_mount_volume_path`
you can define how you want to highlight _bind mounts_ depending on its source path.
In the example above, each mount point beginning with `/var/` is highlighted in red.
If this section appears more than once, all the rules are applied in order.

More information:
- For the regular expression syntax, see https://docs.python.org/3/library/re.html.
- For the text formatting syntax, see https://rich.readthedocs.io/en/stable/markup.html.
- For a list of supported colors, see https://rich.readthedocs.io/en/stable/appendix/colors.html.

### Backup

You need a `.backup.rsync` configuration for using the `doco backups` command.

Doco uses rsync-daemon features via a remote-shell connection.
See:
- https://download.samba.org/pub/rsync/rsync.1#opt--rsh
- https://download.samba.org/pub/rsync/rsync.1#USING_RSYNC-DAEMON_FEATURES_VIA_A_REMOTE-SHELL_CONNECTION

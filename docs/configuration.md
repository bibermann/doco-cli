# Doco configuration

Doco uses the first `doco.config.json` it finds,
beginning at the current working directory,
going upwards the directory hierarchy.

## Example

Example configuration file `doco.config.json`:
```json
{
  "output": {
    "text_substitutions": {
      "bind_mount_volume_path": [
        {
          "pattern": "^/var/(.*)$",
          "replace": "[red]/var/\\1[/]"
        }
      ]
    }
  },
  "backup": {
    "rsync": {
      "rsh": "ssh -p 22 -i /home/johndoe/.ssh/id_ed25519",
      "host": "backup-user@my-nas.example.com",
      "module": "NetBackup",
      "root": "/docker-projects"
    }
  }
}
```

## Configuration options

### Output

In `.output.text_substitutions.bind_mount_volume_path`
you can define how you want to highlight _bind mounts_ depending on its source path.
In the example above, each mount point beginning with `/var/` is highlighted in red.

More information:
- For the regular expression syntax, see https://docs.python.org/3/library/re.html.
- For the text formatting syntax, see https://rich.readthedocs.io/en/stable/markup.html.
- For a list of supported colors, see https://rich.readthedocs.io/en/stable/appendix/colors.html.

### Backup

For the `doco backups` command, you need a `rsync` configuration.

Doco uses rsync-daemon features via a remote-shell connection.
See:
- https://download.samba.org/pub/rsync/rsync.1#opt--rsh
- https://download.samba.org/pub/rsync/rsync.1#USING_RSYNC-DAEMON_FEATURES_VIA_A_REMOTE-SHELL_CONNECTION

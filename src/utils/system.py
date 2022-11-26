import getpass
import grp
import os
import pwd
import shutil
import typing as t


def get_user_groups(user: str = getpass.getuser()) -> list[str]:
    """Get a list of groups the given user belongs to.

    Source: https://stackoverflow.com/a/9324811/704821
    """
    groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
    gid = pwd.getpwnam(user).pw_gid
    groups.append(grp.getgrgid(gid).gr_name)
    return groups


def chown_given_strings(path: t.Union[str, os.PathLike[str]], uid: t.Optional[str], gid: t.Optional[str]):
    if uid is not None or gid is not None:
        shutil.chown(
            path,
            int(uid) if uid is not None and uid.isnumeric() else uid,  # type: ignore
            int(gid) if gid is not None and gid.isnumeric() else gid,  # type: ignore
        )

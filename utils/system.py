import getpass
import grp
import pwd


def get_user_groups(user: str = getpass.getuser()) -> list[str]:
    """Get a list of groups the given user belongs to.

    Source: https://stackoverflow.com/a/9324811/704821
    """
    groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
    gid = pwd.getpwnam(user).pw_gid
    groups.append(grp.getgrgid(gid).gr_name)
    return groups

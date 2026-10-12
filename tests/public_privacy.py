"""Independent recursive privacy assertion shared by HTTP contract tests.

Do not import production sanitizers here: the oracle must catch their omissions.
"""
import re


PRIVATE_LOCATION = re.compile(
    r"file://|[A-Za-z]:[\\/]|\\\\[^\\\s]+\\|"
    r"/(?:Users|home|private|tmp|var|opt|etc|usr|root|Volumes|mnt|srv|run|workspace|workspaces)/|"
    r"(?:^|[\s\[\](){}\"'=,:;])/(?![/\s])[^\s\[\](){}\"',;<>]+",
    re.I,
)


def assert_no_local_paths(value, *, private_roots=()):
    def walk(item, location):
        if isinstance(item, dict):
            for index, (key, child) in enumerate(item.items()):
                walk(key, f"{location}.key[{index}]")
                walk(child, f"{location}.value[{index}]")
        elif isinstance(item, (list, tuple)):
            for index, child in enumerate(item):
                walk(child, f"{location}[{index}]")
        elif isinstance(item, str):
            assert not PRIVATE_LOCATION.search(item), f"local path at {location}"
            assert not any(str(root) in item for root in private_roots), f"private root at {location}"
    walk(value, "$")

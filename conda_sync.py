#!/usr/bin/env python
from __future__ import print_function
import itertools
import subprocess

import conda.exports
import networkx

import re
from pathlib import Path
import argparse

import re

def bash(cmd: str):
    print(f"running:\n{cmd}")
    return subprocess.run(cmd, shell=True, executable="/bin/bash", check=True)


def parse_spec(spec: str):
    m = re.match(
        "^(?:(?P<channel>.*)::)?(?P<name>[\w-]+)(?P<version>[<>=]+[^\n]+)?$", spec
    )
    if m is None:
        raise ValueError(f'"{spec}" not recognized')
    return m.groupdict()


def get_local_cache(prefix):
    return conda.exports.linked_data(prefix=prefix)


def make_cache_graph(cache):
    g = networkx.DiGraph()
    for k, v in cache.items():
        g.add_node(v["name"], key=k, value=v)
        for j in v["depends"]:
            n2 = j.split(" ")[0]
            g.add_edge(v["name"], n2)
    return g


def stripComments(code):
    for line in code:
        line = line.partition("#")[0].rstrip()
        if line:
            yield line


def prune(env):
    prefix, channels, dependencies = env["prefix"], env["channels"], env["dependencies"]

    spec2name = lambda s: parse_spec(s)["name"]

    to_keep_user = set(map(spec2name, dependencies))
    to_keep_system = set(["conda"])
    to_keep = set([*to_keep_user, *to_keep_system])

    l = get_local_cache(prefix)
    g = make_cache_graph(l)

    def is_develop(n):
        d = g.nodes[n]
        if "key" not in d:
            return False
        else:
            return d["key"].channel == "<develop>"

    to_keep |= set(filter(is_develop, g.nodes))

    print(f"{to_keep=}")

    def flood(g, nodes):
        marked = set()

        def _flood(node):
            if node not in marked:
                marked.add(node)
                for k, v in g.out_edges(node):
                    _flood(v)

        for node in nodes:
            _flood(node)
        return marked

    to_remove = set(g.nodes) - flood(g, to_keep)
    if not to_remove:
        print("Nothing to remove")
        return
    to_remove_roots = {n for n in to_remove if g.in_degree(n) == 0}

    print(f"Roots of removal: {' '.join(to_remove_roots)}")

    remove_cmd = f"mamba remove --no-pin --use-index-cache --override-channels {' '.join(f'-c {c}' for c in channels)} --prefix {env['prefix']} {' '.join(to_remove)}"

    bash(remove_cmd)


def write_pin(env):
    with (Path(env["prefix"]).expanduser() / "conda-meta/pinned").open("w") as f:
        for spec in env["dependencies"]:
            d = parse_spec(spec)
            if d["version"] or d["channel"]:
                c = d["channel"]
                f.write(
                    f"{c+'::' if c else ''}{d['name']}{d['version'] if d['version'] else ''}\n"
                )


def get_channel_specs(env):
    specs = list(map(parse_spec, env["dependencies"]))

    args_channels = itertools.chain(
        env["channels"],
    )

    args = [
        f"--prefix {env['prefix']}",
        "--override-channels",
        " ".join(f"-c {c}" for c in args_channels),
    ]
    args += [
        '"'
        + (d["channel"] + "::" if d["channel"] else "")
        + d["name"]
        + (d["version"] if d["version"] else "")
        + '"'
        for d in specs
    ]

    return args


def args_install(env):
    return ["--strict-channel-priority ", *get_channel_specs(env)]


def args_update(env):
    return args_install(env)


def create(env):
    print(f"Creating {env['prefix']}")
    args = [
        "--no-default-packages",
        *args_install(env),
    ]
    cmd = " ".join(["mamba create", *args])
    bash(cmd)


def update(env):

    # pinning only works for new packages
    # ie if the version for a package changes, it needs to be removed manually
    print(f"Updating {env['prefix']}")
    p = Path(env["prefix"]).expanduser() / "conda-meta/pinned"
    if p.exists():
        p.unlink()
    
    cmd = " ".join([
        "mamba install",
        *args_install(env),
        ])
    
    bash(cmd)
    
    write_pin(env)

    cmd = " ".join(["mamba update", *args_update(env)])
    
    bash(cmd)


def sync(env):
    if not Path(env["prefix"]).expanduser().exists():
        create(env)
    else:
        prune(env)
        update(env)


def main(sys_args):
    parser = argparse.ArgumentParser(
        description="Update a conda environment with pruning and mamba in a reproducible manner.",
    )

    parser.add_argument(
        "--prefix",
        type=str,
        help="set to environment.yml' value if present else ./.conda",
    )
    parser.add_argument(
        "--file",
        default="environment.yml",
        type=str,
    )

    parser.add_argument(
        "mode", default="sync", choices=["sync", "freeze", "replicate"], type=str
    )
    args = parser.parse_args(sys_args)

    import yaml

    file = Path(args.file)
    if not file.exists():
        with file.open("w") as f:
            yaml.dump(
                {
                    "prefix": args.prefix or "./.conda",
                    "channels": ["conda-forge", "nodefaults"],
                    "dependencies": ["python"],
                },
                f,
            )
    assert file.exists()

    with file.open("r") as f:
        env = yaml.safe_load(f)

    if args.prefix:
        env["prefix"] = args.prefix
    if "prefix" not in env:
        env["prefix"] = "./.conda"
    if "~" in env["prefix"]:
        assert env["prefix"][:2] == "~/"
        env["prefix"] = str(Path.home() / (env["prefix"][2:]))
    env["prefix"] = str(Path(env["prefix"]).absolute())

    mode: str = args.mode
    if mode == "sync":
        sync(env)
    elif mode == "freeze":
        bash(f"mamba list --prefix {env['prefix']} --explicit > spec-file.txt")
    elif mode == "replicate":
        if Path(env["prefix"]).expanduser().exists():
            bash(f"rm -rdf {env['prefix']}")
        bash(f"mamba create --prefix {env['prefix']} --file spec-file.txt")
    else:
        raise ValueError(f"unrecognized mode {mode}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])

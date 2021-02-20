#!/usr/bin/env python
from __future__ import print_function

import conda.exports
import networkx

import re
from pathlib import Path


def get_local_cache(prefix):
    return conda.exports.linked_data(prefix=prefix)


def make_cache_graph(cache):
    g = networkx.DiGraph()
    for k,v in cache.items():
        g.add_node(v['name'], key=k,value=v)
        for j in v['depends']:
            n2 = j.split(' ')[0]
            g.add_edge(v['name'], n2)
    return(g)

def stripComments(code):
    for line in code:
        line = line.partition('#')[0].rstrip()
        if line:
            yield line

def main(extra_args):
    channels = stripComments(Path('channels.txt').read_text().split('\n'))

    specs = stripComments(Path('packages.txt').read_text().split('\n'))
    spec2name = lambda s : re.match("^(?:[a-z.]+:)?([^<=>]+)", s).groups()[0]

    prefix='./.conda'
    to_keep_user=set(map(spec2name,specs))
    to_keep_system=set(['conda'])
    to_keep=set([*to_keep_user,*to_keep_system])

    l = get_local_cache(prefix)
    g = make_cache_graph(l)

    def is_develop(n):
        d=g.nodes[n]
        if 'key' not in d:
            return False
        else:
            return d['key'].channel=='<develop>'
            
    to_keep|=set(filter(is_develop,g.nodes))

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

    to_remove = set(g.nodes)-flood(g,to_keep)
    if not to_remove:
        print('Nothing to remove')
        return
    to_remove_roots = {n for n in to_remove if g.in_degree(n)==0}

    print(f"Roots of removal: {' '.join(to_remove_roots)}")

    import subprocess
    import os

    remove_cmd=f"mamba remove --no-pin --use-index-cache --override-channels {' '.join(f'-c {c}' for c in channels)} --prefix {os.environ['ENV_PREFIX']} {extra_args} {' '.join(to_remove)}"

    subprocess.run(remove_cmd,shell=True)

if __name__ == "__main__":
    import sys
    main(' '.join(sys.argv[1:]))
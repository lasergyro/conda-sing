Usage: conda-sing conda|sing|upgrade [args...]

Manages and packages a conda environment in .conda in a Singularity container using mamba & micromamba.

Containers are tagged with last commit that changed the container's definition.

Build is done remotely on sylabs.io. Tested on Linux and WSL2.

## Typical usage:

Put `./conda-sing` on PATH.

### Conda:
- Install conda (e.g. https://docs.conda.io/en/latest/miniconda.html )
- In your base environment install mamba, networkx and yaml.
- Cd to your code repo
- Create empty environment with (`conda-sing conda update` )
- Add environment to gitignore `echo '.conda/' >> '.gitignore'`
- Edit environment.yml and run `conda-sing conda update`
- Run `conda-sing conda freeze` to freeze environment to spec-file.txt

### Singularity:
- Install singularity if not present ( `conda-sing sing install` )
- Create an account on sylabs.io, create and save access token
- Run `conda-sing sing config` and edit sing.config.sh accordingly
- Run `singularity remote login` and enter access token
- Run `conda-sing sing freeze` to create the container definition.
- Commit and push changes to repo: `git add . && git commit -m <message>`
- Run `conda-sing sing make remote` to create and push the container.
- Run `conda-sing sing show` to get the container address, `TARGET`.
- Test with `singularity exec $TARGET bash -l " python -i"`

### On cluster:

Configure Singularity cache location so they are in a shared filesystem, i.e.

```sh
# place on your .bash_profile
SING=~/Scratch/.singularity
export SINGULARITY_CACHEDIR=$SING/cache
export SINGULARITY_TMPDIR=$SING/tmp
export SINGULARITY_LOCALCACHEDIR=$SING/localcache
export SINGULARITY_PULLFOLDER=$SING/pull
export SINGULARITY_BINDPATH=~/Scratch:~/Scratch
unset SING
# run at least once
mkdir -p $SINGULARITY_CACHEDIR
mkdir -p $SINGULARITY_TMPDIR
mkdir -p $SINGULARITY_LOCALCACHEDIR
mkdir -p $SINGULARITY_PULLFOLDER
```

### On cluster/locally for testing:

- Without the repo:
	- On a login node:
		- put contents of `sing.env.sh` in your .bash_profile
		- run `singularity pull $TARGET`

		- Test with `singularity exec $TARGET bash -l "python -i"`
	- On a job
		- use a login shell '#!/bin/bash -l"
		- run `singularity exec $TARGET bash -l "exec <command> <args...>"` 

- With the repo (better isolation):
	- Locally or on a login node:
		- In your repo create symbolic links, for instance `ln -s ~/Scratch/data .`
	- On a login node
		- Install `conda-sing`
		- Clone your repo to a directory (DIR) and cd to it
		- Run `conda-sing sing pull` to cache the container
	- On a job
		- Use a login shell in your job script '#!/bin/bash -l" so `conda-sing` is on PATH
		- cd to $DIR
		- Run `conda-sing sing exec <executable> <args...>` to use the container.
		- The command will start with DIR as working directory, so pass it a path relative to DIR e.g:
			```sh
			#!/bin/bash -l
			...
			cd <DIR>
			conda-sing sing exec <executable> ./data/exp3
			```
	- MPI jobs with either:
		- prefix with MPI runner:
			- `mpirun <mpi args> singularity exec $TARGET bash -l "exec <command> <args...>"`
			or
			- `mpirun <mpir args> conda-sing sing exec <executable> <args...>`

### Editing the environment:
After editing environment.yml, run `conda-sing conda update`.

Once done testing locally, run `conda-sing upgrade`.

This will update the environment, write over the conda spec-file and the container definition Singularity, complain and exit if they need to be commited, after which, if called again, will, if necessary, remake the container.

### Replicating the environment:
Run `conda-sing conda replicate`. This will read the spec-file and recreate the environment exactly.


## Development Notes

### Incremental changes to environment
`conda env` has a --prune flag to remove files, however it considers `conda install` history (
https://github.com/conda/conda/issues/7279 ).
`conda-sing conda update` currently parses `environment.yml` and the conda environment state to find unused packages, which it then uninstalls.
This is experimental and might break easily, in which case delete `./.conda` first.


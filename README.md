Usage: conda-sing co|da|sing|upgrade [args...]
Manages and packages a conda environment in .conda in a Singularity container using mamba & micromamba. Containers are tagged with last commit that changed the container's definition.
Build is done remotely on sylabs.io. Tested on Linux and WSL2.

Typical usage:

Put this directory on PATH.

Conda:
	Install conda (e.g. https://docs.conda.io/en/latest/miniconda.html )
	Cd to your code repo
	Make environment in ./.conda
		Create empty with (`conda-sing conda create` )
		Edit channels.txt and packages.txt and run (`conda-sing conda update`)
		Add environment to gitignore `echo '.conda/' >> '.gitignore'`
	Run `conda-sing conda freeze` to freeze environment to spec-file.txt

Singularity:
	Install singularity if not present ( `conda-sing sing install` )
	Create an account on sylabs.io, create and save access token
	
	Run `conda-sing sing config` and edit sing.config.sh accordingly
	Run `singularity remote login` and enter access token

	Run `conda-sing sing freeze` to create the container definition.
	Commit and push changes to repo.
	Run `conda-sing sing make remote` to create and push the container.
	Run `conda-sing sing show` to get the container address, TARGET.

	Test with `singularity exec $TARGET bash -l " python -i"`

On cluster:
	Configure Singularity cache location to they are in a shared filesystem, i.e.
	```
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

On cluster/locally for testing:

	Without the repo:
		On a login node:
			put contents of `sing.env.sh` in your .bash_profile
			run `singularity pull $TARGET`

			Test with
				`singularity exec $TARGET bash -l "python -i"`
		On a job
			use a login shell '#!/bin/bash -l"
			run `singularity exec $TARGET bash -l "exec <command> <args...>"` 

	With the repo (better isolation):
		Locally or on a login node:
			In your repo create symbolic links, for instance `ln -s ~/Scratch/data .`
		On a login node
			Install `conda-sing`
			Clone your repo to a directory (DIR) and cd to it
			Run `conda-sing sing pull` to cache the container
		On a job
			Use a login shell in your job script '#!/bin/bash -l" so `conda-sing` is on PATH
			cd to $DIR
			Run `conda-sing sing exec <executable> <args...>` to use the container.
			The command will start with DIR as working directory, so pass it a path relative to DIR.
			e.g.
			```
			#!/bin/bash -l
			...
			cd <DIR>
			conda-sing sing exec <executable> ./data/exp3
			```
	MPI jobs with either:
		prefix with MPI runner:
			`mpirun <mpi args> singularity exec $TARGET bash -l "exec <command> <args...>"`
			or
			`mpirun <mpir args> conda-sing sing exec <executable> <args...>`

After changing the environment (editing packages.txt or channels.txt):
	Run `conda-sing upgrade`
		This will update the environment, write over ./spec-file.txt and ./Singularity, complain and exit if they need to be commited, after which, if called again, will, if necessary, remake the container.
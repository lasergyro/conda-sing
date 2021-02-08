#!/usr/bin/env bash

# Full path of the current script
THIS=`readlink -f "${BASH_SOURCE[0]}" 2>/dev/null||echo $0`
# The directory where current script resides
DIR=`dirname "${THIS}"`

function inject(){
	echo "cat <<-'EOF_SING_DEF' > $3"
	cat "$2" | while IFS= read line; do echo "$1	$line"; done
	echo "$1	EOF_SING_DEF"
}

cat << EOF
Bootstrap: library
From: ubuntu:18.04

%setup -c /bin/bash
	if [ -L /dev/shm ]; then
		if [ ! -d /run/shm ]; then exit 1; fi
		mkdir -p /dev/manual
		ln -s /dev/manual \${SINGULARITY_ROOTFS}/run/shm
		touch \${SINGULARITY_ROOTFS}/rm_run_shm
	fi

%post -c /bin/bash
	set -e

	DIR=\$(mktemp -d sing_def.XXX )
	echo "building in \$DIR"
	cd \$DIR

	$(inject "	" spec-file.txt spec-file.txt)

	$(inject "	" $DIR/install.conda.container.sh install.conda.container.sh)

	apt-get update
	apt-get -y upgrade

	mkdir /pwd

	. install.conda.container.sh

	apt-get autoremove --purge -y; apt-get clean -y
	rm -rf /var/lib/{apt,dpkg,cache,log}

	cd ..
	rm -rdf \$DIR

	mkdir /test
	$(inject "	" sing.test.sh /test/sing.test.sh)
	chmod +x /test/sing.test.sh

	if [ -f /rm_run_shm ]; then 
		rm /run/shm;
		rm /rm_run_shm
	fi

%test
	bash -l -c '/test/sing.test.sh'

%help
	This container encapsulates a conda environment at /opt/conda.
	This is loaded via /etc/profile.d/micromamba.sh.
EOF
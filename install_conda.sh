#!/usr/bin/env bash
# expects ./spec-file.txt
set -e

echo "installing micromamba"

apt-get install -y ca-certificates wget bash bzip2

wget -qO- https://micromamba.snakepit.net/api/micromamba/linux-64/latest | tar -xvj bin/micromamba --strip-components=1

mv micromamba /bin/

micromamba shell init -s bash -p /opt/micromamba

chmod o+rX /opt/micromamba

cat <<-'EOF' > /etc/profile.d/micromamba.sh
export MAMBA_EXE="/bin/micromamba";
export MAMBA_ROOT_PREFIX="/opt/micromamba";
export MAMBA_NO_BANNER=1
__mamba_setup="$('/bin/micromamba' shell hook --shell bash --prefix '/opt/micromamba' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    if [ -f "/opt/micromamba/etc/profile.d/mamba.sh" ]; then
        . "/opt/micromamba/etc/profile.d/mamba.sh"
    else
        export PATH="/opt/micromamba/bin:$PATH"
    fi
fi
unset __mamba_setup

export PYTHONDONTWRITEBYTECODE=true
EOF
chmod o+rX /etc/profile.d/micromamba.sh

. /etc/profile.d/micromamba.sh

echo "spec"
micromamba create --strict-channel-priority -f spec-file.txt -p /opt/conda
chmod -R o+rX /opt/conda
echo "micromamba activate /opt/conda">> /etc/profile.d/micromamba.sh

echo "clean"
TARGET=/opt/conda
rm -rf $TARGET/pkgs
find $TARGET/ -follow -type f -name '*.a' -delete
find $TARGET/ -follow -type f -name '*.pyc' -delete
find $TARGET/ -follow -type f -name '*.js.map' -delete
find $TARGET/lib/python*/site-packages/bokeh/server/static -follow -type f -name '*.js' ! -name '*.min.js' -delete || :

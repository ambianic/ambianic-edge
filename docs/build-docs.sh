
# verbose mode, exit on error
set -ex

# parse command line arguments
# while getopts ":u" flag
# do
#     case "${flag}" in
#        u) upload_codecov=true;;
#     esac
# done

# if [ "$upload_codecov" = true ] ; then
#     echo 'Code coverage upload flag set. Will upload report to codecov.io'
# fi

python3 -m pip install -U pdoc3 # python code documentation generator
BASEDIR=$(dirname $0)
# Install the ambianic module
python3 -m pip install -e $BASEDIR/../src
echo "Script location: ${BASEDIR}"
# change work dir location to a predictable place
# where codecov can find the generated reports
cd $BASEDIR/../
echo PWD=$PWD
# python3 -m 
pdoc --html --output-dir docs/dist src/ambianic


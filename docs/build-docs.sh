
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

# Install python code documentation generator
python3 -m pip install -U pdoc3 
BASEDIR=$(dirname $0)
# Install the ambianic edge module
python3 -m pip install -e $BASEDIR/../src
echo "Script location: ${BASEDIR}"

# change work dir to project root dir
cd $BASEDIR/../
echo PWD=$PWD

# Generate Python API docs
mkdir -p docs/dist/pythonapi
pdoc --html --output-dir docs/dist/pythonapi src/ambianic

# Generate OpenAPI docs
cd docs
mkdir -p dist/openapi
cp ambianic-edge-openapi.html dist/openapi/
python3 fastapi_spec_gen.py --appmodule="ambianic.webapp.fastapi_app" --outfile="dist/openapi/ambianic-edge-openapi.json"

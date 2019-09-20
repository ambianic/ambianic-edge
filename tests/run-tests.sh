
# verbose mode, exit on error
set -ex

pip3 install -U pytest # unit test tool
pip3 install -U codecov # code coverage tool
pip3 install -U pytest-cov # coverage plugin for pytest
pip3 install pylint # python linter
BASEDIR=$(dirname $0)
pip3 install -e $BASEDIR/../src
echo "Script location: ${BASEDIR}"
# install ambianic package in edit mode
# cd $TESTS_DIR
# pip3 install -e "${BASEDIR}/../"
TESTS_DIR="${BASEDIR}/../tests"
python3 -m pytest $TESTS_DIR

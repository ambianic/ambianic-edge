
# verbose mode, exit on error
set -ex

pip3 install -U pytest # unit test tool
pip3 install -U codecov # code coverage tool
pip3 install -U pytest-cov # coverage plugin for pytest
pip3 install -U pylint # python linter
pip3 install -U dynaconf
BASEDIR=$(dirname $0)
pip3 install -e $BASEDIR/../src
echo "Script location: ${BASEDIR}"
# change work dir location to a predictable place
# where codecov can find the generated reports
cd $BASEDIR/../
echo PWD=$PWD
python3 -m pytest --cov=ambianic --cov-report=xml --cov-report=term tests/
# pytest --cov-report=xml --cov=ambianic tests
# codecov
# pylint --errors-only src/ambianic
# submit code coverage report to codecov.io

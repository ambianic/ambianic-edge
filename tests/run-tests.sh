
# verbose mode, exit on error
set -ex

pip3 install -U pytest # unit test tool
pip3 install -U codecov # code coverage tool
pip3 install -U pytest-cov # coverage plugin for pytest
pip3 install -U pylint # python linter
BASEDIR=$(dirname $0)
pip3 install -e $BASEDIR/../src
echo "Script location: ${BASEDIR}"
TESTS_DIR="${BASEDIR}/../tests"
python3 -m pytest $TESTS_DIR --cov-report=xml --cov=ambianic
# pytest --cov-report=xml --cov=ambianic tests
# codecov
# pylint --errors-only src/ambianic
# submit code coverage report to codecov.io
  

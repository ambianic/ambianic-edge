
# exit on error, verbose mode
set -ex

# script's own dir
MY_DIR="$(dirname "$0")"
cd $MY_DIR/../
echo PWD=$PWD
pip3 install mkdocs
pip3  install pydoc-markdown
cp src/ambianic/webapp/client/public/favicon.ico $MY_DIR/docs/
pydocmd simple ambianic++ ambianic.pipeline++ ambianic.webapp++ > "$MY_DIR/docs/ambianic-python-api.md"
mkdocs build -f "$MY_DIR/mkdocs.yml"

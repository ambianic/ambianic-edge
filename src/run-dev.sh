export LD_LIBRARY_PATH=/opt/vc/lib
cd /workspace
pip3 install -r build/requirements.txt
pip3 install -e src
python3 -m ambianic


import pytest

import ambianic

def test_no_work_dir():
    with pytest.raises(AssertionError):
        ambianic.start(None)

def test_bad_work_dir():
    with pytest.raises(AssertionError):
        ambianic.start('/_/_/_dir_does_not_exist___')

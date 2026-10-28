import sys

import numpy
import pandas
import requests
import yaml


def test_python_version():
    assert sys.version_info[:2] == (3, 11)


def test_dependencies():
    assert numpy.__version__
    assert pandas.__version__
    assert requests.__version__
    assert yaml.__version__
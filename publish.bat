python setup.py sdist
python setup.py bdist_wheel
twine upload --repository testpypi dist/*
pip install -U --index-url https://test.pypi.org/simple/ GramophoneTools
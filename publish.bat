call .\docs\make.bat html
python setup.py sdist
python setup.py bdist_wheel
twine upload dist/*
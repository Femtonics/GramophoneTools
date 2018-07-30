call .\docs\make.bat html
python setup.py sdist
twine upload dist/*
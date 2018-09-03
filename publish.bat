call .\docs\make.bat html
python setup.py sdist
python setup.py bdist_wheel
python setup.py bdist_msi
python setup.py bdist_wininst --bitmap "res\femtonics_installer.bmp"
python setup.py clean --all
twine upload dist/*
call upload.bat
git push
rm -r -fo build
rm -r -fo dist
rm -r -fo docs\build\
rm -r -fo GramophoneTools.egg-info
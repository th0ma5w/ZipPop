mkdir temp
cp three_kay.zip ./temp/
python3 ../zippop.py all ./temp/three_kay.zip
rm one_kay*
rm temp/three_kay.zip
rmdir temp


# WebsiteImageSize
A python script to find all the images in bulk website with >100kb [ changeable ] to optimize it.

use url.txt file to list all the url. write url in single line

run python script using python script.py urls.txt

prequisite: pip install requests beautifulsoup4 Pillow

This will create two files.


File 1: failed_websites: It will list all the website which were not included and not opening.

File 2: image_report: It will list domain, image path, size and dimention

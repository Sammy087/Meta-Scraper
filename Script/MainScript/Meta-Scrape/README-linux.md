how to:

Prepare host (one time setup):
sudo apt install python3-venv
sudo apt install imagemagick ffmpeg

Edit /etc/ImageMagick-6/policy.xml:
Find the following line (near bottom of the file) 
<policy domain="path" rights="none" pattern="@*" />
And replace with:
<!-- <policy domain="path" rights="none" pattern="@*"/> -->


Prepare Python Venv for isolation of dependencies (one time setup)
Create python virtual env:
python3 -m venv .venv



Enter in the virtual space (everytime you open the terminal):
source .venv/bin/activate

download deps (only once):
python -m pip install -r requirements.txt




run:
python main.py


https://www.youtube.com/watch?v=tPEE9ZwTmy0

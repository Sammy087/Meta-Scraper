FROM python:3.12.4

RUN apt-get update && apt-get -y install \
    ffmpeg \
    fonts-freefont-otf \
    fonts-liberation \
    fonts-liberation2 \
    ghostscript \
    imagemagick \
    locales \
    && rm -rf /var/lib/apt/lists/*
    


RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml \
    && locale-gen C.UTF-8 \
    && /usr/sbin/update-locale LANG=C.UTF-8

ENV LC_ALL=C.UTF-8

ADD . /var/src/MetaScraper/

RUN pip install -r /var/src/MetaScraper/requirements.txt

WORKDIR /data/videos

ENTRYPOINT ["python", "/var/src/MetaScraper/main.py"]



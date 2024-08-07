FROM python:3.12.4

RUN apt-get update && apt-get -y install \
    build-essential \
    chrpath \
    libssl-dev \
    libxft-dev \
    libfreetype6 libfreetype6-dev \
    libfontconfig1 libfontconfig1-dev \
    ffmpeg \
    fontconfig \
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

RUN PHANTOM_JS='phantomjs-2.1.1-linux-x86_64' \
    && wget https://bitbucket.org/ariya/phantomjs/downloads/$PHANTOM_JS.tar.bz2 \
    && tar xvjf $PHANTOM_JS.tar.bz2 \
    && rm $PHANTOM_JS.tar.bz2 \
    && mv $PHANTOM_JS /usr/local/share \
    && ln -sf /usr/local/share/$PHANTOM_JS/bin/phantomjs /usr/local/bin

ADD . /var/src/MetaScraper/

RUN pip install -r /var/src/MetaScraper/requirements.txt

WORKDIR /data/videos

ENTRYPOINT ["python", "/var/src/MetaScraper/main.py"]



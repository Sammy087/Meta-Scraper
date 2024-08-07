docker build -t sammy/meta-scraper .

docker run --rm -it -p 8050:8050 -v ./videos/:/data/videos sammy/meta-scraper

Open browser to: http://127.0.0.1:8050/



https://www.youtube.com/watch?v=tPEE9ZwTmy0

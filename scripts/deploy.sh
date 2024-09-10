set -e
version="0.2.3"

git checkout production

git pull

docker build -t pms:$version .

docker container rm --force pms &>/dev/null && echo 'Removed old container'

docker run -d -p 80:80 --name pms --restart=unless-stopped pms:$version

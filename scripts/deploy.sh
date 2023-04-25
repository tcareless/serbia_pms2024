set -e
version="0.1.10"

git checkout production

docker build -t pms:$version .

docker container rm --force pms &>/dev/null && echo 'Removed old container'

docker run -d -p 80:80 --name pms --restart=unless-stopped pms:$version
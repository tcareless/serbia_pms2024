set -e
version="test"

# git checkout production

git pull

docker build -t pms:$version .

docker container rm --force pms_808 &>/dev/null && echo 'Removed old container'

docker run -d -p 8080:80 --name pms_8080 --restart=unless-stopped pms:$version

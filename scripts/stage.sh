set -e
version="0.1.9-b1"

git checkout main

docker build -t pms-staging:$version .

docker container rm --force pms-staging &>/dev/null && echo 'Removed old container'

docker run -d -p 8080:80 --name pms-staging --rm pms-staging:$version
set -e

git pull

git checkout production

docker-compose -f docker-compose-deploy.yml up -d --build

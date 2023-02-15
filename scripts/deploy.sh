set -e

git checkout main
git pull

git checkout production
git merge main

docker-compose -f docker-compose-deploy.yml up -d --build

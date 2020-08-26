#!/bin/bash
set -e # stop on error

# PUSHES HTML BUILD RESULT TO gh-pages ORPHAN BRANCH
#
# This script assumes GitHub Pages has already been set up:
#
#   1) initialize orphan gh-pages branch:
#       git checkout --orphan gh-pages
#       git rm -rf .
#       touch .nojekyll index.html
#       git add .nojekyll index.html
#       git commit -m "initial github pages"
#       git push -u origin gh-pages
#
#   2) enable github pages for project:
#       - open project settings -> options -> GitHub Pages
#       - under "Source", select gh-pages branch and root folder

# the directory containing the build results of make
BUILD_DIR='_build/html/*'

# build the pages
echo "> building pages"
make html

# create temp directory and checkout gh-pages
pwd=$(pwd)
tmp_dir=$(mktemp -d)
remote_url=$(git config --get remote.origin.url)

echo "> checkout gh-pages in $tmp_dir"
cd $tmp_dir
git clone $remote_url --branch gh-pages .

# set dummy author information such that global git config is not re-used
git config user.name "GitHub Pages Publisher"
git config user.email ""

echo "> cleaning content"
git rm -rf .

build_src="${pwd}/${BUILD_DIR}"
echo "> copy build result from $build_src to $tmp_dir"
cp -R $build_src .

# ensures GitHub does not invoke Jekyll but directly serves the static html webpage
touch .nojekyll

# commit and push to gh-pages
echo "> committing and pushing build result to gh-pages"
git add --all
git commit -m "deployed pages"
git push

echo "> cleanup"
cd $pwd
rm -rf $tmp_dir

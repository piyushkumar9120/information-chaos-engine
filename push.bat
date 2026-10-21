@echo off
echo Cleaning old git setup...
rmdir /s /q .git 2>nul

echo Initializing Git...
git init
git config user.name "piyushkumar9120"
git config user.email "piyushkumar9120637533@gmail.com"

echo Adding files...
git add .

echo Committing files...
git commit -m "feat: complete Information Chaos Engine for FlipHack 26"

echo Setting main branch...
git branch -M main

echo Connecting to GitHub repository...
git remote add origin https://github.com/piyushkumar9120/information-chaos-engine.git

echo Uploading to GitHub...
git push -u origin main

echo Done!
pause
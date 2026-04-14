@echo off
echo Pushing to GitHub...
git add .
git commit -m "%~1"
git push
echo Done!
pause
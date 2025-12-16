@echo off
echo --MakeMigrations--
python manage.py makemigrations

echo. 
echo --Migrate--
python manage.py migrate

echo. 
echo --Done--
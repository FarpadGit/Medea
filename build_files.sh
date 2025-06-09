cd main
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput

cd ..
mkdir -p .vercel/output/static
cp -r ./main/staticfiles/ .vercel/output/static/

cd main
python3 manage.py makemigrations
python3 manage.py migrate
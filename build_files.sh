python3.9 -m pip install -r requirements.txt
python3.9 manage.py collectstatic --noinput

mkdir -p .vercel/output/static
cp -r staticfiles/ .vercel/output/static/

python3.9 manage.py makemigrations
python3.9 manage.py migrate
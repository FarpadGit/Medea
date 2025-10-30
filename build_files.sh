python3 -m venv venv
source venv/bin/activate

python3 -m pip install --upgrade pip

python3 -m pip install -r ./main/requirements.txt --no-dependencies
python3 ./main/manage.py collectstatic --noinput

mkdir -p .vercel/output/static
cp -r ./main/staticfiles/* .vercel/output/static/
cp ./main/main/wsgi.py .vercel/output/main/main/

cd main
# python3 manage.py makemigrations
# python3 manage.py migrate
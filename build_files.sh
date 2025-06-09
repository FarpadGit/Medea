python3 -m venv venv
source venv/bin/activate

python3 -m pip install -r ./main/requirements.txt
python3 ./main/manage.py collectstatic --noinput

mkdir -p .vercel/output/static
cp -r ./main/staticfiles/* .vercel/output/static/

cd main
python3 manage.py makemigrations
python3 manage.py migrate
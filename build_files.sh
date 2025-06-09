export PYTHONPATH=/python312/bin:$PYTHONPATH

python3 -m pip install -r ./main/requirements.txt
python3 ./main/manage.py collectstatic --noinput

python3 -m pip list -v

mkdir -p .vercel/output/static
cp -r ./main/staticfiles/* .vercel/output/static/

cd main
python3 manage.py makemigrations
python3 manage.py migrate
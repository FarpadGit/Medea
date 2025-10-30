uv venv
source .venv/bin/activate

python3 -m pip install --upgrade pip

uv sync
python3 ./main/manage.py collectstatic --noinput

mkdir -p .vercel/output/static
cp -r ./main/staticfiles/* .vercel/output/static/

cd main
# python3 manage.py makemigrations
# python3 manage.py migrate
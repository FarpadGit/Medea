python3 -m pip install --upgrade pip
python3 -m pip install uv

uv venv
source .venv/bin/activate

uv pip install -r .main/requirements.txt
uv run ./main/manage.py collectstatic --noinput

mkdir -p .vercel/output/static
cp -r ./main/staticfiles/* .vercel/output/static/

cd main
# uv run manage.py makemigrations
# uv run manage.py migrate
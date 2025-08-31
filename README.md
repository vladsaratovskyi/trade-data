Trade Data (Django)
===================

Simple Django app to record crypto/forex/index trades and view stats.

Features
- Add trades: type, price, stop loss, volume, result (take/loss), direction (long/short), date, three timeframe images, risk %, R/R, tags, comment
- List with filters by type, result, direction, tags
- Basic stats: totals, win rate, averages; breakdown by type and direction

Quickstart
1) Create venv and install deps
   python -m venv .venv
   .venv\\Scripts\\activate   # Windows
   pip install -r requirements.txt

2) Initialize DB
   python manage.py makemigrations
   python manage.py migrate

3) Run dev server
   python manage.py runserver

4) Visit
   - http://127.0.0.1:8000/        (trades list + filters)
   - http://127.0.0.1:8000/add/    (add trade)
   - http://127.0.0.1:8000/stats/  (stats)

Notes
- Image uploads require Pillow (included in requirements.txt)
- Uploaded images are stored under media/; served automatically in DEBUG
- Use Django Admin to manage tags easily: create a superuser via `python manage.py createsuperuser` and visit /admin


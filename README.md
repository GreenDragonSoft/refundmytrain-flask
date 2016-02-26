## Run with development (sqlite3) database

```
export DATABASE_URL="sqlite:///db.sqlite3"
./app.py
```


## Create database

From Python shell:

```
>>> from app import DB
>>> DB.create_all()
```

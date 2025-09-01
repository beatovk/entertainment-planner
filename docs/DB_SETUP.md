# Database Setup

This project stores places in a SQLite database. Development and tests use the
same schema and include a small set of sample data for experimentation.

## Initialising the database

Run the seed script to create both `raw.db` and `clean.db` in the project
root:

```bash
python apps/ingest/db_init.py
```

The script creates the necessary tables and seeds `clean.db` with three sample
Bangkok places:

* **Tom Yum Goong Master** – Thai restaurant famous for tom yum soup.
* **Lumpini Park** – Central Bangkok park with walking paths and a lake.
* **Sky Bar Bangkok** – Rooftop bar offering panoramic city views.

After running the script a summary of row counts is printed for verification.

## Using a temporary database

The API and test suite automatically create a temporary database when the file
specified by the `DB_PATH` environment variable does not exist. To use a custom
location, set the variable before starting the API or running tests:

```bash
export DB_PATH=/tmp/entertainment.db
```

If the file is missing, the application will initialize it using the same
seed data shown above.


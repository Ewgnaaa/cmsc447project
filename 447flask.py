
#install req dependencies on venv
#localhost:5000 should show connect, /buildings returns query in html /building/<id> (currently 1 2 or 3 should return json data)

import psycopg2
from flask import Flask, render_template

DB_URI = "postgresql://cmsc447db:cmsc447db@cmsc447.cpa4aoaw6a8r.us-east-2.rds.amazonaws.com:5432/postgres"

app = Flask(__name__)

@app.route('/')
def home():
    try:
        conn = psycopg2.connect(
            host='cmsc447.cpa4aoaw6a8r.us-east-2.rds.amazonaws.com',
            dbname='postgres',
            user='cmsc447db',
            password='cmsc447db',
            port=5432,
            sslmode='require'  # if ssl
        )
        conn.close()
        return "Connected to AWS RDS PostgreSQL"

    except Exception as e:
        return f"Failed to connect: {e}"

@app.route('/buildings')
def show_buildings():
    try:
        # Connect to db
        conn = psycopg2.connect(
            host='cmsc447.cpa4aoaw6a8r.us-east-2.rds.amazonaws.com',
            dbname='postgres',
            user='cmsc447db',
            password='cmsc447db',
            port=5432,
            sslmode='require' 
        )

        cur = conn.cursor()

        # Execute a query to get all buildings
        cur.execute("SELECT building_id, name, description, ST_AsText(location) AS location FROM buildings ORDER BY building_id ASC")
        buildings = cur.fetchall()

        # Clean
        cur.close()
        conn.close()

        # Pass the buildings data to the template
        return render_template('index.html', buildings=buildings)

    except Exception as e:
        return f"Error fetching buildings: {e}"

# Run inital
if __name__ == '__main__':
    app.run(debug=True)

import psycopg2
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Db connect if better way to do then lmk
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host='cmsc447.cpa4aoaw6a8r.us-east-2.rds.amazonaws.com',
            dbname='postgres',
            user='cmsc447db',
            password='cmsc447db',
            port=5432,
            sslmode='require'
        )
        return conn
    except Exception as e:
        print(f"Failed to connect to the database: {e}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

# fetch building, lcoation
@app.route('/all-buildings')
def all_buildings():
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor()
        
        query = """
        SELECT 
            building_id, 
            building_name, 
            ST_X(ST_Transform(building_location::geometry, 4326)) AS longitude, 
            ST_Y(ST_Transform(building_location::geometry, 4326)) AS latitude
        FROM buildings;
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()

        buildings = [
            {
                "building_id": row[0],
                "building_name": row[1],
                "longitude": row[2],
                "latitude": row[3]
            }
            for row in rows if row[2] and row[3]
        ]

        cursor.close()
        conn.close()

        print("Buildings Data Sent:", buildings)  # Debugging

        return jsonify(buildings)
    
    except Exception as e:
        print("Error fetching all buildings:", e)
        return jsonify({"error": str(e)}), 500

# Run flask app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


"""
UPDATE buildings 
SET building_location = ST_SetSRID(ST_MakePoint(-76.7423, 39.2550), 4326) 
WHERE building_id = 1;
"""
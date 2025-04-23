

import json
import psycopg2
from flask import Flask, render_template, jsonify, request, send_from_directory
import networkx as nx
import geopy.distance

app = Flask(__name__)

# db connection
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

@app.route('/geojson')
def get_geojson():
    return send_from_directory('.', 'umbc-footways.geojson')

@app.route('/all-buildings', methods=['GET'])
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
        cursor.close()
        conn.close()

        buildings = [
            {
                "building_id": row[0],
                "building_name": row[1],
                "longitude": row[2],
                "latitude": row[3]
            }
            for row in rows if row[2] and row[3]
        ]

        return jsonify(buildings)

    except Exception as e:
        print("Error fetching all buildings:", e)
        return jsonify({"error": str(e)}), 500
    
@app.route('/navigate', methods=['POST'])
def navigate():
    try:
        data = request.json
        user_location = data.get('user_location')  # [lat, lon]
        building_location = data.get('building_location')  # [lat, lon]

        if not user_location or not building_location:
            return jsonify({'error': 'Missing location data'}), 400

        print(f"User location: {user_location}, Building location: {building_location}")

        # Build graph from GeoJSON
        G = build_graph_from_geojson('umbc-footways.geojson')

        # find closest nodes to user and building
        start_node = closest_node(tuple(user_location), G)
        end_node = closest_node(tuple(building_location), G)

        print(f"Closest graph node to user: {start_node} with coordinates {user_location}")
        print(f"Closest graph node to destination: {end_node} with coordinates {building_location}")

        # debug check if path exists
        if not nx.has_path(G, start_node, end_node):
            print(f"No path between {start_node} and {end_node}")
            return jsonify({"error": "No path found between the selected points."}), 400

        # paht calculation here
        path = nx.shortest_path(G, source=start_node, target=end_node, weight='weight')

        if not path:
            return jsonify({"error": "Failed to find a valid path."}), 400

        geojson_path = {
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': path  # [lon, lat]
                },
                'properties': {}
            }]
        }

        return jsonify(geojson_path)

    except Exception as e:
        print("Error calculating navigation path:", e)
        return jsonify({'error': str(e)}), 500


def build_graph_from_geojson(geojson_file):
    with open(geojson_file) as f:
        geo = json.load(f)

    G = nx.Graph()
    for feature in geo['features']:
        if feature['geometry']['type'] == 'LineString':
            coords = feature['geometry']['coordinates']
            for i in range(len(coords) - 1):
                p1 = tuple(coords[i])
                p2 = tuple(coords[i + 1])
                dist = geopy.distance.distance((p1[1], p1[0]), (p2[1], p2[0])).meters
                
                print(f"Adding edge: {p1} -> {p2} with distance {dist:.2f} meters")
                
                G.add_edge(p1, p2, weight=dist)
    
    print("Edges in graph:", list(G.edges))
    
    return G


def closest_node(coord, graph):
    closest = min(graph.nodes, key=lambda node: geopy.distance.distance(coord, (node[1], node[0])).meters)
    print(f"Closest node to {coord} is {closest}")
    
    return closest

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

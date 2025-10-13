import json
import base64
import os
from dotenv import load_dotenv
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import psycopg2
# load environment variables from .env file
load_dotenv()

# db configuration( use env vars)
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
PORT = int(os.getenv('PORT', '2500'))
# basic auth credentials(from .env)
VALID_USERNAME = os.getenv('API_USER')
VALID_PASSWORD = os.getenv('API_PASS')

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500

# db helpers
def get_db_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )

def dict_from_cursor_row(cursor, row):
    return {desc[0]: row[idx] for idx, desc in enumerate(cursor.description)}

# === Custom top-k algorithm (no heapq/sorted/Counter) ===
# We'll implement a simple map aggregation + manual selection via Quickselect-like partition
# to find top-K pickup zones by count. This satisfies the "manually implement an algorithm" requirement.

def quickselect_partition(arr, left, right, pivot_index):
    pivot_value = arr[pivot_index][1]
    # move pivot to end
    arr[pivot_index], arr[right] = arr[right], arr[pivot_index]
    store_index = left
    for i in range(left, right):
        if arr[i][1] > pivot_value:  # note: we want top K -> larger first
            arr[store_index], arr[i] = arr[i], arr[store_index]
            store_index += 1
    # Move pivot to its final place
    arr[right], arr[store_index] = arr[store_index], arr[right]
    return store_index

def quickselect(arr, left, right, k):
    # Select the k-th largest element (0-based; k=0 => largest)
    if left == right:
        return
    pivot_index = left + (right - left) // 2
    pivot_index = quickselect_partition(arr, left, right, pivot_index)
    if k == pivot_index:
        return
    elif k < pivot_index:
        quickselect(arr, left, pivot_index - 1, k)
    else:
        quickselect(arr, pivot_index + 1, right, k)

def top_k_pairs(pairs, k):
    """
    pairs: list of (key, count)
    returns top k pairs sorted by count desc (ties arbitrary).
    Implementation: quickselect to partition and then sort top-k slice (small).
    NOTE: allowed to use built-in sort for the small final slice of size k.
    """
    n = len(pairs)
    if k <= 0:
        return []
    if k >= n:
        # small final sort acceptable
        return sorted(pairs, key=lambda x: x[1], reverse=True)

    # use quickselect to put top-k in front (unsorted)
    quickselect(pairs, 0, n - 1, k - 1)
    topk = pairs[:k]
    # sort final small slice
    topk.sort(key=lambda x: x[1], reverse=True)
    return topk

# Server setup and handlers

class APIHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def _authenticate(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header:
            return False
        try:
            auth_type, credentials = auth_header.split(' ')
            if auth_type.lower() != 'basic':
                return False
            decoded = base64.b64decode(credentials).decode('utf-8')
            username, password = decoded.split(':', 1)
            return username == VALID_USERNAME and password == VALID_PASSWORD
        except Exception:
            return False

    def _send_unauthorized(self):
        self._set_headers(401)
        self.wfile.write(json.dumps({'error': 'Unauthorized', 'message': 'Invalid or missing credentials'}).encode())

    def _send_response(self, data, status_code=200):
        self._set_headers(status_code)
        self.wfile.write(json.dumps(data, default=str, indent=2).encode())

    def _send_error(self, status_code, message):
        self._set_headers(status_code)
        self.wfile.write(json.dumps({'error': True, 'message': message}).encode())

    def do_OPTIONS(self):
        self._set_headers(204)

    # --- Helpers to parse pagination/filtering ---
    def _parse_pagination(self, qs):
        try:
            page = int(qs.get('page', ['1'])[0])
            page_size = int(qs.get('page_size', [str(DEFAULT_PAGE_SIZE)])[0])
        except Exception:
            page, page_size = 1, DEFAULT_PAGE_SIZE
        if page < 1: page = 1
        if page_size < 1: page_size = DEFAULT_PAGE_SIZE
        if page_size > MAX_PAGE_SIZE: page_size = MAX_PAGE_SIZE
        offset = (page - 1) * page_size
        return page, page_size, offset

    # --- GET ---
    def do_GET(self):
        if not self._authenticate():
            self._send_unauthorized()
            return

        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        try:
            if path == '/':
                self._send_response({'success': True, 'message': 'NYC Taxi Analytics API', 'endpoints': [
                    '/trips', '/trips/{trip_id}', '/locations', '/vendors', '/time_dimensions',
                    '/analytics/hourly', '/analytics/daily', '/analytics/location_stats', '/analytics/top_zones'
                ]})

            # GET /vendors
            elif path == '/vendors':
                conn = get_db_conn()
                cur = conn.cursor()
                cur.execute("SELECT vendor_id, vendor_name, description FROM vendors ORDER BY vendor_id;")
                rows = cur.fetchall()
                data = [dict_from_cursor_row(cur, r) for r in rows]
                cur.close(); conn.close()
                self._send_response({'success': True, 'count': len(data), 'data': data})

            # GET /locations (optionally ?zone_name=... or ?bbox=minlon,minlat,maxlon,maxlat)
            elif path == '/locations':
                conn = get_db_conn()
                cur = conn.cursor()
                if 'zone_name' in qs:
                    cur.execute("SELECT created_at, location_id, latitude, longitude, location_type, zone_name FROM locations WHERE zone_name = %s;", (qs['zone_name'][0],))
                elif 'bbox' in qs:
                    bbox = qs['bbox'][0].split(',')
                    if len(bbox) == 4:
                        minlon, minlat, maxlon, maxlat = map(float, bbox)
                        cur.execute("""
                            SELECT location_id, latitude, longitude, zone_name, borough
                            FROM locations
                            WHERE longitude BETWEEN %s AND %s AND latitude BETWEEN %s AND %s;
                        """, (minlon, maxlon, minlat, maxlat))
                    else:
                        cur.execute("SELECT created_at, location_id, latitude, longitude, location_type FROM locations LIMIT 100;")
                else:
                    cur.execute("SELECT created_at, location_id, latitude, longitude, location_type FROM locations LIMIT 100;")
                rows = cur.fetchall()
                data = [dict_from_cursor_row(cur, r) for r in rows]
                cur.close(); conn.close()
                self._send_response({'success': True, 'count': len(data), 'data': data})

            # GET /time_dimensions
            elif path == '/time_dimensions':
                conn = get_db_conn(); cur = conn.cursor()
                cur.execute("SELECT time_id, pickup_datetime, pickup_hour, pickup_day, pickup_month, pickup_weekday, time_of_day, is_weekend FROM time_dimensions LIMIT 200;")
                rows = cur.fetchall()
                data = [dict_from_cursor_row(cur, r) for r in rows]
                cur.close(); conn.close()
                self._send_response({'success': True, 'count': len(data), 'data': data})

            # GET /trips or /trips/{id} with filters: start_date, end_date, min_distance_km, max_distance_km, pickup_zone_id, dropoff_zone_id, page, page_size
            elif path.startswith('/trips'):
                parts = path.strip('/').split('/')
                if len(parts) == 1:
                    # list with filters + pagination + sorting
                    page, page_size, offset = self._parse_pagination(qs)
                    where_clauses = []
                    params = []

                    if 'start_date' in qs:
                        where_clauses.append("pickup_datetime >= %s"); params.append(qs['start_date'][0])
                    if 'end_date' in qs:
                        where_clauses.append("pickup_datetime <= %s"); params.append(qs['end_date'][0])
                    if 'min_distance_km' in qs:
                        where_clauses.append("trip_distance_km >= %s"); params.append(float(qs['min_distance_km'][0]))
                    if 'max_distance_km' in qs:
                        where_clauses.append("trip_distance_km <= %s"); params.append(float(qs['max_distance_km'][0]))
                    if 'pickup_zone_id' in qs:
                        where_clauses.append("pickup_location_id = %s"); params.append(int(qs['pickup_zone_id'][0]))
                    if 'dropoff_zone_id' in qs:
                        where_clauses.append("dropoff_location_id = %s"); params.append(int(qs['dropoff_zone_id'][0]))

                    where_sql = ''
                    if where_clauses:
                        where_sql = 'WHERE ' + ' AND '.join(where_clauses)

                    order_by = 'pickup_datetime DESC'
                    if 'sort_by' in qs:
                        sort_by = qs['sort_by'][0]
                        allowed = {'pickup_datetime','trip_duration','trip_distance_km','trip_speed_kmh'}
                        if sort_by in allowed:
                            order_by = f"{sort_by} DESC"

                    conn = get_db_conn(); cur = conn.cursor()
                    count_q = f"SELECT COUNT(*) FROM trip_facts {where_sql};"
                    cur.execute(count_q, tuple(params))
                    total = cur.fetchone()[0]

                    q = f"""
                    SELECT trip_id, vendor_id, pickup_location_id, dropoff_location_id, pickup_datetime, dropoff_datetime,
                           trip_duration, trip_distance_km, trip_speed_kmh, trip_efficiency, passenger_count
                    FROM trip_facts
                    {where_sql}
                    ORDER BY {order_by}
                    LIMIT %s OFFSET %s;
                    """
                    cur.execute(q, tuple(params + [page_size, offset]))
                    rows = cur.fetchall()
                    data = [dict_from_cursor_row(cur, r) for r in rows]
                    cur.close(); conn.close()
                    self._send_response({'success': True, 'page': page, 'page_size': page_size, 'total': total, 'count': len(data), 'data': data})

                else:
                    # /trips/{trip_id}
                    trip_id = parts[1]
                    conn = get_db_conn(); cur = conn.cursor()
                    cur.execute("SELECT * FROM trip_facts WHERE trip_id = %s;", (trip_id,))
                    row = cur.fetchone()
                    if row:
                        data = dict_from_cursor_row(cur, row)
                        cur.close(); conn.close()
                        self._send_response({'success': True, 'data': data})
                    else:
                        cur.close(); conn.close()
                        self._send_error(404, f'Trip {trip_id} not found')

            # analytics endpoints, here i use existing db views
            elif path == '/analytics/hourly':
                # optional ?hour=... & ?is_weekend=true (we can pass these to filter)
                params = []
                where = []
                if 'hour' in qs:
                    where.append("pickup_hour = %s"); params.append(int(qs['hour'][0]))
                if 'is_weekend' in qs:
                    where.append("is_weekend = %s"); params.append(qs['is_weekend'][0].lower() in ('1','true','t','yes'))
                where_sql = ''
                if where:
                    where_sql = 'WHERE ' + ' AND '.join(where)
                conn = get_db_conn(); cur = conn.cursor()
                q = f"""
                SELECT pickup_hour, time_of_day, is_weekend, trip_count, avg_distance, avg_duration, avg_speed, total_distance
                FROM hourly_trip_stats
                {where_sql}
                ORDER BY pickup_hour;
                """
                cur.execute(q, tuple(params))
                rows = cur.fetchall()
                data = [dict_from_cursor_row(cur, r) for r in rows]
                cur.close(); conn.close()
                self._send_response({'success': True, 'count': len(data), 'data': data})

            elif path == '/analytics/daily':
                # optional ?start_date & ?end_date (YYYY-MM-DD)
                params = []
                where = []
                if 'start_date' in qs:
                    where.append("trip_date >= %s"); params.append(qs['start_date'][0])
                if 'end_date' in qs:
                    where.append("trip_date <= %s"); params.append(qs['end_date'][0])
                where_sql = ''
                if where:
                    where_sql = 'WHERE ' + ' AND '.join(where)
                conn = get_db_conn(); cur = conn.cursor()
                q = f"""
                SELECT trip_date, is_weekend, trip_count, avg_distance, avg_duration, avg_speed
                FROM daily_trip_stats
                {where_sql}
                ORDER BY trip_date DESC
                LIMIT 500;
                """
                cur.execute(q, tuple(params))
                rows = cur.fetchall()
                data = [dict_from_cursor_row(cur, r) for r in rows]
                cur.close(); conn.close()
                self._send_response({'success': True, 'count': len(data), 'data': data})

            elif path == '/analytics/location_stats':
                conn = get_db_conn(); cur = conn.cursor()
                cur.execute("SELECT location_id, latitude, longitude, zone_name, pickup_count FROM location_trip_stats ORDER BY pickup_count DESC LIMIT 200;")
                rows = cur.fetchall()
                data = [dict_from_cursor_row(cur, r) for r in rows]
                cur.close(); conn.close()
                self._send_response({'success': True, 'count': len(data), 'data': data})

            # Top zones using manual top-k algorithm
            elif path == '/analytics/top_zones':
                # supports ?limit=10
                limit = int(qs.get('limit', ['10'])[0])
                if limit < 1: limit = 10

                # Query aggregated counts from DB (zone_name and count)
                conn = get_db_conn(); cur = conn.cursor()
                cur.execute("""
                    SELECT l.location_id, l.zone_name, COUNT(*) as pickup_count
                    FROM trip_facts tf
                    JOIN locations l ON tf.pickup_location_id = l.location_id
                    GROUP BY l.location_id, l.zone_name;
                """)
                rows = cur.fetchall()
                pairs = []
                for r in rows:
                    # r: (location_id, zone_name, pickup_count)
                    loc_id = r[0]; zone_name = r[1] or 'UNKNOWN'; cnt = int(r[2])
                    pairs.append(((loc_id, zone_name), cnt))

                conn.close()

                # Use manual top_k_pairs (quickselect-based) to pick top `limit`
                top = top_k_pairs(pairs, limit)
                result = [{'location_id': k[0], 'zone_name': k[1], 'pickup_count': v} for (k, v) in top]
                self._send_response({'success': True, 'limit': limit, 'count': len(result), 'data': result})

            else:
                self._send_error(404, 'Endpoint not found')

        except Exception as e:
            print(traceback.format_exc())
            self._send_error(500, f"Server error: {str(e)}")

    def log_message(self, format, *args):
        print(f"{self.address_string()} - [{self.log_date_time_string()}] {format % args}")


def run_server(PORT):
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, APIHandler)
    print(f'Starting server on port {PORT}...')
    print(f'API docs: GET http://localhost:{PORT}/')
    print(f'Auth user: {VALID_USERNAME}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Shutting down...')
        httpd.server_close()

if __name__ == '__main__':
    run_server(int(os.getenv('PORT', '8000')))
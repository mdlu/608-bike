import sqlite3
import datetime
import time
import json

################################################################################
### LOGGING FUNCTIONS
req_log = '__HOME__/api/bike.log' # For server use.
# req_log = 'bike.log' # For local use.

def logging(s):
    with open(req_log, "a") as myfile:
        myfile.write(str(datetime.datetime.now()))
        myfile.write('\n')
        myfile.write(s)
        myfile.write('\n')

def logging_read():
    file = open(req_log, "r")
    return(file.read().replace('\n', '<br>'))

### END OF LOGGING FUNCTIONS
################################################################################

################################################################################
### DATABASE FUNCTIONS
bike_db = '__HOME__/api/bike.db' # For server use.
# bike_db = 'bike.db' # For local use.

def create_database():
    """Create the bike database `bike_data`. Do nothing if it exists."""
    conn = sqlite3.connect(bike_db)  # connect to that database (will create if it doesn't already exist)
    c = conn.cursor()  # make cursor into database (allows us to execute commands)

    # https://stackoverflow.com/questions/20674282/how-to-automatically-generate-unique-id-in-sql-like-uid12345678
    c.execute('''CREATE TABLE IF NOT EXISTS bike_data
    (user text, route text,
    route_id INTEGER PRIMARY KEY, path_id int,
    start timestamp, end timestamp);''') # run a CREATE TABLE command

    conn.commit() # commit commands
    conn.close() # close connection to database

def insert_into_database(user, route, path_id, start, end):
    """Insert a route data collection.

    `user` is the username of the route person. (string)
    `route` is the serialized route data. (string)
    `path_id` is the calculated path id. (int)
    `start` is the timestamp of route start.
    `end` is the timestamp of route end.
    """
    conn = sqlite3.connect(bike_db)
    c = conn.cursor()

    full_start = datetime.datetime.combine(datetime.datetime.today().date(), start.time())
    full_end = datetime.datetime.combine(datetime.datetime.today().date(), end.time())

    c.execute('''INSERT INTO bike_data (user, route, path_id, start, end)
    VALUES (?,?,?,?,?);''', (user, route, path_id, full_start, full_end))
    c.execute("SELECT last_insert_rowid()")
    route_id = c.fetchone() #Commenting these lines such that a POST request response is only what will end up printed to the ESP
    conn.commit()
    conn.close()

# def delete_vals():
#     conn = sqlite3.connect(bike_db)
#     c = conn.cursor()

#     # full_start = datetime.datetime.combine(datetime.date.today(), datetime.datetime.strptime(start, '%H:%M:%S'))
#     # full_end = datetime.datetime.combine(datetime.date.today(), datetime.datetime.strptime(end, '%H:%M:%S'))

#     # c.execute('''INSERT INTO bike_data (user, route, path_id, start, end)
#     # VALUES (?,?,?,?,?);''', (user, route, path_id, full_start, full_end))
#     # c.execute("SELECT last_insert_rowid()")
#     # route_id = c.fetchone() #Commenting these lines such that a POST request response is only what will end up printed to the ESP
    
#     c.execute("DELETE FROM bike_data WHERE route_id = 26")
#     conn.commit()
#     conn.close()

def trial():
    """Insert a new path route data collection.

    `user` is the username of the route person. (string)
    `route` is the serialized route data. (string)
    `start` is the timestamp of route start.
    `end` is the timestamp of route end.
    """
    conn = sqlite3.connect(bike_db)
    c = conn.cursor()
    c.execute('''UPDATE bike_data SET path_id = 0 WHERE path_id = 22''')
    conn.commit()
    conn.close()

def remove_route_id(route_id):
    """Remove a route.

    `route_id` is the desired route id. (int)
    """
    conn = sqlite3.connect(bike_db)
    c = conn.cursor()
    c.execute('''DELETE FROM bike_data WHERE route_id = ?''', (route_id, ))
    conn.commit()
    conn.close()

def insert_new_path_into_database(user, route, start, end):
    """Insert a new path route data collection.

    `user` is the username of the route person. (string)
    `route` is the serialized route data. (string)
    `start` is the timestamp of route start.
    `end` is the timestamp of route end.
    """
    conn = sqlite3.connect(bike_db)
    c = conn.cursor()
    c.execute('''INSERT INTO bike_data (user, route, path_id, start, end)
    VALUES (?,?,?,?,?);''', (user, route, 0, start, end))
    c.execute("SELECT last_insert_rowid()")
    route_id = c.fetchone()[0]
    c.execute('''UPDATE bike_data SET path_id = ? WHERE route_id = ?''', (route_id, route_id))
    conn.commit()
    conn.close()

def lookup_leaderboard(path_id):
    """Generate leaderboard from path id. Returns a web-formatted list.

    `path_id` is the desired path id. (int)
    """
    conn = sqlite3.connect(bike_db)
    c = conn.cursor()
    response = c.execute('''SELECT user, start, end FROM bike_data WHERE path_id = ?''',(path_id,)).fetchall()
    route_response = c.execute('''SELECT route FROM bike_data WHERE path_id = ? ORDER BY route_id DESC''',(path_id,)).fetchone() # gets the route coordinates from the original poster
    conn.commit()
    conn.close()

    diff = [(user, deserialize('datetime', end) - deserialize('datetime', start), start.split()[0]) for (user, start, end) in response]
    diff.sort(key = lambda x: x[1])
    diff = diff[:10] # takes top 10 for the leaderboard
    list_html = "".join([r'''<li>{}, {}, {}</li>'''.format(user, timediff, date) for user, timediff, date in diff])
    if len(list_html) == 0:
        list_html = "no routes yet recorded for this path ID"

    # top_text = '''<br><a href="./bike_server.py">Back to homepage</a><br><br>Leaderboard for Path ID {}:<br><ol>{}</ol>'''.format(path_id, list_html)
    top_text = '''<br><a href="./bike_server.py">Back to homepage</a><br><br>Leaderboard for <a href="./bike_server.py?path_id={}&leaderboard=">Path ID {}:</a><br><ol>{}</ol>'''.format(path_id, path_id, list_html)
    # return top_text
    return webify_display_map(path_id, top_text, route_response[0])

def get_route(route_id):
    """Return the path of GPS coordinates corresponding to a particular route id.
    Also returns the best time to beat, along with a Google Maps display of the route.
    """
    conn = sqlite3.connect(bike_db)
    c = conn.cursor()
    # ordering by end time below ensures that all users who look up a route by r_id will get the route posted by the original poster
    route_response = c.execute('''SELECT route, path_id FROM bike_data WHERE route_id = ?''',(route_id,)).fetchone()

    if route_response is None:
        conn.commit()
        conn.close()
        return "<br>invalid route ID"

    path_response = c.execute('''SELECT user, start, end FROM bike_data WHERE path_id = ? ORDER BY route_id DESC''',(route_response[1],)).fetchall()
    conn.commit()
    conn.close()

    diff = [(user, deserialize('datetime', end) - deserialize('datetime', start)) for (user, start, end) in path_response]
    diff.sort(key = lambda x: x[1])

    top_text = r"""
    <br><a href="./bike_server.py">Back to homepage</a><br><br>
    <div id="route_nav_form">
        <form method="get" action="" style="display:inline-block">
            <input type="hidden" name="route_id" value="{}">
            <input type="hidden" name="get_route" value="">
            <button type="submit">Previous route</button>
        </form>
        <form method="get" action="" style="display:inline-block">
            <input type="hidden" name="route_id" value="{}">
            <input type="hidden" name="get_route" value="">
            <button type="submit">Next route</button>
        </form>
    </div>
    <a href="javascript:void(0);" onclick="toggle_visibility('route_data');"> Your route's coordinates: </a>
    <br><div id="route_data" style="display: none">{}</div><br>
    <script type="text/javascript">
        function toggle_visibility(id) {{
            var e = document.getElementById(id);
            if(e.style.display == 'block')
                e.style.display = 'none';
            else
                e.style.display = 'block';
        }}
    </script>
    Time to beat:<br>{}, {}<br>
    """.format(int(route_id)-1, int(route_id)+1, route_response[0], diff[0][0], diff[0][1])
    # return top_text
    return webify_display_map(route_id, top_text, route_response[0])

def get_paths():
    """Select all path candidates. Return as list.
    """
    conn = sqlite3.connect(bike_db)
    c = conn.cursor()
    response = c.execute("SELECT route, path_id FROM bike_data WHERE path_id = route_id").fetchall()
    conn.commit()
    conn.close()

    return response

def user_routes(user):
    """Generate all user routes. Returns a web-formatted list.

    `user` is the desired user. (string)
    """
    conn = sqlite3.connect(bike_db)
    c = conn.cursor()
    response = c.execute('''SELECT route_id, path_id, start, end FROM bike_data WHERE user = ?''',(user,)).fetchall()
    conn.commit()
    conn.close()

    if len(response) == 0:
        body = "no routes yet recorded for this user"
    else:
        route_heading = [['Route id', 'Path id', 'Time', 'Date']]
        diff = [[route_id, path_id, str(deserialize('datetime', end) - deserialize('datetime', start)), start.split()[0]] for (route_id, path_id, start, end) in response]
        diff.sort(key = lambda x: x[0])

        body = '''<br><a href="./bike_server.py">Back to homepage</a><br><br><br>{}'s routes:<br>{}'''.format(user, webify_data(route_heading + diff, route_column=0))

    return body

def force_recalculate():
    """Forcefully recalculates path ids of all routes, iterating through in route id order.
    """
    conn = sqlite3.connect(bike_db)
    c = conn.cursor()
    response = c.execute("SELECT route, route_id FROM bike_data ORDER BY route_id DESC").fetchall()
    # Retrieve username, route data, start and end timing.
    for (route, route_id) in response:
        path_id = path_from_route(json.loads(route), void_paths=list(range(route_id, len(response)))) # Ignore self in path correlation
        if path_id is None:
            c.execute('''UPDATE bike_data SET path_id = route_id WHERE route_id = ?''', (route_id,))
        else:
            c.execute('''UPDATE bike_data SET path_id = ? WHERE route_id = ?''', (path_id, route_id,))
    conn.commit()
    conn.close()

def get_all_data(web = True):
    """Dump all data in bike database."""
    conn = sqlite3.connect(bike_db)
    c = conn.cursor()
    c.execute("SELECT * FROM bike_data")
    response = c.fetchall()
    conn.commit()
    conn.close()

    dump = [list(row) for row in response]
    # https://stackoverflow.com/questions/15164655/generate-html-table-from-2d-javascript-array
    if web:
        print(webify_data(dump))
    else:
        # print(dump)
        print('\n'.join([''.join(['{:4}'.format(item) for item in row])
      for row in dump]))

def show_all_paths():
    conn = sqlite3.connect(bike_db)
    c = conn.cursor()
    response = c.execute("SELECT DISTINCT path_id FROM bike_data").fetchall()
    conn.commit()
    conn.close()

    display = "<a href='./bike_server.py'>RETURN TO HOMEPAGE</a><br><br>"
    for r in response:
        display += '''
    <iframe id="inlineFrameExample"
    title="Inline Frame Example"
    width="40%"
    height="600"
    src="./bike_server.py?path_id={}&leaderboard=">
    </iframe>
    <a href="./bike_server.py?path_id={}&leaderboard="><===</a>
    '''.format(r[0],r[0])

    return display

    # print(response)

    # many_maps = ""
    # for n in range(len(response)):
    #     many_maps += '''    <div id="map{}"></div>
    #     '''.format(n)
    #     break

    # display_string = """
    # <!DOCTYPE html>
    # <html>
    #     <head>
    #         <meta name="viewport" content="initial-scale=1.0, user-scalable=no">
    #         <meta charset="utf-8">
    #         <title>Route/Path</title>
    #         <style>
    #             /* Always set the map height explicitly to define the size of the div
    #             * element that contains the map. */
    #             #map {{
    #                 height: 100%;
    #             }}
    #             /* Optional: Makes the sample page fill the window. */
    #             html, body {{
    #                 height: 100%;
    #                 margin: 10;
    #                 padding: 10;
    #             }}
    #         </style>
    #     </head>
    #     <body>
    #     {}
    #         <script>
    #             function initMap() {{
    #                 var image1 = {{
    #                     url: 'https://github.mit.edu/mdlu/608-bike/blob/master/images/bike_vector_original.png?raw=true',
    #                     anchor: new google.maps.Point(24, 35)
    #                 }};

    #                 var image2 = {{
    #                     url: 'https://github.mit.edu/mdlu/608-bike/blob/master/images/finish_flag-512.png?raw=true',
    #                     anchor: new google.maps.Point(19, 50)
    #                 }};

    #                 """.format(many_maps)

    # for num, route in enumerate(response):
    #     new_map = map_only(num, route[0])
    #     display_string += new_map
    #     break

    # end = """
    #             }
    #         </script>
    #         <script async defer
    #             src="https://maps.googleapis.com/maps/api/js?key=AIzaSyBLz3ccOrLWv-xD20JWqRdyb_nkoT3x2Yk&callback=initMap">
    #         </script>
    #     </body>
    # </html>"""
    # display_string += end
    # return display_string


### END OF DATABASE FUNCTIONS
################################################################################

def deserialize(obj, string):
    if obj == 'datetime':
        formats = [
            r"%Y-%m-%d %H:%M:%S.%f",
            r"%d%m%Y %H%M%S.%f",
            r"%Y-%m-%d %H:%M:%S",
            r"%Y-%m-%dT%H:%M",
            r"%H%M%S.%f"
        ]
        for f in formats:
            try:
                return datetime.datetime.strptime(string, f)
            except:
                pass
        # Fail, pass default time
        return datetime.datetime.now()

def webify_data(dump, route_column=None):
    if route_column is None:
        return r'''
            <script>
            function createTable(tableData) {{
                var table = document.createElement('table');
                var tableBody = document.createElement('tbody');

                tableData.forEach(function(rowData) {{
                    var row = document.createElement('tr');

                    rowData.forEach(function(cellData) {{
                        var cell = document.createElement('td');
                        cell.appendChild(document.createTextNode(cellData));
                        row.appendChild(cell);
                    }});

                    tableBody.appendChild(row);
                }});

                table.appendChild(tableBody);
                document.body.appendChild(table);
            }}
            createTable({})
            </script>
            '''.format(str(dump))
    else:
        return r'''
            <script>
            function createTable(tableData) {{
                var table = document.createElement('table');
                var tableBody = document.createElement('tbody');
                var row_idx = 0;

                tableData.forEach(function(rowData) {{
                    var row = document.createElement('tr');
                    var col_idx = 0;

                    rowData.forEach(function(cellData) {{
                        if(row_idx > 0 && col_idx == {}) {{
                            var cell = document.createElement('a');
                            var href = document.createAttribute('href');
                            href.value = `bike_server.py?route_id=${{cellData}}&get_route=`;
                            cell.setAttributeNode(href)
                        }} else {{
                            var cell = document.createElement('td');
                        }}
                        cell.appendChild(document.createTextNode(cellData));
                        row.appendChild(cell);
                        col_idx++;
                    }});

                    tableBody.appendChild(row);
                    row_idx++;
                }});

                table.appendChild(tableBody);
                document.body.appendChild(table);
            }}
            createTable({})
            </script>
            '''.format(route_column, str(dump))

# def map_only(num, route):

#     json_response = json.loads(route)
#     coords = ["{{lat: {}, lng: {}}}".format(r[0], r[1]) for r in json_response]
#     coord_string = ", ".join(coords) # parses coordinates in a way that works with Google Maps

#     return r"""
#                     var map{} = new google.maps.Map(document.getElementById('map{}'), {{
#                     zoom: 15,
#                     center: {{lat: 0, lng: 0}},
#                     mapTypeId: 'terrain'
#                     }});

#                     bounds{} = new google.maps.LatLngBounds();
#                     var flightPlanCoordinates{} = [
#                     {}
#                     ];
#                     var flightPath{} = new google.maps.Polyline({{
#                     path: flightPlanCoordinates{},
#                     geodesic: true,
#                     strokeColor: '#FF0000',
#                     strokeOpacity: 1.0,
#                     strokeWeight: 2
#                     }});

#                     var marker1{} = new google.maps.Marker({{position: {}, map: map{}, icon: image1}});
#                     loc = new google.maps.LatLng(marker1{}.position.lat(), marker1{}.position.lng());
#                     bounds{}.extend(loc);
#                     var marker2{} = new google.maps.Marker({{position: {}, map: map{}, icon: image2}});
#                     loc = new google.maps.LatLng(marker2{}.position.lat(), marker2{}.position.lng());
#                     bounds{}.extend(loc);
#                     flightPath{}.setMap(map{});
#                     map{}.fitBounds(bounds{});
#                     map{}.panToBounds(bounds{});

#             """.format(num, num, num, num, coord_string, num, num, num, coords[0], num, num, num, num, num, coords[-1], num, num, num, num, num, num, num, num, num, num)


def webify_display_map(route_id, top_text, path):
    """Returns the HTML for displaying the appropriate Google Map.
    top_text is the text to be displayed on top of the map."""

    # # finds center location for map displayed
    # center_lat = sum([float(r[0]) for r in json_response]) / len(json_response)
    # center_lng = sum([float(r[1]) for r in json_response]) / len(json_response)

    json_response = json.loads(path)
    coords = ["{{lat: {}, lng: {}}}".format(r[0], r[1]) for r in json_response]
    coord_string = ", ".join(coords) # parses coordinates in a way that works with Google Maps

    return r"""
    <!DOCTYPE html>
    <html>
        <head>
            <meta name="viewport" content="initial-scale=1.0, user-scalable=no">
            <meta charset="utf-8">
            <title>Route/Path {}</title>
            <style>
                /* Always set the map height explicitly to define the size of the div
                * element that contains the map. */
                #map {{
                    height: 100%;
                }}
                /* Optional: Makes the sample page fill the window. */
                html, body {{
                    height: 100%;
                    margin: 10;
                    padding: 10;
                }}
            </style>
        </head>
        <body>
            <div id="toptext">{}</div>
            <div id="map"></div>
            <script>
                function initMap() {{
                    var map = new google.maps.Map(document.getElementById('map'), {{
                    zoom: 15,
                    center: {{lat: 0, lng: 0}},
                    mapTypeId: 'terrain'
                    }});

                    bounds = new google.maps.LatLngBounds();

                    var flightPlanCoordinates = [
                    {}
                    ];
                    var flightPath = new google.maps.Polyline({{
                    path: flightPlanCoordinates,
                    geodesic: true,
                    strokeColor: '#FF0000',
                    strokeOpacity: 1.0,
                    strokeWeight: 2
                    }});

                    var image1 = {{
                        url: 'https://github.mit.edu/mdlu/608-bike/blob/master/images/bike_vector_original.png?raw=true',
                        anchor: new google.maps.Point(24, 35)
                    }};

                    var image2 = {{
                        url: 'https://github.mit.edu/mdlu/608-bike/blob/master/images/finish_flag-512.png?raw=true',
                        anchor: new google.maps.Point(19, 50)
                    }};
                    var marker1 = new google.maps.Marker({{position: {}, map: map, icon: image1}});
                    loc = new google.maps.LatLng(marker1.position.lat(), marker1.position.lng());
                    bounds.extend(loc);
                    var marker2 = new google.maps.Marker({{position: {}, map: map, icon: image2}});
                    loc = new google.maps.LatLng(marker2.position.lat(), marker2.position.lng());
                    bounds.extend(loc);

                    flightPath.setMap(map);
                    map.fitBounds(bounds);
                    map.panToBounds(bounds);
                }}
            </script>
            <script async defer
                src="https://maps.googleapis.com/maps/api/js?key=AIzaSyBLz3ccOrLWv-xD20JWqRdyb_nkoT3x2Yk&callback=initMap">
            </script>
        </body>
    </html>
    """.format(route_id, top_text, coord_string, coords[0], coords[-1])

def home_page():
    return r'''
    <h1>Welcome to 608-bike!</h1>
    <form action="" method="get">
        Enter your username:<br>
        <input type="text" name="user"><br>
        <input type="submit" value="Submit">
    </form>
    Alternatively...
    <form action="" method="get">
        Enter the route id:<br>
        <input type="number" name="route_id"><br>
        <input type="hidden" name="get_route" value="">
        <input type="submit" value="Submit">
    </form>
    <form action="" method="get">
        Enter the path id:<br>
        <input type="number" name="path_id"><br>
        <input type="hidden" name="leaderboard" value="">
        <input type="submit" value="Submit">
    </form>
    <form action="" method="get">
        View debugging info:<br>
        <input type="hidden" name="debug" value="">
        <input type="submit" value="Go">
    </form>
    <br><a href="./bike_server.py?show_all=">Browse all paths</a><br>
    '''

def debug_console():
    return r'''
    <hr>
    <h2>Debug console</h2>
    <form action="" method="post" id="debug_form">
        Username:<br>
        <input type="text" name="user"><br>
        Route:<br>
        <input type="text" name="route" value="[[1,2],[3,4]]"><br>
        Path ID:<br>
        <input type="number" name="path_id" value="0"><br>
        Start:<br>
        <input type="datetime-local" name="start"><br>
        End:<br>
        <input type="datetime-local" name="end"><br><br>

        <input type="submit" value="Submit">
    </form>

    <form action="" method="post" id="force_form">
        View request logs:<br>
        <input type="hidden" name="view_log" value=""><br>

        <input type="submit" value="Submit">
    </form>

    <br />

    <h2>Force recalculate. YOU CANNOT UNDO THIS ACTION.</h2>
    <form action="" method="post" id="force_form">
        Execute?:<br>
        <input type="text" name="force"><br>
        <input type="hidden" name="force_recalculate" value=""><br>

        <input type="submit" value="Submit">
    </form>
    <hr>
    '''

################################################################################
### BEGIN PATH CALCULATION FUNCTIONS

def path_from_route(new_route, void_paths=None):
    best = {'delta': float('inf'), 'path_id': 0}
    for (route_string, path_id) in get_paths():
        route = json.loads(route_string)
        delta = compare(new_route, route)
        if delta < best['delta'] and (void_paths is None or path_id not in void_paths):
            best['delta'], best['path_id'] = delta, path_id
        # print(delta, route, path_id)
    # print(best['delta'])
    if best['delta'] < 1e-5:
        return best['path_id']
    return None

def distance(a, b):
    """Returns the Euclidian distance between the two tuple coordinates."""
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

def distance_list(route):
    """Generate a list of consecutive distances within route, and sum of these distances. Returns as tuple.

    `route` is the route of interest. (array of float pairs)
    """
    distances = list()
    total = 0
    for i in range(len(route) - 1):
        dist = distance(route[i], route[i + 1])
        distances.append(dist)
        total += dist
    return distances, total

def norm_route(route, precision = 10):
    """Generate an array of float pairs along the route, such that these points are equidistant. Returns as array of tuples.

    `route` is the route of interest. (array of float pairs)
    `precision` is the number of float pairs to return, e.g. precision of 3 cooresponds to 2 endpoints plus midpoint, generalize, etc.
    """
    distances, total = distance_list(route)
    norm = list()
    point = {'loc': route[0], 'dist': 0, 'route_dist': 0, 'norm_ix': 0, 'route_ix': 0}
    while point['norm_ix'] < precision:
        target = point['norm_ix']*total / (precision - 1)
        while point['dist'] < target:
            if point['route_dist'] + distances[point['route_ix']] < target:
                point['route_dist'] += distances[point['route_ix']]
                point['dist'] = point['route_dist']
                point['route_ix'] += 1
                point['loc'] = route[point['route_ix']]
            else:
                between = target - point['dist']
                point['dist'] = target
                point['loc'] = midpoint(point['loc'], route[point['route_ix']], route[point['route_ix'] + 1], between, distances[point['route_ix']])

        norm.append(point['loc'])

        point['norm_ix'] += 1

    return norm

def midpoint(s, a, b, d, t):
    """Returns the point a distance d between tuples {s, a} if {a, b} are t apart."""
    return [s[0] + (b[0] - a[0])*d/t, s[1] + (b[1] - a[1])*d/t]

def compare(a, b):
    """Returns the difference between two routes.

    `a, b` are the two routes to compare
    """
    a_norm, b_norm = norm_route(a), norm_route(b)
    delta = 0
    for p, q in zip(a_norm, b_norm):
        delta += distance(p, q)**2
    return delta

### END PATH CALCULATION FUNCTIONS
################################################################################

def request_handler(req):
    if req['method'] == 'POST':
        create_database()

        if 'force_recalculate' in req['form']:
            if req['form']['force'] == 'YES':
                force_recalculate()
                return "Recalculated."
            else:
                return "Aborted. Type YES to confirm force."

        if 'view_log' in req['form']:
            return logging_read()

        logging(str(req))
        try:
            # Retrieve username, route data, start and end timing.
            user = req['form']['user']
            route = req['form']['route']
            start = deserialize('datetime', req['form']['start'])
            end = deserialize('datetime', req['form']['end'])
            path_id = path_from_route(json.loads(route))
            if 'path_id' in req['form']: # Override path-finding algorithm
                path_id = req['form']['path_id']
                insert_into_database(user, route, path_id, start, end)
                return "You successfully uploaded a route to path {}!".format(path_id)
            else: # Default use path finding
                if path_id is None:
                    insert_new_path_into_database(user, route, start, end)
                    return "New path successfully uploaded."
                else:
                    insert_into_database(user, route, path_id, start, end)
                    return "You successfully uploaded a route to path {}!".format(path_id)
            # get_all_data()
            # print('<br>')
        except:
            return "Could not handle request {}".format(str(req))

    if req['method'] == 'GET':
        if 'debug' in req['args']:
            print('<br>')
            create_database()
            get_all_data()
            print('<br>')
            print(debug_console())
        if 'show_all' in req['args']:
            return show_all_paths()
        if 'user' in req['args']:
            user = req['values']['user']
            return user_routes(user) # returns the list of GPS coordinates for a particular r_id
        if 'route_id' in req['args']:
            route_id = req['values']['route_id']
            if 'get_route' in req['args']:
                return get_route(route_id) # returns the list of GPS coordinates for a particular r_id
        if 'path_id' in req['args']:
            path_id = req['values']['path_id']
            if 'leaderboard' in req['args']:
                return lookup_leaderboard(path_id) # returns the current top-10 leaderboard for a particular r_id
        return home_page()

    return "Your request is not allowed. {}".format(str(req))

def test_suite(k):
    routes = [
        [[42.35598,-71.09812],[42.35599,-71.09814],[42.35599,-71.09813],[42.35599,-71.09813]],
        [[42.35925,-71.09601],[42.35925,-71.09609],[42.35928,-71.09606],[42.35929,-71.09607],[42.35925,-71.09615],[42.35926,-71.09614],[42.35927,-71.09612],[42.35929,-71.0961],[42.35933,-71.09605],[42.35936,-71.09601],[42.3594,-71.09595],[42.35941,-71.09594],[42.35941,-71.09593],[42.35941,-71.09593],[42.35945,-71.0959],[42.35943,-71.09591],[42.35943,-71.09592],[42.35945,-71.09594],[42.35949,-71.09585],[42.35955,-71.09575],[42.35971,-71.09551],[42.35987,-71.09531],[42.35987,-71.09531],[42.35987,-71.09531],[42.35987,-71.09531],[42.35987,-71.09531],[42.35987,-71.09531],[42.35987,-71.09531],[42.35987,-71.09531],[42.35987,-71.09531],[42.35987,-71.09531],[42.35886,-71.09744],[42.35877,-71.0976],[42.35868,-71.09775],[42.3586,-71.09789],[42.35853,-71.09806],[42.35845,-71.09821],[42.35839,-71.09835],[42.35832,-71.09849],[42.35824,-71.09865],[42.35816,-71.0988],[42.35811,-71.09893],[42.35811,-71.09907],[42.35803,-71.09915],[42.35795,-71.09927],[42.35786,-71.0994],[42.35779,-71.09953],[42.35772,-71.09967],[42.35765,-71.09982],[42.3576,-71.09995],[42.35754,-71.1001],[42.35752,-71.10014],[42.35752,-71.10018],[42.35752,-71.1002],[42.35748,-71.10033],[42.35744,-71.10041],[42.35735,-71.10059],[42.35723,-71.10069],[42.35714,-71.1008],[42.35705,-71.10091],[42.35697,-71.10107],[42.35688,-71.10123],[42.35681,-71.10141],[42.35674,-71.10157],[42.35665,-71.1017],[42.35665,-71.1017],[42.35653,-71.10197],[42.35653,-71.10197],[42.35653,-71.10197],[42.35653,-71.10197],[42.35653,-71.10197],[42.35616,-71.10271],[42.35609,-71.10285],[42.35603,-71.10299],[42.35596,-71.10311],[42.35589,-71.10322],[42.35587,-71.10326],[42.35589,-71.10325],[42.3559,-71.10325],[42.35591,-71.10326],[42.35591,-71.10326],[42.35592,-71.10326],[42.35593,-71.10325],[42.35594,-71.10329],[42.35598,-71.10329],[42.35598,-71.10329]],
        [[42.356,-71.10332],[42.356,-71.10332],[42.35601,-71.10334],[42.356,-71.10337],[42.356,-71.10339],[42.35599,-71.1034],[42.35598,-71.10341],[42.35598,-71.10342],[42.35598,-71.10341],[42.35597,-71.10343],[42.35595,-71.10339],[42.35596,-71.10325],[42.35602,-71.10311],[42.3561,-71.10296],[42.35618,-71.1028],[42.35626,-71.10262],[42.35635,-71.10244],[42.35646,-71.10225],[42.35656,-71.10204],[42.35666,-71.10184],[42.35676,-71.10163],[42.35686,-71.10143],[42.35697,-71.1012],[42.35708,-71.10098],[42.35719,-71.10075],[42.3573,-71.10053],[42.35741,-71.1003],[42.35753,-71.10004],[42.35766,-71.09976],[42.3578,-71.09949],[42.35793,-71.09923],[42.35806,-71.09897],[42.35817,-71.09873],[42.35828,-71.09852],[42.35839,-71.09829],[42.35847,-71.09814],[42.35847,-71.09814],[42.35847,-71.09814],[42.35847,-71.09814],[42.35847,-71.09814],[42.35847,-71.09814],[42.35847,-71.09814],[42.359,-71.09707],[42.35909,-71.0969],[42.35917,-71.09674],[42.35925,-71.09657],[42.35932,-71.09642],[42.35939,-71.09628],[42.35943,-71.09619],[42.35945,-71.09614],[42.35946,-71.09611],[42.35949,-71.09606],[42.35952,-71.09599],[42.35954,-71.09593],[42.35956,-71.09589],[42.35957,-71.09583],[42.35956,-71.09578],[42.35953,-71.09579],[42.35953,-71.09578],[42.35952,-71.09577],[42.35948,-71.09577],[42.35947,-71.09579],[42.35947,-71.09581],[42.35949,-71.09576],[42.35951,-71.09566]],
        list(reversed([[42.356,-71.10332],[42.356,-71.10332],[42.35601,-71.10334],[42.356,-71.10337],[42.356,-71.10339],[42.35599,-71.1034],[42.35598,-71.10341],[42.35598,-71.10342],[42.35598,-71.10341],[42.35597,-71.10343],[42.35595,-71.10339],[42.35596,-71.10325],[42.35602,-71.10311],[42.3561,-71.10296],[42.35618,-71.1028],[42.35626,-71.10262],[42.35635,-71.10244],[42.35646,-71.10225],[42.35656,-71.10204],[42.35666,-71.10184],[42.35676,-71.10163],[42.35686,-71.10143],[42.35697,-71.1012],[42.35708,-71.10098],[42.35719,-71.10075],[42.3573,-71.10053],[42.35741,-71.1003],[42.35753,-71.10004],[42.35766,-71.09976],[42.3578,-71.09949],[42.35793,-71.09923],[42.35806,-71.09897],[42.35817,-71.09873],[42.35828,-71.09852],[42.35839,-71.09829],[42.35847,-71.09814],[42.35847,-71.09814],[42.35847,-71.09814],[42.35847,-71.09814],[42.35847,-71.09814],[42.35847,-71.09814],[42.35847,-71.09814],[42.359,-71.09707],[42.35909,-71.0969],[42.35917,-71.09674],[42.35925,-71.09657],[42.35932,-71.09642],[42.35939,-71.09628],[42.35943,-71.09619],[42.35945,-71.09614],[42.35946,-71.09611],[42.35949,-71.09606],[42.35952,-71.09599],[42.35954,-71.09593],[42.35956,-71.09589],[42.35957,-71.09583],[42.35956,-71.09578],[42.35953,-71.09579],[42.35953,-71.09578],[42.35952,-71.09577],[42.35948,-71.09577],[42.35947,-71.09579],[42.35947,-71.09581],[42.35949,-71.09576],[42.35951,-71.09566]]))
    ]
    create_database()
    insert_new_path_into_database('a', json.dumps(routes[k]), datetime.datetime.now(), datetime.datetime.now())
    for i in range(len(routes)):
        print(i, path_from_route(routes[i]))


if __name__ == '__main__':
    pass

    # trial() # Clears some data. Leave commented.

    # test_suite(1)
    # print(datetime.date.today())
    # start = "03:11:00.345"
    # end = "03:11:15.567"
    # # # full_start = datetime.datetime.combine(datetime.date.today(), time.strptime(start, '%H:%M:%S'))
    # # # full_end = datetime.datetime.combine(datetime.date.today(), time.strptime(end, '%H:%M:%S'))
    # # full_start = datetime.datetime.combine(datetime.datetime.today().date(), datetime.datetime.strptime(start, '%H:%M:%S.%f').time())
    # # full_end = datetime.datetime.combine(datetime.datetime.today().date(), datetime.datetime.strptime(end, '%H:%M:%S.%f').time())

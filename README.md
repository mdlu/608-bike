# 608-bike
This is a bike-path tracker/timer project for MIT's 6.08 class.

Christian Scarlett (`cjscar`), Griffin Duffy (`gduffy`), Mindren Lu (`mdlu`), Richard Liu (`rtliu`)

# API Documentation

## Post Route Data to Server

`POST http://608dev.net/sandbox/sc/rtliu/api/bike_server.py`

### Body Parameters
| REQUEST BODY DATA | VALUE TYPE        | VALUE                             |
| ----------------- | ----------------- | --------------------------------- |
| user              | string            | The username of the route person. |
| route             | array of GPS data | A JSON array of the route data. For example: `[[13,24,23,12],[123,2,787,2]]` |
| path_id           | integer           | *Optional.* The path id to override pathfinding. |
| start             | timestamp         | The timestamp of route start formatted as `%H%M%S.%f` |
| end               | timestamp         | The timestamp of route end formatted as `%H%M%S.%f` |

## Get All Route Data

`GET http://608dev.net/sandbox/sc/rtliu/api/bike_server.py`

### Query Parameters
| QUERY PARAMETER | VALUE TYPE        | VALUE                             |
| --------------- | ----------------- | --------------------------------- |
| user           | string            | *Optional.* The username to filter results. |
| path_id        | integer           | *Optional.* The shared path id to filter results. |
| route_id       | integer           | *Optional.* The specific route id, to be used with get_route. |
| get_route      |                   | *Optional.* Also specify a route_id to obtain its coordinates and Google Map render. |
| leaderboard    |                   | *Optional.* Also specify a path_id to view its leaderboard and Google Map render. |
| show_all       |                   | *Optional.* Will display all currently uploaded, unique paths. |
| debug          |                   | *Optional.* Will overlay debugging console. |

## Debugging

`POST http://608dev.net/sandbox/sc/rtliu/api/bike_server.py`

### Body Parameters

| REQUEST BODY DATA | VALUE TYPE        | VALUE                             |
| ----------------- | ----------------- | --------------------------------- |
| force_recalculate |                   | *Optional.* Will forcefully recalculate all path_ids. |
| force             | string            | `YES` to confirm action.  |

| REQUEST BODY DATA | VALUE TYPE        | VALUE                             |
| ----------------- | ----------------- | --------------------------------- |
| view_log          |                   | *Optional.* Will display POST requests log. |

# Pertinent Links
* [Team Folder](https://drive.google.com/drive/folders/1r1T_v1TN4lWPNx6CKEavFLthrNx9wQVv)
* [Milestones](https://docs.google.com/spreadsheets/d/1hNAmWUg27VWahC3y2D8TLOmtSDFwFgt827LHS1INffA)
* [Brainstorming](https://docs.google.com/document/d/11rfrXewlPGayR0_hRya6VwRbTsuuQJJi9O_CJRcBoYM)
* [ArduinoJSON Documentation](https://arduinojson.org/)

### Miscellaneous
* `git config --global user.name "FIRST_NAME LAST_NAME"`
* `git config --global user.email "MY_NAME@example.com"`

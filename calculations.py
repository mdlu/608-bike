
# Memory limitations
mem_bytes = 256*(10**3) #bytes available in ESP
bytes_per_float = 4 #char in array
bytes_per_char = 1  #char in post request
bytes_per_loc = (21*bytes_per_char)+(2*bytes_per_float)
loc_period = 3 #seconds
speed = 9.6/3600 #average speed of a cyclist in miles per second

max_locations = mem_bytes/bytes_per_loc
max_time = loc_period*max_locations/60 #convert to minutes
max_dist = speed*(max_time*60) #reconvert to seconds

print("Locs: {}, Time: {}, Dist: {}".format(max_locations, max_time, max_dist))

# Battery limitations
battery_capacity = 1500 #mAh
effective_capacity = battery_capacity*(3.3/5)
ESP_V = 5 #Volts
no_draw = 70 #mA
with_LCD = 60 #mA
with_wifi = 160 #mA
with_gps = 30 #mA
recording_period = 3000 #milliseconds
ping_time = 2 #milliseconds
time_to_post = 5 #seconds
time_to_fix = 5*recording_period #milliseconds

average_ping_draw = ((no_draw+with_gps+with_LCD)*1+(no_draw+with_LCD)*(recording_period-1))/recording_period
recording_capacity = effective_capacity-((with_LCD+with_wifi)*(time_to_post/3600))-(average_ping_draw*(15/3600))
recording_time = (recording_capacity/average_ping_draw)*60
total_time = (recording_time+(15/60)+(5/60))
print("Draw: {}, Cap: {}, RecTime: {}, Time: {}".format(average_ping_draw, recording_capacity, recording_time, total_time))


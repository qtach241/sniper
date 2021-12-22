import time
import datetime as dt

# Date comparison sanity check
timestamp = "1639984967706"
#timestamp = time.time()*1000

# Method 1, convert both to millis time formats
millis_timestamp = int(timestamp)
millis_timenow = dt.datetime.now().timestamp()*1000
millis_timediff = millis_timenow - millis_timestamp
print(f"millis timestamp: {millis_timestamp}, timenow: {millis_timenow}, diff: {millis_timediff}")

# Method 2, convert both to datetime formats
datetime_timestamp = dt.datetime.utcfromtimestamp(millis_timestamp//1000)
datetime_timenow = dt.datetime.utcnow()
datetime_timediff = datetime_timenow - datetime_timestamp
print(f"datetime timestamp: {datetime_timestamp}, timenow: {datetime_timenow}, diff: {datetime_timediff}, diff_min: {datetime_timediff.total_seconds()}")

# ISO format
iso_time = "2021-12-20T07:58:50.195362Z"
iso_time = iso_time[:-1] # Trailing Z makes fromisoformat() shit the bed
datetime_iso = dt.datetime.fromisoformat(iso_time)
datetime_iso_diff = datetime_timenow - datetime_iso
print(f"datetime_iso: {datetime_iso}, timenow: {datetime_timenow}, diff: {datetime_iso_diff}, diff_min: {datetime_iso_diff.total_seconds()}")

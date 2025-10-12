import faust
import json
import snowflake.connector as sf

# IMPORTANT: Fill in your Snowflake details below!
SNOWFLAKE_USER = "THETANVID9"
SNOWFLAKE_PASSWORD = "h5Pn56s3qrzcbLE"
SNOWFLAKE_ACCOUNT = "CZZLRMV-ALB00459" # Example: xy12345.ap-south-1.aws

app = faust.App(
    'consume_and_store',
    broker='kafka://localhost:9092',
    value_serializer='raw',
)

# Establish connection to Snowflake
conn = sf.connect(
    user=SNOWFLAKE_USER,
    password=SNOWFLAKE_PASSWORD,
    account=SNOWFLAKE_ACCOUNT,
    autocommit=False
)
cursor = conn.cursor()

# Set the context for Snowflake
cursor.execute('USE WAREHOUSE COMPUTE_WH')
cursor.execute("USE DATABASE RAMU") # Make sure this database exists!
cursor.execute("USE SCHEMA PUBLIC") # Make sure this schema exists!

# Define the Kafka topic
car_speed_topic = app.topic('car_speed')

@app.agent(car_speed_topic)
async def read_and_store(carspeed_stream_data):
    async for data in carspeed_stream_data:
        captured_event = json.loads(data)
        print(f"Received: {captured_event}")
        cursor.execute("""
        INSERT INTO car_speed_data (car_id, car_name, car_speed, capture_time)
        VALUES (%s, %s, %s, %s)""", (
            captured_event["car_id"],
            captured_event["car_name"],
            captured_event["car_speed"],
            captured_event["capture_time"]
        ))
        conn.commit()

if __name__ == '__main__':
    app.main()
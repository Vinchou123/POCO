import paho.mqtt.client as mqtt
from app import app, db, Plant, socketio
from flask_socketio import emit

def parse_topic(topic):
    parts = topic.split('/')
    if len(parts) == 3 and parts[0] == 'ESP':
        return parts[1], parts[2]
    return None, None

def on_connect(client, userdata, flags, rc):
    print("🔌 Connecté au broker MQTT :", rc)
    client.subscribe("ESP/+/TEMP")
    client.subscribe("ESP/+/HUM")
    client.subscribe("ESP/+/LUM")

def on_message(client, userdata, msg):
    mac, sensor = parse_topic(msg.topic)
    if not mac or not sensor:
        return

    value = msg.payload.decode()
    print(f"[MQTT] {mac} | {sensor} = {value}")

    with app.app_context():
        plant = Plant.query.filter_by(name=mac).first()
        if plant:
            if sensor == 'TEMP':
                plant.temperature = value
            elif sensor == 'HUM':
                plant.humidity = value
            elif sensor == 'LUM':
                plant.light = value
            db.session.commit()

            # Émettre les données via SocketIO
            socketio.emit('mqtt_data', {
                'mac': mac,
                'sensor': sensor,
                'value': value
            }, broadcast=True)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("mqtt.eclipseprojects.io", 1883, 60)
client.loop_forever()

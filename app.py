import signal
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
from flask_migrate import Migrate



app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

app.config['SECRET_KEY'] = 'votre_clé_secrète_ici'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plants.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialiser Flask-Migrate
migrate = Migrate(app, db)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    plants = db.relationship('Plant', secondary='user_plants')

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    temperature = db.Column(db.String(50))
    humidity = db.Column(db.String(50))  # Colonne existante
    watering = db.Column(db.String(50))
    flow_rate = db.Column(db.String(50))
    light = db.Column(db.String(50))  # Colonne existante
    light_duration = db.Column(db.String(50))
    summary = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(200))
    # Nouvelles colonnes pour stocker les données des capteurs
    current_humidity = db.Column(db.Float, nullable=True)  # Humidité actuelle
    current_light = db.Column(db.Float, nullable=True)  # Luminosité actuelle

# Table de liaison entre utilisateurs et plantes
user_plants = db.Table('user_plants',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('plant_id', db.Integer, db.ForeignKey('plant.id'), primary_key=True)
)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('search'))
        flash('Nom d\'utilisateur ou mot de passe incorrect')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur existe déjà')
            return redirect(url_for('register'))
            
        user = User(username=username, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/search')
@login_required
def search():
    return render_template('search.html')

@app.route('/api/plants')
def get_plants():
    plants = Plant.query.all()
    user_plant_ids = [plant.id for plant in current_user.plants] if current_user.is_authenticated else []
    
    return jsonify([{
        'id': plant.id,
        'name': plant.name,
        'temperature': plant.temperature,
        'humidity': plant.humidity,
        'watering': plant.watering,
        'flow_rate': plant.flow_rate,
        'light': plant.light,
        'light_duration': plant.light_duration,
        'summary': plant.summary,
        'image_url': plant.image_url,
        'is_user_plant': plant.id in user_plant_ids
    } for plant in plants])

@app.route('/api/plants/<int:plant_id>/toggle', methods=['POST'])
@login_required
def toggle_plant(plant_id):
    plant = Plant.query.get_or_404(plant_id)
    if plant in current_user.plants:
        current_user.plants.remove(plant)
        db.session.commit()
        return jsonify({'status': 'removed'})
    else:
        current_user.plants.append(plant)
        db.session.commit()
        return jsonify({'status': 'added'})

@app.route('/api/plants/<int:plant_id>/remove', methods=['POST'])
@login_required
def remove_plant(plant_id):
    plant = Plant.query.get_or_404(plant_id)
    if plant in current_user.plants:
        current_user.plants.remove(plant)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Plante supprimée avec succès'})
    return jsonify({'status': 'error', 'message': 'Plante non trouvée ou non associée à l\'utilisateur'}), 400

@app.route('/api/plants/<int:plant_id>/update_mac', methods=['POST'])
@login_required
def update_mac_api(plant_id):
    data = request.get_json()
    mac_address = data.get('mac_address')

    if not mac_address:
        return jsonify({'status': 'error', 'message': "L'adresse MAC est obligatoire."}), 400

    with app.app_context():
        # Rechercher la plante par son ID
        plant = Plant.query.get(plant_id)
        if not plant:
            return jsonify({'status': 'error', 'message': 'Plante introuvable.'}), 404

        # Mettre à jour l'adresse MAC
        plant.mac_address = mac_address
        db.session.commit()

        return jsonify({'status': 'success', 'message': "Adresse MAC mise à jour avec succès."})

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/profile/update_password', methods=['POST'])
@login_required
def update_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    
    if not current_user.check_password(current_password):
        flash('Mot de passe actuel incorrect', 'error')
        return redirect(url_for('profile'))
    
    current_user.password = generate_password_hash(new_password)
    db.session.commit()
    flash('Mot de passe mis à jour avec succès', 'success')
    return redirect(url_for('profile'))

@app.route('/profile/delete_account', methods=['POST'])
@login_required
def delete_account():
    current_user.plants = []
    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    flash('Compte supprimé avec succès', 'success')
    return redirect(url_for('index'))

def load_plants_from_json():
    json_path = os.path.join('data', 'plants.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['plants']

def init_db():
    with app.app_context():
        db.create_all()
        
        # Vérifier si la base de données est vide
        if Plant.query.count() == 0:
            # Charger les plantes depuis le fichier JSON
            plants_data = load_plants_from_json()
            
            for plant_data in plants_data:
                plant = Plant(
                    mac_address=plant_data.get('mac_address', 'UNKNOWN'),  # Ajout de mac_address
                    name=plant_data['name'],
                    temperature=plant_data['temperature'],
                    humidity=plant_data['humidity'],
                    watering=plant_data['watering'],
                    flow_rate=plant_data['flow_rate'],
                    light=plant_data['light'],
                    light_duration=plant_data['light_duration'],
                    summary=plant_data.get('summary', ''),
                    image_url=plant_data.get('image_url', '')
                )
                db.session.add(plant)
            
            db.session.commit()
            
# Configuration MQTT
MQTT_BROKER = 'broker.emqx.io' 
MQTT_PORT = 1883
MQTT_TOPICS = [
    "ESP/5c:01:3b:72:ae:80/HUM",
    "ESP/5c:01:3b:72:ae:80/LUM"
]

# Variable pour suivre l'état de la connexion
is_connected = False

def on_connect(client, userdata, flags, rc):
    print("🔌 Connecté au broker MQTT :", rc)
    with app.app_context():
        plants = Plant.query.all()
        for plant in plants:
            mac_address = plant.mac_address
            if mac_address == "UNKNOWN":
                # Supprimez ou commentez cette ligne pour ne pas afficher les messages
                # print(f"⚠️ Adresse MAC inconnue pour la plante : {plant.name}, abonnement ignoré.")
                continue
            topic = f"ESP/{mac_address}/#"
            client.subscribe(topic)
            print(f"✅ Abonné au topic : {topic}")
                   
def handle_exit(sig, frame):
    print("\nDéconnexion du broker MQTT...")
#    mqtt_client.publish("ESP/5c:01:3b:72:ae:80/HUM", "Déconnecté", qos=1)
    mqtt_client.disconnect()
    mqtt_client.loop_stop()
    print("Déconnecté proprement.")
    sys.exit(0)

# Capture des signaux d'interruption
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

def parse_topic(topic):
    """
    Analyse un topic MQTT et retourne l'adresse MAC et le type de capteur.
    Exemple de topic : "ESP/5c:01:3b:72:ae:80/HUM"
    Retourne : ("5c:01:3b:72:ae:80", "HUM")
    """
    parts = topic.split('/')
    if len(parts) == 3 and parts[0] == 'ESP':
        mac_address = parts[1]
        sensor = parts[2]
        return mac_address, sensor
    return None, None

def on_message(client, userdata, msg):
    print(f"📩 Message brut reçu : Topic = {msg.topic}, Payload = {msg.payload.decode()}")

    mac, sensor = parse_topic(msg.topic)
    if not mac or not sensor:
        print("⚠️ Topic non valide ou non pris en charge")
        return

    value = float(msg.payload.decode())  # Convertir la valeur en float

    print(f"[MQTT] {mac} | {sensor} = {value}")

    with app.app_context():
        # Rechercher la plante correspondant à l'adresse MAC
        plant = Plant.query.filter_by(mac_address=mac).first()
        if plant:
            # Mettre à jour les données du capteur dans les nouvelles colonnes
            if sensor == 'HUM':
                plant.current_humidity = value
            elif sensor == 'LUM':
                plant.current_light = value
            db.session.commit()

            print(f"✅ Données mises à jour pour la plante : {plant.name}")
            # Émettre les données via Socket.IO
            socketio.emit('mqtt_data', {
                'mac': mac,
                'sensor': sensor,
                'value': value
            }, to='/')

def on_disconnect(client, userdata, rc):
    global is_connected
    if is_connected:  # Vérifie si le client était connecté
        print("Déconnecté du broker MQTT")
        # ESP/#
        client.publish("ESP/5c:01:3b:72:ae:80/STATE", "Ping", qos=1)
        is_connected = False  # Met à jour l'état de la connexion

# Configurer le client MQTT
mqtt_client = mqtt.Client(client_id="mqttx_876ac026")
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.on_disconnect = on_disconnect
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 120)
mqtt_client.loop_start()

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True, use_reloader=False)

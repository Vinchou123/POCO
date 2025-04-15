

# 🌱 POCO - Plot de Plante Connecté

**POCO** est un projet IoT (Objet connecté) permettant de surveiller et de gérer à distance l'état d'un pot de plante. Le système utilise le protocole **MQTT** pour la communication entre les capteurs, le microcontrôleur et une interface d'affichage sur un site web.

## 🚀 Objectifs du Projet

- Surveiller en temps réel l'état d'un pot de plante.
- Transmettre les données via MQTT à un serveur ou une application.
- Proposer une solution éco-responsable et pédagogique autour de l'IoT.

## 🛠️ Technologies utilisées

- **Microcontrôleur** : ESP32 avec connectivité Wi-Fi intégrée
- **Capteurs** :
  - Capteur d'humidité du sol 💧
  - Capteur de lumière ☀️
- **Protocole de communication** : [MQTT](https://mqtt.org/)
- **Broker MQTT** : Mosquitto
- **Plateforme** : Site web (en http local : http://127.0.0.1:5000 )

## 📡 Fonctionnement

1. Les capteurs collectent des données environnementales.
2. Le microcontrôleur envoie les données via MQTT à un broker.
3. Les données peuvent être :
   - Visualisées sur un tableau de bord (Onglet Profil)
   - Stockées dans une base de données


## 🧩 C’est quoi MQTT ?
MQTT (Message Queuing Telemetry Transport) est un protocole de messagerie léger spécialement conçu pour les objets connectés. Il fonctionne avec un système de "publish/subscribe", ce qui signifie que :

Les objets publient des données (température, humidité, etc.) sur un topic.

D’autres appareils ou applications s’abonnent à ces topics pour recevoir les données en temps réel.

C’est très pratique pour les projets IoT car c’est rapide, fiable, et économe en énergie

Il fonctionne même avec une connexion Internet instable ou lente

## 🔑 C’est quoi une adresse MAC ?
Une adresse MAC (Media Access Control) est un identifiant unique attribué à chaque appareil connecté à un réseau (Wi-Fi, Ethernet, etc.). Elle est généralement composée de 6 paires de caractères hexadécimaux, comme ceci :
3C:71:BF:09:4A:2E

Dans le cas de POCO :

Chaque pot de plante connecté (ESP32, ESP8266…) a sa propre adresse MAC.

Cela permet de différencier les différents pots dans le réseau, utile si tu en as plusieurs.

### 📦 Installation des dépendances Python

Pour faire fonctionner correctement l’interface backend de POCO, tu dois installer certaines bibliothèques Python.


**Installation de Flask** *(micro-framework web)*  
***`pip install flask`***

**Installation de Flask-Migrate** *(outil de gestion de migrations pour SQLAlchemy)*  
***`pip install flask-migrate`***

**Installation groupée des bibliothèques principales du projet**  
***`pip install flask flask_sqlalchemy flask_migrate flask_cors`***

**Installation de la bibliothèque pour communiquer avec un broker MQTT**  
***`pip install paho-mqtt`***

**Installation de Flask-SocketIO** *(communication en temps réel via WebSockets)*  
***`pip install flask-socketio`***

**Mise à jour de la bibliothèque paho-mqtt** *(utile si une ancienne version est installée)*  
***`pip install --upgrade paho-mqtt`***

**Désinstallation de paho-mqtt** *(si besoin de repartir de zéro ou corriger un conflit)*  
***`pip uninstall paho-mqtt`***

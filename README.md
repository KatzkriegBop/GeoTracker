# 📍 GeoTracker

GeoTracker es un sistema completo de rastreo de ubicación en tiempo real que combina:

- 🧠 Un **bot de Telegram** para registrar ubicaciones de usuarios.
- ☁️ Una **base de datos Firebase** para almacenar coordenadas por número telefónico.
- 🗺️ Una **página web con mapa interactivo** (Leaflet.js) para visualizar y seleccionar usuarios rastreados.

---

## 🚀 Características

- Solicita número de teléfono antes de rastrear.
- Guarda coordenadas cada segundo si el seguimiento está activado.
- Interfaz web que permite seleccionar un número y ver su ubicación más reciente.
- Datos almacenados por número y timestamp.

---

## 🛠️ Tecnologías Utilizadas

| Componente     | Tecnología                    |
|----------------|-------------------------------|
| Bot Telegram   | `python-telegram-bot` (v20+)   |
| Backend        | Python 3.10+                   |
| Base de datos  | Firebase Realtime Database     |
| Mapa Web       | HTML, JavaScript, Leaflet.js   |
| API            | REST JSON (Firebase)           |

---

## 📦 Estructura del Proyecto


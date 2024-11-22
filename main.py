import os
import threading
import socket
import json
from flask import Flask, render_template, request, send_from_directory, jsonify, redirect, url_for
from datetime import datetime

# Настройки
HTTP_PORT = 3000
SOCKET_PORT = 5000
STORAGE_DIR = "storage"
DATA_FILE = os.path.join(STORAGE_DIR, "data.json")

# Создаем папку storage, если она не существует
os.makedirs(STORAGE_DIR, exist_ok=True)

# Если файла data.json нет, создаем пустой
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as file:
        json.dump({}, file)

# Flask приложение
app = Flask(__name__)

# Маршруты
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/message.html", methods=["GET", "POST"])
def message():
    if request.method == "POST":
        username = request.form.get("username")
        message = request.form.get("message")
        print(f"Received: {username} - {message}")
        send_to_socket_server({"username": username, "message": message})
        return redirect(url_for("index"))
    return render_template("message.html")


@app.route("/<path:filename>")
def static_files(filename):
    # Отдаем статические файлы (CSS, картинки)
    return send_from_directory(".", filename)

@app.errorhandler(404)
def page_not_found(e):
    # Возвращаем страницу ошибки 404
    return render_template("error.html"), 404

# Функция отправки данных на сокет-сервер
def send_to_socket_server(data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ("127.0.0.1", SOCKET_PORT)
    message = json.dumps(data).encode("utf-8")
    sock.sendto(message, server_address)
    sock.close()

# Сокет-сервер
def socket_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", SOCKET_PORT))

    print(f"Socket сервер запущен на порту {SOCKET_PORT}")
    while True:
        data, _ = sock.recvfrom(4096)
        message = json.loads(data.decode("utf-8"))

        # Сохраняем сообщение в файл data.json
        with open(DATA_FILE, "r+") as file:
            content = json.load(file)
            timestamp = datetime.now().isoformat()
            content[timestamp] = message
            file.seek(0)
            json.dump(content, file, indent=4)

# Запуск серверов в разных потоках
if __name__ == "__main__":
    threading.Thread(target=socket_server, daemon=True).start()
    print(f"HTTP сервер запущен на порту {HTTP_PORT}")
    app.run(host="0.0.0.0", port=HTTP_PORT)

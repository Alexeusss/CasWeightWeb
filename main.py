from flask import Flask, render_template, jsonify, request
import serial
import serial.tools.list_ports
import threading
import time
import re

app = Flask(__name__)
data = {"message": ""}
port = None

def list_serial_ports():
    """ Возвращает список доступных COM портов """
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def read_weight(port):
    """ Чтение данных с весового терминала """
    weight_pattern = re.compile(r'(\d+\.\d+) kg')

    try:
        with serial.Serial(port, baudrate=9600, timeout=1) as ser:
            while True:
                if ser.in_waiting > 0:
                    try:
                        line = ser.readline().decode('latin1').strip()
                        if line:
                            match = weight_pattern.search(line)
                            if match:
                                weight = match.group(1)
                                if "ST" in line:
                                    data["message"] = f"СТАБ: {weight}0 kg"
                                    data["color"] = "green"
                                elif "US" in line:
                                    data["message"] = f"НСТАБ: {weight}0 kg"
                                    data["color"] = "red"
                                else:
                                    data["message"] = f"Received: {line}"
                                    data["color"] = "orange"
                            else:
                                data["message"] = f"Received: {line}"
                                data["color"] = "orange"
                    except UnicodeDecodeError as e:
                        print(f"Ошибка декодирования: {e}")
                time.sleep(0.1)
    except serial.SerialException as e:
        print(f"Error: {e}")

@app.route('/')
def index():
    ports = list_serial_ports()
    return render_template('index.html', ports=ports)

@app.route('/data')
def get_data():
    return jsonify(data)

@app.route('/start', methods=['POST'])
def start_reading():
    global port
    port = request.json['port']
    start_serial_thread(port)
    return jsonify({"status": "started"})

def start_serial_thread(port):
    thread = threading.Thread(target=read_weight, args=(port,))
    thread.daemon = True
    thread.start()

def main():
    app.run(debug=True, use_reloader=False)

if __name__ == '__main__':
    main()

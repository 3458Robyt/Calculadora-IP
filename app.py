from flask import Flask, request, jsonify, render_template
import ipaddress

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        data = request.get_json()
        ip = data.get("ip").strip()
        mask = data.get("mask").strip()

        if not ip or not mask:
            return jsonify({"error": "Por favor, ingrese la dirección IP y la máscara."}), 400

        # Determinar si la máscara es un prefijo (ej: "24") o una máscara en formato completo (ej: "255.255.255.0")
        if mask.isdigit():  # Caso en que la máscara sea un número como "24"
            mask = int(mask)
            network = ipaddress.ip_network(f"{ip}/{mask}", strict=False)
        else:  # Caso en que la máscara sea una dirección IP como "255.255.255.0"
            mask = ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
            network = ipaddress.ip_network(f"{ip}/{mask}", strict=False)

        # Calcular el rango de IPs útiles
        first_usable_ip = network.network_address + 1
        last_usable_ip = network.broadcast_address - 1
        usable_ips_range = f"{first_usable_ip} - {last_usable_ip}" if first_usable_ip <= last_usable_ip else "No hay IPs útiles"

        # Determinar la clase de la IP
        first_octet = int(ip.split('.')[0])
        if 1 <= first_octet <= 126:
            ip_class = "A"
        elif 128 <= first_octet <= 191:
            ip_class = "B"
        elif 192 <= first_octet <= 223:
            ip_class = "C"
        elif 224 <= first_octet <= 239:
            ip_class = "D (Multicast)"
        elif 240 <= first_octet <= 255:
            ip_class = "E (Experimental)"
        else:
            ip_class = "Desconocida"

        # Determinar si es pública o privada
        ip_type = "Pública"
        private_ranges = [
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16")
        ]
        if any(ipaddress.ip_address(ip) in private for private in private_ranges):
            ip_type = "Privada"

        # Convertir IPs a binario para visualización
        red_bin = ''.join(bin(int(octet))[2:].zfill(8) for octet in str(network.network_address).split('.'))
        host_bin = ''.join(bin(int(octet))[2:].zfill(8) for octet in str(network.broadcast_address).split('.'))

        return jsonify({
            "network": str(network.network_address),
            "broadcast": str(network.broadcast_address),
            "hosts": network.num_addresses - 2 if network.num_addresses > 2 else network.num_addresses,
            "range": usable_ips_range,
            "binary_red": red_bin[:mask],
            "binary_host": host_bin[mask:],
            "class": ip_class,
            "type": ip_type
        })
    except ValueError as e:
        return jsonify({"error": f"Error en el procesamiento: {str(e)}"}), 400

if __name__ == '__main__':
    app.run(port=80)

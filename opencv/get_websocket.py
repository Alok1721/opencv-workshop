import socket

# Get local machine's IP address dynamically
def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Connect to external server
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print("Error getting IP:", e)
        return "127.0.0.1"  # Default to localhost if an error occurs

host_ip = get_host_ip()
print("Your IP Address:", host_ip)

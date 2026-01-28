import urllib.request

def get_public_ip():
    try:
        # Fetch IP from a reliable external service
        with urllib.request.urlopen('https://api.ipify.org') as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return f"Error fetching IP: {e}"

if __name__ == "__main__":
    print("-" * 30)
    print("Fetching Public IPv4 Address...")
    ip = get_public_ip()
    print(f"YOUR SERVER IP: {ip}")
    print("-" * 30)
    print("Use this IP in Google Cloud Console -> APIs & Services -> Credentials")
    print("under 'Application restrictions' -> 'IP addresses'.")

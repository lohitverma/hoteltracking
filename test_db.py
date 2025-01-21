import psycopg2
import socket
import sys
import os

def test_dns():
    host = "dpg-cu7failds78s73arp6j0-a.oregon-postgres.render.com"
    try:
        print(f"\nTesting DNS resolution for {host}")
        ip = socket.gethostbyname(host)
        print(f"✓ DNS Resolution successful: {host} -> {ip}")
        return True
    except socket.gaierror as e:
        print(f"✗ DNS Resolution failed: {e}")
        return False

def test_tcp():
    host = "dpg-cu7failds78s73arp6j0-a.oregon-postgres.render.com"
    port = 5432
    try:
        print(f"\nTesting TCP connection to {host}:{port}")
        sock = socket.create_connection((host, port), timeout=10)
        sock.close()
        print(f"✓ TCP Connection successful")
        return True
    except Exception as e:
        print(f"✗ TCP Connection failed: {e}")
        return False

def test_postgres():
    params = {
        'dbname': 'hoteltracker',
        'user': 'hoteltracker_user',
        'password': 'VoKj4Xa7xyG0DhH2Fa0UW48QFd7gGZme',
        'host': 'dpg-cu7failds78s73arp6j0-a.oregon-postgres.render.com',
        'port': '5432'
    }
    
    ssl_modes = ['require', 'verify-full', 'verify-ca', 'prefer', 'disable']
    
    for ssl_mode in ssl_modes:
        try:
            print(f"\nTesting PostgreSQL connection with sslmode={ssl_mode}")
            conn_str = f"postgresql://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['dbname']}?sslmode={ssl_mode}"
            conn = psycopg2.connect(conn_str, connect_timeout=10)
            
            cur = conn.cursor()
            cur.execute('SELECT version()')
            ver = cur.fetchone()
            print(f"✓ PostgreSQL Connection successful with {ssl_mode}")
            print(f"✓ Server version: {ver[0]}")
            
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"✗ PostgreSQL Connection failed with {ssl_mode}: {e}")
    return False

def main():
    print("Database Connection Test")
    print("=" * 50)
    
    # Test DNS
    dns_ok = test_dns()
    
    # Test TCP
    tcp_ok = test_tcp()
    
    # Test PostgreSQL
    if dns_ok and tcp_ok:
        postgres_ok = test_postgres()
    else:
        print("\n✗ Skipping PostgreSQL test due to network issues")
        postgres_ok = False
    
    print("\nTest Summary")
    print("=" * 50)
    print(f"DNS Resolution: {'✓' if dns_ok else '✗'}")
    print(f"TCP Connection: {'✓' if tcp_ok else '✗'}")
    print(f"PostgreSQL Connection: {'✓' if postgres_ok else '✗'}")
    
    if not (dns_ok and tcp_ok and postgres_ok):
        sys.exit(1)

if __name__ == "__main__":
    main()

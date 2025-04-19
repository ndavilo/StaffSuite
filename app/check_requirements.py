import streamlit as st
import socket
import ipaddress

def get_local_ip():
    """Get the local network IP address"""
    try:
        # Create a socket connection to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        st.error(f"Error getting local IP: {str(e)}")
        return None

def ip_address_range_verification(required_ip_ranges=None):
    if required_ip_ranges is None:
        required_ip_ranges = st.secrets["ALLOWED_IP_RANGES"]  # Gets list from secrets.toml
    """
    Verify if IP is within allowed ranges
    
    Args:
        required_ip_ranges (list): List of allowed IP ranges
    
    Returns:
        tuple: (bool, str) - (True, "") if IP passes, (False, "IP range") if fails
    """
    client_ip = get_local_ip()
    
    if not client_ip:
        return False, "IP detection failed"
    
    # Verify IP range
    try:
        ip = ipaddress.ip_address(client_ip)
        for ip_range in required_ip_ranges:
            start_ip, end_ip = ip_range.split('-')
            network = ipaddress.ip_network(start_ip[:start_ip.rfind('.')] + '.0/24', strict=False)
            if ip in network and int(start_ip.split('.')[-1]) <= int(ip.exploded.split('.')[-1]) <= int(end_ip):
                return True, ""
    except ValueError as e:
        st.error(f"IP validation error: {str(e)}")
    
    return False, "!!! 🔒 Access Restricted: Please connect to the EFCC office network to use this application. If you believe this is an error, contact ICT Support."
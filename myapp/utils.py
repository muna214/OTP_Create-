from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import requests


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_list = [ip.strip() for ip in x_forwarded_for.split(',')]
        # Localhost এবং private IP বাদ দিয়ে রিয়েল IP নিন
        for ip in ip_list:
            if ip != '127.0.0.1' and not ip.startswith('192.168.') and not ip.startswith('10.'):
                return ip
        return ip_list[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
        if ip == '127.0.0.1':
            return None  # localhost এ রিয়েল IP নেই
        return ip

def get_country_from_ip(ip):
    if not ip:
        return 'Unknown'
    try:
        response = requests.get(f'https://ipapi.co/{ip}/json/')
        data = response.json()
        return data.get('country_name', 'Unknown')
    except:
        return 'Unknown'
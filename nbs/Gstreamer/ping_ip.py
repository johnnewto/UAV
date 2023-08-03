__all__ = ['ping_ip']
# find if ethernet address is available
import subprocess
import platform


def ping_ip(ip_address):

    if platform.system().lower() == "windows":
        status = subprocess.call(
            ['ping', '-q', '-n', '1', '-W', '1', ip_address],
            stdout=subprocess.DEVNULL)
    else:
        status = subprocess.call(
            ['ping', '-q', '-c', '1', '-W', '1', ip_address],
            stdout=subprocess.DEVNULL)

    if status == 0:
        return True
    else:
        return False

def test_ping_ip():
    ip_address = "10.42.0.1"
    if ping_ip(ip_address):
        print(f'The IP address {ip_address} is currently in use.')
    else:
        print(f'The IP address {ip_address} is not in use.')

if __name__ == '__main__':
    ip_address = "10.42.0.1"
    # ip_address = '192.168.1.1'

    # status = subprocess.call(
    #     ['ping', '-q', '-c', '1', '-W', '1', ip_address],
    #     stdout=subprocess.DEVNULL)
    # # if status == 0:
    # print(status)

    if ping_ip(ip_address):
        print(f'The IP address {ip_address} is currently in use.')
    else:
        print(f'The IP address {ip_address} is not in use.')
import requests
import smtplib
import os
import paramiko
import linode_api4
import time
import schedule

EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
LINODE_TOKEN = os.environ.get('LINODE_TOKEN')

# EMAIL_ADDRESS = 'mauricio.ecamilo@gmail.com'
# EMAIL_PASSWORD = 'uhmwsnhpijagynkp'
# LINODE_TOKEN = 'TESTE'

def send_notification(email_msg):
        print('Sending email...')
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp: 
            smtp.starttls()
            smtp.ehlo() 
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD) 
            message = f"Subject: SITE DOWN\n{email_msg}"
            smtp.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, message)

def restart_container():
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())   
        ssh.connect(hostname='54.234.185.151', username='root', key_filename='/home/mauricio/.ssh/id_rsa')
        stdin, stdout, stderr = ssh.exec_command('docker start b7c59b87cce6')
        print(stdout.readlines())
        ssh.close()
        print('Application Restarted')

def restart_server_and_container():
    print('Rebooting the server...')
    client = linode_api4.LinodeClient(LINODE_TOKEN) 
    nginx_server = client.load(linode_api4.Instance, 52236040) 
    nginx_server.reboot()

    while True: 
        nginx_server = client.load(linode_api4.Instance, 52236040) 
        if nginx_server.status == 'running':
            time.sleep(5)
            restart_container()
            break        
     
def monitor_application():
    try:
        response = requests.get('http://54.234.185.151:8080/') 
        if response.status_code == 200:
            print('Application is running successfully!')
        else:
            print('Application Down. Fix it!')
            msg = f"Application returned {response.status_code}"
            send_notification()
            restart_container()
    except Exception as ex: 
        print(f"Connection error happened: {ex}")
        msg = f"Application not accessable at all"
        send_notification(msg)  
        restart_server_and_container()

schedule.every(5).minutes.do(monitor_application)

while True:
     schedule.run_pending()
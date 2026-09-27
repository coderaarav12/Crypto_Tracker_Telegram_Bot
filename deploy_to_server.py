import paramiko
from scp import SCPClient
import os

IP = "192.168.1.5"
USER = "aarav12949"
PASS = "12949"

def run_ssh_command(ssh, cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(f"sudo -S bash -c '{cmd}'")
    stdin.write(PASS + '\n')
    stdin.flush()
    out = stdout.read().decode('utf-8', 'replace')
    err = stderr.read().decode('utf-8', 'replace')
    if out: 
        try:
            print("OUT:", out.encode('cp1252', 'replace').decode('cp1252'))
        except:
            print("OUT: <unprintable>")
    if err: 
        try:
            print("ERR:", err.encode('cp1252', 'replace').decode('cp1252'))
        except:
            print("ERR: <unprintable>")
    return out

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("Connecting...")
    try:
        ssh.connect(IP, username=USER, password=PASS, timeout=10)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return
    
    # Create target directory
    run_ssh_command(ssh, "mkdir -p /opt/telegram-bot")
    run_ssh_command(ssh, "chown aarav12949:aarav12949 /opt/telegram-bot")

    print("Uploading files via SCP...")
    with SCPClient(ssh.get_transport()) as scp:
        bot_files = ["api_server.py", "telegram_bot.py", "requirements.txt", ".env"]
        for f in bot_files:
            scp.put(f, f"/opt/telegram-bot/{f}")
        
        scp.put(r"C:\Users\aarav\OneDrive\Documents\linux server\dashboard\server.py", 
                "/home/aarav12949/Projects/dashboard/server.py")
    
    print("Setting up virtual environment...")
    run_ssh_command(ssh, "chmod 600 /opt/telegram-bot/.env")
    run_ssh_command(ssh, "sudo -u aarav12949 python3.14 -m venv /opt/telegram-bot/venv")
    run_ssh_command(ssh, "sudo -u aarav12949 /opt/telegram-bot/venv/bin/pip install --only-binary=:all: -r /opt/telegram-bot/requirements.txt")
    
    print("Creating wrapper script...")
    wrapper = '''#!/bin/bash
/opt/telegram-bot/venv/bin/python /opt/telegram-bot/api_server.py &
API_PID=$!
/opt/telegram-bot/venv/bin/python /opt/telegram-bot/telegram_bot.py &
BOT_PID=$!
trap "kill $API_PID $BOT_PID" EXIT
wait -n
kill $API_PID $BOT_PID 2>/dev/null
'''
    run_ssh_command(ssh, f"cat << 'EOF' > /opt/telegram-bot/start.sh\n{wrapper}\nEOF")
    run_ssh_command(ssh, "chmod +x /opt/telegram-bot/start.sh")
    run_ssh_command(ssh, "chown aarav12949:aarav12949 /opt/telegram-bot/start.sh")

    print("Setting up systemd service...")
    service_content = '''[Unit]
Description=Telegram Bot Backend
After=network.target

[Service]
User=aarav12949
WorkingDirectory=/opt/telegram-bot
EnvironmentFile=/opt/telegram-bot/.env
ExecStart=/opt/telegram-bot/start.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
'''
    run_ssh_command(ssh, f"cat << 'EOF' > /etc/systemd/system/telegram-bot.service\n{service_content}\nEOF")
    
    # Sudoers configuration
    sudoers_rule = 'aarav12949 ALL=(ALL) NOPASSWD: /usr/bin/systemctl start telegram-bot, /usr/bin/systemctl stop telegram-bot, /usr/bin/systemctl restart telegram-bot, /usr/bin/systemctl is-active telegram-bot'
    # Write to a temp file then move it to avoid nested quote issues in bash -c
    run_ssh_command(ssh, f'echo "{sudoers_rule}" > /tmp/telegram-sudoers')
    run_ssh_command(ssh, "mv /tmp/telegram-sudoers /etc/sudoers.d/services")
    run_ssh_command(ssh, "chmod 440 /etc/sudoers.d/services")
    
    # Reload and start
    run_ssh_command(ssh, "systemctl daemon-reload")
    run_ssh_command(ssh, "systemctl enable telegram-bot")
    run_ssh_command(ssh, "systemctl restart telegram-bot")
    
    # Restart dashboard
    run_ssh_command(ssh, "systemctl restart dashboard")
    
    print("Deployment finished.")

if __name__ == '__main__':
    main()

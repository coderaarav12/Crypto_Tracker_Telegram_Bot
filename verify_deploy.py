import paramiko
import sys

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
    print("OUT:", out.encode('cp1252', 'replace').decode('cp1252'))
    if err and "Password:" not in err:
        print("ERR:", err.encode('cp1252', 'replace').decode('cp1252'))
    return out

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USER, password=PASS)
    
    print("\n--- Service Status ---")
    run_ssh_command(ssh, "systemctl status telegram-bot --no-pager")
    
    print("\n--- Health Endpoint ---")
    run_ssh_command(ssh, "curl -s http://127.0.0.1:5003/health")
    
    print("\n--- Dashboard Check ---")
    run_ssh_command(ssh, "curl -s http://127.0.0.1:4097/api/status | grep telegram-bot")

if __name__ == '__main__':
    main()

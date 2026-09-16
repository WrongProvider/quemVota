import paramiko
import os

host = '192.168.68.52'
user = 'matomatka'
password = 'M159753t'
key_path = os.path.expanduser('~/.ssh/id_ed25519.pub')

with open(key_path, 'r') as f:
    pub_key = f.read().strip()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

# Adicionar a chave ao authorized_keys
command = f"mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '{pub_key}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
stdin, stdout, stderr = ssh.exec_command(command)
stdout.read()
ssh.close()
print("Chave copiada com sucesso.")

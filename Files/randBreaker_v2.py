#!/bin/bash

function ctrl_c() {
  echo -e "${red}\n\n[!] Saliendo...\n${normal}"
  rm $py_file 2>/dev/null
  rm out.txt 2>/dev/null
  exit 1
}
# Ctrl+c
trap ctrl_c INT

blue='\033[1;34m'
green='\033[1;32m'
dark_yellow='\033[1;38;5;214m'
red='\033[1;31m'
normal='\033[0m'

py_file="ranBreaker.py"
target="socket.cryptohack.org"
port="13379"

echo -ne "${blue}[+]${normal} ${dark_yellow}Estableciendo conexión a${normal} ${blue}${target}:${port}${normal}\n"
echo
tempfile=$(mktemp)
{
  echo -ne '{"supported": ["DH64"]}\n';
  sleep 2;
  echo -ne '{"chosen": "DH64"}\n';
  sleep 2;
} | nc $target $port>$tempfile &
nc_pid=$!
received_data=false
wait $nc_pid

> out.txt

while read -r line; do
  echo "$line" | tee -a out.txt
  if [[ "$line" == *'"encrypted_flag"'* ]]; then
    received_data=true
    break
  fi
done <$tempfile

rm $tempfile

if $received_data; then
  echo -ne "\n${blue}[+]${normal} ${dark_yellow}Comunicación terminada${normal}\n" | tee -a out.txt
else
  echo "${red}[!] No se recibieron datos${normal}\n"
  exit 1
fi

#Valores

A=$(cat out.txt | grep -o '"A": "0x[^"]*' | cut -d'"' -f4)
iv=$(cat out.txt | grep -o '"iv": "[^"]*' | awk -F ': ' '{print $2}' | tr -d '"')
encrypted_flag=$(cat out.txt | grep -o '"encrypted_flag": "[^"]*' | awk -F ': ' '{print $2}' | tr -d '"')
B=$(cat out.txt | grep -o '"B": "0x[^"]*' | cut -d'"' -f4)
p=$(cat out.txt | grep -o '"p": "0x[^"]*' | cut -d'"' -f4)

############### PyLoad #############################

py_load=$(cat << EOL

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib
import math
import time
import random
from pwn import log

first = time.time() # Comenzando a contar el tiempo

# Intercambiar por input para mas pruebas
A = "$A"
p = "$p"
g = 2
B = "$B"
iv = "$iv"
encrypted_flag = "$encrypted_flag"

# Enteros
p = int(p, 16)
A = int(A, 16)
B = int(B, 16)

progress = log.progress("Calculando parámetros")

progress.status("Parametros: (p, g, A) = (%d, %d, %d)" % (p, g, A))
time.sleep(1)  # Simular carga

def f(runner):
    y, a, b = runner

    if y%3 == 0:
        y = g*y %p
        a = a+1
        
    elif y%3 == 1:
        y = A*y %p
        b = b+1
        
    else:
        y = y*y %p
        a = 2*a 
        b = 2*b
        
    return y, a%(p-1), b%(p-1)

# Tortuga y liebre inician saltos en la misma posición
a_rand = random.randint(1, p-2)
b_rand = random.randint(1, p-2)
liebre = tortuga = (pow(g, a_rand, p)*pow(A, b_rand, p) % p, a_rand, b_rand)

collision_progress = log.progress("Buscando colisión")

#Por cada paso de la tortuga, la liebre avanza dos hasta que choquen
steps = 0
while True:
    tortuga = f(tortuga)
    liebre = f(f(liebre))
    steps += 1
    if steps % 1000 == 0:
        collision_progress.status("Pasos dados: %d" % steps)
        
    if tortuga[0] == liebre[0]:
        collision_progress.success("Colisión encontrada después de %d pasos" % steps)
        break
                
# Cuando haya una colisión, toma de esta el candidato para resolver el log 
at, bt = tortuga[1:]
ah, bh = liebre[1:]

a = ah - at
b = bt - bh

d = math.gcd(bh-bt, p-1)

a = a//d
b = b//d
new_mod = (p-1)//d

k0 = a * pow(b, -1, new_mod) % new_mod

key_progress = log.progress("Probando posibles claves")

for _ in range(d):
    k = k0 + _ * new_mod
    key_progress.status("Probando k = %d" % k)
    
    if pow(g,k,p) == A:
        key_progress.success("Clave compartida encontrada: %d" % k)
        break

# Sacar el secreto compartido y desencriptar
iv = bytes.fromhex(iv)
encrypted_flag = bytes.fromhex(encrypted_flag)
shared_secret = pow(B, k, p) # B=g^x mod p | A=g^k mod p ----> B^k mod p == A^x mod p
ciphertext = encrypted_flag

def decrypt(secret, iv, cipher):
    # SHA1 hash
    sha1 = hashlib.sha1()
    sha1.update(str(secret).encode())
    key = sha1.digest()[:16]
    aes = AES.new(key, AES.MODE_CBC, iv)
    plain = aes.decrypt(cipher)
    return plain

flag = decrypt(shared_secret, iv, ciphertext)
log.info("Flag: %s" % flag.decode())

last = time.time()
timex = (last - first)/60
formatime = "{:.1f}".format(timex)
print(f"\n[*] Duración de: {formatime} minutos.")

timex_sec = last - first
formatimes = "{:.2f}".format(timex_sec)

print(f"\n\t--> {formatimes} en segundos.")


EOL
)

echo "$py_load" > "$py_file"
python3 "$py_file"
rm "$py_file"
rm out.txt

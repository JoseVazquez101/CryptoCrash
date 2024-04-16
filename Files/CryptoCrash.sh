#!/bin/bash

# Declaración de colores
blue='\033[1;34m'
green='\033[1;32m'
dark_yellow='\033[1;38;5;214m'
red='\033[1;31m'
normal='\033[0m'

# Declaración de variables predeterminadas
target="socket.cryptohack.org"
port="13379"
attack="log" # log o rand

# Función para imprimir el banner
function printBanner() {
    cat >banner.py <<EOL
import sys
import random
import time

def print_logo():
    clear = "\\x1b[0m"
    colors = [31, 32, 33, 34, 35, 36]
    logo = """ _______  ______ __   __  _____  _______  _____  _______  ______ _______ _______ _     _
 |       |_____/   \\_/   |_____]    |    |     | |       |_____/ |_____| |______ |_____|
 |_____  |    \\_    |    |          |    |_____| |_____  |    \\_ |     | ______| |     |
    """
    for line in logo.split("\\n"):
        sys.stdout.write("\\x1b[1;%dm%s%s\\n" % (random.choice(colors), line, clear))
        time.sleep(0.1)  # Añadir un pequeño retardo de 0.1 segundos por línea

    # Impresión del 'footer' con información de autoría y versión
    sys.stdout.write("\\033[s")  # Guardar la posición del cursor
    sys.stdout.write("\\033[40;0f")  # Mover cursor a la esquina inferior derecha
    footer_color = random.choice(colors)  # Seleccionar un color aleatorio para el footer
    footer_text = "(made by: retr0 v 1.0.1)"
    sys.stdout.write("\\x1b[1;%dm%s\\x1b[0m" % (footer_color, footer_text))
    sys.stdout.write("\\033[u")  # Restaurar la posición del cursor

print()
print_logo()
print()

EOL
    python3 banner.py
    rm banner.py
}


# Función de ayuda
function showHelp() {
    echo -e "${green}Uso: $0 --host <host> --port <port> --attack <log|rand>${normal}"
    echo -e "${green}Ejemplos:${normal}"
    echo -e "  ${green}$0 --host socket.cryptohack.org --port 13379 --attack log${normal}"
    echo -e "  ${green}$0 --host socket.cryptohack.org --port 13379 --attack rand${normal}"
}

# Manejo de señales (Ctrl+C)
function ctrl_c() {
    echo -e "${red}\n[!] Saliendo...\n${normal}"
    rm $py_file 2>/dev/null
    rm out.txt 2>/dev/null
    exit 1
}
trap ctrl_c INT

# Procesamiento de argumentos de línea de comandos
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --host) target="$2"; shift ;;
        --port) port="$2"; shift ;;
        --attack) attack="$2"; shift ;;
        *) echo -e "${red}Opción desconocida: $1${normal}" >&2; showHelp; exit 1 ;;
    esac
    shift
done

# Verificar que se han proporcionado los parámetros necesarios
if [[ -z "$target" || -z "$port" || -z "$attack" ]]; then
    echo -e "${red}Error: Falta especificar host, puerto o tipo de ataque.${normal}"
    showHelp
    exit 1
fi

# Imprimir el banner
printBanner

echo -ne "${blue}[+]${normal} ${dark_yellow}Estableciendo conexión con ${normal} ${blue}${target}:${port}${normal} usando ${green}$attack attack${normal}\n"
tempfile=$(mktemp)
{
    echo -ne '{"supported": ["DH64"]}\n';
    sleep 2;
    echo -ne '{"chosen": "DH64"}\n';
    sleep 2;
} | nc $target $port >$tempfile &
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
    echo -ne "\n${blue}[+]${normal} ${dark_yellow}Comunicación con el servidor terminada.${normal}\n"
else
    echo -e "${red}[!] No se recibieron datos.${normal}\n"
    exit 1
fi

# Extraer valores
A=$(grep -o '"A": "0x[^"]*' out.txt | cut -d'"' -f4)
iv=$(grep -o '"iv": "[^"]*' out.txt | awk -F ': ' '{print $2}' | tr -d '"')
encrypted_flag=$(grep -o '"encrypted_flag": "[^"]*' out.txt | awk -F ': ' '{print $2}' | tr -d '"')
B=$(grep -o '"B": "0x[^"]*' out.txt | cut -d'"' -f4)
p=$(grep -o '"p": "0x[^"]*' out.txt | cut -d'"' -f4)

if $received_data; then
    echo -ne "\n${blue}[+]${normal} ${dark_yellow}Comunicación con el servidor terminada.${normal}\n"
else
    echo -e "${red}[!] No se recibieron datos.${normal}\n"
    exit 1
fi

# Crear y ejecutar el script de Python específico
echo -ne "${blue}[+]${normal} ${dark_yellow}Generando script de Python para el descifrado...${normal}\n"

if [[ "$attack" == "log" ]]; then
    py_file="LogJam.py"
    cat > "$py_file" <<EOL
from Crypto.Cipher import AES
from Crypto.Util import number
import hashlib
from sympy.ntheory import discrete_log
import pwn

# Inicializar pwntools para mostrar trazas detalladas
pwn.context.log_level = 'debug'

# Convertir valores de cadena a numéricos
p = "${p}"
g = 2
A = "${A}"
B = "${B}"
iv =  "${iv}"
encrypted_flag = "${encrypted_flag}"

# Convertir hex a int
p = int(p, 16)
A = int(A, 16)
B = int(B, 16)
iv = bytes.fromhex(iv)
encrypted_flag = bytes.fromhex(encrypted_flag)

# Mostrar valores convertidos
pwn.log.info("Valores Convertidos: p=%d, A=%d, B=%d, iv=%s, encrypted_flag=[oculto]" % (p, A, B, iv.hex()))

# Iniciar proceso de descifrado
progress = pwn.log.progress("Descifrando")

progress.status("Calculando clave secreta (Discrete Log Problem)")
# Calcular la clave secreta a
a = discrete_log(p, A, g)
pwn.sleep(1)
progress.status("Clave secreta calculada")

progress.status("Generando clave AES a partir de la clave secreta")
secret = pow(B, a, p)
key = hashlib.sha1(str(secret).encode()).digest()[:16]
pwn.sleep(1)
progress.status("Clave AES generada")
print(key)

progress.status("Descifrando la bandera con AES")
flag = AES.new(key, AES.MODE_CBC, iv).decrypt(encrypted_flag)
pwn.sleep(1)
progress.success("Bandera descifrada: ")

print(f"Bandera: {flag.decode()}")

EOL
    python3 "$py_file"
    rm "$py_file"

elif [[ "$attack" == "rand" ]]; then
    py_file="ranBreaker.py"
    cat > "$py_file" <<EOL
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib
import math
import time
import random
from pwn import log

first = time.time()  # Comenzando a contar el tiempo

# Intercambiar por input para mas pruebas
A = "${A}"
p = "${p}"
g = 2
B = "${B}"
iv = "${iv}"
encrypted_flag = "${encrypted_flag}"

# Enteros
p = int(p, 16)
A = int(A, 16)
B = int(B, 16)

progress = log.progress("Calculando parámetros")

progress.status("Parametros: (p, g, A) = (%d, %d, %d)" % (p, g, A))
time.sleep(1)  # Simular carga

def f(runner):
    y, a, b = runner

    if y % 3 == 0:
        y = g * y % p
        a = a + 1
        
    elif y % 3 == 1:
        y = A * y % p
        b = b + 1
        
    else:
        y = y * y % p
        a = 2 * a
        b = 2 * b
        
    return y, a % (p-1), b % (p-1)

# Tortuga y liebre inician saltos en la misma posición
a_rand = random.randint(1, p-2)
b_rand = random.randint(1, p-2)
liebre = tortuga = (pow(g, a_rand, p) * pow(A, b_rand, p) % p, a_rand, b_rand)

collision_progress = log.progress("Buscando colisión")

# Por cada paso de la tortuga, la liebre avanza dos hasta que choquen
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

a = a // d
b = b // d
new_mod = (p-1) // d

k0 = a * pow(b, -1, new_mod) % new_mod

key_progress = log.progress("Probando posibles claves")

for _ in range(d):
    k = k0 + _ * new_mod
    key_progress.status("Probando k = %d" % k)
    
    if pow(g, k, p) == A:
        key_progress.success("Clave compartida encontrada: %d" % k)
        break

# Sacar el secreto compartido y desencriptar
iv = bytes.fromhex(iv)
encrypted_flag = bytes.fromhex(encrypted_flag)
shared_secret = pow(B, k, p)  # B=g^x mod p | A=g^k mod p ----> B^k mod p == A^x mod p
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
    python3 "$py_file"
    rm "$py_file"
else
    echo -e "${red}Tipo de ataque no válido: $attack${normal}"
    showHelp
    exit 1
fi

# Limpieza
echo -ne "${blue}[+]${normal} ${dark_yellow}Limpieza...${normal}\n"
rm out.txt

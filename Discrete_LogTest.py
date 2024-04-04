#!/bin/bash

# Configuración de colores para la salida
red='\033[0;31m'
blue='\033[0;34m'
normal='\033[0m'
dark_yellow='\033[0;33m'

# Definir función para manejar la interrupción (Ctrl+C)
function ctrl_c() {
  echo -e "${red}\n\n[!] Saliendo...\n${normal}"
  # Limpiar archivos temporales
  rm $py_file 2>/dev/null
  rm out.txt 2>/dev/null
  exit 1
}
# Asignar el manejador de señal para Ctrl+C
trap ctrl_c INT

# Configuración inicial
py_file=LogJam.py
target="socket.cryptohack.org"
port="13379"

# Mensaje de inicio
echo -ne "${blue}[+]${normal} ${dark_yellow}Estableciendo conexión con ${normal} ${blue}${target}:${port}${normal}\n"
echo

# Crear archivo temporal para comunicación
tempfile=$(mktemp)

# Iniciar comunicación y capturar en archivo temporal
echo -ne "${dark_yellow}Iniciando intercambio de mensajes con el servidor...${normal}\n"
{
  echo -ne '{"supported": ["DH64"]}\n';
  sleep 2;
  echo -ne '{"chosen": "DH64"}\n';
  sleep 2;
} | nc $target $port > $tempfile &
nc_pid=$!
received_data=false
wait $nc_pid

# Preparar archivo de salida
> out.txt

# Leer y procesar datos recibidos
echo -ne "${dark_yellow}Procesando datos recibidos del servidor...${normal}\n"
while read -r line; do
  echo "$line" | tee -a out.txt
  if [[ "$line" == *'"encrypted_flag"'* ]]; then
    received_data=true
    break
  fi
done <$tempfile

# Limpiar archivo temporal
rm $tempfile

# Verificar si se recibieron datos
if $received_data; then
  echo -ne "\n${blue}[+]${normal} ${dark_yellow}Comunicación con el servidor terminada.${normal}\n"
else
  echo -e "${red}[!] No se recibieron datos.${normal}\n"
  exit 1
fi

# Extract values from the output file
echo -ne "${dark_yellow}Extrayendo valores recibidos...${normal}\n"
A=$(grep -o '"A": "0x[^"]*' out.txt | cut -d'"' -f4)
iv=$(grep -o '"iv": "[^"]*' out.txt | awk -F ': ' '{print $2}' | tr -d '"')
encrypted_flag=$(grep -o '"encrypted_flag": "[^"]*' out.txt | awk -F ': ' '{print $2}' | tr -d '"')
B=$(grep -o '"B": "0x[^"]*' out.txt | cut -d'"' -f4)
p=$(grep -o '"p": "0x[^"]*' out.txt | cut -d'"' -f4)
echo -e "${blue}[+] Valores extraídos: A=${A}, iv=${iv}, encrypted_flag=[oculto], B=${B}, p=${p}${normal}"

# Crear y configurar script de Python para descifrado
echo -ne "${dark_yellow}Generando script de Python para el descifrado...${normal}\n"
py_load=$(cat << EOL

from Crypto.Cipher import AES
from Crypto.Util import number
import hashlib
from sympy.ntheory import discrete_log
import pwn

# Inicializar pwntools para mostrar trazas detalladas
pwn.context.log_level = 'debug'

# Convertir valores de cadena a numéricos
p = "$p"
g = 2
A = "$A"
B = "$B"
iv =  "$iv"
encrypted_flag = "$encrypted_flag"

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
pwn.sleep(1) # Simulación de tiempo de cálculo
progress.status("Clave secreta calculada")

progress.status("Generando clave AES a partir de la clave secreta")
secret = pow(B, a, p)
key = hashlib.sha1(str(secret).encode()).digest()[:16]
pwn.sleep(1) # Simulación de generación de clave AES
progress.status("Clave AES generada")

progress.status("Descifrando la bandera con AES")
flag = AES.new(key, AES.MODE_CBC, iv).decrypt(encrypted_flag)
pwn.sleep(1) # Simulación de descifrado
progress.success("Bandera descifrada")

print(f"Bandera: {flag.decode()}")

EOL
)

# Guardar y ejecutar script de Python
echo "$py_load" > "$py_file"
echo -ne "${blue}[+]${normal} ${dark_yellow}Ejecutando script de Python para obtener la bandera...${normal}\n"
python3 "$py_file"

# Limpiar archivos temporales
echo -ne "${blue}[+]${normal} ${dark_yellow}Limpieza...${normal}\n"
rm "$py_file"
rm out.txt

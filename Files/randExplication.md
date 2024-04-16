# Explicación Segundo Algoritmo

El script está diseñado para romper un cifrado durante un intercambio de llaves usando el método Diffie-Hellman. Este método permite a dos partes establecer una llave secreta compartida a través de un canal inseguro sin necesidad de haber compartido algo secretamente antes.

Componentes del Script

#### 1. Establecimiento de la Conexión:
El script primero intenta conectarse a mi servidor designado usando el comando nc (netcat), que es una herramienta para manejar conexiones TCP/UDP. Se envían dos mensajes JSON para indicar qué método de cifrado se soporta y cuál se elige ("DH64"), reduciendo el numero de seguridad de la llave.

#### 2. Recepción de Datos:
Después de establecer la conexión, el script espera recibir datos que incluyen varios parámetros cifrados como A, B, p, iv, y encrypted_flag. Estos datos son necesarios para intentar descifrar la llave compartida.

- A y B: Son valores públicos generados por las partes durante el intercambio Diffie-Hellman.
- p: Es un número primo usado como base en los cálculos de cifrado.
- iv: Es un vector de inicialización para el cifrado AES.
- encrypted_flag: Es el mensaje cifrado que necesitamos descifrar.

#### 3. Proceso de Descifrado:

El script usa un enfoque para encontrar colisiones y, con ellas, deducir la llave secreta.
Esta parte es en sí la más laboriosa, pues el algoritmo se diseñó con un enfoque de semillas aleatorias, las cuales después de cierto tiempo pasado de no encontrar colisiones, se reinician y se descartan.
Imaginese como una pecera donde dos objetos rebotan aleatoriamente lanzados desde el mismo punto, en algún momento estos deben chocar, y con esto encontrar la llave.

Objetos: Se generan dos secuencias de números, una avanzando más rápido que la otra. La idea es que ambas secuencias eventualmente colisionarán, y esta colisión ayuda a encontrar la llave secreta.
Calculando la Llave Secreta (k): Una vez encontrada la colisión, se calculan posibles valores de k (la llave secreta) usando un pequeño factor corrector d para ajustar la llave y verificar cuál es correcta.

#### 4. Desencriptación del Mensaje:
Usando la llave secreta encontrada, se configura un cifrado AES con el vector de inicialización iv para desencriptar el mensaje. La llave para el AES se deriva aplicando un hash SHA1 al secreto compartido.

Ejecución y Salida:
El script ejecuta todos estos pasos automáticamente y muestra una barra de progreso para cada etapa significativa del proceso. Al final, si todo es correcto, se mostrará el mensaje descifrado (la "flag" alojada en mi servidor).

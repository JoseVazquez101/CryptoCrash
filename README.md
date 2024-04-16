# CryptoCrash

- Proyecto enfocado a realizar ataques Man in the Middle aprovechando la vulnerabilidad clave Diffie-Hellman Export-Grade.
- Para bajarlo y habilitar todos los requerimientos, seguir los siguientes pasos:

~~~bash
❯ apt install nc python3
❯ git clone https://github.com/JoseVazquez101/CryptoCrash
❯ cd CryptoCrash
❯ pip install -r requeriments.txt
~~~

### Uso:
- Para utilizar el script, es necesario tener permisos de ejecución y se puede invocar con diferentes parámetros para especificar el host, puerto y tipo de ataque:

~~~bash
cd files
./CryptoCrash.sh --host <ip> --port <port> --attack log
./CryptoCrash.sh --host <ip> --port <port> --attack rand
~~~


***
#### Testeo de algoritmos por separado:

Caso 1: [DiscreteLog Attack](https://github.com/JoseVazquez101/CryptoCrash/blob/main/Files/DiscreteLog_attack.py)
  - [Explication code](https://github.com/JoseVazquez101/CryptoCrash/blob/main/Files/Explication_Log.md)

Caso 2: Random Colitions Attack -----> [V1](https://github.com/JoseVazquez101/CryptoCrash/blob/main/Files/randBreaker_v1.py) & [V2](https://github.com/JoseVazquez101/CryptoCrash/blob/main/Files/randBreaker_v2.py)
  - [Explication code](https://github.com/JoseVazquez101/CryptoCrash/blob/main/Files/randExplication.md)
***

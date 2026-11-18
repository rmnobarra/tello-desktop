# Tello Desktop

Aplicativo open source para controlar Ryze Tello / Boost Combo no **Ubuntu**, com vídeo e teclado. Controle PS4 opcional com perfil configurável. Python 3.10+; alvo inicial Ubuntu 22.04/24.04.

**Experimental: ainda não validado em drone real.** Testes automatizados cobrem lógica de comandos, não voo, rádio ou compatibilidade do hardware. Não existe garantia de pouso se o programa travar ou o enlace cair. Nenhuma decolagem automática ao iniciar.

## Instalar

```bash
sudo apt update
sudo apt install python3-venv python3-pip libgl1 libglib2.0-0
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
tello-desktop
```

O último comando abre a **simulação**, sem conexão ao drone. Conecte depois o Ubuntu à rede `TELLO-XXXXXX`, feche o app do celular e execute:

```bash
tello-desktop --live
```

Baixe dependências antes de conectar à rede do drone, que não fornece internet. Execute nativamente no Ubuntu com ambiente gráfico, não via WSL, Docker ou SSH. Se o firewall bloquear, permita somente tráfego UDP do IP 192.168.10.1 para as portas locais necessárias (8889 comandos, 8890 estado, 11111 vídeo); não desative o firewall inteiro.

## Teclado

| Comando | Ação |
|---|---|
| Shift+T | Decolar, apenas com entradas neutras e bateria ≥30% |
| L | Pousar |
| W / S | Frente / trás |
| A / D | Esquerda / direita |
| ↑ / ↓ | Subir / descer |
| ← / → | Girar |
| Esc, fechar janela, Ctrl+C | Solicitar pouso e encerrar |

Perda de foco da janela solicita pouso. Comandos de movimento limitados a 30 (escala SDK). Bateria abaixo de 20%, perda do controle e vídeo parado por mais de 3 segundos solicitam pouso. São medidas de software de melhor esforço, não sistemas certificados. O estado exibido de voo é local, não confirmação por telemetria.

## Controle PS4

Conecte por USB inicialmente, ou pareie pelo Bluetooth do Ubuntu. Execute **com o drone desligado**:

```bash
tello-desktop --inspect-controller
cp gamepad.example.json gamepad.json
```

Confira cada eixo e botão e edite `gamepad.json`. O exemplo não é um mapeamento universal: USB, Bluetooth e drivers podem mudar índices. `axes` segue a ordem lateral, frente/trás, altura, giro; `signs` inverte cada eixo. `deadman` precisa ficar pressionado para aceitar os eixos; `takeoff` junto com deadman solicita decolagem; `land` solicita pouso sem deadman. Soltar deadman zera os comandos, mantendo voo estacionário se o posicionamento funcionar. Os atalhos do iPhone não se aplicam aqui.

```bash
tello-desktop --gamepad gamepad.json
# Só após conferir sinais, neutro e botões na simulação:
tello-desktop --live --gamepad gamepad.json
```

Retorne os manches ao centro antes de decolar. Não altere o perfil em voo. A inspeção permanece offline mesmo se `--live` for informado.

## Primeiro teste e limitações

1. Inspecione hélices, protetores e bateria. Use área livre, iluminada e sem vento, pessoas ou animais próximos.
2. Valide toda entrada na simulação e confirme que L é acessível.
3. Conecte ao drone no chão e confirme vídeo e bateria antes de decolar.
4. Faça um voo curto e baixo, mantendo o drone visível. Não teste sobre piscina, água ou areia.

Não há GPS, retorno à origem, desvio de obstáculos, gravação ou mapeamento automático de gamepad neste projeto. Não há monitoramento independente de travamento do processo ou telemetria congelada; perda de rede pode impedir comandos de pouso. Decolagem/pouso são chamadas síncronas e a janela pode ficar momentaneamente sem responder durante a confirmação. Não use este software em cenários que dependam de resposta garantida.

## Desenvolvimento

```bash
pip install --no-deps -e .
python -m unittest discover -s tests -v
```

Abra issues com Ubuntu/Python, conexão USB ou Bluetooth, mensagens e passos para reproduzir. Não publique senhas ou dados pessoais. Contribuições são bem-vindas; alterações de controle devem incluir testes da lógica sem hardware.

## Referências e licença

Implementação original, MIT. [TelloPy](https://github.com/hanyazou/TelloPy), de hanyazou e colaboradores, serviu de referência de uso para vídeo e joystick; não foi copiado nem incorporado código. O backend usado é [DJITelloPy](https://github.com/damiafuentes/DJITelloPy), que utiliza o [SDK oficial Tello 1.3](https://dl-cdn.ryzerobotics.com/downloads/tello/20180910/Tello%20SDK%20Documentation%20EN_1.3.pdf). Recursos exclusivos de EDU não são utilizados. Projeto independente, sem vínculo com Ryze/DJI.

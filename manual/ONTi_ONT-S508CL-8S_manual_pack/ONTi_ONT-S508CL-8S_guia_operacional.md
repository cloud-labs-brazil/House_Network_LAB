# ONTi ONT-S508CL-8S / XikeStor SKS8300-8X - Guia Operacional Rápido

## Arquivos locais disponíveis
- SKS8300-8X_datasheet.pdf
- SKS8300-8X_quick_manual.pdf
- SKS8300-8X_web_ui_manual_13p.pdf
- ONTi_ONT-S508CL-8S_spec_report.md

## Acesso inicial
### Web UI
- Firmware XikeStor: IP padrão 192.168.10.12/24, usuário `admin`, senha `admin`
- Firmware ONTi observado em campo: IP padrão 192.168.2.1/24, usuário `admin`, senha `admin`

### CLI / Console
- Conectar na porta console
- Entrar em modo privilegiado:
  - `enable`
- Entrar em configuração global:
  - `config`
  - ou `config terminal`

## Comandos essenciais
### Identificação e acesso
```text
enable
config
hostname CORE-10G
username admin privilege 15 password 0 SUA-SENHA
service password-encryption
authentication line console login local
authentication line vty login local
ssh-server host-key create rsa
ssh-server enable
write
```

### Criar SVI / IP de gerenciamento
```text
config
interface vlan 1
ip address 192.168.10.2 255.255.255.0
exit
write
```

### Porta access em VLAN 100
```text
config
interface ethernet 1/0/1
switchport mode access
switchport access vlan 100
no shutdown
write
```

### Porta trunk permitindo VLANs 1,100,200
```text
config
interface ethernet 1/0/8
switchport mode trunk
switchport trunk native vlan 1
switchport trunk allowed vlan 1;100;200 tag
no shutdown
write
```

### Porta hybrid
```text
config
interface ethernet 1/0/2
switchport mode hybrid
switchport hybrid native vlan 100
switchport hybrid allowed vlan 1;100 tag
no shutdown
write
```

### Ativar / desativar porta
```text
config
interface ethernet 1/0/3
shutdown
no shutdown
write
```

### Ajuste de velocidade
```text
config
interface ethernet 1/0/1
speed-duplex auto
```

## Comandos de verificação
```text
show version
show running-config
show interface ethernet 1/0/1
show switchport interface ethernet 1/0/1
show ssh-server
show users
show ip route
show tech-support
show memory usage
show cpu usage
```

## Roteamento
### OSPF
```text
config terminal
router ospf 100
ospf router-id 2.3.4.5
network 10.1.1.0/24 area 1
write
```

### RIP
```text
config terminal
router rip
passive-interface vlan 1
route 1.0.0.0/8
write
```

### BGP (exemplo mínimo)
```text
config terminal
router bgp 100
network 172.16.0.0/16
write
```

## Observações importantes
- Salve a configuração com `write`, equivalente a `copy running-config startup-config`
- Todos os ports pertencem à VLAN 1 por padrão
- A mudança entre hybrid e trunk pode exigir voltar primeiro para access
- Em algumas revisões/brands o IP default Web muda entre 192.168.10.12 e 192.168.2.1
- Em caso de módulo/DAC sem link, a Web UI permite forçar modo/velocidade da porta 10G

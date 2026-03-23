# ONTi ONT-S508CL-8S — Especificações Técnicas Consolidadas

## Identidade do equipamento
- Modelo comercial: ONTi ONT-S508CL-8S
- Equivalência amplamente reportada: XikeStor SKS8300-8X
- Classe: switch gerenciável L3 com portas SFP+

## Hardware / interface física
- 8 × portas SFP+ ópticas
- 1 × porta console
- Alimentação externa DC 12V / 2A
- Dimensões: 168 × 94 × 32 mm
- Chassi metálico / desktop ou rack com acessórios
- Sem ventoinha (fanless), conforme review independente

## Velocidades e mídia
- Portas SFP+ com suporte anunciado a 1G / 2.5G / 10G
- Compatibilidade anunciada com módulos MM SFP, SM SFP, BiDi SFP e RJ45 Copper SFP
- 10GBASE-SR: OM1/OM2/OM3+ MMF (2 m ~ 300 m)
- 10GBASE-LR: SMF IEC B1.1/B1.3 (2 m ~ 10 km)
- Compatível com DAC, mas múltiplos relatos dizem que o modo da porta pode precisar ser alterado manualmente para DAC

## Capacidade e desempenho
- Switching capacity: 160 Gbps non-blocking
- Packet forwarding rate:
  - 119.04 Mpps (datasheet PDF / manuais SKS8300-8X)
  - 109.04 Mpps (manual ONTi 8 portas no Manuals+)
- Packet buffer: 12 Mbit
- Jumbo frame: 12 KB
- Modo de encaminhamento: store-and-forward
- Consumo em review independente:
  - 6.3 W em idle
  - 8.3 W com um módulo SFP+ 10GBase-T

## Camada 2 / L2
- VLAN 802.1Q (4K no datasheet)
- Faixa VLAN: 1–4094
- Limite explícito encontrado em uma folha técnica: máximo de 31 VLANs ativas
- Access / Trunk / Hybrid
- Private VLAN
- MAC-based VLAN
- Protocol-based VLAN
- IP-subnet-based VLAN
- Voice VLAN
- GVRP / GMRP
- QinQ / Selective QinQ / Flexible QinQ
- VLAN Translation / N:1 VLAN Translation
- Guest VLAN
- LACP (802.3ad)
- STP / RSTP / MSTP
- MSTP: suporte a até 64 instâncias
- ERPS
- Loopback detection
- LLDP / LLDP-MED
- Port isolation
- Port mirroring / RSPAN
- Storm control
- Port security
- Virtual cable test
- ULDP / Cisco UDLD

## Camada 3 / L3
- IPv4 e IPv6
- Rotas estáticas IPv4/IPv6
- Route aggregation
- RIP v1/v2
- OSPF v2
- BGP4
- IPv6 unicast routing
- MLD v1/v2 snooping

## Multicast
- IGMP snooping v1/v2/v3
- Fast Leave
- IGMP Proxy
- Multicast VLAN

## DHCP / serviços de acesso
- DHCP Server / DHCPv6 Server
- DHCP Client / BOOTP
- DHCP Relay / DHCPv6 Relay
- DHCP Snooping / DHCPv6 Snooping
- DHCP Options 82/43/60/61/67
- IPv6 ND Snooping
- IPv6 SAVI

## QoS / classificação
- Trust CoS/DSCP
- Trust Port
- SP / WRR / WDRR
- Policing / shaping (CAR leak algorithm)
- PolicyMap em ingress / aggregate
- Mapas DSCP↔DSCP, DSCP→DP, DSCP→Queue, COS→DP, COS→Queue
- Classificação por SIP/DIP, protocolo IP, DSCP/TOS/precedence, TCP/UDP src/dst, MAC src/dst, VLAN, COS, tag/untag

## ACL / segurança
- MAC ACL, IP ACL, IP-MAC ACL, user-defined ACL
- ACL por período de tempo
- ACL em VLAN
- 802.1X
- MAB
- RADIUS / TACACS+
- ARP scanning prevention
- ARP spoofing prevention
- ARP guard
- Dynamic ARP inspection
- ARP quantity control
- Anti ICMP attack / ICMP rate limit / ICMP unreachable drop
- CPU protect
- Software / hardware watchdog
- Access management por source MAC e IP
- DoS attack deny

## Gerenciamento
- Console / Telnet / SSH
- HTTP / HTTPS / SSL/TLS
- FTP / TFTP
- Syslog
- SNMP v1/v2c/v3 + SNMP Trap
- SNTP / NTP
- Ping / Traceroute
- Firmware upgrade / backup
- Import/export de configuração via HTTP e TFTP
- Autenticação local / RADIUS / TACACS para console, vty e web

## Endereçamento / defaults encontrados
### Conjunto A (manuais ONTi / blog ONTi)
- IP default: 192.168.2.1
- Usuário/senha: admin / admin

### Conjunto B (manuais SKS8300-8X / device.report)
- IP default: 192.168.10.12
- Usuário/senha: admin / admin
- VLAN padrão: VLAN 1

## Limitações e inconsistências documentais
- 5 GbE não é formalmente listado; compatibilidade depende do módulo e do par remoto
- Há conflito documental sobre packet forwarding rate: 109.04 Mpps vs 119.04 Mpps
- Há conflito documental sobre proteção contra surtos: 3 kV/20 us vs 6 kV/20 us
- A escala de várias features não é detalhada (ACLs, LAGs, rotas, filas QoS, etc.)

## Observações de campo relevantes
- Relatos independentes confirmam equivalência prática entre ONTi ONT-S508CL-8S e XikeStor SKS8300-8X
- Há relato de 512 MB de RAM no `show memory usage`
- DACs funcionam, mas podem exigir ajuste manual de modo da porta para DAC
- Há relatos de que a configuração precisa ser salva explicitamente para sobreviver a reboot/power cycle
- Há relatos de inexistência de um portal público claro para firmware original ONTi
- OpenWrt reconhece o dispositivo como realtek/rtl930x e há suporte, mas ainda com bugs em cenários específicos (ex.: certos GPON SFP 2.5G e problemas com óticas em releases específicos)

## Arquivos baixados nesta coleta
- SKS8300-8X_datasheet.pdf
- SKS8300-8X_quick_manual.pdf
- SKS8300-8X_web_ui_manual_13p.pdf

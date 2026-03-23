# Network Topology — Apartment Infrastructure

## Physical Topology (Corrected after Huawei analysis)

```
   INTERNET (TIM 1Gbps)                   INTERNET (Vivo)
          │                                     │
   ┌──────▼──────┐                       ┌──────▼──────┐
   │  ISP1 TIM   │                       │  ISP2 VIVO  │
   │ 192.168.1.1 │                       │192.168.15.1 │
   │  Sala / 1G  │                       │   Sala      │
   └──────┬──────┘                       └──────┬──────┘
          │                                     │
   ┌──────▼─────────────────────────────────────▼─────┐
   │              ONTi ONT-S508CL-8S                  │
   │              (Core L3 Switch)                    │
   │                                                  │
   │  P1=Vivo   P2..P5=livre   P6=Huawei(WAN)       │
   │  P7=livre  P8=TIM                               │
   │                                                  │
   │  NOTE: P1 & P6 currently bridged (same VLAN)    │
   │  Huawei WAN gets 192.168.15.3 from Vivo DHCP    │
   └──────────────────────┬───────────────────────────┘
                          │ Port 6 (bridged to Vivo L2)
                   ┌──────▼──────────┐
                   │ HUAWEI WiFi BE3 │
                   │ WAN: .15.3      │
                   │ LAN: .16.1/24   │
                   │ (Quartos)       │
                   │ DHCP: .100-.200 │
                   │ DOUBLE NAT      │
                   └─────────────────┘
```

> [!WARNING]
> The Huawei WiFi BE3 is cascaded from Vivo through the switch (double NAT).
> Devices in Quartos (192.168.16.x) pass through TWO NATs to reach internet.
```

## Subnets

| VLAN | Subnet | Gateway (Router) | Gateway (Switch SVI) | DHCP Range | Use |
|------|--------|-------------------|---------------------|------------|-----|
| 10 | 192.168.1.0/24 | 192.168.1.1 (TIM KAON PG2447) | 192.168.1.254 | .2-.254 (24h) | ISP1 + Sala Wi-Fi |
| 15 | 192.168.15.0/24 | 192.168.15.1 (Vivo Askey RTF8225VW) | 192.168.15.254 | .2-.200 (4h) | ISP2 |
| 16 | 192.168.16.0/24 | 192.168.16.1 (Huawei) | 192.168.16.254 | Quartos Wi-Fi |
| 100 | 10.0.0.0/24 | — | 10.0.0.1 | Switch MGMT |

## Devices Inventory

| Hostname | IP | MAC | NIC | Location | Connection |
|----------|-----|-----|-----|----------|------------|
| KAON PG2447 (TIM) | WAN: 177.148.210.103 / LAN: .1.1 | WLAN: 18:34:AF:51:0B:43 | GPON ONT, PPPoE | Sala | Fibra GPON → Switch P8 |
| Vivo Askey RTF8225VW | WAN MAC: 44:89:6d:51:11:30 / LAN: .15.1 | LAN: 44:89:6d:51:f1:30 | Askey GPON ONT | Sala | Fibra → Switch P1 |
| HUAWEI WiFi BE3 | WAN: .15.3 / LAN: .16.1 | WAN: 50:28:73:E3:33:7A | 2.5G WAN, Wi-Fi 7 | Quartos | Switch P6 → cascata Vivo |
| lenovo-lab | 192.168.1.9 | 64:1C:67:A3:FF:97 | Intel I219-LM GbE | Sala | Cabo → TIM |
| 21LAPBRJ401CJ7H | .1.3 / .15.5 / .16.100 | D4:E9:8A:7A:7A:A6 | Intel AX211 Wi-Fi 6E | Mobile | Wi-Fi |
| iPhone | 192.168.1.15 | TBD | — | Sala | Wi-Fi TIM |

## Routing Policy

- **Default route**: 0.0.0.0/0 → 192.168.1.1 (TIM, 1Gbps) — primary
- **Failover route**: 0.0.0.0/0 → 192.168.15.1 (Vivo) — metric 10
- **Wi-Fi devices (30-40)**: Route via TIM (fastest)
- **Wired devices (max 10)**: Route via Vivo

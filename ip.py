from pyroute2 import IPRoute
import socket
import argparse

def format_link_type(link):
  if link.get_attr('IFLA_IFNAME') == 'lo':
    return 'loopback'
  return 'ether'

IFF_FLAGS = {
  0x1: "UP",
  0x2: "BROADCAST",
  0x8: "LOOPBACK",
  0x10: "PTP",
  0x1000: "MULTICAST",
  0x4000: "LOWER_UP",
  0x10000: "DORMANT",
  0x100000: "RUNNING",
}

def get_flags(flags):
  result = []
  for bit, name in IFF_FLAGS.items():
    if flags & bit:
      result.append(name)
  return result

def main():
  parser =  argparse.ArgumentParser(description="argparse")
  parser.add_argument("-i", "--iface", help="Filter interface")
  args = parser.parse_args()

  ip = IPRoute()
  links = ip.get_links()
  addrs = ip.get_addr()

  addr_map = {}
  for addr in addrs:
    index = addr['index']
    ip_addr = addr.get_attr('IFA_ADDRESS')
    family = addr['family']
    prefix = addr['prefixlen']
    broadcast = addr.get_attr('IFA_BROADCAST')

    if index not in addr_map:
      addr_map[index] = []

    addr_map.setdefault(index, []).append((ip_addr, family, prefix, broadcast))

  for link in links:
    index = link['index']
    iface_name = link.get_attr('IFLA_IFNAME')

    if args.iface and iface_name != args.iface:
      continue

    flags = link['flags']
    flags_text = ", ".join(get_flags(flags))
    operstate = link.get_attr('IFLA_OPERSTATE')
    mac_addr = link.get_attr('IFLA_ADDRESS')
    mtu = link.get_attr('IFLA_MTU')
    tx_qeue_len = link.get_attr('IFLA_TXQLEN') or 0
    group = link.get_attr('IFLA_GROUP') or 0
    qdisc = link.get_attr('IFLA_QDISC') or "unknown"
    link_type = format_link_type(link)

    print(
      f"{index}: {iface_name}: <{flags_text}>, "
      f"operstate {operstate}, mtu {mtu}, qdisc {qdisc}, group {group}, qlen {tx_qeue_len}"
    )
    print(f"  link/{link_type} {mac_addr}")

    if index in addr_map:
      for ip_addr, family, prefix, broadcast in addr_map[index]:
        if family == socket.AF_INET:
          line = f"  inet: {ip_addr}/{prefix}"
          if broadcast:
            line += f" brd {broadcast}"
          print(line)
        elif family == socket.AF_INET6:
          print(f"  inet6: {ip_addr}/{prefix}")
    print()

if __name__ == "__main__":
  main()

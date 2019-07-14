from meatball.helpers import TaggedIpList
from bcc import BPF
from bcc.utils import printb
import argparse
import socket
import struct
import glob
import sys
import os

def process_netevent(cpu, data, size):
    global lists
    global args
    event = b["events"].event(data)
    ip_address = socket.inet_ntoa(struct.pack("I", event.address))

    if args.verbose:
        printb(b"\t%s (%d) %s:%d" % (
            event.comm, event.pid, ip_address, socket.htons(event.port)
        ))

    for feed in lists:
        if feed.check_membership(ip_address):
            if args.action == "print":
                print("{} ({}) touched a bad IP ({})".format(
                    event.comm, event.pid, ip_address
                ))
            elif args.action == "dump":
                os.kill(event.pid, 19)
                os.system("gcore -o /tmp/meatball-{}.core {} 2>/dev/null".format(event.ts, event.pid))
                os.kill(event.pid, 9)
                print("{} ({}) Meatball took a dump in /tmp/ ({})".format(
                    event.comm, event.pid, ip_address
                ))
            elif args.action == "suspend":
                os.kill(event.pid, 19)
                print("{} ({}) was suspended ({}) ".format(
                    event.comm, event.pid, ip_address
                ))
            elif args.action == "kill":
                os.kill(event.pid, 9)
                print("{} ({}) was killed by Meatball ({}) ".format(
                    event.comm, event.pid, ip_address
                ))

parser = argparse.ArgumentParser()
parser.add_argument("--action", default="print", choices={"print", "dump", "suspend", "kill"})
parser.add_argument("--verbose", action="store_true")
args = parser.parse_args()

outs = glob.glob("ip_feeds/*.txt")
lists = []
if outs:
    for feed in outs:
        with open(feed, 'r') as handle:
            lists.append(TaggedIpList(feed, handle))
else:
    raise ValueError("No feeds available. Run update_feeds.sh!")

b = BPF(src_file="meatball.c")
b.attach_kprobe(event=b.get_syscall_fnname("connect"), fn_name="probe_connect_enter")
#b.attach_kprobe(event="tcp_v4_connect", fn_name="tcp_v4")
#b.attach_kprobe(event="udp_sendmsg", fn_name="udp_v4")

b["events"].open_perf_buffer(process_netevent)
while 1:
    try:
        b.perf_buffer_poll()
    except KeyboardInterrupt:
        exit()


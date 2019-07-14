# Meatball

A host monitoring proof of concept that uses python and ebpf to watch for bad behavior and optionally take action on it. Named after my parents' cat who attacks me all the time...

## Usage

This tool monitors outbound connections (tcp/udp, ipv4 only) and checks it against threat intelligence lists. There is a script included that pulls down two public feeds, the list of active tor exit nodes and Talos' IP blacklist. Just run `./update_feeds.sh` in the root directory of this project and it'll populate the `ip_feeds/` directory. You can add your own lists to that directory as well.

Run `python main.py` to get started. Out of the box it will not take any action, it'll just print violations as it sees them.

```
$ python main.py -h
usage: main.py [-h] [--action {print,suspend,kill,dump}] [--verbose]

optional arguments:
  -h, --help            show this help message and exit
  --action {print,suspend,kill,dump}
  --verbose
```

There are four actions currently supported via the `--action` flag:
- `print`: the default action, just writes to the screen and that's it
- `suspend`: send a `SIGSTOP` to the process. This can be useful if you need to keep the process in a state where you can interact with it.
- `kill`: kill the process. This may be useful if all you want to do is immediately stop potentially malicious behavior.
- `dump`: suspend the process, take a core dump of it for forensics, and then kill it.

If you're interested in debugging, the `--verbose` flag may be useful to you. This tells the program to print all connections it sees, not just malicious ones.

## Sample output
### Killing Processes

1. In one terminal with root privileges: `$ sudo python main.py --action kill`
2. In another terminal as any user, let's use curl to send an HTTP request to a Tor exit node and another one to google.

We can see we were alerted to only the two out of three curls and that the first two are killed before the connection can complete. The last curl completes just fine.

```
root@gremlin:~/meatball# python main.py --action kill
curl (29514) was killed by Meatball (1.161.127.207)
curl (29515) was killed by Meatball (1.161.127.207)
```

```
gremlin@gremlin:~$ curl -v 1.161.127.207
* Rebuilt URL to: 1.161.127.207/
*   Trying 1.161.127.207...
Killed
gremlin@gremlin:~$ curl -v 1.161.127.207
* Rebuilt URL to: 1.161.127.207/
*   Trying 1.161.127.207...
Killed
gremlin@gremlin:~$ curl google.com
<HTML><HEAD><meta http-equiv="content-type" content="text/html;charset=utf-8">
<TITLE>301 Moved</TITLE></HEAD><BODY>
<H1>301 Moved</H1>
The document has moved
<A HREF="http://www.google.com/">here</A>.
</BODY></HTML>
```

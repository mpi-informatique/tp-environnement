"""Check the VS Code DAP handshake, a breakpoint and source locations without closing stdin."""
import json, subprocess, tempfile, pathlib, threading, queue
with tempfile.TemporaryDirectory() as d:
    source = pathlib.Path(d) / 'main.ml'
    source.write_text('let () =\n  let answer = 42 in\n  Printf.printf "answer=%d\\n" answer\n')
    binary = pathlib.Path(d) / 'main.bc'
    subprocess.run(['ocamlc', '-g', '-o', str(binary), str(source)], check=True)
    p = subprocess.Popen(['ocamlearlybird', 'debug'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    messages = queue.Queue()
    def read():
        try:
            while True:
                headers = {}
                while (line := p.stdout.readline()) not in (b'\r\n', b'\n', b''):
                    k, v = line.decode().split(':', 1)
                    headers[k.lower()] = v.strip()
                if not headers: return
                messages.put(json.loads(p.stdout.read(int(headers['content-length']))))
        except Exception as e: messages.put(e)
    threading.Thread(target=read, daemon=True).start()
    seq = 0
    def send(command, arguments):
        global seq
        seq += 1
        data = json.dumps(dict(seq=seq, type='request', command=command, arguments=arguments)).encode()
        p.stdin.write(f'Content-Length: {len(data)}\r\n\r\n'.encode() + data)
        p.stdin.flush()
        return seq
    def until(predicate):
        while True:
            msg = messages.get(timeout=15)
            if isinstance(msg, Exception): raise msg
            if msg.get('type') == 'response': assert msg['success'], msg
            if predicate(msg): return msg
    def response(s): return until(lambda m: m.get('request_seq') == s)
    try:
        response(send('initialize', dict(adapterID='ocaml.earlybird', linesStartAt1=True, columnsStartAt1=True, pathFormat='path')))
        response(send('launch', dict(program=str(binary), cwd=d, stopOnEntry=True)))
        response(send('setBreakpoints', dict(source=dict(path=str(source)), breakpoints=[dict(line=3)])))
        response(send('configurationDone', {}))
        until(lambda m: m.get('event') == 'stopped' and m.get('body', {}).get('reason') == 'entry')
        response(send('continue', dict(threadId=0)))
        until(lambda m: m.get('event') == 'stopped' and m.get('body', {}).get('reason') == 'breakpoint')
        stack = response(send('stackTrace', dict(threadId=0)))
        assert stack['body']['stackFrames'][0]['line'] == 3, stack
        response(send('disconnect', dict(terminateDebuggee=True)))
        print('Earlybird breakpoint + stack trace OK')
    finally:
        p.kill()
        p.wait()
        print(p.stderr.read().decode())

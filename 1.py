#!/usr/bin/env python3
"""
Kafka Mini UI - Stateless Edition
A minimal, production-ready Flask application for browsing and testing a Kafka cluster.
"""
import atexit
import base64
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify, request
from confluent_kafka import Consumer, KafkaException, Producer, TopicPartition
from confluent_kafka.admin import AdminClient

app = Flask(__name__)

# Thread-safe producer cache
_producer_cache = {}
_producer_lock = threading.Lock()

def get_producer(config: dict) -> Producer:
    """Retrieves or creates a cached Producer instance."""
    cfg_key = tuple(sorted(config.items()))
    with _producer_lock:
        if cfg_key not in _producer_cache:
            _producer_cache[cfg_key] = Producer(config)
        return _producer_cache[cfg_key]

@atexit.register
def close_producers():
    """Flush and close cached producers on exit."""
    for producer in list(_producer_cache.values()):
        try: producer.flush(5)
        except Exception: pass

def get_kafka_config() -> dict:
    """Extracts and decodes the Kafka configuration from the request headers."""
    cfg_b64 = request.headers.get('X-Kafka-Config')
    if not cfg_b64:
        raise ValueError("Kafka configuration missing. Please connect first.")
    try:
        return json.loads(base64.b64decode(cfg_b64))
    except Exception:
        raise ValueError("Invalid Kafka configuration format.")

def build_kafka_config(body: dict) -> dict:
    """Constructs a valid librdkafka config dictionary from the JSON body."""
    c = {
        'bootstrap.servers': str(body.get('bootstrap_servers', '')).strip(),
        'security.protocol': body.get('security_protocol') or 'PLAINTEXT',
        'socket.timeout.ms': 7000
    }
    
    if c['security.protocol'].startswith('SASL'):
        c.update({
            'sasl.mechanism': body.get('sasl_mechanism') or 'PLAIN',
            'sasl.username': body.get('username') or '',
            'sasl.password': body.get('password') or ''
        })
        
    optional = {
        'ssl.ca.location': body.get('ssl_ca_location'),
        'ssl.certificate.location': body.get('ssl_certificate_location'),
        'ssl.key.location': body.get('ssl_key_location'),
        'ssl.key.password': body.get('ssl_key_password'),
        'proxy.url': body.get('proxy_url'),
        'proxy.username': body.get('proxy_username'),
        'proxy.password': body.get('proxy_password'),
    }
    c.update({k: str(v).strip() for k, v in optional.items() if v is not None and str(v).strip()})
    return c

def err(e: Exception) -> str:
    """Extracts readable error messages, specifically handling KafkaException."""
    if isinstance(e, KafkaException) and e.args:
        return str(e.args[0])
    if hasattr(e, 'message'):
        return str(e.message)
    return str(e)

HTML = r'''<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Kafka Mini UI</title>
    <style>
        :root { --bg: #f8fafc; --card: #ffffff; --border: #e2e8f0; --text: #1e293b; --muted: #64748b; --primary: #2563eb; --danger: #dc2626; }
        body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; margin: 0; }
        .wrap { max-width: 1100px; margin: 20px auto; padding: 0 16px; }
        h1 { margin: 0 0 8px 0; }
        .muted { color: var(--muted); font-size: 13px; }
        .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin: 16px 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
        input, select, textarea, button { width: 100%; font: inherit; border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; }
        textarea { min-height: 120px; font-family: monospace; resize: vertical; }
        button { width: auto; background: var(--primary); color: white; border: none; cursor: pointer; font-weight: 600; transition: all 0.2s; }
        button:hover:not(:disabled) { filter: brightness(1.1); }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        button.secondary { background: var(--muted); }
        .row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
        .status { padding: 10px; border-radius: 8px; background: #f1f5f9; margin-top: 12px; white-space: pre-wrap; font-size: 13px; }
        .error { background: #fef2f2; color: var(--danger); }
        table { width: 100%; border-collapse: collapse; word-break: break-word; }
        th, td { text-align: left; padding: 10px; border-bottom: 1px solid var(--border); }
        th { font-size: 12px; color: var(--muted); text-transform: uppercase; }
        tr.topic { cursor: pointer; }
        tr.topic:hover { background: #f8fafc; }
        pre { background: #0f172a; color: #e2e8f0; padding: 16px; border-radius: 8px; overflow: auto; white-space: pre-wrap; max-height: 500px; font-size: 13px; }
        .pill { font-size: 12px; background: #e0e7ff; color: #3730a3; padding: 4px 10px; border-radius: 999px; font-weight: 500; }
        label { font-size: 13px; color: var(--muted); display: block; margin-bottom: 4px; }
        code { font-family: monospace; background: #f1f5f9; padding: 2px 4px; border-radius: 4px; }
        .actions { margin-bottom: 10px; display: flex; gap: 8px; }
    </style>
</head>
<body>
    <div class="wrap">
        <h1>Kafka Mini UI</h1>
        <div class="muted">Inspect, produce JSON, and consume recent records. <strong>Stateless:</strong> Config is stored in your browser.</div>

        <div class="card">
            <h3>Connection</h3>
            <div class="grid">
                <div><label>Bootstrap servers</label><input id="servers" value="localhost:9092"></div>
                <div><label>Security protocol</label>
                    <select id="protocol"><option>PLAINTEXT</option><option>SASL_SSL</option><option>SASL_PLAINTEXT</option><option>SSL</option></select>
                </div>
                <div><label>SASL mechanism</label>
                    <select id="mechanism"><option>PLAIN</option><option>SCRAM-SHA-256</option><option>SCRAM-SHA-512</option></select>
                </div>
                <div><label>Username</label><input id="username"></div>
                <div><label>Password</label><input id="password" type="password"></div>
                <div><label>CA truststore (PEM path)</label><input id="ca" placeholder="/etc/ssl/certs/kafka-ca.pem"></div>
                <div><label>Client certificate</label><input id="cert" placeholder="/run/secrets/client.pem"></div>
                <div><label>Client private key</label><input id="keyfile" placeholder="/run/secrets/client.key"></div>
                <div><label>Key / P12 password</label><input id="keypass" type="password"></div>
                <div><label>HTTP proxy URL</label><input id="proxy" placeholder="http://proxy.example:8080"></div>
                <div><label>Proxy username</label><input id="proxyuser"></div>
                <div><label>Proxy password</label><input id="proxypass" type="password"></div>
            </div>
            <div class="row" style="margin-top:10px">
                <button id="btn-connect" onclick="connect()">Connect</button>
                <button class="secondary" id="btn-refresh" onclick="loadTopics()">Refresh</button>
                <span class="pill" id="selected">No topic selected</span>
            </div>
            <div id="status" class="status">Not connected</div>
        </div>

        <div class="card">
            <h3>Topics</h3>
            <div style="overflow:auto">
                <table>
                    <thead><tr><th>Topic</th><th>Partitions</th><th>Est. Records</th></tr></thead>
                    <tbody id="topics"><tr><td colspan="3" class="muted">Connect to load topics.</td></tr></tbody>
                </table>
            </div>
            <small class="muted">* Record counts are estimates based on offset watermarks.</small>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Produce JSON</h3>
                <label>Optional key</label><input id="key">
                <label>JSON value</label>
                <textarea id="value">{"hello":"kafka"}</textarea>
                <button id="btn-produce" onclick="produce()">Produce</button>
            </div>
            <div class="card">
                <h3>Consume Recent</h3>
                <label>Maximum messages</label>
                <input id="limit" type="number" min="1" max="200" value="20">
                <button id="btn-consume" onclick="consume()">Consume</button>
                <div class="actions" style="margin-top:10px">
                    <button class="secondary" onclick="copyMessages()">Copy JSON</button>
                </div>
                <pre id="messages">[]</pre>
            </div>
        </div>
    </div>

    <script>
        let topic = '';
        let kafkaConfig = {};
        const el = id => document.getElementById(id);

        function note(t, isError = false) {
            el('status').textContent = t;
            el('status').className = 'status' + (isError ? ' error' : '');
        }

        function setLoading(isLoading) {
            const btns = ['btn-connect', 'btn-refresh', 'btn-produce', 'btn-consume'];
            btns.forEach(id => {
                const btn = el(id);
                if (btn) {
                    btn.disabled = isLoading;
                    if (isLoading && id === 'btn-connect') btn.textContent = 'Connecting...';
                    else if (id === 'btn-connect') btn.textContent = 'Connect';
                }
            });
            if (isLoading) note('Loading...');
        }

        function toBase64(str) {
            return btoa(unescape(encodeURIComponent(str)));
        }

        async function api(url, options = {}) {
            options.headers = options.headers || {};
            if (Object.keys(kafkaConfig).length > 0) {
                options.headers['X-Kafka-Config'] = toBase64(JSON.stringify(kafkaConfig));
            }
            try {
                const r = await fetch(url, options);
                const x = await r.json();
                if (!r.ok) throw Error(x.error || 'Request failed');
                return x;
            } catch (e) {
                note(e.message, true);
                throw e;
            }
        }

        async function connect() {
            setLoading(true);
            try {
                const body = {
                    bootstrap_servers: el('servers').value, security_protocol: el('protocol').value,
                    sasl_mechanism: el('mechanism').value, username: el('username').value, password: el('password').value,
                    ssl_ca_location: el('ca').value, ssl_certificate_location: el('cert').value,
                    ssl_key_location: el('keyfile').value, ssl_key_password: el('keypass').value,
                    proxy_url: el('proxy').value, proxy_username: el('proxyuser').value, proxy_password: el('proxypass').value
                };
                const x = await api('/api/connect', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
                });
                kafkaConfig = body;
                note(x.message);
                loadTopics();
            } catch (e) {} finally { setLoading(false); }
        }

        async function loadTopics() {
            if (Object.keys(kafkaConfig).length === 0) return note('Connect first.', true);
            setLoading(true);
            try {
                const x = await api('/api/topics');
                el('topics').innerHTML = x.topics.map(t => `
                    <tr class="topic" data-topic="${encodeURIComponent(t.name)}">
                        <td><code>${safe(t.name)}</code></td><td>${t.partitions}</td><td>${t.records.toLocaleString()}</td>
                    </tr>
                `).join('') || '<tr><td colspan="3" class="muted">No topics found.</td></tr>';
                document.querySelectorAll('.topic').forEach(r => r.onclick = () => pick(decodeURIComponent(r.dataset.topic)));
                note('Topics loaded.');
            } catch (e) {} finally { setLoading(false); }
        }

        function pick(n) { topic = n; el('selected').textContent = n; note('Selected ' + n); }

        async function produce() {
            if (!topic) return note('Select a topic first.', true);
            setLoading(true);
            try {
                const value = JSON.parse(el('value').value);
                const x = await api('/api/produce', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ topic: topic, key: el('key').value || null, value: value })
                });
                note(`Produced to ${x.topic}, partition ${x.partition}, offset ${x.offset}`);
                loadTopics();
            } catch (e) {
                if (e instanceof SyntaxError) note('Invalid JSON value.', true);
            } finally { setLoading(false); }
        }

        async function consume() {
            if (!topic) return note('Select a topic first.', true);
            setLoading(true);
            try {
                const x = await api(`/api/consume/${encodeURIComponent(topic)}?limit=${el('limit').value}`);
                el('messages').textContent = JSON.stringify(x.messages, null, 2);
                note(`Read ${x.messages.length} message(s)`);
            } catch (e) {} finally { setLoading(false); }
        }

        function copyMessages() {
            const text = el('messages').textContent;
            navigator.clipboard.writeText(text).then(() => note('Copied to clipboard!')).catch(() => note('Copy failed.', true));
        }

        function safe(s) { let d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
    </script>
</body>
</html>'''

@app.get('/')
def index():
    return HTML, 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.post('/api/connect')
def connect():
    b = request.get_json(silent=True) or {}
    servers = str(b.get('bootstrap_servers', '')).strip()
    if not servers:
        return jsonify(error='Bootstrap servers are required.'), 400
        
    c = build_kafka_config(b)
    try:
        m = AdminClient(c).list_topics(timeout=8)
        return jsonify(message=f'Connected to {m.cluster_id or servers} ({len(m.brokers)} broker(s))')
    except Exception as e:
        return jsonify(error=err(e)), 502

@app.get('/api/topics')
def topics():
    try:
        c = get_kafka_config()
        admin = AdminClient(c)
        m = admin.list_topics(timeout=8)
        
        def get_size(name, partitions):
            total = 0
            try:
                cons = Consumer({**c, 'group.id': f'ui-size-{name}-{time.time_ns()}', 'enable.auto.commit': False})
                for p in partitions:
                    try:
                        low, high = cons.get_watermark_offsets(TopicPartition(name, p), timeout=3, cached=True)
                        total += max(0, high - low)
                    except Exception: pass
                cons.close()
            except Exception: pass
            return {'name': name, 'partitions': len(partitions), 'records': total}

        rows = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(get_size, name, list(t.partitions.keys())) 
                       for name, t in m.topics.items() if not name.startswith('__') and not t.error]
            for f in futures:
                rows.append(f.result())
                
        rows.sort(key=lambda x: x['name'])
        return jsonify(topics=rows)
    except Exception as e:
        return jsonify(error=err(e)), 502

@app.post('/api/produce')
def produce():
    b = request.get_json(silent=True) or {}
    topic = str(b.get('topic', '')).strip()
    if not topic or 'value' not in b:
        return jsonify(error='Topic and value are required.'), 400
        
    try:
        config = get_kafka_config()
        p = get_producer(config)
        
        result = {}
        done = threading.Event()
        
        def delivered(error, msg):
            result.update(error=err(error) if error else None, topic=msg.topic(), partition=msg.partition(), offset=msg.offset())
            done.set()
            
        value = json.dumps(b['value'], separators=(',', ':'), ensure_ascii=False).encode()
        key = None if b.get('key') is None else str(b['key']).encode()
        
        p.produce(topic, key=key, value=value, headers={'content-type': 'application/json'}, on_delivery=delivered)
        p.flush(10)
        
        if not done.is_set() or result.get('error'):
            raise RuntimeError(result.get('error') or 'Delivery timed out')
            
        return jsonify(**result)
    except Exception as e:
        return jsonify(error=err(e)), 502

@app.get('/api/consume/<path:topic>')
def consume(topic):
    try:
        limit = max(1, min(int(request.args.get('limit', 20)), 200))
        config = get_kafka_config()
        
        c = Consumer({**config, 'group.id': f'ui-consume-{time.time_ns()}', 'enable.auto.commit': False})
        out = []
        
        try:
            m = c.list_topics(topic=topic, timeout=8)
            details = m.topics.get(topic)
            if not details or details.error:
                raise RuntimeError(f'Topic not found: {topic}')
                
            num_partitions = len(details.partitions)
            each = max(1, (limit + num_partitions - 1) // max(1, num_partitions))
            assigned = []
            
            for p in details.partitions:
                try:
                    low, high = c.get_watermark_offsets(TopicPartition(topic, p), timeout=5, cached=True)
                    if high > 0 and high > low:
                        assigned.append(TopicPartition(topic, p, max(low, high - each)))
                except Exception: pass
                
            c.assign(assigned)
            deadline = time.time() + 5
            while len(out) < limit and time.time() < deadline:
                msg = c.poll(0.5)
                if msg is None: continue
                if msg.error():
                    if msg.error().code() == -191: continue
                    raise KafkaException(msg.error())
                    
                raw = msg.value().decode('utf-8', errors='replace') if msg.value() else ''
                try: value = json.loads(raw)
                except json.JSONDecodeError: value = raw
                    
                headers = {}
                if msg.headers():
                    for k, v in msg.headers():
                        if v is not None:
                            try: headers[k] = v.decode('utf-8', errors='replace')
                            except Exception: headers[k] = str(v)
                        else: headers[k] = None
                        
                out.append({
                    'partition': msg.partition(), 'offset': msg.offset(), 'timestamp': msg.timestamp()[1],
                    'key': msg.key().decode('utf-8', errors='replace') if msg.key() else None,
                    'headers': headers, 'value': value
                })
                
            out.sort(key=lambda x: (x['timestamp'] or 0), reverse=True)
            return jsonify(messages=out[:limit])
        finally:
            c.close()
    except Exception as e:
        return jsonify(error=err(e)), 502

if __name__ == '__main__':
    app.run(host=os.getenv('HOST', '127.0.0.1'), port=int(os.getenv('PORT', '5000')), debug=os.getenv('FLASK_DEBUG') == '1')
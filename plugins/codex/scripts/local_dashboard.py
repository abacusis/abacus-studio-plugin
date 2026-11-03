"""Opt-in local observer. No transcripts, cloud calls, Git writes, or agent execution."""
import argparse
from contextlib import contextmanager
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parent))
from plugin_runtime import is_codex

ROLES = {'orchestrator': 'Engineering Lead', 'spec-writer': 'Product Planner', 'builder': 'Software Engineer',
         'verifier': 'QA Engineer', 'code-reviewer': 'Code Reviewer', 'security-reviewer': 'Security Engineer',
         'ui-reviewer': 'Visual Designer', 'ux-reviewer': 'UX Reviewer', 'readiness-reviewer': 'Release Reviewer'}
ACTIONS = ({'submit': '$abacus-submit', 'request-publish': '$abacus-request-publish'} if is_codex() else
           {'submit': '/abacus-studio:submit', 'request-publish': '/abacus-studio:request-publish'})
STALE_AFTER = 300
DASHBOARD_PROTOCOL = 2
SECRET = re.compile(r'(?i)(?:sb_secret_|sbp_|github_pat_|ghp_|sk-proj-|-----BEGIN |\b(?:password|api[_-]?key|token|secret)\s*[:=])')


def text(value, limit=200):
    if not isinstance(value, str) or SECRET.search(value):
        return ''
    return re.sub(r'[\x00-\x1f\x7f]', ' ', value).strip()[:limit]


def key(value):
    if not isinstance(value, str) or not value or len(value) > 300:
        raise ValueError('Missing bounded session or agent identity')
    return hashlib.sha256(value.encode()).hexdigest()[:24]


def safe_file(path):
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError('Unsafe dashboard file')
    return path


def storage(root, create=False):
    root = Path(root).resolve(strict=True)
    base = root / '.studio' / 'dashboard'
    for path in (root / '.studio', base):
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError('Unsafe dashboard directory')
        if create:
            path.mkdir(exist_ok=True, mode=0o700)
    return root, base


def atomic(path, value):
    safe_file(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='dashboard-')
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def git(root, *args):
    executable = shutil.which('git', path=os.defpath) or shutil.which('git')
    if not executable:
        raise ValueError('Git unavailable')
    env = {'PATH': os.defpath, 'GIT_OPTIONAL_LOCKS': '0', 'GIT_TERMINAL_PROMPT': '0'}
    for name in ('SYSTEMROOT', 'WINDIR', 'HOME'):
        if name in os.environ:
            env[name] = os.environ[name]
    result = subprocess.run([executable, '--no-optional-locks', '-c', 'core.fsmonitor=false',
                             '-C', str(root), *args], capture_output=True, env=env, timeout=5)
    if len(result.stdout) > 1024 * 1024:
        raise ValueError('Git result too large')
    return result


def enable(root, approved=False):
    if not approved:
        raise ValueError('Approval for workspace tracking and local server is required')
    root = Path(root).resolve(strict=True)
    top = git(root, 'rev-parse', '--show-toplevel')
    if top.returncode or Path(top.stdout.decode().strip()).resolve() != root:
        raise ValueError('Select one Git workspace root')
    if git(root, 'check-ignore', '-q', '.studio/dashboard/probe').returncode:
        raise ValueError('Dashboard metadata must be Git-ignored; approve adding .studio/ to local exclusions first')
    root, base = storage(root, True)
    config = safe_file(base / 'enabled.json')
    atomic(config, {'root': str(root), 'enabled': True, 'approved_at': time.time()})
    with connect(root):
        pass
    return root


def enabled(root):
    root, base = storage(root)
    path = safe_file(base / 'enabled.json')
    if not path.is_file() or path.stat().st_size > 4096:
        raise ValueError('Dashboard tracking is not enabled')
    config = json.loads(path.read_text())
    if config.get('root') != str(root) or config.get('enabled') is not True:
        raise ValueError('Dashboard tracking is not enabled for this workspace')
    return root, base


@contextmanager
def connect(root):
    root, base = storage(root)
    db_path = safe_file(base / 'activity.sqlite')
    for suffix in ('-journal', '-wal', '-shm'):
        safe_file(Path(str(db_path) + suffix))
    db = sqlite3.connect(db_path, timeout=1)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=DELETE')
    db.executescript('''
      CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, state TEXT, seen REAL);
      CREATE TABLE IF NOT EXISTS agents (session TEXT, id TEXT, role TEXT, state TEXT,
        seen REAL, started REAL, PRIMARY KEY(session,id));
      CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, session TEXT, role TEXT,
        kind TEXT, summary TEXT, file TEXT, source TEXT, time REAL);
      CREATE TABLE IF NOT EXISTS reports (session TEXT, role TEXT, body TEXT, time REAL,
        PRIMARY KEY(session,role));
      CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, action TEXT, state TEXT,
        session TEXT, time REAL);
    ''')
    db_path.chmod(0o600)
    try:
        with db:
            yield db
    finally:
        db.close()


def event(db, sid, role, kind, summary, file=None, source='hook'):
    db.execute('INSERT INTO events(session,role,kind,summary,file,source,time) VALUES(?,?,?,?,?,?,?)',
               (sid, role, kind, summary, file, source, time.time()))
    db.execute('DELETE FROM events WHERE id < (SELECT COALESCE(MAX(id),0)-2000 FROM events)')


def safe_path(root, value):
    if not isinstance(value, str) or len(value) > 500:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    try:
        relative = path.relative_to(root)
    except ValueError:
        return None
    if '..' in relative.parts or any(part.startswith('.') or part.lower() in
        ('node_modules', 'dist', 'build', 'coverage', 'vendor', 'venv') for part in relative.parts):
        return None
    if any(word in relative.name.lower() for word in ('secret', 'credential', 'password', 'token')):
        return None
    if relative.suffix.lower() in ('.pem', '.key', '.log', '.p12', '.pfx'):
        return None
    if any(p.is_symlink() for p in (path, *list(path.parents)[:len(relative.parts)])):
        return None
    name = text(relative.as_posix(), 240)
    return name or None


def observe(payload):
    """Only explicitly enabled workspaces; discard prompts, transcripts and tool output."""
    if not isinstance(payload, dict) or not isinstance(payload.get('cwd'), str) or not Path(payload['cwd']).is_absolute():
        return None
    root, _ = enabled(payload['cwd'])
    sid = key(payload.get('session_id'))
    kind = payload.get('hook_event_name')
    allowed = {'SessionStart', 'UserPromptSubmit', 'SubagentStart', 'SubagentStop', 'PreToolUse',
               'PostToolUse', 'PostToolUseFailure', 'Stop', 'StopFailure', 'SessionEnd'}
    if kind not in allowed:
        return None
    aid = key(payload['agent_id']) if payload.get('agent_id') else None
    role = 'orchestrator'
    now = time.time()
    context = None
    with connect(root) as db:
        db.execute('INSERT OR IGNORE INTO sessions VALUES(?,?,?)', (sid, 'idle', now))
        if kind in ('SubagentStart', 'SubagentStop'):
            role = str(payload.get('agent_type', '')).removeprefix('abacus-studio:')
            if not str(payload.get('agent_type', '')).startswith('abacus-studio:') or role not in ROLES or role == 'orchestrator' or not aid:
                return None
            state = 'working' if kind == 'SubagentStart' else 'returned'
            db.execute('INSERT INTO agents VALUES(?,?,?,?,?,?) ON CONFLICT(session,id) DO UPDATE SET state=excluded.state,seen=excluded.seen,started=CASE WHEN excluded.state="working" THEN excluded.started ELSE agents.started END',
                       (sid, aid, role, state, now, now))
            if state == 'working':
                assigned = db.execute('SELECT body FROM reports WHERE session=? AND role=?', (sid,role)).fetchone()
                if assigned:
                    goal = json.loads(assigned['body'])
                    if goal.get('status') == 'queued' and not goal.get('checks') and not goal.get('findings'):
                        # Explicitly assigned goal belongs to this start, not old check evidence.
                        goal['status'] = ''
                        db.execute('UPDATE reports SET body=?,time=? WHERE session=? AND role=?', (json.dumps(goal),now,sid,role))
            event(db, sid, role, kind, 'Agent started' if state == 'working' else 'Agent returned · outcome not inferred')
        elif kind in ('PreToolUse', 'PostToolUse', 'PostToolUseFailure'):
            if aid:
                agent = db.execute('SELECT role FROM agents WHERE session=? AND id=?', (sid, aid)).fetchone()
                if not agent:
                    return None
                role = agent['role']
                db.execute('UPDATE agents SET seen=? WHERE session=? AND id=?', (now, sid, aid))
            tool = payload.get('tool_name')
            labels = {'Read': 'Read source', 'Grep': 'Searched source', 'Glob': 'Located files',
                      'Edit': 'Edited a file', 'Write': 'Wrote a file', 'Bash': 'Command returned · result not inferred',
                      'Agent': 'Delegation returned', 'Task': 'Delegation returned'}
            if tool not in labels:
                return None
            if kind == 'PreToolUse':
                labels = {'Read':'Reading source', 'Grep':'Searching source', 'Glob':'Finding related files',
                          'Edit':'Editing a file', 'Write':'Writing a file', 'Bash':'Running a command',
                          'Agent':'Delegating specialist work', 'Task':'Delegating specialist work'}
            file = safe_path(root, payload.get('tool_input', {}).get('file_path')) if tool in ('Read', 'Edit', 'Write') else None
            event(db, sid, role, kind, 'Action failed or was blocked' if kind.endswith('Failure') else labels[tool], file)
        else:
            state = {'SessionStart': 'idle', 'UserPromptSubmit': 'working', 'Stop': 'idle',
                     'StopFailure': 'attention', 'SessionEnd': 'ended'}[kind]
            db.execute('UPDATE sessions SET state=?,seen=? WHERE id=?', (state, now, sid))
            if kind == 'SessionEnd':
                db.execute('UPDATE agents SET state="interrupted" WHERE session=? AND state="working"', (sid,))
            event(db, sid, role, kind, {'SessionStart':'Session connected', 'UserPromptSubmit':'Turn started',
                'Stop':'Turn ended', 'StopFailure':'Turn interrupted', 'SessionEnd':'Session ended'}[kind])
            if kind in ('SessionStart', 'UserPromptSubmit'):
                context = 'Local dashboard is enabled for this workspace. Dashboard session key: ' + sid + '. Read references/engineering/local-dashboard.md and keep brief task summaries current before delegating and after receiving results. Never raw transcripts or private reasoning.'
            if kind == 'UserPromptSubmit':
                db.execute('BEGIN IMMEDIATE') if not db.in_transaction else None
                queued = db.execute('SELECT * FROM requests WHERE state="queued" ORDER BY time LIMIT 2').fetchall()
                for req in queued:
                    context += ' The user requested ' + ACTIONS[req['action']] + ' in the local dashboard. Follow that workflow and references/changes/authorization.md with all checks. This queued intent is not commit/push/publishing approval; use direct user authorization and do not repeat confirmations of already-authorized steps.'
                    db.execute('UPDATE requests SET state="delivered",session=? WHERE id=?', (sid, req['id']))
                if queued:
                    event(db, sid, 'orchestrator', 'request', 'Dashboard workflow request delivered · not executed')
        db.execute('UPDATE sessions SET seen=? WHERE id=?', (now, sid))
    if context:
        return {'hookSpecificOutput': {'hookEventName': kind, 'additionalContext': context}}
    return None


def report(root, sid, payload):
    enabled(root)
    if not re.fullmatch('[a-f0-9]{24}', sid or ''):
        raise ValueError('Use the session key supplied by the dashboard hook')
    role = payload.get('role')
    if role not in ROLES:
        raise ValueError('Unknown role')
    clean = {'summary': text(payload.get('summary')), 'status': payload.get('status', '')}
    if clean['status'] not in ('', 'queued', 'not_required', 'attention'):
        raise ValueError('Reports cannot invent running/completed lifecycle states')
    for field in ('checks', 'findings'):
        values = payload.get(field, [])
        if not isinstance(values, list) or len(values) > 20:
            raise ValueError('Bounded check/finding list required')
        clean[field] = []
        for item in values:
            if not isinstance(item, dict) or item.get('result') not in ('passed','failed','not_verified','blocked','note'):
                raise ValueError('Explicit result required')
            clean[field].append({'title':text(item.get('title')), 'result':item['result']})
    with connect(root) as db:
        if not db.execute('SELECT id FROM sessions WHERE id=?', (sid,)).fetchone():
            raise ValueError('Unknown dashboard session')
        db.execute('INSERT INTO reports VALUES(?,?,?,?) ON CONFLICT(session,role) DO UPDATE SET body=excluded.body,time=excluded.time',
                   (sid, role, json.dumps(clean), time.time()))
        event(db, sid, role, 'report', clean['summary'] or 'Coordinator report updated', source='coordinator')


def git_status(root):
    try:
        raw = git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=normal')
        if raw.returncode:
            raise ValueError()
        files, hidden = [], 0
        parts = iter(raw.stdout.decode('utf-8', 'replace').split('\0'))
        for item in parts:
            if len(item) < 4:
                continue
            flags, path = item[:2], item[3:]
            if 'R' in flags or 'C' in flags:
                next(parts, None)
            safe = safe_path(root, path)
            if safe:
                files.append({'path':safe, 'status':flags.strip(), 'staged': flags[0] not in (' ', '?')})
            else:
                hidden += 1
        counts = git(root, 'rev-list', '--left-right', '--count', 'HEAD...@{upstream}')
        ahead, behind = (map(int, counts.stdout.split()) if counts.returncode == 0 else (None, None))
        head = git(root, 'rev-parse', '--short', 'HEAD')
        return {'available':True, 'files':files[:100], 'visible_count':len(files), 'hidden_count':hidden,
                'truncated':len(files)>100, 'ahead':ahead, 'behind':behind,
                'head':text(head.stdout.decode().strip(), 20), 'cached_only':True,
                'note':'Cached upstream comparison only. GitHub and publication have not been checked.'}
    except Exception:
        return {'available':False, 'files':[], 'ahead':None, 'behind':None,
                'note':'Git status unavailable. Nothing has been fetched, saved or published.'}


def snapshot(root):
    root, _ = enabled(root)
    now = time.time()
    with connect(root) as db:
        session = db.execute('SELECT * FROM sessions ORDER BY seen DESC LIMIT 1').fetchone()
        sid = session['id'] if session else None
        events = [dict(row) for row in db.execute('SELECT role,kind,summary,file,source,time FROM events WHERE session=? ORDER BY id DESC LIMIT 150', (sid,))]
        agents = []
        for role, label in ROLES.items():
            rows = db.execute('SELECT * FROM agents WHERE session=? AND role=? ORDER BY seen DESC', (sid,role)).fetchall()
            active = [row for row in rows if row['state']=='working']
            fresh = [row for row in active if now-row['seen'] <= STALE_AFTER and session['state'] != 'ended']
            status = 'working' if fresh else 'stale' if active else rows[0]['state'] if rows else 'idle'
            if role == 'orchestrator' and session:
                status = 'stale' if now-session['seen']>STALE_AFTER and session['state']!='ended' else session['state']
            stored = db.execute('SELECT body,time FROM reports WHERE session=? AND role=?', (sid,role)).fetchone()
            body = json.loads(stored['body']) if stored else {'summary':'', 'checks':[], 'findings':[]}
            report_stale = bool(stored and rows and stored['time'] < max(row['started'] for row in rows))
            if status == 'idle' and stored and not report_stale and body.get('status'):
                status = body['status']
            activity = next((item for item in events if item['role'] == role and item['kind'] in
                            ('PreToolUse','PostToolUse','PostToolUseFailure')), None)
            # A previous invocation's last action is not this invocation's work.
            if activity and rows and activity['time'] < max(row['started'] for row in rows):
                activity = None
            agents.append({'role':role,'name':label,'status':status,'active_count':len(fresh),
                           'participated': bool(rows) or role == 'orchestrator' or bool(stored),
                           'invoked': bool(rows),
                           'activity':activity,
                           'report':body,'report_stale':report_stale,'report_time': stored['time'] if stored else None})
        requests = [dict(row) for row in db.execute('SELECT id,action,state,time FROM requests ORDER BY time DESC LIMIT 10')]
    return {'dashboard_protocol':DASHBOARD_PROTOCOL, 'project':text(root.name), 'session':dict(session) if session else None,
            'agents':agents,'events':events,'git':git_status(root),'requests':requests,
            'observed_at':now,'stale_after':STALE_AFTER,
            'note':'Hook-observed activity and coordinator-reported checks. No private AI reasoning.'}


def queue(root, action):
    enabled(root)
    if action not in ACTIONS:
        raise ValueError('Unknown workflow request')
    with connect(root) as db:
        db.execute('BEGIN IMMEDIATE')
        previous = db.execute('SELECT id FROM requests WHERE action=? AND state="queued"', (action,)).fetchone()
        if previous:
            return previous['id']
        identity = secrets.token_hex(12)
        db.execute('INSERT INTO requests VALUES(?,?,"queued",NULL,?)',(identity,action,time.time()))
    return identity


def handler(root, capability):
    assets = Path(__file__).resolve().parents[1] / 'dashboard'
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Never log capability URLs, request bodies or errors.

        def send(self, status, data, kind='application/json'):
            if not isinstance(data, bytes):
                data = json.dumps(data).encode()
            self.send_response(status)
            for name, value in {'Content-Type':kind, 'Content-Length':str(len(data)),
                'Cache-Control':'no-store', 'Referrer-Policy':'no-referrer', 'X-Content-Type-Options':'nosniff',
                'Content-Security-Policy':"default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"}.items():
                self.send_header(name,value)
            self.end_headers()
            self.wfile.write(data)

        def route(self):
            expected = '127.0.0.1:' + str(self.server.server_port)
            if self.headers.get('Host') != expected or self.headers.get('Origin', 'http://'+expected) != 'http://'+expected:
                self.send(403, {'error':'Local origin required'}); return None
            path = urlsplit(self.path).path.split('/')
            if len(path)<3 or not hmac.compare_digest(path[1],capability):
                self.send(404, {'error':'Not found'}); return None
            return '/'.join(path[2:])

        def do_GET(self):
            route = self.route()
            if route is None:
                return
            try:
                if route == 'api/state':
                    self.send(200,snapshot(root))
                elif route in ('','index.html','app.js','style.css'):
                    file = safe_file(assets / (route or 'index.html'))
                    self.send(200,file.read_bytes(), {'app.js':'text/javascript; charset=utf-8','style.css':'text/css; charset=utf-8'}.get(route,'text/html; charset=utf-8'))
                else:
                    self.send(404,{'error':'Not found'})
            except Exception:
                self.send(503,{'error':'Local activity unavailable. Check the dashboard helper.'})

        def do_POST(self):
            route = self.route()
            if route is None:
                return
            if route not in ('api/request','api/close') or self.headers.get('Origin') != 'http://127.0.0.1:'+str(self.server.server_port):
                self.send(403,{'error':'Workflow request not allowed'}); return
            if route == 'api/close':
                self.send(200,{'status':'server_stopping'})
                threading.Thread(target=self.server.shutdown,daemon=True).start()
                return
            try:
                length = int(self.headers.get('Content-Length','0'))
                if not 0 < length <= 4096:
                    raise ValueError()
                value = json.loads(self.rfile.read(length))
                identity = queue(root,value['action'])
                self.send(202,{'id':identity,'state':'queued','message':'Return to your coding tool and send Continue. Existing workflow checks and approvals still apply.'})
            except Exception:
                self.send(400,{'error':'Use Submit changes or Request publish; no command execution is supported.'})
    return Handler


def serve(root):
    root, base = enabled(root)
    capability = secrets.token_hex(24)
    server = ThreadingHTTPServer(('127.0.0.1',0), handler(root,capability))
    server.daemon_threads = True
    url = 'http://127.0.0.1:'+str(server.server_port)+'/'+capability+'/'
    state = {'url':url,'pid':os.getpid(),'started_at':time.time()}
    atomic(base/'server.json',state)
    try:
        server.serve_forever(poll_interval=.3)
    finally:
        server.server_close()
        # Preserve historical metadata; never claim it proves the process is live.


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=['start','serve','hook','report','state','disable','stop'])
    parser.add_argument('--workspace')
    parser.add_argument('--approved',action='store_true')
    parser.add_argument('--session')
    args = parser.parse_args()
    if args.action == 'hook':
        try:
            raw = sys.stdin.buffer.read(1024*1024+1)
            if len(raw)>1024*1024:
                return 0
            result = observe(json.loads(raw))
            if result:
                print(json.dumps(result))
        except Exception:
            pass  # Observation cannot block or disclose failures to the session.
        return 0
    try:
        if not args.workspace:
            raise ValueError('Select the authorized workspace')
        if args.action in ('start','stop'):
            import urllib.request
            class NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, *args, **kwargs):
                    raise ValueError('Local dashboard redirect rejected')
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
            if args.action == 'stop':
                if not args.approved: raise ValueError('Approval required')
                root,base=enabled(args.workspace)
                old=json.loads(safe_file(base/'server.json').read_text())
                url=old.get('url','')
                if not re.fullmatch(r'http://127\.0\.0\.1:[0-9]+/[a-f0-9]{48}/',url):
                    raise ValueError('Invalid local dashboard address')
                origin='http://'+urlsplit(url).netloc
                req=urllib.request.Request(url+'api/close',data=b'{}',headers={'Origin':origin},method='POST')
                with opener.open(req,timeout=2) as response:
                    print(response.read(4096).decode())
                return 0
            root = enable(args.workspace,args.approved)
            _,base = storage(root)
            state = safe_file(base/'server.json')
            if state.exists() and state.stat().st_size<4096:
                old = json.loads(state.read_text())
                # Do not connect to arbitrary URLs from repository metadata.
                url = old.get('url','')
                if re.fullmatch(r'http://127\.0\.0\.1:[0-9]+/[a-f0-9]{48}/',url):
                    legacy_running=False
                    try:
                        with opener.open(url+'api/state',timeout=1) as response:
                            if response.status == 200:
                                running=json.loads(response.read(1024*1024))
                                if running.get('dashboard_protocol') == DASHBOARD_PROTOCOL:
                                    print(json.dumps({'url':url,'reused':True})); return 0
                                legacy_running=True
                                # Replace only the dashboard identified by this workspace's
                                # private capability, never a guessed port or another listener.
                                origin='http://'+urlsplit(url).netloc
                                req=urllib.request.Request(url+'api/close',data=b'{}',headers={'Origin':origin},method='POST')
                                with opener.open(req,timeout=2) as closed:
                                    if closed.status != 200: raise ValueError('Close the previous dashboard before reopening it')
                                legacy_running=False
                    except Exception:
                        pass
                    if legacy_running:
                        raise ValueError('Close the previous dashboard before reopening it')
            env = {'PATH':os.defpath}
            for name in ('SYSTEMROOT','WINDIR'):
                if name in os.environ: env[name]=os.environ[name]
            process = subprocess.Popen([sys.executable,'-I',str(Path(__file__).resolve()),'serve','--workspace',str(root)],
                cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
            for _ in range(40):
                if process.poll() is not None:
                    raise ValueError('Local dashboard server did not start')
                if state.exists():
                    value=json.loads(state.read_text())
                    if value.get('pid')==process.pid:
                        print(json.dumps(value)); return 0
                time.sleep(.05)
            raise ValueError('Dashboard start timed out; inspect its own process before retrying')
        elif args.action == 'serve':
            serve(args.workspace)
        elif args.action == 'report':
            raw=sys.stdin.read(8193)
            if len(raw)>8192: raise ValueError('Report too large')
            report(args.workspace,args.session,json.loads(raw))
            print(json.dumps({'status':'recorded','source':'coordinator'}))
        elif args.action == 'state':
            print(json.dumps(snapshot(args.workspace)))
        elif args.action == 'disable':
            if not args.approved: raise ValueError('Approval required')
            root,base=enabled(args.workspace)
            atomic(base/'enabled.json',{'root':str(root),'enabled':False})
            print(json.dumps({'status':'tracking_disabled','note':'Existing dashboard/history remains; stop only its identified process if requested.'}))
    except Exception as error:
        print(json.dumps({'status':'unavailable','message':str(error) if isinstance(error,ValueError) else 'Dashboard unavailable; no source, Git or cloud operation was performed.'}))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

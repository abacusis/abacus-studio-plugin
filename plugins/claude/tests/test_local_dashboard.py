import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError

ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('local_dashboard',ROOT/'scripts/local_dashboard.py')
dash=importlib.util.module_from_spec(spec)
spec.loader.exec_module(dash)


class DashboardTests(unittest.TestCase):
    def test_display_names_match_client_guidance_and_frontend_without_new_ids(self):
        expected = {'orchestrator': 'Engineering Lead', 'spec-writer': 'Product Planner',
                    'builder': 'Software Engineer', 'verifier': 'QA Engineer',
                    'code-reviewer': 'Code Reviewer', 'security-reviewer': 'Security Engineer',
                    'ui-reviewer': 'Visual Designer', 'ux-reviewer': 'UX Reviewer',
                    'readiness-reviewer': 'Release Reviewer'}
        self.assertEqual(dash.ROLES, expected)
        import re
        script = (ROOT/'dashboard/app.js').read_text()
        names = re.search(r'const names=\{([^}]+)\}', script).group(1)
        rendered = {
            quoted or bare: label for quoted, bare, label in
            re.findall(r"(?:'([^']+)'|([a-z]+)):'([^']+)'", names)}
        self.assertEqual(rendered, expected)
        guidance = (ROOT/'references/client-communication.md').read_text()
        for role, label in expected.items():
            self.assertIn(f'| {role} | {label} |', guidance)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name).resolve()
        self.git('init','-b','main')
        (self.root/'.gitignore').write_text('.studio/\n')
        (self.root/'app.txt').write_text('initial\n')
        self.git('add','.')
        self.git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','Initial')

    def tearDown(self):
        self.temp.cleanup()

    def git(self,*args):
        return subprocess.run(['git','-C',str(self.root),*args],check=True,capture_output=True,text=True).stdout.strip()

    def observed(self,event,**extra):
        return dash.observe({'cwd':str(self.root),'session_id':'test-session','hook_event_name':event,**extra})

    def enable(self):
        dash.enable(self.root,True)
        self.observed('SessionStart')

    def test_tracking_requires_approval_and_ignore_and_has_no_disabled_side_effect(self):
        with self.assertRaises(ValueError):dash.enable(self.root,False)
        with self.assertRaises(ValueError):self.observed('SessionStart')
        self.assertFalse((self.root/'.studio').exists())
        (self.root/'.gitignore').write_text('')
        with self.assertRaises(ValueError):dash.enable(self.root,True)
        self.assertFalse((self.root/'.studio').exists())
        self.assertIsNone(dash.observe({'hook_event_name':'SessionStart'}))

    def test_lifecycle_concurrency_stale_end_and_return_is_not_pass(self):
        self.enable()
        for aid in ('one','two'):
            self.observed('SubagentStart',agent_id=aid,agent_type='abacus-studio:builder')
        def builder():return next(a for a in dash.snapshot(self.root)['agents'] if a['role']=='builder')
        self.assertEqual(builder()['active_count'],2)
        self.observed('SubagentStop',agent_id='one',agent_type='abacus-studio:builder',last_assistant_message='password=private-do-not-store')
        self.assertEqual(builder()['active_count'],1)
        with dash.connect(self.root) as db:db.execute('UPDATE agents SET seen=?',(time.time()-1000,))
        self.assertEqual(builder()['status'],'stale')
        self.observed('SessionEnd')
        self.assertEqual(builder()['active_count'],0)
        self.assertNotEqual(builder()['status'],'working')
        raw=(self.root/'.studio/dashboard/activity.sqlite').read_bytes()
        self.assertNotIn(b'private-do-not-store',raw)
        self.assertEqual(len(dash.snapshot(self.root)['agents']),9)

    def test_hook_filters_metadata_and_unknown_agents(self):
        self.enable()
        self.observed('SubagentStart',agent_id='one',agent_type='other:builder')
        self.observed('SubagentStart',agent_id='two',agent_type='abacus-studio:builder')
        for path in ('.env','../private.txt','credentials.json','secret.key'):
            self.observed('PostToolUse',agent_id='two',tool_name='Write',tool_input={'file_path':path,'content':'do-not-save-this-content'},tool_response={'output':'do-not-save-this-output'})
        self.observed('PostToolUse',agent_id='two',tool_name='Edit',tool_input={'file_path':str(self.root/'app.txt')})
        state=dash.snapshot(self.root)
        paths=[e['file'] for e in state['events'] if e['file']]
        self.assertEqual(paths,['app.txt'])
        raw=(self.root/'.studio/dashboard/activity.sqlite').read_bytes()
        self.assertNotIn(b'do-not-save-this',raw)
        self.assertIsNone(dash.safe_path(self.root,str(self.root.parent/'private.txt')))

    def test_current_action_and_participation_without_sensitive_tool_bodies(self):
        self.enable()
        self.assertFalse(next(a for a in dash.snapshot(self.root)['agents'] if a['role']=='builder')['participated'])
        self.observed('SubagentStart',agent_id='builder-1',agent_type='abacus-studio:builder')
        self.observed('PreToolUse',agent_id='builder-1',tool_name='Read',tool_input={'file_path':str(self.root/'app.txt'),'content':'private-content-not-recorded'})
        builder=next(a for a in dash.snapshot(self.root)['agents'] if a['role']=='builder')
        self.assertTrue(builder['participated'])
        self.assertEqual(builder['activity']['summary'],'Reading source')
        self.assertEqual(builder['activity']['file'],'app.txt')
        self.observed('PreToolUse',agent_id='builder-1',tool_name='Bash',tool_input={'command':'echo private-command-not-recorded'})
        builder=next(a for a in dash.snapshot(self.root)['agents'] if a['role']=='builder')
        self.assertEqual(builder['activity']['summary'],'Running a command')
        self.assertIsNone(builder['activity']['file'])
        self.observed('SubagentStop',agent_id='builder-1',agent_type='abacus-studio:builder')
        self.assertTrue(next(a for a in dash.snapshot(self.root)['agents'] if a['role']=='builder')['participated'])
        self.observed('SubagentStart',agent_id='builder-2',agent_type='abacus-studio:builder')
        self.assertIsNone(next(a for a in dash.snapshot(self.root)['agents'] if a['role']=='builder')['activity'])
        raw=(self.root/'.studio/dashboard/activity.sqlite').read_bytes()
        self.assertNotIn(b'private-command-not-recorded',raw)
        self.assertNotIn(b'private-content-not-recorded',raw)

    def test_report_provenance_validation_and_staleness(self):
        self.enable()
        sid=dash.key('test-session')
        with self.assertRaises(ValueError):dash.report(self.root,sid,{'role':'builder','status':'working'})
        dash.report(self.root,sid,{'role':'builder','summary':'Implement form','checks':[{'title':'Keyboard flow','result':'not_verified'}]})
        self.observed('SubagentStart',agent_id='new',agent_type='abacus-studio:builder')
        current=next(a for a in dash.snapshot(self.root)['agents'] if a['role']=='builder')
        self.assertTrue(current['report_stale'])
        self.assertEqual(current['report']['checks'][0]['result'],'not_verified')
        self.assertEqual(dash.snapshot(self.root)['events'][1]['source'],'coordinator')

    def test_assigned_goal_survives_start_but_old_checks_are_not_refreshed(self):
        self.enable()
        dash.report(self.root,dash.key('test-session'),{'role':'builder','summary':'Add validation','status':'queued'})
        queued=next(a for a in dash.snapshot(self.root)['agents'] if a['role']=='builder')
        self.assertTrue(queued['participated'])
        self.assertFalse(queued['invoked'])
        self.observed('SubagentStart',agent_id='one',agent_type='abacus-studio:builder')
        builder=next(a for a in dash.snapshot(self.root)['agents'] if a['role']=='builder')
        self.assertFalse(builder['report_stale'])
        self.assertTrue(builder['invoked'])
        self.assertEqual(builder['report']['summary'],'Add validation')
        self.observed('SubagentStop',agent_id='one',agent_type='abacus-studio:builder')
        self.observed('SubagentStart',agent_id='two',agent_type='abacus-studio:builder')
        self.assertTrue(next(a for a in dash.snapshot(self.root)['agents'] if a['role']=='builder')['report_stale'])
        dash.report(self.root,dash.key('test-session'),{'role':'verifier','summary':'Old evidence','status':'queued','checks':[{'title':'Existing test','result':'passed'}]})
        self.observed('SubagentStart',agent_id='three',agent_type='abacus-studio:verifier')
        self.assertTrue(next(a for a in dash.snapshot(self.root)['agents'] if a['role']=='verifier')['report_stale'])

    def test_git_local_changes_upstream_unknown_and_cached_ahead(self):
        self.enable()
        (self.root/'app.txt').write_text('changed\n')
        (self.root/'new.txt').write_text('new\n')
        (self.root/'.env.local').write_text('private fixture value')
        state=dash.git_status(self.root)
        self.assertIsNone(state['ahead'])
        self.assertEqual({f['path'] for f in state['files']},{'app.txt','new.txt'})
        self.assertEqual(state['hidden_count'],1)
        self.git('remote','add','origin','https://example.invalid/no-network.git')
        base=self.git('rev-parse','HEAD')
        self.git('update-ref','refs/remotes/origin/main',base)
        self.git('branch','--set-upstream-to','origin/main','main')
        self.git('add','app.txt')
        self.git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','Local only')
        self.assertEqual(dash.git_status(self.root)['ahead'],1)
        self.assertEqual(self.git('rev-parse','refs/remotes/origin/main'),base)
        self.assertTrue(dash.git_status(self.root)['cached_only'])

    def test_requests_are_allowlisted_idempotent_and_handed_off_once(self):
        self.enable()
        identity=dash.queue(self.root,'submit')
        self.assertEqual(identity,dash.queue(self.root,'submit'))
        with self.assertRaises(ValueError):dash.queue(self.root,'git push')
        injected=self.observed('UserPromptSubmit')['hookSpecificOutput']['additionalContext']
        self.assertIn('/abacus-studio:submit',injected)
        self.assertIn('not commit/push/publishing approval',injected)
        self.assertNotIn('/abacus-studio:submit',self.observed('UserPromptSubmit')['hookSpecificOutput']['additionalContext'])
        self.assertEqual(dash.snapshot(self.root)['requests'][0]['state'],'delivered')
        self.assertEqual(self.git('status','--porcelain'),'')

    def test_storage_symlinks_rejected(self):
        (self.root/'.studio').symlink_to(self.root.parent,target_is_directory=True)
        with self.assertRaises(ValueError):dash.enable(self.root,True)

    def test_observer_cli_failure_is_silent_and_nonblocking(self):
        result=subprocess.run([sys.executable,'-I',str(ROOT/'scripts/local_dashboard.py'),'hook'],input=b'not-json',capture_output=True)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'',b''))

    def test_http_capability_origin_csp_and_no_arbitrary_commands(self):
        self.enable()
        server=ThreadingHTTPServer(('127.0.0.1',0),dash.handler(self.root,'test-capability'))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        origin='http://127.0.0.1:'+str(server.server_port)
        opener=build_opener(ProxyHandler({}))
        def request(path,body=None,**headers):
            try:
                return opener.open(Request(origin+path,data=body,headers=headers),timeout=3)
            except HTTPError as error:
                error.read();error.close()
                raise
        try:
            with request('/test-capability/') as response:
                self.assertIn(b'Your AI team',response.read())
                self.assertIn("frame-ancestors 'none'",response.headers['Content-Security-Policy'])
            for path in ('/','/wrong/api/state','/test-capability/../activity.sqlite'):
                with self.assertRaises(HTTPError):request(path)
            with self.assertRaises(HTTPError):request('/test-capability/api/state',Origin='https://evil.invalid')
            with self.assertRaises(HTTPError):request('/test-capability/api/state',Host='evil.invalid')
            with self.assertRaises(HTTPError):request('/test-capability/api/request',b'{"action":"submit"}',Origin='https://evil.invalid')
            with self.assertRaises(HTTPError):request('/test-capability/api/request',b'{"action":"shell"}',Origin=origin)
            with request('/test-capability/api/request',b'{"action":"submit"}',Origin=origin) as response:
                self.assertEqual(response.status,202)
            self.assertEqual(self.git('status','--porcelain'),'')
        finally:
            server.shutdown();server.server_close();thread.join(3)

    def test_start_replaces_only_the_identified_legacy_dashboard(self):
        self.enable()
        capability='a'*48
        class Legacy(dash.handler(self.root,capability)):
            def do_GET(self):
                if self.path == '/'+capability+'/api/state':
                    self.send(200,{'dashboard_protocol':1})
                else:
                    super().do_GET()
        server=ThreadingHTTPServer(('127.0.0.1',0),Legacy)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        legacy_url=f'http://127.0.0.1:{server.server_port}/{capability}/'
        dash.atomic(self.root/'.studio/dashboard/server.json',{'url':legacy_url,'pid':-1})
        command=[sys.executable,'-I',str(ROOT/'scripts/local_dashboard.py')]
        try:
            result=subprocess.run(command+['start','--workspace',str(self.root),'--approved'],check=True,capture_output=True,text=True,timeout=8)
            new=json.loads(result.stdout)
            self.assertNotEqual(new['url'],legacy_url)
            thread.join(2)
            self.assertFalse(thread.is_alive())
            opener=build_opener(ProxyHandler({}))
            with opener.open(new['url']+'api/state',timeout=3) as response:
                self.assertEqual(json.load(response)['dashboard_protocol'],dash.DASHBOARD_PROTOCOL)
            reuse=subprocess.run(command+['start','--workspace',str(self.root),'--approved'],check=True,capture_output=True,text=True,timeout=5)
            self.assertTrue(json.loads(reuse.stdout)['reused'])
        finally:
            subprocess.run(command+['stop','--workspace',str(self.root),'--approved'],capture_output=True,timeout=5)
            server.shutdown();server.server_close();thread.join(3)


if __name__=='__main__':unittest.main()

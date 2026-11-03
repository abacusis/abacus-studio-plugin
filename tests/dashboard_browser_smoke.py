"""Optional browser smoke test. Run with an already approved Playwright Python.

All application activity is an explicitly illustrative temporary fixture.
No client application, remote repository, or cloud service is used.
"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]


def main():
    from playwright.sync_api import sync_playwright, expect
    spec = importlib.util.spec_from_file_location('dashboard', REPO / 'scripts/local_dashboard.py')
    dashboard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dashboard)
    output = Path(tempfile.mkdtemp(prefix='abacus-coordination-map-')).resolve()
    root = output / 'Illustrative workspace'
    root.mkdir()
    def git(*args):
        return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True)
    git('init', '-b', 'main')
    (root / '.gitignore').write_text('.studio/\n')
    (root / 'SettingsForm.tsx').write_text('// illustrative fixture\n')
    git('add', '.')
    git('-c', 'user.name=Dashboard QA', '-c', 'user.email=qa@example.invalid', 'commit', '-m', 'Fixture')
    helper = [sys.executable, '-I', str(REPO / 'scripts/local_dashboard.py')]
    result = subprocess.run(helper + ['start', '--workspace', str(root), '--approved'], check=True, capture_output=True, text=True)
    url = json.loads(result.stdout)['url']
    sid = 'illustrative-test'
    def emit(kind, **extra):
        return dashboard.observe(dict(cwd=str(root), session_id=sid, hook_event_name=kind, **extra))
    def report(role, summary):
        dashboard.report(root, dashboard.key(sid), dict(role=role, summary=summary))
    def start(role):
        emit('SubagentStart', agent_id=role, agent_type='abacus-studio:' + role)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': 1280, 'height': 800}, device_scale_factor=1)
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            expect(page.locator('.agent:visible')).to_have_count(1)
            emit('SessionStart'); emit('UserPromptSubmit')
            report('orchestrator', 'Illustrative preview · Add project settings')
            page.evaluate('() => refresh()')
            start('spec-writer'); report('spec-writer', 'Define who can edit project settings')
            page.evaluate('() => refresh()')
            expect(page.locator('.agent:visible')).to_have_count(2, timeout=10000)
            expect(page.locator('.connection')).to_have_count(1)
            expect(page.locator('.handoff-pulse[data-direction="assign"]')).to_have_count(1)
            expect(page.locator('#handoff-status')).to_contain_text('Engineering Lead → Product Planner')
            page.wait_for_timeout(1200)
            page.evaluate('() => refresh()')
            expect(page.locator('.handoff-pulse')).to_have_count(0)
            emit('SubagentStop', agent_id='spec-writer', agent_type='abacus-studio:spec-writer')
            report('spec-writer', 'Requirements recorded; admin access agreed')
            page.evaluate('() => refresh()')
            expect(page.locator('.handoff-pulse[data-direction="return"]')).to_have_count(1)
            expect(page.locator('#handoff-status')).to_contain_text('Product Planner → Engineering Lead')
            page.emulate_media(reduced_motion='reduce')
            expect(page.locator('.handoff-pulse')).to_have_count(0)
            start('builder'); report('builder', 'Add required-name validation')
            start('security-reviewer'); report('security-reviewer', 'Review settings access rules')
            emit('PreToolUse', agent_id='builder', tool_name='Read', tool_input={'file_path': str(root / 'SettingsForm.tsx')})
            expect(page.locator('.agent:visible')).to_have_count(4, timeout=10000)
            expect(page.locator('.connection')).to_have_count(3)
            expect(page.locator('.handoff-pulse')).to_have_count(0)
            for path in page.locator('.connection').all():
                assert path.get_attribute('d').startswith('M ')
                assert path.evaluate('(el)=>el.getTotalLength()') > 30
            builder = page.get_by_role('button', name='Software Engineer: Working now', exact=True)
            expect(builder).to_contain_text('Reading source · SettingsForm.tsx')
            expect(page.get_by_role('button', name='Product Planner: Finished task', exact=True)).to_be_visible()
            builder.click()
            page.get_by_role('tab', name='Changes', exact=True).click()
            expect(page.locator('#panel')).to_contain_text('No file changes attributed')
            emit('PreToolUse', agent_id='builder', tool_name='Edit', tool_input={'file_path': str(root / 'SettingsForm.tsx')})
            emit('PostToolUse', agent_id='builder', tool_name='Edit', tool_input={'file_path': str(root / 'SettingsForm.tsx')})
            (root / 'SettingsForm.tsx').write_text('// updated illustrative fixture\n')
            expect(page.locator('#panel')).to_contain_text('SettingsForm.tsx', timeout=10000)
            page.get_by_role('tab', name='Activity', exact=True).click()
            expect(page.locator('#panel')).to_contain_text('Edited a file')
            assert 'Observed hook event' not in page.locator('#panel').inner_text()
            assert builder.bounding_box()['height'] < 180
            page.screenshot(path=str(output / 'desktop.png'), full_page=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            builder.click()
            assert page.locator('#detail-name').evaluate('(el)=>el===document.activeElement')
            assert page.locator('#details').bounding_box()['y'] < 100
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.evaluate('window.scrollTo(0,0)')
            page.screenshot(path=str(output / 'mobile.png'), full_page=True)
            page.get_by_role('tab', name='Activity', exact=True).press('ArrowRight')
            expect(page.get_by_role('tab', name='Changes', exact=True)).to_have_attribute('aria-selected', 'true')
            page.locator('#submit').click()
            expect(page.locator('#request-notice')).to_contain_text('Request queued')
            expect(page.locator('#submit')).to_be_disabled()
            emit('UserPromptSubmit')
            expect(page.locator('#request-notice')).to_contain_text('delivered', timeout=10000)
            page.route('**/api/request', lambda route: route.fulfill(status=400, body='{}'))
            page.locator('#request-publish').click()
            expect(page.locator('#request-notice')).to_contain_text('Could not queue')
            page.wait_for_timeout(3200)
            expect(page.locator('#request-notice')).to_contain_text('Could not queue')
            sid = 'new-illustrative-session'
            emit('SessionStart')
            expect(page.locator('.agent:visible')).to_have_count(1, timeout=10000)
            expect(page.locator('.connection')).to_have_count(0)
            expect(page.locator('#detail-name')).to_have_text('Engineering Lead')
            page.route('**/api/state', lambda route: route.abort())
            expect(page.locator('#connection')).to_have_text('Offline', timeout=10000)
            expect(page.locator('#request-publish')).to_be_disabled()
            assert not errors, errors
            browser.close()
        print(json.dumps({'status': 'passed', 'screenshots': str(output), 'scope': 'illustrative fixture; dynamic participants, live actions, finished state, read versus edit, tabs, mobile, request queue/errors, session reset and offline'}))
    finally:
        subprocess.run(helper + ['stop', '--workspace', str(root), '--approved'], capture_output=True)


if __name__ == '__main__':
    main()

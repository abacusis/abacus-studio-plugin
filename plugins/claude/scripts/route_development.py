"""Constant routing context only: no prompt reads, files, network, or permissions.

Claude evaluates intent. This reminder does not enforce model compliance, block
requests, or launch agents. Missing Python/hook support must not block a session.
"""
import json

CONTEXT = (
    'For downloading latest application code or updating the workspace from GitHub, '
    'use abacus-studio:update, not plain git pull or GitHub sign-in. Do not use '
    'this for plugin marketplace updates. Update never authorizes submission. '
    'Abacus Studio routing: when the current request asks you to plan, add, change, '
    'fix, debug, test, refactor, or review application code or an application feature, '
    'invoke the Skill tool with abacus-studio:engineering BEFORE drafting the plan '
    'or implementation, unless Engineering is already active for this task. '
    'This includes planning-only requests and apps not yet linked to Studio. '
    'Do not answer a feature request using project-knowledge alone; it supports '
    'Engineering, not a replacement workflow. FIRST use Engineering workflow-depth.md: '
    'infer the current user preference (quick, deep, or automatic) from meaning and '
    'context, not isolated keywords. Quick change/keep it simple means minimal '
    'ceremony; be careful/go deep means relevant deeper checks, not every agent. '
    'With no preference, choose the shortest adequate path. Ordinary success '
    'messages using an existing pattern are focused: implement in the main '
    'conversation and run a relevant focused check, then stop. No automatic '
    'Spec Writer, Builder, Verifier, reviewer team or readiness ceremony for '
    'focused low-risk work; do not load full orchestration for it. A quick request '
    'never bypasses sensitive-work checks or approval, and a deep request does '
    'not authorize extra scope. Never add agents to populate the dashboard. '
    'For mockup/prototype requests or material visual uncertainty, use Engineering '
    'mockup-first.md before full feature orchestration. Respect mockup only and '
    'build directly. Suggest a clickable sample-data preview only when useful; '
    'do not add it to small fixes or backend-only work. A visual-only mockup '
    'does not authorize backend connections, real writes or publishing. '
    'Engineering chooses focused versus '
    'structured/sensitive work. For a structured or sensitive feature, delegate the '
    'specification to abacus-studio:spec-writer via the host Agent/Task tool before '
    'drafting your own plan, including planning-only requests. Do not skip an '
    'available specialist merely because the repository is small. '
    'After the spec, delegate authorized structured implementation to '
    'abacus-studio:builder; never invoke Builder for planning-only work. '
    'After structured implementation, delegate approved verification to '
    'abacus-studio:verifier, which reports evidence without fixing code. '
    'For substantial implemented changes also use abacus-studio:code-reviewer '
    'for source review, without automatic fixes or publishing approval. '
    'Trivial text edits stay lightweight; do not launch Spec Writer for them. '
    'For standalone design/security requests use their relevant skills. '
    'Visible substantial changes also use abacus-studio:ui-reviewer with actual '
    'current screenshots, not source-only visual claims; keep UI distinct from UX. '
    'Substantial changes to user tasks also use abacus-studio:ux-reviewer with '
    'actual flow evidence; screenshots alone cannot establish flow success. '
    'Security-sensitive changes use the Security skill and its source-only '
    'abacus-studio:security-reviewer; no security ceremony for trivial edits. '
    'Do NOT activate Engineering for arithmetic, general conversation, pure knowledge '
    'lookup, connection/status, installation help, or questions about plugin commands. '
    'Preserve planning-only boundaries and all approvals. '
    'When asked to open the local team dashboard, load Engineering and its '
    'references/engineering/local-dashboard.md guidance; obtain local tracking '
    'approval first. Do not launch it for connection status. '
    'Structured implemented work ends with abacus-studio:readiness-reviewer '
    'using actual current evidence, not waived checks or publishing approval. '
    'Never invent skill or agent execution. If Skill/delegation is unavailable or denied, disclose the '
    'limitation and continue safely without changing permissions. Keep replies brief.'
)

if __name__ == '__main__':
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit',
                                           'additionalContext': CONTEXT}}))

"""Audit paper dependencies against the observed Overleaf tree and compiler log."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'docs/paper/revision_evidence'
PAPER = ROOT / 'docs/paper/overleaf/01_causal_atlas_bridge.tex'
source = PAPER.read_text(encoding='utf-8')
before = (EVIDENCE / '01_before_appendix_B_online.tex').read_text(encoding='utf-8')
inventory = json.loads((EVIDENCE / 'appendix_B_overleaf_inventory.json').read_text(encoding='utf-8'))
log = (EVIDENCE / 'appendix_B_overleaf_compile_dom.txt').read_text(encoding='utf-8')

start_b = r'\section{Appendix: Experimental Details}'
start_a = r'\section{Appendix: Notation and Proofs}'
start_experiments = r'\section{Experiments:'
assert source[:source.index(start_experiments)] == before[:before.index(start_experiments)]
assert source[source.index(start_a):source.index(start_b)] == before[before.index(start_a):before.index(start_b)]
for count in ['All logs 0', 'Errors 0', 'Warnings 0', 'Info 0']:
    assert f'tab "{count}"' in log
assert 'Output written on /compile/output.xdv (54 pages,' in log
assert not re.search(r'(?:Overfull|Underfull) \\+hbox|LaTeX Warning:', log)

pattern = re.compile(r'\\(?:input|include|includegraphics)(?:\[[^\]]*\])?\{([^}]+)\}')
references = set()


def visit(text):
    for path in pattern.findall(text):
        if path in references:
            continue
        references.add(path)
        target = PAPER.parent / path
        if target.suffix == '.tex':
            visit(target.read_text(encoding='utf-8'))


visit(source)
audit = {
    'scope': 'Current Overleaf 01 only; no files deleted; other documents and build pipelines are outside this cleanup scope.',
    'source_sha256': hashlib.sha256(PAPER.read_bytes()).hexdigest(),
    'online_source_equals_local': True,
    'theory_and_appendix_A_unchanged_from_online_backup': True,
    'compile': {'errors': 0, 'warnings': 0, 'typesetting_messages': 0, 'pages': 54},
    'folders': {},
}
for kind, files in inventory.items():
    prefix = 'experiments/causal_atlas_bridge/' + kind + '/'
    used = sorted(path[len(prefix):] for path in references if path.startswith(prefix))
    assert set(used) <= set(files)
    assert all(prefix + name in log for name in used)
    compiler_used = set(re.findall(re.escape(prefix) + r'([\w.-]+\.(?:pdf|png|tex|csv))', log))
    assert compiler_used == set(used), (kind, compiler_used, used)
    audit['folders'][kind] = {'keep': used, 'not_referenced': sorted(set(files) - set(used))}

(EVIDENCE / 'appendix_B_asset_audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8', newline='\n')
lines = [
    '# Appendix B revision and Overleaf cleanup audit', '',
    'Final online source: `01_causal_atlas_bridge.tex`.',
    'Overleaf project: https://www.overleaf.com/project/6a3410d137fc160e82dd884e', '',
    'The online source was copied back through the editor and matched the archived source exactly.',
    'XeLaTeX compilation: 54 pages, Errors 0, Warnings 0, Info 0.',
    'The theory before Experiments and all of Appendix A match the pre-edit online backup.', '',
    '## Revision', '',
    'Appendix B now has five sections: protocols; robustness and failure boundaries; comparator and selection audit; real-data construction and stability; bridge evidence scope and stability.',
    'It contains 15 tables (12 inline and three external inputs). Its former three external figures are no longer included.',
    'The main experiments retain their structure. Five small text/reference repairs connect them to the reorganized appendix.',
    'Results come from committed CSV records; this revision performs no experimental resampling.',
    'Unfavorable comparisons and validity limitations are retained. The operational bridge monotonicity diagnosis is excluded.', '',
    '## Cleanup scope', '',
    'The lists below cover files actually observed in the Overleaf figures and tables folders, relative to `experiments/causal_atlas_bridge/`.',
    'Not referenced means this compiled 01 document does not load the file, including nested inputs. The compiler log confirms the retained dependencies.',
    'Some unused files contain results now summarized or embedded in 01. Their absence from the dependency list does not mean their experiments were discarded.',
    'CSV records and old outputs may support reproduction or other documents. Keep the repository evidence when cleaning the Overleaf project. No files were deleted.',
    'The 11 generated `app_b_*.tex` files exist locally for reproducibility; their content is embedded in 01 and these filenames were not present in the observed Overleaf folder.', '',
]
for kind, groups in audit['folders'].items():
    for key, names in groups.items():
        lines += [f'## {kind}: {key} ({len(names)})', '', '```text', *names, '```', '']
lines += ['## Evidence and reproduction', '',
          '- `appendix_B_restructure.json`: source and CSV dependency hashes.',
          '- `01_before_appendix_B_online.tex`: pre-edit online backup.',
          '- `appendix_B_overleaf_compile_dom.txt`: observed final compiler log panel.',
          '- `appendix_B_overleaf_inventory.json`: observed online file inventory.',
          '- `appendix_B_asset_audit.json`: machine-readable cleanup decisions.',
          '- Run `python scripts/build/restructure_appendix_b.py` to rebuild the appendix from CSV records.',
          '- Run `python scripts/build/audit_appendix_b_assets.py` to reproduce this audit against the saved online observations.', '']
(EVIDENCE / 'appendix_B_cleanup.md').write_text('\n'.join(lines), encoding='utf-8', newline='\n')
print(json.dumps(audit, indent=2))

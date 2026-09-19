# -*- coding: utf-8 -*-
"""검토 데이터(JSON)를 뷰어 템플릿에 넣어 단일 HTML을 만든다.

    python build.py <data.json> <out.html> [viewer_template.html]

템플릿을 생략하면 이 스크립트와 같은 폴더의 viewer_template.html을 쓴다.
데이터 구조는 ../reference/data-schema.md 참고.
"""
import json, os, sys

sys.stdout.reconfigure(encoding='utf-8')

REQ = ['meta', 'laws', 'parties', 'kinds', 'cols', 'issues']
META_REQ = ['title', 'subtitle', 'org', 'reviewedAt', 'basis', 'status', 'headline', 'disclaimer']
ISSUE_REQ = ['id', 'seq', 'party', 'kind', 'title', 'question', 'amount', 'display', 'certainty', 'sum', 'steps']


def check(d):
    err, warn = [], []
    for k in REQ:
        if k not in d: err.append('최상위 "%s" 없음' % k)
    if err: return err, warn
    for k in META_REQ:
        if k not in d['meta']: err.append('meta.%s 없음' % k)
    lawids = {x['id'] for x in d['laws']}
    pids = {x['id'] for x in d['parties']}
    kids = {x['id'] for x in d['kinds']}
    seen = set()
    nref = 0
    for i in d['issues']:
        for k in ISSUE_REQ:
            if k not in i: err.append('%s: %s 없음' % (i.get('id', '?'), k))
        if i.get('id') in seen: err.append('id 중복: %s' % i.get('id'))
        seen.add(i.get('id'))
        if i.get('party') not in pids: err.append('%s: parties에 없는 party "%s"' % (i.get('id'), i.get('party')))
        if i.get('kind') not in kids: err.append('%s: kinds에 없는 kind "%s"' % (i.get('id'), i.get('kind')))
        if i.get('sum') and not isinstance(i.get('amount'), int):
            err.append('%s: sum=true인데 amount가 정수가 아님' % i.get('id'))
        for s in i.get('steps', []):
            if not s.get('title') and s.get('col') not in d['cols']:
                err.append('%s: cols에 없는 col "%s" (title도 없음)' % (i.get('id'), s.get('col')))
            if not s.get('gist'): err.append('%s: gist 없는 단계' % i.get('id'))
            for r in s.get('refs', []):
                nref += 1
                if r.get('law') not in lawids:
                    err.append('%s: laws에 없는 law "%s" (%s)' % (i.get('id'), r.get('law'), r.get('label')))
                if 'cols' in r:
                    w = len(r['cols'])
                    for n, row in enumerate(r.get('rows', [])):
                        if len(row) != w: err.append('%s / %s: %d행의 칸 수(%d)가 머리행(%d)과 다름' % (i.get('id'), r.get('label'), n + 1, len(row), w))
                elif not r.get('ps'):
                    err.append('%s: 본문(ps)도 표(cols)도 없는 근거 "%s"' % (i.get('id'), r.get('label')))
                else:
                    body = ' '.join(r['ps'])
                    for h in r.get('hl', []):
                        if h not in body: warn.append('형광 문구가 본문에 없음: "%s" (%s)' % (h, r.get('label')))
    for law in d['laws']:
        if not any(r.get('law') == law['id'] for i in d['issues'] for s in i['steps'] for r in s.get('refs', [])):
            warn.append('쓰이지 않는 법령: %s' % law['name'])
    return err, warn


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    here = os.path.dirname(os.path.abspath(__file__))
    data_path, out_path = sys.argv[1], sys.argv[2]
    tpl_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(here, 'viewer_template.html')

    d = json.load(open(data_path, encoding='utf-8-sig'))
    err, warn = check(d)
    for w in warn: print('[확인] ' + w)
    if err:
        for e in err: print('[오류] ' + e)
        print('\n오류 %d건 — HTML을 만들지 않았다.' % len(err)); sys.exit(1)

    tpl = open(tpl_path, encoding='utf-8').read()
    if '/*DATA*/' not in tpl:
        print('템플릿에 /*DATA*/ 자리가 없다.'); sys.exit(1)
    html = tpl.replace('/*DATA*/', 'var DATA = ' + json.dumps(d, ensure_ascii=False) + ';')
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or '.', exist_ok=True)
    open(out_path, 'w', encoding='utf-8').write(html)

    nref = sum(len(s.get('refs', [])) for i in d['issues'] for s in i['steps'])
    tot = {}
    for i in d['issues']:
        if i.get('sum'): tot[i['party']] = tot.get(i['party'], 0) + (i.get('amount') or 0)
    print('완료: %s' % out_path)
    print('  항목 %d건 · 근거 %d건 · %d KB' % (len(d['issues']), nref, round(len(html.encode('utf-8')) / 1024)))
    for p in d['parties']:
        if tot.get(p['id']): print('  %s 합계 %s원' % (p['label'], format(tot[p['id']], ',')))


if __name__ == '__main__':
    main()

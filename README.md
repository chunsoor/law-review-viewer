# law-review-viewer

법률 검토 결과를 **오프라인 단일 HTML 화면**으로 만드는 Claude Code 플러그인이다.
국가법령정보 조회용 MCP 서버(`law`)를 함께 담고 있어, 설치하면 조문 검색부터 화면 생성까지 한 번에 된다.

## 무엇을 만드나

- **요약** — 결론 한 줄 + 금액 카드 + 검토 항목 카드
- **상세** — 항목마다 `법률 → 시행령·규칙 → 처분기준 → 예외·겹침` 4단계, 조문 원문(핵심 문구 형광)
- **표** — 엑셀처럼 정리된 한 장, TSV 복사
- **보고서 모드 / 인쇄** — 캡처해서 한글 보고서에 붙이기 좋게 800px 고정폭

조문은 이미지가 아니라 텍스트라 검색·복사가 된다. 검토 내용은 전부 JSON 한 덩어리라, 데이터만 갈아끼우면 다른 검토 건에 그대로 쓴다.

## 설치

```bash
claude plugin marketplace add <이 저장소 주소>
claude plugin install law-review-viewer@chunsoor-law
```

비공개 저장소면 먼저 깃허브에 로그인되어 있어야 한다(`git` 자격증명 또는 `gh auth login`).
설치 후 Claude Code를 다시 열면 스킬과 `law` MCP가 함께 올라온다.

### MCP 서버가 쓰는 것

`mcp/server.py`는 파이썬 패키지 두 개가 필요하다.

```bash
pip install -r mcp/requirements.txt
```

국가법령정보 OPEN API는 **신청 ID(OC)** 로 인증한다. 이 저장소에는 ID를 넣어 두지 않았으므로, 컴퓨터마다 환경변수로 지정해야 한다.

| 변수 | 필수 | 뜻 |
|---|---|---|
| `LAW_OC` | ● | 국가법령정보 OPEN API 신청 ID |
| `LAW_REFERER` | | 신청 시 등록한 도메인. 등록했다면 같이 넣는다 |

ID는 https://open.law.go.kr 에서 신청한다(무료).

윈도우에서 한 번만 등록하면 된다. 등록 후 터미널과 Claude Code를 다시 연다.

```powershell
setx LAW_OC "내신청ID"
setx LAW_REFERER "https://내도메인/"
```

`LAW_OC`가 없으면 MCP 서버가 뜨면서 무엇을 설정해야 하는지 알려 주고 멈춘다.

## 쓰는 법

Claude Code에서 검토를 시키면 된다. 조문 검색만 시키면 열리지 않는다.

- "○○ 위반 행정처분 가능한지 검토해줘"
- "○○ 조례 제정할 수 있는지 법률 검토하고 화면으로 만들어줘"
- 확실히 하려면 `/law-review-viewer`

결과는 작업 폴더에 `<검토명>.html`과 `<검토명>.json` 두 개로 나온다. 나중에 금액이나 문구만 고칠 때는 JSON만 손보고 다시 만든다.

```bash
python skills/law-review-viewer/assets/build.py data.json 검토서.html
```

`build.py`는 만들기 전에 검증한다 — 등록하지 않은 법령·대상·종류, 표의 칸 수 불일치, 본문에 없는 형광 문구, 빠진 필수 항목. 오류가 있으면 HTML을 만들지 않는다.

## 구조

```
.claude-plugin/plugin.json        플러그인 선언
.claude-plugin/marketplace.json   마켓플레이스 선언 (이 저장소 자체가 마켓플레이스)
.mcp.json                         법령 조회 MCP 서버 선언
mcp/server.py                     국가법령정보 OPEN API 래퍼
skills/law-review-viewer/
  SKILL.md                        작업 순서와 화면 규칙
  assets/viewer_template.html     화면 본체(내용 없는 틀)
  assets/build.py                 JSON → HTML, 검증 포함
  reference/data-schema.md        검토 데이터 구조
  reference/law-sourcing.md       조문을 틀리지 않게 가져오는 법
```

## 주의

- 화면은 `file://`에서 도는 단일 HTML이다. 외부 CDN·웹폰트·`fetch`·`<script type="module">`을 쓰면 안 된다.
- 콘텐츠 폭 800px은 캡처해서 A4 본문에 붙였을 때 10pt로 읽히는 값이다. 바꾸지 않는다.
- 법령 MCP는 **시행예정 판본**을 돌려줄 때가 있다. `조문시행일자`를 반드시 확인한다. 자세한 것은 `reference/law-sourcing.md`.

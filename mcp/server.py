import os, json, httpx
from mcp.server.mcpserver import MCPServer

OC = os.environ.get("LAW_OC", "")
if not OC:
    raise SystemExit(
        "환경변수 LAW_OC가 없습니다. 국가법령정보 OPEN API 신청 ID를 LAW_OC로 지정하십시오.
"
        "신청: https://open.law.go.kr  (신청 시 등록한 도메인은 LAW_REFERER로 지정)"
    )
BASE = "http://www.law.go.kr/DRF"
REFERER = os.environ.get("LAW_REFERER", "")
mcp = MCPServer("law")

async def _get(path, **params):
    params.update({"OC": OC, "type": "JSON"})
    headers = {"Referer": REFERER} if REFERER else {}
    async with httpx.AsyncClient(timeout=20, headers=headers) as c:
        r = await c.get(f"{BASE}/{path}", params=params)
        return r.text

@mcp.tool()
async def law_search(query: str) -> str:
    """법령명으로 현행법령 목록 검색"""
    return await _get("lawSearch.do", target="law", query=query, display=20)

@mcp.tool()
async def law_body(law_id: str) -> str:
    """법령ID 또는 법령명으로 조문 전문 조회"""
    return await _get("lawService.do", target="law", ID=law_id)

@mcp.tool()
async def law_3dan(law_id: str, kind: int = 1) -> str:
    """법률-시행령-시행규칙 조문 대조 (3단 비교). law_id는 법령ID(예: 001749). kind 1=인용조문, 2=위임조문"""
    return await _get("lawService.do", target="thdCmp", ID=law_id, knd=kind)

@mcp.tool()
async def law_delegated(law_id: str) -> str:
    """조문별 하위법령 위임 관계 조회"""
    return await _get("lawService.do", target="lsDelegated", ID=law_id)

@mcp.tool()
async def ordin_search(query: str, org: str = "") -> str:
    """조례·규칙 검색. org는 지자체명(예: 제천시, 충청북도 제천시)"""
    if not org:
        return await _get("lawSearch.do", target="ordin", query=query, display=20)
    # API의 org 파라미터는 기관코드만 받으므로 지자체명은 결과의 지자체기관명으로 거른다
    matched, total = [], 0
    for page in range(1, 21):
        data = json.loads(await _get("lawSearch.do", target="ordin", query=query, display=100, page=page))
        body = data.get("OrdinSearch", {})
        total = int(body.get("totalCnt") or 0)
        items = body.get("law") or []
        items = [items] if isinstance(items, dict) else items
        matched += [x for x in items if org in x.get("지자체기관명", "")]
        if page * 100 >= total:
            break
    return json.dumps({"키워드": query, "지자체": org, "전체검색건수": total,
                       "검색범위": min(total, 2000), "일치건수": len(matched), "law": matched},
                      ensure_ascii=False, indent=1)

@mcp.tool()
async def prec_search(query: str = "", ref_law: str = "") -> str:
    """판례 검색. ref_law에 법령명 입력 시 해당 법령 관련 판례만"""
    return await _get("lawSearch.do", target="prec", query=query, JO=ref_law, display=20)

@mcp.tool()
async def prec_body(prec_id: str) -> str:
    """판례일련번호로 전문 조회 (참조조문·참조판례 포함)"""
    return await _get("lawService.do", target="prec", ID=prec_id)

@mcp.tool()
async def expc_search(query: str) -> str:
    """법제처 법령해석례 검색"""
    return await _get("lawSearch.do", target="expc", query=query)

if __name__ == "__main__":
    mcp.run()
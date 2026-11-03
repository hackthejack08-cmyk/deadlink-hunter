import asyncio
import httpx
from fastapi.testclient import TestClient

from app.crawler import ScanRun
from app.db import Database
from app.main import create_app
from app.models import ScanRequest
from app.runner import ScanManager

PAGES = {
    "/": '<a href="/a">A</a><a href="/missing">Gone</a><a href="https://cdn.test/ok">ext</a><a href="https://cdn.test/blocked">b</a><img src="/img/ok.png"><img src="/img/missing.png">',
    "/a": '<a href="/">home</a><a href="/old">old</a><a href="https://cdn.test/429">rl</a>',
}


def handler(req: httpx.Request) -> httpx.Response:
    host, path = req.url.host, req.url.path
    if host == "example.test":
        if path in PAGES and req.method == "GET":
            return httpx.Response(200, headers={"content-type": "text/html"}, content=PAGES[path])
        if path in PAGES: return httpx.Response(200, headers={"content-type": "text/html"})
        if path == "/old": return httpx.Response(301, headers={"location": "/a"})
        if path == "/img/ok.png": return httpx.Response(200, headers={"content-type": "image/png"})
        return httpx.Response(404)
    if path == "/blocked": return httpx.Response(403)
    if path == "/429": return httpx.Response(429)
    return httpx.Response(200)


def factory(_timeout):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)


def test_full_crawl_results_and_score(tmp_path):
    async def go():
        db = Database(str(tmp_path / "t.db")); await db.init()
        await db.create_scan("s1", "https://example.test/", {})
        async with factory(5) as client:
            run = ScanRun("s1", ScanRequest(url="https://example.test/"), db, client)
            await run.run()
        return db, run.summarize()
    db, s = asyncio.run(go())
    rows, total = asyncio.run(db.query_issues("s1"))
    cats = {(r["url"].split("test")[-1], r["category"]) for r in rows}
    assert ("/missing", "broken") in cats and ("/img/missing.png", "image") in cats
    assert ("/blocked", "blocked") in cats and ("/429", "rate-limited") in cats and ("/old", "redirect") in cats
    assert s["pagesScanned"] == 2  # "/" and "/a"; /old redirects to /a (not re-parsed), /missing is a 404
    assert s["brokenImages"] == 1 and s["blocked"] == 1 and s["rateLimited"] == 1
    assert s["scoreBreakdown"]["excludedBlocked"] == 1
    # 1 broken(1.0) + 1 image(0.75) + 1 redirect(0.05) over evaluated non-blocked URLs
    assert s["scoreBreakdown"]["weightedProblems"] == 1.8
    assert s["scoreBreakdown"]["evaluated"] == 7 and s["healthScore"] == 0  # 400*1.8/7 > 100 -> clamped
    # issue found on both pages is recorded once per occurrence
    assert sum(1 for r in rows if r["url"].endswith("/old")) == 1


def test_api_contract(tmp_path):
    db_path = str(tmp_path / "api.db")
    mgr = ScanManager(Database(db_path), client_factory=factory)
    with TestClient(create_app(db_path, mgr)) as c:
        assert c.get("/api/health").json()["status"] == "ok"
        preflight = c.options("/api/scans", headers={
            "Origin": "https://deadlink-hunter.vercel.app",
            "Access-Control-Request-Method": "POST",
        })
        assert preflight.status_code == 200
        assert preflight.headers["access-control-allow-origin"] == "https://deadlink-hunter.vercel.app"
        bad = c.post("/api/scans", json={"url": "http://169.254.169.254/"})
        assert bad.status_code == 400
        assert c.post("/api/scans", json={"url": "ftp://example.test"}).status_code == 400
        assert c.post("/api/scans", json={"url": "https://example.test/", "maxPages": 999}).status_code == 422
        r = c.post("/api/scans", json={"url": "https://example.test/", "maxPages": 10})
        assert r.status_code == 202
        sid = r.json()["id"]
        for _ in range(100):
            job = c.get(f"/api/scans/{sid}").json()
            if job["status"] in ("completed", "failed"): break
            import time; time.sleep(0.05)
        assert job["status"] == "completed", job
        assert job["summary"]["healthScore"] == c.get(f"/api/scans/{sid}/summary").json()["healthScore"]
        report = c.get(f"/api/scans/{sid}/report")
        assert report.status_code == 200, report.text
        assert report.json()["seo"]["pagesAudited"] >= 1
        assert 0 <= report.json()["seo"]["score"] <= 100
        res = c.get(f"/api/scans/{sid}/results", params={"category": "broken"})
        assert res.headers["X-Total-Count"] == "1"   # only /missing is a 404 link; the broken image has its own category
        assert {i["category"] for i in res.json()} == {"broken"}
        assert res.json()[0]["statusCode"] == 404 and "sourcePage" in res.json()[0]
        assert any(s["id"] == sid for s in c.get("/api/scans").json())
        assert c.get("/api/scans/nope").status_code == 404
        assert c.post(f"/api/scans/{sid}/cancel").json()["status"] == "completed"  # terminal state untouched

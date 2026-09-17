from fastapi.testclient import TestClient

from simjobs.api import app

client = TestClient(app)


def test_health():
    assert client.get("/healthz").json() == {"status": "ok"}


def test_solve_returns_scalars_and_series():
    r = client.post("/solve", json={"n_points": 50})
    assert r.status_code == 200
    body = r.json()
    assert body["T_max_K"] > 400
    assert len(body["series"]["t_s"]) == 50


def test_solve_rejects_bad_parameters():
    assert client.post("/solve", json={"t_end_s": 0}).status_code == 422

import responses
import requests


@responses.activate
def test_simple():
    # Register via 'Response' object
    rsp1 = responses.Response(
        method="PUT",
        url="http://example.com",
    )
    responses.add(rsp1)
    # register via direct arguments
    responses.add(
        responses.GET,
        "http://twitter.com/api/1/foobar",
        json={"error": "not found"},
        status=404,
    )

    resp = requests.get("http://twitter.com/api/1/foobar")
    resp2 = requests.put("http://example.com")

    assert resp.json() == {"error": "not found"}
    assert resp.status_code == 404

    assert resp2.status_code == 200
    assert resp2.request.method == "PUT"

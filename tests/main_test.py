import json
import uuid as uuid_gen

import responses
import requests

# Both of these return the parent element
# r = requests.get(api + "/projects?page%5Bsize%5D=1")
# r = requests.get(api + "/projects/" + project_id)
# This will return the element
# url = api + "/projects/" + project["@id"] + "/query-results"


def request_callback(request_id):
    print(request_id.body)
    payload = json.loads(request_id.body)
    headers = {"Content-type": "application/json", "Accept": "text/plain"}
    return (200, headers, json.dumps({"@id": payload["@id"]}))


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

    assert resp.json() == {"error": "not found"}
    assert resp.status_code == 404


def return_json():
    return {"error": "not found"}


@responses.activate
def test2_simple():
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
        json=return_json(),
        status=404,
    )

    resp2 = requests.put("http://example.com")

    assert resp2.status_code == 200
    assert resp2.request.method == "PUT"


@responses.activate
def test3_simple():
    responses.add_callback(
        responses.POST,
        "http://twitter.com/api/1/foobar",
        callback=request_callback,
        content_type="application/json",
    )

    resp2 = requests.post(
        "http://twitter.com/api/1/foobar", json.dumps({"@id": str(uuid_gen.uuid4())})
    )

    assert resp2.status_code == 200
    assert resp2.request.method == "POST"

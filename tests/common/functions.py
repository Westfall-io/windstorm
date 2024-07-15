import json
import filecmp
import os.path

from functools import partial

import responses


def project_response_fn():
    with open("./tests/mocks/api_projects_response/projects.json", "r") as f:
        project_response = json.loads(f.read())
    return project_response


def are_dir_trees_equal(dir1, dir2):
    """
    Compare two directories recursively. Files in each directory are
    assumed to be equal if their names and contents are equal.

    @param dir1: First directory path
    @param dir2: Second directory path

    @return: True if the directory trees are the same and
        there were no errors while accessing the directories or files,
        False otherwise.
    """

    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if (
        len(dirs_cmp.left_only) > 0
        or len(dirs_cmp.right_only) > 0
        or len(dirs_cmp.funny_files) > 0
    ):
        return False
    (_, mismatch, errors) = filecmp.cmpfiles(
        dir1, dir2, dirs_cmp.common_files, shallow=False
    )
    if len(mismatch) > 0 or len(errors) > 0:
        return False
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        if not are_dir_trees_equal(new_dir1, new_dir2):
            return False
    return True


def request_callback(request_id, mock_dir):
    """
    This function handles reading json files to prepare the response like
    it's coming from the API.


    """
    payload = json.loads(request_id.body)
    # Sample Query
    # {
    # "@type": "Query",
    # "select": [
    # "@id"
    # ],
    # "where": {
    # "@type": "PrimitiveConstraint",
    # "operator": "=",
    # "property": "@type",
    # "value": "Element"
    # }
    # }
    # This doesn't handle all possible cases
    t1 = True
    if payload["@type"] == "Query":
        if payload["where"]["@type"] == "PrimitiveConstraint":
            if payload["where"]["property"] == "@id":
                eid = payload["where"]["value"]
            else:
                raise ValueError("The input query was not an @id")
        elif payload["where"]["@type"] == "CompositeConstraint":
            t1 = False
            if payload["where"]["operator"] == "and":
                for c in payload["where"]["constraint"]:
                    if c["property"] == "@type":
                        t = c["value"]
                    elif c["property"] == "declaredName":
                        dn = c["value"]
                    else:
                        raise ValueError("The input query was not handled")
            else:
                raise ValueError("The input query was not handled")
        else:
            raise ValueError("The input query was not a PrimitiveConstraint")
    else:
        raise ValueError("The input query was not a Query type")

    try:
        if t1:
            with open("./tests/mocks/" + mock_dir + "/" + eid + ".json", "r") as f:
                data = f.read()
        else:
            with open(
                "./tests/mocks/" + mock_dir + "/" + t + "_" + dn + ".json", "r"
            ) as f:
                data = f.read()
    except Exception as e:
        print(e)
        if t1:
            print("./tests/mocks/" + mock_dir + "/" + eid + ".json")
        else:
            print("./tests/mocks/" + mock_dir + "/" + t + "_" + dn + ".json")

        from os import walk

        for dirpath, dirnames, filenames in walk("./tests/mocks/" + mock_dir + "/"):
            print(filenames)
        raise NotImplementedError

    headers = {"Content-type": "application/json", "Accept": "text/plain"}
    return (200, headers, data)


def add_responses(project_response, mock_dir):
    responses.add(
        responses.GET,
        "http://sysml2.intercax.com:9000/projects?page%5Bsize%5D=1",
        json=project_response,
        status=200,
    )

    responses.add_callback(
        responses.POST,
        "http://sysml2.intercax.com:9000/projects/00270ef6-e518-455a-b59e-324ffeb1c9da/query-results",
        callback=partial(request_callback, mock_dir=mock_dir),
        content_type="application/json",
    )

import os
import json
import base64

import papermill as pm
import nbformat as nbf

mocks = {}
for dir_path, dir_names, file_names in os.walk("./tests/mocks"):
    for file in file_names:
        if ".sysml" in file:
            if not dir_path in mocks:
                mocks[dir_path] = []
            mocks[dir_path].append(os.path.join(dir_path, file))

for test_name in mocks:
    # Create a notebook with the test sysml
    nb = nbf.v4.new_notebook()
    nb["cells"] = []
    for cell in sorted(mocks[test_name]):
        with open(cell, "r") as f:
            nb["cells"].append(nbf.v4.new_code_cell(f.read()))

    fname = test_name + ".ipynb"

    with open(fname, "w") as f:
        nbf.write(nb, f)

    pm.execute_notebook(fname, fname, kernel_name="sysml")

    with open(fname, "r") as f:
        # Read the notebook
        nb = json.loads(f.read())
        if nb["metadata"]["language_info"]["name"] == "SysML":
            for cell in nb["cells"]:
                # Check for the SysML cells
                if cell["cell_type"] == "code":
                    # Find the output which must exist now
                    for out in cell["outputs"]:
                        # Find the right output to continue
                        if "data" in out.keys():
                            if "text/html" in out["data"]:
                                html = out["data"]["text/html"][0]
                                data = json.loads(
                                    base64.b64decode(
                                        html[html.find("href=") + 35 : -14]
                                    )
                                )
                                with open(fname.replace(".ipynb", ".json"), "w") as g:
                                    print(
                                        "Creating mock api file: {}".format(
                                            fname.replace(".ipynb", ".json")
                                        )
                                    )
                                    g.write(json.dumps(data))
                                ## End if valid name, otherwise can't export
                            ## End for name
                        ## End check correct data output
                    ## End for each cell output
                ## End this cell is SysML
            ## End for each cell
        ## End if SysML
    ## Close file

    with open(fname.replace(".ipynb", ".json"), "r") as f:
        for i in json.loads(f.read()):
            try:
                if "@id" in i["payload"]:
                    with open(
                        test_name[: test_name.find("/")] + i["payload"]["@id"] + ".json",
                        "w",
                    ) as g:
                        g.write(i["payload"])
                else:
                    # No way to reference this object in the future, just skip.
                    continue
            except Exception as e:
                print(i["payload"])
                raise e
            # End open file for this element
        # For each element
    # End open large json file with all elements

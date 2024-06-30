import os

import papermill as pm
import nbformat as nbf

mocks = {}
for dir_path, dir_names, file_names in os.walk("./tests/mocks"):
    print(file_names)
    for file in file_names:
        if ".sysml" in file:
            print('found')
            if not dir_path in mocks:
                mocks[dir_path] = []
            mocks[dir_path].append(os.path.join(dir_path,file))

for test_name in mocks:
    # Create a notebook with the test sysml
    nb = nbf.v4.new_notebook()
    nb["cells"] = []
    for cell in mocks[test_name]:
        with open(cell, "r") as f:
            nb["cells"].append(nbf.v4.new_code_cell(f.read()))

    fname = test_name+".ipynb"

    with open(fname, "w") as f:
        nbf.write(nb, f)

    pm.execute_notebook(fname, fname, kernel_name="sysml")

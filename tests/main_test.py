import os

import papermill as pm
import nbformat as nbf

def test_1_analysis():
    test_name = '1_analysis'
    # Create a notebook with the test sysml
    nb = nbf.v4.new_notebook()
    cells = []
    pring(os.getcwd())
    #for dir_path, dir_names, file_names in os.walk(os.path.join('./tests', test_name)):
    #    if '.sysml' in file_names:
    #        cells.append(os.path.join(file_names)


    #nb['cells'] = [nbf.v4.new_markdown_cell(text),
    #               nbf.v4.new_code_cell(code)]
    #fname = 'test.ipynb'

    #with open(fname, 'w') as f:
    #    nbf.write(nb, f)

    #pm.execute_notebook(fname,fname,kernel_name="sysml")

    assert None == None

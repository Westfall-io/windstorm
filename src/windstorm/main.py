#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 17 23:13:52 2023

@author: christophercox
"""

import sysml2py


def main(template_filepath, model_filepath, auth_token=False):
    # Determine if path is restful or local
    if len(model_filepath) > 6:
        web = model_filepath[:7]
        if web == "http://":
            rest = True
            # Try to open model from RESTful endpoint
        elif web == "https:/" and len(model_filepath) > 7:
            if model_filepath[:7] == "https://":
                rest = True
                # Try to open model from RESTful endpoint
            else:
                rest = False
        else:
            rest = False
    else:
        rest = False

    # Load the model as a string
    if rest:
        raise NotImplementedError
    else:
        try:
            with open(model_filepath, "r") as f:
                model = f.read()
            f.close()
        except FileNotFoundError:
            print("File was not found.")
            return False

    a = sysml2py.loads(model)
    a.dump()

    print(a.dump())

    return True


if __name__ == "__main__":
    template = "sample.yml"
    model = "sample_model.sysml"
    main(template, model)

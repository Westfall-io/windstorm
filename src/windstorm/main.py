#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 17 23:13:52 2023

@author: christophercox
"""

import sysml2py
import astropy.units as u

def template_test(model, template):
    import re
    from jinja2 import Template
    
    template = Template(template)
    def custom_function(string, element=None):
        #print(string)
        z=re.search(r"\.to\((.*)\)", string)
        if z is not None:
            # remove the to statement
            string = string[:z.start(0)]
            unit_conv = z.groups()[0]
            #!TODO Need to add support for imperial units 
            if unit_conv[:2] == 'u.':
                module = getattr(u, unit_conv[2:])
            else:
                raise ValueError('Needs to start with u.')
            #print(unit_conv)
        r = model._get_child(string).get_value()
        if z is not None:
            r = r.to(module).value
        return r
    
    print(template.render(custom_function=custom_function))
    return True


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

    with open(template_filepath, 'r') as f:
        b = f.read()
    f.close()
    
    template_test(a, b)
        
    return True


if __name__ == "__main__":
    template = "sample.yml"
    model = "sample_model.sysml"
    main(template, model)

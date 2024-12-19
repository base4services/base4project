
import os
import pathlib

# Root directory of the project
def root():

    #TODO: define root when running in a container

    return pathlib.Path(__file__).parent.parent.parent

if __name__=='__main__':

    print(root())
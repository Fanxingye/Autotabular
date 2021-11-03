import os
import sys

from autotabular.pipeline.components.base import AutotabularClassificationAlgorithm

# Add the parent directory to the path to import the parent component as
# dummy_components.dummy_component_2.DummyComponent1
this_directory = os.path.dirname(os.path.abspath(__file__))
parent_directory = os.path.abspath(os.path.join(this_directory, '..'))
sys.path.append(parent_directory)


class DummyComponent2(AutotabularClassificationAlgorithm):
    pass

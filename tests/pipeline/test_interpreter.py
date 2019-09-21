import pytest
from ambianic import pipeline
from ambianic.pipeline import interpreter


def test_get_pipelines_none():
    p = interpreter.get_pipelines(pipelines_config=[])
    assert not p


class _TestSourceElement(pipeline.PipeElement):

    def __init__(self, element_config=None):
        super()
        self.config = element_config

    def heal(self):
        """ Placeholder implementation of abstractmethod"""
        pass

    def receive_next_sample(self, **sample):
        """ Placeholder implementation of abstractmethod"""
        pass


def test_get_pipelines_one():
    # override source op with a mock test class
    interpreter.Pipeline.PIPELINE_OPS['source'] = _TestSourceElement
    p = interpreter.get_pipelines(
        pipelines_config={
            'pipeline_one': [
                      {'source': 'some_source'}
                      ]
            }
        )
    assert isinstance(p[0], interpreter.Pipeline)
    assert p[0].name == 'pipeline_one'
    assert isinstance(p[0].pipe_elements[0], _TestSourceElement)
    assert p[0].pipe_elements[0].config == 'some_source'


def test_get_pipelines_two():
    # override source op with a mock test class
    interpreter.Pipeline.PIPELINE_OPS['source'] = _TestSourceElement
    p = interpreter.get_pipelines(
        pipelines_config={
            'pipeline_one': [
                  {'source': 'some_source'}
                  ],
            'pipeline_two': [
                  {'source': 'another_source'}
                  ]
             },
            )
    assert isinstance(p[0], interpreter.Pipeline)
    assert p[0].name == 'pipeline_one'
    assert isinstance(p[0].pipe_elements[0], _TestSourceElement)
    assert isinstance(p[1], interpreter.Pipeline)
    assert p[0].pipe_elements[0].config == 'some_source'
    assert p[1].name == 'pipeline_two'
    assert isinstance(p[1].pipe_elements[0], _TestSourceElement)
    assert p[1].pipe_elements[0].config == 'another_source'

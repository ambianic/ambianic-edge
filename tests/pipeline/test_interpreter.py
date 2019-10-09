from ambianic import pipeline
from ambianic.pipeline import interpreter


def test_get_pipelines_none():
    p = interpreter.get_pipelines(pipelines_config=[])
    assert not p


class _TestSourceElement(pipeline.PipeElement):

    def __init__(self, **element_config):
        super().__init__()
        self.config = element_config
        self.start_called = False
        self.stop_called = False

    def start(self):
        super().start()
        self.start_called = True
        # send one sample down the pipe
        self.receive_next_sample([1, 2, 3])

    def heal(self):
        """Empty implementation of abstractmethod."""

    def stop(self):
        super().stop()
        self.stop_called = True

    def receive_next_sample(self, *sample):
        """Empty implementation of abstractmethod."""


def test_derived_pipe_element():
    derived_element = _TestSourceElement(element_config='something')
    assert derived_element.state == pipeline.PIPE_STATE_STOPPED


def _one_pipeline_setup():
    # override source op with a mock test class
    interpreter.Pipeline.PIPELINE_OPS['source'] = _TestSourceElement
    p = interpreter.get_pipelines(
        pipelines_config={
            'pipeline_one': [
                      {'source': {'uri': 'test'}}
                      ]
            }
        )
    return p


def test_get_pipelines_one():
    p = _one_pipeline_setup()
    print('p[0]: {p0}'.format(p0=p[0]))
    assert isinstance(p[0], interpreter.Pipeline)
    assert p[0].name == 'pipeline_one'
    assert isinstance(p[0]._pipe_elements[0], _TestSourceElement)
    assert p[0]._pipe_elements[0].config == {'uri': 'test'}


def test_get_pipelines_two():
    # override source op with a mock test class
    interpreter.Pipeline.PIPELINE_OPS['source'] = _TestSourceElement
    p = interpreter.get_pipelines(
        pipelines_config={
            'pipeline_one': [
                  {'source': {'uri': 'test'}}
                  ],
            'pipeline_two': [
                  {'source': {'uri': 'test2'}}
                  ]
             },
            )
    assert isinstance(p[0], interpreter.Pipeline)
    assert p[0].name == 'pipeline_one'
    assert isinstance(p[0]._pipe_elements[0], _TestSourceElement)
    assert isinstance(p[1], interpreter.Pipeline)
    assert p[0]._pipe_elements[0].config == {'uri': 'test'}
    assert p[1].name == 'pipeline_two'
    assert isinstance(p[1]._pipe_elements[0], _TestSourceElement)
    assert p[1]._pipe_elements[0].config == {'uri': 'test2'}


def test_pipeline_start():
    p = _one_pipeline_setup()
    assert p[0]._pipe_elements[0].state == pipeline.PIPE_STATE_STOPPED
    pe = p[0]._pipe_elements[0]
    assert isinstance(pe, _TestSourceElement)
    assert not pe.start_called
    p[0].start()
    assert p[0]._pipe_elements[0].state == pipeline.PIPE_STATE_RUNNING
    assert pe.start_called


def test_pipeline_stop():
    p = _one_pipeline_setup()
    p[0].start()
    pe = p[0]._pipe_elements[0]
    assert pe.state == pipeline.PIPE_STATE_RUNNING
    assert pe.start_called
    assert not pe.stop_called
    p[0].stop()
    # make sure the correct element is still in the correct pipe position
    pe = p[0]._pipe_elements[0]
    assert isinstance(pe, _TestSourceElement)
    assert pe.state == pipeline.PIPE_STATE_STOPPED

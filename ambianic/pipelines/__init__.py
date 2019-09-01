import logging
from .interpreter import Pipeline

log = logging.getLogger(__name__)


def get_pipelines(config):
    pps = config['pipelines']
    pipelines = []
    for pname, pdef in pps.items():
        log.info("loading %s pipeline configuration", pname)
        proc = Pipeline(pname=pname, pdef=pdef)
        pipelines.append(proc)
    return pipelines



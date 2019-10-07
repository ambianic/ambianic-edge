# ambianic

# ambianic.pipeline
Main module for Ambianic AI pipelines.
## PipeElement
```python
PipeElement(self)
```
The basic building block of an Ambianic pipeline.
### healthcheck
```python
PipeElement.healthcheck(self)
```
Check the health of this element.

:returns: (timestamp, status) tuple with most recent heartbeat
timestamp and health status code ('OK' normally).

### heartbeat
```python
PipeElement.heartbeat(self)
```
Set the heartbeat timestamp to time.monotonic().
### stop
```python
PipeElement.stop(self)
```
Receive stop signal and act accordingly.

Subclasses should override this method by
first invoking their super class implementation and then running
through steps specific to stopping their ongoing sample processing.


### connect_to_next_element
```python
PipeElement.connect_to_next_element(self, next_element=None)
```
Connect this element to the next element in the pipe.

Subclasses should not have to override this method.


### receive_next_sample
```python
PipeElement.receive_next_sample(self, **sample)
```
Receive next sample from a connected previous element.

Subclasses should not have to override this method.

:Parameters:
----------
**sample : dict
    A dict of (key, value) pairs that represent the sample.
    It is left to specialized implementations of PipeElement to specify
    their in/out sample formats and enforce compatibility with
    adjacent connected pipe elements.


### process_sample
```python
PipeElement.process_sample(self, **sample)
```
Implement processing in subclass as a generator function.

Invoked by receive_next_sample() when the previous element
(or pipeline source) feeds another data input sample.

Implementing subclasses should process input samples and yield
output samples for the next element in the pipeline.

:Parameters:
----------
**sample : dict
    A dict of (key, value) pairs that represent the sample.
    It is left to specialized implementations of PipeElement to specify
    their in/out sample formats and enforce compatibility with
    adjacent connected pipe elements.

:Returns:
processed_sample: dict
    Processed sample that will be passed to the next pipeline element.


## HealthChecker
```python
HealthChecker(self, health_status_callback=None)
```
Monitor overall pipeline throughput health.

Attaches at the end of a pipeline to monitor its health status
based on received output samples and their frequency.

### process_sample
```python
HealthChecker.process_sample(self, **sample)
```
Call health callback and pass on sample as is.
# ambianic.webapp


# ambianic

## configure
```python
configure(env_work_dir)
```
Load configuration settings

:returns config if configuration was loaded without issues.
    None or a specific exception otherwise.

## start
```python
start(env_work_dir=None)
```
Programmatic start of the main service
## stop
```python
stop()
```
Programmatic stop of the main service
# ambianic.pipeline

## PipeElement
```python
PipeElement(self)
```
The basic building block of an Ambianic pipeline
### connect_to_next_element
```python
PipeElement.connect_to_next_element(self, next_element=None)
```
Connect this element to the next element in the pipe
### receive_next_sample
```python
PipeElement.receive_next_sample(self, **sample)
```
Receive next sample from a connected previous element
:argument **kwargs a variable list of (key, value) pairs that represent the sample

## HealthChecker
```python
HealthChecker(self, health_status_callback=None)
```

Attaches at the end of a pipe to monitor its health status
based on received output samples and their frequency.

### receive_next_sample
```python
HealthChecker.receive_next_sample(self, **sample)
```
update pipeline heartbeat status
# ambianic.webapp


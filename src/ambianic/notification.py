from ambianic.util import ServiceExit, ThreadedJob, ManagedService
import time
import apprise
import logging

log = logging.getLogger(__name__)


class NotificationJob(ManagedService):
    def __init__(self, config: dict):
        # Create an Apprise instance
        self.apobj = apprise.Apprise()
        # Create an Config instance
        self.config = config.get("notifications", {})
        for name, cfg in config.get("providers", {}).items():
            self.apobj.add(cfg, tag=name)

    def notify(
        self,
        event: str, 
        providers: list = ["all"],
        title: str = None,
        message: str = None,
        attach: list = []
    ):

        labels = self.config.get("labels", {})
        templates = self.config.get("templates", {})

        if title is None:
            title = templates.get("title", "[Ambianic.ai] New {event} event" )

        if message is None:
            message = templates.get("message", "New {event} recognized")

        template_args = {
            "event_type": event,
            "event": labels.get(event, event),
        }
        title = title.safe_substitute(**template_args)
        message = message.safe_substitute(**template_args)

        for provider in providers:
            self.apobj.notify(message, title=title, tag=provider)
            log.debug("Sent notification %s to %s" % (event, provider))

class NotificationServer(ManagedService):
    def __init__(self, config):
        self.config = config
        self.notification_job = None

    def start(self, **kwargs):
        log.info('Notification server job starting...')
        f = NotificationJob(self.config)
        self.notification_job = ThreadedJob(f)
        self.notification_job.start()
        log.info('NotificationFlask server job started')

    def healthcheck(self):
        # Note: Implement actual health check for Flask
        # See if the /healthcheck URL returns a 200 quickly
        return time.monotonic(), True

    def heal(self):
        """Heal the server.

        TODO: Keep an eye for potential scenarios that cause this server to
         become unresponsive.
        """

    def stop(self):
        if self.notification_job:
            log.info('Notification server job stopping...')
            self.notification_job.stop()
            self.notification_job.join()
            log.info('Flask server job stopped.')

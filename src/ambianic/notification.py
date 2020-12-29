"""Utilities to send notifications."""

import logging
import apprise
import os
import ambianic

log = logging.getLogger(__name__)

class Notification:
    def __init__(self, event:str="notification", data:dict={}, providers:list=["all"]):
        self.event: str = event
        self.providers: list = providers
        self.title: str = None
        self.message: str = None
        self.attach: list = []
        self.data: dict = data

    def add_attachments(self, *args):
        self.attach.append(*args)

    def to_dict(self) -> dict:
        return dict(vars(self))

class NotificationHandler:
    def __init__(self, config: dict = None):
        if config is None:
            config = ambianic.config
        self.apobj = apprise.Apprise()
        self.config = config.get("notifications", {})
        for name, cfg in config.get("providers", {}).items():
            if not isinstance(cfg, list):
                cfg = [cfg]
            for provider in cfg:
                if not self.apobj.add(provider, tag=name):
                    log.warning("Failed to add notification provider: %s=%s" % (name, provider))

    def send(
        self,
        event: str, 
        providers: list = ["all"],
        title: str = None,
        message: str = None,
        attach: list = [],
        data: dict = {},
    ):

        labels = self.config.get("labels", {})
        templates = self.config.get("templates", {})

        if title is None:
            title = templates.get("title", "[Ambianic.ai] New {event} event" )

        if message is None:
            message = templates.get("message", "New {event} recognized")

        attachments = []
        for a in attach:
            if not os.path.exists(a) or not os.path.isfile(a):
                log.warning("Attachment is not a valid file %s")
                continue
            attachments.append(a)

        template_args = {
            "event_type": event,
            "event": labels.get(event, event),
        } + data
        for key, value in template_args.items():
            title = title.replace("${%s}" % key, value)
            message = message.replace("${%s}" % key, value)

        for provider in providers:
            self.apobj.notify(message, title=title,
                              tag=provider, attach=attachments)
            log.debug("Sent notification %s to %s" % (event, provider))

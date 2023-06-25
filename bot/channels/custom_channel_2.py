import inspect
import logging
from asyncio import CancelledError
from sanic import Blueprint, response
from sanic.request import Request
from typing import (
    Text,
    Optional,
    Callable,
    Awaitable,
)
from asyncio import CancelledError
from sanic.response import HTTPResponse

from rasa.core.channels.channel import (
    InputChannel,
    UserMessage,
    CollectingOutputChannel,
)

logger = logging.getLogger(__name__)

CHANNEL_NAME = "myio2"


class MyIO2(InputChannel):

    @classmethod
    def name(cls) -> Text:
        return CHANNEL_NAME

    async def _extract_sender(self, req: Request) -> Optional[Text]:
        return req.json.get("sender", None)

    # noinspection PyMethodMayBeStatic
    def _extract_message(self, req: Request) -> Optional[Text]:
        return req.json.get("message", None)

    def _extract_input_channel(self) -> Text:
        return self.name()

    def blueprint(
        self, on_new_message: Callable[[UserMessage], Awaitable[None]]
    ) -> Blueprint:
        module_type = inspect.getmodule(self)
        if module_type is not None:
            module_name = module_type.__name__
        else:
            module_name = None

        custom_webhook = Blueprint(
            "custom_webhook_{}".format(type(self).__name__),
            module_name,
        )

        @custom_webhook.route("/", methods=["GET"])
        async def health(request: Request) -> HTTPResponse:
            return response.json({"status": "ok"})

        @custom_webhook.route("/webhook", methods=["POST"])
        async def receive(request: Request) -> HTTPResponse:

            sender_id = await self._extract_sender(request)
            text = self._extract_message(request)
            if text is None:
                return response.text("OK")
            input_channel = self._extract_input_channel()
            metadata = self.get_metadata(request)

            collector = MyIO2OutputChannel()

            try:
                await on_new_message(
                    UserMessage(
                        text,
                        collector,
                        sender_id,
                        input_channel=input_channel,
                        metadata=metadata,
                    )
                )
            except CancelledError:
                logger.error(
                    "Message handling timed out for " "user message '{}'.".format(text)
                )
            except Exception as e:
                logger.exception(
                    f"An exception occurremetadatad while handling user message: {e}, text: {text}"
                )
            return response.json(collector.messages)

        return custom_webhook


class MyIO2OutputChannel(CollectingOutputChannel):
    """Output channel that collects send messages in a list

    (doesn't send them anywhere, just collects them)."""

    @classmethod
    def name(cls) -> Text:
        return CHANNEL_NAME
"""Bound transcription request bytes before FastAPI reads or validates the body."""
import re

from starlette.responses import JSONResponse


MAX_TRANSCRIPTION_BODY_BYTES = 8 * 1024 * 1024
WRITE_PATH = re.compile(
    r"^(?:/submissions/[^/]+/(?:transcriptions|recognitions|audits)|/transcriptions/[^/]+/(?:revisions|accept))/?$"
)


SCHOOL_CAPTURE = re.compile(r"^/dynamic/student/activities/[^/]+/attempts/?$")
SCHOOL_WRITE = re.compile(r"^/dynamic/(?:student/attempts/[^/]+/questions/[^/]+/(?:reading|confirm-reading|recognize)|school-attempts/[^/]+/release)/?$")


class TranscriptionBodyLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if (scope["type"] != "http" or scope["method"] != "POST"
                or not (WRITE_PATH.fullmatch(scope["path"]) or SCHOOL_CAPTURE.fullmatch(scope["path"]) or SCHOOL_WRITE.fullmatch(scope["path"]))):
            await self.app(scope, receive, send)
            return

        maximum = 60 * 1024 * 1024 if SCHOOL_CAPTURE.fullmatch(scope["path"]) else MAX_TRANSCRIPTION_BODY_BYTES
        # Do not trust Content-Length, including oversized or undersized claims.
        # Buffer at most 8 MiB before entering FastAPI or any store operation.
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > maximum:
                response = JSONResponse(
                    {"detail": f"Body acima do limite de {maximum // (1024 * 1024)} MiB."},
                    status_code=413, headers={"Cache-Control": "no-store"},
                )
                await response(scope, receive, send)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        buffered = bytes(body)
        del body
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": buffered, "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, send)

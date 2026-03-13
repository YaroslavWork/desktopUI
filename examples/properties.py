from fabric.core.service import Service, Property
from fabric import Fabricator

class MyService(Service):
    @Property(str, flags="read-write")
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str):
        self._status = value

    def get_value(self):
        return self._status

    def __init__(self, status="", **kwargs):
        super().__init__(**kwargs)
        self._status = status

example_service = MyService("Initializing")

# Connect to the notify::status signal for the status property
example_service.connect("notify::status", lambda *_: print("Status has changed"))
example_service.status = "Running"

fabricator = Fabricator(
    poll_from=lambda *_: "hello there!",
    interval=1000,
).build()\
 .connect("changed", lambda *_: print("changed"))\
 .connect("notify::value", lambda *_: print("value notified"))\
 .set_value("initial value")\
 .unwrap()  # Return the actual Fabricator, not the Builder object

print(example_service.get_value())
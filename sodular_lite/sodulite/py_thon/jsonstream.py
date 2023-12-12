import json


class JSONStream:
    @staticmethod
    def parse(root_path, callback, stream):
        return JSONStreamParser(root_path, callback, stream)

    @staticmethod
    def stringify(prettify, separator, terminator, indent, stream):
        return JSONStreamStringify(prettify, separator, terminator, indent, stream)


class JSONStreamParser:
    def __init__(self, root_path, callback, stream):
        self.root_path = root_path
        self.callback = callback
        self.stream = stream

    async def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            line = await self.stream.__anext__()
            data = json.loads(line)
            if self.root_path in data:
                return self.callback(data[self.root_path])
            return None
        except StopAsyncIteration:
            raise StopAsyncIteration


class JSONStreamStringify:
    def __init__(self, prettify, separator, terminator, indent, stream):
        self.prettify = prettify
        self.separator = separator
        self.terminator = terminator
        self.indent = indent
        self.stream = stream

    def write(self, data):
        json_data = json.dumps(data, separators=(self.separator, self.terminator),
                               indent=self.indent if self.prettify else None)
        self.stream.write(json_data)

    def end(self):
        self.stream.close()

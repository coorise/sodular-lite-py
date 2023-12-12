class Queue:
    def __init__(self):
        self.queue = []
        self.isProcessing = False

    async def add(self, task):
        return await self._processQueue(task)

    async def _processQueue(self, task=None):
        if not task:
            if len(self.queue) == 0:
                self.isProcessing = False
                return

            self.isProcessing = True
            current_task = self.queue.pop(0)
            task, resolve = current_task['task'], current_task['resolve']

            try:
                result = await task()
                resolve(result)
            except Exception as error:
                # Handle errors here
                resolve(None)

            await self._processQueue()
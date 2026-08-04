import asyncio


class Scheduler:

    def __init__(self):

        self.tasks = []

    async def add_bot(self, runner):

        task = asyncio.create_task(
            runner.start()
        )

        self.tasks.append(task)

    async def run(self):

        if self.tasks:
            await asyncio.gather(*self.tasks)
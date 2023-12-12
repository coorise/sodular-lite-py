import re
import os
import json
import asyncio
from ..utils import JsonDatabase, HTTP_RESPONSE, sanitizePath
from jsonstream import JSONStream
import aiofiles


async def writeStream(that, service='create', path='', value=None, merge=False):
    await that.acquireLock()
    try:
        resp = {
            'path': path,
            # 'key': path.split('/').pop()
        }
        error = {
            'code': HTTP_RESPONSE.ERROR_FROM_USER_CODE,
            'message': HTTP_RESPONSE.MESSAGE.ERROR_FROM_USER_CODE,
        }

        with open(that.filePath, 'r', encoding='utf8') as read_Stream, \
                open(that.filePathTemp, 'w', encoding='utf8') as write_Stream:

            pathFound = False

            def parse_callback(data):
                nonlocal pathFound
                obj = data
                that.jsonDB.data = obj

                nonlocal resp
                nonlocal pathFound
                if not pathFound:
                    nonlocal pathFound
                    resp = that.jsonDB[service](path, value, merge)
                    pathFound = True

                obj = resp['obj'] if 'obj' in resp else obj
                del resp['obj'] if 'obj' in resp else None
                return {that.rootPath: obj}

            read_Stream = JSONStream.parse(that.rootPath, parse_callback, read_Stream)
            write_Stream = JSONStream.stringify(False, None, None, 2, write_Stream)

            async for data in read_Stream:
                write_Stream.write(json.dumps(data))
                await asyncio.sleep(0)  # Allow other tasks to run

            write_Stream.end()

            del resp['obj'] if 'obj' in resp else None
            if not pathFound:
                resp['value'] = False
                resp['error'] = error
                return resp
            else:
                os.rename(that.filePathTemp, that.filePath)
                return resp

    except Exception as e:
        if that.mode == 'dev':
            print(e)
        resp['value'] = False
        resp['error'] = {
            'code': HTTP_RESPONSE.INTERNAL_ERROR_CODE,
            'message': HTTP_RESPONSE.MESSAGE.INTERNAL_ERROR_CODE,
        }

    finally:
        await that.releaseLock()


async def readStream(that, service='get', path='', value=None):
    await that.acquireLock()
    try:
        path = sanitizePath(path)
        resp = {
            'path': path,
            'key': path.split('/')[-1],
        }
        error = {
            'code': HTTP_RESPONSE.ERROR_FROM_USER_CODE,
            'message': HTTP_RESPONSE.MESSAGE.ERROR_FROM_USER_CODE,
        }

        with open(that.filePath, 'r', encoding='utf8') as stream:
            search = None
            matches = re.findall(r'(!?\[.*?\])', path)
            if matches and len(matches) > 1:
                search = path.replace(matches[0], '')
                resp['key'] = search.split('/')[-1]
                search = search.replace('/', '.')
                value = {}
            else:
                search = path.replace('/', '.')

            async def callback(data):
                nonlocal resp, found, that
                if data:
                    if value:
                        last_key = path.replace(matches[0], '').split('/')[-1]
                        that.jsonDB.data = {
                            last_key: data,
                        }
                        resp = that.jsonDB[service](f'/{path.split("/")[-1]}', value)
                    else:
                        resp['value'] = data
                    found = True

            parser = JSONStream.parse(search, callback, stream)

            found = False

            async for _ in parser:
                pass

            if not found:
                resp['value'] = False
                resp['error'] = error

        return resp

    except Exception as e:
        if that.mode == 'dev':
            print(e)
        resp['value'] = False
        resp['error'] = {
            'code': HTTP_RESPONSE.INTERNAL_ERROR_CODE,
            'message': HTTP_RESPONSE.MESSAGE.INTERNAL_ERROR_CODE,
        }
        return resp

    finally:
        await that.releaseLock()


class JsonPythonStreamDB:
    def __init__(self, file_path, mode='prod'):
        self.filePath = file_path
        self.mode = mode
        self.jsonDB = JsonDatabase()
        self.jsonDB.mode = mode
        self.rootPath = 'data'
        self.filePathLock = self.filePath + '.lock'
        self.filePathTemp = self.filePath + '.temp'

        if not os.path.exists(self.filePath):
            os.makedirs(os.path.dirname(self.filePath), exist_ok=True)
            with open(self.filePath, 'w', encoding='utf8') as f:
                json.dump({self.rootPath: {}}, f)

        else:
            with open(self.filePath, 'r', encoding='utf8') as f:
                try:
                    file_data = json.load(f)
                    if len(file_data.keys()) > 1:
                        with open(self.filePath, 'w', encoding='utf8') as wf:
                            json.dump({self.rootPath: file_data}, wf)

                    if 'data' not in file_data:
                        with open(self.filePath, 'w', encoding='utf8') as wf:
                            json.dump({self.rootPath: {}}, wf)

                except Exception as e:
                    pass

    async def acquireLock(self):
        return await asyncio.to_thread(self._acquire_lock)

    def _acquire_lock(self):
        if os.path.exists(self.filePathLock):
            return True
        else:
            os.makedirs(os.path.dirname(self.filePathLock), exist_ok=True)
            with open(self.filePathLock, 'w') as f:
                pass
            return False

    async def releaseLock(self):
        return await asyncio.to_thread(self._release_lock)

    def _release_lock(self):
        if os.path.exists(self.filePathLock):
            os.remove(self.filePathLock)
        return True

    async def get(self, path, value):
        return await self.read_stream('get', path, value)

    async def query(self, path, value):
        return await self.read_stream('query', path, value)

    async def set(self, path, value):
        return await self.create(path, value, True)

    async def create(self, path, value, merge=False):
        return await self.write_stream('create', path, value, merge)

    async def update(self, path, value, merge):
        return await self.write_stream('update', path, value, merge)

    async def delete(self, path, value):
        return await self.write_stream('delete', path, value)

    async def read_stream(self, service, path, value):
        return await readStream(self, service, path, value)

    async def write_stream(self, service, path, value, merge):
        return await writeStream(self, service, path, value, merge)

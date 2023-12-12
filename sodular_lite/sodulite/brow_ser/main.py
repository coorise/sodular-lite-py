from ..utils import JsonDatabase
from local_storage import LocalStorage
import json
import asyncio


class JsonBrowserStreamDB:
    db = {}

    def __init__(self, db_name='sodulite', mode='prod', localStorage=None):
        self.dbName = db_name
        self.mode = mode
        self.jsonDB = JsonDatabase()
        self.jsonDB.mode = mode
        self.rootPath = 'data'
        if not localStorage:
            self.localStorage = LocalStorage()
        else:
            if localStorage['getItem'] and localStorage['setItem'] and localStorage['removeItem']:
                self.localStorage = LocalStorage()
            else:
                self.localStorage = localStorage
        if not self.localStorage.getItem(db_name):
            self.localStorage.setItem(db_name, json.dumps({self.rootPath: {}}))
        try:
            file = self.localStorage.getItem(db_name)
            file = json.loads(file)
            if len(file.keys()) > 1:
                self.localStorage.setItem(db_name, json.dumps({self.rootPath: file}))
            if not file[self.rootPath]:
                self.localStorage.setItem(db_name, json.dumps({self.rootPath: {}}))
        except Exception as e:
            pass
        self.dbNameLock = db_name + '-lock'

    async def acquireLock(self):
        return await asyncio.to_thread(self._acquire_lock)

    def _acquire_lock(self):
        db_lock = self.localStorage.getItem(self.dbNameLock)
        if not db_lock:
            self.localStorage.setItem(self.dbNameLock, 'acquired')

    async def releaseLock(self):
        return await asyncio.to_thread(self._release_lock)

    def _release_lock(self):
        self.localStorage.removeItem(self.dbNameLock)

    async def _read_DB(self, db_name):
        if not db_name:
            db_name = self.dbName
        try:
            return json.loads(self.localStorage.getItem(db_name))[self.rootPath]
        except Exception as e:
            return {}

    async def _save_DB(self, db_temp):
        if db_temp:
            self.localStorage.setItem(
                self.dbName,
                json.dumps({
                    self.rootPath: db_temp,
                })
            )
            self.db = db_temp

    async def get(self, path, value):
        try:
            await self.acquireLock()
            self.jsonDB.data = await self._read_DB()
            return await self.jsonDB.get(path, value)
        finally:
            await self.releaseLock()

    async def exists(self, path):
        try:
            await self.acquireLock()
            self.jsonDB.data = await self._read_DB()
            return await self.jsonDB.exists(path)
        finally:
            await self.releaseLock()

    async def create(self, path, value, merge):
        try:
            await self.acquireLock()
            self.jsonDB.data = await self._read_DB()
            resp = await self.jsonDB.create(path, value, merge)

            if resp['obj'] and len(resp['obj'].keys()) >= 1:
                await self._save_DB(resp['obj'])
            del resp['obj']
            return resp
        finally:
            await self.releaseLock()

    async def set(self, path, value):
        return await self.create(path, value, True)

    async def update(self, path, value, mod):
        try:
            await self.acquireLock()
            self.jsonDB.data = await self._read_DB()
            resp = await self.jsonDB.update(path, value, mod)
            if resp['obj'] and len(resp['obj'].keys()) >= 1:
                await self._save_DB(resp['obj'])
            del resp['obj']
            return resp
        finally:
            await self.releaseLock()

    async def delete(self, path, value):
        try:
            await self.acquireLock()
            self.jsonDB.data = await self._read_DB()
            resp = await self.jsonDB.delete(path, value)
            if resp['obj'] and len(resp['obj'].keys()) >= 1:
                await self._save_DB(resp['obj'])
            del resp['obj']
            return resp
        finally:
            await self.releaseLock()

    async def query(self, path, option):
        try:
            await self.acquireLock()
            self.jsonDB.data = await self._read_DB()
            return await self.jsonDB.query(path, option)
        finally:
            await self.releaseLock()

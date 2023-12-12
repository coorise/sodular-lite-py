
class SoduLite:
    @staticmethod
    def init(SoduBaseConfig={'dbName': 'sodubase', 'path': 'database/', 'mode': 'prod', 'localStorage': None}):
        def db(pathDB='data', ref=None):
            async def node(parent={}, name=None, *args):
                try:
                    SoduBaseConfig['dbName'] = (
                        SoduBaseConfig['dbName']
                        .replace(r'[^\w _-]', '_')
                        .replace(r'__', '_')
                        .rstrip('_')
                    )
                    service = {}
                    if SoduBaseConfig['localStorage']:
                        browserDB = __import__('brow_ser', fromlist=['*'])
                        browserDB = getattr(browserDB, 'JsonBrowserStreamDB', None)
                        localStorage = SoduBaseConfig['localStorage']
                        attrs = [
                            SoduBaseConfig['dbName'] + '_' + pathDB,
                            SoduBaseConfig['mode'],
                            localStorage
                        ]
                        service = browserDB(*attrs)
                    else:
                        pythonDB = __import__('py_thon', fromlist=['*'])
                        pythonDB = getattr(pythonDB, 'JsonPythonStreamDB', None)
                        SoduBaseConfig['path'] = SoduBaseConfig['path'] \
                            .lstrip('/.').replace(r'[^\w /_-]', '_').replace(r'__', '_').rstrip('_')
                        path = SoduBaseConfig['path'] + \
                               '/' + SoduBaseConfig['dbName'] + \
                               '/' + pathDB

                        if not path.endswith('.json'):
                            path += '.json'
                        path = path.replace(r'//', '/')
                        service = pythonDB(path, SoduBaseConfig['mode'])

                    value, option, callback = None, None, None

                    if len(args) == 1:
                        if not callable(args[0]):
                            value = args[0]
                        else:
                            callback = args[0]
                    elif len(args) == 2:
                        value = args[0]
                        if not callable(args[1]):
                            option = args[1]
                        else:
                            callback = args[1]
                    elif len(args) >= 3:
                        value = args[0]
                        option = args[1]
                        callback = args[2]

                    parent['ref'] = lambda child_ref: db(pathDB, child_ref)
                    parent['child'] = lambda child_ref: db(pathDB, ref + '/' + child_ref)
                    resp = await getattr(service, name)(ref, value, option)

                    if callable(callback):
                        callback({**resp, **parent})
                    else:
                        return {**resp, **parent}
                except Exception as e:
                    if SoduBaseConfig['mode'] == 'dev':
                        print(e)
                    return {**parent}

            crud = {
                'create': lambda *args: node(crud, 'create', *args),
                'set': lambda *args: node(crud, 'set', *args),
                'get': lambda *args: node(crud, 'get', *args),
                'update': lambda *args: node(crud, 'update', *args),
                'delete': lambda *args: node(crud, 'delete', *args),
                'query': lambda *args: node(crud, 'query', *args),
            }
            return crud

        return {
            'load': lambda file='data': {'ref': lambda ref: db(file, ref)}
        }

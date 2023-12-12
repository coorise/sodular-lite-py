import re
from ..http_resp import HTTP_RESPONSE


def isValidPath(path):
    # print('path is: ', path)
    if not isinstance(path, str):
        return {
            'path': path,
            'error': {
                'code': HTTP_RESPONSE.PAGE_NOT_FOUND_CODE,
                'message': HTTP_RESPONSE.MESSAGE.PAGE_NOT_FOUND_CODE,
            },
        }


def sanitizePath(path):
    try:
        if not path.startswith('/'):
            path = '/' + path
        if len(path) > 1 and path.endswith('/'):
            path = path.rstrip('/')
        path = path.replace('//', '/')
    except Exception as e:
        pass

    return path


def getArrayParam(path):
    result = {'path': path, 'value': None, 'mod': {}}
    matches = re.findall(r'(!?\[.*?\])', path)
    if len(matches) > 1:
        try:
            param = matches[0]
            if re.match(r'^\[\d+\]$', param):
                result['mod']['withFunc'] = 'get'  # Case [x]
                result['value'] = int(param[1:-1])
            elif re.match(r'^!\[\d+\]$', param):
                result['mod']['withFunc'] = 'remove'  # Case ![x]
                result['mod']['notIn'] = True
                result['value'] = int(param[2:-1])
            elif re.match(r'^\[\d+:\d+\]$', param):
                result['mod']['withFunc'] = 'getInterval'  # Case [x:y]
                result['value'] = list(map(int, param[1:-1].split(':')))
            elif re.match(r'^!\[\d+:\d+\]$', param):
                result['mod']['withFunc'] = 'getNotInterval'  # Case ![x:y]
                result['mod']['notIn'] = True
                result['value'] = list(map(int, param[2:-1].split(':')))
            elif re.match(r'^\[\d+(,\d+)*\]$', param):
                result['mod']['withFunc'] = 'getOnly'  # Case [x,y,...]
                result['value'] = list(map(int, param[1:-1].split(',')))
            elif re.match(r'^!\[\d+(,\d+)*\]$', param):
                result['mod']['withFunc'] = 'getAllExcept'  # Case ![x,y,z,...]
                result['mod']['notIn'] = True
                result['value'] = [int(x) for x in filter(None, param[2:-1].split(','))]
            elif re.match(r'^\[(\?(-)*\d+)\]$', param):
                result['mod']['withFunc'] = 'getAllTill'  # Case [?x] or [?-x]
                value_str = re.search(r'\d+', param).group()  # Extract the number x
                result['mod']['till'] = True
                if '-' not in param:
                    result['value'] = int(value_str)
                else:
                    result['mod']['reverse'] = True
                    result['value'] = -int(value_str)
        except Exception as e:
            pass

        result['path'] = path.replace(matches[0], '')

    return result


def operationInObj(object_data):
    data = object_data

    if isinstance(object_data, list):
        data = object_data.copy()
    elif isinstance(object_data, dict):
        data = object_data.copy()

    def insert(key_value, index=None):
        nonlocal data
        if isinstance(data, list):
            if index is None:
                data.append(key_value[1])
            else:
                data.insert(index, key_value[1])
        else:
            if key_value[0] is not None:
                result = data.copy()
                if index is None:
                    result[key_value[0]] = key_value[1]
                else:
                    keys = list(result.keys())
                    keys.insert(index, key_value[0])
                    new_obj = {}
                    for k, i in zip(keys, range(len(keys))):
                        if k == key_value[0]:
                            new_obj[k] = key_value[1]
                        else:
                            new_obj[k] = result[k]
                    result = new_obj
                data = result
        return data

    def remove(x=0):
        nonlocal data
        if isinstance(data, list):
            if x >= 0:
                data.pop(x)
            else:
                data.pop(len(data) + x)
        else:
            result = data.copy()
            if x >= 0:
                del result[list(data.keys())[x]]
            else:
                del result[list(data.keys())[len(data) + x]]
            data = result
        return data

    def get(x=0):
        if isinstance(data, list):
            if x >= 0:
                return data[x]
            else:
                return data[len(data) + x]
        else:
            is_integer = int(x)
            if is_integer:
                result = data.copy()
                keys = list(result.keys())
                index = is_integer
                if is_integer == -1:
                    index = len(keys) - 1
                return {keys[index]: data[keys[index]]}
            return data[x]

    def getInterval(x=0, y=0):
        if isinstance(data, list):
            return data[x:y + 1]
        else:
            result = {}
            keys = list(data.keys())[x:y + 1]
            for key in keys:
                result[key] = data[key]
            return result

    def getNotInterval(x=0, y=0):
        if isinstance(data, list):
            return [val for i, val in enumerate(data) if i < x or i > y]
        else:
            result = {}
            keys = list(data.keys())
            for i, key in enumerate(keys):
                if i < x or i > y:
                    result[key] = data[key]
            return result

    def getAllTill(x=0):
        if isinstance(data, list):
            if x >= 0:
                return data[:x + 1]
            else:
                return data[x:]
        else:
            result = {}
            keys = list(data.keys())
            if x >= 0:
                for key in keys[:x + 1]:
                    result[key] = data[key]
            else:
                for key in keys[x:]:
                    result[key] = data[key]
            return result

    def getOnly(*indexes):
        if isinstance(data, list):
            return [data[idx] for idx in indexes]
        else:
            result = {}
            for idx in indexes:
                key = list(data.keys())[idx]
                if key:
                    result[key] = data[key]
            return result

    def getAllExcept(*indexes):
        if isinstance(data, list):
            return [val for i, val in enumerate(data) if i not in indexes]
        else:
            result = data.copy()
            for idx in indexes:
                key = list(result.keys())[idx]
                if key:
                    del result[key]
            return result

    return {
        'insert': insert,
        'remove': remove,
        'get': get,
        'getInterval': getInterval,
        'getNotInterval': getNotInterval,
        'getAllTill': getAllTill,
        'getOnly': getOnly,
        'getAllExcept': getAllExcept,
    }

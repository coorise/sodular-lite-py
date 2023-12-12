import re
from ..path import getArrayParam,\
  operationInObj,\
  sanitizePath,\
  isValidPath
from ..http_resp import HTTP_RESPONSE


class JsonDatabase:
    mode = 'prod'
    data = {}

    def __init__(self, data={}):
        self.data = data

    def exists(self, path):
        isValidPath(path)
        path = sanitizePath(path)
        resp = {
            'path': path,
            'key': path.split('/').pop(),
        }
        get = self.get(path)
        value = get.get('value', None)

        if value:
            resp['value'] = True
        else:
            resp['value'] = False
            resp['error'] = {
                'code': HTTP_RESPONSE.PAGE_NOT_FOUND_CODE,
                'message': HTTP_RESPONSE.MESSAGE.PAGE_NOT_FOUND_CODE,
            }

        return resp

    def create(self, path, value, merge=False):
        isValidPath(path)
        path = sanitizePath(path)
        resp = {
            'path': path,
            'key': path.split('/').pop(),
        }
        isExist = self.exists(path)

        if isExist['value'] and not merge:
            return {
                **resp,
                'value': False,
                'error': {
                    'code': HTTP_RESPONSE.FORBIDDEN_CODE,
                    'message': HTTP_RESPONSE.MESSAGE.FORBIDDEN_CODE,
                },
            }

        keys = [key for key in path.split('/') if key]  # Split the path into keys

        try:
            obj = self.data
            current = obj
            pathFound = False
            if not pathFound:
                for i in range(len(keys)):
                    key = keys[i]

                    if i == len(keys) - 1:
                        if (
                            merge
                            and current[key]
                            and isinstance(current[key], dict)
                            and isinstance(value, dict)
                        ):
                            # Merge the existing object with the new value
                            if (
                                isinstance(current[key], list)
                                and isinstance(value, list)
                            ):
                                current[key] += value
                            else:
                                current[key] = {**current[key], **value}
                            pathFound = True
                        else:
                            # Replace the value
                            current[key] = value
                            resp['value'] = value
                            pathFound = True
                    else:
                        # Continue traversing the object
                        if not current[key]:
                            # Create an empty object if the key doesn't exist
                            current[key] = {}
                        current = current[key]
            if resp['value']:
                resp['obj'] = obj
        except Exception as e:
            if self.mode == 'dev':
                print(e)
            resp['obj'] = self.data
            resp['value'] = False
            resp['error'] = {
                'code': HTTP_RESPONSE.INTERNAL_ERROR_CODE,
                'message': HTTP_RESPONSE.MESSAGE.INTERNAL_ERROR_CODE,
            }

        return resp

    def set(self, path, value):
        # use set to override existing value
        return self.create(path, value, True)

    def get(self, path, valueObj=None):
        isValidPath(path)
        path = sanitizePath(path)
        resp = {
            'path': path,
            'key': path.split('/').pop(),
        }

        keys = [key for key in path.split('/') if key]  # Split the path into keys
        value = self.data
        try:
            if valueObj:
                query = self.query(path, {'filter': valueObj, 'pagination': {'page': 1, 'limit': 1}})
                if query['value'] and len(query['value']) >= 1:
                    value = query['value'][0]['value']
                    resp['path'] = query['value'][0]['path']
                    resp['key'] = query['value'][0]['key']
                else:
                    value = None
            else:
                if len(path) > 1:
                    for key in keys:
                        if value and isinstance(value, dict) and key in value:
                            value = value[key]
                        else:
                            value = None
                if value:
                    resp['value'] = value
                else:
                    resp['value'] = False
                    resp['error'] = {
                        'path': path,
                        'code': HTTP_RESPONSE.PAGE_NOT_FOUND_CODE,
                        'message': HTTP_RESPONSE.MESSAGE.PAGE_NOT_FOUND_CODE,
                    }
        except Exception as e:
            if self.mode == 'dev':
                print(e)
            resp['value'] = False
            resp['error'] = {
                'code': HTTP_RESPONSE.INTERNAL_ERROR_CODE,
                'message': HTTP_RESPONSE.MESSAGE.INTERNAL_ERROR_CODE,
            }

        return resp

    def update(self, path, value, mod={}):
        result = self.exists(path)
        if not result['value']:
            return result
        isValidPath(path)
        path = sanitizePath(path)
        resp = {
            'path': path,
            'key': path.split('/').pop(),
        }

        segments = [segment for segment in path.split('/') if segment]  # Split the path into keys
        obj = self.data
        current = obj
        try:
            for i in range(len(segments) - 1):
                segment = segments[i]
                current[segment] = current.get(segment, {})
                current = current[segment]
            lastSegment = segments[-1]
            if (
                    current.get(lastSegment)
                    and isinstance(current[lastSegment], dict)
                    and isinstance(value, dict)
                    and mod.get('merge')
            ):
                if isinstance(current[lastSegment], list):
                    mainArray = current[lastSegment]
                    if mod.get('insertAt') and len(mainArray) > int(mod.get('insertAt')):
                        part1 = mainArray[: int(mod['insertAt'])]
                        part2 = mainArray[int(mod['insertAt']):]
                        value = part1 + value + part2
                    else:
                        value = mainArray + value
                else:
                    mainObj = current[lastSegment]
                    mainArray = list(mainObj.keys())
                    if mod.get('insertAt') and len(mainArray) > int(mod.get('insertAt')):
                        part1 = mainArray[: int(mod['insertAt'])]
                        object1 = {key: mainObj[key] for key in part1}
                        part2 = mainArray[int(mod['insertAt']):]
                        object2 = {key: mainObj[key] for key in part2}
                        value = {**object1, **value, **object2}
                    else:
                        value = {**mainObj, **value}
                current[lastSegment] = value
            else:
                current[lastSegment] = value
            resp['value'] = value
            resp['obj'] = obj
        except Exception as e:
            if self.mode == 'dev':
                print(e)
            resp['obj'] = self.data
            resp['value'] = False
            resp['error'] = {
                'code': HTTP_RESPONSE.INTERNAL_ERROR_CODE,
                'message': HTTP_RESPONSE.MESSAGE.INTERNAL_ERROR_CODE,
            }

        return resp

    def delete(self, path, value):
        result = self.exists(path)
        if not result['value']:
            return result
        isValidPath(path)
        if isinstance(value, dict) and not isinstance(value, list):
            result = self.get(path, value)
            if result['value']:
                resp = {
                    'path': path,
                    'key': path.split('/').pop(),
                    'value': {},
                    'obj': {},
                }
                try:
                    keys = list(result.get('value', {}).keys())
                    for key in keys:
                        savedVal = result['value'][key]
                        delValue = self.remove(result['path'] + '/' + key)
                        if delValue['value']:
                            resp['value'][key] = savedVal
                            resp['path'] = result['path']
                            resp['key'] = result['key']
                            resp['obj'] = delValue['obj']
                except Exception as e:
                    if self.mode == 'dev':
                        print(e)
                    resp['value'] = None
                    resp['obj'] = self.data
                    resp['error'] = {
                        'code': HTTP_RESPONSE.INTERNAL_ERROR_CODE,
                        'message': HTTP_RESPONSE.MESSAGE.INTERNAL_ERROR_CODE,
                    }
                return resp
            else:
                return result
        else:
            return self.remove(path)

    def remove(self, path):
        result = self.exists(path)
        if not result['value']:
            return result
        path = sanitizePath(path)
        resp = {
            'path': path,
            'key': path.split('/').pop(),
        }

        keys = [key for key in path.split('/') if key]  # Split the path into keys

        obj = self.data
        current = obj
        pathFound = False
        try:
            for i in range(len(keys)):
                key = keys[i]

                if current.get(key) and i == len(keys) - 1:
                    # Last key in the path
                    resp['value'] = current[key]
                    del current[key]
                    pathFound = True
                else:
                    # Continue traversing the object
                    if not current.get(key):
                        # Create an empty object if the key doesn't exist
                        resp['value'] = False
                        pathFound = True
                        i = len(keys) + 1
                    else:
                        current = current[key]
            if resp['value']:
                resp['obj'] = obj
        except Exception as e:
            if self.mode == 'dev':
                print(e)
            resp['obj'] = self.data
            resp['value'] = False
            resp['error'] = {
                'code': HTTP_RESPONSE.INTERNAL_ERROR_CODE,
                'message': HTTP_RESPONSE.MESSAGE.INTERNAL_ERROR_CODE,
            }

        return resp

    def queryPath(self, path):
        isValidPath(path)
        path = sanitizePath(path)
        resp = {'path': path}
        error = {
            'code': HTTP_RESPONSE.ERROR_FROM_USER_CODE,
            'message': HTTP_RESPONSE.MESSAGE.ERROR_FROM_USER_CODE,
        }
        try:
            matches = re.findall(r'(!?\[.*?\])', path)  # we capture the parameter [x], ![x], ...etc
            data = self.get(path.replace(matches[0], ''))  # we remove parameters from path
            if isinstance(data.get('value'), dict):
                try:
                    resp['key'] = data['key']
                    result = None
                    objectOperation = operationInObj(data['value'])
                    getParam = getArrayParam(path)
                    switchCases = {
                        'get': objectOperation.get,
                        'remove': objectOperation.remove,
                        'getInterval': objectOperation.getInterval,
                        'getNotInterval': objectOperation.getNotInterval,
                        'getAllTill': objectOperation.getAllTill,
                        'getOnly': objectOperation.getOnly,
                        'getAllExcept': objectOperation.getAllExcept,
                    }
                    method = switchCases.get(getParam['mod']['withFunc'], None)
                    if method:
                        result = method(*getParam['value'])
                        resp['params'] = matches[0]
                        resp['key'] = getParam['value']
                        if result:
                            resp['value'] = result
                        else:
                            resp['value'] = False
                            resp['error'] = error
                    else:
                        resp['params'] = matches[0]
                        resp['value'] = False
                        resp['error'] = error
                except Exception as e:
                    if self.mode == 'dev':
                        print(e)
                    resp['value'] = False
                    resp['error'] = error
            else:
                resp['value'] = False
                resp['error'] = error
        except Exception as e:
            resp['value'] = False
            resp['error'] = {
                'code': HTTP_RESPONSE.INTERNAL_ERROR_CODE,
                'message': HTTP_RESPONSE.MESSAGE.INTERNAL_ERROR_CODE,
            }

        return resp

    def query(self, path, options=None):
        if options is None:
            options = {}

        isValidPath(path)
        matches = re.findall(r'(!?\[.*?\])', path)
        if len(matches) > 1:
            return self.queryPath(path)

        path = sanitizePath(path)
        results = []
        response = {
            'path': path,
            'key': path.split('/').pop(),
        }

        try:
            def applyFilter(data):
                if not options.get('filter', {}):
                    return True
                return all(compare(data[key], options['filter'][key]) for key in options['filter'])

            def hasProperties(parent, child):
                if not isinstance(parent, dict):
                    return False
                for key in child:
                    if key not in parent or (
                            isinstance(parent[key], dict) and not hasProperties(parent[key], child[key])):
                        return False
                return True

            def deepEqual(a, b):
                if a is b:
                    return True
                if type(a) is not type(b):
                    return False
                if isinstance(a, list):
                    return len(a) == len(b) and all(deepEqual(x, y) for x, y in zip(a, b))
                if isinstance(a, dict):
                    return len(a) == len(b) and all(k in b and deepEqual(a[k], b[k]) for k in a)
                return a == b

            def compare(value, condition):
                if isinstance(condition, dict):
                    operator = next(iter(condition))
                    operand = condition[operator]
                    switchCases = {
                        '$<': lambda v, o: v < o,
                        '_lt': lambda v, o: v < o,
                        '$>': lambda v, o: v > o,
                        '_gt': lambda v, o: v > o,
                        '$=': lambda v, o: deepEqual(v, o),
                        '_eq': lambda v, o: deepEqual(v, o),
                        '$!=': lambda v, o: not deepEqual(v, o),
                        '_neq': lambda v, o: not deepEqual(v, o),
                        '$>=': lambda v, o: v >= o,
                        '_gte': lambda v, o: v >= o,
                        '$<=': lambda v, o: v <= o,
                        '_lte': lambda v, o: v <= o,
                        '$match': lambda v, o: re.match(o, v),
                        '$!match': lambda v, o: not re.match(o, v),
                        '$includes': lambda v, o: o in v,
                        '$!includes': lambda v, o: o not in v,
                        '$between': lambda v, o: o[0] <= v <= o[1],
                        '$!between': lambda v, o: not (o[0] <= v <= o[1]),
                        '$has': lambda v, o: hasProperties(v, o),
                        '$!has': lambda v, o: not hasProperties(v, o),
                        '$like': lambda v, o: re.match(f'^{o.replace("*", ".*")}$', v),
                        '$!like': lambda v, o: not re.match(f'^{o.replace("*", ".*")}$', v),
                        '$reg': lambda v, o: re.match(o, v),
                    }
                    method = switchCases.get(operator)
                    if method:
                        return method(value, operand)
                    else:
                        return False
                else:
                    return value == condition

            def createGlobMatcher(globPattern):
                regexPattern = '/'.join([
                    '.*?' if segment == '**' else re.escape(segment).replace(r'\*', '[^/]*').replace(r'\?', '.')
                    for segment in globPattern.split('/')
                ])
                regex = re.compile(f'^{regexPattern}$')
                return lambda s: bool(regex.match(s))

            def shouldInclude(path, newPath):
                newPath = re.sub(r'/+', '/', newPath)
                return any(createGlobMatcher(path + '/' + child)(newPath) for child in
                           options.get('mod', {}).get('with', [])) or '*' in options.get('mod', {}).get('with', [])

            def applyModifiers(obj):
                if options.get('mod', {}).get('rm') and options.get('mod', {}).get('only'):
                    del options['mod']['rm']
                if options.get('mod', {}).get('only'):
                    obj = {key: obj[key] for key in options['mod']['only'] if key in obj}
                if options.get('mod', {}).get('rm'):
                    for item in options['mod']['rm']:
                        obj.pop(item, None)
                if options.get('mod', {}).get('rm', []) == ['*']:
                    obj = {}
                return obj

            def traverse(currentPath, obj):
                for key, value in obj.items():
                    newPath = f'{currentPath}/{key}/'.replace(r'/+', '/')
                    if isinstance(value, dict) and (len(path) + 1 >= len(currentPath) or shouldInclude(path, newPath)):
                        traverse(newPath, value)
                    elif applyFilter(obj):
                        applyModifiers(obj)
                        currentPath = f'/{currentPath}'.replace(r'/+', '/').rstrip('/')
                        results.append({
                            'path': currentPath,
                            'key': currentPath.split('/').pop(),
                            'value': obj,
                        })
                        break

            startingNode = self.get(response['path'])
            startingNode = startingNode.get('value')
            if isinstance(startingNode, dict):
                traverse(response['path'], startingNode)

            if options.get('sort') and options['sort']:
                results.sort(key=lambda x: x['value'][options['sort']], reverse=options['sort'].lower() == 'desc')

            if not isinstance(options.get('pagination'), dict):
                options['pagination'] = {}

            if options['pagination']:
                page = options['pagination'].get('page', 1)
                limit = options['pagination'].get('limit', 10)
                startIndex = (page - 1) * limit
                endIndex = startIndex + limit
                if len(results) >= 1:
                    response['pagination'] = {'max': len(results), 'page': page, 'limit': limit}
                response['value'] = results[startIndex:endIndex]
        except Exception as e:
            if self.mode == 'dev':
                print(e)
            response['value'] = False
            response['error'] = {
                'code': HTTP_RESPONSE.INTERNAL_ERROR_CODE,
                'message': HTTP_RESPONSE.MESSAGE.INTERNAL_ERROR_CODE,
            }

        return response
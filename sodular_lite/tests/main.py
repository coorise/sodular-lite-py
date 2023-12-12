from ..sodulite import SoduLite


async def main():
    # Example usage:

    db = SoduLite.init({
        'dbName': 'sodulite @&',  # We use regex to replace any special character with '_'
        'path': './database@/project-Z $é/',
        # Same for path, using '/xxxx' or './xxxx' is not necessary because we use the root of the project only.
        'mode': 'dev',
    })
    db = db['load']('data')  # If .json is not supplied, we will add it. We only support JSON file
    op = None

    # op = await db
    #     .ref('/members/users/0')
    #     .create({'name': 'Alice'})
    #     .then((node) => {
    #         print('Create Alice: ', {
    #             'path': node.path,
    #             'key': node.key,
    #             'value': node.value,
    #             'error': node.error,
    #         })
    #     })
    #     .catch((e) => {
    #         print('Create Alice Error: ', e)
    #     })

    # op = await db
    #     .ref('/members/users/1')
    #     .create({'name': 'Bob'})
    #     .catch((e) => {
    #         print('Create Bob Error: ', e)
    #     })
    # print('Create Bob:', {
    #     'path': op.path,
    #     'key': op.key,
    #     'value': op.value,
    #     'error': op.error,
    # })

    alice = await db.ref('/members/users/0').get().catch(lambda e: print('Get Alice Error: ', e))
    print('Get Alice:', {
        'path': alice.path,
        'key': alice.key,
        'value': alice.value,
        'error': alice.error,
    })

    # await db.update('/members/users/0', {'age': 30})  # without merge, it will override the existing value
    # op = await db
    #     .ref('/members/users/0')
    #     .update({'age': 30}, {'merge': True})
    #     .catch((e) => {
    #         print('Update Alice Error: ', e)
    #     })
    # print('Update Alice:', {
    #     'path': op.path,
    #     'key': op.key,
    #     'value': op.value,
    #     'error': op.error,
    # })

    # bob = await db.ref('/members/users')
    # bob = await bob
    #     .delete({'name': 'Bob'})
    #     .then((node) => {
    #         print('Delete Bob: ', {
    #             'path': node.path,
    #             'key': node.key,
    #             'value': node.value,
    #             'error': node.error,
    #         })
    #     })
    #     .catch((e) => {
    #         print('Delete Bob Error: ', e)
    #     })

    op = await db.ref('/members/users[0;1]').query(
        None, lambda snapshot: print('Query Alice: ', {
            'path': snapshot.path,
            'key': snapshot.key,
            'value': snapshot.value,
            'error': snapshot.error,
        })
    ).catch(lambda e: print('Query Alice Error: ', e))


# Run the main function
main()

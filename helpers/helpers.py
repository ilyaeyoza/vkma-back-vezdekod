

def ids_check(ids):
    if len(ids) > 1000:
        return False

    for id in ids:
        if type(id) != int:
            return False

        if id < 0:
            return False

    return True
def getObjectByIdOrNone(A, k):
    try:
        A = A.order_by('id')
    except AttributeError:
        return next((o for o in A if o.id == int(k)))

    lo = 0
    hi = A.count() - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if A[mid].id == int(k):
            return A[mid]
        else:
            if A[mid].id < int(k):
                lo = mid + 1
            else:
                hi = mid - 1
    return None


def getObjectById(A, k):
    return next((o for o in A if int(o.id) == int(k)))


def getObjectByInternalKey(A, k):
    return next((o for o in A if o.internalKey == k))


def getObjectByCode(A, k):
    return next((o for o in A if o.code == k))

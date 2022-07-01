def getObjectByIdOrNone(A, k):
    A = A.order_by('id')
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

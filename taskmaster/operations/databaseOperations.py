def getObjectByIdOrNone(objects, pk):
    return next((o for o in objects if o.id == int(pk)), None)

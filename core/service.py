import re

ticketPattern = re.compile(r'^([A-Z]+)-?(\d+)$')


def normalizeTicketInput(rawInput):
    cleanedInput = re.sub(r'\s+', '', rawInput).upper()

    parts = cleanedInput.split(',')
    normalizedTickets = set()

    for part in parts:
        if not part:
            continue

        match = ticketPattern.match(part)
        if not match:
            continue

        prefix, number = match.groups()
        normalizedTickets.add(f"{prefix}-{number}")

    return list(normalizedTickets)


def updateOrderNoForListOfObjects(model, ids):
    orderNoInOrder = sorted(m.orderNo for m in model)
    idAndModelMap = {m.id: m for m in model}

    for index, _id in enumerate(ids):
        idAndModelMap[int(_id)].orderNo = orderNoInOrder[index]
    return model

import re

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q

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


def buildQuotedAwareSearchQuery(queryset, searchTerm, searchFields):
    """
    Builds a Django Q object for quote-aware multi-field search.

    Args:
        queryset: initial queryset (not modified)
        searchTerm: search string, can contain single/double quotes
        searchFields: list of field names to search in

    Returns:
        Filtered queryset
    """
    if not searchTerm:
        return queryset

    # Extract quoted phrases (single or double quotes)
    quotedPhrases = re.findall(r'"([^"]+)"|\'([^\']+)\'', searchTerm)
    quotedPhrases = [q[0] or q[1] for q in quotedPhrases]

    # Remove quoted phrases from searchTerm
    tempSearch = re.sub(r'"[^"]+"|\'[^\']+\'', '', searchTerm)
    words = tempSearch.split()

    # Prepare components
    quotedPhrasesComponents = [{'value': phrase, 'exact': True} for phrase in quotedPhrases]
    wordsComponents = [{'value': word, 'exact': False} for word in words]
    searchComponents = quotedPhrasesComponents + wordsComponents

    combinedQ = Q()
    for component in searchComponents:
        componentQ = Q()
        for field in searchFields:
            # Determine if the field is a direct field on the model
            rootField = field.split('__')[0]
            try:
                modelField = queryset.model._meta.get_field(rootField)
                isDirectField = not (modelField.is_relation and not modelField.many_to_many)
            except FieldDoesNotExist:
                isDirectField = False

            if component['exact'] and isDirectField:
                # Only direct fields support regex
                pattern = rf'\b{re.escape(component["value"])}\b'
                componentQ |= Q(**{f"{field}__iregex": pattern})
            else:
                # Related fields or unquoted words
                componentQ |= Q(**{f"{field}__icontains": component["value"]})
        combinedQ &= componentQ  # AND between components

    return queryset.filter(combinedQ)

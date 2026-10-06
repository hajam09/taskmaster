from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from core.models import Ticket, TicketLink


@login_required
def ticketView(request, url):
    # 11 queries
    ticket = get_object_or_404(
        Ticket,
        url=url,
    )
    if request.method == 'POST' and 'delete-ticket' in request.POST:
        ticket.delete()

        history = request.session.get('history', [])
        for url in reversed(history):
            if url != request.path:
                return redirect(url)

        return redirect(ticket.columnStatus.column.board.getUrl)

    context = {
        'ticket': ticket,
        'linkTypeChoices': TicketLink.LinkType.choices,
    }
    return render(request, 'ticket/ticket.html', context)

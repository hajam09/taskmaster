from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from core.models import Ticket, TicketLink


@login_required
def ticketView(request, url):
    ticket = get_object_or_404(
        Ticket.objects.select_related(
            'reporter', 'assignee', 'columnStatus__column',
        ).prefetch_related(
            'epicTickets__columnStatus__column',
            # 'ticketSubTask__subTask__columnStatus__column',
        ),
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

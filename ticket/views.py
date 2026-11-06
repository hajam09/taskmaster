from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from core.forms import TicketForm
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


@login_required
def newTicketView(request):
    if request.method == 'POST':
        form = TicketForm(request, request.POST)

        if form.is_valid():
            ticket = form.save()
            return JsonResponse({
                'success': True,
                'message': 'Ticket created successfully!',
                'redirectUrl': ticket.getUrl,
            })

        html = render_to_string('ticket/partials/ticket-form.html', {'form': form}, request)
        return JsonResponse({
            'success': False,
            'html': html
        })

    form = TicketForm(request)
    return render(request, 'ticket/partials/ticket-form.html', {'form': form})

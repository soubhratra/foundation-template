from allauth.account.adapter import get_adapter as get_account_adapter
from allauth.headless.account.views import SessionView
from django.http import HttpResponse


class HeadlessSessionView(SessionView):
    def delete(self, request, *args, **kwargs):
        adapter = get_account_adapter()
        adapter.logout(request)
        return HttpResponse(status=204)

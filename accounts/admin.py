from django.contrib import admin

from .models import Account, Transaction


class TransactionInline(admin.TabularInline):
    model = Transaction
    fk_name = "account"
    extra = 0
    readonly_fields = ("timestamp",)
    raw_id_fields = ("counterparty_account",)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("account_number", "user", "balance")
    list_select_related = ("user",)
    search_fields = ("account_number", "user__email")
    readonly_fields = ("balance",)
    inlines = [TransactionInline]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "account", "type", "amount", "timestamp", "counterparty_account")
    list_filter = ("type",)
    list_select_related = ("account", "counterparty_account")
    raw_id_fields = ("account", "counterparty_account")
    readonly_fields = ("timestamp",)

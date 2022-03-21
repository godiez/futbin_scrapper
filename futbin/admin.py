from django.contrib import admin
from futbin.models import Percent, Card, Player, PlayerCardPrices


# Register your models here.
@admin.register(Percent)
class PercentAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        count_record = Percent.objects.all().count()
        return True if count_record == 0 else False


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    pass


class PlayerCardPricesInline(admin.TabularInline):
    model = PlayerCardPrices
    fields = ('card', 'price', 'ratio', 'date')

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    inlines = [PlayerCardPricesInline]




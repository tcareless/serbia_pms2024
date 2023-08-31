from django.shortcuts import render
from datetime import datetime

from .models import PartForMachineEvent
from .forms import PartForMachineDate
from .forms import PartForMachineEventForm


def part_for_machine(request):
    context = {}
    context['page_datetime_form'] = PartForMachineDate(initial={'page_datetime': datetime.today()})
    context["event_form"] = PartForMachineEventForm()

    if request.method == 'GET':
        load_data(context)
    if request.method == 'POST':
        date = PartForMachineDate(request.POST)
        event = PartForMachineEventForm(request.POST)
        if date.is_valid() and 'specific' in request.POST:
            context['page_datetime_form'] = PartForMachineDate(initial={'page_datetime': date.cleaned_data.get('page_datetime')})
            load_data(context, date.cleaned_data.get('page_datetime'))
        # The value in the pagedatetime form is mirrored to the event form.
        if event.is_valid() and 'event' in request.POST:
            PartForMachineEvent.objects.create(datetime=event.cleaned_data.get('datetime'), asset=event.cleaned_data.get('asset'), line=event.cleaned_data.get('line'), part=event.cleaned_data.get('part'))
            load_data(context)
    return render(request, f"part_for_machine/part_for_machine.html", context)


# If there is no provided datetime, the latest entry for each tuple is chosen.
def load_data(context, target = None):
    context["data"] = {}
    context["data"]["ab1vrx"] = {}
    context["data"]["ab1vod"] = {}
    context["data"]["ab1vinput"] = {}
    context["data"]["10r140rear"] = {}
    context["data"]["trilobesinter"] = {}
    context["data"]["trilobeoptimized"] = {}
    context["data"]["trilobe"] = {}
    context["data"]["trilobeoffline"] = {}
    context["data"]["10r80mainline"] = {}
    context["data"]["10r80offline"] = {}
    context["data"]["10r80uplift"] = {}
    context["data"]["10r60mainline"] = {}

    table_cell = []
    table_cell.append(('ab1vrx', '1703l'))
    table_cell.append(('ab1vrx', '1740l'))
    table_cell.append(('ab1vrx', '658'))
    table_cell.append(('ab1vrx', '661'))
    table_cell.append(('ab1vrx', '662'))
    table_cell.append(('ab1vrx', '1703r'))
    table_cell.append(('ab1vrx', '1704r'))
    table_cell.append(('ab1vrx', '616'))
    table_cell.append(('ab1vrx', '623'))
    table_cell.append(('ab1vrx', '617'))
    table_cell.append(('ab1vrx', '1727'))
    table_cell.append(('ab1vrx', '659'))
    table_cell.append(('ab1vrx', '626'))
    table_cell.append(('ab1vrx', '1712'))
    table_cell.append(('ab1vrx', '1716l'))
    table_cell.append(('ab1vrx', '1719'))
    table_cell.append(('ab1vrx', '1723'))
    table_cell.append(('ab1vrx', '1724'))
    table_cell.append(('ab1vrx', '1725'))
    table_cell.append(('ab1vrx', '1750'))
    table_cell.append(('ab1vod', '1705'))
    table_cell.append(('ab1vod', '1746'))
    table_cell.append(('ab1vod', '621'))
    table_cell.append(('ab1vod', '629'))
    table_cell.append(('ab1vod', '785'))
    table_cell.append(('ab1vod', '1748'))
    table_cell.append(('ab1vod', '1718'))
    table_cell.append(('ab1vod', '669'))
    table_cell.append(('ab1vod', '1726'))
    table_cell.append(('ab1vod', '1722'))
    table_cell.append(('ab1vod', '1713'))
    table_cell.append(('ab1vod', '1716r'))
    table_cell.append(('ab1vod', '1719'))
    table_cell.append(('ab1vod', '1723'))
    table_cell.append(('ab1vod', '1724'))
    table_cell.append(('ab1vod', '1725'))
    table_cell.append(('ab1vod', '1750'))
    table_cell.append(('ab1vinput', '1740l'))
    table_cell.append(('ab1vinput', '1740r'))
    table_cell.append(('ab1vinput', '1701l'))
    table_cell.append(('ab1vinput', '1701r'))
    table_cell.append(('ab1vinput', '733'))
    table_cell.append(('ab1vinput', '775'))
    table_cell.append(('ab1vinput', '1702'))
    table_cell.append(('ab1vinput', '581'))
    table_cell.append(('ab1vinput', '788'))
    table_cell.append(('ab1vinput', '1714'))
    table_cell.append(('ab1vinput', '1717l'))
    table_cell.append(('ab1vinput', '1706'))
    table_cell.append(('ab1vinput', '1723'))
    table_cell.append(('ab1vinput', '1724'))
    table_cell.append(('ab1vinput', '1725'))
    table_cell.append(('ab1vinput', '1750'))
    table_cell.append(('10r140rear', '1708l'))
    table_cell.append(('10r140rear', '1708r'))
    table_cell.append(('10r140rear', '1709'))
    table_cell.append(('10r140rear', '1710'))
    table_cell.append(('10r140rear', '1711'))
    table_cell.append(('10r140rear', '1715'))
    table_cell.append(('10r140rear', '1717r'))
    table_cell.append(('10r140rear', '1706'))
    table_cell.append(('10r140rear', '1720'))
    table_cell.append(('10r140rear', '677'))
    table_cell.append(('10r140rear', '748'))
    table_cell.append(('10r140rear', '1723'))
    table_cell.append(('10r140rear', '1725'))
    table_cell.append(('trilobesinter', '262'))
    table_cell.append(('trilobesinter', '263'))
    table_cell.append(('trilobesinter', '859'))
    table_cell.append(('trilobeoptimized', '784'))
    table_cell.append(('trilobeoptimized', '770'))
    table_cell.append(('trilobeoptimized', '618'))
    table_cell.append(('trilobeoptimized', '755'))
    table_cell.append(('trilobeoptimized', '769'))
    table_cell.append(('trilobeoptimized', '624'))
    table_cell.append(('trilobeoptimized', '619'))
    table_cell.append(('trilobe', '573'))
    table_cell.append(('trilobe', '728'))
    table_cell.append(('trilobe', '644'))
    table_cell.append(('trilobe', '645'))
    table_cell.append(('trilobe', '646'))
    table_cell.append(('trilobe', '647'))
    table_cell.append(('trilobe', '648'))
    table_cell.append(('trilobe', '649'))
    table_cell.append(('trilobe', '650'))
    table_cell.append(('trilobeoffline', '636'))
    table_cell.append(('trilobeoffline', '625'))
    table_cell.append(('10r80mainline', '1504'))
    table_cell.append(('10r80mainline', '1506'))
    table_cell.append(('10r80mainline', '1519'))
    table_cell.append(('10r80mainline', '1520'))
    table_cell.append(('10r80mainline', '1502'))
    table_cell.append(('10r80mainline', '1507'))
    table_cell.append(('10r80mainline', '1501'))
    table_cell.append(('10r80mainline', '1515'))
    table_cell.append(('10r80mainline', '1508'))
    table_cell.append(('10r80mainline', '1532'))
    table_cell.append(('10r80mainline', '1509'))
    table_cell.append(('10r80mainline', '1514'))
    table_cell.append(('10r80mainline', '1510'))
    table_cell.append(('10r80mainline', '1513'))
    table_cell.append(('10r80mainline', '1503'))
    table_cell.append(('10r80mainline', '1511'))
    table_cell.append(('10r80mainline', '1533'))
    table_cell.append(('10r80offline', '1518'))
    table_cell.append(('10r80offline', '1521'))
    table_cell.append(('10r80offline', '1522'))
    table_cell.append(('10r80offline', '1523'))
    table_cell.append(('10r80offline', '1539'))
    table_cell.append(('10r80offline', '1540'))
    table_cell.append(('10r80offline', '1524'))
    table_cell.append(('10r80offline', '1525'))
    table_cell.append(('10r80offline', '1538'))
    table_cell.append(('10r80offline', '1541'))
    table_cell.append(('10r80offline', '1531'))
    table_cell.append(('10r80offline', '1527'))
    table_cell.append(('10r80offline', '1513'))
    table_cell.append(('10r80offline', '1530'))
    table_cell.append(('10r80offline', '1528'))
    table_cell.append(('10r80offline', '1533'))
    table_cell.append(('10r80uplift', '1546'))
    table_cell.append(('10r80uplift', '1547'))
    table_cell.append(('10r80uplift', '1548'))
    table_cell.append(('10r80uplift', '1549'))
    table_cell.append(('10r80uplift', '594'))
    table_cell.append(('10r80uplift', '1550'))
    table_cell.append(('10r80uplift', '1552'))
    table_cell.append(('10r80uplift', '751'))
    table_cell.append(('10r80uplift', '1554'))
    table_cell.append(('10r80uplift', '1533'))
    table_cell.append(('10r60mainline', '1800'))
    table_cell.append(('10r60mainline', '1801'))
    table_cell.append(('10r60mainline', '1802'))
    table_cell.append(('10r60mainline', '1529'))
    table_cell.append(('10r60mainline', '776'))
    table_cell.append(('10r60mainline', '1824'))
    table_cell.append(('10r60mainline', '1543'))
    table_cell.append(('10r60mainline', '1804'))
    table_cell.append(('10r60mainline', '1805'))
    table_cell.append(('10r60mainline', '1806'))
    table_cell.append(('10r60mainline', '1808'))
    table_cell.append(('10r60mainline', '1810'))
    table_cell.append(('10r60mainline', '1815'))
    table_cell.append(('10r60mainline', '1542'))
    table_cell.append(('10r60mainline', '1812'))
    table_cell.append(('10r60mainline', '1813'))
    table_cell.append(('10r60mainline', '1816'))

    if target:
        for l_line, l_asset in table_cell:
            try:
                context["data"][l_line][l_asset] = PartForMachineEvent.objects.filter(line=l_line, asset=l_asset, datetime__lte=target).latest('datetime').part
            except:
                context["data"][l_line][l_asset] = "unknown"
    else:
        for l_line, l_asset in table_cell:
            try:
                context["data"][l_line][l_asset] = PartForMachineEvent.objects.filter(line=l_line, asset=l_asset).latest('datetime').part
            except:
                context["data"][l_line][l_asset] = "unknown"
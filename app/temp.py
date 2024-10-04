import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pms.settings")
django.setup()


from barcode.models import LaserMark

for index in range(6439350,6000000, -1):
    try:
        mark = LaserMark.objects.get(pk=index)
        if mark.asset == '1750':
            if mark.bar_code[0]=='V':
                print(f'{index}: {mark.bar_code}')
                if mark.unique_portion is None:
                    mark.unique_portion = mark.bar_code[:14]
                    mark.save()


    except LaserMark.DoesNotExist:
        print(f'{index}:')
        continue
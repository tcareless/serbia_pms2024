import time
from django.shortcuts import render
from django.db import connections
# from django.core.context_processors import csrf

# from https://github.com/DaveClark-Stackpole/trakberry/blob/e9fa660e2cdd5ef4d730e0d00d888ad80311cacc/trakberry/forms.py#L57
from django import forms
class sup_downForm(forms.Form):
    machine = forms.CharField()
    reason = forms.CharField()
    priority = forms.CharField()


# from trakberry/trakberry/views_mod2.py
# Calculate Unix Shift Start times and return information
def stamp_shift_start():
    stamp=int(time.time())
    tm = time.localtime(stamp)
    hour1 = tm[3]
    t=int(time.time())
    tm = time.localtime(t)
    shift_start = -2
    current_shift = 3
    if tm[3]<22 and tm[3]>=14:
        shift_start = 14
    elif tm[3]<14 and tm[3]>=6:
        shift_start = 6
    cur_hour = tm[3]
    if cur_hour == 22:
        cur_hour = -1

    # Unix Time Stamp for start of shift Area 1
    u = t - (((cur_hour-shift_start)*60*60)+(tm[4]*60)+tm[5])

    # Amount of seconds run so far on the shift
    shift_time = t-u

    # Amount of seconds left on the shift to run
    shift_left = 28800 - shift_time

    # Unix Time Stamp for the end of the shift
    shift_end = t + shift_left

    return u,shift_time,shift_left,shift_end


def stamp_shift_start_3():
    stamp=int(time.time())
    tm = time.localtime(stamp)
    hour1 = tm[3]
    t=int(time.time())
    tm = time.localtime(t)
    shift_start = -2
    current_shift = 3
    if tm[3]<23 and tm[3]>=15:
        shift_start = 15
    elif tm[3]<15 and tm[3]>=7:
        shift_start = 7
    cur_hour = tm[3]
    if cur_hour == 23:
        cur_hour = -1

    # Unix Time Stamp for start of shift Area 1
    u = t - (((cur_hour-shift_start)*60*60)+(tm[4]*60)+tm[5])	

    # Amount of seconds run so far on the shift
    shift_time = t-u  

    # Amount of seconds left on the shift to run
    shift_left = 28800 - shift_time  

    # Unix Time Stamp for the end of the shift
    shift_end = t + shift_left
    

    return u,shift_time,shift_left,shift_end

"""
below applies to all these dashboard views

# t (t) = current timestamp
# codes (total8) =[('1504', 96, '#4FC34F', 338, 10, 8), ...
#                  [1]=asset number
#                  [2]=production this shift
#                  [3]=cell background color
#                  [4]=projected production
#                  [5]= operation 10, 20, 30
#                  [6]= ?

# op (op_total) = [0,0,... [10]= op 10 total count, [20] = op 20 etc]

# wip (wip_zip) = [('10', 8383, 36, 8391),(20, ...),(30, ...), ...]

# codes_60 (total8_0455) same as codes but for 10R60 part
# op_60 (op_total_0544) same as op_total above but for 10R60 part
# wip_60 (wip_zip_0455) same as wip_zip above but for 10R60 part

# args csrf token and form
"""

def get_line_prod(line_spec, line_target, part, shift_start, shift_time):
    cursor = connections['prodrpt-md'].cursor()

    sql = ('SELECT Machine, COUNT(*) '
           'FROM GFxPRoduction '
           'WHERE TimeStamp >= %s '
           'AND Part = %s '
           'GROUP BY Machine;')

    # Get production from last 5 mins for color coding
    five_mins_ago = shift_start +shift_time -300
    cursor.execute(sql, [five_mins_ago, part])
    prod_last5=cursor.fetchall()

    # Get production since start of shift for current and prediciton
    cursor.execute(sql, [shift_start, part])
    prod_shift=cursor.fetchall()

    machine_production = []
    operation_production = [0]*200	

    for machine in line_spec:  # build the list of tupples for the template
        asset = machine[0]  # this is the asset number on the dashboard
        source = machine[1]  # change this to the asset you want to take the count from 
        machine_rate = machine[2]
        operation = machine[3]

        count_index = next((i for i, v in enumerate(prod_last5) if v[0] == source), -1)
        if count_index>-1:
            prod_last_five = prod_last5[count_index][1]
        else:
            prod_last_five = 0

        count_index = next((i for i, v in enumerate(prod_shift) if v[0] == source), -1)
        if count_index>-1:
            prod_now = prod_shift[count_index][1]
        else:
            prod_now = 0

        # Pediction
        try:
            shift_rate = prod_now / float(shift_time)
        except:
            shift_time = 100
            shift_rate = prod_now / float(shift_time)
            
        predicted_production = int(prod_now + (shift_rate * (28800 - shift_time))) 

        # choose a color based on last 5 mins production vs machine rate
        machine_target = line_target / machine_rate   # need 3200 in 8 hours.  Machine is one of X machines
        five_minute_target = (machine_target / 28800) * 300  # need 'rate' parts in 5 minutes to make 3200 across cell
        five_minute_percentage = int(prod_last_five / five_minute_target * 100)
        if five_minute_percentage >= 100:
            cell_colour = '#009700'
        elif five_minute_percentage >= 90:
            cell_colour = '#4FC34F'
        elif five_minute_percentage >= 80:
            cell_colour = '#A4F6A4'
        elif five_minute_percentage >= 70:
            cell_colour = '#C3C300'
        elif five_minute_percentage >= 50:
            cell_colour = '#DADA3F'
        elif five_minute_percentage >= 25:
            cell_colour = '#F6F687'  # light Yellow
        elif five_minute_percentage >= 10:
            cell_colour = '#F7BA84'  # brown
        elif five_minute_percentage > 0:
            cell_colour = '#EC7371'  # faded red
        else:
            if predicted_production == 0:
                cell_colour = '#D5D5D5' # Grey
            else:
                cell_colour = '#FF0400' # Red


        machine_production.append(
            (asset, prod_now, cell_colour, predicted_production, operation, machine_rate)
        )
        operation_production[operation] += predicted_production


# codes (total8) =[('1504', 96, '#4FC34F', 338, 10, 8), ...
#                  [1]=asset number
#                  [2]=production this shift
#                  [3]=cell background color
#                  [4]=projected production
#                  [5]= operation 10, 20, 30
#                  [6]= ?
    # total8=list(zip(machine8,rate8,color8,pred8,op8,rt8))


    return machine_production, operation_production    


def cell_track_9341(request, template):
    tic = time.time() # track the execution time
    context = {} # data sent to template

    shift_start, shift_time, shift_left, shift_end = stamp_shift_start()	 # Get the Time Stamp info
    context['t'] = shift_start + shift_time
    request.session['shift_start'] = shift_start

    line_spec_9341 = [  # ('Asset','source', rate, OP)
        # Main line
        ('1504','1504',8,10), ('1506','1506',8,10), ('1519','1519',8,10), ('1520','1520',8,10),
        ('1502','1502',4,30), ('1507','1507',4,30),
        ('1501','1501',4,40), ('1515','1515',4,40),
        ('1508','1508',4,50), ('1532','1532',4,50),
        ('1509','1509',2,60),
        ('1514','1514',2,70),
        ('1510','1510',2,80),
        ('1503','1503',2,100),
        ('1511','1511',2,110),
        # Offline
        ('1518','1518',8,10), ('1521','1521',8,10), ('1522','1522',8,10), ('1523','1523',8,10),
        ('1539','1539',4,30), ('1540','1540',4,30),
        ('1524','1524',4,40), ('1525','1525',4,40),
        ('1538','1538',4,50),
        ('1541','1541',2,60),
        ('1531','1531',2,70),
        ('1527','1527',2,80),
        ('1530','1530',2,100),
        ('1528','1528',2,110),
        ('1513','1513',2,90),
        ('1533','1533',2,120),
        # uplift
        ('1546','1546',2,30),
        ('1547','1547',2,40),
        ('1548','1548',2,50),
        ('1549','1549',2,60),
        ('594','594',2,70),
        ('1550','1550',2,80),
        ('1552','1552',2,90),
        ('751','751',2,100),
        ('1554','1554',2,100),
    ]
    target_production_9341 = 3200
    machine_production_9341, op_production_9341 = get_line_prod(
            line_spec_9341, target_production_9341, '50-9341', shift_start, shift_time)

    context['codes'] = machine_production_9341
    context['op'] = op_production_9341
    context['wip'] = []

    line_spec = [  # ('Asset','Count', rate, OP)
        # Main line
        ('1800','1800',2,10), ('1801','1801',2,10), ('1802','1802',2,10), #
        ('1529','1529',4,30), ('1543','1543',4,30), ('776','776',4,30), ('1824','1824',4,30), #
        ('1805','1804',2,40), ('1805','1805',2,40), #
        ('1806','1806',1,50), #
        ('1808','1808',1,60), #
        ('1810','1810',1,70), #
        ('1815','1815',1,80), #
        ('1812','1812',1,100), #
        ('1816','1816',1,120), #
    ]

    target_production_0455 = 900
    machine_production_0455, op_production_0455 = get_line_prod(
            line_spec, target_production_0455, '50-0455', shift_start, shift_time)

    context['codes_60'] = machine_production_0455
    context['op_60'] = op_production_0455
    context['wip_60'] = []


    # Date entry for History
    if request.POST:
        request.session["track_date"] = request.POST.get("date_st")
        request.session["track_shift"] = request.POST.get("shift")
        return render(request,'redirect_cell_track_9341_history.html')	
    else:
        form = sup_downForm()
    args = {'form': form}
    # args.update(csrf(request))
    context['args'] = args
    request.session['runrate'] = 1128

    r80 = machine_production_9341[30][3]
    c80= "#bdb4b3"
    c60= "#bdb4b3"
    if r80 >= 2600:
            c80 = "#7FEB1E"
    elif r80 >= 2600 * .9:
            c80 = "#FFEB55"
    else:
            c80 = "#FF7355"
    context['R80'] = c80
    
    r60= machine_production_0455[14][3]
    if r60 >= 800:
            c60 = "#7FEB1E"
    elif r60 >= 800 * .9:
            c60 = "#FFEB55"
    else:
            c60 = "#FF7355"
    context['R60'] = c60


    context['elapsed'] = time.time()-tic
    # return render(request,'dashboards/cell_track_9341.html',{'t':t,'codes':total8,'op':op_total,'wip':[],'codes_60':total8_0455,'op_60':op_total_0455,'wip_60':[],'args':args,'elapsed':elapsed})	
    return render(request,f'dashboards/{template}',context)	

def cell_track_1467(request, template):
    tic = time.time() # track the execution time
    context = {} # data sent to template

    shift_start, shift_time, shift_left, shift_end = stamp_shift_start()	 # Get the Time Stamp info
    context['t'] = shift_start + shift_time

    line_spec = [
        ('644','644',6,10),('645','645',6,10),('646','646',6,10),
        ('647','647',6,10),('648','648',6,10),('649','649',6,10),
    ]
    # machines1 = ['644','645','646','647','648','649']
    # rate = [6,6,6,6,6,6]
    # line1 = [1,1,1,1,1,1]
    # operation1 = [10,10,10,10,10,10]
    # prt = '50-1467'

    target_production = 1400
    machine_production, op_production = get_line_prod(
            line_spec, target_production, '50-1467', shift_start, shift_time)

    context['codes'] = machine_production
    context['op'] = op_production
    context['wip'] = []

    # Date entry for History
    if request.POST:
        request.session["track_date"] = request.POST.get("date_st")
        request.session["track_shift"] = request.POST.get("shift")
        return render(request,'redirect_cell_track_1467_history.html')	
    else:
        form = sup_downForm()
    args = {}
    # args.update(csrf(request))
    args['form'] = form
    context['args'] = args
    request.session['runrate'] = 1128
    context['elapsed'] = time.time()-tic

    return render(request,f'dashboards/{template}',context)	
    # return render(request,'cell_track_1467.html',{'t':t,'codes':total8,'op':op_total,'args':args})	

def cell_track_8670(request, template):
    tic = time.time() # track the execution time
    context = {} # data sent to template

    shift_start, shift_time, shift_left, shift_end = stamp_shift_start_3()	 # Get the Time Stamp info
    context['t'] = shift_start + shift_time

    # machines1 = ['1703L','1704L','658','661','1703R','1704R','622','623','1727','659','626','1712','1716L','1719','1723','Laser']
    # rate = [4,4,4,4,4,4,4,4,1,2,1,1,1,1,1,1]
    # operation1 = [10,10,10,10,30,30,30,30,40,50,50,60,70,80,90,130]
    line_spec_8670 = [
        ('1703L','a1703L',4,10),('1704L','a1704L',4,10),('658','658',4,10),('661','661',4,10),
        ('1703R','a1703R',4,30),('1704R','a1704R',4,30),('622','622',4,30),('623','623',4,30),
        ('1727','1727',1,40),
        ('659','659',2,50),('626','626',2,50),
        ('1712','1712',1,60),
        ('1716L','1716L',1,70),
        ('1719','1719',1,80),
        ('1723','1723',1,90),
        ('1750','1750',1,130),        
    ]

    target_production = 300
    machine_production_8670, op_production_8670 = get_line_prod(
            line_spec_8670, target_production, '50-8670', shift_start, shift_time)

    context['codes'] = machine_production_8670
    context['op'] = op_production_8670
    context['wip'] = []

    # machines1 = ['1740','1701','733','755','1702','581','788','1714','1717L','1706','1723','Laser']
    # rate = [1,1,1,2,2,2,2,1,1,1,1,1]
    # operation1 = [10,40,50,60,60,70,70,80,90,100,110,130]
    line_spec_5401 = [
        ('1740','1740',1,10),
        ('1701','1701',1,40),
        ('733','733',1,50),
        ('755','755',2,60),('1702','1702',2,60),
        ('581','581',2,70),('788','788',2,70),
        ('1714','1714',1,80),
        ('1717L','1717L',1,90),
        ('1706','1706',1,100),
        ('1723','1723',1,110),
        ('1750','1750',1,130),
    ]

    target_production = 300
    machine_production_5401, op_production_5401 = get_line_prod(
            line_spec_5401, target_production, '50-5401', shift_start, shift_time)

    context['codes_5401'] = machine_production_5401
    context['op_5401'] = op_production_5401
    context['wip_5401'] = []

    # machines1 = ['1705','1746','621','629','785','1748','1718','669','1726','1722','1713','1716R','1719','1723','Laser']
    # rate = [2,2,2,2,3,3,3,1,1,1,1,1,1,1,1]
    # operation1 = [10,10,25,25,30,30,30,35,40,50,60,70,80,90,130]
    line_spec_5404 = [
        ('1705','1705',2,10),('1746','1746',2,10),
        ('621','621',2,25),('629','629',2,25),
        ('785','785',3,30),('1748','1748',3,30),('1718','1718',3,30),
        ('669','669',1,40),
        ('1726','1726',1,50),
        ('1722','1722',1,60),
        ('1713','1713',1,70),
        ('1716R','1716R',1,80),
        ('1723','1723',1,90),
        ('1750','1750',1,130),        
    ]

    target_production = 300
    machine_production_5404, op_production_5404 = get_line_prod(
            line_spec_5404, target_production, '50-5404', shift_start, shift_time)

    context['codes_5404'] = machine_production_5404
    context['op_5404'] = op_production_5404
    context['wip_5404'] = []
    
    # Date entry for History
    if request.POST:
        request.session["track_date"] = request.POST.get("date_st")
        request.session["track_shift"] = request.POST.get("shift")
        return render(request,'redirect_cell_track_8670_history.html')	
    else:
        form = sup_downForm()
    args = {}
    # args.update(csrf(request))
    args['form'] = form
    context['args'] = args

    context['elapsed'] = time.time()-tic
    return render(request,f'dashboards/{template}',context)	

def cell_track_5404(request):
    shift_start, shift_time, shift_left, shift_end = stamp_shift_start_3()	 # Get the Time Stamp info
    machines1 = ['1705','1746','621','629','785','1748','1718','669','1726','1722','1713','1716R','1719','1723','Laser']
    rate = [2,2,2,2,3,3,3,1,1,1,1,1,1,1,1]
    line1 = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    operation1 = [10,10,25,25,30,30,30,35,40,50,60,70,80,90,130]
    prt = '50-5404'
    pp = '5404'
    machine_rate = list(zip(machines1,rate,operation1))
    machine_color =[]
    cursor = connections['prodrpt-md'].cursor()
    color8=[]
    rate8=[]
    machine8=[]
    pred8 = []
    av55=[]
    cnt55=[]
    sh55=[]
    shl55=[]
    op8=[]
    rt8=[]
    request.session['shift_start'] = shift_start
    tt = int(time.time())
    t=tt-300
    start1 = tt-shift_time
    sql="SELECT * FROM GFxPRoduction WHERE TimeStamp >='%s' and Part='%s'"%(start1,prt)
    cursor.execute(sql)
    tmpX=cursor.fetchall()
    sql="SELECT * FROM barcode WHERE scrap >='%s'"%(start1)
    cursor.execute(sql)
    tmpY=cursor.fetchall()
    for i in machine_rate:
        machine2 = i[0]
        rate2 = 300 / float(i[1])
        rate2 = (rate2 / float(28800)) * 300
        if machine2 == '1888':
            machine22 = '1531'
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt = len(list2)
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt33 = len(list2)
        elif machine2 == '1510':
            machine22 = '1514'
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt = len(list2)
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt33 = len(list2)	
        elif machine2 == '1704R':
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
            x1 = 0
            cnt=0
            for j in list2:
                x2 = j[4]
                if (x2-x1) > 150:
                    cnt=cnt+1
                    x1=j[4]
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
            x1 = 0
            cnt33=0
            for j in list2:
                x2 = j[4]
                if (x2-x1) > 150:
                    cnt33=cnt33+1
                    x1=j[4]
        elif machine2 == '1703R':
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
            x1 = 0
            cnt=0
            for j in list2:
                x2 = j[4]
                if (x2-x1) > 150:
                    cnt=cnt+1
                    x1=j[4]		
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
            x1 = 0
            cnt33=0
            for j in list2:
                x2 = j[4]
                if (x2-x1) > 150:
                    cnt33=cnt33+1
                    x1=j[4]
        elif machine2 == 'Laser':
            list2 = list(filter(lambda x:x[2]>=t and x[1][-4:]==pp,tmpY))  # Filter list to get 5 min sum
            cnt=len(list2)			
            list2 = list(filter(lambda x:x[2]>=start1 and x[1][-4:]==pp,tmpY))  # Filter list to get 5 min sum
            cnt33=len(list2)
        else:
            # New faster method to search Data.  Doesn't bog down DB
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
            cnt = len(list2)
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
            cnt33 = len(list2)
        if cnt is None: cnt = 0
        rate3 = cnt / float(rate2)
        rate3 = int(rate3 * 100) # This will be the percentage we use to determine colour
        try:
            avg8 = cnt33 / float(shift_time)
        except:
            shift_time = 100
            avg8 = cnt33 / float(shift_time)
            
        avg9 = avg8 * shift_left
        pred1 = int(cnt33 + avg9)
        op8.append(i[2])
        rt8.append(i[1])
        av55.append(avg8)
        cnt55.append(cnt33)
        sh55.append(shift_time)
        shl55.append(shift_left)
        pred8.append(pred1)
        if rate3>=100:
            cc='#009700'
        elif rate3>=90:
            cc='#4FC34F'
        elif rate3>=80:
            cc='#A4F6A4'
        elif rate3>=70:
            cc='#C3C300'
        elif rate3>=50:
            cc='#DADA3F'
        elif rate3>=25:
            cc='#F6F687'
        elif rate3>=10:
            cc='#F7BA84'
        elif rate3>0:
            cc='#EC7371'
        else:
            if pred1 == 0:
                cc='#D5D5D5'
            else:
                cc='#FF0400'
        color8.append(cc)
        rate8.append(rate3)
        machine8.append(machine2)

    total8=list(zip(machine8,rate8,color8,pred8,op8,rt8))
    total99=0
    last_op=10
    op99=[]
    opt99=[]
    op_total = [0 for x in range(200)]	
    for i in total8:
        op_total[i[4]]=op_total[i[4]] + i[3]
    jobs1 = list(zip(machines1,line1,operation1))
    if request.POST:
        request.session["track_date"] = request.POST.get("date_st")
        request.session["track_shift"] = request.POST.get("shift")
        return render(request,'redirect_cell_track_8670_history.html')	
    else:
        form = sup_downForm()
    args = {}
    # args.update(csrf(request))
    args['form'] = form
    t = int(time.time())
    request.session['runrate'] = 1128

    return total8, op_total
    #return render(request,'cell_track_8670.html',{'t':t,'codes':total8,'op':op_total,'args':args})	

def cell_track_5401(request):
    shift_start, shift_time, shift_left, shift_end = stamp_shift_start_3()	 # Get the Time Stamp info
    machines1 = ['1740','1701','733','755','1702','581','788','1714','1717L','1706','1723','Laser']
    rate = [1,1,1,2,2,2,2,1,1,1,1,1]
    line1 = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    operation1 = [10,40,50,60,60,70,70,80,90,100,110,130]
    prt = '50-5401'
    pp = '6418'
    machine_rate = list(zip(machines1,rate,operation1))
    machine_color =[]
    cursor = connections['prodrpt-md'].cursor()
    color8=[]
    rate8=[]
    machine8=[]
    pred8 = []
    av55=[]
    cnt55=[]
    sh55=[]
    shl55=[]
    op8=[]
    rt8=[]
    request.session['shift_start'] = shift_start
    tt = int(time.time())
    t=tt-300
    start1 = tt-shift_time
    sql="SELECT * FROM GFxPRoduction WHERE TimeStamp >='%s' and Part='%s'"%(start1,prt)
    cursor.execute(sql)
    tmpX=cursor.fetchall()
    sql="SELECT * FROM barcode WHERE scrap >='%s'"%(start1)
    cursor.execute(sql)
    tmpY=cursor.fetchall()

    for i in machine_rate:
        machine2 = i[0]
        rate2 = 300 / float(i[1])
        rate2 = (rate2 / float(28800)) * 300
        if machine2 == '1888':
            machine22 = '1531'
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt = len(list2)
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt33 = len(list2)
        elif machine2 == '1510':
            machine22 = '1514'
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt = len(list2)
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt33 = len(list2)	
        elif machine2 == '1704R':
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
            x1 = 0
            cnt=0
            for j in list2:
                x2 = j[4]
                if (x2-x1) > 150:
                    cnt=cnt+1
                    x1=j[4]
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
            x1 = 0
            cnt33=0
            for j in list2:
                x2 = j[4]
                if (x2-x1) > 150:
                    cnt33=cnt33+1
                    x1=j[4]
        elif machine2 == '1703R':
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
            x1 = 0
            cnt=0
            for j in list2:
                x2 = j[4]
                if (x2-x1) > 150:
                    cnt=cnt+1
                    x1=j[4]		
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
            x1 = 0
            cnt33=0
            for j in list2:
                x2 = j[4]
                if (x2-x1) > 150:
                    cnt33=cnt33+1
                    x1=j[4]
        elif machine2 == 'Laser':
            list2 = list(filter(lambda x:x[2]>=t and x[1][-4:]==pp,tmpY))  # Filter list to get 5 min sum
            cnt=len(list2)			
            list2 = list(filter(lambda x:x[2]>=start1 and x[1][-4:]==pp,tmpY))  # Filter list to get 5 min sum
            cnt33=len(list2)
        else:
            # New faster method to search Data.  Doesn't bog down DB
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
            cnt = len(list2)
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
            cnt33 = len(list2)
        if cnt is None: cnt = 0
        rate3 = cnt / float(rate2)
        rate3 = int(rate3 * 100) # This will be the percentage we use to determine colour
        try:
            avg8 = cnt33 / float(shift_time)
        except:
            shift_time = 100
            avg8 = cnt33 / float(shift_time)
            
        avg9 = avg8 * shift_left
        pred1 = int(cnt33 + avg9)
        op8.append(i[2])
        rt8.append(i[1])
        av55.append(avg8)
        cnt55.append(cnt33)
        sh55.append(shift_time)
        shl55.append(shift_left)
        pred8.append(pred1)
        if rate3>=100:
            cc='#009700'
        elif rate3>=90:
            cc='#4FC34F'
        elif rate3>=80:
            cc='#A4F6A4'
        elif rate3>=70:
            cc='#C3C300'
        elif rate3>=50:
            cc='#DADA3F'
        elif rate3>=25:
            cc='#F6F687'
        elif rate3>=10:
            cc='#F7BA84'
        elif rate3>0:
            cc='#EC7371'
        else:
            if pred1 == 0:
                cc='#D5D5D5'
            else:
                cc='#FF0400'
        color8.append(cc)
        rate8.append(rate3)
        machine8.append(machine2)

    total8=list(zip(machine8,rate8,color8,pred8,op8,rt8))
    total99=0
    last_op=10
    op99=[]
    opt99=[]
    op_total = [0 for x in range(200)]	
    for i in total8:
        op_total[i[4]]=op_total[i[4]] + i[3]
    jobs1 = list(zip(machines1,line1,operation1))
    if request.POST:
        request.session["track_date"] = request.POST.get("date_st")
        request.session["track_shift"] = request.POST.get("shift")
        return render(request,'redirect_cell_track_8670_history.html')	
    else:
        form = sup_downForm()
    args = {}
    # args.update(csrf(request))
    args['form'] = form
    t = int(time.time())
    request.session['runrate'] = 1128

    return total8, op_total
    #return render(request,'cell_track_8670.html',{'t':t,'codes':total8,'op':op_total,'args':args})	


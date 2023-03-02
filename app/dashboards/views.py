import time
from django.shortcuts import render
from django.db import connections


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

    return machine_production, operation_production    


def get_line_prod2(line_spec, line_target, part, shift_start, shift_time):
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

    coloured_op_production =  [0 for x in range(200)]
    for idx, op in enumerate(operation_production):
        if op > line_target:
            color = '#68FF33'
        elif op > line_target*.85:
            color = '#F9FF33'
        else:
            color = '#FF9333'
        coloured_op_production[idx] = (op, color)

    return machine_production, coloured_op_production    


def cell_track_9341(request, target):
    tic = time.time() # track the execution time
    context = {} # data sent to template
    context['page_title']='9341 Tracking'

    target_production_9341 = int(request.site_variables.get('target_production_9341', 2900))
    target_production_0455 = int(request.site_variables.get('target_production_0455', 900))



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
        ('1554','1554',2,110),
    ]
    machine_production_9341, op_production_9341 = get_line_prod2(
            line_spec_9341, target_production_9341, '50-9341', shift_start, shift_time)

    context['codes'] = machine_production_9341
    context['op'] = op_production_9341
    context['wip'] = []

    line_spec = [  # ('Asset','Count', rate, OP)
        # Main line
        ('1800','1800',2,10), ('1801','1801',2,10), ('1802','1802',2,10), #
        ('1529','1529',4,30), ('1543','1543',4,30), ('776','776',4,30), ('1824','1824',4,30), #
        ('1804','1804',2,40), ('1805','1805',2,40), #
        ('1806','1806',1,50), #
        ('1808','1808',1,60), #
        ('1810','1810',1,70), #
        ('1815','1815',1,80), #
        ('1542','1812',1,90), #
        ('1812','1812',1,100), #
        ('1813','1812',1,110), #
        ('1816','1816',1,120), #
    ]

    machine_production_0455, op_production_0455 = get_line_prod2(
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
    context['args'] = args
    request.session['runrate'] = 1128

    r80 = machine_production_9341[30][3]
    c80= "#bdb4b3"
    c60= "#bdb4b3"
    if r80 >= target_production_9341:
            c80 = "#7FEB1E"
    elif r80 >= target_production_9341 * .9:
            c80 = "#FFEB55"
    else:
            c80 = "#FF7355"
    context['R80'] = c80
    
    r60= machine_production_0455[14][3]
    if r60 >= target_production_0455:
            c60 = "#7FEB1E"
    elif r60 >= target_production_0455 * .9:
            c60 = "#FFEB55"
    else:
            c60 = "#FF7355"
    context['R60'] = c60

    context['elapsed'] = time.time()-tic
    context['target'] = target
    if target == 'tv':
        template = 'dashboards/cell_track_9341.html'
    elif target == 'mobile':
        template = 'dashboards/cell_track_9341.html'
    else:
        template = 'dashboards/cell_track_9341.html'

    return render(request,template,context)	






def cell_track_1467(request, template):
    tic = time.time() # track the execution time
    context = {} # data sent to template

    target_production_1467 = int(request.site_variables.get('target_production_1467', 1400))

    shift_start, shift_time, shift_left, shift_end = stamp_shift_start()	 # Get the Time Stamp info
    context['t'] = shift_start + shift_time
    request.session["shift_start"] = shift_start

    line_spec = [
        ('644','644',6,10),('645','645',6,10),('646','646',6,10),
        ('647','647',6,10),('648','648',6,10),('649','649',6,10),
    ]
    
    machine_production, op_production = get_line_prod(
            line_spec, target_production_1467, '50-1467', shift_start, shift_time)

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
    
def cell_track_8670(request, template):
    tic = time.time() # track the execution time
    context = {} # data sent to template

    target_production_AB1V_Rx = int(request.site_variables.get('target_production_AB1V_Rx', 300))
    target_production_AB1V_Input = int(request.site_variables.get('target_production_AB1V_Input', 300))
    target_production_AB1V_OD = int(request.site_variables.get('target_production_AB1V_OD', 300))
    target_production_10R140 = int(request.site_variables.get('target_production_10R140_Rear', 300))

    shift_start, shift_time, shift_left, shift_end = stamp_shift_start_3()	 # Get the Time Stamp info
    context['t'] = shift_start + shift_time
    request.session["shift_start"] = shift_start

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

    machine_production_8670, op_production_8670 = get_line_prod(
            line_spec_8670, target_production_AB1V_Rx, '50-8670', shift_start, shift_time)

    context['codes'] = machine_production_8670
    context['op'] = op_production_8670
    context['wip'] = []

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

    machine_production_5401, op_production_5401 = get_line_prod(
            line_spec_5401, target_production_AB1V_Input, '50-5401', shift_start, shift_time)

    context['codes_5401'] = machine_production_5401
    context['op_5401'] = op_production_5401
    context['wip_5401'] = []

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
            line_spec_5404, target_production_AB1V_OD, '50-5404', shift_start, shift_time)

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

def track_graph_track(request, index):
    prt= '50-9341'
    request.session['track_track'] = 'Shift Track for Machine '+ str(index)

    mr7=[
        # mainline
        ('1504',8,'50-9341'),('1506',8,'50-9341'),('1519',8,'50-9341'),('1520',8,'50-9341'), # Op10/20
        ('1502',4,'50-9341'),('1507',4,'50-9341'), # op30
        ('1501',4,'50-9341'),('1515',4,'50-9341'), # op40
        ('1508',3,'50-9341'),('1532',3,'50-9341'), # op50
        ('1509',2,'50-9341'), # op60
        ('1514',2,'50-9341'), # op70
        ('1510',2,'50-9341'), # op80
        ('1513',2,'50-9341'), # op90
        ('1503',2,'50-9341'), # op100
        ('1511',2,'50-9341'), # op110
        # offline
        ('1518',8,'50-9341'),('1521',8,'50-9341'),('1522',8,'50-9341'),('1523',8,'50-9341'), # Op10/20
        ('1539',4,'50-9341'),('1540',4,'50-9341'), # Op30
        ('1524',4,'50-9341'),('1525',4,'50-9341'), # Op40
        ('1538',3,'50-9341'), # Op50
        ('1541',2,'50-9341'), # Op60
        ('1531',2,'50-9341'), # Op70
        ('1527',2,'50-9341'), # Op80
        ('1530',2,'50-9341'), # Op100
        ('1528',2,'50-9341'), # Op110
        ('1533',1,'50-9341'), # Final
        ('1800',2,'50-0455'),('1801',2,'50-0455'),('1802',2,'50-0455'),  # Op10/20
        ('1529',4,'50-0455'),('1543',4,'50-0455'),('776',4,'50-0455'),('1824',4,'50-0455'), # Op30
        ('1804',2,'50-0455'),('1805',2,'50-0455'), # Op40
        ('1806',1,'50-0455'), # Op50
        ('1808',1,'50-0455'), # Op60
        ('1810',1,'50-0455'), # Op70
        ('1815',1,'50-0455'), # Op80
        ('1542',1,'50-0455'), # Op90
        ('1812',1,'50-0455'), # Op100
        ('1813',1,'50-0455'), # Op110
        ('1816',1,'50-0455'), # Final
    ]

    for i in mr7:
        if i[0] == index :
            rate = i[1]
            prt= i[2]
    rate2 = 3200 / rate
    rate = rate2 / 8

    request.session['asset1_area'] = index
    request.session['asset2_area'] = index
    request.session['asset3_area'] = index
    request.session['asset4_area'] = index

    u = int(request.session['shift_start'])
    t = int(u) + 28800
    t=int(time.time())

    gr_list = track_data(request,t,u,prt,rate) # Get the Graph Data
    return render(request, "dashboards/graph_track_track.html",{'GList':gr_list})

def track_data(request, shift_end, shift_start, part, rate):
    m = '1533'
    asset1 = request.session['asset1_area']
    asset2 = request.session['asset2_area']
    asset3 = request.session['asset3_area']
    asset4 = request.session['asset4_area']
    mrr = (rate*(28800))/float(28800)
    cursor = connections['prodrpt-md'].cursor()
    sql = f'SELECT * FROM GFxPRoduction'
    sql += f' where TimeStamp >= {shift_start} and TimeStamp< {shift_end} and part = "{part}"'
    sql += f' and Machine IN ({asset1},{asset2},{asset3},{asset4})' 
    cursor.execute(sql)
    result = cursor.fetchall()
    gr_list, brk1, brk2, multiplier  = Graph_Data(shift_end,shift_start,m,result,mrr)
    return gr_list

def Graph_Data(t,u,machine,tmp,multiplier):
    # global tst
    cc = 0
    cr = 0
    cm = 0
    # last_by used for comparison
    last_by = 0
    temp_ctr = 0
    brk1 = 0
    brk2 = 0
    multiplier = multiplier / float(6)
    tm_sh = int((t-u)/600)
    px = [0 for x in range(tm_sh)]
    pp = [0 for x in range(tm_sh)]
    by = [0 for x in range(tm_sh)]
    ay = [0 for x in range(tm_sh)]
    cy = [0 for x in range(tm_sh)]
    for ab in range(0,tm_sh):
        temp_u = u + (cc*600)
        u_time = stamp_pdate4(temp_u)

        pp[ab] = u_time
        pp[ab] = u
        px[ab] = u + (cc*600)

        yy = px[ab]
        cc = cc + 1
        cr = cr + multiplier
        cm = cr * .8
        tst = []

        a=[]
        ctr=0
        for i in tmp:
            ctr=ctr+1
            a.append(i[4])

        op4 = list(filter(lambda c:c[4]<yy,tmp))
        by[ab] = len(op4)

        ay[ab] = int(cr)
        cy[ab] = int(cm)

    tm_sh = tm_sh - 1

    gr_list = list(zip(px,by,ay,cy,pp))

    return gr_list, brk1, brk2, multiplier

def stamp_pdate4(stamp):
    tm = time.localtime(stamp)
    ma = ''
    da = ''
    ha= ''
    mia = ''
    if tm[1] < 10: ma = '0'
    if tm[2] < 10: da = '0'
    if tm[3] < 10: ha = '0'
    if tm[4] < 10: mia = '0'
    y1 = str(tm[0])
    m1 = str(tm[1])
    d1 = str(tm[2])
    h1 = str(tm[3])
    mi1 = str(tm[4])

    pdate = y1 + '-' + (ma + m1) + '-' + (da + d1) + ' ' + (ha + h1) + ':' + (mia + mi1)
    pdate = (ha + h1) + ':' + (mia + mi1)

    return pdate

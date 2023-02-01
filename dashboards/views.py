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
    print(stamp,':',tm)
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

    print(u)
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

def cell_track_9341(request):

    shift_start, shift_time, shift_left, shift_end = stamp_shift_start()	 # Get the Time Stamp info
    machines1 = ['1504','1506','1519','1520','1502','1507','1501','1515','1508','1532','1509','1514','1510','1503','1511','1518','1521','1522','1523','1539','1540','1524','1525','1538','1541','1531','1527','1530','1528','1513','1533','1546','1547','1548','1549']
    rate = [8,8,8,8,4,4,4,4,4,4,2,2,2,2,2,8,8,8,8,4,4,4,4,4,2,2,2,2,2,1,1,5,5,5,3]
    line1 = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,0,0,3,3,3,3]
    operation1 = [10,10,10,10,30,30,40,40,50,50,60,70,80,100,110,10,10,10,10,30,30,40,40,50,60,70,80,100,110,90,120,30,40,50,60]
    prt = '50-9341'
    machine_rate = list(zip(machines1,rate,operation1))
    machine_color =[]
    cursor = connections['prodrpt-md'].cursor()
    sql = "SELECT * FROM tkb_wip_track where part = '%s'" %(prt) 
    cursor.execute(sql)
    wip = cursor.fetchall()
    wip_stamp = int(wip[0][1])

    # [1] -- Machine    [4] -- Timestamp  [2] -- Part   [5] -- Count ..usually 1
    # ******************************************
    wip_stamp = int(time.time()) - 360 # This line is just a temp add to speed up the reads and negate WIP

    sql = "SELECT * FROM GFxPRoduction WHERE TimeStamp >= '%d' and Part = '%s'" % (wip_stamp,prt)
    cursor.execute(sql)
    wip_data = cursor.fetchall()
    wip_prod = [0 for x in range(140)]	

    for i in machine_rate:
        list1 = list(filter(lambda x:x[1]==i[0],wip_data))  # Filter list and pull out machine to make list1
        count1=len(list1)  # Total all in list1
        wip_prod[i[2]] = wip_prod[i[2]] + count1  # Add total to that operation variable
    

    # This section is temporary as no grinding *************************************
    wip_prod[80] = wip_prod[40]
    wip_prod[70] = wip_prod[40]
    wip_prod[60] = wip_prod[40]
    wip_prod[50] = wip_prod[40]

    
    # ******************************************************************************

    op5=[]
    wip5=[]
    prd5=[]


    for i in wip:
        op5.append(i[3])
        wip5.append(int(i[4]))
        x=int(i[3])
        prd5.append(wip_prod[x])
    op5.append('120')
    wip5.append(0)
    prd5.append(wip_prod[120])
    wip_zip=list(zip(op5,wip5,prd5))  # Generates totals beside old WIP
    ptr = 1
    new_wip=[]
    for i in wip_zip:
        try:
            w1=i[1]
            i1=i[2]
            i2=wip_zip[ptr][2]
            w1=w1+(i1-i2)
        except:
            w1=0
        if w1 < 0 : w1 = 0
        ptr = ptr + 1
        new_wip.append(w1)
    wip_zip=list(zip(op5,wip5,prd5,new_wip))

    # Filter a List
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

    # Preliminary testing variables for new methord
    tt = int(time.time())
    t=tt-300
    start1 = tt-shift_time
    sql="SELECT * FROM GFxPRoduction WHERE TimeStamp >='%s' and Part='%s'"%(start1,prt)
    cursor.execute(sql)
    tmpX=cursor.fetchall()

    for i in machine_rate:
        machine2 = i[0]

        rate2 = 3200 / float(i[1])
        rate2 = (rate2 / float(28800)) * 300

        # If 1510 going take out below conditional statement
        if machine2 == '1888':
            machine22 = '1531'
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt = len(list2)
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt33 = len(list2)
        # elif machine2 == '1510':  # While running manually 
        # 	machine22 = '1527'
        # 	machine23 = '1513'
        # 	list2 = list(filter(lambda x:x[4]>=t and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
        # 	list3 = list(filter(lambda x:x[4]>=t and x[1]==machine23,tmpX))  # Filter list to get 5 min sum
        # 	cnt = len(list3) - len(list2)
        # 	list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
        # 	list3 = list(filter(lambda x:x[4]>=start1 and x[1]==machine23,tmpX))  # Filter list to get 5 min sum
        # 	cnt33 = len(list3) - len(list2)

    

    
        elif machine2 == '1510':
            machine22 = '1514'
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt = len(list2)
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt33 = len(list2)	
        elif machine2 == '1547':
            machine22 = '1546'
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt = len(list2)
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt33 = len(list2)	
        # elif machine2 == '1533':
        # 	machine22 = '1511'
        # 	list2 = list(filter(lambda x:x[4]>=t and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
        # 	cnt_A = len(list2)
        # 	list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
        # 	cnt33_A = len(list2)
        # 	machine22 = '1528'
        # 	list2 = list(filter(lambda x:x[4]>=t and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
        # 	cnt_B = len(list2)
        # 	list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
        # 	cnt33_B = len(list2)
        # 	cnt = cnt_A + cnt_A
        # 	cnt33 = cnt33_A + cnt33_B
        else:
            # New faster method to search Data.  Doesn't bog down DB
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
            cnt = len(list2)
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
            cnt33 = len(list2)

        # Old Method to search Data
        # try:
        # 	sql = "SELECT SUM(Count) FROM GFxPRoduction WHERE TimeStamp >= '%d' and Part = '%s' and Machine = '%s'" % (t,prt,machine2)
        # 	cur.execute(sql)
        # 	tmp2 = cur.fetchall()
        # 	tmp3 = tmp2[0]
        # 	cnt = int(tmp3[0])
        # except:
        # 	cnt = 0
        # try:
        # 	sql = "SELECT SUM(Count) FROM GFxPRoduction WHERE TimeStamp >= '%d' and Part = '%s' and Machine = '%s'" % (start1,prt,machine2)
        # 	cur.execute(sql)
        # 	tmp22 = cur.fetchall()
        # 	tmp33 = tmp22[0]
        # 	cnt33 = int(tmp33[0])
        # except:
        # 	cnt33 = 0

        if cnt is None: cnt = 0
        rate3 = cnt / float(rate2)
        rate3 = int(rate3 * 100) # This will be the percentage we use to determine colour

        # Pediction
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

    
    # Date entry for History
    if request.POST:
        request.session["track_date"] = request.POST.get("date_st")
        request.session["track_shift"] = request.POST.get("shift")
        return render(request,'redirect_cell_track_9341_history.html')	
    else:
        form = sup_downForm()
    args = {}
    # args.update(csrf(request))
    args['form'] = form

    total8_0455,op_total_0455, wip_zip_0455 = cell_track_0455(request)

    t = int(time.time())
    request.session['runrate'] = 1128


    # This section will check every 30min and email out counts to Jim and Myself

    # Take it out for now.   Errors when using GMail accounts

    # # try:
    # db, cur = db_set(request)
    # cur.execute("""CREATE TABLE IF NOT EXISTS tkb_email_10r(Id INT PRIMARY KEY AUTO_INCREMENT,dummy1 INT(30),stamp INT(30) )""")
    # eql = "SELECT MAX(stamp) FROM tkb_email_10r"
    # cur.execute(eql)
    # teql = cur.fetchall()
    # teql2 = int(teql[0][0])
    # ttt=int(time.time())
    # elapsed_time = ttt - teql2
    # if elapsed_time > 1800:
    # 	x = 1
    # 	dummy = 8
    # 	cur.execute('''INSERT INTO tkb_email_10r(dummy1,stamp) VALUES(%s,%s)''', (dummy,ttt))
    # 	db.commit()
    # 	track_email(request)  
    # db.close()
    # # except:
    # # 	dummy2 = 0

    # *****************************************************************************************************

    return render(request,'dashboards/cell_track_9341.html',{'t':t,'codes':total8,'op':op_total,'wip':wip_zip,'codes_60':total8_0455,'op_60':op_total_0455,'wip_60':wip_zip_0455,'args':args})	

def cell_track_9341_TV(request):
    request.session["local_switch"] = 0

    shift_start, shift_time, shift_left, shift_end = stamp_shift_start()  # Get the Time Stamp info
    cursor = connections['prodrpt-md'].cursor()

    machines1 = ['1504','1506','1519','1520','1502','1507','1501','1515','1508','1532','1509',
                 '1514','1510','1503','1511','1518','1521','1522','1523','1539','1540','1524',
                 '1525','1538','1541','1531','1527','1530','1528','1513','1533']
    rate = [8,8,8,8,4,4,4,4,3,3,2,2,2,2,2,8,8,8,8,4,4,4,4,3,2,2,2,2,2,1,1]
    line1 = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,0,0]
    operation1 = [10,10,10,10,30,30,40,40,50,50,60,70,80,100,110,10,10,10,10,30,30,40,40,50,60,70,80,100,110,90,120]

    prt = '50-9341'

    wip_prod = [0 for x in range(140)]
    machine_rate = list(zip(machines1,rate,operation1))

    sql = ('SELECT * FROM tkb_wip_track '
           'WHERE part = %s;')
    cursor.execute(sql, [prt])


    wip = cursor.fetchall()
    wip_stamp = int(wip[0][1])

    sql = ('SELECT Machine, COUNT(*) '
           'FROM GFxPRoduction '
           'WHERE TimeStamp >= %s '
           'AND Part = %s '
           'GROUP BY Machine;')

    cursor.execute(sql, [wip_stamp, prt])

    wip_data = cursor.fetchall()

   # loop through the list of machines
    #  - add the number produced by that machine since the last wip count to the wip count for its operation 
    for machine in machine_rate:

        count_index = next((i for i, v in enumerate(wip_data) if v[0] == machine[0]), None)
        if count_index:
            count1 = wip_data[count_index][1]
        else:
            count1 = 0

        wip_prod[machine[2]] = wip_prod[machine[2]] + count1  # Add total to that operation variable

    # This section is temporary as no grinding *************************************
    wip_prod[80] = wip_prod[50]
    wip_prod[70] = wip_prod[50]
    wip_prod[60] = wip_prod[50]
    # ******************************************************************************

    op5=[]
    wip5=[]
    prd5=[]

    for i in wip:
        op5.append(i[3])
        wip5.append(int(i[4]))
        x=int(i[3])
        prd5.append(wip_prod[x])
    op5.append('120')
    wip5.append(0)
    prd5.append(wip_prod[120])
    wip_zip=list(zip(op5,wip5,prd5))  # Generates totals beside old WIP
    ptr = 1
    new_wip=[]

    for i in wip_zip:
        try:
            w1=i[1]
            i1=i[2]
            i2=wip_zip[ptr][2]
            w1=w1+(i1-i2)
        except:
            w1=0
        if w1 < 0 : w1 = 0
        ptr = ptr + 1
        new_wip.append(w1)
    wip_zip=list(zip(op5,wip5,prd5,new_wip))

    # Filter a List
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

    # Preliminary testing variables for new methord
    tt = int(time.time())
    t=tt-300
    start1 = tt-shift_time

    sql = ('SELECT Machine, COUNT(*) '
           'FROM GFxPRoduction '
           'WHERE TimeStamp >= %s '
           'AND Part = %s '
           'GROUP BY Machine;')

    # Get production from last 5 mins for color coding
    cursor.execute(sql, [t, prt])
    prod_last5=cursor.fetchall()

    # Get production since start of shift for current and prediciton
    cursor.execute(sql, [start1, prt])
    prod_shift=cursor.fetchall()

    for i in machine_rate:
        machine2 = i[0]

        rate2 = 3200 / float(i[1])
        rate2 = (rate2 / float(28800)) * 300

        # If 1510 going take out below conditional statement
        if machine2 == '1510':
            machine22 = '1514'
        if machine2 == '1527':
            machine22 = '1531'
        if machine2 == '1511':
            machine22 = '1503'
        else:
          machine22 = machine2

        count_index = next((i for i, v in enumerate(prod_last5) if v[0] == machine22), None)
        if count_index:
            cnt = prod_last5[count_index][1]
        else:
            cnt = 0

        count_index = next((i for i, v in enumerate(prod_shift) if v[0] == machine22), None)
        if count_index:
            cnt33 = prod_shift[count_index][1]
        else:
            cnt33 = 0

        print('machine ', machine2, ': ', cnt, cnt33)

        rate3 = cnt / float(rate2)
        rate3 = int(rate3 * 100) # This will be the percentage we use to determine colour

        # Pediction
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

    # Date entry for History
    if request.POST:
        request.session["track_date"] = request.POST.get("date_st")
        request.session["track_shift"] = request.POST.get("shift")
        return render(request,'redirect_cell_track_9341_history.html')
    else:
        form = sup_downForm()
    args = {}
    # args.update(csrf(request))
    args['form'] = form

    total8_0455,op_total_0455, wip_zip_0455 = cell_track_0455(request)

    t = int(time.time())
    request.session['runrate'] = 1128
    return render(request,'cell_track_9341_TV.html',{'t':t,'codes':total8,'op':op_total,'wip':wip_zip,'codes_60':total8_0455,'op_60':op_total_0455,'wip_60':wip_zip_0455,'args':args})

def cell_track_9341_mobile(request):

    shift_start, shift_time, shift_left, shift_end = stamp_shift_start()	 # Get the Time Stamp info
    machines1 = ['1504','1506','1519','1520','1502','1507','1501','1515','1508','1532','1509','1514','1510','1503','1511','1518','1521','1522','1523','1539','1540','1524','1525','1538','1541','1531','1527','1530','1528','1513','1533','1546','1547','1548','1549']
    rate = [8,8,8,8,4,4,4,4,4,4,2,2,2,2,2,8,8,8,8,4,4,4,4,4,2,2,2,2,2,1,1,5,5,5,3]
    line1 = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,0,0,3,3,3,3]
    operation1 = [10,10,10,10,30,30,40,40,50,50,60,70,80,100,110,10,10,10,10,30,30,40,40,50,60,70,80,100,110,90,120,30,40,50,60]
    prt = '50-9341'
    machine_rate = list(zip(machines1,rate,operation1))
    machine_color =[]
    cursor = connections['prodrpt-md'].cursor()
    sql = "SELECT * FROM tkb_wip_track where part = '%s'" % (prt) 
    cursor.execute(sql)
    wip = cursor.fetchall()
    wip_stamp = int(wip[0][1])

    # [1] -- Machine    [4] -- Timestamp  [2] -- Part   [5] -- Count ..usually 1
    # ******************************************
    wip_stamp = int(time.time()) - 360 # This line is just a temp add to speed up the reads and negate WIP

    sql = "SELECT * FROM GFxPRoduction WHERE TimeStamp >= '%d' and Part = '%s'" % (wip_stamp,prt)
    cursor.execute(sql)
    wip_data = cursor.fetchall()
    wip_prod = [0 for x in range(140)]	

    for i in machine_rate:
        list1 = list(filter(lambda x:x[1]==i[0],wip_data))  # Filter list and pull out machine to make list1
        count1=len(list1)  # Total all in list1
        wip_prod[i[2]] = wip_prod[i[2]] + count1  # Add total to that operation variable
    

    # This section is temporary as no grinding *************************************
    wip_prod[80] = wip_prod[40]
    wip_prod[70] = wip_prod[40]
    wip_prod[60] = wip_prod[40]
    wip_prod[50] = wip_prod[40]

    
    # ******************************************************************************

    op5=[]
    wip5=[]
    prd5=[]


    for i in wip:
        op5.append(i[3])
        wip5.append(int(i[4]))
        x=int(i[3])
        prd5.append(wip_prod[x])
    op5.append('120')
    wip5.append(0)
    prd5.append(wip_prod[120])
    wip_zip=list(zip(op5,wip5,prd5))  # Generates totals beside old WIP
    ptr = 1
    new_wip=[]
    for i in wip_zip:
        try:
            w1=i[1]
            i1=i[2]
            i2=wip_zip[ptr][2]
            w1=w1+(i1-i2)
        except:
            w1=0
        if w1 < 0 : w1 = 0
        ptr = ptr + 1
        new_wip.append(w1)
    wip_zip=list(zip(op5,wip5,prd5,new_wip))

    # Filter a List
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


    # Preliminary testing variables for new methord
    tt = int(time.time())
    t=tt-300
    start1 = tt-shift_time
    sql="SELECT * FROM GFxPRoduction WHERE TimeStamp >='%s' and Part='%s'"%(start1,prt)
    cursor.execute(sql)
    tmpX=cursor.fetchall()
    # *********************************************

    for i in machine_rate:
        machine2 = i[0]

        rate2 = 3200 / float(i[1])
        rate2 = (rate2 / float(28800)) * 300
        
        # If 1510 going take out below conditional statement
        if machine2 == '1888':
            machine22 = '1531'
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine22,tmpX)) # Filter list to get 5 min sum
            cnt = len(list2)
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt33 = len(list2)
        # elif machine2 == '1510':  # While running manually 
        # 	machine22 = '1527'
        # 	machine23 = '1513'
        # 	list2 = list(filter(lambda x:x[4]>=t and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
        # 	list3 = list(filter(lambda x:x[4]>=t and x[1]==machine23,tmpX))  # Filter list to get 5 min sum
        # 	cnt = len(list3) - len(list2)
        # 	list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
        # 	list3 = list(filter(lambda x:x[4]>=start1 and x[1]==machine23,tmpX))  # Filter list to get 5 min sum
        # 	cnt33 = len(list3) - len(list2)

    

    
        elif machine2 == '1510':
            machine22 = '1514'
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt = len(list2)
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
            cnt33 = len(list2)	
        elif machine2 == '1547':
            machine22 = '1546'
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine22,tmpX)) # Filter list to get 5 min sum
            cnt = len(list2)
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine22,tmpX)) # Filter list to get 5 min sum
            cnt33 = len(list2)	
        # elif machine2 == '1533':
        # 	machine22 = '1511'
        # 	list2 = list(filter(lambda x:x[4]>=t and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
        # 	cnt_A = len(list2)
        # 	list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
        # 	cnt33_A = len(list2)
        # 	machine22 = '1528'
        # 	list2 = list(filter(lambda x:x[4]>=t and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
        # 	cnt_B = len(list2)
        # 	list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine22,tmpX))  # Filter list to get 5 min sum
        # 	cnt33_B = len(list2)
        # 	cnt = cnt_A + cnt_A
        # 	cnt33 = cnt33_A + cnt33_B
        else:
            # New faster method to search Data.  Doesn't bog down DB
            list2 = list(filter(lambda x:x[4]>=t and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
            cnt = len(list2)
            list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
            cnt33 = len(list2)

        # Old Method to search Data
        # try:
        # 	sql = "SELECT SUM(Count) FROM GFxPRoduction WHERE TimeStamp >= '%d' and Part = '%s' and Machine = '%s'" % (t,prt,machine2)
        # 	cur.execute(sql)
        # 	tmp2 = cur.fetchall()
        # 	tmp3 = tmp2[0]
        # 	cnt = int(tmp3[0])
        # except:
        # 	cnt = 0
        # try:
        # 	sql = "SELECT SUM(Count) FROM GFxPRoduction WHERE TimeStamp >= '%d' and Part = '%s' and Machine = '%s'" % (start1,prt,machine2)
        # 	cur.execute(sql)
        # 	tmp22 = cur.fetchall()
        # 	tmp33 = tmp22[0]
        # 	cnt33 = int(tmp33[0])
        # except:
        # 	cnt33 = 0

        if cnt is None: cnt = 0
        rate3 = cnt / float(rate2)
        rate3 = int(rate3 * 100) # This will be the percentage we use to determine colour

        # Pediction
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
    
    # Date entry for History
    if request.POST:
        request.session["track_date"] = request.POST.get("date_st")
        request.session["track_shift"] = request.POST.get("shift")
        return render(request,'redirect_cell_track_9341_history.html')	
    else:
        form = sup_downForm()
    args = {}
    # args.update(csrf(request))
    args['form'] = form

    total8_0455,op_total_0455, wip_zip_0455 = cell_track_0455(request)

    t = int(time.time())
    request.session['runrate'] = 1128


    # This section will check every 30min and email out counts to Jim and Myself

    # Take it out for now.   Errors when using GMail accounts

    # # try:
    # db, cur = db_set(request)
    # cur.execute("""CREATE TABLE IF NOT EXISTS tkb_email_10r(Id INT PRIMARY KEY AUTO_INCREMENT,dummy1 INT(30),stamp INT(30) )""")
    # eql = "SELECT MAX(stamp) FROM tkb_email_10r"
    # cur.execute(eql)
    # teql = cur.fetchall()
    # teql2 = int(teql[0][0])
    # ttt=int(time.time())
    # elapsed_time = ttt - teql2
    # if elapsed_time > 1800:
    # 	x = 1
    # 	dummy = 8
    # 	cur.execute('''INSERT INTO tkb_email_10r(dummy1,stamp) VALUES(%s,%s)''', (dummy,ttt))
    # 	db.commit()
    # 	track_email(request)  
    # db.close()
    # # except:
    # # 	dummy2 = 0

    # *****************************************************************************************************

    return render(request,'cell_track_9341_mobile.html',{'t':t,'codes':total8,'op':op_total,'wip':wip_zip,'codes_60':total8_0455,'op_60':op_total_0455,'wip_60':wip_zip_0455,'args':args})	

# Same tracking for 0455
def cell_track_0455(request):
    
    shift_start, shift_time, shift_left, shift_end = stamp_shift_start()	 # Get the Time Stamp info
    machines1 = ['1800','1801','1802','1529','1543','776','1824','1804','1805','1806','1808','1810','1815','1812','1816']
    rate = [2,2,2,4,4,4,4,2,2,1,1,1,1,1,1]
    line1 = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    operation1 = [10,10,10,30,30,30,30,40,40,50,60,70,80,100,120]
    prt = '50-0455'
    machine_rate = list(zip(machines1,rate,operation1))
    machine_color =[]
    cursor = connections['prodrpt-md'].cursor()
    sql = "SELECT * FROM tkb_wip_track where part = '%s'" %(prt) 
    cursor.execute(sql)
    wip = cursor.fetchall()
    wip_stamp = int(wip[0][1])

    # [1] -- Machine    [4] -- Timestamp  [2] -- Part   [5] -- Count ..usually 1
    sql = "SELECT * FROM GFxPRoduction WHERE TimeStamp >= '%d' and Part = '%s'" % (wip_stamp,prt)
    cursor.execute(sql)
    wip_data = cursor.fetchall()
    wip_prod = [0 for x in range(140)]	

    for i in machine_rate:
        list1 = list(filter(lambda x:x[1]==i[0],wip_data))  # Filter list and pull out machine to make list1
        count1=len(list1)  # Total all in list1
        wip_prod[i[2]] = wip_prod[i[2]] + count1  # Add total to that operation variable
    
    wip_prod[80] = wip_prod[40]
    wip_prod[70] = wip_prod[40]
    wip_prod[60] = wip_prod[40]
    wip_prod[50] = wip_prod[40]
    wip_prod[100] = wip_prod[40]
    wip_prod[90] = wip_prod[40]

    op5=[]
    wip5=[]
    prd5=[]
    for i in wip:
        op5.append(i[3])
        wip5.append(int(i[4]))
        x=int(i[3])
        prd5.append(wip_prod[x])
    op5.append('120')
    wip5.append(0)
    prd5.append(wip_prod[120])
    wip_zip=list(zip(op5,wip5,prd5))  # Generates totals beside old WIP
    ptr = 1
    new_wip=[]
    for i in wip_zip:
        try:
            w1=i[1]
            i1=i[2]
            i2=wip_zip[ptr][2]
            w1=w1+(i1-i2)
        except:
            w1=0
        if w1 < 0 : w1 = 0
        ptr = ptr + 1
        new_wip.append(w1)

    wip_zip=list(zip(op5,wip5,prd5,new_wip))


    # Filter a List
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


    # Preliminary testing variables for new methord
    tt = int(time.time())
    t=tt-300
    start1 = tt-shift_time
    sql="SELECT * FROM GFxPRoduction WHERE TimeStamp >='%s' and Part='%s'"%(start1,prt)
    cursor.execute(sql)
    tmpX=cursor.fetchall()
    # *********************************************

    for i in machine_rate:
        machine2 = i[0]
        rate2 = 900 / float(i[1])
        rate2 = (rate2 / float(28800)) * 300

        # New faster method to search Data.  Doesn't bog down DB
        list2 = list(filter(lambda x:x[4]>=t and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
        cnt = len(list2)
        list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
        cnt33 = len(list2)



        # try:
        # 	sql = "SELECT SUM(Count) FROM GFxPRoduction WHERE TimeStamp >= '%d' and Part = '%s' and Machine = '%s'" % (t,prt,machine2)
        # 	cur.execute(sql)
        # 	tmp2 = cur.fetchall()
        # 	tmp3 = tmp2[0]
        # 	cnt = int(tmp3[0])
        # except:
        # 	cnt = 0
        # try:
        # 	sql = "SELECT SUM(Count) FROM GFxPRoduction WHERE TimeStamp >= '%d' and Part = '%s' and Machine = '%s'" % (start1,prt,machine2)
        # 	cur.execute(sql)
        # 	tmp22 = cur.fetchall()
        # 	tmp33 = tmp22[0]
        # 	cnt33 = int(tmp33[0])
        # except:
        # 	cnt33 = 0


        if cnt is None: cnt = 0
        rate3 = cnt / float(rate2)
        rate3 = int(rate3 * 100) # This will be the percentage we use to determine colour
        # Pediction
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

        
        # # Use the below pred8 for normal
        pred8.append(pred1)

        # This is temp for total so far
        # pred8.append(cnt33)


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

        # if machine2=='1800' or machine2=='1801' or machine2 =='1802': cc='#C8C8C8'
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

    return total8, op_total, wip_zip


# from https://github.com/DaveClark-Stackpole/trakberry/blob/e9fa660e2cdd5ef4d730e0d00d888ad80311cacc/trakberry/views_production.py#L4422
def new_cell_track_0455(request):

    shift_start, shift_time, shift_left, shift_end = stamp_shift_start()  # Get the Time Stamp info
    machines1 = ['1800','1801','1802','1529','1543','776','1824','1804','1805','1806','1808','1810','1815','1812','1816']
    rate = [2,2,2,4,4,4,4,2,2,1,1,1,1,1,1]
    line1 = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    operation1 = [10,10,10,30,30,30,30,40,40,50,60,70,80,100,120]
    prt = '50-0455'
    machine_rate = list(zip(machines1,rate,operation1))
    machine_color =[]
    cursor = connections['prodrpt-md'].cursor()

    sql = "SELECT * FROM tkb_wip_track where part = %s"
    cursor.execute(sql, [prt])
    wip = cursor.fetchall()
    wip_stamp = int(wip[0][1])

    sql = ('SELECT Machine, COUNT(*) '
           'FROM GFxPRoduction '
           'WHERE TimeStamp >= %s '
           'AND Part = %s '
           'GROUP BY Machine;')

    cursor.execute(sql, [wip_stamp, prt])

    wip_data = cursor.fetchall()

    wip_prod = [0 for x in range(140)]

    for machine in machine_rate:
        count_index = next((i for i, v in enumerate(wip_data) if v[0] == machine[0]), None)
        if count_index:
            count1 = wip_data[count_index][1]
        else:
            count1 = 0

        wip_prod[machine[2]] = wip_prod[machine[2]] + count1  # Add total to that operation variable

    wip_prod[80] = wip_prod[40]
    wip_prod[70] = wip_prod[40]
    wip_prod[60] = wip_prod[40]
    wip_prod[50] = wip_prod[40]
    wip_prod[100] = wip_prod[40]
    wip_prod[90] = wip_prod[40]


    op5=[]
    wip5=[]
    prd5=[]
    for i in wip:
        op5.append(i[3])
        wip5.append(int(i[4]))
        x=int(i[3])
        prd5.append(wip_prod[x])
    op5.append('120')
    wip5.append(0)
    prd5.append(wip_prod[120])
    wip_zip=list(zip(op5,wip5,prd5))  # Generates totals beside old WIP
    ptr = 1
    new_wip=[]
    for i in wip_zip:
        try:
            w1=i[1]
            i1=i[2]
            i2=wip_zip[ptr][2]
            w1=w1+(i1-i2)
        except:
            w1=0
        if w1 < 0 : w1 = 0
        ptr = ptr + 1
        new_wip.append(w1)

    wip_zip=list(zip(op5,wip5,prd5,new_wip))


    # Filter a List
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

    # Preliminary testing variables for new methord
    tt = int(time.time())
    t=tt-300
    start1 = tt-shift_time

    sql = ('SELECT Machine, COUNT(*) '
           'FROM GFxPRoduction '
 
           'WHERE TimeStamp >= %s '
           'AND Part = %s '
           'GROUP BY Machine;')

    # Get production from last 5 mins for color coding
    cursor.execute(sql, [t, prt])
    prod_last5=cursor.fetchall()

    # Get production since start of shift for current and prediciton
    cursor.execute(sql, [start1, prt])
    prod_shift=cursor.fetchall()

    for i in machine_rate:
        machine2 = i[0]
        rate2 = 900 / float(i[1])
        rate2 = (rate2 / float(28800)) * 300

        # New faster method to search Data.  Doesn't bog down DB
        # list2 = list(filter(lambda x:x[4]>=t and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
        # cnt = len(list2)

        count_index = next((i for i, v in enumerate(prod_last5) if v[0] == machine2), None)
        if count_index:
            cnt = prod_last5[count_index][1]
        else:
            cnt = 0

        # list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
        # cnt33 = len(list2)

        count_index = next((i for i, v in enumerate(prod_shift) if v[0] == machine2), None)
        if count_index:
            cnt33 = prod_shift[count_index][1]
        else:
            cnt33 = 0

        rate3 = cnt / float(rate2)
        rate3 = int(rate3 * 100) # This will be the percentage we use to determine colour

        # Pediction
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

        # # Use the below pred8 for normal
        pred8.append(pred1)

        # This is temp for total so far
        # pred8.append(cnt33)


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

        # if machine2=='1800' or machine2=='1801' or machine2 =='1802': cc='#C8C8C8'
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

    return total8, op_total, wip_zip

def cell_track_1467(request):
    shift_start, shift_time, shift_left, shift_end = stamp_shift_start()	 # Get the Time Stamp info
    machines1 = ['644','645','646','647','648','649']
    rate = [6,6,6,6,6,6]
    line1 = [1,1,1,1,1,1]
    operation1 = [10,10,10,10,10,10]
    prt = '50-1467'
    machine_rate = list(zip(machines1,rate,operation1))
    machine_color =[]
    cursor = connections['prodrpt-md'].cursor()

    # Filter a List
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


    # Preliminary testing variables for new methord
    tt = int(time.time())
    t=tt-300
    start1 = tt-shift_time
    sql="SELECT * FROM GFxPRoduction WHERE TimeStamp >='%s' and Part='%s'"%(start1,prt)
    cursor.execute(sql)
    tmpX=cursor.fetchall()
    # *********************************************

    for i in machine_rate:
        machine2 = i[0]
        rate2 = 1400 / float(i[1])
        rate2 = (rate2 / float(28800)) * 300

        list2 = list(filter(lambda x:x[4]>=t and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
        cnt = len(list2)
        list2 = list(filter(lambda x:x[4]>=start1 and x[1]==machine2,tmpX))  # Filter list to get 5 min sum
        cnt33 = len(list2)


        rate3 = cnt / float(rate2)
        rate3 = int(rate3 * 100) # This will be the percentage we use to determine colour
        # Pediction
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
            cc='#009700'
        elif rate3>=80:
            cc='#4FC34F'
        elif rate3>=70:
            cc='#4FC34F'
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

    t = int(time.time())
    request.session['runrate'] = 1128

    return render(request,'cell_track_1467.html',{'t':t,'codes':total8,'op':op_total,'args':args})	

def cell_track_8670(request):

    shift_start, shift_time, shift_left, shift_end = stamp_shift_start_3()	 # Get the Time Stamp info
    machines1 = ['1703L','1704L','658','661','1703R','1704R','622','623','1727','659','626','1712','1716L','1719','1723','Laser']
    rate = [4,4,4,4,4,4,4,4,1,2,1,1,1,1,1,1]
    line1 = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    operation1 = [10,10,10,10,30,30,30,30,40,50,50,60,70,80,90,130]
    prt = '50-8670'
    pp = '6420'
    machine_rate = list(zip(machines1,rate,operation1))
    machine_color =[]
    cursor = connections['prodrpt-md'].cursor()

    # Filter a List
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


    # Preliminary testing variables for new methord
    tt = int(time.time())
    t=tt-300
    start1 = tt-shift_time

    sql="SELECT * FROM GFxPRoduction WHERE TimeStamp >='%s' and Part='%s'"%(start1,prt)
    cursor.execute(sql)
    tmpX=cursor.fetchall()


    sql="SELECT * FROM barcode WHERE scrap >='%s'"%(start1)
    cursor.execute(sql)
    tmpY=cursor.fetchall()
    # *********************************************
    

    for i in machine_rate:
        machine2 = i[0]

        rate2 = 300 / float(i[1])
        rate2 = (rate2 / float(28800)) * 300
        
        # If 1510 going take out below conditional statement
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

        # Pediction
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

    total8_5404,op_total_5404 = cell_track_5404(request)
    total8_5401,op_total_5401 = cell_track_5401(request)

    t = int(time.time())
    request.session['runrate'] = 1128

    # This section will check every 30min and email out counts to Jim and Myself

    # Take it out for now.   Errors when using GMail accounts

    # # try:
    # db, cur = db_set(request)
    # cur.execute("""CREATE TABLE IF NOT EXISTS tkb_email_10r(Id INT PRIMARY KEY AUTO_INCREMENT,dummy1 INT(30),stamp INT(30) )""")
    # eql = "SELECT MAX(stamp) FROM tkb_email_10r"
    # cur.execute(eql)
    # teql = cur.fetchall()
    # teql2 = int(teql[0][0])
    # ttt=int(time.time())
    # elapsed_time = ttt - teql2
    # if elapsed_time > 1800:
    # 	x = 1
    # 	dummy = 8
    # 	cur.execute('''INSERT INTO tkb_email_10r(dummy1,stamp) VALUES(%s,%s)''', (dummy,ttt))
    # 	db.commit()
    # 	track_email(request)  
    # db.close()
    # # except:
    # # 	dummy2 = 0

    # *****************************************************************************************************

    # return render(request,'cell_5404.html',{'t':t,'codes':total8,'op':op_total,'args':args})	
    return render(request,'cell_track_8670.html',{'t':t,'codes':total8,'op':op_total,'codes_5404':total8_5404,'op_5404':op_total_5404,'codes_5401':total8_5401,'op_5401':op_total_5401,'args':args})	

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


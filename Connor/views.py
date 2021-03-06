# -*- coding:utf-8 -*-
from django.shortcuts import render
from Connor import models
from django.http import HttpResponse
import time
import json
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import collections
import xlsxwriter
import csv
from django.db.models import Sum
import numpy as np
import os
import xlrd
import sqlite3



# Create your views here.

# 登陆界面控制器
def login(request):

    return render(request, "login.html")
# 主界面框架控制器
def index(request):
    if request.method == "POST":
        username = request.POST.get("_ctl0:txtusername", None)
        password = request.POST.get("_ctl0:txtpassword", None)
        if not models.UserInfo.objects.filter(user="nlp", pwd="nlp503"):
            models.UserInfo.objects.create(user="nlp", pwd="nlp503")
        info = models.UserInfo.objects.filter(user=username, pwd=password)
        if info:
            request.session['username'] = username
            request.session['password'] = password
            return render(request, "index.html")
        else:
            return render(request, "login.html", {"message": "用户不存在或密码错误"})
    elif request.session.get('username', None):
        return render(request, "index.html")
    else:
        return render(request, "login.html", {"message": "走正门"})

# 主界面顶部控制器
def topFrame(request):
    if request.session.get('username', None):
        return render(request, "topFrame.html")
    else:
        return render(request, "login.html", {"message": "走正门"})

# 主界面顶部第二栏控制器
def colFrame(request):
    if request.session.get('username', None):
        import time
        data = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        return render(request, "colFrame.html", {"data": data})
    else:
        return render(request, "login.html", {"message": "走正门"})

# 主界面左侧菜单控制器
def MenuFrame(request):
    if request.session.get('username', None):
        return render(request, "MenuFrame.html")
    else:
        return render(request, "login.html", {"message": "走正门"})

# 主界面左侧展开收起控制器
def pushRLFrame(request):
    if request.session.get('username', None):
        return render(request, "pushRLFrame.html")
    else:
        return render(request, "login.html", {"message": "走正门"})

# 主界面默认内容控制器
def PageFrame(request):
    if request.session.get('username', None):
        import tools
        import time
        startdata, enddata = tools.daterange()
        # 读取配置文件location.conf
        # 这种方法慢了
        # if not models.locationconf.objects.count():
        #     models.locationconf.objects.create(user="nlp",page="1",li="0")
        info = models.locationconf.objects.filter(id="1")
        if not info:
            models.locationconf.objects.create(user="nlp", page="1", li="0",
                                               time=time.strftime('%Y-%m-%d', time.localtime(time.time())))
        user = info.values()[0]["user"]
        page = info.values()[0]["page"]
        li = info.values()[0]["li"]
        saved = int(page) * int(li)
        time = info.values()[0]["time"]
        # 如果收到后台请求
        if request.method == "POST":
            import sys
            sys.path.append("..")
            # 爬虫
            from spider.crawl_list import ESIspider
            from Connor.models import EsiDissertation
            es = ESIspider()
            title, context, author, publication = es.get_SCIurl()
            EsiDissertation.objects.create(title=title, author=author, context=context, publication=publication)
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')
            btn = "暂停"
            status = 11
            result = "Error!"
            return HttpResponse(json.dumps({
                "status": status,
                "result": result,
                "btn": btn
            }))

        return render(request, "PageFrame.html",
                      {"startdata": startdata, "enddata": enddata, "user": user, "saved": str(saved), "time": time})
    else:
        return render(request, "login.html", {"message": "走正门"})

#以下四个为外部函数
def qwer(*args):
    data = models.Dissertation.objects.filter(*args)
    return data
def mespaper_data(year,*args):
    paper_data = models.Dissertation.objects.filter(*args, DATE__contains=year)
    return paper_data

def mespaper_data2(*args):
    paper_data = models.Dissertation.objects.filter(*args)
    return paper_data

def mesname(names, refclist, *args):
    dic = collections.OrderedDict()
    for refc in refclist:
        if '~' in refc:
            rge = (int(refc.split('~')[0]), int(refc.split('~')[1]))
            names['rec%s' % refc] = models.Dissertation.objects.filter(*args, REFERCOUNT__range=rge).count()
        elif '>=' in refc:
            larger = int(refc.split('>=')[1])
            names['rec%s' % refc] = models.Dissertation.objects.filter(*args, REFERCOUNT__gte=larger).count()
        else:
            same = int(refc)
            names['rec%s' % refc] = models.Dissertation.objects.filter(*args, REFERCOUNT__exact=same).count()
        dic.setdefault('%s' % refc, names['rec%s' % refc])
        # dic['%s' % refc] = names['rec%s' % refc]
    return dic

def Page_lwtj(request):
    if request.session.get('username', None):

        ESI22 = ['None','ALL', 'COMPUTER SCIENCE', 'ENGINEERING', 'MATERIALS SCIENCES', 'BIOLOGY & BIOCHEMISTRY',
                 'ENVIRONMENT & ECOLOGY', 'MICROBIOLOGY', 'MOLECULAR BIOLOGY & GENETICS',
                 'SOCIAL SCIENCES',
                 'ECONOMICS & BUSINESS', 'CHENISTRY', 'GEOSCIENCES', 'MATHEMATICS', 'PHYSICS',
                 'SPACE SCIENCE',
                 'AGRICULTURAL SCIENCES', 'PLANT & ANIMAL SCIENCE', 'CLINICAL MEDICINE', 'IMMUNOIOGY',
                 'NEUROSCIENCE & BEHAVIOR', 'PHARMACOLOGY & TOXICOLOGY', 'PSYCHOLOGR & PSYCHIATRY',
                 'MULTIDISCIPLINARY']
        dic = {}

        units = {'总体情况': ' ', '材料与冶金学院': 'Coll Mat & Met|Sch Met & Mat', '理学院': 'Coll Sci',
                 '化学工程与技术学院': 'Sch Chem & Chem Engn|Sch Chem Engn & Technol|Coll Chem Engn & Techno',
                 '医学院': 'Coll Med|Sch Med',
                 '资源与环境工程学院': 'Coll Resource & Environm Engn|Sch Resource & Environm Engn',
                 '计算机科学与技术学院': 'Coll Comp Sci & Technol|Sch Comp Sci', '信息科学与工程学院': 'Sch Informat Sci & Engn',
                 '机械自动化学院': 'Sch Mech Engn|Coll Mech & Automat|Sch Machinery & Automat',
                 '附属天佑医院': 'Affiliated Tianyou Hosp|Tianyou Hosp', '国际钢铁研究院': 'Int Res Inst Steel Technol',
                 '管理学院': 'Sch Management',
                 '生物医学研究院': 'Inst Biol & Med', '附属普仁医院': 'Puren Hosp', '城市建设学院': 'Coll Urban Construct',
                 '武汉科技大学城市学院': 'City Coll', '文法与经济学院': 'Res Ctr SME', '汉阳医院': 'Hanyang Hosp',
                 '汽车与交通工程学院': 'Sch Automobile & Traff Engn'}
        if request.method == "POST":
            searchUnit11 = request.POST.get('selunit', None)
            searchUnit11 = searchUnit11.encode('utf-8')
            searchEsi11 = request.POST.get('selesi', None)
        else:
            searchUnit11 = '理学院'
            searchEsi11 = 'ALL'

        searchEsi = searchEsi11
        searchUnit = searchUnit11


        for i in units:
            if i != searchUnit:
                continue
            newunits = units[i].split('|')

            if len(newunits) == 3:
                args = (Q(MECHANISM__icontains=newunits[0]) | Q(MECHANISM__icontains=newunits[1]) | Q(
                    RESEARCHDIR__icontains=newunits[2]))
            elif len(newunits) == 2:
                args = (Q(MECHANISM__icontains=newunits[0]) | Q(MECHANISM__icontains=newunits[1]))
            else:
                args = (Q(MECHANISM__icontains=newunits[0]))

            data = models.Dissertation.objects.filter(args)

        data88 = models.Journals.objects.filter()
        title88 = []
        if searchEsi != "ALL":
            for i in data88:
                if searchEsi in i.CATE:
                    v = [i.TITLE, i.TITLE29, i.TITLE20]
                    title88.append(v)

            for i in range(len(title88)):
                title88[i][0] = str(title88[i][0]).upper()
                title88[i][1] = str(title88[i][1]).upper()
                title88[i][2] = str(title88[i][2]).upper()
            for j in data:
                j.PUBLICATION = str(j.PUBLICATION).upper()

            data99 = []
            for i in range(len(title88)):
                for j in data:
                    if title88[i][0] in j.PUBLICATION or title88[i][1] in j.PUBLICATION or title88[i][2] in j.PUBLICATION or j.PUBLICATION in title88[i][0] or j.PUBLICATION in title88[i][1] or j.PUBLICATION in title88[i][2]:
                        data99.append(j)
                        break
            data = data99


        # 把所有的作者全称存入一个列表aulist
        aulist = []
        for au in data:
            a = []
            b = []
            author1 = []
            for i in range(len(au.AULIST)):
                if au.AULIST[i] == '(':
                    a.append(i)
                if au.AULIST[i] == ')':
                    b.append(i)
            lis1 = zip(a, b)
            for i, j in lis1:
                author1.append(au.AULIST[i + 1:j])
            aulist.append(author1)

        b=[]
        for i in aulist:
            a = []
            for j in i:
                j=str(j)
                j=j.replace(',','')
                j = j.replace('-', '')
                j=j.lower()
                a.append(j)
            b.append(a)

        aulist=b

        #‘排名’和名称

        unit1 = []
        cn = []
        en = []
        staffs_unit = models.Staffs.objects.values('INSTITUTION').all()
        staffs_cn = models.Staffs.objects.values('STAFFNAME_CN').all()
        staffs_en = models.Staffs.objects.values('STAFFNAME_EN').all()
        for i in staffs_unit:
            unit1.append(i['INSTITUTION'])
        for j in staffs_cn:
            cn.append(j['STAFFNAME_CN'])
        for k in staffs_en:
            en.append(k['STAFFNAME_EN'])

        a=[]
        for i in en:
            # i=str(i)
            i=i.lower()
            a.append(i)
        en=a

        #篇数
        paper_num = []
        for i in en:
            c = 0
            for j in aulist:
                for k in j:
                    if i == k:
                        c += 1
                        break
            paper_num.append(c)

        #被引频次
        z = zip(data, aulist)

        paper_cited = []
        for i in en:

            c = 0
            for l in range(len(aulist)):
                for j in z[l][1]:
                    if i == j:
                        c += z[l][0].REFERCOUNT
                        break
            paper_cited.append(c)

        #国际合作单位
        internation = []
        for n in en:
            coo_num = 0
            for j in range(len(aulist)):
                for k in z[j][1]:
                    if n == k:
                        for each in z[j][0].MECHANISM.split("u'")[1:-1]:
                            if 'China' not in each:
                                coo_num += 1
                                break
                        break
            internation.append(coo_num)

        lis1 = []
        d = zip(paper_num, cn, unit1, paper_cited, internation)
        for i in range(len(paper_num)):
            lis1.append(d[i])
        lis1 = sorted(lis1, reverse=True)
        lis2 = []
        for i in lis1:
            if i[0] != 0:
                lis2.append(i)


        paper_num2 = []
        cn2 = []
        unit2 = []
        paper_cited2 = []
        internation2 = []

        for i in lis1:
            paper_num2.append(i[0])
            cn2.append(i[1])
            unit2.append(i[2])
            paper_cited2.append(i[3])
            internation2.append(i[4])
        lis = list(range(len(lis2)))
        staffs = zip(lis, unit2, cn2, en, paper_num2, paper_cited2, internation2)

        return render(request, "Page_lwtj.html", {'staffs': staffs, 'units': units.keys(),
                                                  'unit': searchUnit,'esis': ESI22, 'esi': searchEsi})
    else:
        return render(request, "login.html", {"message": "走正门"})

#论文统计控制器
def spiderSen(request):
    if request.session.get('username', None):
        return render(request, "spider.html")
    else:
        return render(request, "login.html", {"message": "走正门"})

#Page_lwzl中的全局变量
data22 = []
List22 = []
aulist22 = []
mechanism22 = []
title122 = []
date122 = []
hot122 = []
hightref122 = []
publication122 = []
totalcount122 = []
esi22 = []


def Page_lwzl(request):
    if request.method == "GET":

        if request.GET.get('tf'):

            title = request.GET.get('title')
            author = request.GET.get('author')
            date = request.GET.get('date')
            hightref = request.GET.get('hightref')
            hot = request.GET.get('hot')

            from django.db.models import Q
            global data22
            global List22
            global mechanism22
            global aulist22
            global title122
            global date122
            global hot122
            global hightref122
            global publication122
            global totalcount122
            global esi22

            args = (Q())

            dic = {"TITLE__contains": title, "AULIST__contains": author, "DATE__contains": date,
                   "HIGHTREF__contains": hightref, "HOT__contains": hot}
            dic1 = {}
            lis = []

            for k, v in dic.items():
                if v:
                    dic1[k] = v
            lis = [Q(TITLE__contains=title), Q(AULIST__contains=author), Q(DATE__contains=date),
                   Q(HIGHTREF__contains=hightref), Q(HOT__contains=hot)]
            lissearch = []
            dicarg = [title, author, date, hightref, hot]
            for i in xrange(len(dicarg)):
                if dicarg[i] != '':
                    lissearch.append(lis[i])

            for i in xrange(len(lissearch)):
                if i == 0:
                    args = lissearch[i]
                else:
                    args = args & lissearch[i]
            args = (args)

            page = request.GET.get('page')
            data22 = qwer(args)

            for i in data22:
                title122.append(i.TITLE)
                date122.append(i.DATE)
                hot122.append(i.HOT)
                hightref122.append(i.HIGHTREF)
                publication122.append(i.PUBLICATION)
                totalcount122.append(i.TOTALREFCOUNT)

            title_data = []
            esi22 = []

            # 遍历paper_publiction ,将Journals表中的 该期刊对象存入  title_data
            for publication in publication122:
                title_data.append(models.Journals.objects.filter(
                    Q(TITLE__icontains=publication) | Q(TITLE29__icontains=publication) | Q(
                        TITLE20__icontains=publication)))

            # 遍历title_data ,判断属于哪个ESI学科，并存入对应的esi_statistics 列表。

            for title in title_data:

                if title:
                    esi22.append(title[0].CATE)
                else:
                    esi22.append("no")

            aulist22 = []
            for au in data22:
                a = []
                b = []
                author122 = ""
                for i in range(len(au.AULIST)):
                    if au.AULIST[i] == '(':
                        a.append(i)
                    if au.AULIST[i] == ')':
                        b.append(i)

                lis1 = zip(a, b)
                for i, j in lis1:
                    author122 = author122 + ' ' + '|' + ' ' + au.AULIST[i + 1:j]

                aulist22.append(author122)

            mechanism22 = []
            for au in data22:
                a = []
                b = []
                c = 1
                mechanism122 = ""
                for i in range(len(au.MECHANISM)):
                    if au.MECHANISM[i:i + 2] == "u'":
                        a.append(i)
                        c = 0
                    if (au.MECHANISM[i] == ',') and (c == 0):
                        b.append(i)
                        c = 1
                lis2 = zip(a, b)
                for i, j in lis2:
                    strbak = au.MECHANISM[i + 2:j]
                    if strbak.find("Wuhan Univ Sci") == (-1):
                        if ']' in strbak:
                            strbak = strbak.split(']')[1]
                        mechanism122 = mechanism122 + ' ' + '|' + ' ' + strbak
                    else:
                        pass

                mechanism22.append(mechanism122)

            List22 = map(str, range(1, 1000))

            contact_list = data22.all()

            paginator = Paginator(contact_list, 10)
            paginator1 = Paginator(aulist22, 10)
            paginator2 = Paginator(mechanism22, 10)
            paginator3 = Paginator(List22, 10)
            paginator4 = Paginator(esi22, 10)
            try:

                aulist66 = paginator1.page(page)
                mechanism66 = paginator2.page(page)
                List66 = paginator3.page(page)
                esi66 = paginator4.page(page)
                contacts = paginator.page(page)

            except PageNotAnInteger:
                aulist66 = paginator1.page(1)
                mechanism66 = paginator2.page(1)
                List66 = paginator3.page(1)
                esi66 = paginator4.page(1)
                contacts = paginator.page(1)
            except EmptyPage:
                aulist66 = paginator1.page(paginator.num_pages)
                mechanism66 = paginator2.page(paginator.num_pages)
                List66 = paginator3.page(paginator.num_pages)
                esi66 = paginator4.page(paginator.num_pages)
                contacts = paginator.page(paginator.num_pages)

            lis = zip(contacts, List66, aulist66, mechanism66, esi66)
            listall = zip(List22, title122, aulist22, publication122, mechanism22, date122, esi22, totalcount122,
                          hot122, hightref122)

            csvFile2 = open('./static/download/csvFile2.csv', 'wb')  # 设置newline，否则两行之间会空一行
            writer = csv.writer(csvFile2)
            m = len(listall)
            writer.writerow(["序号", "标题", "作者", "期刊", "合作机构", "出版年", "所属学科", "被引频次", "高低热点", "高低被引"])

            for i in range(m):
                writer.writerow(listall[i])
            csvFile2.close()

            dict = {"lis": lis, "contacts": contacts}

            return render(request, "Page_lwzl.html", dict)
        elif request.GET.get('page') > 1:

            page = request.GET.get('page')
            contact_list = data22.all()

            paginator = Paginator(contact_list, 10)  #
            paginator1 = Paginator(aulist22, 10)
            paginator2 = Paginator(mechanism22, 10)
            paginator3 = Paginator(List22, 10)
            paginator4 = Paginator(esi22, 10)

            try:
                aulist66 = paginator1.page(page)
                mechanism66 = paginator2.page(page)
                List66 = paginator3.page(page)
                esi66 = paginator4.page(page)
                contacts = paginator.page(page)
            except PageNotAnInteger:
                aulist66 = paginator1.page(1)
                mechanism66 = paginator2.page(1)
                List66 = paginator3.page(1)
                esi66 = paginator4.page(page)
                contacts = paginator.page(1)
            except EmptyPage:
                aulist66 = paginator1.page(paginator.num_pages)
                mechanism66 = paginator2.page(paginator.num_pages)
                List66 = paginator3.page(paginator.num_pages)
                esi66 = paginator4.page(paginator.num_pages)
                contacts = paginator.page(paginator.num_pages)
            lis = zip(contacts, List66, aulist66, mechanism66, esi66)

            dict = {"lis": lis, "contacts": contacts}

            return render(request, "Page_lwzl.html", dict)

        else:
            return render(request, "Page_lwzl.html")

    return render(request, "login.html", {"message": "走正门"})

def Page_yygx(request):
    import time
    thisyear = int(time.strftime('%Y', time.localtime(time.time())))
    year = [x for x in range(thisyear - 10, thisyear + 1)]
    paper_pair = []
    if request.method == "POST":
        searchYear = request.POST.get('selyear', None)
    else:
        searchYear = thisyear-10
    paper_list = models.Dissertation.objects.values("TITLE").filter(DATE__contains=searchYear)[:10]
    for paper in paper_list:
        refer = models.refer.objects.filter(TITLE__contains=paper['TITLE'])
        paper_pair.append(refer)
    return render(request, "Page_yygx.html", {"year": year, "paper_pair": paper_pair})

#被引频次分布
def Page_citationFrequency(request):
    dic = {}
    units = {'总体情况': ' ', '材料与冶金学院': 'Coll Mat & Met|Sch Met & Mat', '理学院': 'Coll Sci',
             '化学工程与技术学院': 'Sch Chem & Chem Engn|Sch Chem Engn & Technol|Coll Chem Engn & Techno',
             '医学院': 'Coll Med|Sch Med',
             '资源与环境工程学院': 'Coll Resource & Environm Engn|Sch Resource & Environm Engn',
             '计算机科学与技术学院': 'Coll Comp Sci & Technol|Sch Comp Sci', '信息科学与工程学院': 'Sch Informat Sci & Engn',
             '机械自动化学院': 'Sch Mech Engn|Coll Mech & Automat|Sch Machinery & Automat',
             '附属天佑医院': 'Affiliated Tianyou Hosp|Tianyou Hosp', '国际钢铁研究院': 'Int Res Inst Steel Technol',
             '管理学院': 'Sch Management',
             '生物医学研究院': 'Inst Biol & Med', '附属普仁医院': 'Puren Hosp', '城市建设学院': 'Coll Urban Construct',
             '武汉科技大学城市学院': 'City Coll', '文法与经济学院': 'Res Ctr SME', '汉阳医院': 'Hanyang Hosp',
             '汽车与交通工程学院': 'Sch Automobile & Traff Engn'}
    refclist = ['0', '1', '2', '3', '4', '5~10', '11~20', '21~30', '31~50', '51~70', '71~100', '101~150', '>=150']
    refclist2 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    names = locals()
    if request.method == "POST":
        searchUnit = request.POST.get('selunit', None)
        searchUnit = searchUnit.encode('utf-8')
    else:
        searchUnit = '理学院'
    for i in units:
        if i != searchUnit:
            continue
        newunits = units[i].split('|')

        if len(newunits) == 3:
            args = (Q(MECHANISM__icontains=newunits[0]) | Q(MECHANISM__icontains=newunits[1]) | Q(MECHANISM__icontains=newunits[2]))
            dic = mesname(names, refclist, args)
        elif len(newunits) == 2:
            args = (Q(MECHANISM__icontains=newunits[0]) | Q(MECHANISM__icontains=newunits[1]))
            dic = mesname(names, refclist, args)
        else:
            args = (Q(MECHANISM__icontains=newunits[0]))
            dic = mesname(names, refclist, args)


    esi_category = {'Computer Science': 0, 'Engineering': 0, 'Materials Sciences': 0, 'Biology & Biochemistry': 0,
                    'Environment & Ecology': 0, 'Microbiology': 0, 'Molecular Biology & Genetics': 0,
                    'Social Sciences': 0,
                    'Economics & Business': 0, 'Chemistry': 0, 'Geosciences': 0, 'Mathematics': 0, 'Physics': 0,
                    'Space Science': 0,
                    'Agricultural Sciences': 0, 'Plant & Animal Science': 0, 'Clinical Medicine': 0, 'Immunology': 0,
                    'Neuroscience & Behavior': 0, 'Pharmacology & Toxicology': 0, 'Psychology & Psychiatry': 0,
                    'Multidisciplinary': 0}
    esi_statistics = {}
    lis = [Q(REFERCOUNT__exact=0), Q(REFERCOUNT__exact=1), Q(REFERCOUNT__exact=2), Q(REFERCOUNT__exact=3),
           Q(REFERCOUNT__exact=4), Q(REFERCOUNT__range=(5, 10)), Q(REFERCOUNT__range=(11, 20)),
           Q(REFERCOUNT__range=(21, 30)), Q(REFERCOUNT__range=(31, 50)), Q(REFERCOUNT__range=(51, 70)),
           Q(REFERCOUNT__range=(71, 100)), Q(REFERCOUNT__range=(101, 150)), Q(REFERCOUNT__gte=150)]
    rng = range(13)
    lis2 = zip(refclist, rng)
    for i, j in lis2:
        args1 = args
        esi_statistics[i] = esi_category.copy()
        args1 = args1 & lis[j]
        args1 = (args1)
        #过滤得到二级单位，及对应的被引频次区间的所有 对象，存入paper_data
        paper_data = mespaper_data2(args1)

        paper_publication = []
        title_data = []
        #遍历paper_data,将文章的发表刊物存在  paper_publication
        for paper in paper_data:
            paper_publication.append(paper.PUBLICATION)

        #遍历paper_publiction ,将Journals表中的 该期刊对象存入  title_data
        for publication in paper_publication:
            title_data.append(models.Journals.objects.filter(Q(TITLE__icontains=publication) | Q(TITLE29__icontains=publication) | Q(TITLE20__icontains=publication)))

        # 遍历title_data ,判断属于哪个ESI学科，并存入对应的esi_statistics 列表。
        for title in title_data:

            for ti in title:
                if 'AGRICULTURAL SCIENCES' == ti.CATE:
                    esi_statistics[i]['Agricultural Sciences'] += 1
                elif 'BIOLOGY & BIOCHEMISTRY' == ti.CATE:
                    esi_statistics[i]['Biology & Biochemistry'] += 1
                elif 'CHEMISTRY' == ti.CATE:
                    esi_statistics[i]['Chemistry'] += 1
                elif 'CLINICAL MEDICINE' == ti.CATE:
                    esi_statistics[i]['Clinical Medicine'] += 1
                elif 'COMPUTER SCIENCE' == ti.CATE:
                    esi_statistics[i]['Computer Science'] += 1
                elif 'ECONOMICS & BUSINESS' == ti.CATE:
                    esi_statistics[i]['Economics & Business'] += 1
                elif 'ENGINEERING' == ti.CATE:
                    esi_statistics[i]['Engineering'] += 1
                elif 'ENVIRONMENT/ECOLOGY' == ti.CATE:
                    esi_statistics[i]['Environment & Ecology'] += 1
                elif 'GEOSCIENCES' == ti.CATE:
                    esi_statistics[i]['Geosciences'] += 1
                elif 'IMMUNOLOGY' == ti.CATE:
                    esi_statistics[i]['Immunology'] += 1
                elif 'MATERIALS SCIENCE' == ti.CATE:
                    esi_statistics[i]['Materials Sciences'] += 1
                elif 'MATHEMATICS' == ti.CATE:
                    esi_statistics[i]['Mathematics'] += 1
                elif 'MICROBIOLOGY' == ti.CATE:
                    esi_statistics[i]['Microbiology'] += 1
                elif 'MOLECULAR BIOLOGY & GENETICS' == ti.CATE:
                    esi_statistics[i]['Molecular Biology & Genetics'] += 1
                elif 'Multidisciplinary' == ti.CATE:
                    esi_statistics[i]['Multidisciplinary'] += 1
                elif 'NEUROSCIENCE & BEHAVIOR' == ti.CATE:
                    esi_statistics[i]['Neuroscience & Behavior'] += 1
                elif 'PHARMACOLOGY & TOXICOLOGY' == ti.CATE:
                    esi_statistics[i]['Pharmacology & Toxicology'] += 1
                elif 'PHYSICS' == ti.CATE:
                    esi_statistics[i]['Physics'] += 1
                elif 'PLANT & ANIMAL SCIENCE' == ti.CATE:
                    esi_statistics[i]['Plant & Animal Science'] += 1
                elif 'PSYCHIATRY/PSYCHOLOGY' == ti.CATE:
                    esi_statistics[i]['Psychology & Psychiatry'] += 1
                elif 'SOCIAL SCIENCES, GENERAL' == ti.CATE:
                    esi_statistics[i]['Social Sciences'] += 1
                else:
                    esi_statistics[i]['Space Science'] += 1

    return render(request, "Page_citationFrequency.html", {
        'refcount': {},
        'totalcount': json.dumps(dic),
        'esi': json.dumps(esi_statistics),
        'list': refclist,
        'units': units.keys(),
        'unit': searchUnit,
    })

#期刊影响因子分布
def Page_JournalImpactFactor(request):
    dic = {}
    from django.db.models import Q
    units = {'总体情况': ' ', '材料与冶金学院': 'Coll Mat & Met|Sch Met & Mat', '理学院': 'Coll Sci',
             '化学工程与技术学院': 'Sch Chem & Chem Engn|Sch Chem Engn & Technol|Coll Chem Engn & Techno',
             '医学院': 'Coll Med|Sch Med',
             '资源与环境工程学院': 'Coll Resource & Environm Engn|Sch Resource & Environm Engn',
             '计算机科学与技术学院': 'Coll Comp Sci & Technol|Sch Comp Sci', '信息科学与工程学院': 'Sch Informat Sci & Engn',
             '机械自动化学院': 'Sch Mech Engn|Coll Mech & Automat|Sch Machinery & Automat',
             '附属天佑医院': 'Affiliated Tianyou Hosp|Tianyou Hosp', '国际钢铁研究院': 'Int Res Inst Steel Technol',
             '管理学院': 'Sch Management',
             '生物医学研究院': 'Inst Biol & Med', '附属普仁医院': 'Puren Hosp', '城市建设学院': 'Coll Urban Construct',
             '武汉科技大学城市学院': 'City Coll', '文法与经济学院': 'Res Ctr SME', '汉阳医院': 'Hanyang Hosp',
             '汽车与交通工程学院': 'Sch Automobile & Traff Engn'}
    refclist = ['0', '1', '2', '3', '4', '5~10', '11~20', '21~30', '31~50', '51~70', '71~100', '101~150', '>=150']
    names = locals()
    if request.method == "POST":
        searchUnit = request.POST.get('selunit', None)
        searchUnit = searchUnit.encode('utf-8')
    else:
        searchUnit = '理学院'

    for i in units:
        if i != searchUnit:
            continue
        newunits = units[i].split('|')

        if len(newunits) == 3:
            args = (Q(MECHANISM__icontains=newunits[0]) | Q(MECHANISM__icontains=newunits[1]) | Q(
                MECHANISM__icontains=newunits[2]))
            dic = mesname(names, refclist, args)
        elif len(newunits) == 2:
            args = (Q(MECHANISM__icontains=newunits[0]) | Q(MECHANISM__icontains=newunits[1]))
            dic = mesname(names, refclist, args)
        else:
            args = (Q(MECHANISM__icontains=newunits[0]))
            dic = mesname(names, refclist, args)

    return render(request, "Page_JournalImpactFactor.html", {
        'refcount': {},
        'totalcount': json.dumps(dic),
        'esi': {},
        'list': refclist,
        'units': units.keys(),
        'unit': searchUnit,
    })

#年度论文及被引频次分布
def Page_annualPublications(request):
    dic = {}
    units = {'总体情况': ' ', '材料与冶金学院': 'Coll Mat & Met|Sch Met & Mat', '理学院': 'Coll Sci',
             '化学工程与技术学院': 'Sch Chem & Chem Engn|Sch Chem Engn & Technol|Coll Chem Engn & Techno',
             '医学院': 'Coll Med|Sch Med',
             '资源与环境工程学院': 'Coll Resource & Environm Engn|Sch Resource & Environm Engn',
             '计算机科学与技术学院': 'Coll Comp Sci & Technol|Sch Comp Sci', '信息科学与工程学院': 'Sch Informat Sci & Engn',
             '机械自动化学院': 'Sch Mech Engn|Coll Mech & Automat|Sch Machinery & Automat',
             '附属天佑医院': 'Affiliated Tianyou Hosp|Tianyou Hosp', '国际钢铁研究院': 'Int Res Inst Steel Technol',
             '管理学院': 'Sch Management',
             '生物医学研究院': 'Inst Biol & Med', '附属普仁医院': 'Puren Hosp', '城市建设学院': 'Coll Urban Construct',
             '武汉科技大学城市学院': 'City Coll', '文法与经济学院': 'Res Ctr SME', '汉阳医院': 'Hanyang Hosp',
             '汽车与交通工程学院': 'Sch Automobile & Traff Engn'}
    refclist = ['0', '1', '2', '3', '4', '5~10', '11~20', '21~30', '31~50', '51~70', '71~100', '101~150', '>=150']
    names = locals()
    if request.method == "POST":
        searchUnit = request.POST.get('selunit', None)
        searchUnit = searchUnit.encode('utf-8')
    else:
        searchUnit = '理学院'

    for i in units:
        if i != searchUnit:
            continue

        newunits = units[i].split('|')

        if len(newunits) == 3:
            args = (Q(MECHANISM__icontains=newunits[0]) | Q(MECHANISM__icontains=newunits[1]) | Q(
                RESEARCHDIR__icontains=newunits[2]))
        elif len(newunits) == 2:
            args = (Q(MECHANISM__icontains=newunits[0]) | Q(MECHANISM__icontains=newunits[1]))
        else:
            args = (Q(MECHANISM__icontains=newunits[0]))

    cur_year = int(time.strftime('%Y', time.localtime(time.time())))
    ref_count = {}
    total_count = {}
    esi_category = {'Computer Science': 0, 'Engineering': 0, 'Materials Sciences': 0, 'Biology & Biochemistry': 0,
                    'Environment & Ecology': 0, 'Microbiology': 0, 'Molecular Biology & Genetics': 0,
                    'Social Sciences': 0,
                    'Economics & Business': 0, 'Chemistry': 0, 'Geosciences': 0, 'Mathematics': 0, 'Physics': 0,
                    'Space Science': 0,
                    'Agricultural Sciences': 0, 'Plant & Animal Science': 0, 'Clinical Medicine': 0, 'Immunology': 0,
                    'Neuroscience & Behavior': 0, 'Pharmacology & Toxicology': 0, 'Psychology & Psychiatry': 0,
                    'Multidisciplinary': 0}
    esi_statistics = {}
    for year in range(cur_year - 10, cur_year + 1):
        year_ref_count = 0
        year_total_count = 0
        esi_statistics[year] = esi_category.copy()
        paper_publication = []
        title_data = []
        paper_data = mespaper_data(year, args)
        for paper in paper_data:
            paper_publication.append(paper.PUBLICATION)
            year_ref_count += paper.REFERCOUNT
            year_total_count += 1
        # 遍历paper_publiction ,将Journals表中的 该期刊对象存入  title_data
        for publication in paper_publication:
            title_data.append(models.Journals.objects.filter(Q(TITLE__icontains=publication) | Q(TITLE29__icontains=publication) | Q(TITLE20__icontains=publication)))
        # 遍历title_data ,判断属于哪个ESI学科，并存入对应的esi_statistics 列表。
        for title in title_data:
            for ti in title:
                if 'AGRICULTURAL SCIENCES' == ti.CATE:
                    esi_statistics[year]['Agricultural Sciences'] += 1
                elif 'BIOLOGY & BIOCHEMISTRY' == ti.CATE:
                    esi_statistics[year]['Biology & Biochemistry'] += 1
                elif 'CHEMISTRY' == ti.CATE:
                    esi_statistics[year]['Chemistry'] += 1
                elif 'CLINICAL MEDICINE' == ti.CATE:
                    esi_statistics[year]['Clinical Medicine'] += 1
                elif 'COMPUTER SCIENCE' == ti.CATE:
                    esi_statistics[year]['Computer Science'] += 1
                elif 'ECONOMICS & BUSINESS' == ti.CATE:
                    esi_statistics[year]['Economics & Business'] += 1
                elif 'ENGINEERING' == ti.CATE:
                    esi_statistics[year]['Engineering'] += 1
                elif 'ENVIRONMENT/ECOLOGY' == ti.CATE:
                    esi_statistics[year]['Environment & Ecology'] += 1
                elif 'GEOSCIENCES' == ti.CATE:
                    esi_statistics[year]['Geosciences'] += 1
                elif 'IMMUNOLOGY' == ti.CATE:
                    esi_statistics[year]['Immunology'] += 1
                elif 'MATERIALS SCIENCE' == ti.CATE:
                    esi_statistics[year]['Materials Sciences'] += 1
                elif 'MATHEMATICS' == ti.CATE:
                    esi_statistics[year]['Mathematics'] += 1
                elif 'MICROBIOLOGY' == ti.CATE:
                    esi_statistics[year]['Microbiology'] += 1
                elif 'MOLECULAR BIOLOGY & GENETICS' == ti.CATE:
                    esi_statistics[year]['Molecular Biology & Genetics'] += 1
                elif 'Multidisciplinary' == ti.CATE:
                    esi_statistics[year]['Multidisciplinary'] += 1
                elif 'NEUROSCIENCE & BEHAVIOR' == ti.CATE:
                    esi_statistics[year]['Neuroscience & Behavior'] += 1
                elif 'PHARMACOLOGY & TOXICOLOGY' == ti.CATE:
                    esi_statistics[year]['Pharmacology & Toxicology'] += 1
                elif 'PHYSICS' == ti.CATE:
                    esi_statistics[year]['Physics'] += 1
                elif 'PLANT & ANIMAL SCIENCE' == ti.CATE:
                    esi_statistics[year]['Plant & Animal Science'] += 1
                elif 'PSYCHIATRY/PSYCHOLOGY' == ti.CATE:
                    esi_statistics[year]['Psychology & Psychiatry'] += 1
                elif 'SOCIAL SCIENCES, GENERAL' == ti.CATE:
                    esi_statistics[year]['Social Sciences'] += 1
                else:
                    esi_statistics[year]['Space Science'] += 1

        ref_count[year] = year_ref_count * 1
        # times -1 to show the data on the left in the chart
        total_count[year] = year_total_count * -1

    return render(request, "Page_annualPublications.html", {
        'refcount': json.dumps(ref_count),
        'totalcount': json.dumps(total_count),
        'esi': json.dumps(esi_statistics),
        'units': units.keys(),
        'unit': searchUnit,
    })

#合作论文分布
def Page_cooperationTypes(request):

    ESI22 = ['None', 'ALL', 'COMPUTER SCIENCE', 'ENGINEERING', 'MATERIALS SCIENCES', 'BIOLOGY & BIOCHEMISTRY',
             'ENVIRONMENT & ECOLOGY', 'MICROBIOLOGY', 'MOLECULAR BIOLOGY & GENETICS',
             'SOCIAL SCIENCES',
             'ECONOMICS & BUSINESS', 'CHENISTRY', 'GEOSCIENCES', 'MATHEMATICS', 'PHYSICS',
             'SPACE SCIENCE',
             'AGRICULTURAL SCIENCES', 'PLANT & ANIMAL SCIENCE', 'CLINICAL MEDICINE', 'IMMUNOIOGY',
             'NEUROSCIENCE & BEHAVIOR', 'PHARMACOLOGY & TOXICOLOGY', 'PSYCHOLOGR & PSYCHIATRY',
             'MULTIDISCIPLINARY']
    dic = {}
    units = {'总体情况': '', '材料与冶金学院': 'Coll Mat & Met|Sch Met & Mat', '理学院': 'Coll Sci',
             '化学工程与技术学院': 'Sch Chem & Chem Engn|Sch Chem Engn & Technol|Coll Chem Engn & Techno',
             '医学院': 'Coll Med|Sch Med',
             '资源与环境工程学院': 'Coll Resource & Environm Engn|Sch Resource & Environm Engn',
             '计算机科学与技术学院': 'Coll Comp Sci & Technol|Sch Comp Sci', '信息科学与工程学院': 'Sch Informat Sci & Engn',
             '机械自动化学院': 'Sch Mech Engn|Coll Mech & Automat|Sch Machinery & Automat',
             '附属天佑医院': 'Affiliated Tianyou Hosp|Tianyou Hosp', '国际钢铁研究院': 'Int Res Inst Steel Technol',
             '管理学院': 'Sch Management',
             '生物医学研究院': 'Inst Biol & Med', '附属普仁医院': 'Puren Hosp', '城市建设学院': 'Coll Urban Construct',
             '武汉科技大学城市学院': 'City Coll', '文法与经济学院': 'Res Ctr SME', '汉阳医院': 'Hanyang Hosp',
             '汽车与交通工程学院': 'Sch Automobile & Traff Engn'}
    if request.method == "POST":
        searchUnit11 = request.POST.get('selunit', None)
        searchUnit11 = searchUnit11.encode('utf-8')
        searchEsi11 = request.POST.get('selesi', None)
    else:
        searchUnit11 = '理学院'
        searchEsi11 = 'ALL'
    searchEsi = searchEsi11
    searchUnit = searchUnit11

    for i in units:
        if i != searchUnit:
            continue
        newunits = units[i].split('|')

        if len(newunits) == 3:
            args = (Q(MECHANISM__icontains=newunits[0]) | Q(MECHANISM__icontains=newunits[1]) | Q(
                RESEARCHDIR__icontains=newunits[2]))
        elif len(newunits) == 2:
            args = (Q(MECHANISM__icontains=newunits[0]) | Q(MECHANISM__icontains=newunits[1]))
        else:
            args = (Q(MECHANISM__icontains=newunits[0]))

        data = models.Dissertation.objects.filter(args)

    data88 = models.Journals.objects.filter()
    title88 =[]

    if searchEsi != "ALL":
        for i in data88:
            if searchEsi in i.CATE:
                v = [i.TITLE, i.TITLE29, i.TITLE20]
                title88.append(v)
        for i in range(len(title88)):
            title88[i][0] = str(title88[i][0]).upper()
            title88[i][1] = str(title88[i][1]).upper()
            title88[i][2] = str(title88[i][2]).upper()
        for j in data:
            j.PUBLICATION = str(j.PUBLICATION).upper()

        data99 = []
        for i in range(len(title88)):
            for j in data:
                if title88[i][0] in j.PUBLICATION or title88[i][1] in j.PUBLICATION or title88[i][2] in j.PUBLICATION or j.PUBLICATION in title88[i][0] or j.PUBLICATION in title88[i][1] or j.PUBLICATION in title88[i][2]:
                    data99.append(j)
                    break
        data = data99


    #统计篇数
    independence_coo = 0    #独立发表
    domestic_coo = 0    #国内合作
    internation_coo = 0 #国际合作
    HongKong_coo = 0    #香港合作
    Taiwan_coo = 0
    Macao_coo = 0

    #被引频次
    independence_cit = 0
    domestic_cit = 0
    internation_cit = 0
    HongKong_cit = 0
    Taiwan_cit = 0
    Macao_cit = 0

    for paper in data:
        for each in paper.MECHANISM.split("u'")[1:-1]:
            if 'China' not in each:
                internation_coo += 1
                internation_cit += paper.REFERCOUNT
                break
        a=0
        for each in paper.MECHANISM.split("u'")[1:-1]:
            if 'China' not in each:
                a = 1
        if a == 0:
            domestic_coo += 1
            domestic_cit += paper.REFERCOUNT

        if 'Hong Kong' in paper.MECHANISM:
            HongKong_coo += 1
            HongKong_cit += paper.REFERCOUNT

        if 'Taiwan' in paper.MECHANISM:
            Taiwan_coo += 1
            Taiwan_cit += paper.REFERCOUNT

        if 'Macao' in paper.MECHANISM:
            Macao_coo += 1
            Macao_cit += paper.REFERCOUNT

        b = 0
        for each in paper.MECHANISM.split("u'")[1:-1]:
            if 'Wuhan Univ Sci & Technol' not in each:
                b = 1
        if b == 0:
            independence_coo += 1
            independence_cit += paper.REFERCOUNT

    domestic_coo = domestic_coo - HongKong_coo - Taiwan_coo - Macao_coo
    domestic_cit = domestic_cit - HongKong_cit - Taiwan_cit - Macao_cit


    coo_type = ['独立发表', '国内合作(不包含港澳台)', '国际合作', '香港合作', '台湾合作', '澳门合作']
    coo_num = [independence_coo, domestic_coo, internation_coo, HongKong_coo, Taiwan_coo, Macao_coo]
    cit_num = [independence_cit, domestic_cit, internation_cit, HongKong_cit, Taiwan_cit, Macao_cit]
    aa = bb = cc = dd = ee = ff = 0
    ave_num = [aa, bb, cc, dd, ee, ff]
    for i in range(len(coo_num)):
        if coo_num[i] != 0:
            ave_num[i] = cit_num[i] * 1.0 / coo_num[i]
        else:
            ave_num[i] = 0
    coo = zip(coo_type, coo_num, cit_num, ave_num)

    return render(request, "Page_cooperationTypes.html", {"coo": coo, 'units': units.keys(),
                                                  'unit': searchUnit, 'esis': ESI22, 'esi': searchEsi})


def Page_lwfb(request):
    ESI22 = ['None', 'ALL', 'COMPUTER SCIENCE', 'ENGINEERING', 'MATERIALS SCIENCES', 'BIOLOGY & BIOCHEMISTRY',
             'ENVIRONMENT & ECOLOGY', 'MICROBIOLOGY', 'MOLECULAR BIOLOGY & GENETICS',
             'SOCIAL SCIENCES',
             'ECONOMICS & BUSINESS', 'CHENISTRY', 'GEOSCIENCES', 'MATHEMATICS', 'PHYSICS',
             'SPACE SCIENCE',
             'AGRICULTURAL SCIENCES', 'PLANT & ANIMAL SCIENCE', 'CLINICAL MEDICINE', 'IMMUNOIOGY',
             'NEUROSCIENCE & BEHAVIOR', 'PHARMACOLOGY & TOXICOLOGY', 'PSYCHOLOGR & PSYCHIATRY',
             'MULTIDISCIPLINARY']

    units = {'总体情况': ' ', '材料与冶金学院': 'Coll Mat & Met|Sch Met & Mat', '理学院': 'Coll Sci',
             '化学工程与技术学院': 'Sch Chem & Chem Engn|Sch Chem Engn & Technol|Coll Chem Engn & Techno',
             '医学院': 'Coll Med|Sch Med',
             '资源与环境工程学院': 'Coll Resource & Environm Engn|Sch Resource & Environm Engn',
             '计算机科学与技术学院': 'Coll Comp Sci & Technol|Sch Comp Sci', '信息科学与工程学院': 'Sch Informat Sci & Engn',
             '机械自动化学院': 'Sch Mech Engn|Coll Mech & Automat|Sch Machinery & Automat',
             '附属天佑医院': 'Affiliated Tianyou Hosp|Tianyou Hosp', '国际钢铁研究院': 'Int Res Inst Steel Technol',
             '管理学院': 'Sch Management',
             '生物医学研究院': 'Inst Biol & Med', '附属普仁医院': 'Puren Hosp', '城市建设学院': 'Coll Urban Construct',
             '武汉科技大学城市学院': 'City Coll', '文法与经济学院': 'Res Ctr SME', '汉阳医院': 'Hanyang Hosp',
             '汽车与交通工程学院': 'Sch Automobile & Traff Engn'}
    if request.method == "POST":
        searchUnit = request.POST.get('selunit', None)
        searchUnit = searchUnit.encode('utf-8')
        searchEsi = request.POST.get('selesi', None)
    else:
        searchUnit = "理学院"
        searchEsi = "ALL"

    for i in units:
        if i != searchUnit:
            continue
        newunits = units[i].split('|')
        if len(newunits) == 3:
            args = (Q(MECHANISM__icontains=newunits[0]) | Q(MECHANISM__icontains=newunits[1]) | Q(
                RESEARCHDIR__icontains=newunits[2]))
        elif len(newunits) == 2:
            args = (Q(MECHANISM__icontains=newunits[0]) | Q(MECHANISM__icontains=newunits[1]))
        else:
            args = (Q(MECHANISM__icontains=newunits[0]))

        data = models.Dissertation.objects.filter(args)

    # ‘排名’和名称
    lis = list(range(1, 31))
    data88 = models.Journals.objects.filter()
    title88 = []

    if searchEsi != "ALL":
        for i in data88:
            if searchEsi in i.CATE:

                v = [i.TITLE, i.TITLE29, i.TITLE20]
                title88.append(v)

        for i in range(len(title88)):
            title88[i][0] = str(title88[i][0]).upper()
            title88[i][1] = str(title88[i][1]).upper()
            title88[i][2] = str(title88[i][2]).upper()

        data99 = []
        for i in range(len(title88)):

            for j in data:
                j.PUBLICATION = str(j.PUBLICATION)
                if title88[i][0] in j.PUBLICATION or title88[i][1] in j.PUBLICATION or title88[i][2] in j.PUBLICATION or j.PUBLICATION in title88[i][0] or j.PUBLICATION in title88[i][1] or j.PUBLICATION in title88[i][2]:
                    data99.append(j)
                    break
        data = data99

    dic6 = {}
    for i in data:
        strbak = i.PUBLICATION
        strbak = str(strbak)
        dic6[strbak] = [0, 0, 0]

    for i in data:
        strbak = i.PUBLICATION
        strbak = str(strbak)
        dic6[strbak][0] = dic6[strbak][0] + 1
        dic6[strbak][1] = dic6[strbak][1] + i.TOTALREFCOUNT
        if dic6[strbak][0] != 0:
            dic6[strbak][2] = 1.0 * dic6[strbak][1] / dic6[strbak][0]
        else:
            dic6[strbak][2] = 0
    a = []
    b = []
    c = []
    d = []
    for k in dic6:
        a.append(k)
        b.append(dic6[k][0])
        c.append(dic6[k][1])
        d.append(dic6[k][2])
    staffs = zip(lis, a, b, c, d)
    staffs.sort(key=lambda x: x[4], reverse=True)
    return render(request, "Page_lwfb.html", {'staffs': staffs, 'units': units.keys(),
                                              'unit': searchUnit, 'esis': ESI22, 'esi': searchEsi})
def Page_lwhz(request):
    type1 = ["AVERAGE", "NUMBER", "FREQUENCY"]

    if request.method == "POST":
        type2 = request.POST.get('type2', None)
    else:
        type2 = "AVERAGE"

    data = models.Dissertation.objects.filter()

    dic = {}

    for au in data:
        a = []
        b = []
        c = 1

        for i in range(len(au.MECHANISM)):
            if au.MECHANISM[i:i + 2] == "u'":
                a.append(i)
                c = 0
            if (au.MECHANISM[i] == ',') and (c == 0):
                b.append(i)
                c = 1
        lis2 = zip(a, b)
        for i, j in lis2:
            strbak = au.MECHANISM[i + 2:j]
            if strbak.find("Wuhan Univ Sci") == (-1):
                if ']' in strbak:
                    strbak = strbak.split(']')[1]
                strbak = str(strbak)
                dic[strbak] = [0, 0, 0]
            else:
                pass

    for au in data:
        a = []
        b = []
        c = 1
        for i in range(len(au.MECHANISM)):
            if au.MECHANISM[i:i + 2] == "u'":
                a.append(i)
                c = 0
            if (au.MECHANISM[i] == ',') and (c == 0):
                b.append(i)
                c = 1
        lis2 = zip(a, b)
        for i, j in lis2:
            strbak = au.MECHANISM[i + 2:j]
            if strbak.find("Wuhan Univ Sci") == (-1):
                if ']' in strbak:
                    strbak = strbak.split(']')[1]
                strbak = str(strbak)
                dic[strbak][0] = dic[strbak][0] + 1
                dic[strbak][1] = dic[strbak][1] + au.TOTALREFCOUNT
                if dic[strbak][0] != 0:
                    dic[strbak][2] = 1.0 * dic[strbak][1] / dic[strbak][0]
                else:
                    dic[strbak][2] = 0
            else:
                pass

    a = []
    b = []
    c = []
    d = []
    for k in dic:
        a.append(k)
        b.append(dic[k][0])
        c.append(dic[k][1])
        d.append(dic[k][2])
    e = zip(a, b, c, d)
    if type2 == "AVERAGE":
        e.sort(key=lambda x: x[3], reverse=True)
    if type2 == "NUMBER":
        e.sort(key=lambda x: x[1], reverse=True)
    if type2 == "FREQUENCY":
        e.sort(key=lambda x: x[2], reverse=True)

    return render(request, "Page_lwhz.html", {"lis": e, "type1": type1, "type2": type2})

#二级单位论文贡献
def Page_journalsContribution(request):
    institutionDict = {
        '材料与冶金学院': ['Coll Mat & Met', 'Sch Met & Mat'],
        '理学院': ['Coll Sci'],
        '化学工程与技术学院': ['Sch Chem & Chem Engn', 'Sch Chem Engn & Technol', 'Coll Chem Engn & Techno'],
        '医学院': ['Coll Med', 'Sch Med'],
        '资源与环境工程学院': ['Coll Resource & Environm Engn', 'Sch Resource & Environm Engn'],
        '计算机科学与技术学院': ['Coll Comp Sci & Technol', 'Sch Comp Sci'],
        '信息科学与工程学院': ['Sch Informat Sci & Engn'],
        '机械自动化学院': ['Sch Mech Engn', 'Coll Mech & Automat', 'Sch Machinery & Automat'],
        '附属天佑医院': ['Affiliated Tianyou Hosp', 'Tianyou Hosp'],
        '国际钢铁研究院': ['Int Res Inst Steel Technol'],
        '管理学院': ['Sch Management'],
        '生物医学研究院': ['Inst Biol & Med'],
        '附属普仁医院': ['Puren Hosp'],
        '城市建设学院': ['Coll Urban Construct'],
        '武汉科技大学城市学院': ['City Coll'],
        '文法与经济学院': ['Res Ctr SME'],
        '汉阳医院': ['Hanyang Hosp'],
        '汽车与交通工程学院': ['Sch Automobile & Traff Engn']}
    institutionJournalDict = {
        '材料与冶金学院': 0,
        '理学院': 0,
        '化学工程与技术学院': 0,
        '医学院': 0,
        '资源与环境工程学院': 0,
        '计算机科学与技术学院': 0,
        '信息科学与工程学院': 0,
        '机械自动化学院': 0,
        '附属天佑医院': 0,
        '国际钢铁研究院': 0,
        '管理学院': 0,
        '生物医学研究院': 0,
        '附属普仁医院': 0,
        '城市建设学院': 0,
        '武汉科技大学城市学院': 0,
        '文法与经济学院': 0,
        '汉阳医院': 0,
        '汽车与交通工程学院': 0
    }
    if request.session.get('username', None):

        esi_statistics = institutionJournalDict.copy()

        for key in institutionDict:

            esi_statistics[key] = []

            for institute in institutionDict[key]:
                paper_data = list(models.Dissertation.objects.filter(MECHANISM__icontains=institute))

                # for paper in paper_data:
                #
                #     esi_statistics[key].append(paper)
                esi_statistics[key] += paper_data

            institutionJournalDict[key] = len(esi_statistics[key])
        print(esi_statistics)

        return render(request, "Page_journalsContribution.html", {
            'instituteContributeDict':json.dumps(institutionJournalDict),
            # 'esiStatistics':json.dumps(esi_statistics),
        })

    else:
        return render(request, "login.html", {"message": "走正门"})


#上传期刊Excel文件并保存至static/journalsExcelFolder
def Page_journalsImport(request):

    # if request.method == "POST":  # 请求方法为POST时，进行处理
    #     files = request.FILES.getlist("excels", None)
    #     if not files:
    #         return HttpResponse("no files for upload!")
    #
    #     for f in files:
    #         destination = open(os.path.join(".\static\journalsExcelFolder", f.name), 'wb+')
    #         for chunk in f.chunks():
    #             destination.write(chunk)
    #         destination.close()
    #
    #     JournalsDBAppend()
    #     return HttpResponse("上传成功")

    return render(request,"Page_journalsImport.html")
#上传职工Excel文件并保存到static/staffsExcelFolder
def Page_staffsImport(request):

    if request.method == "POST":  # 请求方法为POST时，进行处理
        files = request.FILES.getlist("excels", None)
        if not files:
            return HttpResponse("no files for upload!")

        for f in files:
            destination = open(os.path.join(".\static\staffsExcelFolder", f.name), 'wb+')
            for chunk in f.chunks():
                destination.write(chunk)
            destination.close()

        staffsDBAppend()
        return HttpResponse("上传成功")

    return render(request,"Page_staffsImport.html")

#解析期刊Excel数据存入数据库
def JournalsDBAppend():

    excelfolderpath = ".\static\journalsExcelFolder\\"

    conn = sqlite3.connect('.\db.sqlite3')
    c = conn.cursor()

    deleteSql = """delete from Connor_journals"""
    c.execute(deleteSql)

    pathDir = os.listdir(excelfolderpath)

    for allDir in pathDir:
        child = os.path.join(allDir)
        excelpath = excelfolderpath+child
        workbook = xlrd.open_workbook(excelpath)
        booksheet = workbook.sheet_by_index(0)

        for row in range(1, booksheet.nrows):
            row_data = []
            for col in range(booksheet.ncols):
                cel = booksheet.cell(row, col)
                val = cel.value
                val = str(val)
                row_data.append(val)
            if booksheet.ncols == 5:
                title = row_data[0]
                title29 = row_data[0]
                title20 = row_data[1]
                cate = row_data[4]
            else:
                title = row_data[0]
                title29 = row_data[1]
                title20 = row_data[2]
                cate = row_data[5]
            c.execute("insert into Connor_journals (TITLE,TITLE29,TITLE20,CATE) values (?, ?, ?, ?)",
                      (title, title29, title20, cate))
            conn.commit()

    conn.close()

#解析员工Excel导入数据库
def staffsDBAppend():
    excelfolderpath = ".\static\staffsExcelFolder\\"

    conn = sqlite3.connect('.\db.sqlite3')
    c = conn.cursor()

    deleteSql = """delete from Connor_staffs"""
    c.execute(deleteSql)

    pathDir = os.listdir(excelfolderpath)

    for allDir in pathDir:
        child = os.path.join(allDir)
        excelpath = excelfolderpath + child
        workbook = xlrd.open_workbook(excelpath)
        booksheet = workbook.sheet_by_index(0)

        for row in range(1, booksheet.nrows):
            row_data = []
            for col in range(booksheet.ncols):
                cel = booksheet.cell(row, col)
                val = cel.value
                val = str(val)
                row_data.append(val)
            institution = row_data[0]
            staffname_cn = row_data[1]
            staffname_en = row_data[2]

            c.execute("insert into Connor_staffs (INSTITUTION, STAFFNAME_CN, STAFFNAME_EN) values (?, ?, ?)",
                      (institution, staffname_cn, staffname_en))
            conn.commit()

    conn.close()
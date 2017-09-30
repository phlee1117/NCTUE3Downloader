import requests
import xml.etree.ElementTree
import urllib
import os
import datetime
import sys
from multiprocessing import Queue


def createFolder(name, path=''):
    try:
        os.mkdir(os.path.join(path, name))
    except FileExistsError:
        return


def requestXML(path, data):
    BASE_URL = "http://e3.nctu.edu.tw/mService/service.asmx/"
    HEADERS = {
        'content-type': 'application/x-www-form-urlencoded',
    }
    r = requests.post(BASE_URL + path, data=data, headers=HEADERS)
    root = xml.etree.ElementTree.fromstring(r.content)
    return root


def fileModified(date):
    fileTime = datetime.datetime.strptime(
        date, '%Y/%m/%d %H:%M:%S')
    if (fileTime >= lastTime):
        return True
    else:
        return False


def downloadFile(url, replace, folder, path):
    r = requests.get(url, stream=True)
    try:
        fileName = r.headers['Content-Disposition']
    except KeyError:
        return
    fileName = fileName.encode('latin-1').decode('utf-8')
    fileName = fileName[fileName.find('=') + 2:fileName.find(',') - 1]
    fileName = urllib.parse.unquote(fileName)
    print(fileName)
    segment = int(r.headers['content-length']) // 80
    cnt = 0
    if os.path.isfile(os.path.join(path, folder, fileName)) is False or replace:
        with open(os.path.join(path, folder, fileName), 'wb') as f:
            sum = 0
            for chunk in r.iter_content(chunk_size=1024):
                if sum > segment * cnt:
                    cnt += 1
                    print('#', end='', flush=True)
                if segment < 1024:
                    for k in range(((sum - (segment * cnt)) // segment)):
                        cnt += 1
                        print('#', end='', flush=True)
                sum += 1024
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
            print('')
    else:
        print('skip')


def downloadMaterial(docType, CourseName, CourseId, LoginTicket):
    if docType == 1:
        typeName = "課程講義"
    else:
        typeName = "參考資料"
    print(typeName)
    createFolder(typeName, CourseName)
    data = {"loginTicket": LoginTicket,
            "courseId": CourseId, 'docType': str(docType)}
    root = requestXML('GetMaterialDocList', data)
    DocumentId = []
    for j in root:
        DocumentId.append(j[11].text)
    for j in DocumentId:
        data = {"loginTicket": LoginTicket, "resId": j,
                'metaType': '10', 'courseId': CourseId}
        root = requestXML('GetAttachFileList', data)
        for k in root:
            if fileModified(k[8].text):
                downloadFile(k[4].text, replace=True,
                             path=CourseName, folder=typeName)
            else:
                print(k[3].text)
                print('skipped')


def downloadHomeWorkOrAnnouncement(HwOrAnn, CourseName, CourseId, LoginTicket):
    if HwOrAnn == 0:
        index = 25
        path = "GetStuHomeworkListWithAttach"
        typeName = "作業"
        repeat = 4
    else:
        index = 13
        path = "GetAnnouncementListWithAttach"
        typeName = "公告"
        repeat = 2
    print(typeName)
    createFolder(typeName, CourseName)
    for listType in range(1, repeat + 1):
        data = {"loginTicket": LoginTicket,
                "courseId": CourseId, "accountId": AccountId, 'listType': str(listType), 'bulType': str(listType)}
        root = requestXML(path, data)
        if len(root) > 0:
            for k in root:
                for j in k[index]:
                    if j.text is not None:
                        downloadFile(j.text[:-1], replace=False,
                                     path=CourseName, folder=typeName)


try:
    ACCOUNT = sys.argv[1]
    PASSWORD = sys.argv[2]
except IndexError:
    ACCOUNT = input('學號 ')
    PASSWORD = input('密碼 ')


while True:
    try:
        data = {"account": ACCOUNT, "password": PASSWORD}
        root = requestXML('Login', data)
        LoginTicket = root[0].text
        AccountId = root[1].text
        print("Login Success")
        break
    except:
        print("Login Fail")
        ACCOUNT = input('學號 ')
        PASSWORD = input('密碼 ')
        continue


try:
    f = open('lastTime.txt', 'r')
    try:
        lastTime = datetime.datetime.strptime(f.read(), '%Y/%m/%d %H:%M:%S')
        print("last run:" + lastTime.strftime("%Y/%m/%d %H:%M:%S"))
    except:
        print("lastTime.txt is corrupted.")
        lastTime = datetime.datetime(1970, 1, 1, 0, 0, 0)
    f.close()
except FileNotFoundError:
    print("Download all files.")
    lastTime = datetime.datetime(1970, 1, 1, 0, 0, 0)


programStartTime = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

data = {"loginTicket": LoginTicket, "accountId": AccountId, 'role': 'stu'}
root = requestXML('GetCourseList', data)
CourseId = []
CourseName = []
for i in root:
    CourseId.append(i[0].text)
    CourseName.append(i[3].text)


for i in range(len(CourseId)):
    print(CourseName[i])
    createFolder(CourseName[i])

    downloadMaterial(1, CourseName[i], CourseId[i], LoginTicket)
    downloadMaterial(2, CourseName[i], CourseId[i], LoginTicket)
    downloadHomeWorkOrAnnouncement(0, CourseName[i], CourseId[i], LoginTicket)
    downloadHomeWorkOrAnnouncement(1, CourseName[i], CourseId[i], LoginTicket)
    print('')

f = open('lastTime.txt', 'w')
f.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
f.close()

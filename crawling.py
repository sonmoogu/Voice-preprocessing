import time
import random
import os
import requests
from bs4 import BeautifulSoup
from threading import Thread
import wget
import urllib3
import re
import moviepy.editor as mp 

# requests에서 urllib3를 쓰며 발생하는 InsecureRequestsWarning을 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# request요청 시 보낼 header정보
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
}

def createDirectory(path):
    if not os.path.isdir(path):
        os.makedirs(path)

# 에러 발생한 파일 목록 저장
def createErrorList(fileName):
    file = open('./errorList.txt', 'a')
    file.write(fileName + '\n')
    file.close()

def startGetVideo(divLastPageNum):
    html = requests.get('https://phishing-keeper.fss.or.kr/fss/vstop/avoid/this_voice_l.jsp', headers=headers)
    soup = BeautifulSoup(html.text, 'html.parser')
    lastPage = soup.find('div', {'class':'paging'}).find_all('a')[-1]['href'][-2:]
    
    pageStep = int(lastPage) // divLastPageNum + 1
    
    threads = []
    for i in range(1, int(lastPage) + 1, pageStep):
        th = Thread(target=getVideoLinkAndDownload, args=(i, pageStep))
        threads.append(th)
        th.start()
        
    print(f'number of video thread : {len(threads)}')
    for thread in threads:
        thread.join()

def getVideoLinkAndDownload(page, pageStep):

    links = []
    
    for p in range(page, page + pageStep):
        html = requests.get(f'https://phishing-keeper.fss.or.kr/fss/vstop/avoid/this_voice_l.jsp?page={p}', headers=headers)
        soup = BeautifulSoup(html.text, 'html.parser')
        contents = soup.find_all('dd', {'class': 'tit'})
    
        for content in contents:
            links.append(content.find('a')['href'])

    downloadVideo(page - 1, links)

def downloadVideo(page, links):
    fileNumber = page * 6
    for link in links:
        print(f'start {fileNumber} video download')
        html = requests.get(link.replace('.', 'https://phishing-keeper.fss.or.kr/fss/vstop/avoid', 1), headers=headers)
        soup = BeautifulSoup(html.text, 'html.parser')
        
        req = requests.get(soup.find_all('tr')[2].find('a')['href'], stream=True, verify=False, headers=headers)
        fileNumber += 1

        try:
            with open(f'./video/file{fileNumber}.mp4', 'wb') as file:
                #file.write(req.content)
                for chunk in req.iter_content(chunk_size=2048):
                    if chunk:
                        file.write(chunk)
                file.close()
        # 이 에러 발생 시 실제 발생 원인은 EncodingError가 아닌 ConnectionResetError가 발생한 것
        # 에러 메시지로 Connection on reset by peer가 출력
        # 위 에러 메시지의 의미는 원격 서버에서 RST 패킷을 보내어 연결을 강제로 종료시킨 것(https://stackoverflow.com/questions/1434451/what-does-connection-reset-by-peer-mean)
        # RST 패킷은 이 패킷을 보낸 곳이 현재 연결된 상대방과의 연결을 즉시 끊기 위해 보내는 패킷
        except requests.exceptions.ChunkedEncodingError as e:
            print(f'Exception : download video{fileNumber} error : {e}')
            createErrorList(f'video{fileNumber}')

        # 하나 다운로드 한 뒤 10초 ~ 20초 랜덤으로 뽑아 대기
        # 고정적으로 두면 봇으로 판단 가능성 있음
        time.sleep(random.uniform(10, 20)) 

def startGetAudioAndText(divLastPageNum):
    html = requests.get('https://phishing-keeper.fss.or.kr/fss/vstop/bbs/list.jsp?category=100128&url=/fss/vstop/1436425918273&bbsid=1436425918273&page=1', headers=headers)
    soup = BeautifulSoup(html.text, 'html.parser')
    lastPage = soup.find('div', {'class': 'paging'}).find_all('a')[-1]['href'][-2:]

    pageStep = int(lastPage) // divLastPageNum + 1

    threads = []
    for i in range(1, int(lastPage) + 1, pageStep):
        th = Thread(target=getAudioAndTextLinkAndDownload, args=(i, pageStep))
        threads.append(th)
        th.start()
        
    print(f'number of audio & text thread : {len(threads)}')
    for thread in threads:
        thread.join()

def getAudioAndTextLinkAndDownload(page, pageStep):

    links = []

    for p in range(page, page + pageStep):
        html = requests.get(f'https://phishing-keeper.fss.or.kr/fss/vstop/bbs/list.jsp?category=100128&url=/fss/vstop/1436425918273&bbsid=1436425918273&page={p}', headers=headers)
        soup = BeautifulSoup(html.text, 'html.parser')
        aTagParents = soup.find_all('td', {'class': 't_al'})
    
        for aTagParent in aTagParents:
            links.append((aTagParent.find('a')['href']).replace('.', 'https://phishing-keeper.fss.or.kr/fss/vstop/bbs/', 1))
    
    downloadAudioAndText(page - 1, links)

def downloadAudioAndText(page, links):
    fileNumber = page * 10
    for link in links:
        print(f'\nstart {fileNumber} audio and text download')
        html = requests.get(link, headers=headers)
        soup = BeautifulSoup(html.text, 'html.parser')
        fileNumber += 1
        
        try :
            wget.download(soup.find('source')['src'], f'./audio/audio{fileNumber}.mp3')
        # 먼저 알아야 할 점은 wget모듈은 url처리 모듈인 urllib를 토대로 만들어진 것
        # 이 에러는 다운로드 받은 데이터 양이 Content-Length헤더 값에 명시된 전체 데이터의 양보다 적을 때 발생 : https://docs.python.org/ko/3/library/urllib.error.html#module-urllib.error
        # 발생 원인 예상 : video를 다운로드 받을 때 발생할 수 있는 ConnectionResetError와 같이 서버측에서 연결을 끊어 다운로드가 중지되어 이와 같은 에러가 발생한 것으로 보임
        # urlretrieve()는 사용 가능한 데이터양이 예상 양(Content-Length 헤더에 의해 보고된 크기)보다 작은 것을 감지하면 ContentTooShortError를 발생시킵니다. : https://docs.python.org/ko/3/library/urllib.request.html#urllib.request.urlretrieve
        # 예를 들어, 다운로드가 중단된 경우에 발생할 수 있습니다.
        except wget.ulib.ContentTooShortError as e:
            print(f'wget audio{fileNumber} error')
            createErrorList(f'audio{fileNumber}')

        # text가 담겨있는 class가 b_scroll인 div태그가 있으면 텍스트 긁어옴
        texts = soup.find('div', {'class':'b_scroll'})
        
        try:
            if texts:
                texts = texts.find_all('p')
                file = open(f'./text/audio{fileNumber}Text.txt', 'a')
                for text in texts:
                    file.write(text.text + '\n\n')
                file.close()
        except:
            print(f'download text{fileNumber} error')
            createErrorList(f'text{fileNumber}')
        
        # 하나 다운로드 한 뒤 10초 ~ 20초 랜덤으로 뽑아 대기
        # 고정적으로 두면 봇으로 판단 가능성 있음
        time.sleep(random.uniform(10, 20)) 

# 영상에서 오디오 추출
def extractAudio():
    path = './video/'
    fileList = os.listdir(path) # path내의 모든 파일 목록 리스트로 받아옴

    for videoFile in fileList:
        # 정규식이용 : a~z 또는 .mp4를 빈문자로 replace (file2.mp4 -> 2)
        fileNumber = re.sub("[a-z]|(.mp4)", '', videoFile)

        clip = mp.VideoFileClip(f'{path}{videoFile}')
        clip.audio.write_audiofile(f'./extractAudio/extractAudio{fileNumber}.mp3')

if __name__ == '__main__':
    t = time.time()

    createDirectory('./audio')
    createDirectory('./video')
    createDirectory('./text')
    createDirectory('./extractAudio')
    
    # lastPage를 인자 값으로 나눠 스레드 생성
    startGetVideo(3)
    startGetAudioAndText(3)
    extractAudio()

    print(f'time : {time.time() - t}')
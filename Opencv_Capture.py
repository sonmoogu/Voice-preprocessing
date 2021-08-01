import cv2

def capture_video(capture, frameRate, folderIdx):
    count = 0
    while (capture.isOpened):
        ret, frame = capture.read()
        if ret == False:
            break
        print()
        if(int(capture.get(1)) % frameRate == 0):
            cv2.imwrite("capture/" + folderIdx + "/frame%d.jpg" % count, frame)
            count += 1



for i in range(1,11):
    folderIdx = "video" + str(i)
    capture = cv2.VideoCapture("capture/" + folderIdx + "/video.mp4")
    frameCnt = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if frameCnt <= 50:
        frameRate = 0
    else:
        frameRate = (int)(frameCnt / 50)

    capture_video(capture, frameRate, folderIdx)


capture.release()


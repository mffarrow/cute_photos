import praw
import requests, os, re, glob, shutil, PIL
import pymysql as mdb
from bs4 import BeautifulSoup

#get the first 1000 submissions from the 'hot' section of the 'aww' subreddit:
r = praw.Reddit(user_agent='web_app:v1.0 (by /u/your_reddit_username)')
submissions = r.get_subreddit('aww').get_hot(limit=1000)
photos = []

for submission in submissions:
    if 'http://imgur.com/a/' in submission.url:
        # This is an album submission.
        albumId = submission.url[len('http://imgur.com/a/'):]
        htmlSource = requests.get(submission.url).text
        
        soup = BeautifulSoup(htmlSource)
        matches = soup.select('.album-view-image-link a')
        for match in matches:
            imageUrl = 'http:' + match['href']

        photos.append([imageUrl, submission.title, submission.score])

    elif 'http://i.imgur.com/' in submission.url:
        #The URL is a direct link to the image.
        imageUrl = submission.url
        photos.append([imageUrl, submission.title, submission.score])
    
    elif 'http://imgur.com/' in submission.url:
        # This is an Imgur page with a single image.        
        imageUrl = 'http://i.imgur.com/' + submission.url.rsplit('/',1)[1] + ".jpg"
        photos.append([imageUrl, submission.title, submission.score])

    else:
        pass

#clean up image urls
for photo in photos:
    if photo[0].split('.')[-1] == 'gifv':
        # remove .gifv files
        photos.remove(photo)

    elif photo[0].split('.')[-1] == 'webm':
        # remove .webm files
        photos.remove(photo)
    
    elif len(photo[0].split('.')[-1]) > 4:
        # remove ? and ?/ from file extensions of image urls 
        if len(photo[0].split("?")[-1]) == 1:
            url = photo[0]
            photo.remove(url)
            url = url.split("?")[0]
            photo.insert(0, url)
        else:
            pass
    
    elif str(photo[0].split('.')[-1]) == 'com/':
        #get rid of files without a file extension
        photos.remove(photo)
    else:
        pass
    

#get rid of emojis in titles
try:
    #UCS-4 build
    highpoints = re.compile(u'([\U00002600-\U000027BF])|([\U0001f300-\U0001f64F])|([\U0001f680-\U0001f6FF])')
except re.error:
    #UCS-2 build
    highpoints = re.compile(u'([\u2600-\u27BF])|([\uD83C][\uDF00-\uDFFF])|([\uD83D][\uDC00-\uDE4F])|([\uD83D][\uDE80-\uDEFF])')

for photo in photos:
    title = photo[1]
    photo.remove(title)
    photo.insert(1, highpoints.sub(u'', title))


#get filenumber of most recent SQL entry as an integer
db = mdb.connect(user="root", host="your_host", db="your_db", charset='utf8')
cur = db.cursor()
cur.execute("SELECT filenumber FROM your_table ORDER BY filenumber DESC LIMIT 1;")
query_results = cur.fetchall()

if not query_results:
    a = -1
else:
    a = int(str(query_results[0][0]))


#assigns filenumbers to each photo
a = a + 1
for photo in photos:
    photo.insert(0, a)
    a = a + 1

#saves new downloaded image files (named by filenumber) on local host
for photo in photos:
    response = requests.get(photo[1], stream=True)
    filename = 'your_directory/your_photo_folder/'+str(photo[0])+'.'+str(photo[1].split('.')[-1])
    filename = filename.split("?")[0]
    if filename.split('.')[-1] != 'webm' and filename.split('.')[-1] != 'gifv':
        try:
            with open(filename, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            del response
        except:
            pass
    else:
        pass

#create folder (called small_images) with smaller versions of new image files on local host & remove full size images
destdir = 'your_directory/your_photo_folder/'
files = [ f for f in os.listdir(destdir) if os.path.isfile(os.path.join(destdir,f)) ]
fileList = os.listdir(destdir)

from PIL import Image
for f in files[:]:
    try:
        basewidth = 300
        img = Image.open(destdir+'/'+str(f)).convert('RGB')
        wpercent = (basewidth/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        img = img.resize((basewidth,hsize), PIL.Image.ANTIALIAS)
        img.save('your_directory/'+'/small_images/'+str(f))
    except:
        pass    
    files.remove(f)

for filename in fileList:
    item = os.path.join(destdir,filename)
    if os.path.isfile(item):
        os.remove(item)


#upload photo information to SQL DB on local host
for photo in photos:
    filename = str(photo[0])+'.'+str(photo[1].split('.')[-1])
    filename = filename.split("?")[0]
    filenumber = photo[0]
    filetitle = photo[2]
    filescore = photo[3]
    #print filename, filenumber, filetitle, filescore
    
    if filename.split('.')[-1] != 'webm' and filename.split('.')[-1] != 'gifv':
        try:
            db = mdb.connect(user="root", host="your_host", db="your_db", charset='utf8')
            cur = db.cursor()
            cur.execute("INSERT INTO your_table (filename, filenumber, filetitle, filescore) VALUES (%s, %s, %s, %s);", (filename, filenumber, filetitle, filescore) )
            query_results = db.commit()
        except:
            pass

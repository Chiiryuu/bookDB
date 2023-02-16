import urllib3
import json
import re
import sqlite3
import html


simpleHdr = {'User-Agent' : "Magic Browser"}

http = urllib3.PoolManager()
db = sqlite3.connect('bookDB.db')
print("Opened database successfully")

def makeDB():
    db.execute('''CREATE TABLE Books 
        (ISBN INT PRIMARY KEY     NOT NULL,
         Title        TEXT    NOT NULL,
         Volume       TEXT    NOT NULL,
         Author       TEXT,
         Date         TEXT);''')
    print("Table created successfully!")
    
    
def addEntry(isbn, title, volume, author, date):
    db.execute("INSERT INTO Books VALUES ("+isbn+", '"+title+"', '"+volume+"', '"+author+"', '"+date+"')")
    db.commit()

def getStringFromURL(url):
    rawResult = http.request("GET", url, headers=simpleHdr)
    return rawResult.data.decode('utf-8')

def removeDuplicateSpaces(input):
    return re.sub(' +', ' ', input).strip()

def checkKeyExists(key):
    result = db.execute('SELECT * FROM Books WHERE ISBN = '+key).fetchone()
    return(result!=None)
    #for row in db.execute('SELECT * FROM Books WHERE ISBN = '+key):
        #print(row)
    
def decodeHTMLEscapes(text):
    return html.unescape(text)

def getVolumeFromTitle(title):
    volume = re.search('(?:Vol\. )([0123456789]*)',title)
    
    if (volume != None):
        volume = volume.group(1)
        title = re.sub('(?:Vol\. )([0123456789]*)', '', title)
    else:
        volume = re.search('(?:Volume )([0123456789]*)',title)
        if (volume != None):
            volume = volume.group(1)
            title = re.sub('(?:Volume )([0123456789]*)', '', title)
        else:
            volume = re.search('([0123456789]+)$',title)
            if (volume != None):
                volume = volume.group(1)
                title = re.sub('([0123456789]+)$', '', title)
            else:
                volume = "1"
                print("No volume found!")
    return (title,volume)


def lookupByBarcode(code):
    
    if checkKeyExists(code):
        print("Already Exists!")
        return tuple(db.execute('SELECT * FROM Books WHERE ISBN = '+code).fetchone())
    
    
    result = getStringFromURL("https://bookscouter.com/book/"+code)
    result = decodeHTMLEscapes(result)
    #print(result)
    try:
        match = re.search('(?:<h2 class="book__title flex-child__100")((.|\n)*)?(?:<div class="book__details--basic flex-child__fill">)', result).group(1)
    except:
        print("Error locating book information in result.")
        return
        
    #print("MATCH:\n"+match)
    try:
        title = re.search('(?:>)((.)*)?(?:<\/h2>)',match).group(1)
        #print(title)
    except:
        print("Error locating title in result.")
        return
        
    
    title = re.sub('&#(\d)*;', ' ', title)
    title = re.sub('\(.*\)', '', title)
    
    
    title,volume = getVolumeFromTitle(title)
    
    try:
        author = re.search('(?:<strong class="book__label">Author:<\/strong><span class="book__text">)((.)*)?(?:<\/span>)',match).group(1)
    except:
        print("Error locating author in result.")
        return
    
    try:
        published = re.search('(?:<strong class="book__label">Published:</strong><span class="book__text">)((.)*)?(?:<\/span>)',match).group(1)
    except:
        print("Error locating publishing date in result.")
        return
    
    #title = re.sub(r'[^\s\w+]', '', title)
    
    title  = removeDuplicateSpaces(title)
    
    volume  = removeDuplicateSpaces(volume)
    
    author  = removeDuplicateSpaces(author)
    
    published  = removeDuplicateSpaces(published)
    
    #print("RESULT:\n"+title+" Volume "+volume+", by "+author+"\nPublished "+published)
    print(title)
    print("Vol. "+volume)
    print(author)
    print(published)
    return (code, title, volume, author, published)
    


#makeDB();        

    
#print(json.loads(r.data.decode('utf-8')))

#lookupByBarcode("9781935934127")

add = True

print("Entering DB Add Mode. Enter invalid value to continue.")
while add:
    isbn = input("Please scan your book...")
    if (re.search('(\\d+)',isbn) != None):
        book = lookupByBarcode(isbn)
        print(book)
        if (book != None):
            if (checkKeyExists(str(book[0]))):
                print("Book is already in database!")
            else:
                addEntry(book[0],book[1],book[2],book[3],book[4])
        else:
            print("Invalid or unknown ISBN given.")
    else:
        print("Invalid value given, Exiting loop.")
        add = False
    
db.close()
# program exit
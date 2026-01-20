'''
File name: SurveyDataProcessingV1.py
Purpose: This script takes in the photos for survey entries and outputs a file with GPS data
    in columns with survey ids and file names.
Created by: Alton Hipps
Last Modified: 01/20/2026

Need yet:

'''

#Importing required modules
# Install from here: https://gdal.org/en/stable/download.html
from osgeo import ogr,gdal
#Install from here: https://pillow.readthedocs.io/en/stable/
from PIL import Image,ExifTags
from PIL.ExifTags import TAGS
#Install from here: https://beautiful-soup-4.readthedocs.io/en/latest/#installing-beautiful-soup
from bs4 import BeautifulSoup
# Install from here: https://github.com/tkrajina/gpxpy?tab=readme-ov-file
import gpxpy
# Install Garmin Fit SDK: https://developer.garmin.com/fit/download/
from garmin_fit_sdk import Decoder, Stream
# included in default python install
import os
import math
from datetime import datetime,timedelta

# Create class for image info
class Photo:
    allPhotos=[]
    def __init__(self,lat,lon,file,recordID,photo,fullPath):
        self.lat = lat
        self.lon = lon
        self.file=file
        self.recordID=recordID
        self.photo=photo
        self.fullPath=fullPath
        self.coords=(lat,lon)
        # Add to list of all photos
        self.snapCoords=None
        Photo.allPhotos.append(self)

    def __str__(self):
        if self.snapCoords == None:
            return f'{self.photo}\n\t{str(self.lat)}\n\t{str(self.lon)}\n\t{self.file}\n\t{self.recordID}'
        else:
            return f'{self.photo}\n\tRectified: {str(self.snapLat)}\n\tRectified: {str(self.snapLon)}\n\t{self.file}\n\t{self.recordID}'
    
    def snapPoint(self,latLonTup):
        self.snapLat=latLonTup[0]
        self.snapLon=latLonTup[1]
        self.snapCoords=latLonTup
        return True

    @classmethod
    def matchAndSnap(cls,matchTup,snapTup):
        for photo in cls.allPhotos:
            if photo.coords==matchTup:
                photo.snapPoint(snapTup)
                #print('Match!!!')
                return True
        #print('No Match Found')
        return False

# Create class for questionnaire answers
class Entry:
    instance_order=[]
    inst_counter=1

    def __init__(self,recordID,instanceID,photo,imageDescript,personRank,personText,dogRank,dogText,walkRank,walkText):
        self.recordID=recordID
        self.instanceID=instanceID
        self.photo=photo
        self.imageDescript=imageDescript
        self.personRank=personRank
        self.personText=personText
        self.dogRank=dogRank
        self.dogText=dogText
        self.walkRank=walkRank
        self.walkText=walkText
        self.inst_count=Entry.inst_counter
        Entry.inst_counter+=1
        self.instance_order.append(instanceID)
    def __str__(self):
        return f'{self.recordID}\t{self.instanceID}\t{self.photo}'
    
    def get_instanceOrder(self):
        return self.instance_order

# Create class to combine the info from the two tables
class EntryPhotoCombo:
    def __init__(self,photoObj,entryObj):
        self.recordID=entryObj.recordID
        self.instanceID=entryObj.instanceID
        self.photo=entryObj.photo
        self.imageDescript=entryObj.imageDescript
        self.personRank=entryObj.personRank
        self.personText=entryObj.personText
        self.dogRank=entryObj.dogRank
        self.dogText=entryObj.dogText
        self.walkRank=entryObj.walkRank
        self.walkText=entryObj.walkText        
        self.file= photoObj.file
        self.fullPath=photoObj.fullPath
        # Create blank to fill later
        self.newPath=''
        self.photoObj=photoObj
        # Check if rectified and use if so
        self.lat = photoObj.lat
        self.lon = photoObj.lon
        self.coords=(photoObj.lat,photoObj.lon)

    def __str__(self):
        return f'{self.photo}\t({self.lat},{self.lon})\t{self.instanceID}'

    def selfRectify(self):
        if self.photoObj.snapCoords==None:
            #print('No Photo Obj found to rectify with')
            pass
        else:
            #print(f'{self.lat}\t{self.photoObj.snapCoords[1]}\n{self.lon}\t{self.photoObj.snapCoords[0]}\n{self.coords}\t{self.photoObj.snapCoords}\n')
            self.lat=self.photoObj.snapCoords[1]
            self.lon=self.photoObj.snapCoords[0]
            self.coords=self.photoObj.snapCoords

class Track:
    recordIdList=[]

    def __init__(self,recordID):
        self.recordID=recordID
        self.points=[]
        self.coords=[]
        self.recordIdList.append(recordID)

    def addPoint(self,EntryPhotoComboObj,message=0):
        self.points.append(EntryPhotoComboObj)
        self.coords.append(EntryPhotoComboObj.coords)
        if message==1: print(f'Point Add\t {str(len(self.points))} points total on {self.recordID})')

    def __str__(self):
        return f'{self.recordID}\t{self.points}'

    def pointCount(self):
        return str(len(self.points))
    
    def instIDfromCoords(self,coordTup):
        for i in range(len(self.points)):
            if coordTup[0]==self.points[i].coords[0] and coordTup[1]==self.points[i].coords[1]:
                print(f'\t{coordTup[0]},{coordTup[1]}\n\t{self.points[i].coords[0]},{self.points[i].coords[1]}')
                return self.points[i].instanceID
            i+=1
        print('No matching point found')
        return False

    # create method to generate list of necessary fields in format for csv
    def listForFile(self,listOfProperties,separator,newLineChar='\n',printMessage=0): 
        outList=[]
        counter=1
        for point in self.points:
            outStr=''
            for prop in listOfProperties:
                cleaned=str(prop).strip().lower()
                if cleaned=='recordid':newValue=self.recordID
                elif cleaned=='lat':
                    point.selfRectify()
                    newValue=str(point.lon)
                elif cleaned=='lon':
                    point.selfRectify()
                    newValue=str(point.lat)
                elif cleaned=='photo':newValue=point.photo
                elif cleaned=='stopid':newValue=point.instanceID
                elif cleaned=='stopnumber':newValue=f'Stop #{str(counter)}'
                elif cleaned=='imagedescript':newValue=point.imageDescript
                elif cleaned=='personrank':newValue=point.personRank
                elif cleaned=='persontext':newValue=point.personText
                elif cleaned=='dogrank':newValue=point.dogRank
                elif cleaned=='dogtext':newValue=point.dogText
                elif cleaned=='walkrank':newValue=point.walkRank
                elif cleaned=='walktext':newValue=point.walkText
                elif cleaned=='newpath':newValue=point.newPath[1:].replace('\\','/')
                elif cleaned=='id':newValue=f'{str(counter)}'
                if newValue[:-1]!=newValue[0:]:newValue=newValue
                outStr+='"'+newValue.strip().replace('"',"'")+'"'
                outStr+=separator
            counter+=1
            outStr=outStr[:-1]+newLineChar
            outList.append(outStr)
        if printMessage==1:print(f'Completed output for track {self.recordID} with {counter-1} points')
        return outList

# Define class for timing
class Timer:
    allTimings=[]
    checkpoints={}
    lastCheckpoint=''

    def __init__(self):
        self.time=datetime.now()
        self.allTimings.append(self.time)
        print('Timer initiated')
    
    def mark(self,checkpointName='',printMessage=False):
        if self.lastCheckpoint=='': 
            lastTime='First Time'
        else:
            check=self.checkpoints[self.lastCheckpoint][0]
            totDiff=-(check-datetime.now())
            comboTime=totDiff.seconds+round(totDiff.microseconds/1000000,4)
            if comboTime<0.01:
                comboTime='<0.01'
            lastTime=str(comboTime)+' seconds'
        if printMessage==True: 
            print(f'{lastTime}\t| Checkpoint Added')
        self.checkpoints[checkpointName]=(datetime.now(),lastTime)
        self.lastCheckpoint=checkpointName
        return f'{datetime.now}\t| Checkpoint Added'
    
    def getCheckpoints(self):
        return self.checkpoints

    def printCheckpoints(self):
        print('Checkpoint Name\t\tTime\t\t\t\tElapsed Time')
        for checkpointKey in list(self.checkpoints.keys()):
            timings=self.checkpoints[checkpointKey]
            if len(checkpointKey)<8:
                print(f'{checkpointKey}\t\t\t{timings[0]}\t{timings[1]}')
            elif len(checkpointKey)<16:
                print(f'{checkpointKey}\t\t{timings[0]}\t{timings[1]}')
            elif len(checkpointKey)<24:
                print(f'{checkpointKey}\t{timings[0]}\t{timings[1]}')
            else:
                print(f'{checkpointKey[:24]}{timings[0]}\t{timings[1]}')
        print(f'Total Time\t\t\t\t\t\t{(datetime.now()-self.time).seconds + round((datetime.now()-self.time).microseconds/1000000,4)} seconds')
        return True

class FitReading:
    def __init__(self,msgDict):
        self.lat=msgDict['position_lat']/11930465 
        self.lon=msgDict['position_long']/11930465
        self.heartrate=msgDict['heart_rate']
        self.timestamp=msgDict['timestamp']
        self.encoded_lat=msgDict['position_lat']
        self.encoded_lon=msgDict['position_long']
        self.recordID=''
        self.pointID=''

    def __str__(self):
        if len(self.recordID)>0 and len(str(self.pointID))>0: # all fields filled
            outString=f'{self.lat},{self.lon}\t{self.heartrate}\t{self.timestamp}\t{self.recordID}\t{self.pointID}\t{self.type}'
        elif len(self.recordID)<0 and len(str(self.pointID))>0: # pointID but no recordID
            outString=f'{self.lat},{self.lon}\t{self.heartrate}\t{self.timestamp}\t{self.pointID}'
        elif len(self.recordID)>0 and len(str(self.pointID))<0: # recordID but no pointID
            outString=f'{self.lat},{self.lon}\t{self.heartrate}\t{self.timestamp}\t{self.recordID}'
        else: # neither/catchall
            outString=f'{self.lat},{self.lon}\t{self.heartrate}\t{self.timestamp}'
        return outString 

    def get_hr(self):
        return self.heartrate

    def setType(self,participantType):
        self.type=participantType

    def setID(self,ID):
        self.pointID=ID
    
    def addRecordID(self,recID):
        self.recordID=recID

    def classify(self,inTup): # inTup will be (class value, index of class value)
        self.classification=inTup[0]
        self.classIndex=inTup[1]

# Define function to switch from degrees minutes seconds to decimal degrees
def DMS_to_Decimal(inputTuple,sign):
    return sign*(float(inputTuple[0])+float(inputTuple[1])/60+float(inputTuple[2])/3600)

# Define function to define slash for file paths
def slash():
    if os.name=='nt':
        slash="\\"
    else:
        slash="/"
    return slash

def likertTextToNumber(inputText,likertDict):
    outputNum=likertDict[inputText]
    return str(outputNum)

# Define access module
def accessGPS_IFD(path):

    # Access the image
    im = Image.open(path)
    exif = im.getexif()
    gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)

    # Account for north south 
    if gps_ifd[1].upper()=='S':
        northSouth=-1
    else:
        northSouth=1
        
    # Account for east west
    if gps_ifd[3].upper()=='W':
        eastWest=-1
    else:
        eastWest=1

    # Convert to decimal degrees
    lat = round(DMS_to_Decimal(gps_ifd[2],northSouth),8)
    lon = round(DMS_to_Decimal(gps_ifd[4],eastWest),8)
    
    # Identify end file name
    fileNameBuild=''
    for char in path[::-1]:
        if char!=slash():
            fileNameBuild+=char
            continue
        else:
            break
 
    # Flip file name and separate out photo name from record ID
    fileName=path[len(path)-len(fileNameBuild):]
    findIMG=fileName.find('IMG')
    reportID=fileName[:findIMG-1]
    justPhoto=fileName[findIMG:]
    im=None
    # Return lat lon and file name
    return (lat,lon,fileName,reportID,justPhoto,path)

# Define function to leaf through file structure from photo export
def findDirectories(rep):
    outList=[]
    for folder in os.listdir(rep):
        if '.' not in folder:
            for photo in os.listdir(rep+slash()+folder):
                outList.append(rep+slash()+folder+slash()+photo)
    return outList

# Define function to find questionnaire tsv file
def findTSV(dataPath,printMessage=0):
    for item in os.listdir(dataPath):
        if item[-3:]=='tsv' or item[-3:]=='TSV':
            if printMessage==1:print(f'Located {item} as questionnaire')
            return item
        else:
            continue
    print('TSV of questionnaire data not found')
    return True

# Define function to find files
def findFiles(directory,lastThree):
    outList=[]
    for file in os.listdir(directory):
        if file[-3:].lower()==lastThree:
            outList.append(directory+slash()+file)
    if len(outList)<1:
        print(f'No {lastThree} files located.')
        return False
    else:
        return outList # returns list of file names

# Define function to read GPX files
def readGPX(listOfGPXfiles,printMode=0):
    filenum=1
    outDict={}
    gdal.UseExceptions()
    for file in listOfGPXfiles:
        if printMode==1:print(f'File #{str(filenum)} - {file}')
        filenum+=1
        gpx_file = open(file, 'r')
        gpx = gpxpy.parse(gpx_file)
        tracknum=1
        for track in gpx.tracks:
            if printMode==1:print('Track #'+str(tracknum))
            tracknum+=1
            segnum=1
            for segment in track.segments:
                if printMode==1:print('Segment #'+str(segnum))
                segnum+=1
                pointnum=1
                line = ogr.Geometry(ogr.wkbLineString)
                for point in segment.points:
                    if printMode==1:print(f'Point #{pointnum} at ({point.latitude},{point.longitude}) -> {point.elevation}')
                    line.AddPoint(point.latitude,point.longitude)
        outDict[file[10:-4]]=line # Testing without .ExportToJson()
        gpx = None
    return outDict


def createJSONs(GPXDict,listOfTracks,decoder,outPath,message=False):
    IDList=Track.recordIdList
    counter=1

    # Loop through all record IDs
    for ID in IDList:
        # Decode file name with decoder table
        fileName=decoder[ID]
        # Set first track as a human track
        routeType='human_GPS'

        # loop through each item in the decoder 
        for item in fileName:

            # Set first id number to one on each segment
            idval=1 

            # get line ojb from GPX track for correct file
            lineObj=GPXDict[item]

            # Create the output Driver
            outDriver = ogr.GetDriverByName('GeoJSON')

            # Create the output GeoJSON
            outDataSource = outDriver.CreateDataSource(f'{outPath}{slash()}{ID}{slash()}{ID}_{routeType[:-4]}_GPX.geojson')

            outLayer = outDataSource.CreateLayer(f'{routeType}', geom_type=ogr.wkbLineString )

            # Create id field in properties
            field_id = ogr.FieldDefn("id", ogr.OFTInteger)
            field_id.SetWidth(24)
            outLayer.CreateField(field_id)

            # Get the output Layer's Feature Definition
            featureDefn = outLayer.GetLayerDefn()
            
            # loop through tracks (should be 2)
            for track in listOfTracks:
                if track.recordID==ID: # If record ID matches ID, i.e. just pull the track obj for the proper 
                    
                    # Create list of coords from the track obj
                    coordsList=track.coords
                    if routeType=='dog_GPS': 
                        coordsList=dogCopy
                    else:
                        dogCopy=coordsList[:]

                    if message==True:print(f'New Track: {ID} with {len(coordsList)} entries')
                    
                    # intitalize variables for search
                    factor=.00001
                    containsTest=False
                    trackMatch=[]
                    firstPoint=None

                    # loop for each coordinate in the list from the track
                    while len(coordsList)>0:

                        # loop through each coordinate from the track
                        for coord in coordsList:
                            # intialize the segment list
                            segList=[]#firstPoint]

                            # Create a point object from the coords
                            point = ogr.Geometry(ogr.wkbPoint)
                            point.AddPoint(coord[0],coord[1])

                            # Buffer the photo point by a defined amount
                            pbuff=point.Buffer(factor)

                            # loop through points from the GPX file IDed earlier
                            for i in range(len(lineObj.GetPoints())):

                                # Create a OGR point object
                                testPoint=ogr.Geometry(ogr.wkbPoint)
                                testPoint.AddPoint(lineObj.GetPoint(i)[0],lineObj.GetPoint(i)[1])

                                # Add the point to a list for this segment
                                segList.append((lineObj.GetPoint(i)[0],lineObj.GetPoint(i)[1]))

                                # Check if the GPX point is within the buffer of the photo point
                                containsTest=pbuff.Contains(testPoint) # returns Bool

                                # If the point is within the buffer:
                                if containsTest==True:
                                    if message==True:
                                        print(f'Match #{counter}: {factor} | {coord} | {testPoint}')
                                        counter+=1
                                        print(f'{track.recordID} | {track.instIDfromCoords(coord)}')
                                    
                                    # Add a copy of the segment coordinates in to the track segments list
                                    trackMatch.append(segList[:])

                                    # Set up the first point of the next segment
                                    firstPoint=coord
                                    
                                    # Take this point out of the list
                                    coordsList.remove(coord)

                                    # Record to snap photo to point
                                    Photo.matchAndSnap((coord[0],coord[1]),(lineObj.GetPoint(i)[0],lineObj.GetPoint(i)[1]))

                                    # Get out of the GPX coordinates loop
                                    break

                            # Make the next buffer bigger
                            factor+=.0001
                            factor=round(factor,4)
                
                    # loop through segements in this track list
                    for segment in trackMatch:
                        
                        # Create linesting Geometry
                        coordCount=1
                        segLine=ogr.Geometry(ogr.wkbLineString)

                        # Loop through each coordinate pair and add to the segment LineString
                        for coordPair in segment:
                            
                            # Handle first segment's first point
                            if coordPair==None:continue

                            # Add points to lineString
                            segLine.AddPoint(coordPair[1],coordPair[0])

                            coordCount+=1

                        # create a new feature
                        outFeature = ogr.Feature(featureDefn)
                        outFeature.SetField('id',idval)

                        # Set new geometry
                        outFeature.SetGeometry(segLine)

                        # Add new feature to output Layer
                        outLayer.CreateFeature(outFeature)
                        
                        # Iterate up the ID number for the next feature
                        idval+=1

            # Save and close DataSources
            outFeature = None
            outDataSource = None

            # Set up for dog route run
            routeType='dog_GPS'

# Define function to take geography from photo path and save to file
def photoGPSinfo_toList(listOfGPSTuples):
    outList=[]
    for GPSTuple in listOfGPSTuples:
        pic=Photo(GPSTuple[0],GPSTuple[1],GPSTuple[2],GPSTuple[3],GPSTuple[4],GPSTuple[5])
        outList.append(pic)
    return outList
        
# Read questionnaire
def readQuestionnaire(path,likertDict):
    listOfEntries=[]

    # Reading Questionnaire
    with open(path,mode='r',encoding='utf-16') as file:
        rowCount=0
        
        # For each row,
        for row in file:
            if rowCount < 3: # Skip header rows
                rowCount+=1
                continue

            # Create list from row
            rowList=row.split('\t')

            stopNum=0
            record=''
            detailList=[]
            nextSeven=0
            inc_id=''
            photoString=''
            skipBeginning=True

            # Iterate column by column
            for item in rowList:
                item=item.strip()
                
                # Skip empty cells
                if len(item)<1:
                    continue

                # identify columns containing the Respondant ID
                if item[:2]=='R_':
                    stopNum+=1
                    record=item[:]
                    continue

                # ID column with Field ID
                if item[:2]=='F_':
                    inc_id=item[:]
                    skipBeginning=False
                    continue

                # Id field with photo file name
                if item[-3:]=="png" or item[-4:]=="jpeg":
                    if item!='image/jpeg':
                        photoString=item[:]
                        #print(photoString)
                        nextSeven=0
                    continue
                # loop through rankings and text questions
                if nextSeven<8:
                    if nextSeven<1:
                        nextSeven+=1
                        continue
                    if skipBeginning==True:
                        continue
                    detailList.append(item)
                    nextSeven+=1
                    continue
                # Create Entry OBj and add to list
                if len(detailList)>6:
                    entryObj=Entry(record, #Record ID
                      inc_id, # Instance ID
                      photoString, # Photo Path
                      detailList[0], # Image Description
                      likertTextToNumber(detailList[1],likertDict), # Person Rank
                      detailList[2], # Person Text
                      likertTextToNumber(detailList[3],likertDict),# Dog Rank
                      detailList[4], # Dog Text
                      likertTextToNumber(detailList[5],likertDict), # Walk Rank
                      detailList[6] # Walk Text
                      )
                    #print('Created Entry\t'+str(entryObj))
                    listOfEntries.append(entryObj)
                    detailList=[]  
    return listOfEntries

# Define function to create class of combined photo and survey data
def createComboObjs(listPhotoObjs,listEntryObjs):
    outList=[]
    shortList=[]
    for obj in listPhotoObjs:
        searchFile=obj.photo
        for entry in listEntryObjs:
            if entry.photo==searchFile:
                combo=EntryPhotoCombo(obj,entry)
                shortList.append(combo)
    for ID in listEntryObjs[0].get_instanceOrder():
        for combo in shortList:
            if ID==combo.instanceID:
                outList.append(combo)
    return outList

# Define function to create Track objs
def createTracks(listOfCombos):
    outList=[]
    trackList=[]
    for combo in listOfCombos:
        if len(outList)<1: # Always create track for first obj
            track1=Track(combo.recordID)
            track1.addPoint(combo)
            outList.append(track1)
            trackList.append(track1.recordID)
            continue
        cID=combo.recordID
        if cID not in trackList:
            newTrack=Track(combo.recordID)
            newTrack.addPoint(combo)
            outList.append(newTrack)
            trackList.append(newTrack.recordID)
            continue
        index=0
        for recID in trackList:
            if cID!=recID:
                index+=1
                continue
            track=outList[index]
            track.addPoint(combo)   
    return outList # Return list of track objs

# Define function to take geography from photo path and save to file
def tracks_toCSV(listOfTracks,headers,outPath):
    listOfTrackStrings=[]
    #numTracks=len(listOfTracks)
    for track in listOfTracks:
        recordID=track.recordID
        trackStringList=track.listForFile(headers,',')
        listOfTrackStrings.extend(trackStringList)
        actualPath=f'{outPath}{slash()}{recordID}{slash()}{recordID}.csv'
        csv=open(actualPath,'w')
        rowString=''
        for i in range(len(headers)):
            rowString+=str(headers[i])+','
        csv.write(rowString[:-1]+'\n')
        length=len(listOfTrackStrings)
        counter=1
        for trackStr in listOfTrackStrings:
            if recordID in trackStr:
                if counter!=length:
                    csv.write(trackStr)
                else:
                    csv.write(trackStr[:-1])
            counter+=1 
        csv.close()
    return True

# Create new subdirectories for each track
def createDirectFromTracks(listOfTracks,printMessages=0):
    for track in listOfTracks:
        recordID=track.recordID
        allFolders=('img','assets')
        for x in allFolders:
            newpath=f'.{slash()}{x}{slash()}{recordID}'
            if not os.path.exists(newpath):
                os.makedirs(newpath)
                if printMessages==1:print(f'Created {newpath}')
            else:
                if printMessages==1:print(f'{newpath} already exists')
    return True

# Function to move images into a place where they can be accessed by the site
def moveImagesFromTracks(listOfTracks,printMessages=0):
    if printMessages==1:trackingDict={'okay':0,'resized':0,'moved':0,'tracks':0}
    for track in listOfTracks: # Access each track
        entries=track.points
        recordID=track.recordID
        if printMessages==1:trackingDict['tracks']+=1
        for entry in entries: # Access each EntryPhotoComboObj
            fullPath=entry.fullPath
            photo=entry.photo
            if printMessages==1:print(fullPath)
            image=Image.open(fullPath) # open the image and get size
            Xsize,Ysize=image.size
            exif=image.getexif()
            for k, v in exif.items():
                if TAGS[k] == 'Orientation': 
                    if v == 3:
                        rotator=180
                    elif v == 6:
                        rotator=270
                    else:
                        rotator=0
            if printMessages==1:trackingDict['okay']+=1
            if Xsize>1000 or Ysize>1000: # resize if over 1000 pixels in any direction
                ratio=Xsize/Ysize
                if printMessages==1:print(f'\tPhoto too big ({Xsize},{Ysize}) with ratio {round(ratio,4)}')
                if rotator==180: # landscape
                    image=image.rotate(rotator)
                    newSize=(1000,int(round(1000/ratio,0)))
                    if printMessages==1:print(f'\tNew size: {newSize}\tratio {round(newSize[0]/newSize[1],4)}')
                else: # Portrait mode
                    image=image.rotate(rotator,expand=True)
                    newSize=(1000,int(round(1000/(1/ratio),0)))
                    if printMessages==1:print(f'New size: {newSize}\tratio {round(newSize[0]/newSize[1],4)}')
                smallPhoto = image.resize(newSize,1) # Resizes image

                if printMessages==1:trackingDict['resized']+=1
                if printMessages==1:trackingDict['okay']-=1

            data = list(smallPhoto.getdata())
            image_without_exif = Image.new(smallPhoto.mode, smallPhoto.size)
            image_without_exif.putdata(data)
            newPath=f'.{slash()}img{slash()}{recordID}{slash()}{photo}'
            image_without_exif.save(newPath)
            # Assign new photo to object
            entry.newPath=newPath
            if printMessages==1:print(f'\tSmall Photo Saved to .{slash()}img{slash()}{recordID}{slash()}{photo}')
            image.close()
            smallPhoto.close()
            image_without_exif.close()
            if printMessages==1:trackingDict['moved']+=1
    if printMessages==1:print(f'\t{trackingDict["moved"]} photos moved\t{trackingDict["resized"]} photos resized\t{trackingDict["okay"]} photos okay size\t{trackingDict["tracks"]} tracks accessed.')
    return True

# Define function to copy html file
def copyHTMLpage(toCopy,copyLoc,listOfTracks):
    for track in listOfTracks:
        recordID=track.recordID
        outFile=copyLoc+slash()+recordID+'.html'
        toWrite=open(outFile,'w')
        with open(toCopy,'r') as toRead:
            soup = BeautifulSoup(toRead,features="html.parser")
            soup.title.string=f'{recordID}'
            toWrite.write(soup.prettify(formatter="html"))
        toWrite.close()
    return True

# Read .fit files 
def readFit(listOfFiles):
    outDict={}
    for fitFile in listOfFiles:
        stream = Stream.from_file(fitFile)
        decoder = Decoder(stream)
        messages, errors = decoder.read()
        if len(errors)==0:
            outDict[fitFile]=messages
        else:
            print(f'ERROR:\t{fitFile} : {errors}')
    return outDict


# Process fit files
def getMessages(dictOfDicts,stemLen=0,printMessage=0):
    i=1
    outDict={}
    #no_heartrate=[]
    for key in list(dictOfDicts.keys()):
        if printMessage==1:print(f'Counter: {i}\tKey:{key}')
        messageDict=dictOfDicts[key]
        recordMsgs=[]
        counter=1
        for sec_key in list(messageDict.keys()):
            if sec_key == 'record_mesgs':
                for individualDict in messageDict[sec_key]:
                    if len(list(individualDict.keys()))<14:
                        #print(f'\tLess than 14 {len(list(individualDict.keys()))}')
                        #if 'heart_rate' not in list(individualDict.keys()):
                        #    individualDict['heart_rate']='No data'
                        #no_heartrate.append(FitReading(individualDict))
                        continue
                    else:
                        fitObj=FitReading(individualDict)
                        fitObj.setID(counter)
                    recordMsgs.append(fitObj)
                    counter+=1
        quickCopy=recordMsgs[:]
        shortKey=key[stemLen:]
        #print(shortKey)
        outDict[shortKey]=quickCopy
        i+=1
    return outDict

# Function to create segments from heartrate objs
def segmentize(fitDict,IDMap,HumanOrDog):
    inverseMap={}
    inverseHumanDog={}
    outDict={}
    keyList=list(fitDict.keys())

    for ID in IDMap:
        for fileName in IDMap[ID]:
            inverseMap[fileName]=ID
    #print(inverseMap)
    for ID in HumanOrDog:
        for fileName in HumanOrDog[ID]:
            inverseHumanDog[fileName]=ID

    #print(inverseHumanDog)

    maxDict={}
    maxOutList=[]
    for item in range(len(keyList)):
        #print(keyList[item])
        counter=0
        minhr=500
        maxhr=0
        maxHrObjID=''
        matchName=keyList[item][:-4]
        fitObjs=fitDict[keyList[item]]
        recID=inverseMap[matchName]
        participantType=inverseHumanDog[matchName]
        smallList=[]
        for obj in fitObjs:
            obj.addRecordID(recID)
            obj.setType(participantType)
            counter+=1
            #obj.setID(counter)
            objhr=obj.heartrate
            if minhr>objhr:
                minhr=objhr
            if maxhr<objhr:
                maxhr=objhr
                maxHrObjID=obj.pointID
            smallList.append(obj)

        maxDict[f'{obj.recordID}_{obj.type}']=maxHrObjID

        minclass=math.floor(minhr/10)*10
        maxclass=math.ceil(maxhr/10)*10
        numOfClasses=(maxclass-minclass)/10
        classFloors=[]
        classifySummaryDict={}
        for i in range(int(numOfClasses)):
            nextClass=minclass+10*i
            classFloors.append(nextClass)
            classifySummaryDict[nextClass]=0
        classFloors.append(nextClass+10)
        classifySummaryDict[nextClass+10]=0

        for obj in fitObjs:
            hrtRound=round(int(obj.heartrate)/10)*10
            for classFloor in classFloors:
                if classFloor != hrtRound:
                    continue
                else:
                    index=classFloors.index(classFloor)
                    obj.classify((classFloor,index))
                    classifySummaryDict[classFloor]=classifySummaryDict[classFloor]+1

        heartrateBefore=0
        segNum=1

        totalSegList=[]
        segList=[]

        for obj in fitObjs:
            if obj.pointID == maxDict[f'{obj.recordID}_{obj.type}']:
                obj.maxHRT=True
                maxOut=(obj.pointID,obj.lon,obj.lat,obj.heartrate,obj.timestamp)
                maxOutList.append(maxOut)
                #print(obj.pointID,obj.heartrate)
            else:
                obj.maxHRT=False
            
            if obj.classification != heartrateBefore:
                #print(f'New Segment #{segNum}\t{obj.classification}\t{pID}')
                heartrateBefore=obj.classification
                listCopy=segList[:]
                if len(listCopy)>0:
                    totalSegList.append(listCopy)
                    segNum+=1
                    listCopy=[]
                segList=[]
            else:
                segList.append(obj)
        #stats=(minhr,maxhr,counter,minclass,maxclass,classifySummaryDict,len(totalSegList))
        #print(stats)
        outDict[totalSegList[0][0].recordID+'_'+totalSegList[0][0].type]=totalSegList[:]
    #print(outDict)
    return outDict,maxOutList

# Function to create a JSON file for heartrate data
def createFitJSONs(fitDict,filePrefix):

    for segLists in fitDict:

        recID=str(fitDict[segLists][0][0].recordID)
        particType=fitDict[segLists][0][0].type

        if 'Dog' in particType:
            outFileName=filePrefix+slash()+recID+slash()+recID+'_dog_fit.geojson'
        else:
            outFileName=filePrefix+slash()+recID+slash()+recID+'_human_fit.geojson'

        # Get driver for GeoJSON file
        outDriver = ogr.GetDriverByName('GeoJSON')

        # Create the output GeoJSON
        outDataSource = outDriver.CreateDataSource(outFileName)
        outLayer = outDataSource.CreateLayer(outFileName[len(filePrefix)+1+len(recID)+1:-12]+'_hrt', geom_type=ogr.wkbLineString )

        # Create id field in properties
        field_id = ogr.FieldDefn("id", ogr.OFTInteger)
        field_id.SetWidth(24)
        outLayer.CreateField(field_id)

        field_id = ogr.FieldDefn("hrt", ogr.OFTInteger)
        field_id.SetWidth(24)
        outLayer.CreateField(field_id)

        field_id = ogr.FieldDefn("maxHrt", ogr.OFSTBoolean)
        field_id.SetWidth(1)
        outLayer.CreateField(field_id)

        # Get the output Layer's Feature Definition
        featureDefn = outLayer.GetLayerDefn()

        # Loop to create individual segment features
        segCounter=0
        skippedLast=False
        for segList in fitDict[segLists]:
            line = ogr.Geometry(ogr.wkbLineString)

            if skippedLast==True:
                skippedLast=False
                line.AddPoint(catchPoint.lon,catchPoint.lat)

            if segCounter!=0:
                line.AddPoint(lastObjOfLastSeg.lon,lastObjOfLastSeg.lat)
            
            maxBool=0
            for obj in segList:
                lat,lon=obj.lat,obj.lon
                line.AddPoint(lon,lat)  # Proper Order
                lastObjOfLastSeg=obj
                if int(obj.maxHRT)==1:
                    maxBool=1
                    #print(obj,segCounter+1) # prints id of max segement
                else:
                    continue

            if len(line.GetPoints()) == 1:
                #print(f'Skipping Line Seg {segCounter}')
                skippedLast=True
                catchPoint=lastObjOfLastSeg
                continue

            # create a new feature
            outFeature = ogr.Feature(featureDefn)
            outFeature.SetField('id',segCounter+1)
            outFeature.SetField('hrt',obj.classification)
            outFeature.SetField('maxHrt',maxBool)


            # Set new geometry
            outFeature.SetGeometry(line)

            # Add new feature to output Layer
            outLayer.CreateFeature(outFeature)

            # Close Feature
            segCounter+=1
            outFeature = None
            line=None

        outDataSource = None
        #print(outFileName)

    return True

# Constants
rawData=f'.{slash()}rawData'
outAssetsFilePath=f"..{slash()}assets"
outPagesPath=f"..{slash()}pages"
outFields=['recordID','stopID','stopNumber','lat','lon','newPath','imageDescript','personRank','personText',
           'dogRank','dogText','walkRank','walkText','id']
ID_to_GPX={ # This piece is still manual and could be tough with more files. Probably need some kind of naming convention
    'R_1L0xQ5tCBthP53o':('sample_April_crop','sample_pup_Cabot_wApril_crop'),
    'R_1hPUV8wxBmis1gR':('sample_Jonathan_crop','sample_pup_Nittany_wJonathan_crop')
}
ID_to_fit=ID_to_GPX
ID_to_Type={
    'Dog':('sample_pup_Cabot_wApril_crop','sample_pup_Nittany_wJonathan_crop'),
    'Human':('sample_April_crop','sample_Jonathan_crop')
}
likertMap={
    'Extremely positive':5,
    'Somewhat positive':4,
    'Neither positive nor negative':3,
    'Somewhat negative':2,
    'Extremely negative':1,
    'Not Applicable':0,
    'Extremely conducive':5,
    'Somewhat conducive':4,
    'Neither conducive nor inconducive':3,
    'Somewhat inconducive':2,
    'Extremely inconducive':1
}

# Actual processes
ts=Timer()
ts.mark('Start')
photoFileList=findDirectories(rawData)
ts.mark('Found Photos')
GPS_Data_list=[]
for photoPath in photoFileList:
    GPS_Data_list.append(accessGPS_IFD(photoPath))
photoObjs=photoGPSinfo_toList(GPS_Data_list)
ts.mark('Created Photo Objects')
entries=readQuestionnaire(rawData+slash()+findTSV(rawData),likertMap)
combos=createComboObjs(photoObjs,entries)
print(str(len(entries))+' Entries detected')
ts.mark('Created Combo Objects')
trackList=createTracks(combos)
createJSONs(readGPX(findFiles(rawData,'gpx')),trackList,ID_to_GPX,outAssetsFilePath)
ts.mark('Built GPS JSON files')
fitFiles=findFiles(rawData,'fit')
ts.mark('Found Fit Files')
messages=getMessages(readFit(fitFiles),len(rawData)+1)
ts.mark('Retrieved Messages')
segements,maxHRTInfo=segmentize(messages,ID_to_fit,ID_to_Type)
print(maxHRTInfo)
ts.mark('Heartrate Segmented')
createFitJSONs(segements,outAssetsFilePath)
ts.mark('Fit JSONs completed')
trackList=createTracks(combos) # reiterate to snap photos to gps tracks
createDirectFromTracks(trackList)
moveImagesFromTracks(trackList)
ts.mark('Prepared Photos')
# Add entry for max heartRate

#copyHTMLpage(r'./toCopy.html',outPagesPath,trackList)
#ts.addCheckpoint('Built HTML Pages')
tracks_toCSV(trackList,outFields,outAssetsFilePath)
ts.mark('Built CSV files')
ts.printCheckpoints()

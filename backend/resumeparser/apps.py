from django.apps import AppConfig
from pdf2image import convert_from_path
import PIL
from PIL import ImageDraw
from PIL import Image
import os
import json
import re
import cv2
from os import path
import numpy as np
import requests
from math import *
from requests.exceptions import ConnectionError
import img2pdf
import cv2
import numpy as np




class ResumeparserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'resumeparser'

    @staticmethod
    def pdf_to_text(filepath):

        '''
        This function is used to convert the pdf to text. It utilizes another model to get the headings/section of the resume.
        '''
        
        try:
            with open(filepath, 'rb') as fp:
                files = {'resume': fp.read()}
                response = requests.post('http://crmdi-gpu3:8781/get-predictions', files=files)
                predictions = list(response.json()['predictions'].values())
        except FileNotFoundError:
            print("Filepath may be incorrect")
        except ConnectionError:
            print("Predictions server is not online")
        except Exception as e:
            print(e)

        @staticmethod
        def merge_bounding_boxes(boxes):
            boxes = list(filter(lambda x: not (x[0] == x[1] == x[2] == x[3] == 0), boxes))
            if len([box for box in boxes if box is not None]) == 0:
                return [0, 0, 0, 0]
            x_min = min(box[0] for box in boxes if box is not None)
            y_min = min(box[1] for box in boxes if box is not None)
            x_max = max(box[2] for box in boxes if box is not None)
            y_max = max(box[3] for box in boxes if box is not None)
            merged_box = [x_min, y_min, x_max, y_max]
            return merged_box
        
        headings = []
        seq = []
        words = []
        boxes = []
        result = {}
        
        for item in predictions:
            result[item['word']] = item['box']
            label = item['prediction']
            if 'HEADING' not in label:
                continue
            label_tag, label_type = label.split('-')
            if label_tag == 'S':
                headings.append({'text': item['word'], 'box': item['box']})
            elif label_tag == 'B':
                seq = [item['word']]
                boxes = [item['box']]
            elif label_tag == 'I':
                seq.append(item['word'])
                boxes.append(item['box'])
            elif label_tag == 'E':
                seq.append(item['word'])
                boxes.append(item['box'])
                headings.append({'text': ' '.join(seq), 'box': merge_bounding_boxes(boxes)})
                seq = []
                boxes = []
                
        return result,headings
    
    @staticmethod
    def pdf2image(filename):

        '''
        This function is used to convert pdf to image.
        '''
        
        pdf_images = convert_from_path(filename)
        for i in range(len(pdf_images)):
            pdf_images[i].save(str(i+1)+filename[:len(filename)-4]+'.jpg','JPEG')


    ##### CHANGES MADE HERE ###########
    @staticmethod
    def get_slope(coord1, coord2):

        '''
        This function is important as it plays a major role in detecting the layout of the resume
        '''
        
        x2 = coord2[0]
        x1 = coord1[0]
        y2 = coord2[1]
        y1 = coord1[1]
        return ((y2 - y1) / (x2 - x1))
    
    @staticmethod
    def getLayout(filename):

        '''
        This function gives the output based on the slopes.
        It can be either SINGLE or MULTI layout.
        This gives the final layout of the resume.
        '''

        result, headings = ResumeparserConfig.pdf_to_text(filename)
        slopes = []
        for i in headings:
            box1 = i['box']
            for j in headings:
                box2 = j['box']
                try:
                    slope = ResumeparserConfig.get_slope(box1, box2)
                    if slope == 'nan':
                        slopes.append(slope)
                    else:
                        slopes.append(abs(int(slope)))
                except:
                    pass
        
        count = 0
        for i in slopes:
            if i == 0:
                count += 1

        if count <= 3:
            final_layout = "SINGLE"
        else:
            final_layout = "MULTI"
            
        return final_layout,headings,result
    
    @staticmethod
    def multi(filename,headings,result):

        '''
        This function is written for MULTI Layout Resume Use Cases.
        This function is highly compilicated as it solves almost every edge cases.
        Returns the message which can be "SUCCESS" or "FAILED" along with the final coordinates , returns {} if the message is "FAILED"

        '''
        
        pdf_images = convert_from_path(filename)
        for i in range(len(pdf_images)):
            pdf_images[i].save(str(i+1) + 'resume.jpg', 'JPEG')

    #################### INITIAL PREDICTION OF THRESHOLD ############################
        visited = {}
        for i in headings:
            visited[i['text'].lower()] = i['box']

        img = PIL.Image.open('1resume.jpg')
        w, h = img.size

        res = []
        for i in visited:
            res.append(visited[i])

        max_f = -1
        min_h = h

        for i in res:
            min_h = min(min_h, i[1])

        c = 0
        l = []
        for i in res:
            if (i[1] - min_h != 0):
                l.append(i[1])
                c += 1

        if c == 1:
            temp_min_h = w
            for i in res:
                if i[1] == min_h:
                    pass
                else:
                    temp_min_h = min(temp_min_h, i[1])
            min_h = temp_min_h

        count = 0
        
        for i in visited:
            if visited[i][1] == min_h:
                count += 1

        if count == 2:
            
            for i in visited:
                if visited[i][1] == min_h:
                    max_f = max(max_f, visited[i][0])
        else:
            for i in visited:
                if visited[i][1] == min_h:
                    max_f = visited[i][0]
        
    ##################### HORIZONTAL PREDICTION ###############################
        image = cv2.imread("1resume.jpg", 0)
        adaptive_thresh = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 25, 10)
        
        h, w = image.shape

        verti = []
        for i in res:
            if abs(i[0]-max_f) <= 20:   
                verti.append(i[1])
        
        verti = sorted(verti)
        ind = verti.index(min_h)
        if(ind+1 != len(verti)):
            temp_min = verti[ind+1]
        else:
            temp_min = verti[ind]

        hori = []
        for i in res:
            hori.append(i[2])

        temp_max = min(hori)


        if max_f < temp_max:
            max_f = -1
            for i in res:
                max_f = max(max_f, i[0])
            min_h = h
            for i in res:
                if i[0] == max_f:
                    min_h = min(min_h, i[1])

        

        coords = {}
        if(ind + 1 != len(verti)):
            for j in range(max_f, temp_max, -1):
                for i in range(min_h, temp_min):
                    value = adaptive_thresh[i, j]
                    if value == 255:
                        if j not in coords:
                            coords[j] = 1
                        else:
                            coords[j] += 1

        count = -1
        key = []
        for i in coords:
            if coords[i] > count:
                count = coords[i]

        for i in coords:
            if abs(coords[i] - count) <= 10:
                key.append(i)

        if(len(key) != 0):
            max_f = max(key)
        
        ########################## VERTICAL PREDICTION ########################

        image = cv2.imread('1resume.jpg')
        h, w = image.shape[:2]

        te = []
        for i in result:
            if result[i][2] < max_f:
                te.append(result[i][2])
        temp_max = max(te)

        tem = -1
        for i in res:
            tem = max(tem, i[1])

        coords = {}
        for j in range(max_f, temp_max, -1):
            for i in range(tem, 1, -1):
                try:
                    value = adaptive_thresh[i, j]
                except:
                    pass
                if value == 255:
                    if i not in coords:
                        coords[i] = 1
                    else:
                        coords[i] += 1

        count = max_f - temp_max

        tem = h
        for i in res:
            tem = min(tem, i[1])

        key = []
        for i in coords:
            if coords[i] == count and i < tem:
                key.append(i)
        key = sorted(key)
        differences = [abs(key[i] - key[i-1]) for i in range(1, len(key))]
        
        mapped_values = {key[i]: differences[i-1] for i in range(1, len(key))}
        diff = 100000000000000
        for i in mapped_values:
            diff = min(mapped_values[i],diff)

        sk = []
        for i in mapped_values:
            if mapped_values[i] == diff:
                sk.append(i)

        if len(sk) != 0:
            min_h = max(sk)
        else:
            min_h = 1
        


        shalf = []
        fhalf = []
        shalf_label = []
        fhalf_label = []
        for i in headings:
            if i['box'][0] >= max_f-50:
                shalf.append(i['box'])
                shalf_label.append(i['text'])
            else:
                fhalf.append(i['box'])
                fhalf_label.append(i['text'])
        
        

        if max_f < 1100 and max_f > 500:
            if min_h > 10:
                final_coords = {"profile":[0,0,w-10,min_h]}
                prev = min_h
                for i in range(len(fhalf)-1):
                    final_coords[fhalf_label[i]] = [0,fhalf[i][1],max_f,fhalf[i+1][1]]
                    prev = fhalf[i+1][1]

                final_coords[fhalf_label[-1]] = [0,prev,max_f,h]

                prev = min_h
                for i in range(len(shalf)-1):
                    if shalf[i][0] < max_f:
                        final_coords[shalf_label[i]] = [shalf[i][0],shalf[i][1],w-10,shalf[i+1][1]]
                    else:
                        final_coords[shalf_label[i]] = [max_f,shalf[i][1],w-10,shalf[i+1][1]]

                    prev = shalf[i+1][1]
                
                final_coords[shalf_label[-1]] = [max_f,prev,w,h]


                ######################################## TO VISUALIZE ############################################
                # image_path = '1resume.jpg'
                # image = cv2.imread(image_path)

                # def draw_boxes(image, coordinates):
                #     for label, coord in coordinates.items():
                #         x1, y1, x2, y2 = coord
                #         cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                #         cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                #     cv2.imwrite('bounding.jpg',image)
                
                # draw_boxes(image, final_coords)
                #####################################################################################################
                return "SUCCESS",final_coords
                
            
            else:
                final_coords = {}
                prev = min_h
                for i in range(len(fhalf)-1):
                    final_coords[fhalf_label[i]] = [0,fhalf[i][1],max_f,fhalf[i+1][1]]
                    prev = fhalf[i+1][1]

                final_coords[fhalf_label[-1]] = [0,prev,max_f,h]

                prev = min_h
                for i in range(len(shalf)-1):
                    if shalf[i][0] < max_f:
                        final_coords[shalf_label[i]] = [shalf[i][0],shalf[i][1],w-10,shalf[i+1][1]]
                    else:
                        final_coords[shalf_label[i]] = [max_f,shalf[i][1],w-10,shalf[i+1][1]]

                    prev = shalf[i+1][1]
                
                final_coords[shalf_label[-1]] = [max_f,prev,w,h]

                #################################### TO VISUALIZE ###############################################
                # image_path = '1resume.jpg'
                # image = cv2.imread(image_path)

                # def draw_boxes(image, coordinates):
                #     for label, coord in coordinates.items():
                #         x1, y1, x2, y2 = coord
                #         cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                #         cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                #     cv2.imwrite('bounding.jpg',image)
                
                # draw_boxes(image, final_coords)
                ###################################################################################################
                return "SUCCESS",final_coords
            
            
        else:
            return "FAILED",{}
    
    @staticmethod
    def single_layout(filename,headings):
    
        '''
        This function/algorithm is written for the cases which has SINGLE LAYOUT.
        Returns a "SUCCESS" message along with final coordinates.
        
        '''

        pdf_images = convert_from_path(filename)
        for i in range(len(pdf_images)):
            pdf_images[i].save(str(i+1)+'resume.jpg')
        
        

        img = PIL.Image.open('1resume.jpg')
        w,h = img.size
        min_f = w
        for i in headings:
            min_f = min(min_f,i['box'][0])

        prev = 0
        hei = 0
        final_coords = {}
        label = ['prof']
        for i in headings:
            label.append(i['text'])
        
        coord = []
        for i in headings:
            coord.append(i['box'])

        for i in range(len(coord)-1):
            hei = coord[i][1]
            final_coords[label[i]] = [0,prev,w,hei]
            prev = coord[i][1]
        
        final_coords[label[-1]] = [0,coord[-1][1],w,h]
        
        return "SUCCESS",final_coords

        ########################################## TO VISUALIZE ##################################################
        # image_path = '1resume.jpg'
        # image = cv2.imread(image_path)

        # def draw_boxes(image, coordinates):
        #     for label, coord in coordinates.items():
        #         x1, y1, x2, y2 = coord
        #         cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        #         cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        #     cv2.imwrite('bounding.jpg',image)
        
        # draw_boxes(image, final_coords)
        #############################################################################################################
    @staticmethod
    def get_coordinates(filename):
        res , headings,results = ResumeparserConfig.getLayout(filename)
        if res == "SINGLE":
            msg,coords = ResumeparserConfig.single_layout(filename,headings)
        else:
            msg ,coords = ResumeparserConfig.multi(filename,headings,results)

        os.remove('1resume.jpg')
        return msg,coords
    





        




    
    



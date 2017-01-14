import cv2
from PIL import Image, ImageFilter
from pylab import *
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt
import os
import glob

HISTO_DEBUG = False

src_path = 'images\\usjn_mod1.png'
# src_path = 'images\\phoneimg_cropped.png'
#src_path = 'images\\phoneimg_table.png'

storage_path = 'static\\images\\*.png'


def get_image_file(img_file):

    try:
        print('Getting image for processing...')
        pil_object = Image.open(img_file)
        # print('PIL Object = ', pil_object.size, 'Mode = ', pil_object.mode)
    except IOError:
        print(' Unable to open image: ', img_file)

    return pil_object


def remove_old_image_files(remove_files_path, purge=True):

    # Find and remove any current images in folder
    img_files = glob.glob(remove_files_path)
    # print (img_files)
    if img_files and purge:
        print ("Removing old crops before creating new...")
        for im in img_files:
            os.remove(im)
    else:
        if purge:
            print('Image folder was found empty...')


def invert_image_pixels(img_array, max_bin):

    invert_image = empty_like(img_array)
    # print('invert image = ', type(invert_image), invert_image.shape, invert_image.dtype)
    print('Inverting image pixels...')
    for point in np.ndindex(img_array.shape):
        if img_array[point] > (max_bin + 25):
            invert_image[point] = 250
        else:
            invert_image[point] = 0

    # cv2.imshow('CV2 Invert Image', invert_image)

    return invert_image


def calculate_histogram(img_file):

    print('Calculating histogram...')
    #cv2.imshow('CV2 Histo Img', img_file)
    hist1 = cv2.calcHist([img_file], [0], None, [256], [0, 256])
    # print('hist1 = ', type(hist1), hist1.shape, hist1.dtype)
    # Finding the largest bin, bin index indicates intensity value
    # print ('Max point = ', np.nanargmax(hist1), 'Max size = ', hist1[np.nanargmax(hist1), 0])

    if HISTO_DEBUG:
        plt.plot(hist1)
        plt.show()
        plt.plot(hist2)
        plt.show()

    return invert_image_pixels(img_file, np.nanargmax(hist1))


def find_horizontal_lines(img_array):

    maxy, maxx = img_array.shape
    horProj = cv2.reduce(img_array, 1, cv2.REDUCE_AVG)
    isSpace = False
    count = None
    yMean = None
    yCoords = list()
    for index in np.ndindex(horProj.shape):
        y, x = index
        # print(index, horProj[(y, x)])
        if isSpace == False:
            if horProj[(y, x)] == 0:
                isSpace = True
                count = 1
                yMean = y
        else:
            if horProj[(y, x)] != 0 or y == (maxy - 1):
                isSpace = False
                # print(yMean / count)
                yCoords.append((yMean / count) - 2)
            else:
                yMean += y
                count += 1

    return yCoords


def find_vertical_lines(img_array, number):

    maxy, maxx = img_array.shape
    isSpace = False
    count = None
    xMean = None
    xCoords = list()
    vertProj = cv2.reduce(img_array, 0, cv2.REDUCE_AVG)
    for index in np.ndindex(vertProj.shape):
        y, x = index
       # print(index, vertProj[(y, x)])
        if isSpace == False:
            if x + 2 <= maxx:
                if vertProj[(y, x)] == 0 and vertProj[(y, (x-2))] == 0 and vertProj[(y, (x-3))] == 0 and vertProj[(y, (x+2))] == 0 and vertProj[(y, (x+3))] == 0:
                    isSpace = True
                    count = 1
                    xMean = x
            else:
                if vertProj[(y, x)] == 0 and vertProj[(y, (x-2))] == 0:
                    isSpace = True
                    count = 1
                    xMean = x
        else:
            if vertProj[(y, x)] != 0 or x == (maxx - 1):
                isSpace = False
                if (xMean / count) > 1:
                    #print("Image #", number, "VLine Draw @ = ", xMean / count)
                    xCoords.append((xMean / count) - 2)
            else:
                xMean += x
                count += 1

    return xCoords


def save_vertical_crops(image_list, selected_image):

    if not os.path.exists('static/images/' + str(selected_image) + "/"):
        os.makedirs('static/images/' + str(selected_image) + "/")
    else:
        remove_old_image_files('static/images/' + str(selected_image) + "/*.*", True)

    count = 0
    for eachImage in image_list:
        y, x = eachImage.shape
        if x > 0:
            #print('each_image = ' + str(count), type(eachImage), eachImage.shape, eachImage.dtype)
            #cv2.imshow('Row Crops' + str(selected_image), eachImage)
            cv2.imwrite('static/images/' + str(selected_image) + "/" + str(selected_image) + "-" + str(count) + '.png', eachImage)
            count += 1


if __name__ == '__main__':

    remove_old_image_files(storage_path, True)

    pil_image = get_image_file(src_path)

    # What are the dimensions of the image
    maxy, maxx, dtype = np.array(pil_image).shape
    print("Original Image Shape = ", maxy, maxx)

    pil_img_sharpen = pil_image.filter(ImageFilter.SHARPEN)
    #print('pil_img_sharpen = ', type(pil_img_sharpen))

    img_grey = cv2.cvtColor(np.array(pil_img_sharpen), cv2.COLOR_RGB2GRAY)
    # cv2.imshow('CV2 Grey', img_grey)
    # print('img_grey = ', type(img_grey), img_grey.shape, img_grey.dtype)

    kernel = np.ones((1, 1), np.uint8)

    img_dilate = cv2.dilate(img_grey, kernel, iterations=1)
    # cv2.imshow('CV2 Dilate', img_dilate)

    img_erode = cv2.erode(img_dilate, kernel, iterations=1)
    # cv2.imshow('CV2 Erode', img_erode)

    img_denoise = cv2.fastNlMeansDenoising(img_erode)
    # cv2.imshow('CV2 Denoise', img_denoise)

    # img_bilateral = cv2.bilateralFilter(img_denoise, 3, 50, 50)

    # Invert the bits of the image, this turns text white
    img_invert = cv2.bitwise_not(img_erode)
    # print('img_invert = ', type(img_invert), img_invert.shape, img_invert.dtype)
    # cv2.imshow('CV2 Invert', img_invert)

    img_threshold = cv2.adaptiveThreshold(img_grey, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    # cv2.imshow('CV2 Threshold', img_threshold)

    final_img = calculate_histogram(img_invert)
    print('final_img = ', type(final_img), final_img.shape, final_img.dtype)

    print('Find horizontal line segments...')
    horizontal_segments = find_horizontal_lines(final_img)

    previousYpt = 0
    cropped_images = list()
    print('Cropping images by row... ')
    for ypt in horizontal_segments:
        # its img[y: y + h, x: x + w], upper left and lower right X,Y coords
        cropped_images.append(final_img[previousYpt:ypt, 0:maxx])
        # draw the horizontal lines on the image
        # cv2.line(img_final, (0, ypt), (maxx, ypt), (0, 0, 255))
        previousYpt = ypt

    i = 30  # default starting pic count, makes for easy sorting
    previousXpt = 1
    vertical_crops = list()
    for im in cropped_images:
        print('Find vertical line segments...')
        vertical_segments = find_vertical_lines(im, i)
        #print('im = ', type(im), im.shape, im.dtype)
        maxy, maxx = im.shape
        for xpt in vertical_segments:
            vertical_crops.append(im[0:maxy, previousXpt:xpt])
            # cv2.line(vert_img, (xpt, 0), (xpt, maxy), (0, 255, 0))
            # cv2.putText(img_final, str(xpt), (xpt, 30), cv2.FONT_HERSHEY_SIMPLEX, .2, (0, 255, 0))
            previousXpt = xpt
            #cv2.imshow('CV2 Cropped' + str(xpt), im[0:maxy, previousXpt:xpt])
        save_vertical_crops(vertical_crops, i)
        vertical_crops = list()
        print ('Saving cropped image...' + str(i))
        # cv2.imshow('CV2 Cropped' + str(i), im)
        cv2.imwrite('static\\images\\' + str(dt.date.today()) + str(i) + '.png', im)
        i += 1

    print('Image processing completed!')

    cv2.waitKey(0)
    cv2.destroyAllWindows()

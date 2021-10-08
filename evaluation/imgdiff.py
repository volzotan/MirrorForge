import os
import datetime

import cv2
import numpy as np

IMG_DIR         = "images"
OUTPUT_DIR      = "."
REFERENCE_IMAGE = os.path.join(IMG_DIR, "glass_al.jpg")

OUTPUT_IMAGE_QUALITY    = 60
NUMBER_OF_ITERATIONS    = 1000
TERMINATION_EPS         = 1e-4 #1e-6 #1e-10

images = []
for f in os.listdir(IMG_DIR):
    p = os.path.join(IMG_DIR, f)
    if os.path.isfile(p):
        for ext in ["jpg", "png"]:
            if f.lower().endswith(ext):
                images.append(p)

if REFERENCE_IMAGE in images:
    images.remove(REFERENCE_IMAGE)

if len(images) > 0:
    print("found images: {}".format(len(images)))
    for name in images:
        print("    {}".format(name))

ref_img = cv2.imread(REFERENCE_IMAGE, cv2.IMREAD_GRAYSCALE)

for path in images:
    basepath, filename = os.path.split(path)
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    diff = np.zeros(img.shape, dtype=np.int8)

    time_start = datetime.datetime.now()

    warp_matrix = np.eye(3, 3, dtype=np.float32)

    WARP_MODE               = cv2.MOTION_HOMOGRAPHY
    CRITERIA = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, NUMBER_OF_ITERATIONS, TERMINATION_EPS)
    (cc, warp_matrix) = cv2.findTransformECC(ref_img, img, warp_matrix, WARP_MODE, CRITERIA, None, 5)
    size = img.shape
    img = cv2.warpPerspective(img, warp_matrix, (size[1], size[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
   
    print("aligned image: {} | time: {:06.2f}s".format(filename, (datetime.datetime.now()-time_start).total_seconds()))

    diff = img.astype(np.int) - ref_img.astype(np.int)
    diff = np.abs(diff)

    cv2.imwrite(os.path.join(OUTPUT_DIR, "align_{}".format(filename)), img, [int(cv2.IMWRITE_JPEG_QUALITY), OUTPUT_IMAGE_QUALITY])
    cv2.imwrite(os.path.join(OUTPUT_DIR, "diff_{}".format(filename)), diff, [int(cv2.IMWRITE_JPEG_QUALITY), OUTPUT_IMAGE_QUALITY])
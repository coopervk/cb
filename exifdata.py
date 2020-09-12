import exif

with open('samplegpsexif.jpg', 'rb') as image:
    image = exif.Image(image)
    print("dir:", dir(image))
    print(f"gps lat, long: {image.gps_latitude}, {image.gps_longitude}")


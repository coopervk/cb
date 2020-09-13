import exif

def get_exif_data(image_name):
    with open(image_name, 'rb') as image:
        image = exif.Image(image)
        print("dir:", dir(image))
        print("have exif?:", image.has_exif)
        if image.has_exif:
            print(f"gps lat, long: {image.gps_latitude}, {image.gps_longitude}")

def main():
    print("---EXIF---")
    get_exif_data("samplegpsexif.jpg")
    print("\n---NO EXIF---")
    get_exif_data("samplenoexif.jpg")


if __name__ == "__main__":
    main()

import exif
import types

def get_exif_data(image_name):
    with open(image_name, 'rb') as image:
        image = exif.Image(image)
        if image.has_exif:
            for prop in dir(image):
                try:
                    val = getattr(image, prop)
                    if prop[0:1] != "_":
                        if not isinstance(val, types.MethodType):
                            print(f"{prop}: {val}")
                except:
                    pass

def clean_exif(image_name):
    with open(image_name, 'rb') as image:
        image = exif.Image(image)
        if not image.has_exif:
            return None
        image.delete_all()
        with open('cleaned.jpg', 'wb') as cleaned_image:
            cleaned_image.write(image.get_file())
        return 'cleaned.jpg'

def main():
    print("---EXIF---")
    get_exif_data("samplegpsexif.jpg")
    print("\n---NO EXIF---")
    get_exif_data("samplenoexif.jpg")
    #print("\n---CLEAN EXIF---")
    #new_image = clean_exif("samplegpsexif.jpg")
    #if new_image:
    #    get_exif_data(new_image)

if __name__ == "__main__":
    main()
